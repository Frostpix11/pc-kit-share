import QtQuick
import qs.services
import qs.modules.serp

// serp-skin: Serpantinum's hold-to-confirm power button — hold it and a liquid fills it from the
// bottom (550 ms × weight, InSine); full = done; let go and it drains (1500 ms × level)
Item {
    id: hb
    property string icon: "power"
    property string label: ""
    property real weight: 1
    property color tint: Serp.mauve
    signal confirmed
    property real level: 0
    readonly property bool done: level >= 1

    Rectangle {
        id: plate
        anchors.fill: parent
        radius: Serp.radiusSmall
        color: ma.containsMouse ? Serp.surface1 : Serp.surface0
        clip: true
        Behavior on color {
            ColorAnimation {
                duration: Serp.quick
            }
        }
        // the liquid, a wave on top
        Canvas {
            id: liquid
            anchors.fill: parent
            property real phase: 0
            visible: hb.level > 0
            onPaint: {
                const c = getContext("2d");
                c.reset();
                const h = height * (1 - hb.level), w = width, a = Math.min(4, height * 0.06);
                c.fillStyle = Qt.alpha(hb.tint, 0.85);
                c.beginPath();
                c.moveTo(0, height);
                for (let x = 0; x <= w; x += 4)
                    c.lineTo(x, h + Math.sin(x / w * Math.PI * 2 + phase) * a);
                c.lineTo(w, height);
                c.closePath();
                c.fill();
            }
            NumberAnimation on phase {
                running: liquid.visible
                from: 0
                to: Math.PI * 2
                duration: 1200
                loops: Animation.Infinite
            }
            onPhaseChanged: requestPaint()
        }
        Column {
            anchors.centerIn: parent
            spacing: Serp.px(4)
            SIcon {
                anchors.horizontalCenter: parent.horizontalCenter
                name: hb.icon
                size: Serp.px(18)
                color: hb.level > 0.5 ? Serp.onAccent : Serp.text
            }
            SText {
                visible: hb.label !== "" && hb.width > Serp.px(70)
                anchors.horizontalCenter: parent.horizontalCenter
                text: hb.label
                size: Serp.px(10)
                color: hb.level > 0.3 ? Serp.onAccent : Serp.subtext0
            }
        }
    }
    NumberAnimation {
        id: fill
        target: hb
        property: "level"
        to: 1
        easing.type: Easing.InSine
        onFinished: if (hb.level >= 1) {
            hb.confirmed();
            drain.start();
        }
    }
    NumberAnimation {
        id: drain
        target: hb
        property: "level"
        to: 0
        easing.type: Easing.OutCubic
    }
    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onPressed: {
            drain.stop();
            fill.duration = 550 * hb.weight * (1 - hb.level);
            fill.start();
        }
        onReleased: if (!hb.done) {
            fill.stop();
            drain.duration = 1500 * hb.level;
            drain.start();
        }
    }
}
