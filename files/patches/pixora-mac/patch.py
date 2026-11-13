#!/usr/bin/env python3
"""VM-патч angelOS: Golden Gate (мак-режим) с выключенными «значками MacTahoe» берёт свои
иконки пользователя (angelos-folders-b → pixora), а не Adwaita: GTK, Qt, Strata и кнопки дока.

  patch.py apply    поставить (уже стоящие куски пропускаются)
  patch.py revert   вернуть как у автора
  patch.py check    0 = всё стоит, 1 = нет
Печатает по строке на кусок; в конце «changed-qml», если правился QML (шеллу нужен restart).
"""
import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"

# «включены ли значки MacTahoe»: из палитры (ThemeExport), иначе из settings.json
HELPER = '''def mac_icons(pal):  # vm-patch pixora-mac: Golden Gate → «значки MacTahoe» (палитра, иначе settings.json)
    if "macIcons" in pal:
        return pal["macIcons"] != ""
    try:
        return json.loads((HOME / ".config/angelos/settings.json").read_text()).get("mac", {}).get("dockMacIcons", True)
    except (OSError, ValueError, AttributeError):
        return True


'''

# предыдущая тема иконок пользователя (до мак-режима): её запомнил goldengate.py
OWN = '''HOME / ".local/state/angelos/goldengate-before.json"'''

SUBS = [
    ("services/ThemeExport.qml",
     '''            "skin": "goldengate",
            "macBinds": "",''',
     '''            "skin": "goldengate",
            // vm-patch pixora-mac: «значки MacTahoe» выключены → свои иконки (pixora), не Adwaita
            "macIcons": Config.mac.dockMacIcons ? "1" : "",
            "macBinds": "",'''),

    ("scripts/goldengate.py",
     '''def wanted():
    fams = families()''',
     HELPER + '''def wanted(mac=True):
    fams = families()'''),
    ("scripts/goldengate.py",
     '''    if icon_theme_here("Adwaita"):
        want["icon-theme"] = "Adwaita"
    return want''',
     '''    if mac and icon_theme_here("Adwaita"):
        want["icon-theme"] = "Adwaita"
    elif not mac:  # vm-patch pixora-mac: свои иконки — папки в цветах Golden Gate (folder-tint.py), иначе тема до мак-режима
        cur = (gsettings("icon-theme") or "").strip("'")
        before = json.loads(STATE.read_text())["gsettings"].get("icon-theme") if STATE.exists() else cur
        before = (before or "").strip("'")
        if (cur.startswith("angelos-folders-mac-") or cur in ("pixora", "pixora-dark")) and icon_theme_here(cur):
            want["icon-theme"] = cur
        elif before and before != "Adwaita":
            want["icon-theme"] = before
    return want'''),
    ("scripts/goldengate.py",
     '''def on():
    want = wanted()''',
     '''def on(mac=True):  # vm-patch pixora-mac
    want = wanted(mac)'''),
    ("scripts/goldengate.py",
     '''    if pal.get("skin") == "goldengate":
        on()''',
     '''    if pal.get("skin") == "goldengate":
        on(mac_icons(pal))  # vm-patch pixora-mac'''),

    ("scripts/qt-theme.py",
     '''def set_conf(on, mac=False):''',
     HELPER + '''def set_conf(on, mac=False, mac_ic=True):  # vm-patch pixora-mac'''),
    ("scripts/qt-theme.py",
     '''        if any((d / "Adwaita/index.theme").exists() for d in (HOME / ".local/share/icons", Path("/usr/share/icons"))):
            mac_want[("Appearance", "icon_theme")] = "Adwaita"''',
     '''        if not mac_ic:  # vm-patch pixora-mac: тема иконок, что была до мак-режима (у Qt своей нет — GTK-шная)
            prev = json.loads(keep_mac.read_text()).get("Appearance/icon_theme") if keep_mac.exists() else None
            gg = ''' + OWN + '''
            if not prev and gg.exists():
                prev = (json.loads(gg.read_text())["gsettings"].get("icon-theme") or "").strip("'") or None
            try:  # the folders in Golden Gate's colours (folder-tint.py) when they are on
                cur = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "icon-theme"], capture_output=True, text=True).stdout.strip().strip("'")
            except OSError:
                cur = ""
            if cur.startswith("angelos-folders-mac-") or cur in ("pixora", "pixora-dark"):
                prev = cur
            if prev:
                mac_want[("Appearance", "icon_theme")] = prev
        elif any((d / "Adwaita/index.theme").exists() for d in (HOME / ".local/share/icons", Path("/usr/share/icons"))):
            mac_want[("Appearance", "icon_theme")] = "Adwaita"'''),
    ("scripts/qt-theme.py",
     '''    set_conf(True, mac)''',
     '''    set_conf(True, mac, mac_icons(pal))  # vm-patch pixora-mac'''),

    ("scripts/folder-tint.py",
     '''def apply(palette):
    if palette.get("skin") == "goldengate":
        strata_icons([])''',
     HELPER + '''MAC_OURS = ("angelos-folders-mac-a", "angelos-folders-mac-b")  # vm-patch pixora-mac


def mac_qt(name):
    """Qt apps' icon theme (qt6ct) to the same one (qt-theme.py runs before this hook)"""
    conf = CONFIG / "qt6ct/qt6ct.conf"
    if conf.exists():
        text = conf.read_text()
        new = re.sub(r"^icon_theme=.*$", f"icon_theme={name}", text, flags=re.M)
        if new != text:
            conf.write_text(new)


def mac_folders(palette):
    """vm-patch pixora-mac: Golden Gate without MacTahoe's icons — the user's Pixora with its folders in
    Golden Gate's colours, the pixel theme's logic: a tinted copy in angelos-folders-mac-a/-b (the name
    swaps on every change, so GTK apps reload live), the icon theme for GTK, Qt and Strata. The pixel
    theme's own angelos-folders-a/-b stay as they are for when it comes back"""
    gg = HOME / ".local/state/angelos/goldengate-before.json"
    own = (json.loads(gg.read_text())["gsettings"].get("icon-theme") or "").strip("'") if gg.exists() else current()
    base = base_of(own)
    if base not in BASES or not theme_dirs(base):
        strata_icons([])
        return f"icon theme {own or '?'} is not Pixora: folders left alone"
    cur = current()
    tint = palette.get("folderTint") or "pixora"
    if tint == "pixora":
        if cur != base:
            set_theme(base)
        mac_qt(base)
        for name in MAC_OURS:
            shutil.rmtree(ICONS / name, ignore_errors=True)
        strata_icons([base])
        return f"Golden Gate: folders as Pixora draws them ({base})"
    fill = (palette.get("folderFill") or "#" + BODY).lstrip("#")[:6]
    shade = (palette.get("folderShade") or "#" + SHADE).lstrip("#")[:6]
    stamp = ICONS / ".angelos-folders-mac"
    want = f"{base} {fill} {shade}"
    if cur in MAC_OURS and stamp.is_file() and stamp.read_text() == want and theme_dirs(cur):
        mac_qt(cur)
        strata_icons([cur, base])
        return f"Golden Gate: folders {fill} already ({cur})"
    name = MAC_OURS[1] if cur == MAC_OURS[0] else MAC_OURS[0]
    n = build(name, base, fill, shade)
    stamp.write_text(want)
    set_theme(name)
    mac_qt(name)
    shutil.rmtree(ICONS / (MAC_OURS[0] if name == MAC_OURS[1] else MAC_OURS[1]), ignore_errors=True)
    strata_icons([name, base])
    return f"Golden Gate: folders {fill}/{shade}: {n} icons in {name} over {base}"


def apply(palette):
    if palette.get("skin") == "goldengate":
        if not mac_icons(palette):  # vm-patch pixora-mac: папки в цветах Golden Gate, как в пиксельной теме
            return mac_folders(palette)
        strata_icons([])'''),

    # Док: «Приложения», «Настройки», «Загрузки», «Корзина» без значков MacTahoe — из темы иконок
    # (angelos-dock-*: свои pixora от Codex), пока тема их даёт; иначе нарисованные доком, как у автора
    ("modules/mac/MacDock.qml",
     '''            readonly property bool drawn: !cell.mac && !appIcon.badge && (cell.item.kind !== "app" && !cell.isWin || appIcon.status === Image.Error || appIcon.source.toString() === "")''',
     '''            readonly property bool drawn: !cell.mac && !appIcon.badge && (cell.item.kind !== "app" && !cell.isWin && appIcon.source.toString() === "" || appIcon.status === Image.Error || appIcon.source.toString() === "")  // vm-patch pixora-mac'''),
    ("modules/mac/MacDock.qml",
     '''                visible: !cell.mac && (cell.item.kind === "settings" || cell.item.kind === "apps")''',
     '''                visible: !cell.mac && art.drawn && (cell.item.kind === "settings" || cell.item.kind === "apps")  // vm-patch pixora-mac'''),
    ("modules/mac/MacDock.qml",
     '''                    const n = String(cell.item.icon || "");
                    if (cell.item.kind !== "app" && !cell.isWin || !n)
                        return "";''',
     '''                    const n = String(cell.item.icon || "");
                    // vm-patch pixora-mac: the Dock's own items from the icon theme (angelos-dock-*), when it has them
                    if (cell.item.kind !== "app" && !cell.isWin)
                        return Quickshell.iconPath("angelos-dock-" + (cell.item.kind === "trash" && n === "user-trash-full" ? "trash-full" : cell.item.kind), true) || "";
                    if (!n)
                        return "";'''),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    texts = {f: (SHELL / f).read_text() for f in {s[0] for s in SUBS} if (SHELL / f).exists()}
    missing = changed_qml = 0
    for f, old, new in (SUBS if mode != "revert" else list(reversed(SUBS))):
        s = texts.get(f)
        if s is None:
            print(f"нет файла {f}"); missing += 1; continue
        if mode == "revert":
            if new in s:
                texts[f] = s.replace(new, old, 1); print(f"откат {f}")
            continue
        if new in s:
            print(f"уже стоит {f}")
        elif s.count(old) == 1:
            if mode == "apply":
                texts[f] = s.replace(old, new, 1); print(f"поставлен {f}")
                changed_qml |= f.endswith(".qml")
            else:
                missing += 1
        else:
            print(f"ВНИМАНИЕ: {f} у автора изменился, кусок не найден — не встал"); missing += 1
    if mode == "check":
        sys.exit(1 if missing else 0)
    for f, s in texts.items():
        p = SHELL / f
        if p.read_text() != s:
            if f.endswith(".py"):
                compile(s, str(p), "exec")
            p.write_text(s)
            changed_qml |= f.endswith(".qml") and mode == "revert"
    if changed_qml:
        print("changed-qml")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
