#!/usr/bin/env python3
"""Окна в DE-режиме angelOS открываются там же и того же размера, где их закрыли.

Слушает `niri msg -j event-stream`. Для каждого плавающего окна держит последнее положение
(tile_pos_in_workspace_view) и размер (window_size); при закрытии пишет их по app-id в
~/.local/state/window-memory.json. Когда программа открывает первое окно (других её окон нет)
и DE-режим включён (settings.json windows.floatAll), окно ставится на запомненное место
и в запомненный размер (move-floating-window, set-window-width/height по id).
Файлы angelOS и angel-niri не трогаются.

  window-memory.py          служба (systemd --user: window-memory.service)
  window-memory.py list     что запомнено
  window-memory.py forget [APP_ID]   забыть одну программу или всё
"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

HOME = Path.home()
STATE = Path(os.environ.get("XDG_STATE_HOME") or HOME / ".local/state") / "window-memory.json"
SETTINGS = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config") / "angelos/settings.json"
# программы, которые не трогаем (свои окна angelOS, картинка-в-картинке и т.п.)
SKIP = {"", "quickshell", "org.quickshell"}
MIN_W, MIN_H = 200, 120


def load():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save(mem):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(mem, ensure_ascii=False, indent=1, sort_keys=True))
    tmp.replace(STATE)


def desktop_mode():
    try:
        return bool(json.loads(SETTINGS.read_text()).get("windows", {}).get("floatAll"))
    except Exception:
        return False


def niri(*args):
    return subprocess.run(["niri", "msg", *args], capture_output=True, text=True)


def outputs():
    r = niri("-j", "outputs")
    try:
        out = {}
        for name, o in json.loads(r.stdout).items():
            lg = o.get("logical") or {}
            if lg:
                out[name] = (lg["width"], lg["height"])
        return out
    except Exception:
        return {}


class Memory:
    def __init__(self):
        self.mem = load()
        self.windows = {}      # id -> window dict (последнее известное)
        self.geo = {}          # id -> {"x","y","w","h","output"}
        self.workspaces = {}   # id -> output
        self.seen = set()      # окна, которые уже были при старте или уже обработаны
        self.started = False

    # ---- события ----
    def on_workspaces(self, wss):
        self.workspaces = {w["id"]: w.get("output") for w in wss}

    def note(self, w):
        self.windows[w["id"]] = w
        lay = w.get("layout") or {}
        pos, size = lay.get("tile_pos_in_workspace_view"), lay.get("window_size")
        if w.get("is_floating") and pos and size:
            self.geo[w["id"]] = {
                "x": round(pos[0]), "y": round(pos[1]),
                "w": int(size[0]), "h": int(size[1]),
                "output": self.workspaces.get(w.get("workspace_id")),
            }

    def on_windows(self, ws):
        for w in ws:
            self.note(w)
            if not self.started:
                self.seen.add(w["id"])
        self.started = True

    def on_opened_or_changed(self, w):
        new = w["id"] not in self.windows and w["id"] not in self.seen
        self.note(w)
        if new:
            self.seen.add(w["id"])
            self.restore(w)

    def on_layouts(self, changes):
        for wid, lay in changes:
            w = self.windows.get(wid)
            if w is not None:
                w = dict(w, layout=lay)
                self.note(w)

    def on_closed(self, wid):
        w = self.windows.pop(wid, None)
        g = self.geo.pop(wid, None)
        self.seen.discard(wid)
        if not w or not g or not w.get("is_floating") or not desktop_mode():
            return
        app = w.get("app_id") or ""
        if app in SKIP or g["w"] < MIN_W or g["h"] < MIN_H:
            return
        self.mem[app] = g
        save(self.mem)

    # ---- восстановление ----
    def restore(self, w):
        app = w.get("app_id") or ""
        g = self.mem.get(app)
        if not g or app in SKIP or not desktop_mode():
            return
        # только первое окно программы: второе окно и диалоги открываются как обычно
        if any(o.get("app_id") == app and o["id"] != w["id"] for o in self.windows.values()):
            return
        threading.Thread(target=self.place, args=(w["id"], g), daemon=True).start()

    def place(self, wid, g):
        # дать angel-niri показать окно (и бросок «Desk throw»), потом поставить на место
        time.sleep(0.15)
        w = self.windows.get(wid)
        if not w or not w.get("is_floating"):
            return
        outs = outputs()
        out = self.workspaces.get(w.get("workspace_id"))
        sw, sh = outs.get(out) or next(iter(outs.values()), (1920, 1080))
        ww, wh = min(g["w"], sw), min(g["h"], sh)
        # не дать окну уехать за экран (на другом мониторе/разрешении)
        x = max(0, min(g["x"], sw - min(ww, 120)))
        y = max(0, min(g["y"], sh - 60))
        i = str(wid)
        niri("action", "set-window-width", "--id", i, str(ww))
        niri("action", "set-window-height", "--id", i, str(wh))
        niri("action", "move-floating-window", "--id", i, "-x", str(x), "-y", str(y))
        # move-floating-window считает от рабочей области (без панелей), а позиция в IPC — от края
        # экрана: сверить, где окно встало, и сдвинуть на разницу
        time.sleep(0.1)
        pos = self.pos_of(wid)
        if pos:
            dx, dy = x - round(pos[0]), y - round(pos[1])
            if dx or dy:
                niri("action", "move-floating-window", "--id", i, "-x", f"{dx:+d}", "-y", f"{dy:+d}")

    def pos_of(self, wid):
        r = niri("-j", "windows")
        try:
            for w in json.loads(r.stdout):
                if w["id"] == wid:
                    return (w.get("layout") or {}).get("tile_pos_in_workspace_view")
        except ValueError:
            pass
        return None


def serve():
    m = Memory()
    while True:
        p = subprocess.Popen(["niri", "msg", "-j", "event-stream"], stdout=subprocess.PIPE, text=True)
        for line in p.stdout:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            k, v = next(iter(ev.items()))
            if k == "WorkspacesChanged":
                m.on_workspaces(v["workspaces"])
            elif k == "WindowsChanged":
                m.on_windows(v["windows"])
            elif k == "WindowOpenedOrChanged":
                m.on_opened_or_changed(v["window"])
            elif k == "WindowLayoutsChanged":
                m.on_layouts(v["changes"])
            elif k == "WindowClosed":
                m.on_closed(v["id"])
        p.wait()
        time.sleep(2)  # niri перезапустился — подключиться снова


def main():
    a = sys.argv[1:]
    if not a:
        serve()
    elif a[0] == "list":
        for app, g in sorted(load().items()):
            print(f"{app}: {g['w']}x{g['h']} в ({g['x']}, {g['y']}) на {g.get('output')}")
    elif a[0] == "forget":
        mem = load()
        if len(a) > 1:
            mem.pop(a[1], None)
        else:
            mem = {}
        save(mem)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
