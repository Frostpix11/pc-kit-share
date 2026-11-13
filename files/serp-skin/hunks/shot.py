# serp-skin: the screenshot editor (modules/capture/ShotEditor) and the Quick Share window
# (modules/quickshare/ShareView) in Serpantinum's look. Both hardcode settingsSkin "classic" on
# their body: under Serp.on it is "goldengate", so their Px* controls (buttons, checks, texts) draw
# modern at once. The pixel PxWindow frame is worn as a rounded serp plate (modules/serp/
# SerpShotFrame: Serp.solid — they sit over windows — SText title, round ×); the editor's tools
# become SerpShotTools (round pills, the tool in hand in the accent) on plates of their own, and its
# swatches, size dots, stickers, recent shots and the shot's well get round corners. Classic /
# Golden Gate: as they were.

IMPORT = ("import qs.widgets\n", "import qs.widgets\nimport qs.modules.serp  // serp-skin\n")

HUNKS = {
    "modules/capture/ShotEditor.qml": [
        IMPORT,
        # the frame: the skin's plate and title strip over the pixel window
        ("    PxWindow {\n        id: frame\n        anchors.fill: parent\n        anchors.rightMargin: Theme.u * 2\n",
         "    SerpShotFrame {  // serp-skin\n"
         "        win: frame\n"
         "        icon: \"image\"\n"
         "    }\n"
         "    PxWindow {\n        id: frame\n        anchors.fill: parent\n        anchors.rightMargin: Theme.u * 2\n"),
        ("            readonly property string settingsSkin: \"classic\"\n            readonly property int gap: Theme.u * 3\n",
         "            readonly property string settingsSkin: Serp.on ? \"goldengate\" : \"classic\"  // serp-skin\n"
         "            readonly property int gap: Theme.u * 3\n"),
        # plates under the top row, the tools and the tool's options; the skin's tools
        ("            // ---- along the top: undo, the zoom, what to do with the result\n",
         "            // serp-skin: rounded surface0 plates under the toolbars, the skin's tool pills\n"
         "            Repeater {\n"
         "                model: Serp.on ? [top, serpTools, side] : []\n"
         "                Rectangle {\n"
         "                    required property Item modelData\n"
         "                    readonly property int m: Serp.px(6)\n"
         "                    x: modelData.x - m\n"
         "                    y: modelData.y - m\n"
         "                    width: modelData.width + m * 2\n"
         "                    height: (modelData === top ? modelData.height : modelData.implicitHeight) + m * 2\n"
         "                    radius: Serp.radius\n"
         "                    color: Serp.surface0\n"
         "                    border.width: 1\n"
         "                    border.color: Serp.line\n"
         "                }\n"
         "            }\n"
         "            SerpShotTools {\n"
         "                id: serpTools\n"
         "                visible: Serp.on\n"
         "                editor: ed\n"
         "                x: toolCol.x\n"
         "                y: toolCol.y\n"
         "                width: toolCol.width\n"
         "            }\n"
         "            // ---- along the top: undo, the zoom, what to do with the result\n"),
        ("                id: toolCol\n",
         "                id: toolCol\n                visible: !Serp.on  // serp-skin: SerpShotTools\n"),
        # the colours: round swatches, a ring of the text's colour round the one in use
        ("                            border.width: on ? Theme.u : 1\n                            border.color: on ? Theme.accent : Theme.edge\n",
         "                            border.width: on ? (Serp.on ? Serp.px(3) : Theme.u) : 1  // serp-skin\n"
         "                            border.color: on ? (Serp.on ? Serp.text : Theme.accent) : Serp.on ? Serp.line : Theme.edge  // serp-skin\n"
         "                            radius: Serp.on ? width / 2 : 0  // serp-skin\n"),
        # the sizes: round wells
        ("                            color: ed.level === index ? Qt.alpha(Theme.accent, 0.3) : Theme.sunken\n"
         "                            border.width: 1\n"
         "                            border.color: ed.level === index ? Theme.accent : Theme.edge\n",
         "                            color: Serp.on ? (ed.level === index ? Serp.selected : Serp.surface1) : ed.level === index ? Qt.alpha(Theme.accent, 0.3) : Theme.sunken  // serp-skin\n"
         "                            border.width: 1\n"
         "                            border.color: Serp.on ? (ed.level === index ? Serp.accent : Serp.line) : ed.level === index ? Theme.accent : Theme.edge  // serp-skin\n"
         "                            radius: Serp.on ? width / 2 : 0  // serp-skin\n"),
        # the stickers
        ("                            color: ed.sticker === modelData ? Qt.alpha(Theme.accent, 0.3) : Theme.sunken\n"
         "                            border.width: 1\n"
         "                            border.color: ed.sticker === modelData ? Theme.accent : Theme.edge\n",
         "                            color: Serp.on ? (ed.sticker === modelData ? Serp.selected : Serp.surface1) : ed.sticker === modelData ? Qt.alpha(Theme.accent, 0.3) : Theme.sunken  // serp-skin\n"
         "                            border.width: 1\n"
         "                            border.color: Serp.on ? (ed.sticker === modelData ? Serp.accent : Serp.line) : ed.sticker === modelData ? Theme.accent : Theme.edge  // serp-skin\n"
         "                            radius: Serp.on ? Serp.radiusSmall : 0  // serp-skin\n"),
        # the recent shots
        ("                        color: Theme.sunken\n                        border.width: here ? Theme.u : 1\n                        border.color: here ? Theme.accent : Theme.edge\n",
         "                        color: Serp.on ? Serp.surface0 : Theme.sunken  // serp-skin\n"
         "                        border.width: here ? (Serp.on ? Serp.px(2) : Theme.u) : 1  // serp-skin\n"
         "                        border.color: here ? (Serp.on ? Serp.accent : Theme.accent) : Serp.on ? Serp.line : Theme.edge  // serp-skin\n"
         "                        radius: Serp.on ? Serp.radiusSmall : 0  // serp-skin\n"),
        # the shot's well
        ("            PxBox {\n                anchors.fill: view\n                anchors.margins: -Theme.u\n                sunken: true\n                color: Theme.sunken\n            }\n",
         "            PxBox {\n                visible: !Serp.on  // serp-skin\n                anchors.fill: view\n                anchors.margins: -Theme.u\n                sunken: true\n                color: Theme.sunken\n            }\n"
         "            Rectangle {  // serp-skin: the shot's well, rounded\n"
         "                visible: Serp.on\n"
         "                anchors.fill: view\n"
         "                anchors.margins: -Serp.px(4)\n"
         "                radius: Serp.radius\n"
         "                color: Qt.alpha(Serp.crust, 0.6)\n"
         "                border.width: 1\n"
         "                border.color: Serp.line\n"
         "            }\n"),
    ],
    "modules/quickshare/ShareView.qml": [
        IMPORT,
        ("    PxWindow {\n        id: frame\n        anchors.fill: parent\n        anchors.rightMargin: view.u * 2\n",
         "    SerpShotFrame {  // serp-skin\n"
         "        win: frame\n"
         "        icon: \"airplay\"\n"
         "    }\n"
         "    PxWindow {\n        id: frame\n        anchors.fill: parent\n        anchors.rightMargin: view.u * 2\n"),
        ("            readonly property string settingsSkin: \"classic\"\n            width: parent.width\n",
         "            readonly property string settingsSkin: Serp.on ? \"goldengate\" : \"classic\"  // serp-skin\n"
         "            width: parent.width\n"),
        # what goes: a rounded well
        ("                sunken: true\n                color: Theme.sunken\n                PxText {\n                    visible: !view.something\n",
         "                sunken: true\n"
         "                color: Serp.on ? \"transparent\" : Theme.sunken  // serp-skin\n"
         "                outline: !Serp.on  // serp-skin\n"
         "                flat: Serp.on || Theme.zine  // serp-skin (its own: Theme.zine here)\n"
         "                Rectangle {  // serp-skin\n"
         "                    visible: Serp.on\n"
         "                    anchors.fill: parent\n"
         "                    z: -1\n"
         "                    radius: Serp.radius\n"
         "                    color: Serp.surface0\n"
         "                    border.width: 1\n"
         "                    border.color: Serp.line\n"
         "                }\n"
         "                PxText {\n                    visible: !view.something\n"),
        # the radar: smooth rings instead of pixel squares
        ("                        ctx.reset();\n                        const g = view.u;\n",
         "                        ctx.reset();\n                        const g = view.u;\n"
         "                        if (Serp.on) {  // serp-skin: smooth rings in the skin's accent\n"
         "                            const R = Math.min(width, height) / 2 - g;\n"
         "                            ctx.lineWidth = Serp.px(2);\n"
         "                            for (let k = 0; k < 3; k++) {\n"
         "                                const t = (phase + k / 3) % 1;\n"
         "                                ctx.strokeStyle = Qt.alpha(Serp.accent, 0.55 * (1 - t));\n"
         "                                ctx.beginPath();\n"
         "                                ctx.arc(radar.cx, radar.cy, R * (0.25 + 0.75 * t), 0, 2 * Math.PI);\n"
         "                                ctx.stroke();\n"
         "                            }\n"
         "                            return;\n"
         "                        }\n"),
        # files dragged over the window
        ("        color: Qt.alpha(Theme.accent, 0.16)\n        border.width: Math.max(2, view.u)\n        border.color: Theme.accent\n",
         "        color: Qt.alpha(Serp.on ? Serp.accent : Theme.accent, 0.16)  // serp-skin\n"
         "        border.width: Math.max(2, view.u)\n"
         "        border.color: Serp.on ? Serp.accent : Theme.accent  // serp-skin\n"
         "        radius: Serp.on ? Serp.radius : 0  // serp-skin\n"),
    ],
}
