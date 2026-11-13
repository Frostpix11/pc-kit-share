# serp-skin: the lock screen in Serpantinum's look. modules/lock/LockScreen picks a face by
# Config.lock.style (NGO / heaven / 2004); under Serp.on it loads modules/serp/SerpLock instead —
# the same lockScope, the same props. Auth is untouched: Lock.qml (PAM, the session lock surface,
# the finger, the sleep inhibitor) is not hunked at all; SerpLock types into angelOS's own
# HeartPassword (invisible) and calls lockScope.submit() like the NGO face. The other screens'
# "the password is on the main screen" plate gets the skin's capsule. Classic / Golden Gate: as
# they were.

HUNKS = {
    "modules/lock/LockScreen.qml": [
        ("import qs.widgets\n",
         "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ('        sourceComponent: root.lockScope.look === "heaven" ? heaven : root.lockScope.look === "2004" ? save : ngo\n',
         '        sourceComponent: Serp.on ? serpLook : root.lockScope.look === "heaven" ? heaven : root.lockScope.look === "2004" ? save : ngo  // serp-skin\n'),
        ("    Component {\n        id: ngo\n",
         "    Component {  // serp-skin: the skin's face\n"
         "        id: serpLook\n"
         "        SerpLock {\n"
         "            screenName: root.screenName\n"
         "            primary: root.primary\n"
         "            lockScope: root.lockScope\n"
         "            now: clock.date\n"
         "            preview: root.preview\n"
         "        }\n"
         "    }\n"
         "    Component {\n        id: ngo\n"),
        ("        PxBox {\n            anchors.horizontalCenter: parent.horizontalCenter\n            anchors.bottom: parent.bottom\n",
         "        // serp-skin: the plate as the skin's capsule\n"
         "        Rectangle {\n"
         "            visible: Serp.on\n"
         "            anchors.horizontalCenter: parent.horizontalCenter\n"
         "            anchors.bottom: parent.bottom\n"
         "            anchors.bottomMargin: Serp.px(48)\n"
         "            width: serpHint.implicitWidth + Serp.px(40)\n"
         "            height: Serp.px(42)\n"
         "            radius: height / 2\n"
         "            color: Qt.alpha(Serp.base, 0.72)\n"
         "            border.width: 1\n"
         "            border.color: Serp.line\n"
         "            SText {\n"
         "                id: serpHint\n"
         "                anchors.centerIn: parent\n"
         "                text: hint.text\n"
         "                bold: true\n"
         "                elide: Text.ElideNone\n"
         "            }\n"
         "        }\n"
         "        PxBox {\n            visible: !Serp.on  // serp-skin\n"
         "            anchors.horizontalCenter: parent.horizontalCenter\n            anchors.bottom: parent.bottom\n"),
    ],
}
