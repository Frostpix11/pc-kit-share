#!/usr/bin/env python3
"""pc-kit patch tray-pin (Celestia, 2026-11-06): the author's #136 taken early, on angelOS acd9f1b.

Right click a tray icon → «На панель»: it stands on the bar by the tray's arrow, «Убрать с панели»
takes it back. Classic's bar only. The code is the author's from 89feddf, word for word; the pins
live in Config.bar.layout as "tray:<id>", his format, so they survive the update.

When the author's own code is there (BarLayout has pinTray without our mark) this patch does
nothing: check says so, apply skips, revert leaves his files alone.

  apply.py | apply.py check | apply.py revert     (originals kept as <file>.angelos-orig)
"""
import os, shutil, sys
from pathlib import Path

SHELL = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos")
HERE = Path(__file__).resolve().parent
MARK = "celestia tray-pin"
ICON = SHELL / "modules/bar/parts/TrayIcon.qml"

SUBS = [
    ("services/BarLayout.qml",
     "import Quickshell\nimport qs.config\n",
     "import Quickshell\nimport Quickshell.Services.SystemTray\nimport qs.config\n"),
    ("services/BarLayout.qml",
     '''    readonly property var hidden: (Config.bar.hidden || []).filter(id => valid(id))
''',
     '''    readonly property var hidden: (Config.bar.hidden || []).filter(id => valid(id))
    // celestia tray-pin: tray icons pinned to the bar (#136): "tray:<the app's StatusNotifier id>", there while the app runs
    readonly property var trayIds: SystemTray.items.values.map(t => "tray:" + t.id)
    function trayItem(id) {
        return SystemTray.items.values.find(t => "tray:" + t.id === id) || null;
    }
    function pinned(t) {
        return !!t && all.includes("tray:" + t.id);
    }
    // pin: next to the tray's arrow (the start of the right side without one); unpin: out of the layout
    function pinTray(t, on) {
        const id = "tray:" + t.id;
        if (!on) {
            const cfg = Config.bar.layout || {};
            const out = {};
            for (const s of sections)
                out[s] = (cfg[s] || effective[s]).filter(x => x !== id);
            Config.bar.layout = out;
            return;
        }
        for (const s of sections) {
            const at = effective[s].indexOf("tray");
            if (at >= 0)
                return move(id, s, at);
        }
        move(id, "right", 0);
    }
'''),
    ("services/BarLayout.qml",
     '''            return false;
        return id.startsWith("plugin:") ? pluginIds.includes(id) : !!meta[id];
    }
    function info(id) {
''',
     '''            return false;
        if (id.startsWith("tray:"))
            return trayIds.includes(id);
        return id.startsWith("plugin:") ? pluginIds.includes(id) : !!meta[id];
    }
    function info(id) {
        if (id.startsWith("tray:")) {
            const t = trayItem(id);
            return {
                "label": t ? (t.tooltipTitle || t.title || t.id) : id.slice(5),
                "icon": "layers"
            };
        }
'''),
    ("modules/bar/BarItem.qml",
     '''            return wid.startsWith("plugin:") ? pluginC : null;
''',
     '''            return wid.startsWith("plugin:") ? pluginC : wid.startsWith("tray:") ? trayIconC : null;
'''),
    ("modules/bar/BarItem.qml",
     '''    Component {
        id: layoutC
''',
     '''    Component {  // celestia tray-pin
        id: trayIconC
        TrayIcon {
            tray: BarLayout.trayItem(root.wid)
            above: root.bar.above
        }
    }
    Component {
        id: layoutC
'''),
    ("modules/bar/TrayMenu.qml",
     '''    property var handle: null
''',
     '''    property var handle: null
    // celestia tray-pin: the tray item itself: its menu ends with «На панель» / «Убрать с панели» (#136)
    property var tray: null
'''),
    ("modules/bar/TrayMenu.qml",
     '''        if (!handle)
            return;
        opening = true;
''',
     '''        if (!handle && !tray)
            return;
        opening = true;
'''),
    ("modules/bar/TrayMenu.qml",
     '''    items: entriesOf(opener.children)
''',
     '''    items: {
        const own = root.handle ? entriesOf(opener.children) : [];
        if (!root.tray)
            return own;
        const t = root.tray, on = BarLayout.pinned(t);
        return own.concat(own.length ? [{
                    "separator": true
                }] : [], [{
                    "label": on ? I18n.t("Убрать с панели", "Unpin from the bar") : I18n.t("На панель", "Pin to the bar"),
                    "run": () => BarLayout.pinTray(t, !on)
                }]);
    }
'''),
    ("modules/bar/parts/Tray.qml",
     '''    readonly property int rows: Math.ceil(SystemTray.items.values.length / columns)
''',
     '''    // celestia tray-pin: the ones pinned to the bar (BarLayout "tray:<id>") stand there, not here
    readonly property var loose: SystemTray.items.values.filter(t => !BarLayout.pinned(t))
    readonly property int rows: Math.ceil(loose.length / columns)
'''),
    ("modules/bar/parts/Tray.qml",
     '''                        model: SystemTray.items
''',
     '''                        model: root.loose
'''),
    ("modules/bar/parts/Tray.qml",
     '''                                        menu.handle = cell.modelData.hasMenu ? cell.modelData.menu : null;
                                        menu.toggle();
''',
     '''                                        menu.handle = cell.modelData.hasMenu ? cell.modelData.menu : null;
                                        menu.tray = cell.modelData;
                                        menu.toggle();
'''),
    ("modules/bar/parts/Tray.qml",
     '''                visible: SystemTray.items.values.length === 0
''',
     '''                visible: root.loose.length === 0
'''),
]
FILES = sorted({rel for rel, _, _ in SUBS})


def author_has_it():
    t = (SHELL / "services/BarLayout.qml").read_text()
    return "function pinTray" in t and MARK not in t


def on():
    return ICON.exists() and all(new in (SHELL / rel).read_text() for rel, _, new in SUBS)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if author_has_it():
        print("author has it now: nothing to do, this patch can go")
        sys.exit(0)
    if mode == "check":
        sys.exit(0 if on() else 1)
    if mode == "revert":
        for rel in FILES:
            o = SHELL / (rel + ".angelos-orig")
            if o.exists():
                shutil.copy2(o, SHELL / rel)
                o.unlink()
        if ICON.exists() and MARK in ICON.read_text():
            ICON.unlink()
        print("reverted")
        return
    if on():
        print("already applied")
        return
    # all or nothing: every piece must fit before a single file changes
    texts = {rel: (SHELL / rel).read_text() for rel in FILES}
    for rel, old, new in SUBS:
        if new not in texts[rel] and texts[rel].count(old) != 1:
            print(f"does not fit: {rel} (author changed it?)")
            sys.exit(2)
    for rel in FILES:
        shutil.copy2(SHELL / rel, SHELL / (rel + ".angelos-orig"))
    for rel, old, new in SUBS:
        if new not in texts[rel]:
            texts[rel] = texts[rel].replace(old, new, 1)
    for rel in FILES:
        (SHELL / rel).write_text(texts[rel])
    shutil.copy2(HERE / "TrayIcon.qml", ICON)
    print("applied")


if __name__ == "__main__":
    main()
