#!/usr/bin/env python3
"""serp-skin (Celestia, local only, never pushed): the Golden Gate skin in the Serpantinum look.
Config.mac.look = "serp" turns it on (Golden Gate must be the skin). Flat dark surfaces leaning to
the wallpaper, a pastel accent from it, JetBrains Mono, smaller radii, and SerpBar (three floating
islands) instead of the menu bar. Hell keeps hell's colours.

  apply.py [apply] | check | revert        ANGELOS_SHELL=<dir> works on a copy
Every hunk is an exact OLD -> NEW that must occur once; revert puts OLD back (other patches that
share these files — mac-tint, skin-morph, dock-spacing — are left alone). No hunk may sit inside
another patch's text: kit's watcher then thinks that patch is gone and applies it AGAIN (2026-11-13:
skin-morph and mac-tint got doubled, the shell died). After any change: run every kit check.
"""
import os, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHELL = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos")
MARK = "serp-skin"

HUNKS = {
    "config/SettingsSchema.qml": [
        # after appMenus: no other patch's text spans these lines (mac-tint owns wallpaperTint/-Accent)
        ("        property bool appMenus: true        // the focused app's own menus in the menu bar (scripts/appmenu.py)\n",
         "        property bool appMenus: true        // the focused app's own menus in the menu bar (scripts/appmenu.py)\n"
         "        property string look: \"mac\"         // serp-skin: \"mac\" | \"serp\" (the Serpantinum look)\n"),
    ],
    "services/GoldenGate.qml": [
        # after hell, not after on: skin-morph checks itself by "on: chosen" + its morphHandler
        ("    readonly property bool hell: on && Angel.demon\n",
         "    readonly property bool hell: on && Angel.demon\n"
         "    readonly property bool serp: on && Config.mac.look === \"serp\"  // serp-skin\n"),
        ("    readonly property bool dark: hell || Theme.dark\n",
         "    readonly property bool dark: hell || serp || Theme.dark  // serp-skin: always dark\n"),
        ("    readonly property int barHeight: px(24)\n",
         "    readonly property int barHeight: serp ? px(36) : px(24)  // serp-skin: islands 30 + 6\n"),
        ("    readonly property int menuRadius: px(12)\n",
         "    readonly property int menuRadius: serp ? px(10) : px(12)  // serp-skin\n"),
        ("    readonly property int panelRadius: px(26)",
         "    readonly property int panelRadius: serp ? px(14) : px(26)  // serp-skin"),
        ("    readonly property string font: Theme.macFont\n",
         "    readonly property string font: serp ? Theme.macMono : Theme.macFont  // serp-skin: mono\n"),
        ("    readonly property color accent: hell ? Theme.hellAccent : Theme.macAccent\n"
         "    readonly property color accentText: \"#ffffff\"\n",
         "    readonly property color accent: hell ? Theme.hellAccent : serp ? serpAccent : Theme.macAccent\n"
         "    readonly property color accentText: serp && !hell ? \"#141414\" : \"#ffffff\"  // serp-skin\n"
         "    // serp-skin: the wallpaper's accent made pastel, the flat base the islands and panels stand on\n"
         "    readonly property color serpAccent: Theme.mix(Theme.macAccent, Qt.rgba(1, 1, 1, 1), 0.32)\n"
         "    readonly property color serpBase: glass(0)\n"
         "    readonly property color serpRed: \"#e5787a\"\n"),
        ("    readonly property bool glassFx: on && !reduceTransparency && !gameMode && !hell\n",
         "    readonly property bool glassFx: on && !serp && !reduceTransparency && !gameMode && !hell  // serp-skin: flat\n"),
        ("        const a = (blurOn ? 0.26 + tint * 0.62 : 0.94) + (extra || 0);\n",
         "        const a = (blurOn ? 0.26 + tint * 0.62 : 0.94) + (extra || 0);\n"
         "        if (serp && !hell) {  // serp-skin: flat, nearly solid, a breath of the wallpaper\n"
         "            const f = Theme.mix(Qt.rgba(0.075, 0.078, 0.085, 1), Theme.macSeed, 0.10);\n"
         "            return Qt.rgba(f.r, f.g, f.b, Math.min(0.97, (blurOn ? 0.86 : 0.96) + (extra || 0)));\n"
         "        }\n"),
    ],
    "modules/mac/MacDesktop.qml": [
        ("        MacMenuBar {\n            modelData: scope.modelData\n        }\n",
         "        // serp-skin: the islands instead of the menu bar in the Serpantinum look\n"
         "        LazyLoader {\n            active: !GoldenGate.serp\n"
         "            MacMenuBar {\n                modelData: scope.modelData\n            }\n        }\n"
         "        LazyLoader {\n            active: GoldenGate.serp\n"
         "            SerpBar {\n                modelData: scope.modelData\n            }\n        }\n"),
    ],
    # serp keeps the windows' own mode (the Strip by default) — Golden Gate proper is always Desktop
    "services/WindowConfig.qml": [
        ("    readonly property bool floatAll: GoldenGate.on || Config.windows.floatAll\n",
         "    readonly property bool floatAll: (GoldenGate.on && !GoldenGate.serp) || Config.windows.floatAll  // serp-skin: Strip stays\n"),
    ],
    # the skin-morph plugin (installed copy): no Strip -> Desktop throw into or out of serp
    "~/.config/angelos/plugins/skin-morph/Main.qml": [
        ("        if (Niri.nativeMinimize && !Config.windows.floatAll && mem) {\n",
         "        const serpSide = Config.mac.look === \"serp\";  // serp-skin: the windows keep their mode\n"
         "        if (Niri.nativeMinimize && !Config.windows.floatAll && mem && !serpSide) {\n"),
        ("        if (Niri.nativeMinimize && WindowConfig.deskThrow && !Config.windows.floatAll) {\n",
         "        if (Niri.nativeMinimize && WindowConfig.deskThrow && !Config.windows.floatAll && !serpSide) {\n"),
    ],
    "services/DesktopWidgets.qml": [
        ("        value: root.weatherWanted || Halo.weatherWanted || StartPrefs.current === \"tiles\"",
         "        value: root.weatherWanted || Halo.weatherWanted || StartPrefs.current === \"tiles\" || GoldenGate.serp  // serp-skin"),
    ],
}
NEW_FILES = {"modules/mac/SerpBar.qml": HERE / "qml/SerpBar.qml"}


def path(rel):
    return Path(rel).expanduser() if rel.startswith("~/") else SHELL / rel


def applied(rel):
    t = path(rel).read_text()
    return all(new in t for _, new in HUNKS[rel])


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if mode == "check":
        ok = all(applied(r) for r in HUNKS) and all((SHELL / r).exists() for r in NEW_FILES)
        sys.exit(0 if ok else 1)
    if mode == "revert":
        for rel, hunks in HUNKS.items():
            f = path(rel)
            t = f.read_text()
            for old, new in hunks:
                if new in t:
                    t = t.replace(new, old, 1)
            f.write_text(t)
        for rel in NEW_FILES:
            (SHELL / rel).unlink(missing_ok=True)
        print("reverted")
        return
    # apply: check every hunk fits before touching anything
    texts = {}
    for rel, hunks in HUNKS.items():
        t = path(rel).read_text()
        for old, new in hunks:
            if new in t:
                continue
            if t.count(old) != 1:
                print(f"does not fit: {rel}: {old.strip()[:70]!r} found {t.count(old)}x")
                sys.exit(2)
            t = t.replace(old, new, 1)
        texts[rel] = t
    for rel, t in texts.items():
        if path(rel).read_text() != t:
            path(rel).write_text(t)
    for rel, src in NEW_FILES.items():
        shutil.copy2(src, SHELL / rel)
    print("applied")


if __name__ == "__main__":
    main()
