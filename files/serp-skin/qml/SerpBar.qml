pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Services.SystemTray
import qs.config
import qs.services
import qs.widgets

// serp-skin (Celestia, local): the Golden Gate skin's bar in the Serpantinum look — three floating
// islands over the wallpaper; the centre one is angelOS's Halo when it is on. Leading: the angel (Start) and the desks as pills, the active one
// stretched in the accent. Centre: the time, hours big, minutes over seconds, and the weather
// (Notification Center on click). Trailing: tray, input, Wi-Fi, Bluetooth, sound, battery and
// Control Center — the same popovers as the menu bar (MacMenus). Flat, mono, accent from the
// wallpaper (GoldenGate serp tokens). In hell: hell's colours, horns on the angel.
PanelWindow {
    id: win

    required property var modelData
    readonly property string screenName: modelData.name
    readonly property bool menuHere: MacMenus.isOpen && MacMenus.screen === screenName

    // measures
    readonly property int gap: GoldenGate.px(6)            // from the screen's edge
    readonly property real h: GoldenGate.barHeight          // 36 in serp: the popovers hang below it
    readonly property int pillH: h - gap
    readonly property int radius: GoldenGate.px(12)
    readonly property string haloZoneMode: Config.halo.windows === "maximized" && !WindowConfig.floatAll ? "bar" : Config.halo.windows || "bar"
    readonly property int haloZone: Halo.on(screenName) && Config.halo.reserve && haloZoneMode === "bar" ? Halo.strip : 0
    readonly property var plugins: BarLayout.all.filter(id => id.startsWith("plugin:")).reverse()

    // colours
    readonly property color base: GoldenGate.serpBase
    readonly property color ink: GoldenGate.label
    readonly property color dim: GoldenGate.secondaryLabel
    readonly property color accent: GoldenGate.accent
    readonly property color pillOff: Qt.alpha(ink, 0.16)
    readonly property color pillUsed: Qt.alpha(ink, 0.38)

    screen: modelData
    anchors {
        top: true
        left: true
        right: true
    }
    implicitHeight: h
    exclusiveZone: Shell.dev ? 0 : Math.max(h, haloZone)
    exclusionMode: Shell.dev ? ExclusionMode.Ignore : ExclusionMode.Normal
    color: "transparent"
    WlrLayershell.namespace: "angelos-macbar"
    WlrLayershell.layer: WlrLayer.Top
    ZoneReport {
        win: win
        key: "macbar"
    }
    // only the islands take clicks; the strip between them lets them through
    mask: Region {
        Region {
            item: leftIsland
        }
        Region {
            item: centerIsland.visible ? centerIsland : null
        }
        Region {
            item: rightIsland
        }
    }
    BackgroundEffect.blurRegion: GoldenGate.blurOn ? blurRegion : null
    Region {
        id: blurRegion
        Region {
            item: leftIsland
            radius: win.radius
        }
        Region {
            item: centerIsland.visible ? centerIsland : null
            radius: win.radius
        }
        Region {
            item: rightIsland
            radius: win.radius
        }
    }

    component Island: Rectangle {
        y: win.gap
        height: win.pillH
        radius: win.radius
        color: win.base
        border.width: 1
        border.color: Qt.alpha(win.ink, 0.06)
        Behavior on width {
            NumberAnimation {
                duration: 250
                easing.type: Easing.OutCubic
            }
        }
    }

    // a round-cornered press target inside an island
    component Btn: Item {
        id: btn
        property string kind: ""
        property bool active: win.menuHere && MacMenus.statusKind === kind && kind !== ""
        default property alias content: box.data
        signal clicked(var mouse)
        width: Math.max(GoldenGate.px(26), box.childrenRect.width + GoldenGate.px(12))
        height: win.pillH
        Rectangle {
            anchors.fill: parent
            anchors.margins: GoldenGate.px(4)
            radius: GoldenGate.px(8)
            color: btn.active ? Qt.alpha(win.accent, 0.22) : ma.containsMouse ? Qt.alpha(win.ink, 0.08) : "transparent"
            Behavior on color {
                ColorAnimation {
                    duration: 150
                }
            }
        }
        Item {
            id: box
            anchors.centerIn: parent
            width: childrenRect.width
            height: childrenRect.height
        }
        MouseArea {
            id: ma
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
            onClicked: m => btn.clicked(m)
        }
    }
    function rightOf(item) {
        return item.mapToItem(null, item.width, 0).x;
    }

    // ---- leading: the angel and the desks ----
    Island {
        id: leftIsland
        x: win.gap * 2
        width: leftRow.implicitWidth + GoldenGate.px(8)

        Row {
            id: leftRow
            x: GoldenGate.px(4)
            height: win.pillH
            spacing: GoldenGate.px(4)

            Btn {
                MacIcon {
                    name: Angel.demon || Story.marked ? "angel-horns" : "angel"
                    size: GoldenGate.px(17)
                    color: win.accent
                }
                onClicked: Shell.toggleStart(win.screenName)
            }

            Item {
                id: desks
                readonly property var list: Niri.workspacesOn(win.screenName)
                readonly property int dot: GoldenGate.px(9)
                readonly property int wide: GoldenGate.px(26)
                readonly property int sp: GoldenGate.px(7)
                width: list.length ? list.reduce((a, w) => a + (w.is_active ? wide : dot), 0) + sp * (list.length - 1) + GoldenGate.px(8) : 0
                height: win.pillH

                Row {
                    anchors.centerIn: parent
                    spacing: desks.sp
                    Repeater {
                        model: desks.list
                        Rectangle {
                            id: pill
                            required property var modelData
                            readonly property bool used: Niri.windowsOn(modelData.id).length > 0
                            readonly property bool urgent: modelData.is_urgent === true
                            anchors.verticalCenter: parent.verticalCenter
                            width: modelData.is_active ? desks.wide : desks.dot
                            height: desks.dot
                            radius: height / 2
                            color: modelData.is_active ? win.accent : urgent ? GoldenGate.serpRed : used ? win.pillUsed : win.pillOff
                            scale: deskMa.containsMouse && !modelData.is_active ? 1.25 : 1
                            Behavior on width {
                                NumberAnimation {
                                    duration: 380
                                    easing.type: Easing.OutQuint
                                }
                            }
                            Behavior on color {
                                ColorAnimation {
                                    duration: 250
                                }
                            }
                            Behavior on scale {
                                NumberAnimation {
                                    duration: 250
                                    easing.type: Easing.OutQuint
                                }
                            }
                            MouseArea {
                                id: deskMa
                                anchors.fill: parent
                                anchors.margins: -GoldenGate.px(4)
                                hoverEnabled: true
                                onClicked: Niri.focusWorkspace(pill.modelData.id)
                            }
                        }
                    }
                }
                // the wheel goes through the desks, as on the classic bar
                WheelHandler {
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                    onWheel: e => {
                        const l = desks.list, i = l.findIndex(w => w.is_active);
                        const n = i + (e.angleDelta.y < 0 ? 1 : -1);
                        if (n >= 0 && n < l.length)
                            Niri.focusWorkspace(l[n].id);
                    }
                }
            }
        }
    }

    // ---- centre: the time and the weather ----
    Island {
        id: centerIsland
        // angelOS's Halo holds the top centre (time, weather, the cat): the clock island only without it
        visible: !Halo.on(win.screenName)
        x: Math.round((win.width - width) / 2)
        width: centerRow.implicitWidth + GoldenGate.px(24)
        readonly property bool ncOpen: GoldenGate.panel === "nc" && GoldenGate.panelScreen === win.screenName
        color: ncOpen ? Qt.alpha(win.accent, 0.18) : win.base

        property date now: new Date()
        Timer {
            interval: 1000
            running: !Shell.hiddenScreen(win.screenName)
            repeat: true
            triggeredOnStart: true
            onTriggered: centerIsland.now = new Date()
        }

        Row {
            id: centerRow
            anchors.centerIn: parent
            spacing: GoldenGate.px(10)

            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: GoldenGate.px(3)
                MacText {
                    anchors.verticalCenter: parent.verticalCenter
                    text: Qt.formatTime(centerIsland.now, "HH")
                    size: GoldenGate.px(17)
                    bold: true
                    color: win.accent
                }
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: -GoldenGate.px(3)
                    MacText {
                        text: Qt.formatTime(centerIsland.now, "mm")
                        size: GoldenGate.px(10)
                        bold: true
                        color: win.ink
                    }
                    MacText {
                        text: Qt.formatTime(centerIsland.now, "ss")
                        size: GoldenGate.px(10)
                        color: win.dim
                    }
                }
            }
            Rectangle {
                visible: wx.visible
                anchors.verticalCenter: parent.verticalCenter
                width: 1
                height: GoldenGate.px(14)
                color: Qt.alpha(win.ink, 0.15)
            }
            Row {
                id: wx
                visible: Weather.ok
                anchors.verticalCenter: parent.verticalCenter
                spacing: GoldenGate.px(6)
                MacIcon {
                    anchors.verticalCenter: parent.verticalCenter
                    readonly property string k: Weather.now ? Weather.kind(Weather.now.code) : "cloudy"
                    name: k === "clear" ? (Weather.now && Weather.now.day === false ? "moon" : "sun") : k === "partly" ? "sun-dim" : k === "rain" || k === "storm" ? "zap" : k === "fog" ? "wind" : "cloud"
                    size: GoldenGate.px(15)
                    color: win.ink
                    stroke: 2
                }
                MacText {
                    anchors.verticalCenter: parent.verticalCenter
                    text: Weather.now ? Weather.deg(Weather.now.temp) : ""
                    size: GoldenGate.px(12)
                    color: win.ink
                }
            }
        }
        MouseArea {
            anchors.fill: parent
            onClicked: GoldenGate.togglePanel("nc", win.screenName)
        }
    }

    // ---- trailing: status ----
    Island {
        id: rightIsland
        x: win.width - width - win.gap * 2
        width: status.implicitWidth + GoldenGate.px(8)

        Row {
            id: status
            x: GoldenGate.px(4)
            height: win.pillH
            spacing: 0

            // the plugins' panel widgets (their Mac versions)
            Repeater {
                model: win.plugins.slice().reverse()
                Item {
                    id: plugExtra
                    required property string modelData
                    readonly property var p: Plugins.byId(modelData.slice(7))
                    readonly property string settingsSkin: "goldengate"
                    visible: !!plug.item
                    width: plug.item ? Math.max(GoldenGate.px(22), Math.round(plug.item.implicitWidth) + GoldenGate.px(10)) : 0
                    height: win.pillH
                    Loader {
                        id: plug
                        anchors.centerIn: parent
                        readonly property string src: plugExtra.p ? Plugins.url(plugExtra.p, plugExtra.p.barWidget) : ""
                        function load() {
                            if (plugExtra.p && !item)
                                setSource(src, {
                                    "plugin": Plugins.context(plugExtra.p),
                                    "screenName": win.screenName,
                                    "barWindow": win
                                });
                        }
                        onSrcChanged: if (item) {
                            source = "";
                            load();
                        }
                        Component.onCompleted: load()
                    }
                }
            }
            Repeater {
                model: SystemTray.items
                Btn {
                    id: extra
                    required property var modelData
                    active: win.menuHere && MacMenus.statusKind === "tray" && MacMenus.trayItem === modelData
                    Image {
                        width: GoldenGate.px(16)
                        height: width
                        sourceSize: Qt.size(width * 2, height * 2)
                        source: StdIcon.safe(extra.modelData.icon, "application-x-executable")
                        smooth: true
                        mipmap: true
                    }
                    onClicked: m => {
                        if (m.button === Qt.MiddleButton)
                            extra.modelData.secondaryActivate();
                        else if ((m.button === Qt.RightButton || extra.modelData.onlyMenu) && extra.modelData.hasMenu)
                            MacMenus.toggleStatus(win.screenName, "tray", win.rightOf(extra), extra.modelData);
                        else
                            extra.modelData.activate();
                    }
                }
            }
            Rectangle {
                visible: SystemTray.items.values.length > 0
                anchors.verticalCenter: parent.verticalCenter
                width: 1
                height: GoldenGate.px(14)
                color: Qt.alpha(win.ink, 0.15)
            }
            Btn {
                id: input
                kind: "input"
                visible: Niri.keyboardLayouts.length > 1
                MacText {
                    text: Niri.layoutShort.toUpperCase()
                    size: GoldenGate.px(11)
                    bold: true
                    color: win.ink
                }
                onClicked: MacMenus.toggleStatus(win.screenName, "input", win.rightOf(input))
            }
            Btn {
                id: wifi
                kind: "wifi"
                visible: Wifi.hasWifi
                MacIcon {
                    name: !Wifi.enabled ? "wifi-off" : !Wifi.connected ? "wifi-zero" : Wifi.strength < 0.4 ? "wifi-low" : "wifi"
                    color: win.ink
                    stroke: 2
                }
                onClicked: MacMenus.toggleStatus(win.screenName, "wifi", win.rightOf(wifi))
            }
            Btn {
                id: bt
                kind: "bluetooth"
                visible: Bt.available
                MacIcon {
                    name: "bluetooth"
                    color: Bt.enabled ? win.ink : Qt.alpha(win.ink, 0.4)
                    stroke: 2
                }
                onClicked: MacMenus.toggleStatus(win.screenName, "bluetooth", win.rightOf(bt))
            }
            Btn {
                id: sound
                kind: "sound"
                visible: Audio.ready
                Row {
                    spacing: GoldenGate.px(5)
                    MacIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        name: Audio.muted || Audio.volume === 0 ? "volume-x" : Audio.volume < 0.34 ? "volume" : Audio.volume < 0.67 ? "volume-1" : "volume-2"
                        color: win.ink
                        stroke: 2
                    }
                    MacText {
                        anchors.verticalCenter: parent.verticalCenter
                        text: Math.round(Audio.volume * 100) + "%"
                        size: GoldenGate.px(11)
                        color: win.ink
                    }
                }
                onClicked: MacMenus.toggleStatus(win.screenName, "sound", win.rightOf(sound))
            }
            Btn {
                id: battery
                kind: "battery"
                visible: Power.hasBattery && Config.power.showBattery
                MacText {
                    text: Power.percent + "%"
                    size: GoldenGate.px(11)
                    bold: true
                    color: Power.discharging && Power.percent <= Config.power.lowAt ? GoldenGate.serpRed : win.ink
                }
                onClicked: MacMenus.toggleStatus(win.screenName, "battery", win.rightOf(battery))
            }
            Btn {
                active: GoldenGate.panel === "cc" && GoldenGate.panelScreen === win.screenName
                MacIcon {
                    name: "control-center"
                    color: win.ink
                    stroke: 1.8
                }
                onClicked: GoldenGate.togglePanel("cc", win.screenName)
            }
        }
    }

    RightClickGuard {}
}
