# serp-skin: the skin's own cursor (angelOS-Serp, cursor/build.py) while it is on — through
# Golden Gate's way of wearing a skin's arrow (macCursor: the cursor before it is noted in
# Config.cursor.beforeMac and comes back when the skin goes). The macTheme line itself is
# pc-kit's mac-cursor patch: not touched here.
HUNKS = {
    "services/Cursors.qml": [
        ("    readonly property bool macCursor: GoldenGate.on && !hellOn && (macInstalled || other.includes(macTheme))\n",
         "    readonly property bool macCursor: (GoldenGate.on || serpArrow) && !hellOn && (serpArrow || macInstalled || other.includes(macTheme))  // serp-skin\n"
         "    // serp-skin: the skin's own arrow while it is on, as Golden Gate's\n"
         "    readonly property bool serpArrow: Serp.on && other.includes(\"angelOS-Serp\")\n"
         "    readonly property string skinArrow: serpArrow ? \"angelOS-Serp\" : macTheme\n"),
        ("        if (macCursor)\n            return macTheme;\n",
         "        if (macCursor)\n            return skinArrow;  // serp-skin\n"),
        ("        if (macCursor && now !== macTheme) {\n",
         "        if (macCursor && now !== skinArrow) {  // serp-skin\n"),
        ("                \"theme\": macTheme,\n",
         "                \"theme\": skinArrow,  // serp-skin\n"),
        ("        if (!macCursor && now === macTheme && Config.cursor.beforeMac) {\n",
         "        if (!macCursor && (now === macTheme || now === \"angelOS-Serp\") && Config.cursor.beforeMac) {  // serp-skin\n"),
    ],
}
