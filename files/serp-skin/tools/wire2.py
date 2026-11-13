#!/usr/bin/env python3
"""serp-skin: wire the second batch (net / sound / weather panels, OSD, desk strip, clipboard)."""
from pathlib import Path
Q = Path.home() / "serp-skin/qml"

def edit(rel, pairs):
    p = Q / rel
    t = p.read_text()
    for old, new in pairs:
        if new in t:
            continue
        assert t.count(old) == 1, (rel, old[:60], t.count(old))
        t = t.replace(old, new, 1)
    p.write_text(t)

edit("services/Serp.qml", [
    ('''    property string panelScreen: ""
''', '''    property string panelScreen: ""
    property string panelTab: ""       // the net panel's tab: wifi | bt
'''),
    ('''    function openPanel(kind, screenName) {
        Shell.closeTransient();''', '''    function openPanel(kind, screenName, tab) {
        Shell.closeTransient();
        panelTab = tab || "";'''),
    ('''    function togglePanel(kind, screenName) {
        if (panel === kind && panelScreen === (screenName || panelScreen))
            closePanel();
        else
            openPanel(kind, screenName);''', '''    function togglePanel(kind, screenName, tab) {
        if (panel === kind && panelScreen === (screenName || panelScreen) && (!tab || tab === panelTab))
            closePanel();
        else
            openPanel(kind, screenName, tab);'''),
])

edit("modules/serp/SerpPanels.qml", [
    ('''            "eq": {''', '''            "net": {
                "w": Math.min(win.width - edge * 4, Serp.px(720)),
                "h": Serp.px(560),
                "x": win.width - Math.min(win.width - edge * 4, Serp.px(720)) - edge * 2,
                "from": "top"
            },
            "sound": {
                "w": Serp.px(410),
                "h": Serp.px(580),
                "x": win.width - Serp.px(410) - edge * 2,
                "from": "top"
            },
            "weather": {
                "w": Serp.px(480),
                "h": Serp.px(470),
                "x": edge * 2,
                "from": "top"
            },
            "eq": {'''),
    ('''        Loader {
            anchors.fill: parent
            active: win.shown === "eq" && box.visible''', '''        Loader {
            anchors.fill: parent
            active: win.shown === "net" && box.visible
            sourceComponent: SerpNetPanel {
                screenName: win.screenName
                progress: win.progress
                tab: Serp.panelTab || "wifi"
            }
        }
        Loader {
            anchors.fill: parent
            active: win.shown === "sound" && box.visible
            sourceComponent: SerpSoundPanel {
                screenName: win.screenName
                progress: win.progress
            }
        }
        Loader {
            anchors.fill: parent
            active: win.shown === "weather" && box.visible
            sourceComponent: SerpWeatherPanel {
                screenName: win.screenName
                progress: win.progress
            }
        }
        Loader {
            anchors.fill: parent
            active: win.shown === "eq" && box.visible'''),
])

edit("modules/serp/SerpDesktop.qml", [
    ('''        SerpBar {
            modelData: scope.modelData
        }
''', '''        SerpBar {
            modelData: scope.modelData
        }
        SerpOsd {
            modelData: scope.modelData
        }
        SerpDeskStrip {
            modelData: scope.modelData
        }
'''),
])

edit("modules/serp/SerpWindows.qml", [
    ('''    LazyLoader {
        active: Serp.on && Serp.settingsOpen
        SerpSettings {}
    }
''', '''    LazyLoader {
        active: Serp.on && Serp.settingsOpen
        SerpSettings {}
    }
    // the clipboard history (Mod+V…) in the skin's look; angelOS's own steps aside (LazyWindows)
    Linger {
        id: clipKeep
        when: Serp.on && Shell.clipboardOpen
    }
    LazyLoader {
        active: clipKeep.alive
        SerpClipboard {}
    }
'''),
])

# the bar: weather in the left island; Wi-Fi / Bluetooth → the net panel, sound → the sound panel
edit("modules/serp/SerpBar.qml", [
    ('''            // now playing: the cover, the title, play/pause; the media panel on click''', '''            // the weather (the centre is the Halo's): its panel on click
            SButton {
                id: wxBtn
                visible: Serp.cfg.barWeather && Weather.ok
                anchors.verticalCenter: parent.verticalCenter
                active: Serp.isOpen("weather", win.screenName)
                Row {
                    spacing: Serp.px(5)
                    SIcon {
                        anchors.verticalCenter: parent.verticalCenter
                        name: SerpIcons.weather(Weather.now)
                        size: Serp.px(15)
                        color: Serp.accent
                    }
                    SText {
                        anchors.verticalCenter: parent.verticalCenter
                        text: Weather.now ? Weather.deg(Weather.now.temp) : ""
                        size: Serp.px(11.5)
                        bold: true
                    }
                }
                onClicked: Serp.togglePanel("weather", win.screenName)
            }

            // now playing: the cover, the title, play/pause; the media panel on click'''),
    ('''                active: Serp.isOpen("quick", win.screenName)
                SIcon {
                    name: SerpIcons.net()
                }
                onClicked: Serp.togglePanel("quick", win.screenName)''', '''                active: Serp.isOpen("net", win.screenName) && Serp.panelTab !== "bt"
                SIcon {
                    name: SerpIcons.net()
                }
                onClicked: Serp.togglePanel("net", win.screenName, "wifi")'''),
    ('''                active: Serp.isOpen("quick", win.screenName)
                SIcon {
                    name: "bluetooth"
                    color: Bt.enabled ? Serp.text : Qt.alpha(Serp.text, 0.4)
                }
                onClicked: Serp.togglePanel("quick", win.screenName)''', '''                active: Serp.isOpen("net", win.screenName) && Serp.panelTab === "bt"
                SIcon {
                    name: "bluetooth"
                    color: Bt.enabled ? Serp.text : Qt.alpha(Serp.text, 0.4)
                }
                onClicked: Serp.togglePanel("net", win.screenName, "bt")'''),
    ('''                visible: Audio.ready
                active: Serp.isOpen("quick", win.screenName)''', '''                visible: Audio.ready
                active: Serp.isOpen("sound", win.screenName)'''),
    ('''                    else
                        Serp.togglePanel("quick", win.screenName);
                }
                onWheel: w => Audio.step(w.angleDelta.y > 0 ? 0.05 : -0.05)''', '''                    else
                        Serp.togglePanel("sound", win.screenName);
                }
                onWheel: w => Audio.step(w.angleDelta.y > 0 ? 0.05 : -0.05)'''),
])
print("wired")
