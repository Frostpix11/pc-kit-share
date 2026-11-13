# the plugins' popovers (BarPopup) get the liquid glass under the skin: the popup works out where it
# stands on the screen from the bar item it hangs from (as the compositor places it: its right edge
# at the item's right edge, under the bar, slid in from the screen's edges)
HUNKS = {
    "modules/bar/BarPopup.qml": [
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ("    MacGlass {\n        id: macPanel\n",
         "    // serp-skin: where this popup stands on its screen, for the glass's wallpaper\n"
         "    readonly property var serpBarWin: root.anchorItem ? root.anchorItem.QsWindow.window : null\n"
         "    readonly property point serpOrigin: {\n"
         "        if (!root.anchorItem || !serpBarWin)\n"
         "            return Qt.point(0, 0);\n"
         "        const p = root.anchorItem.mapToItem(null, 0, 0);\n"
         "        const sw = serpBarWin.screen ? serpBarWin.screen.width : serpBarWin.width;\n"
         "        const ax = p.x + root.anchor.rect.x + root.anchor.rect.width;\n"
         "        const ay = p.y + root.anchor.rect.y + root.anchor.rect.height;\n"
         "        const x = Math.max(0, Math.min(sw - root.width, ax - root.width));\n"
         "        return Qt.point(x, root.above ? ay - root.height : ay);\n"
         "    }\n"
         "    SerpBackdrop {\n"
         "        id: serpPopBack\n"
         "        active: Serp.glassOn && root.mac\n"
         "        screenName: root.serpBarWin && root.serpBarWin.screen ? root.serpBarWin.screen.name : \"\"\n"
         "        origin: root.serpOrigin\n"
         "    }\n"
         "    MacGlass {\n        id: macPanel\n"),
        ("        focus: root.mac\n        Keys.onEscapePressed: PopupManager.close(root)\n",
         "        focus: root.mac\n        Keys.onEscapePressed: PopupManager.close(root)\n"
         "        // serp-skin: the liquid glass over the flat plate (menus: dense and frosted, text reads)\n"
         "        SGlass {\n"
         "            visible: Serp.glassOn\n"
         "            anchors.fill: parent\n"
         "            backdrop: serpPopBack\n"
         "            radius: macPanel.radius  // its content item has none (an undefined → double warning)\n"
         "            tintAmount: Math.max(Serp.cfg.glassTint, 0.7)\n"
         "            frost: 10\n"
         "            bezel: Serp.px(10)  // a thin lens edge like the islands: a thick one stretched the wallpaper into bars\n"
         "        }\n"),
    ],
}
