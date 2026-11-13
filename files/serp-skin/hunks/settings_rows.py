# serp-skin: Settings, phase B (plan: notes/plan-settings-start.md) — the catalog's rows as
# Serpantinum's settings rows, and what stayed Mac-white under the skin. With the skin on and a
# page in the Golden Gate look (settingsSkin "goldengate", which SettingsView keeps under serp),
# CatalogPage's Entry loads modules/serp/settings/CatRow.qml for toggle / choice / slider / spin
# and labelled buttons; fields, links, notes, bare buttons and custom parts stay angelOS's (the
# slot keeps label/hint/isNew, so the search and the «new» stars find the row as before).
# The Px widgets' Mac look (PxToggle, PxSlider, PxButton), the section tiles (SettingsTile,
# CategoryPage's cards) and the search results wear the skin's tokens. Everything gated on
# Serp.on: Classic and Golden Gate are untouched.
HUNKS = {
    "modules/settings/CatalogPage.qml": [
        ("import qs.modules.settings.kit\n",
         "import qs.modules.settings.kit\nimport qs.modules.serp.settings  // serp-skin: CatRow\n"),
        ("        readonly property bool catRow: true\n        readonly property bool fixedWidth: true\n",
         "        readonly property bool catRow: true\n        readonly property bool fixedWidth: true\n"
         "        // serp-skin: the skin on, a Golden Gate page: Serpantinum's rows (CatRow)\n"
         "        readonly property bool serpRow: Serp.on && Theme.settingsSkinFor(slot.parent) === \"goldengate\"  // serp-skin\n"),
        ("            const k = modelData.kind;\n",
         "            const k = modelData.kind;\n"
         "            if (slot.serpRow && (k === \"toggle\" || k === \"choice\" || k === \"slider\" || k === \"spin\" || (k === \"button\" && modelData.label)))  // serp-skin\n"
         "                return serpCatRow;\n"),
        ("        onLoaded: item.entry = modelData\n",
         "        onLoaded: item.entry = modelData\n"
         "        Component {  // serp-skin\n"
         "            id: serpCatRow\n"
         "            CatRow {\n"
         "                entry: slot.modelData\n"
         "            }\n"
         "        }\n"),
    ],
    # the Mac switch: Serpantinum's (the accent, a knob in onAccent; off: surface2, subtext1 knob)
    "widgets/PxToggle.qml": [
        ("        color: root.shown ? GoldenGate.accent : GoldenGate.dark ? Qt.rgba(1, 1, 1, 0.18) : Qt.rgba(0, 0, 0, 0.1)\n",
         "        color: root.shown ? GoldenGate.accent : Serp.on ? Serp.surface2 : GoldenGate.dark ? Qt.rgba(1, 1, 1, 0.18) : Qt.rgba(0, 0, 0, 0.1)  // serp-skin\n"),
        ("            color: \"#ffffff\"\n            border.width: 1\n            border.color: Qt.rgba(0, 0, 0, 0.08)\n",
         "            color: Serp.on ? (root.shown ? Serp.onAccent : Serp.subtext1) : \"#ffffff\"  // serp-skin\n"
         "            border.width: Serp.on ? 0 : 1  // serp-skin\n"
         "            border.color: Qt.rgba(0, 0, 0, 0.08)\n"),
    ],
    # the Mac slider: a 6 px surface2 track, an accent knob ringed in base
    "widgets/PxSlider.qml": [
        ("        height: GoldenGate.px(4)\n        radius: height / 2\n        color: GoldenGate.dark ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(0, 0, 0, 0.12)\n",
         "        height: Serp.on ? Serp.px(6) : GoldenGate.px(4)  // serp-skin\n        radius: height / 2\n"
         "        color: Serp.on ? Serp.surface2 : GoldenGate.dark ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(0, 0, 0, 0.12)  // serp-skin\n"),
        ("        color: \"#ffffff\"\n        border.width: 1\n        border.color: Qt.rgba(0, 0, 0, mouse.pressed ? 0.25 : 0.14)\n",
         "        color: Serp.on ? Serp.accent : \"#ffffff\"  // serp-skin\n"
         "        border.width: Serp.on ? Serp.px(2) : 1  // serp-skin\n"
         "        border.color: Serp.on ? Serp.base : Qt.rgba(0, 0, 0, mouse.pressed ? 0.25 : 0.14)  // serp-skin\n"),
    ],
    # the Mac button: surface1/2 plates (no white), radiusSmall, onAccent ink on the accent
    "widgets/PxButton.qml": [
        ("        radius: GoldenGate.px(7)\n        color: root.accent || root.checked ? (mouse.pressed ? Qt.darker(GoldenGate.accent, 1.12) : GoldenGate.accent) : mouse.pressed ? GoldenGate.hoverBg : GoldenGate.dark ? Qt.rgba(1, 1, 1, mouse.containsMouse ? 0.18 : 0.12) : mouse.containsMouse ? \"#fafafa\" : \"#ffffff\"\n        border.width: root.accent || root.checked ? 0 : 1\n",
         "        radius: Serp.on ? Serp.radiusSmall : GoldenGate.px(7)  // serp-skin\n"
         "        color: root.accent || root.checked ? (mouse.pressed ? Qt.darker(GoldenGate.accent, 1.12) : GoldenGate.accent) : Serp.on ? (mouse.containsMouse || mouse.pressed ? Serp.surface2 : Serp.surface1) : mouse.pressed ? GoldenGate.hoverBg : GoldenGate.dark ? Qt.rgba(1, 1, 1, mouse.containsMouse ? 0.18 : 0.12) : mouse.containsMouse ? \"#fafafa\" : \"#ffffff\"  // serp-skin\n"
         "        border.width: root.accent || root.checked || Serp.on ? 0 : 1  // serp-skin\n"),
        ("            color: root.accent || root.checked ? \"#ffffff\" : root.danger ? GoldenGate.lights[0] : GoldenGate.label\n",
         "            color: root.accent || root.checked ? (Serp.on ? Serp.onAccent : \"#ffffff\") : root.danger ? (Serp.on ? Serp.red : GoldenGate.lights[0]) : GoldenGate.label  // serp-skin\n"),
        ("root.mac ? (root.accent || root.checked ? \"#ffffff\" : root.danger ? GoldenGate.lights[0] : GoldenGate.label) :",
         "root.mac ? (root.accent || root.checked ? (Serp.on ? Serp.onAccent : \"#ffffff\") : root.danger ? (Serp.on ? Serp.red : GoldenGate.lights[0]) : GoldenGate.label) :  /* serp-skin */"),
    ],
    # the section tiles (sidebar, link cards, folding cards): rounded, the accent, no bevel
    "widgets/SettingsTile.qml": [
        ("import qs.config\n",
         "import qs.config\nimport qs.services  // serp-skin\n"),
        ("    width: size\n    height: size\n    color: tint\n    border.width: Math.max(1, Theme.u / 2)\n    border.color: Qt.darker(tint, 1.45)\n",
         "    // serp-skin: the skin's accent, rounded, flat\n"
         "    readonly property color face: Serp.on ? Serp.accent : tint  // serp-skin\n"
         "    width: size\n    height: size\n    color: face  // serp-skin\n"
         "    radius: Serp.on ? Serp.radiusSmall : 0  // serp-skin\n"
         "    border.width: Serp.on ? 0 : Math.max(1, Theme.u / 2)  // serp-skin\n"
         "    border.color: Qt.darker(tint, 1.45)\n"),
        ("        height: Math.max(1, Theme.u / 2)\n        color: Qt.lighter(root.tint, 1.35)\n",
         "        height: Math.max(1, Theme.u / 2)\n        visible: !Serp.on  // serp-skin\n        color: Qt.lighter(root.tint, 1.35)\n"),
        ("        ink: \"#ffffff\"\n        fill: Qt.lighter(root.tint, 1.45)\n        fill2: Qt.lighter(root.tint, 1.3)\n        fill3: Qt.lighter(root.tint, 1.6)\n        light: Qt.lighter(root.tint, 1.8)\n        bad: \"#ffffff\"\n        body: Qt.darker(root.tint, 1.3)\n",
         "        ink: Serp.on ? Serp.onAccent : \"#ffffff\"  // serp-skin\n"
         "        fill: Qt.lighter(root.face, 1.45)  // serp-skin: face (= tint without the skin)\n"
         "        fill2: Qt.lighter(root.face, 1.3)\n        fill3: Qt.lighter(root.face, 1.6)\n        light: Qt.lighter(root.face, 1.8)\n"
         "        bad: Serp.on ? Serp.onAccent : \"#ffffff\"\n        body: Qt.darker(root.face, 1.3)\n"),
    ],
    # a category's page: its cards as SetRow cards
    "modules/settings/CategoryPage.qml": [
        ("                color: cardMouse.containsMouse ? Theme.mix(Theme.faceAlt, Theme.accent, 0.12) : Theme.mix(Theme.face, Theme.faceAlt, 0.55)\n"
         "                border.width: Math.max(1, Theme.u / 2)\n",
         "                color: Serp.on ? Qt.alpha(cardMouse.containsMouse ? Serp.surface1 : Serp.surface0, 0.4) : cardMouse.containsMouse ? Theme.mix(Theme.faceAlt, Theme.accent, 0.12) : Theme.mix(Theme.face, Theme.faceAlt, 0.55)  // serp-skin\n"
         "                radius: Serp.on ? Serp.radius : 0  // serp-skin\n"
         "                border.width: Serp.on ? 0 : Math.max(1, Theme.u / 2)  // serp-skin\n"),
    ],
    # the search: results and history in the skin's selection, the found row flashed in its accent
    "modules/settings/SettingsView.qml": [
        ("            color: Qt.alpha(Theme.accent, 0.12)\n            border.width: Math.max(2, Theme.u)\n            border.color: Theme.accent\n",
         "            color: Qt.alpha(Serp.on ? Serp.accent : Theme.accent, 0.12)  // serp-skin\n"
         "            radius: Serp.on ? Serp.radius : 0  // serp-skin\n"
         "            border.width: Math.max(2, Theme.u)\n"
         "            border.color: Serp.on ? Serp.accent : Theme.accent  // serp-skin\n"),
        ("                        color: picked ? Theme.select : hm.containsMouse ? Theme.mix(Theme.face, Theme.accent, 0.15) : \"transparent\"\n",
         "                        color: Serp.on ? (picked ? Serp.selected : hm.containsMouse ? Serp.hover : \"transparent\") : picked ? Theme.select : hm.containsMouse ? Theme.mix(Theme.face, Theme.accent, 0.15) : \"transparent\"  // serp-skin\n"
         "                        radius: Serp.on ? Serp.radiusSmall : 0  // serp-skin\n"),
        ("                                ink: hist.picked ? Theme.selectText : (Theme.dark ? Theme.text : Theme.edge)\n",
         "                                ink: Serp.on ? (hist.picked ? Serp.accent : Serp.subtext0) : hist.picked ? Theme.selectText : (Theme.dark ? Theme.text : Theme.edge)  // serp-skin\n"),
        ("                                    color: hist.picked ? Theme.selectText : Theme.text\n",
         "                                    color: Serp.on ? (hist.picked ? Serp.accent : Serp.text) : hist.picked ? Theme.selectText : Theme.text  // serp-skin\n"),
        ("                                    color: hist.picked ? Theme.selectText : Theme.textDim\n",
         "                                    color: Serp.on ? Serp.subtext0 : hist.picked ? Theme.selectText : Theme.textDim  // serp-skin\n"),
        ("                        color: picked ? Theme.select : rm.containsMouse ? Theme.mix(Theme.face, Theme.accent, 0.15) : \"transparent\"\n",
         "                        color: Serp.on ? (picked ? Serp.selected : rm.containsMouse ? Serp.hover : \"transparent\") : picked ? Theme.select : rm.containsMouse ? Theme.mix(Theme.face, Theme.accent, 0.15) : \"transparent\"  // serp-skin\n"
         "                        radius: Serp.on ? Serp.radiusSmall : 0  // serp-skin\n"),
        ("                                ink: res.picked ? Theme.selectText : (Theme.dark ? Theme.text : Theme.edge)\n",
         "                                ink: Serp.on ? (res.picked ? Serp.accent : Serp.subtext0) : res.picked ? Theme.selectText : (Theme.dark ? Theme.text : Theme.edge)  // serp-skin\n"),
        ("                                    color: res.picked ? Theme.selectText : Theme.text\n",
         "                                    color: Serp.on ? (res.picked ? Serp.accent : Serp.text) : res.picked ? Theme.selectText : Theme.text  // serp-skin\n"),
        ("                                    color: res.picked ? Theme.selectText : Theme.textDim\n",
         "                                    color: Serp.on ? Serp.subtext0 : res.picked ? Theme.selectText : Theme.textDim  // serp-skin\n"),
    ],
}
