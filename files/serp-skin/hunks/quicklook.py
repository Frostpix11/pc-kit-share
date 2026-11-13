# serp-skin: Quick Look (Space on a file: modules/quicklook/QuickLookWindow) in Serpantinum's look.
# The pixel PxWindow is worn as a rounded serp plate (modules/serp/SerpShotFrame: Serp.solid, SText
# title, a round × in SIcon); its content sits in a wrapper whose settingsSkin is "goldengate" under
# the skin (the PxWindow itself says "classic" to all inside it), so its buttons and texts draw
# modern; the text / folder wells and the video chip become rounded surface0 cards, the cut's
# frame and grips the skin's accent; the dim behind it the skin's crust. Classic / Golden Gate: as
# they were.


def well(head, indent, color="Theme.face", radius="Serp.radius"):
    """a PxBox opened by `head` drawn as a rounded card under the skin (its own fill see-through,
    no outline, no bevels; a Rectangle under its content)"""
    s = " " * indent
    return (head, head
            + f"{s}color: Serp.on ? \"transparent\" : {color}  // serp-skin\n"
            + f"{s}outline: !Serp.on  // serp-skin\n"
            + f"{s}flat: Serp.on || Theme.zine  // serp-skin (its own: Theme.zine here)\n"
            + f"{s}Rectangle {{  // serp-skin\n"
            + f"{s}    visible: Serp.on\n"
            + f"{s}    anchors.fill: parent\n"
            + f"{s}    z: -1\n"
            + f"{s}    radius: {radius}\n"
            + f"{s}    color: Serp.surface0\n"
            + f"{s}    border.width: 1\n"
            + f"{s}    border.color: Serp.line\n"
            + f"{s}}}\n")


HUNKS = {
    "modules/quicklook/QuickLookWindow.qml": [
        ("import qs.widgets\n", "import qs.widgets\nimport qs.modules.serp  // serp-skin\n"),
        ("            color: Qt.alpha(Theme.shadow, 0.35)\n",
         "            color: Serp.on ? Qt.alpha(Serp.crust, 0.3) : Qt.alpha(Theme.shadow, 0.35)  // serp-skin\n"),
        # the frame: the skin's plate and title strip over the pixel window
        ("            PxWindow {\n                id: dialog\n",
         "            SerpShotFrame {  // serp-skin\n"
         "                win: dialog\n"
         "                icon: ({\n"
         "                        \"folder\": \"folder\",\n"
         "                        \"image\": \"image\",\n"
         "                        \"video\": \"play\",\n"
         "                        \"audio\": \"music\",\n"
         "                        \"text\": \"file-text\",\n"
         "                        \"archive\": \"layers\",\n"
         "                        \"font\": \"type\"\n"
         "                    })[win.kind] || \"file\"\n"
         "            }\n"
         "            PxWindow {\n                id: dialog\n"),
        # the content in a wrapper that says "goldengate" to its Px* under the skin…
        ("                MouseArea {\n                    anchors.fill: parent\n                }\n\n                Item {\n                    id: stage\n",
         "                MouseArea {\n                    anchors.fill: parent\n                }\n\n"
         "                Item {  // serp-skin: the content's look (PxWindow says \"classic\" to all inside it)\n"
         "                readonly property string settingsSkin: Serp.on ? \"goldengate\" : \"classic\"\n"
         "                anchors.fill: parent\n"
         "                Item {\n                    id: stage\n"),
        # … closed at the window's end
        ("                    }\n                }\n            }\n            RightClickGuard {}\n",
         "                    }\n                }\n                }  // serp-skin: the wrapper's end\n            }\n            RightClickGuard {}\n"),
        # the video's chip, the text's well, the folder's list
        well("                        width: vrow.implicitWidth + win.u * 6\n                        height: vrow.implicitHeight + win.u * 4\n",
             24, radius="height / 2"),
        well("                        id: textView\n                        visible: win.kind === \"text\"\n                        anchors.fill: parent\n                        sunken: true\n",
             24),
        well("                            height: parent.height - listHead.height - win.u * 2\n                            sunken: true\n",
             28),
        # the cut of a video: the part kept and its grips in the skin's accent, rounded
        ("                            border.width: win.u\n                            border.color: Theme.accent\n",
         "                            border.width: win.u\n"
         "                            border.color: Serp.on ? Serp.accent : Theme.accent  // serp-skin\n"
         "                            radius: Serp.on ? Serp.radiusSmall : 0  // serp-skin\n"),
        ("                                color: grip.pressed || grip.containsMouse ? Theme.mix(Theme.accent, Theme.text, 0.25) : Theme.accent\n",
         "                                color: Serp.on ? (grip.pressed || grip.containsMouse ? Qt.lighter(Serp.accent, 1.2) : Serp.accent) : grip.pressed || grip.containsMouse ? Theme.mix(Theme.accent, Theme.text, 0.25) : Theme.accent  // serp-skin\n"
         "                                radius: Serp.on ? width / 2 : 0  // serp-skin\n"),
    ],
}
