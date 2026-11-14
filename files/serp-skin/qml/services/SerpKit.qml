pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

// serp-skin (Celestia, local): pc-kit's doctor inside the skin — `kit doctor --json`
// (~/pc-kit/kit/kit.py): our patches over angelOS and the system around them. Read by the bar's
// shield (SerpBar), its panel and the settings page «pc-kit» (settings/PageKit). Asked when the
// skin wakes, every 10 minutes, and when the panel or the page opens; not while a game runs
// (the check starts ~40 processes: systemctl, diff, git apply --check).
Singleton {
    id: root

    readonly property string kitBin: Quickshell.env("HOME") + "/.local/bin/kit"
    property var patches: []
    property var system: []
    property int bad: 0
    property int warn: 0
    property real at: 0               // ms of the last good answer
    property string error: ""         // kit missing, or its answer wasn't JSON
    readonly property bool busy: proc.running
    readonly property bool known: at > 0
    // ok | warn | bad | unknown — the shield's colour
    readonly property string state: !known ? "unknown" : bad > 0 ? "bad" : warn > 0 ? "warn" : "ok"
    readonly property int patchesOn: patches.filter(p => p.state === "on").length
    readonly property int patchesOff: patches.filter(p => p.state !== "on" && !p.disabled).length
    readonly property int patchesTaken: patches.filter(p => p.disabled && p.state !== "on").length
    readonly property int systemOk: system.filter(s => s.state === "ok" || s.state === "info").length
    // what needs a look, the worst first
    readonly property var problems: {
        const out = [];
        for (const p of patches)
            if (p.state !== "on" && !p.disabled)
                out.push({
                    "state": "bad",
                    "label": p.name,
                    "note": p.note || (p.state === "unfit" ? "не подходит к коду автора" : "слетел: kit apply " + p.name)
                });
        for (const s of system)
            if (s.state === "bad")
                out.push(s);
        for (const s of system)
            if (s.state === "warn")
                out.push(s);
        return out;
    }

    // the marks' colours: red and green are the theme's own danger / ok; the palette's «yellow» is
    // not a warning colour (in the wallpaper palette it is the titles' tint, bluish on a blue
    // wallpaper — 2026-11-14), so the warning is a fixed amber
    readonly property color warnColor: "#f2b544"
    function tone(s) {
        return s === "bad" || s === "unfit" ? Serp.red : s === "warn" || s === "off" ? warnColor : s === "ok" || s === "on" ? Serp.green : Serp.subtext;
    }

    function ago() {
        if (!known)
            return "ещё не проверяли";
        const m = Math.floor((Date.now() - at) / 60000);
        return m < 1 ? "только что" : m < 60 ? m + " мин назад" : Math.floor(m / 60) + " ч назад";
    }

    function refresh() {
        if (proc.running || !Serp.on)
            return;
        proc.running = true;
    }
    // the panel/page opened: ask again only when the answer is older than a minute
    function touch() {
        if (!known || Date.now() - at > 60000)
            refresh();
    }

    Process {
        id: proc
        command: [root.kitBin, "doctor", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(text);
                    root.patches = d.patches || [];
                    root.system = d.system || [];
                    root.bad = d.bad || 0;
                    root.warn = d.warn || 0;
                    root.at = Date.now();
                    root.error = "";
                } catch (e) {
                    root.error = text.trim() ? "kit ответил не JSON" : "kit не ответил (" + root.kitBin + ")";
                }
            }
        }
    }

    // ---- the inventory: every piece with the proof against the author (`kit inventory`), asked
    // when the panel opens (0.7 s) ----
    property var inv: null
    property real invAt: 0
    readonly property bool invBusy: invProc.running
    function loadInventory(force) {
        if (invProc.running || !Serp.on)
            return;
        if (!force && inv && Date.now() - invAt < 60000)
            return;
        invProc.running = true;
    }
    Process {
        id: invProc
        command: [root.kitBin, "inventory"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.inv = JSON.parse(text);
                    root.invAt = Date.now();
                } catch (e) {
                    root.error = "kit inventory ответил не JSON";
                }
            }
        }
    }
    function group(id) {
        return inv ? (inv.groups || []).find(g => g.id === id) || null : null;
    }

    // ---- one piece's changes, file by file (`kit diff ID`), asked when its card opens; kept ----
    property var diffs: ({})
    property string diffWant: ""
    readonly property string diffBusy: diffProc.running ? diffProc.wantId : ""
    function loadDiff(id) {
        if (!id || diffs[id])
            return;
        diffWant = id;
        if (!diffProc.running)
            diffNext();
    }
    function diffNext() {
        if (!diffWant || diffs[diffWant])
            return;
        diffProc.wantId = diffWant;
        diffProc.command = [root.kitBin, "diff", diffWant];
        diffProc.running = true;
    }
    Process {
        id: diffProc
        property string wantId: ""
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(text);
                    const m = Object.assign({}, root.diffs);
                    m[d.id] = d.files || [];
                    root.diffs = m;
                } catch (e) {}
            }
        }
        onExited: Qt.callLater(root.diffNext)
    }

    // ---- doing: apply / revert one patch. Detached (systemd-run): `kit apply` restarts the shell,
    // and a child of this shell would die with it half way; the answer comes as a notification ----
    property string acting: ""          // the patch being worked on
    function act(verb, name) {
        if (acting || (verb !== "apply" && verb !== "revert"))
            return;
        acting = name;
        actProc.command = ["systemd-run", "--user", "--collect", "--quiet", "--unit=pc-kit-" + verb + "-" + name.replace(/[^a-z0-9-]/g, "") + "-" + Date.now(), root.kitBin, verb, name, "--notify"];
        actProc.running = true;
        actDone.restart();
    }
    Process {
        id: actProc
    }
    // a patch that doesn't restart the shell: look again after a moment (one that does, brings a
    // new shell, and the new one asks on its own)
    Timer {
        id: actDone
        interval: 4000
        onTriggered: {
            root.acting = "";
            root.diffs = ({});
            root.refresh();
            root.loadInventory(true);
        }
    }

    Timer {
        interval: 10 * 60 * 1000
        repeat: true
        triggeredOnStart: true
        running: Serp.on && Serp.awake && !GoldenGate.gameMode
        // the inventory too (0.7 s): the panel opens full, not «Собираю…» first
        onTriggered: {
            root.refresh();
            root.loadInventory(true);
        }
    }

    // the panel (panels/SerpKitPanel): `qs -c angelos ipc call serpkit panel`, a key bind; `show`
    // opens it on one piece (showReq, read by the panel when it is built and while it is open)
    property var showReq: null
    // the panel's left side: "tree" (SerpKitTree) | "list"; kept while the shell runs
    property string mode: "tree"
    IpcHandler {
        target: "serpkit"
        function panel(): string {
            if (!Serp.on)
                return "the serp skin is off";
            Serp.togglePanel("kit", Niri.focusedOutput || Shell.primaryName);
            return Serp.panel || "closed";
        }
        // open the panel on one piece: `ipc call serpkit open shell halo-game-sleep diff`
        // (tab: shell | niri | satellite | plugins | system | audit; view: about | diff | history)
        function open(tab: string, name: string, view: string): string {
            if (!Serp.on)
                return "the serp skin is off";
            root.showReq = {
                "tab": tab || "shell",
                "name": name || "",
                "view": view || "about",
                "n": Date.now()
            };
            if (Serp.panel !== "kit")
                Serp.openPanel("kit", Niri.focusedOutput || Shell.primaryName);
            return "ok";
        }
        // the panel's left side: tree | list
        function mode(m: string): string {
            if (m === "tree" || m === "list")
                root.mode = m;
            return root.mode;
        }
        function refresh(): string {
            root.refresh();
            root.loadInventory(true);
            return root.state;
        }
        function status(): string {
            return JSON.stringify({
                "state": root.state,
                "bad": root.bad,
                "warn": root.warn,
                "patches": root.patchesOn + "/" + root.patches.length,
                "error": root.error,
                "ago": root.ago()
            });
        }
    }
}
