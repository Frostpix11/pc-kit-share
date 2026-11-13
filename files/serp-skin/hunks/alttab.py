# serp-skin: Alt+Tab / ⌘Tab in the skin's look (Serp.on only): AltTabHost loads modules/serp/
# SerpAltTab (a centred island of the skin, window cards, the pick in an accent ring) instead of
# AltTab.style's switcher or Golden Gate's ⌘Tab slab; hell's own switcher (Config.y2k.hellAltTab
# "hell") still wins while the demon rules. Keys, model and picking stay AltTabHost's.
HUNKS = {
    "modules/alttab/AltTabHost.qml": [
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ("            BackgroundEffect.blurRegion: AltTab.mode === \"apps\" && GoldenGate.on && GoldenGate.blurOn ? atBlur : null\n",
         "            BackgroundEffect.blurRegion: Serp.on ? (Serp.blurOn && !win.hellOwn ? serpAtBlur : null) : AltTab.mode === \"apps\" && GoldenGate.on && GoldenGate.blurOn ? atBlur : null  // serp-skin\n"
         "            // serp-skin: niri's blur under the skin's island, and the wallpaper for its liquid glass\n"
         "            Region {\n"
         "                id: serpAtBlur\n"
         "                item: stage\n"
         "                radius: Math.min(Serp.px(24), Math.round(Serp.radius * 1.4))\n"
         "            }\n"
         "            SerpBackdrop {\n"
         "                id: serpAtBack\n"
         "                origin: Qt.point(0, 0)\n"
         "            }\n"),
        ("                    sourceComponent: AltTab.mode === \"apps\" ? mac : win.hellOwn ? hell : AltTab.style === \"ngo\" ? ngo : AltTab.style === \"y2k\" ? y2k : angelos\n",
         "                    sourceComponent: Serp.on && !win.hellOwn ? serpLook : AltTab.mode === \"apps\" ? mac : win.hellOwn ? hell : AltTab.style === \"ngo\" ? ngo : AltTab.style === \"y2k\" ? y2k : angelos  // serp-skin\n"),
        ("            Component {\n                id: mac\n                AltTabMac {\n",
         "            // serp-skin: the skin's switcher\n"
         "            Component {\n"
         "                id: serpLook\n"
         "                SerpAltTab {\n"
         "                    host: win\n"
         "                    backdrop: serpAtBack\n"
         "                }\n"
         "            }\n"
         "            Component {\n                id: mac\n                AltTabMac {\n"),
    ],
}
