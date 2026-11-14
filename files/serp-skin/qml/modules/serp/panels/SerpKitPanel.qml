pragma ComponentBehavior: Bound

import QtQuick
import qs.config
import qs.services
import qs.modules.serp

// serp-skin: pc-kit — everything we put over angelOS, one panel (services/SerpKit: `kit inventory`,
// `kit doctor --json`, `kit diff ID`). The state orb and the proof up top (every changed author
// file undone back to the author's own, ~/AngelOS-Dotfiles), the groups as a sliding switch
// (shell, niri, satellite, plugins, system, outside the patches), the list on the left, the piece
// on the right: what it does, its files, its own changes line by line, its git history, and the
// hold-to-confirm switch (kit apply / kit revert, detached: the shell may restart).
Item {
    id: root
    property string screenName: ""
    property real progress: 1

    implicitWidth: Serp.px(860)
    implicitHeight: Serp.px(660)

    readonly property bool still: Motion.still
    function st(d) {
        return Math.max(0, Math.min(1, (progress - d) / Math.max(0.01, 1 - d)));
    }
    function ease(t) {
        return 1 - Math.pow(1 - t, 3);
    }
    readonly property int pad: Serp.px(16)

    Component.onCompleted: {
        SerpKit.touch();
        SerpKit.loadInventory(false);
        takeShow();
    }
    // `ipc call serpkit open TAB NAME VIEW`: open on that piece
    function takeShow() {
        const r = SerpKit.showReq;
        if (!r || Date.now() - r.n > 5000)
            return;
        tab = r.tab;
        pendingName = r.name || "";
        pendingView = r.view || "about";
        takePending();
    }
    // the inventory may still be on its way when asked: kept until the piece is there
    property string pendingName: ""
    property string pendingView: ""
    function takePending() {
        if (!pendingView)
            return;
        if (pendingName) {
            const it = items.find(x => x.name === pendingName || x.num === pendingName || x.id === pendingName);
            if (!it)
                return;
            pick(it);
        } else if (!items.length)
            return;
        view = pendingView;
        pendingName = "";
        pendingView = "";
    }
    onItemsChanged: {
        takePending();
        Qt.callLater(syncList);
    }
    // the list's highlight follows the piece shown (ListView resets its index when the model
    // changes, so it is set by hand, not bound)
    function syncList() {
        const i = items.indexOf(cur);
        if (list.currentIndex !== i)
            list.currentIndex = i;
        if (i >= 0)
            list.positionViewAtIndex(i, ListView.Contain);
    }
    Connections {
        target: SerpKit
        function onShowReqChanged() {
            root.takeShow();
        }
    }

    // ---- states: one word each for the colour and the words ----
    function norm(it) {
        if (!it)
            return "info";
        if (it.disabled && it.state !== "on")
            return "taken";
        return ({
                "on": "ok",
                "ok": "ok",
                "off": "warn",
                "warn": "warn",
                "unfit": "bad",
                "bad": "bad",
                "info": "info"
            })[it.state] || "info";
    }
    function tone(s) {
        return s === "bad" ? Serp.red : s === "warn" ? SerpKit.warnColor : s === "ok" ? Serp.green : Serp.subtext0;
    }
    function stateWord(it) {
        const s = it ? it.state : "";
        if (!it)
            return "";
        if (tab === "system")
            return ({
                    "ok": "в порядке",
                    "warn": "замечание",
                    "bad": "надо поправить",
                    "info": "сведения"
                })[s] || s;
        if (tab === "audit")
            return it.whoLabel || "";
        if (it.disabled && s !== "on")
            return "снят тобой";
        return ({
                "on": tab === "plugins" ? "установлен" : tab === "niri" || tab === "satellite" ? "в сборке" : "работает",
                "off": tab === "plugins" ? "не установлен" : "слетел",
                "warn": "отличается",
                "unfit": "не подходит к коду автора"
            })[s] || s;
    }

    // ---- what is shown ----
    property string tab: "shell"
    property var sel: ({})              // the picked id per tab
    property string view: "about"       // about | diff | history
    property int gen: 0                 // bumps on a tab change: the list comes in again
    onTabChanged: {
        gen++;
        view = "about";
    }

    readonly property var tabs: [
        {
            "id": "shell",
            "icon": "layers",
            "label": "Оболочка"
        },
        {
            "id": "niri",
            "icon": "monitor",
            "label": "niri"
        },
        {
            "id": "satellite",
            "icon": "app-window",
            "label": "satellite"
        },
        {
            "id": "plugins",
            "icon": "puzzle",
            "label": "Плагины"
        },
        {
            "id": "system",
            "icon": "activity",
            "label": "Система"
        },
        {
            "id": "audit",
            "icon": "scan",
            "label": "Вне патчей"
        }
    ]
    function itemsOf(id) {
        if (id === "system")
            return SerpKit.system.map((s, i) => ({
                        "id": "sys:" + i,
                        "name": s.label,
                        "desc": "",
                        "state": s.state,
                        "note": s.note
                    }));
        if (id === "audit") {
            const a = SerpKit.inv ? SerpKit.inv.audit : null;
            return a ? (a.handEdits || []).map(h => Object.assign({
                        "desc": h.note || "",
                        "state": h.who ? "info" : "warn",
                        "note": h.path,
                        "files": []
                    }, h)) : [];
        }
        const g = SerpKit.group(id);
        return g ? g.items : [];
    }
    function problemsOf(id) {
        return itemsOf(id).filter(it => {
            const s = norm(it);
            return id === "audit" ? s === "warn" : s === "bad" || s === "warn";
        }).length;
    }
    readonly property var items: {
        SerpKit.inv;
        SerpKit.system;
        return itemsOf(tab);
    }
    readonly property var cur: {
        const want = sel[tab];
        return items.find(it => it.id === want) || items[0] || null;
    }
    function pick(it) {
        const m = Object.assign({}, sel);
        m[tab] = it.id;
        sel = m;
    }
    readonly property bool hasChanges: !!cur && (tab === "shell" || tab === "niri" || tab === "satellite" || tab === "audit")
    readonly property bool hasHistory: !!cur && !!cur.history && cur.history.length > 0
    onCurChanged: {
        if (view === "diff" && !hasChanges || view === "history" && !hasHistory)
            view = "about";
        if (view === "diff" && cur)
            SerpKit.loadDiff(cur.id);
        detailIn.restart();
        Qt.callLater(syncList);
    }
    onViewChanged: if (view === "diff" && cur)
        SerpKit.loadDiff(cur.id)

    // the counts up top
    function tileData(i) {
        const hand = SerpKit.inv ? (SerpKit.inv.audit.handEdits || []) : [];
        return [
            {
                "icon": "shield",
                "value": proof ? proof.proven : 0,
                "of": proof ? proof.files : 0,
                "label": "файлов доказано",
                "go": "shell",
                "bad": proof ? proof.files - proof.proven : 0
            },
            {
                "icon": "layers",
                "value": piecesOk,
                "of": piecesAll,
                "label": "частей работают",
                "go": "shell",
                "bad": piecesAll - piecesOk
            },
            {
                "icon": "activity",
                "value": SerpKit.systemOk,
                "of": SerpKit.system.length,
                "label": "проверок ок",
                "go": "system",
                "bad": SerpKit.system.length - SerpKit.systemOk
            },
            {
                "icon": "scan",
                "value": hand.length,
                "of": -1,
                "label": "конфигов вне патчей",
                "go": "audit",
                "bad": hand.filter(h => !h.who).length
            }
        ][i];
    }
    readonly property var proof: SerpKit.inv ? SerpKit.inv.proof : null
    readonly property int piecesAll: ["shell", "niri", "satellite", "plugins"].reduce((n, g) => n + itemsOf(g).length, 0)
    readonly property int piecesOk: ["shell", "niri", "satellite", "plugins"].reduce((n, g) => n + itemsOf(g).filter(it => norm(it) === "ok").length, 0)

    // ---- the card ----
    Rectangle {
        anchors.fill: parent
        radius: Math.min(Serp.radius * 1.4, 24)
        color: Serp.ground
        border.width: 1
        border.color: Qt.tint(Serp.base, Qt.alpha(Serp.text, 0.12))
    }
    // a press on the panel's own empty places stays here (under it: «a click outside closes»)
    MouseArea {
        anchors.fill: parent
        z: -1
    }

    // ---- header: the orb, what it is, check again ----
    Item {
        id: head
        x: root.pad
        y: root.pad
        width: parent.width - root.pad * 2
        height: Serp.px(46)
        opacity: root.ease(root.st(0))
        transform: Translate {
            y: (1 - root.ease(root.st(0))) * -Serp.px(10)
        }

        // the orb: breathes when all is good, sends rings out when not, an arc runs round while asking
        Item {
            id: orb
            width: Serp.px(44)
            height: width
            anchors.verticalCenter: parent.verticalCenter
            readonly property string s: SerpKit.state === "unknown" ? "info" : SerpKit.state
            readonly property color c: root.tone(s)
            Repeater {
                model: 2
                Rectangle {
                    id: wave
                    required property int index
                    anchors.centerIn: parent
                    width: orb.width
                    height: width
                    radius: width / 2
                    color: "transparent"
                    border.width: Serp.px(2)
                    border.color: orb.c
                    opacity: 0
                    visible: orb.s === "bad" || orb.s === "warn"
                    SequentialAnimation {
                        running: wave.visible && !root.still && root.visible
                        loops: Animation.Infinite
                        PauseAnimation {
                            duration: wave.index * 900
                        }
                        ParallelAnimation {
                            NumberAnimation {
                                target: wave
                                property: "scale"
                                from: 1
                                to: 1.55
                                duration: 1800
                                easing.type: Easing.OutCubic
                            }
                            NumberAnimation {
                                target: wave
                                property: "opacity"
                                from: 0.55
                                to: 0
                                duration: 1800
                                easing.type: Easing.OutCubic
                            }
                        }
                        PauseAnimation {
                            duration: (1 - wave.index) * 900
                        }
                    }
                }
            }
            Rectangle {
                id: orbBody
                anchors.fill: parent
                radius: width / 2
                color: Qt.alpha(orb.c, 0.18)
                border.width: 1
                border.color: Qt.alpha(orb.c, 0.45)
                Behavior on color {
                    ColorAnimation {
                        duration: Serp.slow
                    }
                }
                SequentialAnimation on scale {
                    running: orb.s === "ok" && !root.still && root.visible
                    loops: Animation.Infinite
                    NumberAnimation {
                        to: 1.06
                        duration: 1400
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        to: 1
                        duration: 1400
                        easing.type: Easing.InOutSine
                    }
                }
                SIcon {
                    anchors.centerIn: parent
                    name: orb.s === "bad" ? "circle-x" : orb.s === "ok" ? "check" : "shield"
                    size: Serp.px(21)
                    color: orb.c
                }
            }
            Canvas {
                id: arc
                anchors.fill: parent
                anchors.margins: -Serp.px(4)
                visible: SerpKit.busy || SerpKit.invBusy
                onPaint: {
                    const c = getContext("2d");
                    c.reset();
                    c.strokeStyle = Serp.accent;
                    c.lineWidth = Serp.px(2.5);
                    c.lineCap = "round";
                    c.beginPath();
                    c.arc(width / 2, height / 2, width / 2 - c.lineWidth, 0, Math.PI * 0.6);
                    c.stroke();
                }
                RotationAnimation on rotation {
                    running: arc.visible
                    from: 0
                    to: 360
                    duration: 900
                    loops: Animation.Infinite
                }
            }
        }
        Column {
            anchors.left: orb.right
            anchors.leftMargin: Serp.px(12)
            anchors.right: again.left
            anchors.rightMargin: Serp.px(10)
            anchors.verticalCenter: parent.verticalCenter
            spacing: Serp.px(2)
            SText {
                width: parent.width
                text: "pc-kit"
                size: Serp.px(17)
                black: true
            }
            SText {
                width: parent.width
                size: Serp.px(10.5)
                dim: true
                text: {
                    if (SerpKit.error)
                        return SerpKit.error;
                    const s = SerpKit.state === "bad" ? "надо поправить: " + SerpKit.bad : SerpKit.state === "warn" ? "есть замечания: " + SerpKit.warn : SerpKit.state === "ok" ? "всё работает" : "проверяю…";
                    const a = SerpKit.inv ? " · angelOS " + SerpKit.inv.author.rev : "";
                    return s + a + " · проверено " + SerpKit.ago();
                }
            }
        }
        SButton {
            id: again
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            flat: false
            padH: Serp.px(10)
            Row {
                spacing: Serp.px(6)
                SIcon {
                    id: againIcon
                    anchors.verticalCenter: parent.verticalCenter
                    name: "refresh-cw"
                    size: Serp.px(13)
                    RotationAnimation on rotation {
                        running: SerpKit.busy || SerpKit.invBusy
                        from: 0
                        to: 360
                        duration: 900
                        loops: Animation.Infinite
                        onStopped: againIcon.rotation = 0
                    }
                }
                SText {
                    anchors.verticalCenter: parent.verticalCenter
                    text: SerpKit.busy || SerpKit.invBusy ? "Проверяю…" : "Проверить всё"
                    size: Serp.px(11.5)
                }
            }
            onClicked: {
                SerpKit.refresh();
                SerpKit.diffs = ({});
                SerpKit.loadInventory(true);
            }
        }
    }

    // ---- the tiles: the proof and the counts (they count up as the panel opens) ----
    Row {
        id: tiles
        x: root.pad
        y: head.y + head.height + Serp.px(12)
        width: parent.width - root.pad * 2
        height: Serp.px(62)
        spacing: Serp.px(10)
        Repeater {
            // a number model (not an array of objects): the tiles stay when the data comes in, so
            // their numbers count on from where they stand instead of starting from 0 again
            model: 4
            Rectangle {
                id: tile
                required property int index
                readonly property var modelData: root.tileData(index)
                width: (tiles.width - tiles.spacing * 3) / 4
                height: tiles.height
                radius: Serp.radiusSmall
                color: tileMa.containsMouse ? Serp.surface1 : Qt.alpha(Serp.surface0, 0.75)
                border.width: 1
                border.color: root.tab === modelData.go && tileMa.containsMouse ? Qt.alpha(Serp.accent, 0.5) : Serp.line
                Behavior on color {
                    ColorAnimation {
                        duration: Serp.quick
                    }
                }
                readonly property real inT: root.ease(root.st(0.08 + index * 0.06))
                opacity: inT
                transform: Translate {
                    y: (1 - tile.inT) * Serp.px(14)
                }
                // the number counts up to its value
                property real shownValue: 0
                readonly property int target: modelData.value
                onTargetChanged: count.restart()
                Component.onCompleted: count.restart()
                NumberAnimation {
                    id: count
                    target: tile
                    property: "shownValue"
                    to: tile.target
                    duration: root.still ? 0 : 900
                    easing.type: Easing.OutCubic
                }
                Row {
                    x: Serp.px(12)
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Serp.px(10)
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: Serp.px(30)
                        height: width
                        radius: width / 2
                        color: Qt.alpha(tile.modelData.bad > 0 && tile.modelData.of >= 0 ? root.tone("warn") : Serp.accent, 0.16)
                        SIcon {
                            anchors.centerIn: parent
                            name: tile.modelData.icon
                            size: Serp.px(15)
                            color: tile.modelData.bad > 0 && tile.modelData.of >= 0 ? root.tone("warn") : Serp.accent
                        }
                    }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: Serp.px(1)
                        Row {
                            spacing: Serp.px(3)
                            SText {
                                text: Math.round(tile.shownValue)
                                size: Serp.px(19)
                                black: true
                            }
                            SText {
                                visible: tile.modelData.of >= 0
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: Serp.px(3)
                                text: "/" + tile.modelData.of
                                size: Serp.px(12)
                                dim: true
                            }
                        }
                        SText {
                            width: tile.width - Serp.px(60)
                            text: tile.modelData.label
                            size: Serp.px(9.5)
                            dim: true
                            elide: Text.ElideRight
                        }
                    }
                }
                MouseArea {
                    id: tileMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.tab = tile.modelData.go
                }
            }
        }
    }

    // ---- the groups: a sliding switch ----
    Rectangle {
        id: seg
        x: root.pad
        y: tiles.y + tiles.height + Serp.px(12)
        width: parent.width - root.pad * 2
        height: Serp.px(34)
        radius: height / 2
        color: Serp.surface0
        border.width: 1
        border.color: Qt.tint(Serp.base, Qt.alpha(Serp.text, 0.12))
        opacity: root.ease(root.st(0.2))
        readonly property real cell: (width - Serp.px(6)) / root.tabs.length
        readonly property int at: Math.max(0, root.tabs.findIndex(t => t.id === root.tab))
        Rectangle {
            id: segPill
            x: Serp.px(3) + seg.at * seg.cell
            y: Serp.px(3)
            width: seg.cell
            height: seg.height - Serp.px(6)
            radius: height / 2
            color: Serp.accent
            Behavior on x {
                NumberAnimation {
                    duration: root.still ? 0 : Serp.slow
                    easing.type: Easing.OutQuint
                }
            }
        }
        Row {
            anchors.fill: parent
            anchors.margins: Serp.px(3)
            Repeater {
                model: root.tabs
                Item {
                    id: tabItem
                    required property var modelData
                    required property int index
                    readonly property bool on: Math.abs(segPill.x - Serp.px(3) - index * seg.cell) < seg.cell / 2
                    readonly property int probs: {
                        SerpKit.inv;
                        SerpKit.system;
                        return root.problemsOf(modelData.id);
                    }
                    width: seg.cell
                    height: parent.height
                    Row {
                        anchors.centerIn: parent
                        spacing: Serp.px(5)
                        SIcon {
                            anchors.verticalCenter: parent.verticalCenter
                            name: tabItem.modelData.icon
                            size: Serp.px(13)
                            color: tabItem.on ? Serp.onAccent : tabMa.containsMouse ? Serp.text : Serp.subtext0
                        }
                        SText {
                            anchors.verticalCenter: parent.verticalCenter
                            text: tabItem.modelData.label
                            size: Serp.px(11)
                            bold: true
                            color: tabItem.on ? Serp.onAccent : tabMa.containsMouse ? Serp.text : Serp.subtext0
                        }
                        SText {
                            anchors.verticalCenter: parent.verticalCenter
                            text: root.itemsOf(tabItem.modelData.id).length
                            size: Serp.px(9.5)
                            color: tabItem.on ? Qt.alpha(Serp.onAccent, 0.7) : Serp.subtext0
                        }
                    }
                    Rectangle {
                        visible: tabItem.probs > 0
                        anchors.right: parent.right
                        anchors.rightMargin: Serp.px(8)
                        anchors.top: parent.top
                        anchors.topMargin: Serp.px(4)
                        width: Serp.px(6)
                        height: width
                        radius: width / 2
                        color: tabItem.modelData.id === "audit" ? SerpKit.warnColor : Serp.red
                    }
                    MouseArea {
                        id: tabMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.tab = tabItem.modelData.id
                    }
                }
            }
        }
    }

    // ---- the list ----
    Rectangle {
        id: listBox
        x: root.pad
        y: seg.y + seg.height + Serp.px(12)
        width: Serp.px(300)
        height: parent.height - y - root.pad
        radius: Serp.radiusSmall
        color: Qt.alpha(Serp.surface0, 0.45)
        border.width: 1
        border.color: Serp.line
        clip: true
        opacity: root.ease(root.st(0.3))
        transform: Translate {
            x: (1 - root.ease(root.st(0.3))) * -Serp.px(16)
        }
        SText {
            anchors.centerIn: parent
            visible: list.count === 0
            text: SerpKit.invBusy || !SerpKit.inv ? "Собираю…" : "Пусто"
            dim: true
        }
        ListView {
            id: list
            anchors.fill: parent
            anchors.margins: Serp.px(6)
            spacing: Serp.px(2)
            model: root.items
            boundsBehavior: Flickable.StopAtBounds
            onCountChanged: Qt.callLater(root.syncList)
            highlightFollowsCurrentItem: true
            highlightMoveDuration: root.still ? 0 : 260
            highlightMoveVelocity: -1
            highlightResizeDuration: 0
            highlight: Rectangle {
                radius: Serp.radiusSmall
                color: Serp.selected
                border.width: 1
                border.color: Qt.alpha(Serp.accent, 0.35)
            }
            delegate: Item {
                id: row
                required property var modelData
                required property int index
                readonly property string s: root.norm(modelData)
                readonly property bool picked: root.cur === modelData
                width: ListView.view.width
                height: Serp.px(root.tab === "system" ? 44 : 50)
                // in, one after another, when the group changes
                property real inT: 1
                Component.onCompleted: rowIn.restart()
                Connections {
                    target: root
                    function onGenChanged() {
                        rowIn.restart();
                    }
                }
                SequentialAnimation {
                    id: rowIn
                    PropertyAction {
                        target: row
                        property: "inT"
                        value: root.still ? 1 : 0
                    }
                    PauseAnimation {
                        duration: root.still ? 0 : Math.min(row.index, 8) * 22
                    }
                    NumberAnimation {
                        target: row
                        property: "inT"
                        to: 1
                        duration: root.still ? 0 : 320
                        easing.type: Easing.OutCubic
                    }
                }
                opacity: inT
                transform: Translate {
                    x: (1 - row.inT) * -Serp.px(12)
                }
                Rectangle {
                    anchors.fill: parent
                    radius: Serp.radiusSmall
                    color: rowMa.containsMouse && !row.picked ? Serp.hover : "transparent"
                }
                // the state dot (a beat while broken)
                Rectangle {
                    id: dot
                    x: Serp.px(10)
                    anchors.verticalCenter: parent.verticalCenter
                    width: Serp.px(9)
                    height: width
                    radius: width / 2
                    color: root.tone(row.s)
                    SequentialAnimation on opacity {
                        running: row.s === "bad" && !root.still
                        loops: Animation.Infinite
                        NumberAnimation {
                            to: 0.35
                            duration: 600
                        }
                        NumberAnimation {
                            to: 1
                            duration: 600
                        }
                    }
                }
                Column {
                    anchors.left: dot.right
                    anchors.leftMargin: Serp.px(10)
                    anchors.right: side.left
                    anchors.rightMargin: Serp.px(6)
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Serp.px(2)
                    SText {
                        width: parent.width
                        text: row.modelData.num ? row.modelData.num + " · " + row.modelData.name : row.modelData.title || row.modelData.name
                        size: Serp.px(12)
                        bold: true
                        elide: Text.ElideRight
                    }
                    SText {
                        visible: text !== ""
                        width: parent.width
                        text: root.tab === "system" ? row.modelData.note || "" : root.tab === "audit" ? row.modelData.path : row.modelData.desc || ""
                        size: Serp.px(10)
                        dim: true
                        elide: Text.ElideRight
                    }
                }
                SText {
                    id: side
                    anchors.right: parent.right
                    anchors.rightMargin: Serp.px(8)
                    anchors.verticalCenter: parent.verticalCenter
                    text: {
                        const m = row.modelData;
                        if (root.tab === "audit")
                            return "+" + m.plus + " −" + m.minus;
                        if (m.plus !== undefined)
                            return "+" + m.plus;
                        if (m.touched)
                            return m.touched + (root.tab === "plugins" ? " ф." : " ф.");
                        return "";
                    }
                    size: Serp.px(9.5)
                    color: Serp.subtext0
                }
                MouseArea {
                    id: rowMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.pick(row.modelData)
                }
            }
        }
    }

    // ---- the piece ----
    Rectangle {
        id: detail
        x: listBox.x + listBox.width + Serp.px(12)
        y: listBox.y
        width: parent.width - x - root.pad
        height: listBox.height
        radius: Serp.radiusSmall
        color: Qt.alpha(Serp.surface0, 0.45)
        border.width: 1
        border.color: Serp.line
        clip: true
        opacity: root.ease(root.st(0.38))
        transform: Translate {
            x: (1 - root.ease(root.st(0.38))) * Serp.px(16)
        }

        Item {
            id: dBody
            anchors.fill: parent
            anchors.margins: Serp.px(14)
            visible: !!root.cur
            // a new piece slides in
            property real k: 1
            opacity: k
            transform: Translate {
                x: (1 - dBody.k) * Serp.px(14)
            }
            NumberAnimation {
                id: detailIn
                target: dBody
                property: "k"
                from: root.still ? 1 : 0.3
                to: 1
                duration: root.still ? 0 : 300
                easing.type: Easing.OutCubic
            }

            // the title
            Item {
                id: dHead
                width: parent.width
                height: Serp.px(44)
                Rectangle {
                    id: dIcon
                    width: Serp.px(40)
                    height: width
                    radius: Serp.radiusSmall
                    color: Qt.alpha(root.tone(root.norm(root.cur)), 0.16)
                    SIcon {
                        anchors.centerIn: parent
                        name: root.tabs.find(t => t.id === root.tab).icon
                        size: Serp.px(20)
                        color: root.tone(root.norm(root.cur))
                    }
                }
                Column {
                    anchors.left: dIcon.right
                    anchors.leftMargin: Serp.px(12)
                    anchors.right: chip.left
                    anchors.rightMargin: Serp.px(8)
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Serp.px(2)
                    SText {
                        width: parent.width
                        text: root.cur ? (root.cur.num ? root.cur.num + " · " : "") + (root.cur.title || root.cur.name) : ""
                        size: Serp.px(15)
                        black: true
                        elide: Text.ElideRight
                    }
                    SText {
                        width: parent.width
                        text: root.cur ? (root.cur.source || root.cur.path || "") : ""
                        size: Serp.px(10)
                        dim: true
                        elide: Text.ElideMiddle
                    }
                }
                Rectangle {
                    id: chip
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    height: Serp.px(24)
                    width: chipText.implicitWidth + Serp.px(22)
                    radius: height / 2
                    color: Qt.alpha(root.tone(root.norm(root.cur)), 0.16)
                    border.width: 1
                    border.color: Qt.alpha(root.tone(root.norm(root.cur)), 0.4)
                    SText {
                        id: chipText
                        anchors.centerIn: parent
                        text: root.stateWord(root.cur)
                        size: Serp.px(10.5)
                        bold: true
                        color: root.tone(root.norm(root.cur))
                    }
                }
            }

            // Обзор | Изменения | История
            Rectangle {
                id: vseg
                y: dHead.height + Serp.px(10)
                visible: root.hasChanges || root.hasHistory
                width: parent.width
                height: visible ? Serp.px(30) : 0
                radius: height / 2
                color: Qt.alpha(Serp.base, 0.35)
                readonly property var views: [
                    {
                        "id": "about",
                        "icon": "info",
                        "label": "Обзор",
                        "on": true
                    },
                    {
                        "id": "diff",
                        "icon": "file-text",
                        "label": "Изменения",
                        "on": root.hasChanges
                    },
                    {
                        "id": "history",
                        "icon": "clock",
                        "label": "История" + (root.cur && root.cur.commits ? " · " + root.cur.commits : ""),
                        "on": root.hasHistory
                    }
                ].filter(v => v.on)
                readonly property real cell: (width - Serp.px(6)) / Math.max(1, views.length)
                readonly property int at: Math.max(0, views.findIndex(v => v.id === root.view))
                Rectangle {
                    id: vPill
                    x: Serp.px(3) + vseg.at * vseg.cell
                    y: Serp.px(3)
                    width: vseg.cell
                    height: Math.max(0, vseg.height - Serp.px(6))
                    radius: height / 2
                    color: Serp.surface1
                    border.width: 1
                    border.color: Qt.alpha(Serp.accent, 0.4)
                    Behavior on x {
                        NumberAnimation {
                            duration: root.still ? 0 : Serp.normal
                            easing.type: Easing.OutQuint
                        }
                    }
                }
                Row {
                    anchors.fill: parent
                    anchors.margins: Serp.px(3)
                    Repeater {
                        model: vseg.views
                        Item {
                            id: vItem
                            required property var modelData
                            required property int index
                            readonly property bool on: Math.abs(vPill.x - Serp.px(3) - index * vseg.cell) < vseg.cell / 2
                            width: vseg.cell
                            height: parent.height
                            Row {
                                anchors.centerIn: parent
                                spacing: Serp.px(5)
                                SIcon {
                                    anchors.verticalCenter: parent.verticalCenter
                                    name: vItem.modelData.icon
                                    size: Serp.px(12)
                                    color: vItem.on ? Serp.accent : Serp.subtext0
                                }
                                SText {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: vItem.modelData.label
                                    size: Serp.px(10.5)
                                    bold: vItem.on
                                    color: vItem.on ? Serp.text : Serp.subtext0
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.view = vItem.modelData.id
                            }
                        }
                    }
                }
            }

            // the page under the switch
            Item {
                id: page
                y: vseg.y + vseg.height + Serp.px(10)
                width: parent.width
                height: parent.height - y

                // --- Обзор ---
                Flickable {
                    id: about
                    anchors.fill: parent
                    visible: root.view === "about"
                    clip: true
                    contentWidth: width
                    contentHeight: aboutCol.implicitHeight + Serp.px(8)
                    boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: aboutCol
                        width: about.width
                        spacing: Serp.px(10)
                        // what it does
                        SText {
                            visible: text !== ""
                            width: parent.width
                            text: root.cur ? root.cur.desc || "" : ""
                            size: Serp.px(12.5)
                            wrapMode: Text.WordWrap
                            elide: Text.ElideNone
                        }
                        SText {
                            visible: text !== ""
                            width: parent.width
                            text: root.cur && root.tab !== "audit" ? root.cur.note || "" : ""
                            size: Serp.px(11)
                            color: root.tone(root.norm(root.cur)) === Serp.green ? Serp.subtext0 : root.tone(root.norm(root.cur))
                            wrapMode: Text.WordWrap
                            elide: Text.ElideNone
                        }
                        // the proof
                        Rectangle {
                            visible: root.tab === "shell" || root.tab === "niri" || root.tab === "satellite" || root.tab === "plugins"
                            width: parent.width
                            height: proofRow.implicitHeight + Serp.px(18)
                            radius: Serp.radiusSmall
                            readonly property bool good: !!root.cur && root.cur.proven !== false
                            color: Qt.alpha(good ? Serp.green : SerpKit.warnColor, 0.1)
                            border.width: 1
                            border.color: Qt.alpha(good ? Serp.green : SerpKit.warnColor, 0.3)
                            Row {
                                id: proofRow
                                x: Serp.px(10)
                                y: Serp.px(9)
                                width: parent.width - Serp.px(20)
                                spacing: Serp.px(8)
                                SIcon {
                                    name: parent.parent.good ? "check" : "shield"
                                    size: Serp.px(15)
                                    color: parent.parent.good ? Serp.green : SerpKit.warnColor
                                }
                                SText {
                                    width: parent.width - Serp.px(24)
                                    wrapMode: Text.WordWrap
                                    elide: Text.ElideNone
                                    size: Serp.px(11)
                                    text: {
                                        const c = root.cur;
                                        if (!c)
                                            return "";
                                        if (root.tab === "plugins")
                                            return "Плагин целиком наш: у автора такого нет. Установленная копия сверена с pc-kit (правки скина serp в ней учтены).";
                                        if (root.tab === "niri" || root.tab === "satellite") {
                                            const g = SerpKit.group(root.tab);
                                            return "Патч исходников компоситора: +" + c.plus + " / −" + c.minus + " строк в " + c.touched + " файлах. Собирается скриптом из чистого кода автора, сейчас стоит сборка " + (g ? g.build : "?") + ".";
                                        }
                                        const mine = (c.files || []).filter(f => f.mine);
                                        const whole = mine.filter(f => !f.author).length;
                                        if (c.state !== "on")
                                            return (c.disabled ? "Сейчас снят тобой" : "Сейчас не стоит") + ": его файлы как у автора (angelOS " + (SerpKit.inv ? SerpKit.inv.author.rev : "") + "). Пар «было → стало» в патче: " + c.pairs + ".";
                                        if (!c.proven)
                                            return "Не всё сходится: в его файлах есть правки, которых нет ни в одном патче. Смотри «Изменения».";
                                        return "Доказано: если откатить наши правки, получается ровно файл автора (angelOS " + (SerpKit.inv ? SerpKit.inv.author.rev : "") + "). Правит " + (mine.length - whole) + " файл(ов) автора" + (whole ? ", и " + whole + " файл(ов) целиком наши" : "") + "; пар «было → стало»: " + c.pairs + ".";
                                    }
                                }
                            }
                        }
                        // its files
                        SText {
                            visible: fileRep.count > 0
                            text: "Файлы"
                            size: Serp.px(11)
                            bold: true
                            color: Serp.subtext1
                        }
                        Repeater {
                            id: fileRep
                            model: root.cur && root.tab !== "audit" ? (root.cur.files || []).filter(f => f.mine || f.author) : []
                            Rectangle {
                                id: fileRow
                                required property var modelData
                                width: aboutCol.width
                                height: Serp.px(38)
                                radius: Serp.radiusSmall
                                color: fMa.containsMouse ? Serp.hover : Qt.alpha(Serp.base, 0.25)
                                SIcon {
                                    id: fIcon
                                    x: Serp.px(10)
                                    anchors.verticalCenter: parent.verticalCenter
                                    name: "file"
                                    size: Serp.px(14)
                                    color: fileRow.modelData.mine ? Serp.accent : Serp.subtext0
                                }
                                Column {
                                    anchors.left: fIcon.right
                                    anchors.leftMargin: Serp.px(8)
                                    anchors.right: fTags.left
                                    anchors.rightMargin: Serp.px(6)
                                    anchors.verticalCenter: parent.verticalCenter
                                    SText {
                                        width: parent.width
                                        text: fileRow.modelData.name
                                        size: Serp.px(11.5)
                                        bold: true
                                        elide: Text.ElideRight
                                    }
                                    SText {
                                        width: parent.width
                                        text: fileRow.modelData.path
                                        size: Serp.px(9.5)
                                        dim: true
                                        elide: Text.ElideMiddle
                                    }
                                }
                                Row {
                                    id: fTags
                                    anchors.right: parent.right
                                    anchors.rightMargin: Serp.px(8)
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: Serp.px(4)
                                    Repeater {
                                        model: {
                                            const f = fileRow.modelData;
                                            const t = [];
                                            if (!f.author)
                                                t.push({
                                                    "text": "наш файл",
                                                    "c": Serp.accent
                                                });
                                            else if (f.mine)
                                                t.push({
                                                    "text": "правка",
                                                    "c": Serp.green
                                                });
                                            else
                                                t.push({
                                                    "text": "не тронут",
                                                    "c": Serp.subtext0
                                                });
                                            if (f.others && f.others.length)
                                                t.push({
                                                    "text": "+ " + f.others.join(", "),
                                                    "c": Serp.subtext0
                                                });
                                            return t;
                                        }
                                        Rectangle {
                                            id: tag
                                            required property var modelData
                                            height: Serp.px(18)
                                            width: Math.min(tagText.implicitWidth + Serp.px(12), Serp.px(150))
                                            radius: height / 2
                                            color: Qt.alpha(tag.modelData.c, 0.14)
                                            SText {
                                                id: tagText
                                                anchors.centerIn: parent
                                                width: Math.min(implicitWidth, Serp.px(138))
                                                text: tag.modelData.text
                                                size: Serp.px(9)
                                                color: tag.modelData.c
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }
                                }
                                MouseArea {
                                    id: fMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: root.hasChanges ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: if (root.hasChanges)
                                        root.view = "diff"
                                }
                            }
                        }
                        // the switch: hold to confirm
                        Item {
                            visible: root.tab === "shell" && !!root.cur
                            width: parent.width
                            height: visible ? Serp.px(74) : 0
                            readonly property bool isOn: !!root.cur && root.cur.state === "on"
                            readonly property bool can: !!root.cur && root.cur.canToggle === true
                            SText {
                                visible: !parent.can
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width
                                wrapMode: Text.WordWrap
                                elide: Text.ElideNone
                                text: "Скин serp снимается только из терминала: эта панель сама живёт в нём (kit revert serp-skin после angelos settingsSkin classic)."
                                size: Serp.px(10.5)
                                dim: true
                            }
                            SHoldButton {
                                id: hold
                                visible: parent.can && SerpKit.acting === ""
                                width: Serp.px(150)
                                height: parent.height
                                icon: parent.isOn ? "undo-2" : "power"
                                label: parent.isOn ? "Держи: снять" : "Держи: включить"
                                weight: 1.6
                                tint: parent.isOn ? Serp.red : Serp.green
                                onConfirmed: SerpKit.act(parent.isOn ? "revert" : "apply", root.cur.name)
                            }
                            Row {
                                visible: SerpKit.acting !== ""
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: Serp.px(8)
                                SIcon {
                                    name: "refresh-cw"
                                    size: Serp.px(14)
                                    color: Serp.accent
                                    RotationAnimation on rotation {
                                        running: SerpKit.acting !== ""
                                        from: 0
                                        to: 360
                                        duration: 900
                                        loops: Animation.Infinite
                                    }
                                }
                                SText {
                                    text: "Работаю над " + SerpKit.acting + "… ответ придёт уведомлением"
                                    size: Serp.px(11)
                                }
                            }
                            SText {
                                visible: parent.can && SerpKit.acting === ""
                                anchors.left: hold.right
                                anchors.leftMargin: Serp.px(12)
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                wrapMode: Text.WordWrap
                                elide: Text.ElideNone
                                size: Serp.px(10.5)
                                dim: true
                                text: (parent.isOn ? "Вернёт файлы автора и запомнит, что патч снят тобой: сторож не поставит его обратно." : "Поставит патч заново (kit apply " + (root.cur ? root.cur.name : "") + ").") + (root.cur && root.cur.restartsShell ? " Шелл перезапустится." : "")
                            }
                        }
                    }
                }

                // --- Изменения: the piece's own lines ---
                Item {
                    anchors.fill: parent
                    visible: root.view === "diff"
                    readonly property var files: root.cur ? SerpKit.diffs[root.cur.id] || null : null
                    readonly property var lines: {
                        const out = [];
                        (files || []).forEach(f => {
                            out.push({
                                "t": "file",
                                "s": f.path
                            });
                            if (f.whole) {
                                out.push({
                                    "t": "whole",
                                    "s": "наш файл целиком: " + f.lines + " строк, у автора его нет"
                                });
                                return;
                            }
                            (f.diff || "").split("\n").forEach(l => {
                                if (l.startsWith("--- ") || l.startsWith("+++ ") || l.startsWith("index ") || l === "")
                                    return;
                                out.push({
                                    "t": l.startsWith("@@") ? "@" : l.startsWith("+") ? "+" : l.startsWith("-") ? "-" : " ",
                                    "s": l.startsWith("@@") ? l.replace(/^@@ [^@]*@@ ?/, "") : l.substring(1)
                                });
                            });
                            if (f.left)
                                out.push({
                                    "t": "left",
                                    "s": "в этом файле есть правки вне патчей"
                                });
                        });
                        return out;
                    }
                    SText {
                        anchors.centerIn: parent
                        visible: !parent.files
                        text: "Достаю изменения…"
                        dim: true
                    }
                    ListView {
                        id: diffList
                        anchors.fill: parent
                        clip: true
                        model: parent.lines
                        boundsBehavior: Flickable.StopAtBounds
                        cacheBuffer: Serp.px(600)
                        delegate: Rectangle {
                            id: dl
                            required property var modelData
                            width: ListView.view.width
                            height: modelData.t === "file" ? Serp.px(30) : modelData.t === "@" ? Serp.px(22) : Math.max(Serp.px(17), dlText.implicitHeight + Serp.px(2))
                            color: modelData.t === "+" ? Qt.alpha(Serp.green, 0.13) : modelData.t === "-" ? Qt.alpha(Serp.red, 0.13) : modelData.t === "file" ? "transparent" : "transparent"
                            SText {
                                visible: dl.modelData.t === "+" || dl.modelData.t === "-"
                                x: Serp.px(4)
                                y: Serp.px(1)
                                text: dl.modelData.t
                                size: Serp.px(10.5)
                                bold: true
                                color: dl.modelData.t === "+" ? Serp.green : Serp.red
                            }
                            SText {
                                id: dlText
                                x: dl.modelData.t === "file" ? 0 : Serp.px(16)
                                y: dl.modelData.t === "file" ? Serp.px(10) : dl.modelData.t === "@" ? Serp.px(5) : Serp.px(1)
                                width: dl.width - x - Serp.px(4)
                                text: dl.modelData.s
                                size: dl.modelData.t === "file" ? Serp.px(11) : Serp.px(10.5)
                                bold: dl.modelData.t === "file"
                                color: dl.modelData.t === "file" ? Serp.accent : dl.modelData.t === "@" || dl.modelData.t === "whole" ? Serp.subtext0 : dl.modelData.t === "left" ? SerpKit.warnColor : Serp.text
                                wrapMode: Text.WrapAnywhere
                                elide: Text.ElideNone
                                textFormat: Text.PlainText
                            }
                        }
                    }
                }

                // --- История: its commits in pc-kit ---
                ListView {
                    anchors.fill: parent
                    visible: root.view === "history"
                    clip: true
                    model: root.cur && root.cur.history ? root.cur.history : []
                    boundsBehavior: Flickable.StopAtBounds
                    spacing: 0
                    delegate: Item {
                        id: hc
                        required property var modelData
                        required property int index
                        width: ListView.view.width
                        height: hcCol.implicitHeight + Serp.px(14)
                        // the time line
                        Rectangle {
                            x: Serp.px(7)
                            y: hc.index === 0 ? Serp.px(10) : 0
                            width: Serp.px(2)
                            height: hc.height - (hc.index === 0 ? Serp.px(10) : 0)
                            color: Serp.line
                        }
                        Rectangle {
                            x: Serp.px(3)
                            y: Serp.px(6)
                            width: Serp.px(10)
                            height: width
                            radius: width / 2
                            color: hc.index === 0 ? Serp.accent : Serp.surface1
                            border.width: 1
                            border.color: Serp.accent
                        }
                        Column {
                            id: hcCol
                            x: Serp.px(24)
                            y: Serp.px(2)
                            width: hc.width - x
                            spacing: Serp.px(2)
                            Row {
                                spacing: Serp.px(8)
                                SText {
                                    text: hc.modelData.hash
                                    size: Serp.px(10.5)
                                    bold: true
                                    color: Serp.accent
                                }
                                SText {
                                    text: hc.modelData.date
                                    size: Serp.px(10.5)
                                    dim: true
                                }
                            }
                            SText {
                                width: parent.width
                                text: hc.modelData.subject
                                size: Serp.px(11)
                                wrapMode: Text.WordWrap
                                elide: Text.ElideNone
                                maximumLineCount: 4
                            }
                        }
                    }
                }
            }
        }
    }
}
