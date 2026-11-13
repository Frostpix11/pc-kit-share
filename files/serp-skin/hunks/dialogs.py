# serp-skin: angelOS's dialogs in Serpantinum's look — the session menu and its confirm, the polkit
# password, and the one-off prompts of shell.qml (update, main screen, telemetry, Settings look,
# the author's apps). Each window keeps its keys, its functions and its pixel frame; under Serp.on
# the frame is hidden (opacity 0 where its own focus item lives inside it, so the keys still
# land there; visible false where the keys live beside it) and a SerpDialog* card
# (modules/serp) is laid over it, calling the window's own functions. Classic / Golden Gate: as
# they were.

IMPORT = ("import qs.widgets\n", "import qs.widgets\nimport qs.modules.serp  // serp-skin\n")


def shade(indent):
    s = " " * indent
    return (f"{s}color: Qt.alpha(Theme.shadow, 0.35)\n",
            f"{s}color: Serp.on ? Qt.alpha(Serp.crust, 0.25) : Qt.alpha(Theme.shadow, 0.35)  // serp-skin\n")


def blur(indent, item):
    s = " " * indent
    return (f"{s}BackgroundEffect.blurRegion: Config.appearance.blur ? blurRegion : null\n"
            f"{s}Region {{\n{s}    id: blurRegion\n{s}    item: {item}\n{s}}}\n",
            f"{s}BackgroundEffect.blurRegion: (Serp.on ? Serp.blurOn : Config.appearance.blur) ? blurRegion : null  // serp-skin\n"
            f"{s}Region {{\n{s}    id: blurRegion\n{s}    item: Serp.on ? serpDlg.card : {item}  // serp-skin\n"
            f"{s}    radius: Serp.on ? Serp.radius + Serp.px(4) : 0  // serp-skin\n{s}}}\n")


def hide_frame(head, indent, how="opacity"):
    """the pixel frame steps aside under the skin: `head` is its opening lines"""
    s = " " * (indent + 4)
    line = (f"{s}opacity: Serp.on ? 0 : 1  // serp-skin: hidden, its keys still listen (SerpDialog* draws)\n"
            if how == "opacity" else f"{s}visible: !Serp.on  // serp-skin: SerpDialog* draws\n")
    return (head, head + line)


def face(indent, qml):
    s = " " * indent
    return (f"{s}RightClickGuard {{}}\n", f"{s}{qml}  // serp-skin\n\n{s}RightClickGuard {{}}\n")


HUNKS = {
    "modules/session/SessionMenu.qml": [
        IMPORT,
        shade(4),
        blur(4, "dialog"),
        hide_frame("    PxWindow {\n        id: dialog\n", 4),
        face(4, "SerpDialogSession { id: serpDlg; host: win }"),
    ],
    "modules/session/SessionConfirm.qml": [
        IMPORT,
        shade(4),
        blur(4, "card"),
        hide_frame("    SessionConfirmCard {\n        id: card\n", 4),
        face(4, "SerpDialogConfirm { id: serpDlg; host: card }"),
    ],
    "modules/polkit/PolkitDialog.qml": [
        IMPORT,
        shade(8),
        blur(8, "dialog"),
        hide_frame("        PxWindow {\n            id: dialog\n", 8),
        face(8, "SerpDialogPolkit { id: serpDlg; flow: root.flow; field: field }"),
    ],
    "modules/settings/UpdatePrompt.qml": [
        IMPORT,
        shade(4),
        blur(4, "dialog"),
        hide_frame("    PxWindow {\n        id: dialog\n", 4),
        face(4, "SerpDialogUpdate { id: serpDlg; host: win }"),
    ],
    "modules/settings/MainScreenPrompt.qml": [
        IMPORT,
        shade(4),
        hide_frame("    PxWindow {\n        id: dialog\n", 4, "visible"),
        face(4, "SerpDialogScreen { id: serpDlg; host: win }"),
    ],
    "modules/settings/TelemetryPrompt.qml": [
        IMPORT,
        shade(4),
        hide_frame("    PxWindow {\n        anchors.centerIn: parent\n", 4, "visible"),
        face(4, "SerpDialogTelemetry { id: serpDlg; host: win }"),
    ],
    "modules/settings/SettingsLookPrompt.qml": [
        IMPORT,
        shade(4),
        hide_frame("    PxWindow {\n        anchors.centerIn: parent\n", 4, "visible"),
        face(4, "SerpDialogLook { id: serpDlg; host: win }"),
    ],
    # a floating window as big as its card: under the skin, as big as ours
    "modules/settings/AppsSyncPrompt.qml": [
        IMPORT,
        ("    implicitWidth: dialog.width + rim * 2\n    implicitHeight: dialog.height + rim * 2\n",
         "    implicitWidth: (Serp.on ? serpDlg.cardWidth + Serp.px(32) : dialog.width) + rim * 2  // serp-skin\n"
         "    implicitHeight: (Serp.on ? serpDlg.card.height : dialog.height) + rim * 2  // serp-skin\n"),
        blur(4, "dialog"),
        hide_frame("    AppsSyncCard {\n        id: dialog\n", 4),
        face(4, "SerpDialogApps { id: serpDlg; host: dialog }"),
    ],
}
