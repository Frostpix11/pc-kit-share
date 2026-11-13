# serp-skin: the sidebar (the heart tab's panel) in Serpantinum's look. Under Serp.on the phone
# look steps aside (Sidebar.phone false: the 3D flip phone is pixel art, the skin has no face for
# it) and SidebarHost loads SerpSidebarPanel (modules/serp) in the panel's window instead of the
# pixel SidebarPanel: an island full height at the tab's edge, the same blocks as cards, the
# window's own slide, catcher, keys and blur. apply.py itself hunks SidebarHost's tab (the heart
# island, its import) — these pairs sit elsewhere in the file. Classic / Golden Gate: as they were.

HUNKS = {
    "services/Sidebar.qml": [
        ('    readonly property bool phone: Config.sidebar.look !== "panel"\n',
         '    readonly property bool phone: Config.sidebar.look !== "panel" && !Serp.on  // serp-skin: the skin\'s side panel instead\n'
         '    readonly property bool serpSide: Serp.on  // serp-skin: the look swapped under it (the skin on / off): away\n'
         '    onSerpSideChanged: hide()  // serp-skin\n'),
    ],
    "modules/sidebar/SidebarHost.qml": [
        # the blur under the skin's island (rounded), by the skin's blur setting
        ("                BackgroundEffect.blurRegion: Config.appearance.blur && panelWin.shown && !Sidebar.phone ? blurRegion : null\n"
         "                Region {\n"
         "                    id: blurRegion\n"
         "                    item: panelLoader.item\n"
         "                }\n",
         "                BackgroundEffect.blurRegion: (Serp.on ? Serp.blurOn : Config.appearance.blur) && panelWin.shown && !Sidebar.phone ? blurRegion : null  // serp-skin\n"
         "                Region {\n"
         "                    id: blurRegion\n"
         "                    item: Serp.on ? (serpSideLoader.item ? serpSideLoader.item.island : null) : panelLoader.item  // serp-skin\n"
         "                    radius: Serp.on ? Math.min(Serp.radius * 1.4, Serp.px(24)) : 0  // serp-skin\n"
         "                }\n"),
        # the pixel panel only without the skin
        ("                    active: panelWin.shown && !Sidebar.phone\n",
         "                    active: panelWin.shown && !Sidebar.phone && !Serp.on  // serp-skin: SerpSidebarPanel instead\n"),
        ("                // built while the panel is shown only: closed, the sidebar holds no panel at all\n",
         "                // serp-skin: the skin's side panel (modules/serp/SerpSidebarPanel): an island at the edge\n"
         "                Loader {\n"
         "                    id: serpSideLoader\n"
         "                    anchors.fill: parent\n"
         "                    active: Serp.on && panelWin.shown && !Sidebar.phone\n"
         "                    sourceComponent: SerpSidebarPanel {\n"
         "                        host: panelWin\n"
         "                        edge: scope.edge\n"
         "                        screenName: scope.modelData.name\n"
         "                        toggles: serpQuick.list\n"
         "                        SidebarToggles {\n"
         "                            id: serpQuick\n"
         "                        }\n"
         "                    }\n"
         "                    // the phone gone with the look swap: no window left open with nothing in it\n"
         "                    Connections {\n"
         "                        target: Serp\n"
         "                        function onOnChanged() {\n"
         "                            panelWin.shown = false;\n"
         "                            panelWin.slideAt = 1;\n"
         "                        }\n"
         "                    }\n"
         "                }\n"
         "                // built while the panel is shown only: closed, the sidebar holds no panel at all\n"),
    ],
}
