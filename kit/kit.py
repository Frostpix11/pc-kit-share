#!/usr/bin/env python3
"""kit — everything pc-kit puts on top of angelOS, in one place (Celestia, 2026-11-03).

  kit                 = kit status
  kit status          what is on, what slipped off, what doesn't fit the author's code any more
  kit status|doctor --json   the same as one JSON object (for the serp panel)
  kit inventory       JSON: every piece (shell patches, niri, satellite, plugins) with the proof
                      against the author's files (~/AngelOS-Dotfiles) and its git history
  kit diff ID         JSON: one piece's own changes, file by file
  kit doctor          status + the system around it (niri/satellite builds, explicit sync,
                      game mode, GPU clocks, groups, recorders, plugins)
  kit apply [NAME…]   put on what is off (all by default); one shell restart for the lot
  kit apply --after-update   the same, once angelOS's updater has finished (the watcher calls it)
  kit revert NAME     take one off (back to the author's)
  kit list            the names
  kit watch-files     the files the watcher listens to
  kit install-watcher write/refresh the one systemd watcher (kit-update.path/.service)

Exit code: 0 all good, 1 something is off or broken. Patches live in ~/pc-kit/files/patches
(the one source); each keeps its own way of patching, kit only drives them.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True   # kit imports inventory.py and the patch scripts: no __pycache__ beside them

HOME = Path.home()
KIT = Path(os.environ.get("PC_KIT") or Path(__file__).resolve().parent.parent)   # pc-kit/kit/kit.py
P = KIT / "files/patches"
SHELL = HOME / ".config/quickshell/angelos"
BIN = HOME / ".local/bin"
SETTINGS = HOME / ".config/angelos/settings.json"
RUN = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
# patches taken off by `kit revert` stay off (the watcher doesn't put them back) until `kit apply NAME`
DISABLED = HOME / ".config/pc-kit/disabled"


def disabled() -> set[str]:
    try:
        return set(DISABLED.read_text().split())
    except OSError:
        return set()


def set_disabled(name: str, off: bool):
    d = disabled()
    d = d | {name} if off else d - {name}
    DISABLED.parent.mkdir(parents=True, exist_ok=True)
    DISABLED.write_text("\n".join(sorted(d)) + ("\n" if d else ""))

# ---- colours (only on a terminal) ----
TTY = sys.stdout.isatty()
def c(code, s): return f"\033[{code}m{s}\033[0m" if TTY else s
OK, OFF, BAD, INFO = c("1;32", "ok "), c("1;33", "off"), c("1;31", "BAD"), c("1;36", " ··")


def run(cmd, **kw) -> subprocess.CompletedProcess:
    env = dict(os.environ, KIT_RUNNER="1")
    return subprocess.run(cmd, capture_output=True, text=True, env=env, **kw)


# ---------------------------------------------------------------- patches
class Patch:
    """A patch of the author's files. check() -> (state, note): state on | off | unfit"""
    kind = "patch"
    restarts_shell = True
    after: list[str] = []          # commands to run after apply/revert (e.g. restart a service)

    def __init__(self, name, desc, watch, **kw):
        self.name, self.desc, self.watch = name, desc, watch
        self.__dict__.update(kw)

    @property
    def dir(self): return P / self.name


class PatchPy(Patch):
    """apply.sh + patch.py (SUBS of old → new), the older kit format"""
    def check(self):
        r = run(["python3", "-I", str(self.dir / "patch.py"), "check"])
        return ("on", "") if r.returncode == 0 else ("off", "")
    def apply(self):
        return run([str(self.dir / "apply.sh"), "--wait"])
    def revert(self):
        return run([str(self.dir / "apply.sh"), "revert"])


class ApplyPy(Patch):
    """apply.py check|apply|revert, the newer kit format (one file, old → new pairs)"""
    def check(self):
        r = run(["python3", "-I", str(self.dir / "apply.py"), "check"])
        return ("on", r.stdout.strip()) if r.returncode == 0 else ("off", "")
    def apply(self):
        return run(["python3", "-I", str(self.dir / "apply.py"), "apply"])
    def revert(self):
        return run(["python3", "-I", str(self.dir / "apply.py"), "revert"])


class GitPatches(Patch):
    """codex-fixes: git patches against the shell, each only if the author's code still fits"""
    def check(self):
        states = []
        ga = lambda *x: run(["git", "-C", str(HOME), "apply", *x]).returncode == 0
        for p in sorted(self.dir.glob("*.patch")):
            if ga("--reverse", "--check", str(p)):
                states.append("on")
            elif ga("--check", str(p)):
                states.append("off")
            else:
                states.append("unfit")
        n = len(states)
        if all(s == "on" for s in states):
            return "on", ""
        if "off" in states:
            return "off", f"{states.count('off')}/{n} not applied"
        return "on", f"{states.count('unfit')}/{n} skipped (author changed or fixed it)"
    def apply(self):
        return run([str(self.dir / "apply.sh"), "--wait"])
    def revert(self):
        return run([str(self.dir / "apply.sh"), "revert"])


class Privacy(Patch):
    """privacy-capture: niri-cast-privacy rule + niri-record-region pieces + Settings toggle"""
    def check(self):
        notes = []
        cp = BIN / "niri-cast-privacy"
        if cp.exists() and "kit-patch: и на записи" not in cp.read_text():
            notes.append("cast rule")
        rr = BIN / "niri-record-region"
        if rr.exists():
            t = rr.read_text()
            miss = [f.name for f in sorted((self.dir / "rec").glob("*-new.txt")) if f.read_text() not in t]
            if miss:
                notes.append(f"record pieces {len(miss)}")
        if run(["python3", "-I", str(self.dir / "settings.py"), "check"]).returncode != 0:
            notes.append("settings toggle")
        return ("off", "missing: " + ", ".join(notes)) if notes else ("on", "")
    def apply(self):
        return run([str(self.dir / "apply.sh"), "--wait"])
    def revert(self):
        return run([str(self.dir / "apply.sh"), "revert"])


class SerpSkin(ApplyPy):
    """serp-skin (files/serp-skin): a whole skin — its own modules copied in, hunks in ~60 of the
    author's files. What it watches comes from its apply.py (HUNKS + NEW), so the list never drifts."""
    @property
    def dir(self): return P.parent / "serp-skin"

    @property
    def watch(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("serp_apply", self.dir / "apply.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return sorted(k for k in list(m.HUNKS) + list(m.NEW) if not k.startswith("~/"))

    @watch.setter
    def watch(self, _): pass


S = "config/SettingsSchema.qml"
# watch lists: the files each patch changes (taken from its old per-patch watcher)
PATCHES: list[Patch] = [
    PatchPy("cursor-motion", "Настройки → Курсор: живой курсор и камера", [S, "services/CursorShake.qml", "modules/settings/catalog/Cursor.qml", "modules/settings/tree.json"]),
    PatchPy("dock-spacing", "Golden Gate: отступы Дока", [S, "services/GoldenGate.qml", "modules/mac/MacDock.qml", "modules/settings/catalog/Mac.qml"]),
    PatchPy("mac-cursor", "Golden Gate: пиксельный мак-курсор", ["services/Cursors.qml"]),
    PatchPy("mac-settings-lights", "Golden Gate: один светофор у Настроек", ["modules/settings/views/MacView.qml"]),
    PatchPy("mac-tint", "Golden Gate: цвет из обоев", [S, "config/Config.qml", "config/Theme.qml", "services/PaletteGenerator.qml", "services/GoldenGate.qml", "services/ThemeExport.qml", "modules/settings/catalog/Mac.qml"]),
    PatchPy("pixora-mac", "Golden Gate: иконки Pixora вместо MacTahoe", ["services/ThemeExport.qml", "scripts/goldengate.py", "scripts/qt-theme.py", "scripts/folder-tint.py", "modules/mac/MacDock.qml"]),
    PatchPy("skin-morph", "морфинг Classic ↔ Golden Gate", ["services/GoldenGate.qml", "widgets/SettingsSkinCard.qml", "modules/settings/SetupAssistant.qml", "modules/Ipc.qml"]),
    PatchPy("stack-memory", "Лента ↔ Desktop помнит окна", ["services/WindowConfig.qml", "modules/Ipc.qml"]),
    GitPatches("codex-fixes", "исправления Кодекса (Spotlight, панель, Win+D, Genie)", ["modules/bar/StartOverlay.qml", "modules/mac/MacMenuBar.qml", "modules/halo/HaloWindow.qml", "modules/mac/MacMinimizeFx.qml", "shaders/genie.vert"]),
    Privacy("privacy-capture", "приватность и на записи; запись области wf-recorder/gsr", ["bin:niri-cast-privacy", "bin:niri-record-region", S, "modules/settings/catalog/Capture.qml"]),
    ApplyPy("game-detect", "игровой режим: игра по настоящему владельцу окна (XRes), буст игры", ["bin:niri-game-mode"],
            restarts_shell=False, after=["systemctl --user restart niri-game-mode.service"]),
    ApplyPy("angel-game-quiet", "ангел молчит, пока игра закрывает её экран", ["services/Angel.qml", "modules/y2k/AngelHelper.qml"]),
    ApplyPy("halo-game-sleep", "Нимб не рисует над игрой, когда показывать нечего", ["modules/halo/HaloWindow.qml"]),
    ApplyPy("halo-game-notify", "уведомления в игре: в Нимбе на 3.5 с и со звуком (Настройки → Нимб → Поверх игры)", ["services/Halo.qml", "modules/halo/HaloWindow.qml", "modules/settings/catalog/Halo.qml", "services/Sounds.qml"]),
    ApplyPy("tray-pin", "ВРЕМЕННО, до обновления: значки трея на панель (#136 автора)", ["services/BarLayout.qml", "modules/bar/BarItem.qml", "modules/bar/TrayMenu.qml", "modules/bar/parts/Tray.qml"]),
    ApplyPy("author-picks", "ВРЕМЕННО, до обновления: фиксы автора (обои под музыку, ночные слои, текст песни, меню выключения)", ["widgets/SceneDrums.qml", "widgets/SceneLayer.qml", "widgets/SceneWall.qml", "modules/bar/parts/BarLyrics.qml", "modules/session/SessionMenu.qml"]),
    ApplyPy("scene-handover", "живые обои-сцены сменяют свой кадр только после загрузки всех слоёв (без чёрной вспышки при входе)", ["widgets/SceneLayer.qml", "widgets/SceneWall.qml", "modules/background/WallpaperView.qml"]),
    SerpSkin("serp-skin", "скин Serpantinum: острова, жидкое стекло, панели, свои виджеты (Настройки → Внешний вид → Скин)", []),
    ApplyPy("tray-menu-fresh", "меню трея спрашивает программу при каждом открытии (надпись уведомлений Telegram)", ["modules/bar/TrayMenu.qml"]),
]
BY = {p.name: p for p in PATCHES}


def watch_paths(p: Patch) -> list[Path]:
    out = []
    for w in p.watch:
        out.append(BIN / w[4:] if w.startswith("bin:") else SHELL / w)
    return out


def patch_states():
    rows = []
    for p in PATCHES:
        try:
            state, note = p.check()
        except Exception as e:  # noqa
            state, note = "unfit", str(e)
        rows.append((p, state, note))
    return rows


def restart_shell():
    subprocess.run([str(P / "restart-shell.sh")], capture_output=True)


def notify(title, body):
    subprocess.run(["notify-send", "-a", "pc-kit", "-i", "security-high", title, body], capture_output=True)


def do_apply(names, after_update=False, tell=False) -> int:
    if after_update:
        # angelOS's updater writes files for a while: wait until it is gone, then a moment more
        t0 = time.time()
        while run(["pgrep", "-f", "[d]otfiles-update.sh|[A]ngelOS-Dotfiles/install.sh|[i]nstaller/steps"]).returncode == 0:
            if time.time() - t0 > 1800:
                break
            time.sleep(5)
        time.sleep(3)
    for n in names:                       # asked by name: wanted again
        set_disabled(n, False)
    todo = [BY[n] for n in names] if names else [p for p in PATCHES if p.name not in disabled()]
    shell, failed, done = False, [], []
    for p in todo:
        state, _ = p.check()
        if state == "on":
            continue
        r = p.apply()
        state2, note = p.check()
        if state2 == "on":
            done.append(p.name)
            shell |= p.restarts_shell
            for cmd in p.after:
                subprocess.run(cmd, shell=True)
        else:
            failed.append((p.name, (r.stdout + r.stderr).strip().splitlines()[-3:] if (r.stdout or r.stderr) else [note]))
    if shell:
        restart_shell()
    for n in done:
        print(f"{OK} {n}: applied")
    for n, why in failed:
        print(f"{BAD} {n}: did not apply — " + " | ".join(why))
    if after_update and (done or failed):
        msg = (f"встало заново: {', '.join(done)}" if done else "") + \
              (("\nНЕ встало: " + ", ".join(n for n, _ in failed) + " — kit doctor") if failed else "")
        subprocess.run(["notify-send", "-a", "pc-kit", "pc-kit после обновления angelOS", msg.strip()], capture_output=True)
    if tell and not after_update:   # asked from the serp panel (detached): the answer as a notification
        if failed:
            notify("pc-kit: не встало", ", ".join(n for n, _ in failed) + " — " + " | ".join(failed[0][1])[:200])
        else:
            notify("pc-kit", "включено: " + (", ".join(done) or ", ".join(names) + " (уже было)"))
    if not todo or (not done and not failed):
        print("all patches already on")
    return 1 if failed else 0


# ---------------------------------------------------------------- the system around
def read(p) -> str:
    try:
        return Path(p).read_text()
    except OSError:
        return ""


def settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text())
    except (OSError, ValueError):
        return {}


def checks():
    """(state, label, note) rows: ok | warn | bad | info"""
    rows = []
    add = lambda s, l, n="": rows.append((s, l, n))

    # niri: our build, the pin it was made for, explicit sync
    niri = Path(os.path.realpath(BIN / "niri"))
    dropin = read(HOME / ".config/systemd/user/niri.service.d/angel-niri.conf")
    m = re.search(r"ExecStart=(\S+/niri)", dropin)
    running = ""
    r = run(["pgrep", "-x", "niri"])
    if r.stdout.strip():
        running = os.path.realpath(f"/proc/{r.stdout.split()[0]}/exe")
    pin = ""
    try:
        pin = json.loads(read(SHELL / "data/angel-niri.json")).get("commit", "")[:8]
    except ValueError:
        pass
    build = niri.parent.name
    add("ok" if build.startswith(pin or "@") and "kit" in build else "bad", "niri: our build",
        f"{build} (angelOS pins {pin})" + ("" if build.startswith(pin) else " — angelOS moved to a new niri: rebuild with build-niri.sh"))
    if m and os.path.realpath(m.group(1)) != str(niri):
        add("warn", "niri: drop-in and ~/.local/bin/niri differ", f"{m.group(1)}")
    if running and running.replace(" (deleted)", "") != str(niri):
        add("warn", "niri: running build", f"{running} — relogin to start {build}")
    add("ok" if "ANGEL_NIRI_SYNCOBJ=1" in dropin else "bad", "niri: explicit sync (ANGEL_NIRI_SYNCOBJ=1)",
        "" if "ANGEL_NIRI_SYNCOBJ=1" in dropin else "off: Xwayland copies every frame on NVIDIA")
    for env, why in (("ANGEL_NIRI_SYNC_TRACE=1", "diagnostics: frame trace in the journal"),
                     ("ANGEL_NIRI_TEAR_UNTHROTTLED=1", "measured worse (2026-11-03)")):
        if env in dropin:
            add("warn", f"niri: {env.split('=')[0]} is on", why)
    # satellite
    sat = Path(os.path.realpath(BIN / "xwayland-satellite"))
    spin = ""
    try:
        spin = json.loads(read(SHELL / "data/angel-niri.json")).get("satellite_commit", "")[:8]
    except ValueError:
        pass
    add("ok" if sat.parent.name.startswith(spin or "@") and "kit" in sat.parent.name else "bad", "satellite: our build",
        f"{sat.parent.name} (angelOS pins {spin})")
    if (BIN / "Xwayland").exists():
        add("bad", "Xwayland debug wrapper left in ~/.local/bin", "rm ~/.local/bin/Xwayland")

    # game mode
    add("ok" if "games" in run(["id", "-nG"]).stdout.split() else "bad", "group games (niri −11, focus boost)")
    add("ok" if run(["systemctl", "--user", "is-active", "niri-game-mode.service"]).stdout.strip() == "active" else "bad",
        "niri-game-mode watcher running")
    g = settings().get("gaming") or {}
    add("ok" if g.get("tearing", True) else "warn", "game mode: tearing", "on" if g.get("tearing", True) else "off (was on)")
    add("ok" if g.get("gpuClocks") is False else "warn", "game mode: author's gpuClocks off", "our helper holds the cap")
    # GPU
    gc = read("/usr/local/lib/angelos/gpu-clocks")
    cap = re.search(r"^CAP=(\d+)", gc, re.M)
    add("ok" if cap and cap.group(1) == "1950" else "bad", "GPU clock cap 1950 (undervolt +200 is unstable above)",
        f"gpu-clocks CAP={cap.group(1) if cap else '?'}" + ("" if gc else " — helper missing (AngelOS game-setup rewrote it?)"))
    for u in ("nvidia-power-limit.service", "nvidia-gpu-offset.service", "nvidia-fan-curve.service"):
        st = run(["systemctl", "is-active", u]).stdout.strip()
        add("ok" if st == "active" else "bad", u, st)
    st = run(["systemctl", "is-enabled", "celestia-wake.service"]).stdout.strip()
    add("ok" if st == "enabled" else "bad", "celestia-wake.service (EasyEffects after sleep)", st)
    add("ok" if (BIN / "kitty").exists() else "bad", "kitty wrapper (no explicit sync: it hung after sleep)")
    # Celestia's face
    # the installed copy against pc-kit's; what serp-skin changes in it on purpose (her face in the
    # skin's look) doesn't count — inventory undoes those hunks first (2026-11-14: a false warning)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import inventory
    pst, pnote = inventory.plugin_state(sys.modules[__name__], inventory.Prover(sys.modules[__name__]), "celestia",
                                        KIT / "files/plugins/celestia", HOME / ".config/angelos/plugins/celestia")
    add("ok" if pst == "on" else "warn", "plugin celestia = pc-kit", "" if pst == "on" else pnote + " — copy it again and `angelos restart`")
    hooks = read(HOME / ".claude/settings.json")
    add("ok" if "celestia-hook" in hooks and "hooks/pulse.py" in hooks else "warn", "Claude hooks for her moods (pulse + celestia-hook)")
    add("ok" if re.search(r"^AutoEnable=false", read("/etc/bluetooth/main.conf"), re.M) else "warn", "Bluetooth stays off after sleep (AutoEnable=false)")
    # CS2 launch
    c2 = read(HOME / ".config/celestia-run/730.conf")
    envline = re.search(r"^ENV=\((.*?)\)", c2, re.M)
    add("ok" if envline and "wayland" not in envline.group(1) else "warn", "CS2: X11 + hold 4:3 (the best measured)",
        envline.group(0) if envline else "no 730.conf")
    # recorders
    rec = run(["pgrep", "-a", "gpu-screen-rec"]).stdout.strip()
    add("info" if not rec else "warn", "screen recorders", "none running" if not rec else
        ("replay/timelapse running: −2…7% in games" if "-r " in rec or "timelapse" in rec else "a recording is running"))

    # plugins: the kit's copies against what is installed
    up = HOME / ".config/angelos/plugins"
    for name in ("angelos-night-2004", "privacy-eye", "mac-eq", "skin-morph"):
        src = KIT / "files/plugins" / name
        same = run(["diff", "-rq", str(src), str(up / name)]).returncode == 0
        add("ok" if same else ("bad" if not (up / name).exists() else "warn"), f"plugin {name}",
            "" if same else ("missing" if not (up / name).exists() else "differs from pc-kit"))
    for name, src in (("angelos-typer", "AngelOS-Typer"), ("angelos-room", "AngelOS-Room")):
        add("ok" if (up / name).exists() else "bad", f"plugin {name} (Кодекс)", "" if (up / name).exists() else f"install: python3 {KIT}/files/codex-plugins/{src}/install.py")
    # our tools: links into pc-kit (one copy)
    for t in sorted((KIT / "files/tools").glob("*")):
        lk = BIN / t.name
        ok = lk.is_symlink() and Path(os.path.realpath(lk)) == t.resolve()
        add("ok" if ok else "warn", f"tool {t.name}", "" if ok else "not linked from pc-kit (install.sh gaming)")
    xl = run(["python3", "-c", "import Xlib"]).returncode == 0
    add("ok" if xl else "warn", "python-xlib (game-detect asks X who owns a window)", "" if xl else "falls back to the author's guess")
    kp = HOME / ".local/share/angelos-kit/patches"
    add("ok" if kp.is_symlink() else "warn", "patches: one copy (angelos-kit/patches → pc-kit)", "" if kp.is_symlink() else "a separate copy")
    # the watcher
    st = run(["systemctl", "--user", "is-active", "kit-update.path"]).stdout.strip()
    add("ok" if st == "active" else "bad", "kit watcher (kit-update.path)", st)
    old = [u.name for u in (HOME / ".config/systemd/user").glob("*.path") if u.name.startswith(("kit-patch-", "vm-patch-"))]
    if old:
        add("warn", "old per-patch watchers still there", ", ".join(old))
    return rows


def show_patches() -> int:
    bad = 0
    print(c("1", "patches (angelOS files)"))
    for p, state, note in patch_states():
        off_by_user = p.name in disabled()
        tag = c("1;34", "-- ") if off_by_user and state != "on" else {"on": OK, "off": OFF, "unfit": BAD}[state]
        bad += state != "on" and not off_by_user
        if off_by_user:
            note = (note + "; " if note else "") + "taken off by you (kit apply " + p.name + " to bring it back)"
        print(f"  {tag} {p.name:20s} {p.desc}" + (f"  — {note}" if note else ""))
    return bad


def cmd_status() -> int:
    bad = show_patches()
    if bad:
        print(f"\n{bad} off: kit apply")
    return 1 if bad else 0


def cmd_doctor() -> int:
    bad = show_patches()
    print(c("1", "\nsystem"))
    for state, label, note in checks():
        tag = {"ok": OK, "warn": c("1;33", "!! "), "bad": BAD, "info": INFO}[state]
        bad += state == "bad"
        print(f"  {tag} {label}" + (f"  — {note}" if note else ""))
    print("\nall good" if not bad else f"\n{bad} to fix")
    return 1 if bad else 0


def as_json(with_system: bool) -> int:
    """the same as status/doctor, for the shell (serp «pc-kit» panel): one JSON object on stdout"""
    off = disabled()
    patches = []
    for p, state, note in patch_states():
        patches.append({"name": p.name, "desc": p.desc, "kind": type(p).__name__, "state": state,
                        "note": note, "disabled": p.name in off,
                        "files": [str(f) for f in watch_paths(p)]})
    bad = sum(1 for x in patches if x["state"] != "on" and not x["disabled"])
    system = []
    if with_system:
        for state, label, note in checks():
            system.append({"state": state, "label": label, "note": note})
        bad += sum(1 for x in system if x["state"] == "bad")
    warn = sum(1 for x in system if x["state"] == "warn")
    print(json.dumps({"time": int(time.time()), "bad": bad, "warn": warn,
                      "patches": patches, "system": system}, ensure_ascii=False))
    return 1 if bad else 0


def cmd_watch_files():
    seen = []
    for p in PATCHES:
        for f in watch_paths(p):
            if f not in seen:
                seen.append(f)
    return seen


def cmd_install_watcher():
    u = HOME / ".config/systemd/user"
    me = Path(__file__).resolve()
    lines = ["[Unit]", "Description=pc-kit: put our patches back after an angelOS update", "", "[Path]"]
    lines += [f"PathChanged={f}" for f in cmd_watch_files()]
    lines += ["Unit=kit-update.service", "", "[Install]", "WantedBy=default.target"]
    (u / "kit-update.path").write_text("\n".join(lines) + "\n")
    (u / "kit-update.service").write_text("\n".join([
        "[Unit]", "Description=pc-kit: kit apply --after-update", "",
        "[Service]", "Type=oneshot", f"ExecStart=/usr/bin/python3 -I {me} apply --after-update", ""]) + "\n")
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    subprocess.run(["systemctl", "--user", "enable", "--now", "kit-update.path"])
    print(f"kit-update.path: {len(cmd_watch_files())} files watched")


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "status"
    if cmd == "inventory":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import inventory
        print(json.dumps(inventory.build(sys.modules[__name__]), ensure_ascii=False))
        return
    if cmd == "diff":
        if len(a) < 2:
            sys.exit("kit diff ID (patch:NAME | niri:00NN | satellite:00NN | audit:~/path)")
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import inventory
        print(json.dumps(inventory.diff_json(sys.modules[__name__], a[1]), ensure_ascii=False))
        return
    if cmd in ("status", "doctor") and "--json" in a:
        sys.exit(as_json(cmd == "doctor"))
    if cmd == "status":
        sys.exit(cmd_status())
    if cmd == "doctor":
        sys.exit(cmd_doctor())
    if cmd == "list":
        for p in PATCHES:
            print(f"{p.name:20s} {p.desc}")
        return
    if cmd == "apply":
        names = [x for x in a[1:] if not x.startswith("--")]
        unknown = [n for n in names if n not in BY]
        if unknown:
            sys.exit(f"unknown: {', '.join(unknown)} (kit list)")
        sys.exit(do_apply(names, after_update="--after-update" in a, tell="--notify" in a))
    if cmd == "revert":
        names = [x for x in a[1:] if not x.startswith("--")]
        if len(names) != 1 or names[0] not in BY:
            sys.exit("kit revert NAME (kit list)")
        p = BY[names[0]]
        set_disabled(p.name, True)
        r = p.revert()
        print((r.stdout + r.stderr).strip())
        if "--notify" in a:
            st, _ = p.check()
            notify("pc-kit", f"снято: {p.name} (как у автора)" if st != "on" else f"не снялось: {p.name} — {(r.stdout + r.stderr).strip()[-160:]}")
        for cmd2 in p.after:
            subprocess.run(cmd2, shell=True)
        if p.restarts_shell:
            restart_shell()
        return
    if cmd == "watch-files":
        for f in cmd_watch_files():
            print(f)
        return
    if cmd == "install-watcher":
        cmd_install_watcher()
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
