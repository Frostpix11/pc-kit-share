# serp-skin: the toasts in the skin's look (Serp.on only). The achievement card (its `mac` branch,
# Skin.mac, is on under the skin) lies on an SGlass island instead of Golden Gate's Liquid Glass
# card (SkinCard → MacGlass), its words in the skin's colours and font; hell keeps hell's card.
# (Its controls already take the modern look: body's settingsSkin "goldengate"; PxText's colours
# come from hunks/halo_open.py's PxText hunk.)
HUNKS = {
    "modules/y2k/AchievementToast.qml": [
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ("            // the card: hover holds it, a click opens the page (or the diary)\n",
         "            // serp-skin: the wallpaper in screen space for the island's liquid glass\n"
         "            SerpBackdrop {\n"
         "                id: serpToastBack\n"
         "            }\n"
         "            // the card: hover holds it, a click opens the page (or the diary)\n"),
        ("                // ---- pixel and Golden Gate ----\n                SkinCard {\n                    visible: !root.hell\n",
         "                // serp-skin: the skin's island (Golden Gate's glass card steps aside)\n"
         "                SGlass {\n"
         "                    visible: Serp.on && !root.hell\n"
         "                    anchors.fill: parent\n"
         "                    backdrop: serpToastBack\n"
         "                    radius: Math.min(Serp.radius * 1.4, Serp.px(24))\n"
         "                }\n"
         "                // ---- pixel and Golden Gate ----\n                SkinCard {\n                    visible: !root.hell && !Serp.on  // serp-skin\n"),
        ("                                    color: \"#ffffff\"\n                                    size: GoldenGate.px(22)\n",
         "                                    color: Serp.on ? Serp.onAccent : \"#ffffff\"  // serp-skin\n                                    size: GoldenGate.px(22)\n"),
        ("                                    color: root.hell ? Theme.hellGold : Theme.textDim\n                                    font.letterSpacing:",
         "                                    color: root.hell ? Theme.hellGold : Serp.on ? Serp.subtext1 : Theme.textDim  // serp-skin\n                                    font.letterSpacing:"),
        ("                                    font.family: root.hell ? Theme.fontHell : mac ? Theme.macFont : Theme.fontTitle\n",
         "                                    font.family: root.hell ? Theme.fontHell : mac ? (Serp.on ? Serp.font : Theme.macFont) : Theme.fontTitle  // serp-skin\n"),
        ("                                    color: root.hell ? Theme.hellText : Theme.text\n",
         "                                    color: root.hell ? Theme.hellText : Serp.on ? Serp.text : Theme.text  // serp-skin\n"),
        ("                                    color: root.hell ? Theme.hellTextDim : Theme.text\n"
         "                                    font.family: root.hell ? Theme.fontHellText : mac ? Theme.macFont : Theme.fontBody\n",
         "                                    color: root.hell ? Theme.hellTextDim : Serp.on ? Serp.subtext1 : Theme.text  // serp-skin\n"
         "                                    font.family: root.hell ? Theme.fontHellText : mac ? (Serp.on ? Serp.font : Theme.macFont) : Theme.fontBody  // serp-skin\n"),
        # the thing's slot
        ("root.mac ? Qt.rgba(0, 0, 0, GoldenGate.dark ? 0.25 : 0.06) : Theme.sunken\n",
         "root.mac ? (Serp.on ? Serp.surface0 : Qt.rgba(0, 0, 0, GoldenGate.dark ? 0.25 : 0.06)) : Theme.sunken  // serp-skin\n"),
        ("                                        color: root.hell ? Theme.hellGold : Theme.accent\n",
         "                                        color: root.hell ? Theme.hellGold : Serp.on ? Serp.accent : Theme.accent  // serp-skin\n"),
        ("                                        color: root.hell ? Theme.hellGold : Theme.text\n",
         "                                        color: root.hell ? Theme.hellGold : Serp.on ? Serp.text : Theme.text  // serp-skin\n"),
        ("                                        color: root.hell ? Theme.hellTextDim : Theme.textDim\n",
         "                                        color: root.hell ? Theme.hellTextDim : Serp.on ? Serp.subtext1 : Theme.textDim  // serp-skin\n"),
    ],
}
