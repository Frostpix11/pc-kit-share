# serp-skin: Mission Control (modules/mission/MissionControl.qml, Mod+W) in the skin's look
# (Serp.on only): the screen dimmed in the skin's crust, the desk strip on an island of the skin
# (SGlass: flat or liquid glass) with the desks as rounded plates (SerpMissionTile: the accent's
# ring on the current one, the plus as a line icon), the labels in the skin's font and colours
# (settingsSkin "goldengate" on the strip and the stage → PxText's mac branch), the picked window
# in a rounded accent frame, its title on a small plate of the skin.
HUNKS = {
    "modules/mission/MissionControl.qml": [
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ("                color: Qt.alpha(\"#000000\", (Mission.desktopUnder ? 0.3 : 0.78) * win.progress)\n",
         "                color: Qt.alpha(Serp.on ? Serp.crust : \"#000000\", (Mission.desktopUnder ? 0.3 : 0.78) * win.progress)  // serp-skin\n"),
        # the strip: on the skin's island
        ("            Row {\n                id: deskRow\n",
         "            // serp-skin: the wallpaper for the liquid glass, and the strip's island\n"
         "            SerpBackdrop {\n"
         "                id: serpMissionBack\n"
         "                origin: Qt.point(0, 0)\n"
         "            }\n"
         "            SGlass {\n"
         "                visible: Serp.on\n"
         "                anchors.fill: deskRow\n"
         "                anchors.margins: -Serp.px(12)\n"
         "                anchors.bottomMargin: -Serp.px(6)\n"
         "                backdrop: serpMissionBack\n"
         "                radius: Math.min(Serp.px(24), Math.round(Serp.radius * 1.4))\n"
         "                opacity: win.progress\n"
         "            }\n"
         "            Row {\n                id: deskRow\n"
         "                // serp-skin: its labels in the skin's font and colours; as before otherwise\n"
         "                readonly property string settingsSkin: Serp.on ? \"goldengate\" : Theme.settingsSkinFor(win.contentItem)\n"),
        # the clean desk 0
        ("                        color: zeroTile.hot ? Theme.accent : Theme.face\n"
         "                        edgeColor: win.zero && win.zero.is_active ? Theme.accent : Theme.edge\n",
         "                        color: Serp.on ? \"transparent\" : zeroTile.hot ? Theme.accent : Theme.face  // serp-skin\n"
         "                        edgeColor: win.zero && win.zero.is_active ? Theme.accent : Theme.edge\n"
         "                        outline: !Serp.on  // serp-skin\n"
         "                        flat: Serp.on || Theme.zine  // serp-skin\n"
         "                        SerpMissionTile {  // serp-skin\n"
         "                            visible: Serp.on\n"
         "                            anchors.fill: parent\n"
         "                            hot: zeroTile.hot\n"
         "                            current: !!win.zero && win.zero.is_active\n"
         "                            plus: true\n"
         "                        }\n"),
        ("                            ink: zeroTile.hot ? \"#ffffff\" : Theme.textDim\n",
         "                            ink: zeroTile.hot ? \"#ffffff\" : Theme.textDim\n"
         "                            visible: !Serp.on  // serp-skin\n"),
        ("                        text: I18n.t(\"Чистый стол\", \"Clean desk\")\n                        color: \"#ffffff\"\n",
         "                        text: I18n.t(\"Чистый стол\", \"Clean desk\")\n                        color: Serp.on ? Serp.text : \"#ffffff\"  // serp-skin\n"),
        # the desks
        ("                            color: win.dropDesk === deskTile.modelData.id ? Theme.accent : Theme.face\n"
         "                            edgeColor: deskTile.current ? Theme.accent : Theme.edge\n",
         "                            color: Serp.on ? \"transparent\" : win.dropDesk === deskTile.modelData.id ? Theme.accent : Theme.face  // serp-skin\n"
         "                            edgeColor: deskTile.current ? Theme.accent : Theme.edge\n"
         "                            outline: !Serp.on  // serp-skin\n"
         "                            flat: Serp.on || Theme.zine  // serp-skin\n"
         "                            SerpMissionTile {  // serp-skin\n"
         "                                visible: Serp.on\n"
         "                                anchors.fill: parent\n"
         "                                hot: win.dropDesk === deskTile.modelData.id\n"
         "                                current: deskTile.current\n"
         "                                plus: deskTile.list.length === 0\n"
         "                            }\n"),
        ("                                visible: deskTile.list.length === 0\n",
         "                                visible: deskTile.list.length === 0 && !Serp.on  // serp-skin\n"),
        ("                            text: win.deskName(deskTile.modelData)\n                            color: \"#ffffff\"\n",
         "                            text: win.deskName(deskTile.modelData)\n                            color: Serp.on ? Serp.text : \"#ffffff\"  // serp-skin\n"),
        # "+": a new desk
        ("                        color: win.dropDesk === -2 || plusArea.containsMouse ? Theme.accent : Theme.face\n"
         "                        edgeColor: Theme.edge\n",
         "                        color: Serp.on ? \"transparent\" : win.dropDesk === -2 || plusArea.containsMouse ? Theme.accent : Theme.face  // serp-skin\n"
         "                        edgeColor: Theme.edge\n"
         "                        outline: !Serp.on  // serp-skin\n"
         "                        flat: Serp.on || Theme.zine  // serp-skin\n"
         "                        SerpMissionTile {  // serp-skin\n"
         "                            visible: Serp.on\n"
         "                            anchors.fill: parent\n"
         "                            hot: win.dropDesk === -2 || plusArea.containsMouse\n"
         "                            plus: true\n"
         "                        }\n"),
        ("                            ink: win.dropDesk === -2 || plusArea.containsMouse ? \"#ffffff\" : Theme.textDim\n",
         "                            ink: win.dropDesk === -2 || plusArea.containsMouse ? \"#ffffff\" : Theme.textDim\n"
         "                            visible: !Serp.on  // serp-skin\n"),
        ("                        text: I18n.t(\"Новый стол\", \"New desk\")\n                        color: \"#ffffff\"\n",
         "                        text: I18n.t(\"Новый стол\", \"New desk\")\n                        color: Serp.on ? Serp.text : \"#ffffff\"  // serp-skin\n"),
        # the windows
        ("                id: stage\n                x: win.u * 16\n",
         "                id: stage\n                x: win.u * 16\n"
         "                // serp-skin: the titles in the skin's font; as before otherwise\n"
         "                readonly property string settingsSkin: Serp.on ? \"goldengate\" : Theme.settingsSkinFor(win.contentItem)\n"),
        ("                            color: card.lit ? Theme.accent : \"transparent\"\n"
         "                            outline: card.lit\n"
         "                            flat: true\n",
         "                            color: card.lit && !Serp.on ? Theme.accent : \"transparent\"  // serp-skin\n"
         "                            outline: card.lit && !Serp.on  // serp-skin\n"
         "                            flat: true\n"
         "                            // serp-skin: the picked window in a rounded accent frame\n"
         "                            Rectangle {\n"
         "                                visible: Serp.on && card.lit\n"
         "                                anchors.fill: parent\n"
         "                                radius: Serp.radiusSmall\n"
         "                                color: Serp.accent\n"
         "                            }\n"),
        ("                            color: Theme.face\n                            AppIcon {\n",
         "                            color: Serp.on ? Serp.solid : Theme.face  // serp-skin\n"
         "                            radius: Serp.on ? Serp.radiusSmall : 0  // serp-skin\n"
         "                            AppIcon {\n"),
        ("                        Row {\n"
         "                            anchors.horizontalCenter: parent.horizontalCenter\n"
         "                            y: parent.height + win.u * 3\n",
         "                        // serp-skin: the title on a small plate of the skin\n"
         "                        Rectangle {\n"
         "                            visible: Serp.on\n"
         "                            anchors.centerIn: serpTitleRow\n"
         "                            width: serpTitleRow.width + Serp.px(18)\n"
         "                            height: serpTitleRow.height + Serp.px(8)\n"
         "                            radius: height / 2\n"
         "                            color: Serp.solid\n"
         "                            opacity: win.progress\n"
         "                        }\n"
         "                        Row {\n"
         "                            id: serpTitleRow  // serp-skin\n"
         "                            anchors.horizontalCenter: parent.horizontalCenter\n"
         "                            y: parent.height + win.u * 3\n"),
        ("                                color: \"#ffffff\"\n                                text: card.hidden ?",
         "                                color: Serp.on ? Serp.text : \"#ffffff\"  // serp-skin\n                                text: card.hidden ?"),
        ("                    color: \"#ffffff\"\n                    opacity: win.progress\n",
         "                    color: Serp.on ? Serp.text : \"#ffffff\"  // serp-skin\n                    opacity: win.progress\n"),
    ],
}
