import QtQuick
import Quickshell.Io
import qs.config
import qs.services
import "finale"

// Exposes scene/ (the author's 06-2004 with a night baked by his own scripts) as
// ~/Pictures/AngelOS-Night and shows it; disabling the plugin brings back the wallpaper before.
Item {
    id: root
    property var plugin
    property string sceneBase: Config.home + "/Pictures/AngelOS-Night"
    readonly property string base: sceneBase + "/"
    readonly property string selected: base + "reference/neutral-656x376.png"
    readonly property string author: Config.home + "/Pictures/AngelOS/06-2004"
    readonly property string skin: Config.wallpaper.themeOf || (Skin.mac ? "mac" : "pixel")
    property bool initialized: false
    property bool preparing: false
    property string error: ""

    function copy(v) { return JSON.parse(JSON.stringify(v)); }
    function pack(w) { return copy({fallback: w.fallback || "", outputs: w.outputs || {}, workspaces: w.workspaces || {}}); }
    function owns(w) { return !!w && String(w.fallback || "").startsWith(base); }
    function put(w) {
        Config.wallpaper.fallback = w.fallback;
        Config.wallpaper.outputs = copy(w.outputs);
        Config.wallpaper.workspaces = copy(w.workspaces);
    }
    function apply() {
        if (!plugin || !initialized || !Config.ready)
            return;
        if (skin !== (Skin.mac ? "mac" : "pixel")) {
            settle.restart();
            return;
        }
        const before = copy(plugin.get("before", {}));
        if (!before[skin] && !owns(Config.wallpaper)) {
            before[skin] = pack(Config.wallpaper);
            plugin.set("before", before);
        }
        put({fallback: selected, outputs: {}, workspaces: {}});
        error = "";
    }
    function restore() {
        if (!plugin)
            return;
        const before = plugin.get("before", {});
        const themes = copy(Config.wallpaper.themes || {});
        for (const key of Object.keys(before))
            if (owns(themes[key]))
                themes[key] = pack(before[key]);
        Config.wallpaper.themes = themes;
        if (owns(Config.wallpaper) && before[skin])
            put(before[skin]);
        plugin.set("before", {});
    }
    function initialize() {
        if (!plugin || initialized || preparing || !Config.ready)
            return;
        preparing = true;
        expose.command = ["python3", plugin.dir + "/ensure-scene.py", plugin.dir, Config.home + "/Pictures/AngelOS-Night"];
        expose.running = true;
    }
    // the author's scene's own settings (depth text, sounds, live effects) carry over to ours
    function carrySettings() {
        const perWall = copy(Config.wallpaper.perWall || {});
        if (!perWall[sceneBase]) {
            perWall[sceneBase] = Object.assign({}, perWall[author] || {}, {sceneDepth: (perWall[author] || {}).sceneDepth || "release"});
            Config.wallpaper.perWall = perWall;
        }
    }
    onPluginChanged: initialize()
    Component.onCompleted: initialize()
    onSkinChanged: if (initialized) settle.restart()
    Connections {
        target: Config
        function onReadyChanged() { root.initialize(); }
    }
    Timer {
        id: settle
        interval: 650
        onTriggered: root.apply()
    }
    Process {
        id: expose
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.sceneBase = JSON.parse(text).dir;
                    root.initialized = true;
                    root.preparing = false;
                    root.carrySettings();
                    Wallpapers.scan();
                    settle.restart();
                } catch (e) {
                    root.error = "Не удалось подготовить папку сцены";
                    root.preparing = false;
                }
            }
        }
    }
    Component.onDestruction: {
        if (!plugin || !initialized)
            return;
        const entry = Plugins.byId(plugin.id);
        // reload/shutdown keeps the wallpaper; restore only when disabled or removed
        if (!entry || !Plugins.isEnabled(entry))
            restore();
    }
    // the meteor's last seconds: the plunge, flash, shock ring, quake and sounds (finale/)
    FinaleFx {
        sceneDir: root.sceneBase
        fxDir: root.plugin ? root.plugin.dir + "/finale" : ""
    }
    IpcHandler {
        target: "angelos-night-2004"
        function select(): string { root.apply(); return "ok"; }
        // a look at the night by hand (services/SceneDebug, not saved): hour 0..24, -1 = the clock
        function hour(h: real): string { SceneDebug.hour = h; return "hour " + h; }
        // the meteor from age s (−2400 it appears, 0 the impact), paused or running
        function event(age: real, run: bool): string { SceneDebug.jump(age); SceneDebug.playing = run; return "event " + age; }
        function reset(): string { SceneDebug.reset(); return "clock"; }
        // the meteor's colour by hand: -1 tonight's, 0 its own, 1..5 red green blue purple gold
        function color(v: int): string { SceneDebug.variant = v; return "variant " + v; }
        // the debug timeline now: is it running, where, how fast
        function clock(): string { return JSON.stringify({on: SceneDebug.eventOn, age: SceneDebug.eventAge, playing: SceneDebug.playing, speed: SceneDebug.speed, hour: SceneDebug.hour}); }
        function state(): string {
            return JSON.stringify({selected: root.selected, shown: Config.wallpaper.fallback,
                scene: Wallpapers.sceneOf(Config.wallpaper.fallback), night: Wallpapers.nightOf(Config.wallpaper.fallback),
                error: root.error, saved: root.plugin.get("before", {})});
        }
    }
}
