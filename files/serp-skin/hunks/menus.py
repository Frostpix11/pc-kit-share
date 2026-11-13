# serp-skin: every pixel context menu (widgets/PxMenu*: the desktop's right-click, a widget's, a
# task's WindowMenu, the tray's, the Halo's, a notification's) in the skin's look (Serp.on only).
# services/MenuLook hands out a `serp` token set instead of classic's: a flat rounded plate of
# Serp.solid (readable over windows even with the glass on), the skin's text, the accent on a
# soft highlight, hairline separators, no bevels or pixel shadows. The pixel frame (PxBox) then
# draws nothing and PxMenuList lays the plate under it; its rows get the skin's font (settingsSkin
# "goldengate" → PxText's mac branch → Serp.font/colours, hunks/halo_open.py) and line icons
# (MacIcon, MenuLook.serpIcon maps angelOS's pixel names to Lucide ones).
HUNKS = {
    "services/MenuLook.qml": [
        ("import qs.config\n",
         "import qs.config\nimport \"../widgets/MacIcons.js\" as MacIcons  // serp-skin\n"),
        ("    readonly property var classic: hell ? classicHell : plain\n",
         "    readonly property var classic: Serp.on ? serp : hell ? classicHell : plain  // serp-skin\n"
         "    // serp-skin: the Serpantinum skin's menus. `serp` marks the set: PxMenuList lays `plate` (a\n"
         "    // flat rounded Serp.solid) under a frame that draws nothing, rows light up rounded\n"
         "    readonly property var serp: ({\n"
         "            \"name\": \"classic\",\n"
         "            \"serp\": true,\n"
         "            \"plate\": Serp.solid,\n"
         "            \"face\": \"transparent\",\n"
         "            \"edge\": Serp.line,\n"
         "            \"hi\": Serp.surface2,\n"
         "            \"lo\": Serp.surface1,\n"
         "            \"flat\": true,\n"
         "            \"outline\": false,\n"
         "            \"hellBox\": false,\n"
         "            \"shadow\": false,\n"
         "            \"shadowColor\": \"transparent\",\n"
         "            \"shadowU\": 0,\n"
         "            \"headText\": Serp.subtext0,\n"
         "            \"pad\": 7,\n"
         "            \"text\": Serp.text,\n"
         "            \"dim\": Serp.subtext1,\n"
         "            \"ink\": Serp.subtext1,\n"
         "            \"outlineText\": \"transparent\",\n"
         "            \"lit\": Serp.selected,\n"
         "            \"litText\": Serp.accent,\n"
         "            \"litInk\": Serp.accent,\n"
         "            \"markerColor\": Serp.accent,\n"
         "            \"sepLo\": Serp.line,\n"
         "            \"sepHi\": \"transparent\",\n"
         "            \"tileBg\": Serp.surface0,\n"
         "            \"tileEdge\": Serp.line,\n"
         "            \"tileBevel\": false\n"
         "        })\n"
         "    // a menu entry's pixel icon name → the line icon the skin draws (MacIcons, Lucide)\n"
         "    readonly property var serpIcons: ({\n"
         "            \"prev\": \"skip-back\", \"next\": \"skip-forward\", \"pin\": \"star\", \"maximize\": \"maximize-2\",\n"
         "            \"minimize\": \"minimize-2\", \"warn\": \"circle-x\", \"sparkleStar\": \"sparkles\", \"wifiOff\": \"wifi-off\",\n"
         "            \"bolt\": \"zap\", \"chat\": \"bot\", \"width\": \"sliders-horizontal\", \"height\": \"sliders-horizontal\",\n"
         "            \"spider\": \"activity\", \"skull\": \"angel-horns\", \"rotate\": \"rotate-ccw\", \"pill\": \"toggle-right\",\n"
         "            \"note\": \"file-text\", \"allDesks\": \"layout-grid\", \"phone\": \"airplay\", \"headphones\": \"volume-2\",\n"
         "            \"ampoule\": \"sun\", \"ethernet\": \"ethernet-port\", \"eye\": \"eye\", \"pause\": \"pause\", \"minus\": \"minus\"\n"
         "        })\n"
         "    function serpIcon(n) {\n"
         "        return serpIcons[n] || MacIcons.fromPixel(n || \"\") || \"circle-dot\";\n"
         "    }\n"),
    ],
    "widgets/PxMenuList.qml": [
        ("    readonly property var t: menuTokens\n",
         "    readonly property var t: menuTokens\n"
         "    // serp-skin: the rows' PxText in the skin's font and sizes (its mac branch); as before otherwise\n"
         "    readonly property string settingsSkin: Serp.on ? \"goldengate\" : Theme.settingsSkinFor(list.parent)\n"),
        ("    PxBox {\n        id: frame\n",
         "    // serp-skin: the skin's flat rounded plate under the rows (the pixel frame draws nothing then)\n"
         "    Rectangle {\n"
         "        visible: !!list.t.serp\n"
         "        width: frame.width\n"
         "        height: frame.height\n"
         "        radius: Serp.radius\n"
         "        color: list.t.plate || \"transparent\"\n"
         "        border.width: 1\n"
         "        border.color: Serp.line\n"
         "    }\n"
         "    PxBox {\n        id: frame\n"),
        ("        Column {\n            id: col\n            width: parent.width\n",
         "        Column {\n            id: col\n            width: parent.width\n"
         "            topPadding: list.t.serp ? Serp.px(5) : 0  // serp-skin: rows clear of the round corners\n"
         "            bottomPadding: list.t.serp ? Serp.px(5) : 0  // serp-skin\n"),
    ],
    "widgets/PxMenuItem.qml": [
        ("    // the highlight\n    Rectangle {\n        visible: !root.separator\n        anchors.fill: parent\n",
         "    // the highlight\n    Rectangle {\n        visible: !root.separator\n        anchors.fill: parent\n"
         "        anchors.leftMargin: root.t.serp ? Serp.px(5) : 0  // serp-skin: a rounded pill inside the plate\n"
         "        anchors.rightMargin: root.t.serp ? Serp.px(5) : 0  // serp-skin\n"
         "        radius: root.t.serp ? Serp.radiusSmall : 0  // serp-skin\n"),
        ("                visible: root.icon !== \"\"\n"
         "                name: root.icon || \"heart\"\n"
         "                ink: root.lit ? root.t.litInk : root.t.ink\n"
         "            }\n",
         "                visible: root.icon !== \"\" && !root.t.serp  // serp-skin\n"
         "                name: root.icon || \"heart\"\n"
         "                ink: root.lit ? root.t.litInk : root.t.ink\n"
         "            }\n"
         "            // serp-skin: the skin's line icon\n"
         "            MacIcon {\n"
         "                anchors.centerIn: parent\n"
         "                visible: !!root.t.serp && root.icon !== \"\"\n"
         "                name: root.t.serp ? MenuLook.serpIcon(root.icon) : \"circle-dot\"\n"
         "                size: Math.round(Serp.iconSize * root.iconScale)\n"
         "                stroke: 2\n"
         "                color: root.lit ? root.t.litInk : root.t.ink\n"
         "            }\n"),
        ("            visible: side.tick && root.checked\n",
         "            visible: side.tick && root.checked && !root.t.serp  // serp-skin\n"),
        ("            name: \"check\"\n            ink: root.lit ? root.t.litInk : root.t.ink\n        }\n",
         "            name: \"check\"\n            ink: root.lit ? root.t.litInk : root.t.ink\n        }\n"
         "        // serp-skin: the tick as a line icon\n"
         "        MacIcon {\n"
         "            visible: !!root.t.serp && side.tick && root.checked\n"
         "            anchors.right: parent.right\n"
         "            anchors.verticalCenter: parent.verticalCenter\n"
         "            name: \"check\"\n"
         "            size: Serp.iconSize\n"
         "            stroke: 2\n"
         "            color: root.t.litInk\n"
         "        }\n"),
        ("                color: on ? Theme.accent : chipMouse.containsMouse ? Qt.alpha(Theme.accent, 0.3) : Qt.alpha(root.t.lo, 0.5)\n",
         "                color: on ? (root.t.serp ? Serp.accent : Theme.accent) : chipMouse.containsMouse ? Qt.alpha(root.t.serp ? Serp.accent : Theme.accent, 0.3) : Qt.alpha(root.t.lo, 0.5)  // serp-skin\n"
         "                radius: root.t.serp ? Serp.px(4) : 0  // serp-skin\n"),
        ("                    color: chip.on ? Theme.selectText : root.lit ? root.t.litText : root.t.text\n",
         "                    color: chip.on ? (root.t.serp ? Serp.onAccent : Theme.selectText) : root.lit ? root.t.litText : root.t.text  // serp-skin\n"),
    ],
    "widgets/PxMenuTile.qml": [
        ("    PxBox {\n        anchors.fill: parent\n        visible: root.lit || root.on\n",
         "    // serp-skin: a soft rounded plate instead of the bevelled tile\n"
         "    Rectangle {\n"
         "        visible: !!root.t.serp && (root.lit || root.on)\n"
         "        anchors.fill: parent\n"
         "        radius: Serp.radiusSmall\n"
         "        color: root.on ? Serp.selected : Serp.hover\n"
         "        border.width: root.on && root.highlighted ? 1 : 0\n"
         "        border.color: Serp.accent\n"
         "    }\n"
         "    PxBox {\n        anchors.fill: parent\n        visible: (root.lit || root.on) && !root.t.serp  // serp-skin\n"),
        ("                pixel: root.scale_ > 1.1 ? Theme.u * 2 : Theme.u\n                ink: root.t.ink\n            }\n",
         "                pixel: root.scale_ > 1.1 ? Theme.u * 2 : Theme.u\n                ink: root.t.ink\n"
         "                visible: !root.t.serp  // serp-skin\n            }\n"
         "            // serp-skin: the skin's line icon\n"
         "            MacIcon {\n"
         "                anchors.centerIn: parent\n"
         "                visible: !!root.t.serp\n"
         "                name: root.t.serp ? MenuLook.serpIcon(root.entry ? root.entry.icon || \"heart\" : \"heart\") : \"circle-dot\"\n"
         "                size: Math.round(parent.width * 0.75)\n"
         "                stroke: 2\n"
         "                color: root.on || root.lit ? Serp.accent : Serp.text\n"
         "            }\n"),
        ("                    color: sel ? Theme.accent : chipMouse.containsMouse ? Qt.alpha(Theme.accent, 0.3) : Qt.alpha(root.t.lo, 0.5)\n",
         "                    color: sel ? (root.t.serp ? Serp.accent : Theme.accent) : chipMouse.containsMouse ? Qt.alpha(root.t.serp ? Serp.accent : Theme.accent, 0.3) : Qt.alpha(root.t.lo, 0.5)  // serp-skin\n"
         "                    radius: root.t.serp ? Serp.px(3) : 0  // serp-skin\n"),
        ("                        color: chip.sel ? Theme.selectText : root.t.text\n",
         "                        color: chip.sel ? (root.t.serp ? Serp.onAccent : Theme.selectText) : root.t.text  // serp-skin\n"),
    ],
    # the compositor's blur under the menu: rounded like the plate
    "widgets/PxMenu.qml": [
        ("        width: list.width\n        height: list.height\n    }\n",
         "        width: list.width\n        height: list.height\n        radius: list.t.serp ? Serp.radius : 0  // serp-skin\n    }\n"),
    ],
    "widgets/PxMenuSub.qml": [
        ("        width: menuList.width\n        height: menuList.height\n    }\n",
         "        width: menuList.width\n        height: menuList.height\n        radius: menuList.t.serp ? Serp.radius : 0  // serp-skin\n    }\n"),
    ],
}
