# serp-skin: Start under the Serpantinum skin — StartOverlay's look "serp" (modules/serp/
# SerpLauncher: Serpantinum's launcher look over Golden Gate's Spotlight logic), centred a fifth
# down the screen as the Spotlight looks are, with the Spotlight's deep settings (StartPrefs).
# And the separate app launcher (modules/launcher/Launcher, Mod+Space, Shell.launcherOpen) is not
# built while the skin is on: its call opens the serp Start instead (LazyWindows).
# Anchors stay out of StartOverlay.qml L141-180 (pc-kit codex-fixes: fix-golden-gate-spotlight-blur)
# and off LazyWindows' clipboard loader (apply.py's own hunk).
HUNKS = {
    "modules/bar/StartOverlay.qml": [
        ("import qs.modules.mac\n",
         "import qs.modules.mac\nimport qs.modules.serp  // serp-skin\n"),
        ('        readonly property string style: hellish ? "hell" : GoldenGate.on ? "mac" : StartPrefs.current\n',
         '        readonly property string style: hellish ? "hell" : Serp.on ? "serp" : GoldenGate.on ? "mac" : StartPrefs.current  // serp-skin\n'),
        ('        readonly property bool spot: style === "spotlight" || style === "mac"\n',
         '        readonly property bool spot: style === "spotlight" || style === "mac" || style === "serp"  // serp-skin\n'),
        ('        readonly property var prefs: StartPrefs.of(style === "hell" ? "classic" : style === "mac" ? "spotlight" : style)\n',
         '        readonly property var prefs: StartPrefs.of(style === "hell" ? "classic" : style === "mac" || style === "serp" ? "spotlight" : style)  // serp-skin\n'),
        ('                    "mac": macComp,\n',
         '                    "mac": macComp,\n                    "serp": serpComp,  // serp-skin\n'),
        ("        Component {\n            id: macComp\n            MacSpotlight {}\n        }\n",
         "        Component {\n            id: macComp\n            MacSpotlight {}\n        }\n"
         "        // serp-skin: Start in the Serpantinum look\n"
         "        Component {\n            id: serpComp\n            SerpLauncher {}\n        }\n"),
    ],
    "modules/LazyWindows.qml": [
        # the launcher's window is not built under the skin…
        ("        activeAsync: launcherKeep.alive || root.launcherWarm\n",
         "        activeAsync: (launcherKeep.alive || root.launcherWarm) && !Serp.on  // serp-skin\n"),
        # …its call opens the serp Start (what was handed to it typed into Start's search)
        ("            if (Shell.launcherOpen)\n                launcherLoader.active = true;\n",
         "            if (Shell.launcherOpen && Serp.on) {  // serp-skin: Start instead\n"
         "                Shell.launcherOpen = false;\n"
         "                const pre = Shell.launcherPrefill;\n"
         "                Shell.launcherPrefill = \"\";\n"
         "                if (pre)\n"
         "                    Shell.startPrefill = pre;\n"
         "                if (Shell.startScreen !== \"\" && !pre)\n"
         "                    Shell.closeStart();\n"
         "                else\n"
         "                    Shell.openStart(\"\");\n"
         "            } else if (Shell.launcherOpen)\n                launcherLoader.active = true;\n"),
    ],
}
