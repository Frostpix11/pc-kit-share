# serp-skin: the boot screen under the skin — «Пробуждение» (modules/serp/SerpBoot.qml) in place
# of the Y2K CD-ROM show, in the same window on the same clock (its once-a-login, its click to skip,
# Settings → Y2K's switch stay the author's). The window goes see-through under the skin: the show
# ends by opening onto the desktop. Its sound: modules/serp/sounds/boot.wav (tools/boot_sound.py).
HUNKS = {
    "modules/y2k/BootScreen.qml": [
        ("    NumberAnimation {\n        id: run\n        target: root\n        property: \"p\"\n        from: 0\n        to: 1\n        duration: Motion.ms(3400)\n        onFinished: root.finish()\n    }",
         "    // serp-skin: under the skin the show stops at «Готово» (0.84) until the wallpaper is\n"
         "    // drawn under it (Serp.wallsDrawn, at most 5 s), then the last part opens onto it\n"
         "    SequentialAnimation {\n"
         "        id: run\n"
         "        NumberAnimation {\n"
         "            target: root\n"
         "            property: \"p\"\n"
         "            from: 0\n"
         "            to: Serp.on ? 0.84 : 1\n"
         "            duration: Motion.ms(Serp.on ? 3400 * 0.84 : 3400)\n"
         "        }\n"
         "        ScriptAction {\n"
         "            script: Serp.on ? serpHold.restart() : root.finish()\n"
         "        }\n"
         "    }\n"
         "    Timer {\n"
         "        id: serpHold\n"
         "        interval: 50\n"
         "        repeat: true\n"
         "        property int n: 0\n"
         "        onTriggered: {\n"
         "            if (Serp.wallsDrawn(Shell.bootScreens) || ++n > 100) {\n"
         "                stop();\n"
         "                n = 0;\n"
         "                serpTail.restart();\n"
         "            }\n"
         "        }\n"
         "    }\n"
         "    NumberAnimation {\n"
         "        id: serpTail\n"
         "        target: root\n"
         "        property: \"p\"\n"
         "        from: 0.84\n"
         "        to: 1\n"
         "        duration: Motion.ms(3400 * 0.16)\n"
         "        onFinished: root.finish()\n"
         "    }"),
        ("    function finish() {\n        run.stop();\n",
         "    function finish() {\n        run.stop();\n        serpHold.stop();  // serp-skin\n        serpTail.stop();\n"),
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ('            color: Shell.bootOpen ? "#0c0710" : "#000000"\n',
         '            // serp-skin: the window is always made see-through, its colour drawn by a rectangle in it.\n            // At login the window is made before the settings are read (the skin unknown): made opaque\n            // then, its surface had no alpha, and serp\'s show opened onto black. Classic looks the same\n            color: "transparent"\n            Rectangle {\n                anchors.fill: parent\n                color: Serp.on ? (Shell.bootOpen ? "transparent" : "black") : Shell.bootOpen ? "#0c0710" : "#000000"\n            }\n'),
        ("                visible: Shell.bootOpen\n                opacity: root.p < 0.9",
         "                visible: Shell.bootOpen && !Serp.on  // serp-skin: SerpBoot instead\n                opacity: root.p < 0.9"),
        ("            MouseArea {\n                anchors.fill: parent\n                onClicked: root.finish()",
         "            // serp-skin: «Пробуждение»\n"
         "            SerpBoot {\n"
         "                anchors.fill: parent\n"
         "                visible: Shell.bootOpen && Serp.on\n"
         "                p: root.p\n"
         "                screenName: win.modelData.name\n"
         "            }\n"
         "            MouseArea {\n                anchors.fill: parent\n                onClicked: root.finish()"),
    ],
    # the show holds at «Готово» until the wallpaper is drawn under it, then opens onto it: at login
    # the wallpapers are still being found when the 3.4 s are up, and the circle opened onto an
    # empty (black) desktop for a moment (2026-11-13). At most 5 s of holding
    "modules/background/WallpaperView.qml": [
        ("    property bool waitingForLoad: false\n",
         "    property bool waitingForLoad: false\n"
         "    // serp-skin: the wallpaper is on screen — its picture loaded and the background window has\n"
         "    // put frames of it out since (at login Image.Ready came before the window's first frame:\n"
         "    // the boot show opened onto black for a moment). The boot show waits for it\n"
         "    readonly property bool serpDrawn: shown !== \"\" && progress >= 1 && toImg.status === Image.Ready\n"
         "    property int serpFrames: 0\n"
         "    onSerpDrawnChanged: {\n"
         "        serpFrames = 0;\n"
         "        if (!serpDrawn)\n"
         "            Serp.noteWallDrawn(screenName, false);\n"
         "    }\n"
         "    Connections {\n"
         "        target: root.serpDrawn && root.serpFrames < 2 ? root.Window.window : null\n"
         "        function onFrameSwapped() {\n"
         "            if (++root.serpFrames === 2)\n"
         "                Serp.noteWallDrawn(root.screenName, true);\n"
         "        }\n"
         "    }\n"),
    ],
    "services/Sounds.qml": [
        ('        if (macOwn("startup") && Date.now() - loginChimeAt < 8000)\n            return;\n        _play("startup", true, 1);',
         '        if (macOwn("startup") && Date.now() - loginChimeAt < 8000)\n            return;\n'
         '        if (Serp.on) {  // serp-skin: «Пробуждение» has its own\n'
         '            playFile(Quickshell.shellDir + "/modules/serp/sounds/boot.wav", 0.9);\n'
         '            return;\n'
         '        }\n'
         '        _play("startup", true, 1);'),
    ],
}
