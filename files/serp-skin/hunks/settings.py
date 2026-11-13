# serp-skin: angelOS's Settings window in the skin's look (plan: notes/plan-settings-start.md,
# "Settings"). With the skin on, SettingsView takes the Mac path (settingsSkin stays "goldengate",
# so the Px* widgets of the pages keep their modern look) but loads views/SerpView.qml — the Guide
# sidebar and header — on a transparent frame; GoldenGate's label/group/control tokens wear Serp's
# colours, so the pages' text and cards follow the skin's palette (light ones too: `dark` from
# Serp.base). Never touched: GoldenGate L21-27 (skin-morph), L58-60 (mac-tint), MacView (pc-kit's
# mac-settings-lights). PxText's colour and font are hunks/halo_open.py's.
HUNKS = {
    "modules/settings/SettingsView.qml": [
        ('    readonly property string skin: ["classic", "windose", "stream", "goldengate"].includes(Config.settingsUi.skin) ? Config.settingsUi.skin : "classic"\n',
         '    readonly property string skin: ["classic", "windose", "stream", "goldengate", "serp"].includes(Config.settingsUi.skin) ? Config.settingsUi.skin : "classic"  // serp-skin\n'),
        ('    readonly property bool mac: skin === "goldengate" && !hellDress\n',
         '    readonly property bool mac: (skin === "goldengate" || skin === "serp") && !hellDress  // serp-skin\n'),
        ('    readonly property string viewId: mac ? "mac" : "win11"\n',
         '    readonly property string viewId: mac ? (skin === "serp" ? "serp" : "mac") : "win11"  // serp-skin\n'),
        ('    readonly property bool fluent: viewId === "win11" || viewId === "mac"\n',
         '    readonly property bool fluent: viewId === "win11" || viewId === "mac" || viewId === "serp"  // serp-skin\n'),
        ('        visible: win.mac\n        anchors.fill: parent\n        color: GoldenGate.contentBg\n',
         '        visible: win.mac\n        anchors.fill: parent\n        color: win.viewId === "serp" ? "transparent" : GoldenGate.contentBg  // serp-skin: SerpView draws its own card\n'),
        ('            const v = win.viewId === "mac" ? {\n                "file": "MacView.qml"\n            } : ',
         '            const v = win.viewId === "serp" ? {  // serp-skin\n                "file": "SerpView.qml"\n            } : win.viewId === "mac" ? {\n                "file": "MacView.qml"\n            } : '),
    ],
    # the blur behind the window rounded like SerpView's card
    "modules/settings/SettingsWindow.qml": [
        ("        item: view.frame\n",
         "        item: view.frame\n        radius: Serp.on && view.viewId === \"serp\" ? Math.min(Serp.px(24), Serp.radius * 1.4) : 0  // serp-skin\n"),
    ],
    "services/GoldenGate.qml": [
        # light palettes: Golden Gate's dark/light pick follows the skin's base
        ("    readonly property bool dark: hell || Theme.dark\n",
         "    readonly property bool dark: hell || (Serp.on ? Serp.base.hslLightness < 0.5 : Theme.dark)  // serp-skin\n"),
        # L54-57 only (L58-60 are mac-tint's)
        ("    readonly property color label: hell ? Theme.hellText : dark ? Qt.rgba(1, 1, 1, 0.88) : Qt.rgba(0, 0, 0, 0.86)\n"
         "    readonly property color secondaryLabel: hell ? Theme.hellTextDim : dark ? Qt.rgba(1, 1, 1, 0.55) : Qt.rgba(0, 0, 0, 0.5)\n"
         "    readonly property color tertiaryLabel: dark ? Qt.rgba(1, 1, 1, 0.3) : Qt.rgba(0, 0, 0, 0.26)\n"
         "    readonly property color separator: dark ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0, 0, 0, 0.1)\n",
         "    readonly property color label: hell ? Theme.hellText : Serp.on ? Serp.text : dark ? Qt.rgba(1, 1, 1, 0.88) : Qt.rgba(0, 0, 0, 0.86)  // serp-skin\n"
         "    readonly property color secondaryLabel: hell ? Theme.hellTextDim : Serp.on ? Serp.subtext1 : dark ? Qt.rgba(1, 1, 1, 0.55) : Qt.rgba(0, 0, 0, 0.5)  // serp-skin\n"
         "    readonly property color tertiaryLabel: Serp.on ? Serp.overlay : dark ? Qt.rgba(1, 1, 1, 0.3) : Qt.rgba(0, 0, 0, 0.26)  // serp-skin\n"
         "    readonly property color separator: Serp.on ? Qt.alpha(Serp.text, 0.1) : dark ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0, 0, 0, 0.1)  // serp-skin\n"),
        # L61-63
        ("    readonly property color groupBg: hell ? Theme.hellFaceAlt : dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.035)\n"
         "    readonly property color controlBg: dark ? Qt.rgba(1, 1, 1, 0.14) : Qt.rgba(0, 0, 0, 0.06)\n"
         "    readonly property color hoverBg: dark ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(0, 0, 0, 0.07)\n",
         "    readonly property color groupBg: hell ? Theme.hellFaceAlt : Serp.on ? Qt.alpha(Serp.surface0, 0.55) : dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.035)  // serp-skin\n"
         "    readonly property color controlBg: Serp.on ? Qt.alpha(Serp.surface1, 0.8) : dark ? Qt.rgba(1, 1, 1, 0.14) : Qt.rgba(0, 0, 0, 0.06)  // serp-skin\n"
         "    readonly property color hoverBg: Serp.on ? Serp.hover : dark ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(0, 0, 0, 0.07)  // serp-skin\n"),
    ],
    # the cards of the pages (Mac look) and their hairlines: the skin's tokens (via GoldenGate)
    "widgets/PxGroup.qml": [
        ('        color: root.mac ? (Theme.dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.035)) : Theme.mix(Theme.toneOf(root.settingsSkin, "face"), Theme.toneOf(root.settingsSkin, "sunken"), Theme.dark ? 0.45 : 0.3)\n',
         '        color: root.mac ? (Serp.on ? GoldenGate.groupBg : Theme.dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.035)) : Theme.mix(Theme.toneOf(root.settingsSkin, "face"), Theme.toneOf(root.settingsSkin, "sunken"), Theme.dark ? 0.45 : 0.3)  // serp-skin\n'),
        ('        color: root.mac ? (foldMouse.containsMouse ? (Theme.dark ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(0, 0, 0, 0.06)) : (Theme.dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.035))) : foldMouse.containsMouse ? Theme.mix(Theme.toneOf(root.settingsSkin, "faceAlt"), Theme.accent, 0.12) : Theme.mix(Theme.toneOf(root.settingsSkin, "face"), Theme.toneOf(root.settingsSkin, "faceAlt"), 0.55)\n',
         '        color: root.mac ? (Serp.on ? (foldMouse.containsMouse ? Qt.alpha(Serp.surface1, 0.7) : GoldenGate.groupBg) : foldMouse.containsMouse ? (Theme.dark ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(0, 0, 0, 0.06)) : (Theme.dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.035))) : foldMouse.containsMouse ? Theme.mix(Theme.toneOf(root.settingsSkin, "faceAlt"), Theme.accent, 0.12) : Theme.mix(Theme.toneOf(root.settingsSkin, "face"), Theme.toneOf(root.settingsSkin, "faceAlt"), 0.55)  // serp-skin\n'),
    ],
    "widgets/SettingRow.qml": [
        ("        visible: root.mac && root.placeY > 0\n        x: Theme.u * 5\n        width: parent.width - x * 2\n        height: 1\n        color: Theme.dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.07)\n",
         "        visible: root.mac && root.placeY > 0\n        x: Theme.u * 5\n        width: parent.width - x * 2\n        height: 1\n        color: Serp.on ? GoldenGate.separator : Theme.dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.07)  // serp-skin\n"),
    ],
    # the fields (the search too): the skin's ink and font
    "widgets/PxField.qml": [
        ('        color: Theme.toneOf(root.settingsSkin, "text")\n',
         '        color: Serp.on && root.mac ? Serp.text : Theme.toneOf(root.settingsSkin, "text")  // serp-skin\n'),
        ("        font.family: script ? Theme.fontScript : root.mac ? Theme.macFont : root.kind === \"title\" ? Theme.fontTitle : Theme.fontBody\n",
         "        font.family: script ? Theme.fontScript : root.mac ? (Serp.on ? Serp.font : Theme.macFont) : root.kind === \"title\" ? Theme.fontTitle : Theme.fontBody  // serp-skin\n"),
    ],
}
