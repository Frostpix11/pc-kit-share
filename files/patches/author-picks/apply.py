#!/usr/bin/env python3
"""pc-kit patch author-picks (Celestia, 2026-11-06). ВРЕМЕННЫЙ: только до обновления angelOS.

The author's small fixes from 89feddf, word for word, taken early on acd9f1b:
  · wallpaper: the lens takes the bass on the scene's own tick (was ~80 frames a second under music)
  · wallpaper: night layers and the night light load only while the night shows
  · bar lyrics: the word's hop and fade in steps, not each frame of the monitor
  · session menu: the keys work in the Russian layout too (#165)

Once the author's code is there this patch does nothing: check says so, apply skips, revert leaves
his files alone; then delete this folder and its line in kit.py.

  apply.py | apply.py check | apply.py revert     (originals kept as <file>.angelos-orig)
"""
import os, shutil, sys
from pathlib import Path

SHELL = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos")
MARK = "celestia author-picks"

SUBS = [
    ("widgets/SceneDrums.qml",
     '''    Binding {
        target: root.wall
        property: "breath"
        value: root.hearsBreath ? Bass.dense * LyricsGlow.loud : 0
    }
''',
     '''    // celestia author-picks: the lens takes the bass on the scene's own tick (wall.time), not on each of Bass's lines:
    // two clocks made the wallpaper draw ~80 frames a second under music, not the scene's 24 (03.11)
    Connections {
        target: root.wall
        enabled: root.hearsBreath
        function onTimeChanged() {
            const v = Bass.dense * LyricsGlow.loud;
            if (v !== root.wall.breath)
                root.wall.breath = v;
        }
    }
    onHearsBreathChanged: if (!hearsBreath)
        wall.breath = 0
'''),
    ("widgets/SceneLayer.qml",
     '''    Repeater {
        id: nightFrames
        model: layer.ownNight ? layer.modelData.frames : []
''',
     '''    // celestia author-picks: loaded only while the night shows: by day they held a second copy of every layer (03.11)
    Repeater {
        id: nightFrames
        model: layer.ownNight && wall.nightMix > 0 ? layer.modelData.frames : []
'''),
    ("widgets/SceneWall.qml",
     '''        source: root.nightInfo && root.nightInfo.light ? "file://" + root.dir''',
     '''        source: root.nightInfo && root.nightInfo.light && root.nightMix > 0 ? "file://" + root.dir'''),
    ("modules/bar/parts/BarLyrics.qml",
     '''            x: cur.x + root.clipW
            anchors.verticalCenter: parent.verticalCenter
''',
     '''            x: cur.x + root.clipW
            anchors.verticalCenter: parent.verticalCenter
            // celestia author-picks: the hop in whole art pixels and the fade in tenths: the window draws a frame per
            // step, not each frame of the monitor for every word sung (03.11)
            property int hop: 0
            property int fade: 10
            anchors.verticalCenterOffset: hop * Theme.u
            opacity: fade / 10
'''),
    ("modules/bar/parts/BarLyrics.qml",
     '''                property: "opacity"
                from: 0.3
                to: 1
                duration: Motion.ms(90)
''',
     '''                property: "fade"
                from: 3
                to: 10
                duration: Motion.ms(90)
'''),
    ("modules/bar/parts/BarLyrics.qml",
     '''                property: "anchors.verticalCenterOffset"
                from: Theme.u * 3
                to: 0
                duration: Motion.ms(200)
''',
     '''                property: "hop"
                from: 3
                to: 0
                duration: Motion.ms(200)
'''),
    ("modules/session/SessionMenu.qml",
     '''                    const a = win.actions.find(a => a.key === e.text.toUpperCase());
''',
     '''                    // celestia author-picks: the same key in the Russian layout too (#165): «Д» is L, «Ы» is S…
                    const t = e.text.toUpperCase(), sw = SettingsSearch.swapLayout(e.text).toUpperCase();
                    const a = win.actions.find(a => a.key === t || a.key === sw);
'''),
]
FILES = sorted({rel for rel, _, _ in SUBS})


def author_has_it():
    t = (SHELL / "widgets/SceneDrums.qml").read_text()
    return "two clocks made the wallpaper" in t and MARK not in t


def on():
    return all(new in (SHELL / rel).read_text() for rel, _, new in SUBS)


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
    print("applied")


if __name__ == "__main__":
    main()
