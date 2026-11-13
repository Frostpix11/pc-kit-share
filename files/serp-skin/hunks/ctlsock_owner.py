# Only the main shell owns the key socket (ctl.sock: niri's desk / Alt+Tab / Mission keys). The
# capture overlay runs its own Quickshell (circle-root) and, once it built WorkspaceAnim (through the
# plugin theme -> Serp chain), it rm'd and re-bound the socket: after every screenshot the keys
# talked to the overlay, which answered "ok" and did nothing (2026-11-13).
HUNKS = {
    "services/WorkspaceAnim.qml": [
        ("    Process {\n        running: true\n        command: [\"sh\", \"-c\", 'mkdir -p \"$1\" && chmod 700 \"$1\" && rm -f \"$2\"'",
         "    Process {\n        running: Quickshell.shellDir.indexOf(\"circle-root\") < 0  // serp-skin: the main shell only\n        command: [\"sh\", \"-c\", 'mkdir -p \"$1\" && chmod 700 \"$1\" && rm -f \"$2\"'"),
        ("        active: root.socketReady\n",
         "        active: root.socketReady && Quickshell.shellDir.indexOf(\"circle-root\") < 0  // serp-skin\n"),
    ],
}
