pragma ComponentBehavior: Bound

import QtQuick
import qs.services
import qs.modules.serp

// serp-skin: pc-kit as a living tree (SerpKitPanel's «Дерево»), in the family of the network
// orbit. The author's angelOS is the root in the middle; our six branches (shell, niri,
// satellite, plugins, system, outside the patches) stand round it; every piece is a leaf on the
// outer ring. The picked branch opens its leaves over a wide arc with their names, the others
// close up into beads; changing branch turns the whole ring (one morph, 750 ms). Inside the ring,
// chords tie the picked leaf to the leaves that change the same files (thicker = more files in
// common). A spark runs root → branch → leaf; while kit is asked, waves leave the root.
// Lines are one Canvas (repainted only while something moves), nodes are plain Items.
Item {
    id: tree
    // [{id, icon, label, items: [...]}] — the panel's groups, in the switch's order
    property var groups: []
    property string selGroup: "shell"
    property string selId: ""
    property var toneOf: s => Serp.text      // a piece → its colour (the panel's tone(norm(it)))
    property var badOf: it => false          // a piece that should beat
    property color rootTone: Serp.green
    property string rootIcon: "check"
    property string rootLabel: "angelOS"
    property string rootSub: ""
    property bool busy: false
    property bool still: false
    signal pickGroup(string gid)
    signal pickItem(string gid, var item)
    signal rootClicked

    // ---- measures ----
    readonly property real cx: width / 2
    readonly property real cy: height / 2 + Serp.px(22)
    // the names stand level in two columns beside the ring (turned 10 px text can't be sharp:
    // a 1 px stroke at 30-60° is smeared by antialiasing whatever the renderer, 2026-11-14)
    readonly property real colW: Serp.px(128)
    readonly property real colGap: Serp.px(22)
    readonly property real leafR: Math.max(Serp.px(60), Math.min((width - (colW + colGap) * 2) / 2, height / 2 - Serp.px(36)))
    readonly property real branchR: leafR * 0.52
    function pt(aDeg, r) {
        const a = aDeg * Math.PI / 180;
        return {
            "x": cx + Math.cos(a) * r,
            "y": cy + Math.sin(a) * r
        };
    }

    // ---- the leaves, flat ----
    readonly property var leaves: {
        const out = [];
        groups.forEach((g, gi) => (g.items || []).forEach((it, li) => out.push({
                        "g": gi,
                        "gid": g.id,
                        "i": li,
                        "n": g.items.length,
                        "item": it
                    })));
        return out;
    }
    readonly property int selIdx: Math.max(0, groups.findIndex(g => g.id === selGroup))

    // ---- the layout: every leaf's angle and every branch's, for one picked branch ----
    function layoutFor(sel) {
        const n = groups.length;
        if (!n)
            return {
                "leaf": [],
                "branch": []
            };
        const counts = groups.map(g => Math.max(1, (g.items || []).length));
        const gap = 7;
        // the picked one: ~24 px a leaf at the ring, between 50° and 230°
        const selArc = Math.max(50, Math.min(240, counts[sel] * Serp.px(22) / leafR * 180 / Math.PI));
        const rest = 360 - selArc - gap * n;
        const others = counts.reduce((s, c, i) => s + (i === sel ? 0 : Math.sqrt(c)), 0);
        const arcs = counts.map((c, i) => i === sel ? selArc : Math.max(6, rest * Math.sqrt(c) / Math.max(1, others)));
        const branch = new Array(n).fill(0);
        const starts = new Array(n).fill(0);
        let cur = -90 - selArc / 2;
        for (let k = 0; k < n; k++) {
            const g = (sel + k) % n;
            starts[g] = cur;
            branch[g] = cur + arcs[g] / 2;
            cur += arcs[g] + gap;
        }
        const leaf = leaves.map(l => starts[l.g] + (l.i + 0.5) * arcs[l.g] / l.n);
        return {
            "leaf": leaf,
            "branch": branch
        };
    }
    property var fromL: ({
            "leaf": [],
            "branch": []
        })
    property var toL: ({
            "leaf": [],
            "branch": []
        })
    property real morph: 1
    function relayout(animate) {
        const next = layoutFor(selIdx);
        if (animate && !still && toL.leaf.length === next.leaf.length && toL.branch.length === next.branch.length) {
            // from wherever it stands now
            fromL = {
                "leaf": next.leaf.map((_, i) => leafAngle(i)),
                "branch": next.branch.map((_, i) => branchAngle(i))
            };
            toL = next;
            morphAnim.restart();
        } else {
            fromL = next;
            toL = next;
            morph = 1;
        }
    }
    function lerpAngle(a, b, t) {
        const d = ((b - a) % 360 + 540) % 360 - 180;
        return a + d * t;
    }
    function ease(t) {
        return 1 - Math.pow(1 - t, 3);
    }
    function leafAngle(i) {
        const a = fromL.leaf[i], b = toL.leaf[i];
        return a === undefined || b === undefined ? (b || 0) : lerpAngle(a, b, ease(morph));
    }
    function branchAngle(i) {
        const a = fromL.branch[i], b = toL.branch[i];
        return a === undefined || b === undefined ? (b || 0) : lerpAngle(a, b, ease(morph));
    }
    NumberAnimation {
        id: morphAnim
        target: tree
        property: "morph"
        from: 0
        to: 1
        duration: 750
        easing.type: Easing.Linear
    }
    onSelIdxChanged: relayout(true)
    onLeavesChanged: relayout(false)
    onLeafRChanged: relayout(false)
    Component.onCompleted: relayout(false)

    // ---- the tree grows in when shown ----
    property real grow: still ? 1 : 0
    NumberAnimation on grow {
        running: !tree.still
        from: 0
        to: 1
        duration: 1100
        easing.type: Easing.OutCubic
    }
    function clamp(x) {
        return Math.max(0, Math.min(1, x));
    }

    // ---- what shares files with the picked leaf (same branch) ----
    function ownFiles(it) {
        return (it && it.files || []).filter(f => f.mine).map(f => f.path);
    }
    readonly property var selLeaf: leaves.find(l => l.item.id === selId) || null
    readonly property var chords: {
        if (!selLeaf)
            return [];
        const mine = ownFiles(selLeaf.item);
        if (!mine.length)
            return [];
        const out = [];
        leaves.forEach((l, i) => {
            if (l.g !== selLeaf.g || l.item.id === selId)
                return;
            const shared = ownFiles(l.item).filter(p => mine.indexOf(p) >= 0);
            if (shared.length)
                out.push({
                    "to": i,
                    "n": shared.length,
                    "files": shared
                });
        });
        return out;
    }
    readonly property int selLeafIdx: selLeaf ? leaves.indexOf(selLeaf) : -1
    property real chordT: 1
    onSelIdChanged: {
        if (still)
            chordT = 1;
        else
            chordAnim.restart();
    }
    NumberAnimation {
        id: chordAnim
        target: tree
        property: "chordT"
        from: 0
        to: 1
        duration: 650
        easing.type: Easing.OutCubic
    }

    // ---- the names: the picked branch's leaves, left half → left column, right half → right,
    // each at its leaf's height, pushed apart to one row each, kept inside ----
    readonly property real rowH: Serp.px(17)
    // from where the leaves END UP (toL), not where they are mid-turn: a leaf crossing the middle
    // threw its name into the other column for a frame (2026-11-14); the leaders do the moving
    readonly property var labels: {
        const out = {};
        const sides = [[], []];
        leaves.forEach((l, i) => {
            if (l.g !== selIdx)
                return;
            const a = toL.leaf[i] === undefined ? 0 : toL.leaf[i], p = pt(a, leafR);
            sides[p.x < cx ? 0 : 1].push({
                "i": i,
                "y": p.y,
                "a": a
            });
        });
        sides.forEach((arr, s) => {
            // top to bottom in the leaves' own order (from the arc's top outward): the leaders
            // never cross. Spread evenly from above the ring down to the lowest leaf
            arr.sort((x, y) => x.y - y.y);
            const n = arr.length;
            if (!n)
                return;
            const minTop = rowH / 2 + Serp.px(4), maxBottom = height - rowH / 2 - Serp.px(30);
            const top = Math.max(minTop, cy - leafR - Serp.px(26));
            const bottom = Math.min(maxBottom, Math.max(top + (n - 1) * rowH, arr[n - 1].y + Serp.px(6)));
            const step = n > 1 ? Math.max(rowH, (bottom - top) / (n - 1)) : 0;
            const t0 = Math.max(minTop, Math.min(top, maxBottom - (n - 1) * step));
            arr.forEach((e, k) => out[e.i] = {
                    "side": s,
                    "y": t0 + k * step
                });
        });
        return out;
    }
    // where a name's leader ends (the column's inner edge)
    function labelEdge(side) {
        return side === 0 ? colW + Serp.px(6) : width - colW - Serp.px(6);
    }

    property int hovered: -1          // a leaf under the pointer
    property int hoveredBranch: -1

    // ---- the lines: one canvas ----
    Canvas {
        id: lines
        anchors.fill: parent
        renderTarget: Canvas.FramebufferObject
        renderStrategy: Canvas.Cooperative
        function bez(p0, p1, p2, p3, t) {
            const u = 1 - t;
            return {
                "x": u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
                "y": u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y
            };
        }
        onPaint: {
            const c = getContext("2d");
            c.reset();
            const g1 = tree.clamp(tree.grow * 2.2), g2 = tree.clamp(tree.grow * 2.2 - 0.9);
            const o = {
                "x": tree.cx,
                "y": tree.cy
            };
            c.lineCap = "round";
            // root → branches
            tree.groups.forEach((g, gi) => {
                const a = tree.branchAngle(gi), b = tree.pt(a, tree.branchR * g1);
                const sel = gi === tree.selIdx;
                c.strokeStyle = sel ? Qt.alpha(Serp.accent, 0.6) : Qt.alpha(Serp.text, gi === tree.hoveredBranch ? 0.3 : 0.13);
                c.lineWidth = sel ? Serp.px(2.2) : Serp.px(1.2);
                c.beginPath();
                c.moveTo(o.x, o.y);
                c.lineTo(b.x, b.y);
                c.stroke();
            });
            if (g2 <= 0)
                return;
            // branches → leaves (a radial dendrogram: out from the branch, then round to the leaf)
            const mid = (tree.branchR + tree.leafR) / 2;
            tree.leaves.forEach((l, i) => {
                const ab = tree.branchAngle(l.g), al = tree.leafAngle(i);
                const p0 = tree.pt(ab, tree.branchR), p1 = tree.pt(ab, mid), p2 = tree.pt(al, mid), p3 = tree.pt(al, tree.leafR);
                const sel = l.g === tree.selIdx, picked = i === tree.selLeafIdx, hov = i === tree.hovered;
                c.strokeStyle = picked ? Serp.accent : sel ? Qt.alpha(tree.toneOf(l.item), hov ? 0.7 : 0.32) : Qt.alpha(Serp.text, hov ? 0.3 : 0.06);
                c.lineWidth = picked ? Serp.px(2.2) : sel ? Serp.px(1.3) : Serp.px(1);
                c.beginPath();
                c.moveTo(p0.x, p0.y);
                const steps = 18, end = g2;
                for (let s = 1; s <= steps; s++) {
                    const q = bez(p0, p1, p2, p3, s / steps * end);
                    c.lineTo(q.x, q.y);
                }
                c.stroke();
            });
            // chords: the picked leaf ↔ the ones changing the same files
            // leaders: leaf → its name in the column
            const gl = tree.clamp(tree.grow * 2.6 - 1.5) * (tree.morph < 1 ? tree.ease(tree.morph) : 1);
            if (gl > 0) {
                c.globalAlpha = gl;
                for (const k in tree.labels) {
                    const i = Number(k), lb = tree.labels[k], l = tree.leaves[i];
                    if (!l)
                        continue;
                    const a = tree.leafAngle(i), p0 = tree.pt(a, tree.leafR + Serp.px(7)), p1 = tree.pt(a, tree.leafR + Serp.px(22));
                    const ex = tree.labelEdge(lb.side), dir = lb.side === 0 ? 1 : -1;
                    const picked = i === tree.selLeafIdx, hov = i === tree.hovered;
                    c.strokeStyle = picked ? Qt.alpha(Serp.accent, 0.9) : Qt.alpha(tree.toneOf(l.item), hov ? 0.6 : 0.22);
                    c.lineWidth = picked ? Serp.px(1.6) : Serp.px(1);
                    c.beginPath();
                    c.moveTo(p0.x, p0.y);
                    c.bezierCurveTo(p1.x, p1.y, ex + dir * Serp.px(18), lb.y, ex, lb.y);
                    c.stroke();
                }
                c.globalAlpha = 1;
            }
            // chords last: after the leaves they join have grown in
            const chordK = tree.chordT * tree.clamp((g2 - 0.7) / 0.3);
            if (tree.selLeafIdx >= 0 && chordK > 0) {
                const a0 = tree.leafAngle(tree.selLeafIdx), s0 = tree.pt(a0, tree.leafR - Serp.px(10));
                tree.chords.forEach(ch => {
                    const a1 = tree.leafAngle(ch.to), s1 = tree.pt(a1, tree.leafR - Serp.px(10));
                    // bowed toward the middle
                    const m = {
                        "x": tree.cx + ((s0.x + s1.x) / 2 - tree.cx) * 0.25,
                        "y": tree.cy + ((s0.y + s1.y) / 2 - tree.cy) * 0.25
                    };
                    const hov = ch.to === tree.hovered;
                    c.strokeStyle = Qt.alpha(Serp.accent, hov ? 0.85 : 0.45);
                    c.lineWidth = Serp.px(1) + Math.min(3, ch.n) * Serp.px(0.9);
                    c.beginPath();
                    c.moveTo(s0.x, s0.y);
                    const steps = 24;
                    for (let s = 1; s <= steps; s++) {
                        const t = s / steps * chordK, u = 1 - t;
                        c.lineTo(u * u * s0.x + 2 * u * t * m.x + t * t * s1.x, u * u * s0.y + 2 * u * t * m.y + t * t * s1.y);
                    }
                    c.stroke();
                });
            }
        }
        // repaint only while something moves
        Connections {
            target: tree
            function onMorphChanged() {
                lines.requestPaint();
            }
            function onGrowChanged() {
                lines.requestPaint();
            }
            function onChordTChanged() {
                lines.requestPaint();
            }
            function onHoveredChanged() {
                lines.requestPaint();
            }
            function onHoveredBranchChanged() {
                lines.requestPaint();
            }
            function onSelIdChanged() {
                lines.requestPaint();
            }
            function onLeavesChanged() {
                lines.requestPaint();
            }
            function onWidthChanged() {
                lines.requestPaint();
            }
            function onHeightChanged() {
                lines.requestPaint();
            }
        }
    }

    // ---- while kit is asked: waves out of the root ----
    Repeater {
        model: 2
        Rectangle {
            id: wave
            required property int index
            property real t: 0
            width: tree.leafR * 2
            height: width
            radius: width / 2
            x: tree.cx - width / 2
            y: tree.cy - height / 2
            color: "transparent"
            border.width: Serp.px(2)
            border.color: Serp.accent
            scale: 0.15 + 0.85 * t
            opacity: tree.busy ? 0.35 * (1 - t) : 0
            visible: tree.busy && !tree.still
            SequentialAnimation on t {
                running: wave.visible
                loops: Animation.Infinite
                PauseAnimation {
                    duration: wave.index * 700
                }
                NumberAnimation {
                    from: 0
                    to: 1
                    duration: 1400
                    easing.type: Easing.OutCubic
                }
                PauseAnimation {
                    duration: (1 - wave.index) * 700
                }
            }
        }
    }

    // ---- the spark: root → picked branch → picked leaf ----
    Rectangle {
        id: spark
        property real s: 0
        readonly property var p: {
            tree.morph;
            if (tree.selLeafIdx < 0)
                return {
                    "x": tree.cx,
                    "y": tree.cy
                };
            const ab = tree.branchAngle(tree.selIdx);
            if (s < 0.35)
                return tree.pt(ab, tree.branchR * s / 0.35);
            const t = (s - 0.35) / 0.65, al = tree.leafAngle(tree.selLeafIdx), mid = (tree.branchR + tree.leafR) / 2;
            return lines.bez(tree.pt(ab, tree.branchR), tree.pt(ab, mid), tree.pt(al, mid), tree.pt(al, tree.leafR), t);
        }
        visible: tree.selLeafIdx >= 0 && !tree.still && tree.grow > 0.95
        width: Serp.px(7)
        height: width
        radius: width / 2
        x: p.x - width / 2
        y: p.y - height / 2
        z: 3
        color: Qt.lighter(Serp.accent, 1.3)
        opacity: Math.sin(s * Math.PI) * 0.95
        NumberAnimation on s {
            running: spark.visible
            from: 0
            to: 1
            duration: 1500
            loops: Animation.Infinite
        }
    }

    // ---- the branches ----
    Repeater {
        model: tree.groups
        Item {
            id: br
            required property var modelData
            required property int index
            readonly property bool sel: index === tree.selIdx
            readonly property var p: {
                tree.morph;
                return tree.pt(tree.branchAngle(index), tree.branchR * tree.clamp(tree.grow * 2.2));
            }
            property real size: sel ? Serp.px(34) : Serp.px(26)
            width: size
            height: size
            x: p.x - width / 2
            y: p.y - height / 2
            z: 6
            Behavior on size {
                NumberAnimation {
                    duration: tree.still ? 0 : Serp.normal
                    easing.type: Easing.OutBack
                }
            }
            opacity: tree.clamp(tree.grow * 3 - 0.3 - index * 0.08)
            readonly property int probs: (modelData.items || []).filter(it => tree.badOf(it)).length
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: br.sel ? Serp.accent : brMa.containsMouse ? Serp.surface1 : Serp.surface0
                border.width: 1
                border.color: br.sel ? Qt.lighter(Serp.accent, 1.2) : Qt.alpha(Serp.text, 0.18)
                Behavior on color {
                    ColorAnimation {
                        duration: Serp.normal
                    }
                }
                SIcon {
                    anchors.centerIn: parent
                    name: br.modelData.icon
                    size: br.sel ? Serp.px(16) : Serp.px(13)
                    color: br.sel ? Serp.onAccent : Serp.subtext0
                }
            }
            Rectangle {
                visible: br.probs > 0
                x: parent.width - width + Serp.px(1)
                y: -Serp.px(1)
                width: Serp.px(8)
                height: width
                radius: width / 2
                color: br.modelData.id === "audit" ? SerpKit.warnColor : Serp.red
            }
            MouseArea {
                id: brMa
                anchors.fill: parent
                anchors.margins: -Serp.px(4)
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onContainsMouseChanged: tree.hoveredBranch = containsMouse ? br.index : (tree.hoveredBranch === br.index ? -1 : tree.hoveredBranch)
                onClicked: tree.pickGroup(br.modelData.id)
            }
        }
    }

    // ---- the leaves ----
    Repeater {
        model: tree.leaves
        Item {
            id: lf
            required property var modelData
            required property int index
            readonly property bool open: modelData.g === tree.selIdx
            readonly property bool picked: index === tree.selLeafIdx
            readonly property bool tied: tree.chords.some(ch => ch.to === index)
            readonly property bool hov: tree.hovered === index
            readonly property real a: {
                tree.morph;
                return tree.leafAngle(index);
            }
            readonly property var p: tree.pt(a, tree.leafR)
            readonly property color tone: tree.toneOf(modelData.item)
            property real size: picked ? Serp.px(18) : open ? (hov ? Serp.px(14) : Serp.px(11)) : (hov ? Serp.px(9) : Serp.px(6))
            Behavior on size {
                NumberAnimation {
                    duration: tree.still ? 0 : 220
                    easing.type: Easing.OutBack
                }
            }
            width: size
            height: size
            x: p.x - width / 2
            y: p.y - height / 2
            z: picked ? 9 : hov ? 8 : 7
            // in after the branches, one after another round the ring
            opacity: tree.clamp(tree.grow * 2.6 - 1.2 - (modelData.i / Math.max(1, modelData.n)) * 0.5)
            // a glow under the picked one
            Rectangle {
                visible: lf.picked
                anchors.centerIn: parent
                width: parent.width + Serp.px(12)
                height: width
                radius: width / 2
                color: Qt.alpha(Serp.accent, 0.18)
                SequentialAnimation on scale {
                    running: lf.picked && !tree.still
                    loops: Animation.Infinite
                    NumberAnimation {
                        to: 1.18
                        duration: 1100
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        to: 1
                        duration: 1100
                        easing.type: Easing.InOutSine
                    }
                }
            }
            Rectangle {
                id: dotBody
                anchors.fill: parent
                radius: width / 2
                color: lf.picked ? Serp.accent : lf.open ? Qt.tint(Serp.surface0, Qt.alpha(lf.tone, 0.35)) : Qt.alpha(lf.tone, 0.75)
                border.width: lf.open ? Math.max(1, Serp.px(1.5)) : 0
                border.color: lf.picked ? Qt.lighter(Serp.accent, 1.25) : lf.tied ? Serp.accent : lf.tone
                SequentialAnimation on opacity {
                    running: tree.badOf(lf.modelData.item) && !tree.still
                    loops: Animation.Infinite
                    NumberAnimation {
                        to: 0.35
                        duration: 650
                    }
                    NumberAnimation {
                        to: 1
                        duration: 650
                    }
                }
            }
            MouseArea {
                anchors.centerIn: parent
                width: Math.max(parent.width, Serp.px(14))
                height: width
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onContainsMouseChanged: tree.hovered = containsMouse ? lf.index : (tree.hovered === lf.index ? -1 : tree.hovered)
                onClicked: tree.pickItem(lf.modelData.gid, lf.modelData.item)
            }
        }
    }

    // ---- the picked branch's names, level, in the two columns (sharp: the skin's own text) ----
    Repeater {
        model: tree.leaves
        Item {
            id: lab
            required property var modelData
            required property int index
            readonly property var lb: tree.labels[index] || null
            readonly property bool picked: index === tree.selLeafIdx
            readonly property bool tied: tree.chords.some(ch => ch.to === index)
            readonly property bool hov: tree.hovered === index
            visible: !!lb && opacity > 0.01
            opacity: lb ? tree.clamp(tree.grow * 2.6 - 1.5) * (tree.morph < 1 ? tree.ease(tree.morph) : 1) : 0
            width: tree.colW
            height: tree.rowH
            x: lb ? (lb.side === 0 ? 0 : tree.width - tree.colW) : 0
            y: lb ? lb.y - height / 2 : 0
            z: 5
            Rectangle {
                anchors.fill: parent
                radius: height / 2
                color: lab.picked ? Qt.alpha(Serp.accent, 0.18) : lab.hov ? Serp.hover : "transparent"
            }
            SText {
                anchors.fill: parent
                anchors.leftMargin: Serp.px(7)
                anchors.rightMargin: Serp.px(7)
                horizontalAlignment: lab.lb && lab.lb.side === 0 ? Text.AlignRight : Text.AlignLeft
                text: {
                    const it = lab.modelData.item;
                    return it.num ? it.num.slice(2) + " " + it.name : (it.title && it.title.length < 20 ? it.title : it.name);
                }
                size: Serp.px(11)
                bold: lab.picked || lab.hov
                color: lab.picked ? Serp.accent : lab.tied || lab.hov ? Serp.text : Serp.subtext1
            }
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onContainsMouseChanged: tree.hovered = containsMouse ? lab.index : (tree.hovered === lab.index ? -1 : tree.hovered)
                onClicked: tree.pickItem(lab.modelData.gid, lab.modelData.item)
            }
        }
    }

    // ---- the root: the author's angelOS ----
    Item {
        id: root0
        width: Serp.px(56)
        height: width
        x: tree.cx - width / 2
        y: tree.cy - height / 2
        z: 10
        scale: 0.6 + 0.4 * tree.clamp(tree.grow * 3)
        opacity: tree.clamp(tree.grow * 3)
        Rectangle {
            anchors.centerIn: parent
            width: parent.width + Serp.px(14)
            height: width
            radius: width / 2
            color: Qt.alpha(tree.rootTone, 0.12)
            border.width: 1
            border.color: Qt.alpha(tree.rootTone, 0.25)
            SequentialAnimation on scale {
                running: !tree.still && !tree.busy
                loops: Animation.Infinite
                NumberAnimation {
                    to: 1.08
                    duration: 1600
                    easing.type: Easing.InOutSine
                }
                NumberAnimation {
                    to: 1
                    duration: 1600
                    easing.type: Easing.InOutSine
                }
            }
        }
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            border.width: Serp.px(2)
            border.color: Qt.lighter(Serp.accent, 1.15)
            gradient: Gradient {
                GradientStop {
                    position: 0
                    color: Qt.lighter(Serp.accent, 1.12)
                }
                GradientStop {
                    position: 1
                    color: Qt.darker(Serp.accent, 1.2)
                }
            }
            SIcon {
                anchors.centerIn: parent
                name: "angel"
                size: Serp.px(26)
                color: Serp.onAccent
            }
            // the state, a small badge
            Rectangle {
                x: parent.width - width + Serp.px(2)
                y: parent.height - height + Serp.px(2)
                width: Serp.px(18)
                height: width
                radius: width / 2
                color: Serp.base
                border.width: 1
                border.color: tree.rootTone
                SIcon {
                    anchors.centerIn: parent
                    name: tree.rootIcon
                    size: Serp.px(10)
                    color: tree.rootTone
                }
            }
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: tree.rootClicked()
        }
    }
    // the root's name: at the foot of the tree (under the root it covered the lower branches)
    Rectangle {
        x: tree.cx - width / 2
        y: tree.height - height - Serp.px(6)
        z: 10
        width: rootText.implicitWidth + Serp.px(14)
        height: rootText.implicitHeight + Serp.px(6)
        radius: height / 2
        color: Qt.alpha(Serp.base, 0.85)
        opacity: tree.clamp(tree.grow * 3 - 0.5)
        SText {
            id: rootText
            anchors.centerIn: parent
            text: tree.rootLabel + (tree.rootSub ? " · " + tree.rootSub : "")
            size: Serp.px(9.5)
            bold: true
        }
    }

    // ---- what the pointer is over (beads have no names on the ring) ----
    Rectangle {
        id: tip
        readonly property var l: tree.hovered >= 0 ? tree.leaves[tree.hovered] : null
        readonly property var bg: tree.hoveredBranch >= 0 ? tree.groups[tree.hoveredBranch] : null
        readonly property string txt: l ? (l.item.num ? l.item.num + " · " : "") + (l.item.title || l.item.name) : bg ? bg.label + " · " + (bg.items || []).length : ""
        readonly property var at: l ? tree.pt(tree.leafAngle(tree.hovered), tree.leafR) : bg ? tree.pt(tree.branchAngle(tree.hoveredBranch), tree.branchR) : null
        visible: !!at && (!l || l.g !== tree.selIdx)
        z: 20
        width: tipText.implicitWidth + Serp.px(14)
        height: tipText.implicitHeight + Serp.px(8)
        radius: Serp.radiusSmall
        color: Serp.solid
        border.width: 1
        border.color: Serp.line
        x: at ? Math.max(0, Math.min(tree.width - width, at.x - width / 2)) : 0
        y: at ? Math.max(0, at.y - height - Serp.px(14)) : 0
        SText {
            id: tipText
            anchors.centerIn: parent
            text: tip.txt
            size: Serp.px(10.5)
            bold: true
        }
    }
}
