#!/usr/bin/env python3
"""VM-патч angelOS «mac-tint»: Golden Gate (мак-режим) под цвет обоев — как «Из обоев» пиксельной темы.

Настройки → Golden Gate → Внешний вид → «Цвет из обоев» (Config.mac.wallpaperTint). Пока включено:
  · цвет берёт PaletteGenerator с текущих обоев (та же область картинки, ночь сцены), пишет его
    в Config.mac.wallpaperAccent — пиксельный Config.appearance.customAccent не трогается;
  · Theme: акцент (macAccent) — тон обоев в мак-яркости; поверхности (macBase) слегка тонированы;
  · GoldenGate: фон окон/контента/сайдбара и стекло (меню, Dock, Пункт управления) тонированы;
  · ThemeExport: GTK/Qt/терминалы/браузеры получают те же тонированные мак-цвета.
Смысловые цвета (светофор, красный, белый на акценте) не трогаются.

  patch.py apply | revert | check      печатает «changed-qml», если правился QML
"""
import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"
M = "  // vm-patch mac-tint"

SUBS = [
    # ---- settings: the toggle and the remembered colour ----
    ("config/SettingsSchema.qml",
     '''        property string accent: "blue"      // blue | purple | pink | red | orange | yellow | green | graphite''',
     '''        property string accent: "blue"      // blue | purple | pink | red | orange | yellow | green | graphite
        property bool wallpaperTint: false  // vm-patch mac-tint: the accent and a tint of everything from the wallpaper (PaletteGenerator)
        property string wallpaperAccent: "" // vm-patch mac-tint: the wallpaper's colour for Golden Gate, kept apart from appearance.customAccent'''),
    ("config/Config.qml",
     '''    readonly property var notUndoable: ["launcher.usage", ''',
     '''    readonly property var notUndoable: ["mac.wallpaperAccent", "launcher.usage", '''),
    ("services/GoldenGate.qml",
     '''
        "mac.accent",
''',
     '''
        "mac.accent",
        "mac.wallpaperTint",''' + M + '''
'''),  # (author 2026-11-03: themeKeys one key a line)
    ("modules/settings/catalog/Mac.qml",
     '''        CatChoice {
            label: I18n.t("Цвет акцента", "Accent colour")''',
     '''        CatToggle {''' + M + '''
            label: I18n.t("Цвет из обоев", "Colour from the wallpaper")
            hint: I18n.t("акцент, окна, меню, Dock, Пункт управления и программы (GTK, Qt, терминалы, браузеры) окрашиваются под обои и меняются вместе с ними — как «Из обоев» в пиксельной теме", "the accent, windows, menus, the Dock, Control Center and the apps (GTK, Qt, terminals, browsers) take the wallpaper's colour and follow it, like the pixel theme's From wallpaper")
            checked: Config.mac.wallpaperTint
            onToggled: v => Config.mac.wallpaperTint = v
        }
        CatChoice {
            present: !Config.mac.wallpaperTint''' + M + '''
            label: I18n.t("Цвет акцента", "Accent colour")'''),

    # ---- Theme: the accent and the surfaces ----
    ("config/Theme.qml",
     '''    readonly property color macAccent: (macAccents[Config.mac.accent] || macAccents.blue)[dark ? 1 : 0]''',
     '''    // vm-patch mac-tint: Golden Gate under the wallpaper's colour (Config.mac.wallpaperTint)
    readonly property bool macTint: macLook && !!Config.mac.wallpaperTint && /^#[0-9a-f]{6}$/i.test(Config.mac.wallpaperAccent || "")
    readonly property color macSeed: macTint ? Qt.color(Config.mac.wallpaperAccent) : "#0091ff"
    // the seed at a Mac accent's brightness; a grey picture gives graphite
    function macTone(isDark, hueShift) {
        const s = macSeed;
        const grey = s.hslSaturation < 0.12;
        return hex(Qt.hsla((s.hslHue + (hueShift || 0) + 1) % 1, grey ? s.hslSaturation : Math.min(0.9, Math.max(0.55, s.hslSaturation)), isDark ? 0.62 : 0.5, 1));
    }
    // a surface leaned toward the wallpaper, as macOS tints its windows
    function macTinted(c, k) {
        return macTint ? hex(mix(Qt.color(c), macSeed, k === undefined ? (dark ? 0.07 : 0.05) : k)) : c;
    }
    readonly property color macAccent: macTint ? macTone(dark) : (macAccents[Config.mac.accent] || macAccents.blue)[dark ? 1 : 0]'''),
    ("config/Theme.qml",
     '''    readonly property var macBase: dark ? ({''',
     '''    readonly property var macBaseRaw: dark ? ({'''),
    ("config/Theme.qml",
     '''    readonly property var base: macLook ? macBase : baseOf(flavor, dark, night)''',
     '''    // vm-patch mac-tint: the Mac's surfaces tinted by the wallpaper, its accents from it
    readonly property var macBase: !macTint ? macBaseRaw : Object.assign({}, macBaseRaw, {
            desk: macTinted(macBaseRaw.desk),
            face: macTinted(macBaseRaw.face),
            faceAlt: macTinted(macBaseRaw.faceAlt),
            sunken: macTinted(macBaseRaw.sunken),
            hi: macTinted(macBaseRaw.hi),
            lo: macTinted(macBaseRaw.lo),
            accent: hex(macAccent),
            title1: hex(macAccent),
            accent2: macTone(dark, 0.08),
            title2: macTone(dark, 0.08)
        })
    readonly property var base: macLook ? macBase : baseOf(flavor, dark, night)'''),

    # ---- PaletteGenerator: read the wallpaper for Golden Gate too ----
    ("services/PaletteGenerator.qml",
     '''    readonly property bool auto: Config.ready && Config.appearance.flavor === "wallpaper" && Config.appearance.autoWallpaperColors && !Wallpapers.hellOn
''',
     '''    readonly property bool auto: Config.ready && Config.appearance.flavor === "wallpaper" && Config.appearance.autoWallpaperColors && !Wallpapers.hellOn
    // vm-patch mac-tint: Golden Gate's "Colour from the wallpaper" follows the picture as well
    readonly property bool macAuto: Config.ready && Theme.macLook && !!Config.mac.wallpaperTint && !Wallpapers.hellOn
    onMacAutoChanged: if (macAuto)
        autoTimer.restart()
'''),
    ("services/PaletteGenerator.qml",
     '''    onAreaChanged: if (auto)
        autoTimer.restart()''',
     '''    onAreaChanged: if (auto || macAuto)''' + M + '''
        autoTimer.restart()'''),
    ("services/PaletteGenerator.qml",
     '''    onWallpaperChanged: if (auto)
        autoTimer.restart()''',
     '''    onWallpaperChanged: if (auto || macAuto)''' + M + '''
        autoTimer.restart()'''),
    ("services/PaletteGenerator.qml",
     '''    onWallNightChanged: if (auto)
        autoTimer.restart()''',
     '''    onWallNightChanged: if (auto || macAuto)''' + M + '''
        autoTimer.restart()'''),
    ("services/PaletteGenerator.qml",
     '''        onTriggered: if (root.auto && root.wallpaper)''',
     '''        onTriggered: if ((root.auto || root.macAuto) && root.wallpaper)''' + M),
    ("services/PaletteGenerator.qml",
     '''            if (auto && wallpaper)
                generateFrom(wallpaper);''',
     '''            if ((auto || macAuto) && wallpaper)''' + M + '''
                generateFrom(wallpaper);'''),
    ("services/PaletteGenerator.qml",
     '''    function apply(accent, switchFlavor) {
        if (!Wallpapers.hellOn && Config.appearance.customAccent !== accent)''',
     '''    function apply(accent, switchFlavor) {
        // vm-patch mac-tint: Golden Gate keeps its own; the pixel theme's only when it asked
        if (macAuto && Config.mac.wallpaperAccent !== accent)
            Config.mac.wallpaperAccent = accent;
        if (macAuto && !auto && !switchFlavor)
            return;
        if (!Wallpapers.hellOn && Config.appearance.customAccent !== accent)'''),

    # ---- GoldenGate: windows, content, sidebar, the glass ----
    ("services/GoldenGate.qml",
     '''    readonly property color windowBg: hell ? Theme.hellBody : dark ? "#1e1e1e" : "#f5f5f5"
    readonly property color contentBg: hell ? Theme.hellFace : dark ? "#232323" : "#ffffff"
    readonly property color sidebarBg: hell ? Theme.hellSunken : dark ? "#2a2a2a" : "#e9e9e9"''',
     '''    readonly property color windowBg: hell ? Theme.hellBody : Theme.macTinted(dark ? "#1e1e1e" : "#f5f5f5")''' + M + '''
    readonly property color contentBg: hell ? Theme.hellFace : Theme.macTinted(dark ? "#232323" : "#ffffff")''' + M + '''
    readonly property color sidebarBg: hell ? Theme.hellSunken : Theme.macTinted(dark ? "#2a2a2a" : "#e9e9e9")''' + M),
    ("services/GoldenGate.qml",
     '''        return hell ? Qt.rgba(0.07, 0.03, 0.03, Math.min(0.97, a + 0.1)) : dark ? Qt.rgba(0.12, 0.12, 0.13, Math.min(0.97, a)) : Qt.rgba(0.97, 0.97, 0.975, Math.min(0.97, a));''',
     '''        if (!hell && Theme.macTint) {''' + M + ''': the glass leans toward the wallpaper too
            const g = Theme.mix(dark ? Qt.rgba(0.12, 0.12, 0.13, 1) : Qt.rgba(0.97, 0.97, 0.975, 1), Theme.macSeed, dark ? 0.12 : 0.08);
            return Qt.rgba(g.r, g.g, g.b, Math.min(0.97, a));
        }
        return hell ? Qt.rgba(0.07, 0.03, 0.03, Math.min(0.97, a + 0.1)) : dark ? Qt.rgba(0.12, 0.12, 0.13, Math.min(0.97, a)) : Qt.rgba(0.97, 0.97, 0.975, Math.min(0.97, a));'''),

    # ---- ThemeExport: the apps' Mac colours ----
    ("services/ThemeExport.qml",
     '''        const h = c => Theme.hex(c);
        // Golden Gate is always Desktop''',
     '''        const h = c => Theme.hex(c);
        const t = c => Theme.macTinted(c);''' + M + ''': the apps' surfaces lean toward the wallpaper
        // Golden Gate is always Desktop'''),
    ("services/ThemeExport.qml",
     '''            "macWindow": d ? "#1e1e1e" : "#f5f5f5",
            "macContent": d ? "#232323" : "#ffffff",
            "macSidebar": d ? "#2a2a2c" : "#e8e8ea",
            "macPopover": d ? "#2b2b2d" : "#f6f6f6",''',
     '''            "macWindow": t(d ? "#1e1e1e" : "#f5f5f5"),''' + M + '''
            "macContent": t(d ? "#232323" : "#ffffff"),
            "macSidebar": t(d ? "#2a2a2c" : "#e8e8ea"),
            "macPopover": t(d ? "#2b2b2d" : "#f6f6f6"),'''),
    ("services/ThemeExport.qml",
     '''            "macOverview": d ? "#101012" : "#2c2c30",''',
     '''            "macOverview": t(d ? "#101012" : "#2c2c30"),''' + M),
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
