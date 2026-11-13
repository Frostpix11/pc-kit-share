import QtQuick
import Quickshell.Io
import qs.config
import qs.services

Item {
    id: root
    property var plugin
    readonly property string base: Config.home + "/Pictures/AngelOS-Room/"
    readonly property string mode: plugin ? plugin.get("mode", "night") : "night"
    readonly property string skin: Config.wallpaper.themeOf || (Skin.mac ? "mac" : "pixel")
    readonly property bool night: mode === "night" || (mode === "auto" && Theme.night)
    readonly property string selected: base + (night ? "night" : "day") + "/reference/neutral-656x376.png"
    property bool initialized: false
    property string error: ""

    function copy(v) { return JSON.parse(JSON.stringify(v)); }
    function pack(w) {
        return copy({fallback: w.fallback || "", outputs: w.outputs || {}, workspaces: w.workspaces || {}});
    }
    function owns(w) { return !!w && String(w.fallback || "").startsWith(base); }
    function put(w) {
        Config.wallpaper.fallback = w.fallback;
        Config.wallpaper.outputs = copy(w.outputs);
        Config.wallpaper.workspaces = copy(w.workspaces);
    }
    function apply() {
        if (!plugin || !initialized || !Config.ready)
            return;
        // GoldenGate switches its saved wallpaper slot after a short settle timer.
        // Wait for themeOf to identify the actual active slot before saving it.
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
        // A wallpaper chosen independently while the plugin ran takes precedence.
        if (owns(Config.wallpaper) && before[skin])
            put(before[skin]);
        plugin.set("before", {});
    }
    function initialize() {
        if (!plugin || initialized)
            return;
        initialized = true;
        // Own settings use the release folder for the author's scene, but our
        // independent collection uses its scene dirs. Preserve its depth mode
        // explicitly so ReleaseMark stays suppressed and text remains behind city.
        const perWall = copy(Config.wallpaper.perWall || {});
        const original = perWall[Config.home + "/Pictures/AngelOS/06-2004"] || {};
        for (const variant of ["day", "night"]) {
            const key = base + variant;
            if (!perWall[key])
                perWall[key] = Object.assign({}, original, {sceneDepth: "release"});
        }
        Config.wallpaper.perWall = perWall;
        Wallpapers.scan();
        settle.restart();
    }
    onPluginChanged: initialize()
    Component.onCompleted: initialize()
    onSelectedChanged: if (initialized) settle.restart()
    onSkinChanged: if (initialized) settle.restart()
    Connections {
        target: Config
        function onReadyChanged() { if (Config.ready) settle.restart(); }
    }
    Timer {
        id: settle
        interval: 650
        onTriggered: root.apply()
    }
    Component.onDestruction: {
        if (!plugin || !initialized)
            return;
        const entry = Plugins.byId(plugin.id);
        // Reload/shutdown keeps the wallpaper and recovery snapshot. Restore only
        // when the user actually disables or removes this plugin.
        if (!entry || !Plugins.isEnabled(entry))
            restore();
    }
    IpcHandler {
        target: "angelos-room"
        function mode(value: string): string {
            if (!["day", "night", "auto"].includes(value))
                return "Use day, night or auto";
            root.plugin.set("mode", value);
            root.apply();
            return value;
        }
        function state(): string {
            return JSON.stringify({mode: root.mode, night: root.night, selected: root.selected,
                shown: Config.wallpaper.fallback, scene: Wallpapers.sceneOf(Config.wallpaper.fallback),
                skin: root.skin, error: root.error, saved: root.plugin.get("before", {})});
        }
    }
}
