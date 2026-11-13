#!/usr/bin/env python3
"""VM-патч angelOS «dock-spacing»: в Golden Gate отступы Дока настраиваются.

Настройки → Golden Gate → Dock: «Промежуток между значками» (Config.mac.dockSpacing, 0–40 px,
по умолчанию 5 — как у автора при значках 48) и «Поля вокруг значков» (Config.mac.dockPadding,
0–30 px, по умолчанию 7). У автора было icon*0.1 и icon*0.14. Оба входят в «Сбросить тему».

  patch.py apply | revert | check      печатает «changed-qml», если правился QML
"""
import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"
M = "  // vm-patch dock-spacing"

SUBS = [
    ("config/SettingsSchema.qml",
     '''        property int dockMagnifySize: 96    // the icon right under the pointer, logical px (dockSize..128)''',
     '''        property int dockMagnifySize: 96    // the icon right under the pointer, logical px (dockSize..128)
        property int dockSpacing: 5         // vm-patch dock-spacing: between the Dock's icons, logical px
        property int dockPadding: 7         // vm-patch dock-spacing: inside the slab around the icons, logical px'''),
    ("services/GoldenGate.qml",
     '''            "mac.dockMagnifySize": [32, 128],''',
     '''            "mac.dockMagnifySize": [32, 128],
            "mac.dockSpacing": [0, 40],''' + M + '''
            "mac.dockPadding": [0, 30],''' + M),
    # (author 2026-11-03: _watched is built from limits' keys, themeKeys is one key a line)
    ("services/GoldenGate.qml",
     '''
        "mac.dockMagnifySize",
''',
     '''
        "mac.dockMagnifySize",
        "mac.dockSpacing",''' + M + '''
        "mac.dockPadding",''' + M + '''
'''),
    ("modules/mac/MacDock.qml",
     '''    readonly property real gap: Math.round(icon * 0.1)          // between icons
    readonly property real pad: Math.round(icon * 0.14)         // inside the slab, around the icons''',
     '''    readonly property real gap: Math.round(GoldenGate.px(Config.mac.dockSpacing))   // between icons''' + M + '''
    readonly property real pad: Math.round(GoldenGate.px(Config.mac.dockPadding))   // inside the slab, around the icons''' + M),
    ("modules/settings/catalog/Mac.qml",
     '''            onMoved: v => Config.mac.dockMagnifySize = v
        }''',
     '''            onMoved: v => Config.mac.dockMagnifySize = v
        }
        CatSlider {''' + M + '''
            label: I18n.t("Промежуток между значками", "Space between icons")
            from: page.lim["mac.dockSpacing"][0]
            to: page.lim["mac.dockSpacing"][1]
            stepSize: 1
            value: Config.mac.dockSpacing
            suffix: " px"
            onMoved: v => Config.mac.dockSpacing = v
        }
        CatSlider {''' + M + '''
            label: I18n.t("Поля вокруг значков", "Padding around icons")
            hint: I18n.t("Отступ от значков до края подложки Dock.", "From the icons to the edge of the Dock's slab.")
            from: page.lim["mac.dockPadding"][0]
            to: page.lim["mac.dockPadding"][1]
            stepSize: 1
            value: Config.mac.dockPadding
            suffix: " px"
            onMoved: v => Config.mac.dockPadding = v
        }'''),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    files = {f for f, _, _ in SUBS}
    texts = {f: (SHELL / f).read_text() for f in files if (SHELL / f).exists()}
    missing = 0
    for f, old, new in (SUBS if mode != "revert" else list(reversed(SUBS))):
        s = texts.get(f)
        if s is None:
            print(f"нет файла {f}"); missing += 1; continue
        if mode == "revert":
            if new in s:
                texts[f] = s.replace(new, old, 1)
            continue
        if new in s:
            continue
        if s.count(old) == 1:
            if mode == "apply":
                texts[f] = s.replace(old, new, 1)
            else:
                missing += 1
        else:
            print(f"ВНИМАНИЕ: {f} у автора изменился, кусок не найден: {old.strip()[:70]}"); missing += 1
    if mode == "check":
        sys.exit(1 if missing else 0)
    changed = []
    for f, s in texts.items():
        p = SHELL / f
        if p.read_text() != s:
            p.write_text(s); changed.append(f)
    for f in changed:
        print(("откат " if mode == "revert" else "поставлен ") + f)
    if any(f.endswith(".qml") for f in changed):
        print("changed-qml")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
