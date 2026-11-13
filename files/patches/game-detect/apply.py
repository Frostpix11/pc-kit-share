#!/usr/bin/env python3
"""pc-kit patch game-detect for ~/.local/bin/niri-game-mode (Celestia, 2026-11-03).

X11 windows reach niri as xwayland-satellite's, so the author's is_game() took ANY X11 window for a
game while a Steam game ran (Spotify, Steam itself) and FocusBoost raised satellite, never the game.
Now: the X server says who owns the window (XRes, from the client's socket: the app can't lie),
that process's own environment decides (SteamGameId / Minecraft); FocusBoost raises that process
tree AND satellite's (Xwayland is on every frame's path of an X11 game). Without python-xlib or
XRes it falls back to the author's rule. The boost line logs niri's real nice.

  apply.py          apply (keeps niri-game-mode.angelos-orig once)
  apply.py check    exit 0 if applied
  apply.py revert   back to the original
"""
import os, shutil, sys
from pathlib import Path

F = Path(os.environ.get("NGM_FILE") or Path.home() / ".local/bin/niri-game-mode")
ORIG = F.with_name("niri-game-mode.angelos-orig")
MARK = "# celestia game-detect"

PAIRS = [
# 1. XRes helper before is_game
("""def is_game(win: dict) -> bool:
""", """# celestia game-detect: the real owner of an X11 window (XRes) instead of satellite's pid
_X = None
_XPID: dict[int, tuple[str, int | None]] = {}   # niri window id -> (title, pid)


def _xdisplay():
    global _X
    if _X is None:
        try:
            from Xlib import display
            _X = display.Display(os.environ.get("DISPLAY") or ":1")
            if not _X.has_extension("X-Resource"):
                _X = False
        except Exception:
            _X = False
    return _X or None


def x11_pid(win: dict) -> int | None:
    \"\"\"the process behind an X11 window: niri's app_id is its WM_CLASS, the title its name; the
    X server tells the owner from the socket (XRes). None: unknown (no python-xlib/XRes, not found)\"\"\"
    global _X
    wid, title, app = win.get("id"), win.get("title") or "", win.get("app_id") or ""
    hit = _XPID.get(wid)
    if hit and hit[0] == title and hit[1] and Path(f"/proc/{hit[1]}").exists():
        return hit[1]
    d = _xdisplay()
    if d is None:
        return None
    try:
        from Xlib.ext import res
        named, same_app = [], []
        todo = [d.screen().root]
        while todo:
            w = todo.pop()
            for c in w.query_tree().children:
                todo.append(c)
                try:
                    cls = c.get_wm_class()
                except Exception:
                    cls = None
                if not cls or app not in cls:
                    continue
                same_app.append(c)
                try:
                    p = c.get_full_property(d.intern_atom("_NET_WM_NAME"), d.intern_atom("UTF8_STRING"))
                    name = p.value.decode("utf-8", "replace") if p else (c.get_wm_name() or "")
                except Exception:
                    name = ""
                if name == title:
                    named.append(c)
        pick = named or same_app
        pid = None
        for c in pick:
            r = d.res_query_client_ids([{"client": c.id, "mask": res.LocalClientPIDMask}])
            pids = [i.value[0] for i in r.ids if i.spec.mask == res.LocalClientPIDMask and i.value]
            if pids:
                pid = pids[0]
                break
    except Exception:
        _X = None          # satellite restarted: connect again next time
        return None
    _XPID[wid] = (title, pid)
    return pid


def _satellite(pid) -> bool:
    return isinstance(pid, int) and pid > 0 and _comm(pid).lower().startswith(("xwayland", "xwayland-satellite"))


def boost_pids(win: dict | None) -> tuple[int, ...]:
    \"\"\"whom FocusBoost raises for the focused window: its process; for an X11 window the real
    owner and satellite (with its Xwayland)\"\"\"
    pid = (win or {}).get("pid")
    if not isinstance(pid, int) or pid <= 1:
        return ()
    if _satellite(pid):
        real = x11_pid(win)
        return (real, pid) if real and real != pid else (pid,)
    return (pid,)


def is_game(win: dict) -> bool:
"""),
# 2. X11 branch of is_game
("""    if not _comm(pid).lower().startswith(("xwayland", "xwayland-satellite")):
        return False
    return steam_game_running() or""",
"""    if not _comm(pid).lower().startswith(("xwayland", "xwayland-satellite")):
        return False
    real = x11_pid(win)
    if real is not None:   # celestia game-detect: the owner's own environment decides
        return bool(re.search(rb"(?:^|\\0)Steam(?:Game|App)Id=[1-9]", _environ(real))) or _minecraft(real)
    return steam_game_running() or"""),
# 3. FocusBoost over several roots
("""    def move(self, pid: int | None) -> None:
        if pid == self.pid:
            return
        self.restore()
        self.pid = pid
        if pid is None or pid <= 1 or not focus_boost_wanted():
            return
        for proc in process_tree(pid):""",
"""    def move(self, pids) -> None:
        # celestia game-detect: a tuple of roots (boost_pids), or a pid / None as before
        pids = tuple(pids) if isinstance(pids, (tuple, list)) else ((pids,) if pids else ())
        if pids == self.pid:
            return
        self.restore()
        self.pid = pids
        if not pids or not focus_boost_wanted():
            return
        for proc in [p for root in pids if root > 1 for p in process_tree(root)]:"""),
("""        if self.pid is not None and back:
            for proc in process_tree(self.pid):""",
"""        if self.pid and back:
            for proc in [p for root in self.pid for p in process_tree(root)]:"""),
# 4. the watcher hands the roots
("""                        focus.move(win.get("pid") if win else None)""",
"""                        focus.move(boost_pids(win))"""),
# 5. honest log
("""        return "boost on: performance, niri nice %d" % NIRI_NICE""",
"""        tids = niri_threads()   # celestia game-detect: the nice niri really has
        real = os.getpriority(os.PRIO_PROCESS, tids[0]) if tids else None
        return "boost on: performance, niri nice %s" % real"""),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    text = F.read_text()
    applied = MARK in text
    if mode == "check":
        sys.exit(0 if applied else 1)
    if mode == "revert":
        if ORIG.exists():
            shutil.copy2(ORIG, F); print("reverted")
        else:
            print("no original kept"); sys.exit(1)
        return
    if applied:
        print("already applied"); return
    for old, new in PAIRS:
        if text.count(old) != 1:
            print("does not fit (author changed niri-game-mode?):\n" + old[:200]); sys.exit(2)
    shutil.copy2(F, ORIG)   # the author's file as it is now (an update may have changed it)
    for old, new in PAIRS:
        text = text.replace(old, new, 1)
    F.write_text(text)
    print("applied")


if __name__ == "__main__":
    main()
