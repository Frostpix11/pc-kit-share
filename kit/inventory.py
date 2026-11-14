"""inventory — what every pc-kit piece changed against the author's angelOS, proven by undoing it.

For each file we touch: take the file as it is now, undo every «было → стало» pair our patches
know (the pairs are read out of the patches themselves), and compare with the author's original
in ~/AngelOS-Dotfiles (git, the commit we stand on). Equal → every difference is ours and
accounted for. Not equal → what is left is a change no patch explains (shown as a diff).

Used by kit.py (`kit inventory --json`, `kit diff NAME`). Celestia, 2026-11-14.
"""
from __future__ import annotations

import difflib
import importlib.util
import io
import os
import re
import subprocess
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

HOME = Path.home()
AUTHOR = HOME / "AngelOS-Dotfiles"


# ------------------------------------------------------------------ the author's side
def author_rev() -> str:
    r = subprocess.run(["git", "-C", str(AUTHOR), "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip()


def author_text(path: Path) -> str | None:
    """the author's version of a file we have at `path` (None: not the author's file)"""
    try:
        rel = Path(path).resolve().relative_to(HOME) if not Path(path).is_symlink() else Path(path).relative_to(HOME)
    except ValueError:
        return None
    a = AUTHOR / rel
    try:
        return a.read_text()
    except (OSError, UnicodeDecodeError):
        return None


def fill_placeholders(text: str) -> str:
    """the installer writes the author's @HOME@ etc. as this machine's values"""
    return text.replace("@HOME@", str(HOME))


# ------------------------------------------------------------------ our side: the pairs
def _load(path: Path, name: str):
    """import a patch script as a module (they all keep their work under `if __name__ == "__main__"`)"""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    old_argv, old_path = sys.argv, list(sys.path)
    sys.argv = [str(path)]
    sys.path.insert(0, str(path.parent))
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            spec.loader.exec_module(mod)
    finally:
        sys.argv, sys.path[:] = old_argv, old_path
    return mod


def _is_rel(s) -> bool:
    return isinstance(s, str) and "\n" not in s and len(s) < 160 and bool(re.search(r"\.(qml|js|json|py|sh|kdl|frag|vert)$|^bin:|/", s))


def _walk_pairs(obj, out: list, depth=0, rel=None):
    """every (old, new, file|None) of strings inside a patch's data: tuples (old, new),
    (file, old, new), dicts {file: [...]} of them"""
    if depth > 5:
        return
    if isinstance(obj, (tuple, list)) and len(obj) in (2, 3) and all(isinstance(x, str) for x in obj):
        old, new = obj[-2], obj[-1]
        r = obj[0] if len(obj) == 3 and _is_rel(obj[0]) else rel
        if old != new and len(new) > 8:
            out.append((old, new, r))
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            _walk_pairs(v, out, depth + 1, k if _is_rel(k) else rel)
    elif isinstance(obj, (tuple, list)):
        for v in obj:
            _walk_pairs(v, out, depth + 1, rel)


def _git_patch_pairs(text: str) -> list:
    """a unified diff → (old, new, file) a hunk: context and − lines vs context and + lines"""
    pairs, old, new, inside, rel = [], [], [], False, None
    def flush():
        if inside and old != new:
            pairs.append(("".join(old), "".join(new), rel))
    for line in text.splitlines(keepends=True):
        if line.startswith("+++ "):
            rel = line[4:].strip().removeprefix("b/")
        if line.startswith("@@"):
            flush()
            old, new, inside = [], [], True
        elif line.startswith(("diff --git", "--- ", "+++ ", "index ")):
            flush()
            old, new, inside = [], [], False
        elif inside:
            tag, body = line[:1], line[1:]
            if tag == " ":
                old.append(body); new.append(body)
            elif tag == "-":
                old.append(body)
            elif tag == "+":
                new.append(body)
            elif tag == "\\":
                pass
    flush()
    return pairs


def patch_pairs(p, kit_dir: Path) -> list:
    """the (old, new) pairs of one kit patch, read out of its own files"""
    out: list = []
    d = p.dir
    name = type(p).__name__
    try:
        if name == "SerpSkin" or p.name == "serp-skin":
            mod = _load(kit_dir / "files/serp-skin/apply.py", "kitinv_serp")
            _walk_pairs(getattr(mod, "HUNKS", {}), out)
            return out
        if name == "GitPatches":
            for f in sorted(d.glob("*.patch")):
                out += _git_patch_pairs(f.read_text())
            return out
        if name == "Privacy":
            for new in sorted((d / "rec").glob("*-new.txt")):
                old = new.with_name(new.name.replace("-new", "-old"))
                if old.exists():
                    out.append((old.read_text(), new.read_text(), "bin:niri-record-region"))
            # the cast rule: OLD / NEW are bash strings in apply.sh — let bash itself read them
            sh = (d / "apply.sh").read_text()
            m = re.search(r"^OLD=.*?(?=^if )", sh, re.S | re.M)
            if m:
                r = subprocess.run(["bash", "-c", m.group(0) + '\nprintf "%s\\0%s" "$OLD" "$NEW"'], capture_output=True, text=True)
                o, _, n = r.stdout.partition("\0")
                if o and n:
                    out.append((o, n, "bin:niri-cast-privacy"))
            for extra in ("settings.py", "rec-switch.py"):
                if (d / extra).exists():
                    mod = _load(d / extra, "kitinv_" + p.name.replace("-", "_") + extra[:-3].replace("-", "_"))
                    for k, v in vars(mod).items():
                        if not k.startswith("_") and not callable(v):
                            _walk_pairs(v, out)
            return out
        script = d / ("apply.py" if (d / "apply.py").exists() else "patch.py")
        mod = _load(script, "kitinv_" + p.name.replace("-", "_"))
        for k, v in vars(mod).items():
            if k.startswith("_") or callable(v) or k in ("OLD", "NEW"):
                continue
            _walk_pairs(v, out)
        if isinstance(getattr(mod, "OLD", None), str) and isinstance(getattr(mod, "NEW", None), str):
            out.append((mod.OLD, mod.NEW, None))
    except Exception as e:  # noqa — a patch we can't read is reported, not fatal
        out.append(("", f"<unreadable: {e}>", None))
    return out


# ------------------------------------------------------------------ proving
def pair_fits(rel: str | None, path: Path, shell: Path, bindir: Path) -> bool:
    """a pair that names its file applies only there"""
    if not rel:
        return True
    if rel.startswith("bin:"):
        return Path(path) == bindir / rel[4:]
    if rel.startswith("~/"):
        return Path(path) == Path(rel).expanduser()
    return str(path).endswith("/" + rel.lstrip("/"))


def undo(text: str, pairs: list[tuple[str, str, str]]) -> tuple[str, list[str]]:
    """undo every (patch, old, new) whose `new` is in the text (later patches first, several
    passes for nested ones); returns the text and the names of the patches that had something here"""
    used: list[str] = []
    for _ in range(4):
        changed = False
        for name, old, new in reversed(pairs):
            if new and new in text and not (old and old in text and new in old):
                text = text.replace(new, old, 1)
                changed = True
                if name not in used:
                    used.append(name)
        if not changed:
            break
    return text, used


def udiff(a: str, b: str, name: str, ctx=2, limit=400) -> str:
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(), "автор/" + name, "сейчас/" + name, n=ctx, lineterm=""))
    if len(lines) > limit:
        lines = lines[:limit] + [f"… ещё {len(lines) - limit} строк"]
    return "\n".join(lines)


def stat(a: str, b: str) -> tuple[int, int]:
    plus = minus = 0
    for l in difflib.unified_diff(a.splitlines(), b.splitlines(), n=0, lineterm=""):
        if l.startswith("+") and not l.startswith("+++"):
            plus += 1
        elif l.startswith("-") and not l.startswith("---"):
            minus += 1
    return plus, minus


COLOR = re.compile(r"#[0-9a-fA-F]{6,8}\b|\b\d{1,3};\d{1,3};\d{1,3}\b|\b0\.\d{3}\b")


def only_colours(a: str, b: str) -> bool:
    """the difference is only theme colours (angelOS writes them from the wallpaper)"""
    return COLOR.sub("C", a) == COLOR.sub("C", b)


# the author's config files that differ outside our patches: who changed them (Celestia read each
# diff on 2026-11-14). who: angelos = angelOS itself (Settings, theme, skin, installer answers),
# apps = programs, ours = we did it by hand, you = yours
KNOWN = {
    "~/.config/fastfetch/config.jsonc": ("angelos", "цвета темы из обоев и подпись окна fastfetch"),
    "~/.config/fish/config.fish": ("you", "твой конфиг fish: автор разрешает его менять, обновления сливают свои строки"),
    "~/.config/foot/themes/angelos": ("angelos", "цвета темы из обоев"),
    "~/.config/gtk-3.0/bookmarks": ("you", "закладка /mnt/game в файловом менеджере"),
    "~/.config/gtk-4.0/bookmarks": ("you", "закладка /mnt/game в файловом менеджере"),
    "~/.config/gtk-3.0/settings.ini": ("angelos", "курсор скина serp и кнопка «свернуть» в заголовках (Настройки)"),
    "~/.config/gtk-4.0/settings.ini": ("angelos", "курсор скина serp и кнопка «свернуть» в заголовках (Настройки)"),
    "~/.config/gtk-4.0/angelos.css": ("angelos", "цвета темы из обоев"),
    "~/.config/mimeapps.list": ("apps", "программы записали себя: freshGram, Thunderbird"),
    "~/.config/niri/cfg/keybinds-pixel.kdl": ("angelos", "профиль клавиш angelOS: столы через скрипт angelos"),
    "~/.config/niri/monitor.kdl": ("angelos", "настройки монитора (165 Гц) из Настроек"),
    "~/.config/niri/cfg/animation.kdl": ("angelos", "скорость анимаций из Настроек и цвет темы"),
    "~/.config/niri/cfg/input.kdl": ("angelos", "раскладка из установщика (us,ru, Caps) и мышь без ускорения (flat) из Настроек"),
    "~/.config/niri/cfg/misc.kdl": ("angelos", "курсор скина serp, Qt через qt6ct (так пишет angelOS)"),
    "~/.config/niri/config.kdl": ("angelos", "подключения angelOS: окна, сворачивание, ноутбук"),
    "~/.config/spicetify/config-xpui.ini": ("angelos", "spicetify-apply angelOS: свои цвета + marketplace"),
    "~/.config/user-dirs.dirs": ("you", "папки Шаблоны/Общие/Проекты убраны"),
    "~/.config/voxtype/config.toml": ("ours", "голосовой ввод: язык ru, GPU-изоляция, без OSD (2026-11-01)"),
    "~/.config/niri/angelos.kdl": ("angelos", "цвета рамок окон из обоев"),
}
WHO = {"angelos": "angelOS сам", "apps": "программы", "ours": "мы вручную", "you": "ты", "": "неизвестно, проверь"}


# ------------------------------------------------------------------ the whole picture
NIRI_DESC = {
    "0001": "Окна в стекинге: прилипание к половинам, четвертям и третям экрана, подглядывание за окном, скрытие окон и слоёв",
    "0002": "Живой курсор: покачивание, размытие в движении, отскок, тень",
    "0003": "Камера за курсором: зум экрана, который плавно следует за указателем (Super+Ctrl+Shift+U)",
    "0004": "Живой курсор и для собственных курсоров программ (Steam, игры Wine/Proton, X11)",
    "0005": "Стол 0, пульс, прозрачность окна точками по Alt+колесо, подглядывание: под оболочку c4795df",
    "0006": "Стол 0 без паники: компоситор чинит странное состояние вместо падения",
    "0007": "Закреп окна помнит номер стола и при включённом столе 0",
    "0008": "Курсор подпрыгивает в такт музыке",
    "0009": "Пипетка без зависания: камера не блокирует снимок экрана",
    "0010": "Окна на невидимых столах засыпают (suspend): меньше нагрузки, +FPS в играх",
    "0011": "Засыпают и невидимые окна на текущем столе: за кадром, под вкладкой, под полноэкранным",
    "0012": "Явная синхронизация (explicit sync) для NVIDIA: Xwayland не копирует каждый кадр игры (ANGEL_NIRI_SYNCOBJ=1)",
    "0013": "Explicit sync для окон + трассировка кадров для диагностики (ANGEL_NIRI_SYNC_TRACE=1)",
    "0014": "Тиринг без ограничения частотой (по желанию, ANGEL_NIRI_TEAR_UNTHROTTLED=1; замер: хуже, выключено)",
    "0015": "Закреп программы переживает смену заголовка до первого кадра (Strata открывалась не там)",
    "0016": "Блюр под панелями снимается сразу при закрытии (без «хвоста» с explicit sync)",
    "0017": "Живой курсор берёт картинку нужного размера из темы, а не растягивает маленькую",
}
SAT_DESC = {
    "0001": "Удержанное окно X11 рисуется в размере компоситора (CS2 в 4:3 без пересоздания)",
    "0002": "Невидимые окна X11 получают HIDDEN: Chromium/Electron перестают рисовать за кадром",
    "0003": "Тосты Steam показываются как отдельное окно в углу, а не висят на скрытом родителе",
}


def _git_log(kit_dir: Path, path: str, n=12) -> list[dict]:
    r = subprocess.run(["git", "-C", str(kit_dir), "log", f"-n{n}", "--format=%h%x09%as%x09%s", "--", path],
                       capture_output=True, text=True)
    out = []
    for line in r.stdout.splitlines():
        h, d, s = (line.split("\t", 2) + ["", ""])[:3]
        out.append({"hash": h, "date": d, "subject": s})
    return out


def _git_count(kit_dir: Path, path: str) -> int:
    r = subprocess.run(["git", "-C", str(kit_dir), "rev-list", "--count", "HEAD", "--", path], capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0


def _home(p) -> str:
    s = str(p)
    return "~" + s[len(str(HOME)):] if s.startswith(str(HOME)) else s


def kit_path(p, kit_dir: Path) -> str:
    """where a kit patch lives inside pc-kit (for its git history)"""
    if p.name == "serp-skin":
        return "files/serp-skin"
    return str(p.dir.relative_to(kit_dir)) if str(p.dir).startswith(str(kit_dir)) else f"files/patches/{p.name}"


class Prover:
    """the pairs of every patch, and the proof per file (cached)"""
    def __init__(self, kit):
        self.kit = kit
        self.pairs = {p.name: patch_pairs(p, kit.KIT) for p in kit.PATCHES}
        self.watch = {p.name: list(kit.watch_paths(p)) for p in kit.PATCHES}
        self._proof: dict = {}

    def pairs_for(self, f: Path, names=None):
        out = []
        for p in self.kit.PATCHES:
            if names is not None and p.name not in names:
                continue
            if f not in self.watch[p.name] and not any(r and pair_fits(r, f, self.kit.SHELL, self.kit.BIN) for _, _, r in self.pairs[p.name]):
                continue
            out += [(p.name, o, n) for o, n, r in self.pairs[p.name] if pair_fits(r, f, self.kit.SHELL, self.kit.BIN)]
        return out

    def proof(self, f: Path) -> dict:
        """{author: has the author this file, same: untouched, proven: all differences are ours,
        by: patches that changed it, left: (+, −) unexplained lines}"""
        if f in self._proof:
            return self._proof[f]
        A = author_text(f)
        try:
            C = Path(f).read_text()
        except (OSError, UnicodeDecodeError):
            C = None
        res = {"author": A is not None, "exists": C is not None, "same": False, "proven": False, "by": [], "left": [0, 0]}
        if A is not None and C is not None:
            A = fill_placeholders(A)
            if A == C:
                res.update(same=True, proven=True)
            else:
                R, used = undo(C, self.pairs_for(f))
                res["by"] = used
                res["proven"] = R == A
                if R != A:
                    res["left"] = list(stat(A, R))
        self._proof[f] = res
        return res

    def own_diff(self, name: str, f: Path) -> str:
        """only this patch's changes in this file: the file with just its pairs undone → now"""
        try:
            C = Path(f).read_text()
        except (OSError, UnicodeDecodeError):
            return ""
        R, _ = undo(C, self.pairs_for(f, {name}))
        return udiff(R, C, Path(f).name)

    def left_diff(self, f: Path) -> str:
        A = author_text(f)
        if A is None:
            return ""
        R, _ = undo(Path(f).read_text(), self.pairs_for(f))
        return udiff(fill_placeholders(A), R, Path(f).name)


def plugin_state(kit, prover: Prover, name: str, src: Path, dst: Path) -> tuple[str, str]:
    """installed plugin vs its copy in pc-kit; changes serp-skin makes on purpose don't count"""
    if not dst.exists():
        return "off", "не установлен"
    differ = []
    for s in sorted(x for x in src.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.name != "face.frag"):
        d = dst / s.relative_to(src)
        try:
            a, b = s.read_text(), d.read_text()
        except (OSError, UnicodeDecodeError):
            if not d.exists():
                differ.append(str(s.relative_to(src)))
            continue
        if a == b:
            continue
        R, _ = undo(b, prover.pairs_for(d, {"serp-skin"}))
        if R != a:
            differ.append(str(s.relative_to(src)))
    if differ:
        return "warn", "отличается от pc-kit: " + ", ".join(differ[:4])
    return "on", ""


def build(kit, states=None) -> dict:
    """everything pc-kit puts over angelOS, in groups, with the proof against the author"""
    t0 = __import__("time").time()
    kd = kit.KIT
    prover = Prover(kit)
    states = states or {p.name: (s, n) for p, s, n in kit.patch_states()}
    off = kit.disabled()
    groups = []

    # 1. the shell and its scripts: the kit patches
    items = []
    for p in kit.PATCHES:
        st, note = states.get(p.name, ("unfit", ""))
        files = []
        for f in prover.watch[p.name]:
            pr = prover.proof(f)
            mine = p.name in pr["by"]
            if not pr["author"] and not pr["exists"]:
                continue
            files.append({"path": _home(f), "name": Path(f).name, "author": pr["author"], "mine": mine or not pr["author"],
                          "proven": pr["proven"], "same": pr["same"], "others": [x for x in pr["by"] if x != p.name],
                          "left": pr["left"]})
        kp = kit_path(p, kd)
        items.append({"id": "patch:" + p.name, "name": p.name, "desc": p.desc, "state": st, "note": note,
                      "disabled": p.name in off, "kind": type(p).__name__, "restartsShell": bool(getattr(p, "restarts_shell", True)),
                      "canToggle": p.name != "serp-skin", "files": files,
                      "touched": sum(1 for f in files if f["mine"]), "proven": all(f["proven"] for f in files if f["mine"]),
                      "pairs": len(prover.pairs[p.name]), "source": kp,
                      "commits": _git_count(kd, kp), "history": _git_log(kd, kp)})
    groups.append({"id": "shell", "title": "Оболочка", "subtitle": "патчи файлов angelOS: QML и скрипты", "icon": "layers", "items": items})

    # 2. the compositor: niri and xwayland-satellite, our builds
    for gid, title, sub, d, desc, binname in (
            ("niri", "niri", "наши патчи компоситора, собираются build-niri.sh", kd / "files/angel-niri", NIRI_DESC, "niri"),
            ("satellite", "satellite", "xwayland-satellite: окна X11 и игры", kd / "files/angel-satellite", SAT_DESC, "xwayland-satellite")):
        build_dir = Path(os.path.realpath(kit.BIN / binname)).parent.name
        ours = "kit" in build_dir
        items = []
        for f in sorted(d.glob("00*.patch")):
            text = f.read_text()
            num = f.name[:4]
            files = sorted({l[6:].strip() for l in text.splitlines() if l.startswith("+++ b/")})
            plus = sum(1 for l in text.splitlines() if l.startswith("+") and not l.startswith("+++"))
            minus = sum(1 for l in text.splitlines() if l.startswith("-") and not l.startswith("---"))
            rel = str(f.relative_to(kd))
            items.append({"id": f"{gid}:{num}", "name": f.stem[5:], "num": num, "desc": desc.get(num, f.stem[5:].replace("-", " ")),
                          "state": "on" if ours else "off", "note": f"в сборке {build_dir}" if ours else f"сейчас стоит {build_dir}: пересобрать",
                          "disabled": False, "kind": "rust", "canToggle": False, "plus": plus, "minus": minus,
                          "files": [{"path": x, "name": Path(x).name, "author": True, "mine": True, "proven": True, "same": False, "others": [], "left": [0, 0]} for x in files],
                          "touched": len(files), "proven": True, "source": rel,
                          "commits": _git_count(kd, rel), "history": _git_log(kd, rel)})
        groups.append({"id": gid, "title": title, "subtitle": sub, "icon": "monitor" if gid == "niri" else "app-window", "items": items, "build": build_dir})

    # 3. plugins: ours whole (the author has none of them)
    items = []
    up = HOME / ".config/angelos/plugins"
    plug = [(p.name, p, up / p.name) for p in sorted((kd / "files/plugins").iterdir()) if p.is_dir()]
    for src_name, inst in (("AngelOS-Room", "angelos-room"), ("AngelOS-Typer", "angelos-typer")):
        plug.append((inst, kd / "files/codex-plugins" / src_name, up / inst))
    for name, src, dst in plug:
        man = {}
        for mf in (src / "manifest.json", dst / "manifest.json"):
            try:
                man = __import__("json").loads(mf.read_text())
                break
            except (OSError, ValueError):
                continue
        dname, ddesc = man.get("name", name), man.get("description", "")
        if isinstance(dname, dict):
            dname = dname.get("ru") or dname.get("en") or name
        if isinstance(ddesc, dict):
            ddesc = ddesc.get("ru") or ddesc.get("en") or ""
        if "codex-plugins" in str(src):
            st, note = ("on", "") if dst.exists() else ("off", "не установлен")
        else:
            st, note = plugin_state(kit, prover, name, src, dst)
        rel = str(src.relative_to(kd))
        nfiles = sum(1 for x in src.rglob("*") if x.is_file() and "__pycache__" not in x.parts)
        items.append({"id": "plugin:" + name, "name": name, "title": dname, "desc": ddesc, "state": st, "note": note,
                      "disabled": False, "kind": "plugin", "canToggle": False, "files": [], "touched": nfiles, "proven": True,
                      "source": rel, "commits": _git_count(kd, rel), "history": _git_log(kd, rel)})
    groups.append({"id": "plugins", "title": "Плагины", "subtitle": "целиком наши, у автора их нет", "icon": "puzzle", "items": items})

    # 4. the audit: the author's files that differ and belong to no patch
    claimed = set()
    for fs in prover.watch.values():
        claimed |= {Path(f) for f in fs}
    r = subprocess.run(["git", "-C", str(AUTHOR), "ls-files", "-z", "--", ".config", ".local"], capture_output=True)
    hand, theme, filled, missing = [], 0, 0, 0
    for rel in r.stdout.decode().split("\0"):
        if not rel:
            continue
        a, b = AUTHOR / rel, HOME / rel
        if b in claimed or a.is_symlink() or b.is_symlink():
            continue
        if not b.exists():
            missing += 1
            continue
        try:
            at, bt = a.read_text(), b.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if at == bt:
            continue
        af = fill_placeholders(at)
        if af == bt:
            filled += 1
            continue
        if only_colours(af, bt):
            theme += 1
            continue
        # placeholders the installer filled from questions (@KB_LAYOUT@…): equal once those lines go
        rest_a = [l for l in af.splitlines() if not re.search(r"@[A-Z_]+@", l)]
        pl, mi = stat(af, bt)
        who, why = KNOWN.get("~/" + rel, ("", ""))
        hand.append({"id": "audit:~/" + rel, "path": "~/" + rel, "name": Path(rel).name, "plus": pl, "minus": mi,
                     "who": who, "whoLabel": WHO[who], "note": why})
    audit = {"handEdits": hand, "theme": theme, "filled": filled, "missing": missing}

    # 5. the proof, summed up
    shell_files = [f for it in groups[0]["items"] for f in it["files"] if f["author"] and not f["same"]]
    uniq = {f["path"]: f for f in shell_files}
    proven = sum(1 for f in uniq.values() if f["proven"])
    return {"time": int(__import__("time").time()), "took": round(__import__("time").time() - t0, 2),
            "author": {"repo": _home(AUTHOR), "rev": author_rev()},
            "proof": {"files": len(uniq), "proven": proven, "unexplained": [f["path"] for f in uniq.values() if not f["proven"]]},
            "groups": groups, "audit": audit}


def diff_json(kit, item_id: str) -> dict:
    """the changes of one item, file by file (asked when its card opens)"""
    kd = kit.KIT
    kind, _, name = item_id.partition(":")
    out = {"id": item_id, "files": []}
    if kind == "patch":
        prover = Prover(kit)
        for f in prover.watch.get(name, []):
            pr = prover.proof(f)
            if not pr["exists"]:
                continue
            if not pr["author"]:
                try:
                    n = len(Path(f).read_text().splitlines())
                except (OSError, UnicodeDecodeError):
                    n = 0
                out["files"].append({"path": _home(f), "name": Path(f).name, "whole": True, "lines": n, "diff": ""})
                continue
            if name not in pr["by"]:
                continue
            out["files"].append({"path": _home(f), "name": Path(f).name, "whole": False, "diff": prover.own_diff(name, f),
                                 "left": prover.left_diff(f) if not pr["proven"] else ""})
    elif kind in ("niri", "satellite"):
        d = kd / ("files/angel-niri" if kind == "niri" else "files/angel-satellite")
        for f in d.glob(name + "-*.patch"):
            cur, buf = None, []
            for line in f.read_text().splitlines():
                if line.startswith("diff --git"):
                    if cur:
                        out["files"].append({"path": cur, "name": Path(cur).name, "whole": False, "diff": "\n".join(buf[:400])})
                    cur, buf = line.split(" b/")[-1], []
                elif cur:
                    buf.append(line)
            if cur:
                out["files"].append({"path": cur, "name": Path(cur).name, "whole": False, "diff": "\n".join(buf[:400])})
    elif kind == "audit":
        rel = name.removeprefix("~/")
        a, b = AUTHOR / rel, HOME / rel
        try:
            out["files"].append({"path": name, "name": Path(rel).name, "whole": False,
                                 "diff": udiff(fill_placeholders(a.read_text()), b.read_text(), Path(rel).name)})
        except (OSError, UnicodeDecodeError):
            pass
    return out
