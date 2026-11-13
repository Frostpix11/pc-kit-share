# serp-skin: the screensaver in Serpantinum's look. modules/idle/IdleScreen keeps its windows, its
# triggers and its wake-up (any key, click, wheel or move after the arming delay); under Serp.on
# the ASCII art and the AOD face step aside and modules/serp/SerpIdle draws (aod: the dim black
# face on the other screens). Classic / Golden Gate: as they were.

HUNKS = {
    "modules/idle/IdleScreen.qml": [
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ("            visible: win.aod\n",
         "            visible: win.aod && !Serp.on  // serp-skin: SerpIdle draws\n"),
        ("            active: !win.aod\n",
         "            active: !win.aod && !Serp.on  // serp-skin: SerpIdle draws\n"),
        ("        RightClickGuard {}\n",
         "        // serp-skin: the skin's face (it takes no input: the window's own ends the screensaver)\n"
         "        Loader {\n"
         "            anchors.fill: parent\n"
         "            active: Serp.on\n"
         "            sourceComponent: Component {\n"
         "                SerpIdle {\n"
         "                    screenName: win.modelData ? win.modelData.name : \"\"\n"
         "                    aod: win.aod\n"
         "                }\n"
         "            }\n"
         "        }\n"
         "\n        RightClickGuard {}\n"),
    ],
}
