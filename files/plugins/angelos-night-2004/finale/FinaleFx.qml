import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.config
import qs.services

// The meteor's end, which the author's night engine leaves out (widgets/SceneEvent: it creeps
// for forty minutes, then a dome of fire is just there). The author's meteor stops high in the
// sky (our scene.json's path) and goes out at the event's moment; from there this plunges it
// behind the houses in `fall` seconds, faster and faster. At the impact the light comes at once
// — a flash over the whole scene — in silence; the shock ring spreads over the sky and reaches
// us `delay` seconds later with the sound (it is far): the blast, the screen shaken (the
// demon's quake with its rocks, ScreenQuake), the rubble coming down. Before it, the roar of it
// coming in. Drawn on the Bottom layer: over the wallpaper and its desktop widgets
// (they live in the wallpaper's own window), under every app window; light added, not painted.
Item {
    id: fx

    required property string sceneDir     // ~/Pictures/AngelOS-Night (what Wallpapers reports)
    required property string fxDir        // the plugin's finale/ (shader, front mask)
    property var info: null               // scene.json night.event
    property int cw: 656
    property int ch: 376
    FileView {
        path: fx.sceneDir ? fx.sceneDir + "/scene.json" : ""
        printErrors: false
        onLoaded: {
            try {
                const s = JSON.parse(text());
                fx.cw = s.logical_canvas.width;
                fx.ch = s.logical_canvas.height;
                fx.info = s.night && s.night.event ? s.night.event : null;
            } catch (e) {
                fx.info = null;
            }
        }
    }
    Component.onCompleted: {
        debugAge = SceneDebug.eventAge;
        debugAt = Date.now();
    }

    readonly property real fall: 1.6        // s from the author's meteor going out to the impact
    readonly property real delay: 3.5       // s the blast's sound and shock take to reach us
    readonly property point hold: info ? Qt.point(info.meteor.path[2][0], info.meteor.path[2][1]) : Qt.point(0, 0)
    readonly property point hit: info ? Qt.point(info.fire.origin[0] - 2, info.fire.origin[1]) : Qt.point(0, 0)
    readonly property real scale0: info ? info.meteor.scale[1] : 0.75

    // ---- the event's age, smooth: the clock to the millisecond, the debug page between its steps
    property real debugAge: NaN
    property real debugAt: 0
    Connections {
        target: SceneDebug
        function onEventAgeChanged() {
            fx.debugAge = SceneDebug.eventAge;
            fx.debugAt = Date.now();
        }
    }
    function ageNow() {
        if (SceneDebug.eventOn) {
            const run = SceneDebug.playing ? SceneDebug.speed : 0;
            return debugAge + Math.min(0.3, (Date.now() - debugAt) / 1000) * run;
        }
        return Wallpapers.nightEvent(new Date());
    }
    function shownOn(name) {
        const s = SceneSound.sceneOn(name);
        return !!s && s.dir === sceneDir && Wallpapers.nightMix(s.path, new Date()) > 0.2;
    }
    readonly property bool live: Config.wallpaper.live !== false && !Wallpapers.hellOn

    property real age: NaN
    property real lastAge: NaN
    // near the end it ticks every frame; the rest of the night, twice a second
    readonly property bool close: isFinite(age) && age > -15 && age < 10
    Timer {
        running: fx.live && fx.info !== null && !fx.close
        interval: 500
        repeat: true
        onTriggered: fx.step()
    }
    FrameAnimation {
        running: fx.live && fx.info !== null && fx.close
        onTriggered: fx.step()
    }
    function step() {
        const a = ageNow();
        // the debug page's "whole meteor" runs ×20: the last seconds at their own pace
        if (SceneDebug.eventOn && SceneDebug.speed > 1 && a > -12)
            SceneDebug.speed = 1;
        if (isFinite(a) && isFinite(lastAge) && a > lastAge && a - lastAge < 30)
            cues(lastAge, a);
        lastAge = a;
        age = a;
    }
    function past(from, to, at) {
        return from < at && to >= at;
    }
    function cues(from, to) {
        const vol = SceneSound.eventVol;
        const seen = Shell.screens.some(s => shownOn(s.name));
        if (!seen)
            return;
        if (vol > 0 && past(from, to, -7))
            Sounds.playFile(fxDir + "/approach.ogg", Math.min(2, vol * 1.4));
        // the blast, loud (the player goes up to ×2), when its sound arrives; with it the shock
        // shakes the screen, then the rubble comes down
        const heard = fall + delay;
        if (vol > 0 && past(from, to, heard))
            Sounds.playFile(fxDir + "/boom.ogg", Math.min(2, vol * 2.2));
        if (vol > 0 && past(from, to, heard + 0.3))
            Sounds.playFile(fxDir + "/debris.ogg", Math.min(2, vol * 1.4));
        if (past(from, to, heard))
            quake();
    }
    // the swap's quake (Settings → Y2K → Screen shake), on the first screen showing the night
    function quake() {
        if (!Config.y2k.shake || Story.calm)
            return;
        for (const s of Shell.screens)
            if (shownOn(s.name) && StreamMode.effectsOn(s.name) && !Shell.fullscreenOn(s.name)) {
                Angel.quake(s.name, "hell");      // the demon's: rocks tumbling down, their sound
                return;
            }
    }

    // ---- what is drawn, by the age
    function smooth(x) {
        x = Math.max(0, Math.min(1, x));
        return x * x * (3 - 2 * x);
    }
    readonly property bool falling: isFinite(age) && age >= 0 && age < fall
    readonly property real u: falling ? age / fall : 0
    readonly property real dive: Math.pow(u, 2.4)                 // faster and faster
    readonly property point head: Qt.point(Math.round(hold.x + (hit.x - hold.x) * dive), Math.round(hold.y + (hit.y - hold.y) * dive))
    readonly property real size: scale0 + 0.5 * dive
    readonly property real after: isFinite(age) ? age - fall : -1
    readonly property real flash: after >= 0 && after < 2.5 ? Math.exp(-after / 0.32) * (1 - Math.exp(-after / 0.02)) : 0
    // the shock ring: from the impact out past the screen's edges, arriving as the blast is heard
    readonly property real ring: after >= 0 && after < delay ? after / delay : -1
    readonly property bool active: falling || flash > 0.003 || ring >= 0
    // tonight's colour (Wallpapers.nightVariant, seeded by the date; the debug page's pick): the
    // author's meteor, fire, light and shards take it, so the plunge and the flash do too —
    // the same table as widgets/SceneWall.fires ([deep, mid, hot]; 0 = the meteor's own)
    readonly property var fires: [null, ["#3a0612", "#d8203c", "#ffd6c8"], ["#04281c", "#20d880", "#e2ffe8"], ["#081440", "#3c8cff", "#eaf4ff"], ["#220838", "#a446ff", "#f6e2ff"], ["#3c2204", "#ffb424", "#fffbe6"]]
    readonly property var tonight: active ? fires[Wallpapers.nightVariant(new Date())] || null : null
    readonly property color hot: "#fff2d6"
    readonly property color mid: "#ffb455"
    readonly property color deep: "#c2431b"

    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: win
            required property var modelData
            screen: modelData
            visible: fx.active && fx.live && fx.shownOn(modelData.name)
            color: "transparent"
            anchors {
                top: true
                bottom: true
                left: true
                right: true
            }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.namespace: "angelos-night-finale"
            mask: Region {}

            // the scene's view, as widgets/SceneWall lays it out (canvas inset by 8, whole scales snapped)
            readonly property real k: {
                const c = Math.max(width / (fx.cw - 16), height / (fx.ch - 16));
                return Math.abs(c - Math.round(c)) < 0.02 * c ? Math.round(c) : c;
            }
            readonly property real ox: Math.round((width - fx.cw * k) / 2)
            readonly property real oy: Math.round((height - fx.ch * k) / 2)

            // art pixels: the meteor, its trail, the ring
            Item {
                id: art
                width: fx.cw
                height: fx.ch
                visible: false

                // the trail: back up its path, longer the faster it goes
                Repeater {
                    model: 26
                    Rectangle {
                        required property int index
                        readonly property real f: index / 26
                        readonly property real len: 6 + 46 * fx.dive
                        readonly property real dx: fx.hold.x - fx.hit.x
                        readonly property real dy: fx.hold.y - fx.hit.y
                        readonly property real n: Math.max(1, Math.hypot(dx, dy))
                        visible: fx.falling
                        x: Math.round(fx.head.x + dx / n * len * f)
                        y: Math.round(fx.head.y + dy / n * len * f)
                        width: f < 0.35 ? 2 : 1
                        height: width
                        color: f < 0.25 ? fx.hot : f < 0.6 ? fx.mid : fx.deep
                        opacity: (1 - f) * (0.5 + 0.5 * fx.dive)
                    }
                }
                Image {
                    source: fx.info ? "file://" + fx.sceneDir + "/logical/" + fx.info.meteor.file : ""
                    smooth: false
                    visible: fx.falling
                    width: Math.round(implicitWidth * fx.size)
                    height: Math.round(implicitHeight * fx.size)
                    x: fx.head.x - Math.round((fx.info ? fx.info.meteor.head[0] : 0) * fx.size)
                    y: fx.head.y - Math.round((fx.info ? fx.info.meteor.head[1] : 0) * fx.size)
                }
                // the shock ring, rising over the roofs
                Rectangle {
                    readonly property real r: 4 + 460 * Math.pow(fx.ring, 1.15)
                    visible: fx.ring >= 0
                    x: Math.round(fx.hit.x - r)
                    y: Math.round(fx.hit.y - r)
                    width: Math.round(2 * r)
                    height: width
                    radius: width / 2
                    color: "transparent"
                    border.width: fx.ring < 0.25 ? 2 : 1
                    border.color: fx.ring < 0.3 ? fx.hot : fx.mid
                    opacity: 0.9 * (1 - fx.ring) + 0.1
                }
            }
            ShaderEffectSource {
                id: artTex
                sourceItem: art
                hideSource: true
                smooth: false
                live: true
                textureSize: Qt.size(fx.cw, fx.ch)
            }
            Image {
                id: frontImg
                source: fx.fxDir ? "file://" + fx.fxDir + "/front.png" : ""
                smooth: false
                visible: false
            }
            ShaderEffect {
                x: win.ox
                y: win.oy
                width: fx.cw * win.k
                height: fx.ch * win.k
                property var art: artTex
                property var front: frontImg
                property size canvas: Qt.size(fx.cw, fx.ch)
                property point origin: fx.hit
                property real flash: fx.flash
                property color flashColor: fx.tonight ? fx.tonight[2] : "#ffd9a8"
                property real tint: fx.tonight ? 1 : 0
                property color deep: fx.tonight ? fx.tonight[0] : "black"
                property color mid: fx.tonight ? fx.tonight[1] : "black"
                property color hot: fx.tonight ? fx.tonight[2] : "black"
                fragmentShader: fx.fxDir ? "file://" + fx.fxDir + "/finale.frag.qsb" : ""
            }
        }
    }
}
