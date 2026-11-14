#!/usr/bin/env python3
"""serp-skin (Celestia; part of pc-kit since 2026-11-13, `kit` patch serp-skin): the Serpantinum skin of angelOS.

Config.settingsUi.skin = "serp" turns it on. Its own module set (modules/serp: islands bar, dock,
panels, settings window) and singleton (services/Serp.qml, its settings in ~/.config/angelos/
serp.json) over angelOS's own Strip, windows, Halo, angel and hell.

  apply.py [apply] | check | revert        ANGELOS_SHELL=<dir> works on a copy

Hunks are exact OLD -> NEW that must occur once; revert puts OLD back. RULE (2026-11-13): no hunk
may sit inside another patch's text (pc-kit's skin-morph, mac-tint, codex-fixes…): kit's watcher
then thinks that patch is gone and applies it again. After any change: `kit` (all ok) and
scripts/qml-check.sh.
"""
import os, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHELL = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos")

HUNKS = {
    "shell.qml": [
        ("import qs.modules.mac\n",
         "import qs.modules.mac\nimport qs.modules.serp  // serp-skin\n"),
        ("    MacDesktop {}\n",
         "    MacDesktop {}\n    SerpDesktop {}  // serp-skin\n    SerpWindows {}  // serp-skin\n"),
    ],
    # the classic bar (taskbar, Start button, tray…) steps aside for the islands
    "modules/bar/Bar.qml": [
        ("    model: GoldenGate.on || Shell.desktopHeld ? [] :",
         "    model: GoldenGate.on || Serp.on || Shell.desktopHeld ? [] :"),
    ],
    # Settings → Appearance → Skin: our card (its name, and a little drawing of the islands)
    "widgets/SettingsSkinCard.qml": [
        ('            "goldengate": ["Golden Gate", I18n.t("весь стол как macOS 27", "the whole desktop like macOS 27")]\n',
         '            "goldengate": ["Golden Gate", I18n.t("весь стол как macOS 27", "the whole desktop like macOS 27")],\n'
         '            "serp": ["Serpantinum", I18n.t("острова, док и темы — в стиле angelOS", "islands, a dock and themes, angelOS style")]  // serp-skin\n'),
        ("        height: Math.round(width * 0.62)\n        clip: true\n",
         "        height: Math.round(width * 0.62)\n        clip: true\n"
         "        SerpSkinPreview {  // serp-skin\n            visible: root.skin === \"serp\"\n            anchors.fill: parent\n        }\n"),
    ],
    "modules/settings/catalog/Appearance.qml": [
        ("                    readonly property int cols: width >= Theme.u * 5 * 96 ? 5 : width >= Theme.u * 3 * 96 ? 3 : 2\n",
         "                    readonly property int cols: width >= Theme.u * 6 * 96 ? 6 : width >= Theme.u * 3 * 96 ? 3 : 2  // serp-skin: six\n"),
        ('                        model: ["classic", "win10", "windose", "stream", "goldengate"]\n',
         '                        model: ["classic", "win10", "windose", "stream", "goldengate", "serp"]  // serp-skin\n'),
    ],
    # the desktop widgets: the modern card look (Golden Gate's) under Serpantinum too, in the
    # skin's colours, font and corners (DesktopWidgets' card tokens); no Liquid Glass rim.
    # And the weather is fetched while the skin shows it.
    "services/DesktopWidgets.qml": [
        ("        value: root.weatherWanted || Halo.weatherWanted || StartPrefs.current === \"tiles\"",
         "        value: root.weatherWanted || Halo.weatherWanted || StartPrefs.current === \"tiles\" || Serp.on  // serp-skin"),
        ('    readonly property bool macStyle: Config.ready && (style === "mac" || (style === "auto" && GoldenGate.on))\n',
         '    readonly property bool macStyle: Config.ready && (style === "mac" || (style === "auto" && (GoldenGate.on || Serp.on)))  // serp-skin\n'),
        ("    readonly property int macRadius: mpx(22)\n",
         "    readonly property int macRadius: Serp.on ? Math.min(Serp.px(24), Math.round(Serp.radius * 1.4)) : mpx(22)  // serp-skin\n"),
        ("    readonly property string macTextFamily: Config.mac.font",
         "    readonly property string macTextFamily: Serp.on ? Serp.font : Config.mac.font"),
        ("    readonly property string macDisplayFamily: Config.mac.font",
         "    readonly property string macDisplayFamily: Serp.on ? Serp.font : Config.mac.font"),
        ("    readonly property color macLabel: Qt.alpha(Theme.text, 0.95)\n",
         "    readonly property color macLabel: Serp.on ? Serp.text : Qt.alpha(Theme.text, 0.95)  // serp-skin\n"),
        ("    readonly property color macSecondary: Theme.mix(",
         "    readonly property color macSecondary: Serp.on ? Serp.subtext1 : Theme.mix("),
        ("    readonly property color macTertiary: Theme.dark ?",
         "    readonly property color macTertiary: Serp.on ? Serp.subtext0 : Theme.dark ?"),
        ("    readonly property color macSeparator: Qt.alpha(",
         "    readonly property color macSeparator: Serp.on ? Serp.line : Qt.alpha("),
        ("    readonly property color macFill: Qt.alpha(",
         "    readonly property color macFill: Serp.on ? Serp.cardFill : Qt.alpha("),
        ("    readonly property color macEdge: Theme.dark ?",
         "    readonly property color macEdge: Serp.on ? Serp.line : Theme.dark ?"),
        ("    readonly property color macRim: Theme.dark ?",
         "    readonly property color macRim: Serp.on ? \"transparent\" : Theme.dark ?"),
        ("        const pool = [Theme.accent, Theme.accent2, Theme.accent4, Theme.accent3, Theme.ok, Theme.danger, Theme.title2].map(macInk);\n",
         "        const pool = Serp.on ? [Serp.mauve, Serp.blue, Serp.peach, Serp.green, Serp.teal, Serp.red, Serp.pink] : [Theme.accent, Theme.accent2, Theme.accent4, Theme.accent3, Theme.ok, Theme.danger, Theme.title2].map(macInk);  // serp-skin\n"),
    ],
    "widgets/MacWidgetCard.qml": [
        ("    readonly property bool blurred: !!backdrop && Config.appearance.blur && !GoldenGate.reduceTransparency\n",
         "    readonly property bool blurred: !!backdrop && Config.appearance.blur && !GoldenGate.reduceTransparency && (!Serp.on || Serp.glassOn)  // serp-skin: solid cards, no live blur (~5% CPU) — but under the glass\n"),
        ("    readonly property bool rimFx: glassBody && blurred && !GoldenGate.gameMode && !(GoldenGate.on && GoldenGate.hell)\n",
         "    readonly property bool rimFx: glassBody && blurred && !GoldenGate.gameMode && !(GoldenGate.on && GoldenGate.hell) && !Serp.on  // serp-skin: flat\n"),
    ],
    # the desktop widgets keep out from under the islands and the dock
    "modules/background/Background.qml": [
        ("                id: faceArea\n                anchors.fill: parent\n",
         "                id: faceArea\n                anchors.fill: parent\n"
         "                anchors.topMargin: Serp.on ? Serp.barHeight + Serp.px(8) : 0  // serp-skin\n"
         "                anchors.bottomMargin: Serp.on && Serp.cfg.dock && !Serp.cfg.dockAutohide ? Serp.px(Serp.cfg.dockSize) + Serp.px(40) : 0  // serp-skin\n"),
        ("                id: deskArea\n                anchors.fill: parent\n",
         "                id: deskArea\n                anchors.fill: parent\n"
         "                anchors.topMargin: Serp.on ? Serp.barHeight + Serp.px(8) : 0  // serp-skin\n"
         "                anchors.bottomMargin: Serp.on && Serp.cfg.dock && !Serp.cfg.dockAutohide ? Serp.px(Serp.cfg.dockSize) + Serp.px(40) : 0  // serp-skin\n"),
    ],
    # the notification cards come out on the skin's side (Serp.cfg.notifPosition, top-right: where
    # its notification centre opens)
    "modules/notifications/NotificationPopups.qml": [
        ('    readonly property string pos: Config.notifications.position || "top-right"\n',
         '    readonly property string pos: Serp.on ? Serp.cfg.notifPosition : Config.notifications.position || "top-right"  // serp-skin\n'),
    ],
    # the built-in desktop widgets wear the skin's own faces (modules/serp/widgets/<Name>Widget.qml)
    # while it is the skin — a third look beside the pixel one and the macOS card; the skin
    # switched, the content is loaded again
    "modules/desktop/DesktopWidgetHost.qml": [
        ('                        setSource(Qt.resolvedUrl("widgets/" + name + "Widget.qml"), props);\n',
         '                        setSource(Serp.on && Serp.widgetFaces.includes(name) ? Qt.resolvedUrl("../serp/widgets/" + name + "Widget.qml") : Qt.resolvedUrl("widgets/" + name + "Widget.qml"), props);  // serp-skin\n'),
        ("                function load() {\n",
         "                // serp-skin: the skin's faces come and go with the skin\n"
         "                readonly property bool serpFace: Serp.on\n"
         "                onSerpFaceChanged: if (status !== Loader.Null) {\n"
         "                    source = \"\";\n"
         "                    load();\n"
         "                }\n"
         "                function load() {\n"),
    ],
    # the plugins' theme API (services/Skin): under the skin the plugins draw their modern look
    # (as under Golden Gate) in the skin's roles, font and corners — their bar icons, their
    # popovers, their panels; no Liquid Glass
    "services/Skin.qml": [
        ('    readonly property bool mac: force !== "" ? force === "mac" : GoldenGate.on\n',
         '    readonly property bool mac: force !== "" ? force === "mac" : GoldenGate.on || Serp.on  // serp-skin\n'),
        ('    readonly property bool glass: mac && !reduceTransparency\n',
         '    readonly property bool glass: mac && !reduceTransparency && !Serp.on  // serp-skin: flat\n'),
        ('    readonly property color accent: hell ? Theme.hellAccent : Theme.accent\n',
         '    readonly property color accent: hell ? Theme.hellAccent : Serp.on ? Serp.accent : Theme.accent  // serp-skin\n'),
        ('    readonly property color accentText: hell ? Theme.hellBody : mac ?',
         '    readonly property color accentText: hell ? Theme.hellBody : Serp.on ? Serp.onAccent : mac ?'),
        ('    readonly property color text: hell ? Theme.hellText : mac ?',
         '    readonly property color text: hell ? Theme.hellText : Serp.on ? Serp.text : mac ?'),
        ('    readonly property color textDim: hell ? Theme.hellTextDim : mac ?',
         '    readonly property color textDim: hell ? Theme.hellTextDim : Serp.on ? Serp.subtext1 : mac ?'),
        ('    readonly property color textFaint: hell ? Qt.alpha(Theme.hellTextDim, 0.7) : mac ?',
         '    readonly property color textFaint: hell ? Qt.alpha(Theme.hellTextDim, 0.7) : Serp.on ? Serp.subtext0 : mac ?'),
        ('    readonly property color surface: hell ? Theme.hellFace : mac ?',
         '    readonly property color surface: hell ? Theme.hellFace : Serp.on ? Serp.ground : mac ?'),
        ('    readonly property color surfaceAlt: hell ? Theme.hellFaceAlt : mac ?',
         '    readonly property color surfaceAlt: hell ? Theme.hellFaceAlt : Serp.on ? Serp.surface0 : mac ?'),
        ('    readonly property color sunken: hell ? Theme.hellSunken : mac ?',
         '    readonly property color sunken: hell ? Theme.hellSunken : Serp.on ? Serp.surface1 : mac ?'),
        ('    readonly property color separator: hell ? Theme.hellEdge : mac ?',
         '    readonly property color separator: hell ? Theme.hellEdge : Serp.on ? Serp.line : mac ?'),
        ('    readonly property color hover: hell ? Theme.mix(Theme.hellFace, Theme.hellAccent, 0.2) : mac ?',
         '    readonly property color hover: hell ? Theme.mix(Theme.hellFace, Theme.hellAccent, 0.2) : Serp.on ? Serp.hover : mac ?'),
        ('        return hell ? Theme.hellText : mac ? GoldenGate.barInk(screenName || "") : Theme.text;\n',
         '        return hell ? Theme.hellText : Serp.on ? Serp.text : mac ? GoldenGate.barInk(screenName || "") : Theme.text;  // serp-skin\n'),
        ('    readonly property string font: mac ? Theme.macFont : Theme.fontBody\n',
         '    readonly property string font: Serp.on ? Serp.font : mac ? Theme.macFont : Theme.fontBody  // serp-skin\n'),
        ('    readonly property string titleFont: mac ? Theme.macFont : Theme.fontTitle\n',
         '    readonly property string titleFont: Serp.on ? Serp.font : mac ? Theme.macFont : Theme.fontTitle  // serp-skin\n'),
        ('    readonly property string mono: mac ? Theme.macMono : Theme.fontMono\n',
         '    readonly property string mono: Serp.on ? Serp.font : mac ? Theme.macMono : Theme.fontMono  // serp-skin\n'),
        ('    readonly property int radius: mac ? GoldenGate.px(10) : 0 ',
         '    readonly property int radius: Serp.on ? Serp.radiusSmall : mac ? GoldenGate.px(10) : 0 '),
        ('    readonly property int cardRadius: mac ? GoldenGate.px(16) : 0 ',
         '    readonly property int cardRadius: Serp.on ? Serp.radius : mac ? GoldenGate.px(16) : 0 '),
    ],
    # the shared macOS controls (sliders, switches…) in plugin popovers take the skin's accent
    "services/GoldenGate.qml": [
        ("    readonly property color accent: hell ? Theme.hellAccent : Theme.macAccent\n",
         "    readonly property color accent: hell ? Theme.hellAccent : Serp.on ? Serp.accent : Theme.macAccent  // serp-skin\n"),
    ],
    # the plugins' popovers: the skin's flat panel instead of Liquid Glass
    "modules/bar/BarPopup.qml": [
        ("        radius: GoldenGate.px(14)\n        shadowSize: GoldenGate.px(20)\n",
         "        radius: Serp.on ? Serp.radius : GoldenGate.px(14)  // serp-skin\n"
         "        fill: Serp.on ? Serp.solid : GoldenGate.glassFill  // serp-skin\n"
         "        highlight: !Serp.on  // serp-skin\n"
         "        shadowSize: GoldenGate.px(20)\n"),
    ],
    # gestures that open Golden Gate's panels open the skin's
    "services/Gestures.qml": [
        ('        case "notifications":\n            if (Skin.mac)\n',
         '        case "notifications":\n            if (Serp.on)  // serp-skin\n                Serp.togglePanel("notifs", out);\n            else if (Skin.mac)\n'),
        ('            else if (Skin.mac)\n                GoldenGate.togglePanel("cc", out);\n',
         '            else if (Serp.on)  // serp-skin\n                Serp.togglePanel("quick", out);\n            else if (Skin.mac)\n                GoldenGate.togglePanel("cc", out);\n'),
    ],
    # Селестия's desktop face (the celestia plugin, installed copy): the skin's ink, plate and blush
    "~/.config/angelos/plugins/celestia/Face.qml": [
        ('        property color ink: root.mono ? root.monoColor : root.hell ? Theme.hellFlame : root.mac ? "#f7f4ff" : Theme.accent\n',
         '        property color ink: root.mono ? root.monoColor : root.hell ? Theme.hellFlame : root.mac ? (Serp.on ? Serp.text : "#f7f4ff") : Theme.accent  // serp-skin\n'),
        ('        property color plate: root.small ? Qt.rgba(0, 0, 0, 0) : root.hell ? Theme.hellPlate : root.mac ? Qt.rgba(0.06, 0.05, 0.10, 0.55) : Qt.darker(Skin.sunken, 1.6)\n',
         '        property color plate: root.small ? Qt.rgba(0, 0, 0, 0) : root.hell ? Theme.hellPlate : root.mac ? (Serp.on ? Qt.alpha(Serp.mantle, 0.75) : Qt.rgba(0.06, 0.05, 0.10, 0.55)) : Qt.darker(Skin.sunken, 1.6)  // serp-skin\n'),
        ('        property color cheek: root.hell ? Theme.hellBlood : Theme.accent2\n',
         '        property color cheek: root.hell ? Theme.hellBlood : Serp.on ? Serp.pink : Theme.accent2  // serp-skin\n'),
    ],
    "~/.config/angelos/plugins/celestia/DesktopWidget.qml": [
        ('            kind: Brain.spoken ? "body" : "tiny"\n',
         '            kind: Brain.spoken ? "body" : "tiny"\n            font.family: Serp.on ? Serp.font : Skin.macWidgets ? Skin.font : Theme.fontBody  // serp-skin\n'),
    ],
    # angelOS's own desk strip and desk popup, OSD and clipboard step aside for the skin's
    # (modules/serp: SerpDeskStrip, SerpOsd, SerpClipboard — same triggers, the skin's look)
    "modules/workspace/WorkspaceStrip.qml": [
        ("    visible: shown || slide.running || linger.running\n",
         "    visible: (shown || slide.running || linger.running) && !Serp.on  // serp-skin\n"),
    ],
    "modules/workspace/WorkspacePopup.qml": [
        ("    visible: shown\n",
         "    visible: shown && !Serp.on  // serp-skin\n"),
    ],
    "modules/osd/Osd.qml": [
        ("    visible: shown || fade.running\n",
         "    visible: (shown || fade.running) && !Serp.on  // serp-skin\n"),
    ],
    "modules/LazyWindows.qml": [
        ("        active: clipboardKeep.alive\n",
         "        active: clipboardKeep.alive && !Serp.on  // serp-skin\n"),
    ],
    # the Halo wears the skin's island: flat, or Serpantinum's liquid glass, rounded like the
    # islands (the pixel pill steps aside while the skin is on)
    "modules/halo/HaloWindow.qml": [
        ("import qs.modules.desktop\n",
         "import qs.modules.desktop\nimport qs.modules.serp  // serp-skin\n"),
        ("    readonly property real wantR: expanded ? 0 : px(8)\n",
         "    readonly property real wantR: expanded ? 0 : Serp.on ? Serp.radius : px(8)  // serp-skin\n"),
        ('            color: win.earsRest || win.expanded ? "transparent" : win.face\n',
         '            color: win.earsRest || win.expanded || Serp.on ? "transparent" : win.face  // serp-skin\n'),
        ('            edge: win.earsRest || win.expanded ? "transparent" : win.edgeColor\n',
         '            edge: win.earsRest || win.expanded || Serp.on ? "transparent" : win.edgeColor  // serp-skin\n'
         '            // serp-skin: the skin island under the pill (flat or liquid glass)\n'
         '            SGlass {\n'
         '                visible: Serp.on && !win.earsRest && !win.expanded\n'
         '                anchors.fill: parent\n'
         '                backdrop: serpHaloBack\n'
         '                radius: Math.min(parent.radius, height / 2)\n'
         '            }\n'),
        ("    // the top edge over the hidden pill (dodging): the pointer there brings the Halo back\n    Item {\n        id: peekZone\n",
         "    // serp-skin: the wallpaper in screen space for the Halo's liquid glass\n"
         "    SerpBackdrop {\n        id: serpHaloBack\n        screenName: win.modelData ? win.modelData.name : \"\"\n        origin: Qt.point(0, 0)\n    }\n"
         "    // the top edge over the hidden pill (dodging): the pointer there brings the Halo back\n    Item {\n        id: peekZone\n"),
    ],
    # the sidebar's bookmark tab (the heart at the edge): a small island of the skin
    "modules/sidebar/SidebarHost.qml": [
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ("                PxBox {\n                    anchors.fill: parent\n                    color: Sidebar.open || Sidebar.shown ? Theme.accent",
         "                PxBox {\n                    visible: !Serp.on  // serp-skin\n                    anchors.fill: parent\n                    color: Sidebar.open || Sidebar.shown ? Theme.accent"),
        ("                MouseArea {\n                    id: tabMouse\n",
         "                // serp-skin: the heart on the skin's island\n"
         "                SerpBackdrop {\n                    id: serpTabBack\n                    screenName: scope.modelData.name\n                    origin: tab.origin\n                }\n"
         "                SGlass {\n"
         "                    visible: Serp.on\n"
         "                    anchors.fill: parent\n"
         "                    backdrop: serpTabBack\n"
         "                    radius: Serp.radiusSmall\n"
         "                    hover: tabMouse.containsMouse ? 1 : 0\n"
         "                    Rectangle {\n"
         "                        anchors.fill: parent\n"
         "                        radius: parent.radius\n"
         "                        color: Sidebar.open || Sidebar.shown ? Serp.accent : tabMouse.containsMouse ? Serp.hover : \"transparent\"\n"
         "                    }\n"
         "                    SIcon {\n"
         "                        anchors.centerIn: parent\n"
         "                        name: \"heart\"\n"
         "                        size: Serp.px(13)\n"
         "                        filled: true\n"
         "                        color: Sidebar.open || Sidebar.shown ? Serp.onAccent : Serp.accent\n"
         "                    }\n"
         "                }\n"
         "                MouseArea {\n                    id: tabMouse\n"),
    ],
    # `angelos settingsSkin serp`
    "modules/Ipc.qml": [
        ("        const skins = [\"classic\", \"win10\", \"windose\", \"stream\", \"goldengate\"];\n",
         "        const skins = [\"classic\", \"win10\", \"windose\", \"stream\", \"goldengate\", \"serp\"];  // serp-skin\n"),
    ],
}
# more hunk sets, one file per area (hunks/<area>.py: HUNKS = {rel: [(old, new), ...]}) — merged
# in; a file another set also touches gets its pairs appended (they must not overlap)
import importlib.util
_skip = set(filter(None, os.environ.get("SERP_SKIP_HUNKS", "").split(",")))   # sets still being written
for _f in sorted((HERE / "hunks").glob("*.py")):
    if _f.stem in _skip:
        continue
    _spec = importlib.util.spec_from_file_location("serp_hunks_" + _f.stem, _f)
    _m = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_m)
    for _rel, _pairs in getattr(_m, "HUNKS", {}).items():
        HUNKS.setdefault(_rel, []).extend(_pairs)

# whole files and directories that are ours
NEW = {
    "services/Serp.qml": HERE / "qml/services/Serp.qml",
    # pc-kit's doctor in the skin (kit doctor --json): the bar's shield, its panel, settings → pc-kit
    "services/SerpKit.qml": HERE / "qml/services/SerpKit.qml",
    "modules/serp": HERE / "qml/modules/serp",
    "widgets/SerpSkinPreview.qml": HERE / "qml/widgets/SerpSkinPreview.qml",
    "modules/settings/views/SerpView.qml": HERE / "qml/settings-views/SerpView.qml",
    # the skin's cursor (cursor/build.py), worn while the skin is on (hunks/cursor.py)
    "~/.local/share/icons/angelOS-Serp": HERE / "cursor/angelOS-Serp",
}


def path(rel):
    return Path(rel).expanduser() if rel.startswith("~/") else SHELL / rel


def hunks_on():
    return all(new in path(rel).read_text() for rel, hs in HUNKS.items() for _, new in hs)


def files_same():
    for rel, src in NEW.items():
        dst = path(rel)
        if src.is_dir():
            for f in src.rglob("*"):
                g = dst / f.relative_to(src)
                if f.is_file() and (not g.exists() or g.read_bytes() != f.read_bytes()):
                    return False
        elif not dst.exists() or dst.read_bytes() != src.read_bytes():
            return False
    return True


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if mode == "check":
        sys.exit(0 if hunks_on() and files_same() else 1)
    if mode == "revert":
        for rel, hs in HUNKS.items():
            f = path(rel)
            t = f.read_text()
            for old, new in hs:
                if new in t:
                    t = t.replace(new, old, 1)
            f.write_text(t)
        for rel in NEW:
            d = path(rel)
            if d.is_dir():
                shutil.rmtree(d)
            else:
                d.unlink(missing_ok=True)
        print("reverted")
        return
    texts = {}
    for rel, hs in HUNKS.items():
        t = path(rel).read_text()
        for old, new in hs:
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
    for rel, src in NEW.items():
        dst = path(rel)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.bak*"))
        else:
            shutil.copy2(src, dst)
    print("applied")


if __name__ == "__main__":
    main()
