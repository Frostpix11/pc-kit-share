# serp-skin: the OPEN Halo in the skin's look (Serp.on only; Classic and Golden Gate untouched).
# The pixel window (PxWindow "frame", its title bar and bevels) steps aside for an SGlass island
# (flat or liquid glass, the islands' corners): a slim header — the page's name in SText, the
# pages' dots, the menu and close as SIcon buttons — and the pages under it. The pages' own
# controls take the modern (Golden Gate) look through settingsSkin "goldengate" on the card, their
# text the skin's colours and font (PxText under that look while the skin is on), the wells and
# quick tiles become rounded plates of the skin.
HUNKS = {
    "modules/halo/HaloWindow.qml": [
        # the Halo's accent (the open card's and the pill's), and the inks: the skin's
        ("    readonly property color accent: songShown ? readable(Theme.mix(Theme.accent, Halo.coverTint, 0.5)) : Theme.accent\n",
         "    readonly property color accent: songShown ? readable(Theme.mix(Serp.on ? Serp.accent : Theme.accent, Halo.coverTint, 0.5)) : Serp.on ? Serp.accent : Theme.accent  // serp-skin\n"),
        ("    readonly property color inkColor: hell ? \"#ff4d4d\" : Theme.text\n"
         "    readonly property color textInk: Theme.text\n"
         "    readonly property color textInkDim: Theme.textDim\n",
         "    readonly property color inkColor: hell ? \"#ff4d4d\" : Serp.on ? Serp.text : Theme.text  // serp-skin\n"
         "    readonly property color textInk: Serp.on ? Serp.text : Theme.text  // serp-skin\n"
         "    readonly property color textInkDim: Serp.on ? Serp.subtext1 : Theme.textDim  // serp-skin\n"),
        # the card starts under the slim header, not the pixel title bar
        ("    readonly property real cardTop: frame.chrome + frame.titleHeight + u * 4\n",
         "    readonly property real cardTop: Serp.on ? Serp.px(38) : frame.chrome + frame.titleHeight + u * 4  // serp-skin: the slim header\n"),
        # the island with its header, under the pages
        ("            // open: a desktop widget's pixel window (as clock.sh, music.sh), the title bar ours\n",
         "            // serp-skin: open, the skin's island instead of the pixel window — a slim header (the\n"
         "            // page's name; the pages' dots, the menu and close on the right), the pages under it\n"
         "            SGlass {\n"
         "                id: serpFrame\n"
         "                visible: Serp.on && win.expanded\n"
         "                anchors.fill: parent\n"
         "                backdrop: serpHaloBack\n"
         "                radius: Math.min(Serp.radius * 1.4, Serp.px(24))\n"
         "                Item {\n"
         "                    x: Serp.px(14)\n"
         "                    y: Serp.px(4)\n"
         "                    width: parent.width - Serp.px(22)\n"
         "                    height: win.cardTop - Serp.px(8)\n"
         "                    SText {\n"
         "                        anchors.left: parent.left\n"
         "                        anchors.right: serpTools.left\n"
         "                        anchors.rightMargin: Serp.px(8)\n"
         "                        anchors.verticalCenter: parent.verticalCenter\n"
         "                        text: win.headName\n"
         "                        bold: true\n"
         "                    }\n"
         "                    Row {\n"
         "                        id: serpTools\n"
         "                        anchors.right: parent.right\n"
         "                        anchors.verticalCenter: parent.verticalCenter\n"
         "                        spacing: Serp.px(2)\n"
         "                        Row {\n"
         "                            visible: !win.menu && !win.dropping && win.pages.length > 1\n"
         "                            anchors.verticalCenter: parent.verticalCenter\n"
         "                            rightPadding: Serp.px(6)\n"
         "                            Repeater {\n"
         "                                model: win.pages.length\n"
         "                                Item {\n"
         "                                    id: serpDot\n"
         "                                    required property int index\n"
         "                                    width: Serp.px(14)\n"
         "                                    height: Serp.px(22)\n"
         "                                    Rectangle {\n"
         "                                        anchors.centerIn: parent\n"
         "                                        width: serpDot.index === win.page ? Serp.px(14) : Serp.px(6)\n"
         "                                        height: Serp.px(6)\n"
         "                                        radius: height / 2\n"
         "                                        color: serpDot.index === win.page || (win.pages[serpDot.index] === \"events\" && win.eventsNew) || serpDotHover.hovered ? Serp.accent : Serp.overlay\n"
         "                                        Behavior on width {\n"
         "                                            NumberAnimation {\n"
         "                                                duration: Serp.quick\n"
         "                                                easing.type: Easing.OutCubic\n"
         "                                            }\n"
         "                                        }\n"
         "                                    }\n"
         "                                    HoverHandler {\n"
         "                                        id: serpDotHover\n"
         "                                        cursorShape: Qt.PointingHandCursor\n"
         "                                    }\n"
         "                                    TapHandler {\n"
         "                                        onTapped: win.page = serpDot.index\n"
         "                                    }\n"
         "                                }\n"
         "                            }\n"
         "                        }\n"
         "                        SButton {\n"
         "                            id: serpMenuBtn\n"
         "                            active: win.menu\n"
         "                            onClicked: {\n"
         "                                if (haloMenu.visible) {\n"
         "                                    haloMenu.close();\n"
         "                                    return;\n"
         "                                }\n"
         "                                const at = serpMenuBtn.mapToItem(null, 0, serpMenuBtn.height);\n"
         "                                win.expanded = false;\n"
         "                                haloMenu.popup(win.menuItems(), \"\", at.x, at.y);\n"
         "                            }\n"
         "                            SIcon {\n"
         "                                name: \"chevron-down\"\n"
         "                                size: Serp.px(15)\n"
         "                                color: Serp.subtext1\n"
         "                            }\n"
         "                        }\n"
         "                        SButton {\n"
         "                            onClicked: win.expanded = false\n"
         "                            SIcon {\n"
         "                                name: \"x\"\n"
         "                                size: Serp.px(15)\n"
         "                                color: Serp.subtext1\n"
         "                            }\n"
         "                        }\n"
         "                    }\n"
         "                }\n"
         "            }\n"
         "            // open: a desktop widget's pixel window (as clock.sh, music.sh), the title bar ours\n"),
        ("                id: frame\n                visible: win.expanded\n",
         "                id: frame\n                visible: win.expanded && !Serp.on  // serp-skin: the island above instead\n"),
        # the pages' controls in the modern look (PxButton, PxToggle, PxField… read settingsSkin)
        ("                Item {\n                    id: card\n",
         "                Item {\n                    id: card\n"
         "                    // serp-skin: the controls inside draw the modern look under the skin (\"classic\":\n"
         "                    // what Theme.settingsSkinFor found here without it)\n"
         "                    readonly property string settingsSkin: Serp.on ? \"goldengate\" : \"classic\"\n"),
        # the rule between events
        ("                                            color: win.hell ? Theme.hellEdge : Theme.edge\n",
         "                                            color: Serp.on ? Serp.line : win.hell ? Theme.hellEdge : Theme.edge  // serp-skin\n"),
        # a well (the plate under an event's picture, a cover…): a rounded plate of the skin
        ("        readonly property color base: win.hell ? Theme.hellSunken : Theme.sunken\n"
         "        color: lit || (clickable && wellHov.hovered) ? Theme.mix(base, win.accent, 0.22) : base\n"
         "        edgeColor: lit ? win.accent : win.hell ? Theme.hellEdge : Theme.edge\n",
         "        readonly property color base: win.hell ? Theme.hellSunken : Theme.sunken\n"
         "        color: Serp.on ? \"transparent\" : lit || (clickable && wellHov.hovered) ? Theme.mix(base, win.accent, 0.22) : base  // serp-skin\n"
         "        edgeColor: lit ? win.accent : win.hell ? Theme.hellEdge : Theme.edge\n"
         "        // serp-skin: no bevels and no outline — the rounded plate below draws it\n"
         "        outline: !Serp.on\n"
         "        flat: Serp.on || settingsSkin === \"windose\" || p5 || (Theme.zine && !hell)\n"
         "        Rectangle {\n"
         "            visible: Serp.on\n"
         "            anchors.fill: parent\n"
         "            radius: Serp.radiusSmall\n"
         "            color: well.lit || (well.clickable && well.hovered) ? Serp.selected : Serp.surface0\n"
         "            border.width: well.lit ? 1 : 0\n"
         "            border.color: Serp.accent\n"
         "        }\n"),
        # the bar of blocks: the skin's trough
        ("                    color: on ? (bb.paused ? Theme.textDim : win.accent) : Qt.alpha(Theme.text, 0.16)\n",
         "                    color: on ? (bb.paused ? (Serp.on ? Serp.overlay : Theme.textDim) : win.accent) : Serp.on ? Serp.surface1 : Qt.alpha(Theme.text, 0.16)  // serp-skin\n"),
        # running text and an event's head: the skin's text colours
        ("        property color color: dim ? Theme.textDim : Theme.text\n        property int align: Text.AlignLeft\n",
         "        property color color: Serp.on ? (dim ? Serp.subtext1 : Serp.text) : dim ? Theme.textDim : Theme.text  // serp-skin\n        property int align: Text.AlignLeft\n"),
        ("                color: hd.bad ? Theme.danger : Theme.text\n",
         "                color: hd.bad ? (Serp.on ? Serp.red : Theme.danger) : Serp.on ? Serp.text : Theme.text  // serp-skin\n"),
        # the quick buttons' tiles: rounded plates of the skin
        ("            sunken: qtTap.pressed || qt.on\n"
         "            color: qt.on ? win.accent : qtHover.hovered ? Theme.mix(win.hell ? Theme.hellFace : Theme.face, win.accent, 0.25) : win.hell ? Theme.hellFace : Theme.face\n"
         "        }\n",
         "            sunken: qtTap.pressed || qt.on\n"
         "            color: qt.on ? win.accent : qtHover.hovered ? Theme.mix(win.hell ? Theme.hellFace : Theme.face, win.accent, 0.25) : win.hell ? Theme.hellFace : Theme.face\n"
         "            visible: !Serp.on  // serp-skin\n"
         "        }\n"
         "        // serp-skin: the tile as the skin's plate\n"
         "        Rectangle {\n"
         "            visible: Serp.on\n"
         "            anchors.fill: parent\n"
         "            radius: Serp.radiusSmall\n"
         "            color: qt.on ? Serp.accent : qtHover.hovered ? Serp.surface1 : Serp.surface0\n"
         "            scale: qtTap.pressed ? 0.97 : 1\n"
         "            Behavior on color {\n"
         "                ColorAnimation {\n"
         "                    duration: Serp.quick\n"
         "                }\n"
         "            }\n"
         "        }\n"),
        ("                ink: qt.on ? Theme.selectText : (Theme.dark ? Theme.text : Theme.edge)\n",
         "                ink: Serp.on ? (qt.on ? Serp.onAccent : Serp.text) : qt.on ? Theme.selectText : (Theme.dark ? Theme.text : Theme.edge)  // serp-skin\n"),
        ("                color: qt.on ? Theme.selectText : Theme.text\n",
         "                color: Serp.on ? (qt.on ? Serp.onAccent : Serp.text) : qt.on ? Theme.selectText : Theme.text  // serp-skin\n"),
    ],
    # text under the modern look (settingsSkin "goldengate": the open Halo's card, the toasts,
    # plugin hosts) takes the skin's colours and font while the skin is on
    "widgets/PxText.qml": [
        ("import qs.config\n",
         "import qs.config\nimport qs.services  // serp-skin\n"),
        ("    color: dim ? (p5 ? Theme.p5Dim : Theme.textDim) : (p5 ? Theme.p5Black : Theme.text)\n",
         "    color: Serp.on && mac ? (dim ? Serp.subtext1 : Serp.text) : dim ? (p5 ? Theme.p5Dim : Theme.textDim) : (p5 ? Theme.p5Black : Theme.text)  // serp-skin\n"),
        ("    font.family: script ? Theme.fontScript : mac ? (kind === \"mono\" ? Theme.macMono : Theme.macFont) : p5Body ? Theme.fontP5Body : kind === \"body\" ? Theme.fontBody : kind === \"mono\" ? Theme.fontMono : Theme.fontTitle\n",
         "    font.family: script ? Theme.fontScript : mac ? (Serp.on ? Serp.font : kind === \"mono\" ? Theme.macMono : Theme.macFont) : p5Body ? Theme.fontP5Body : kind === \"body\" ? Theme.fontBody : kind === \"mono\" ? Theme.fontMono : Theme.fontTitle  // serp-skin\n"),
    ],
}
