#!/usr/bin/env python3
"""pc-kit patch scene-handover (Celestia, 2026-11-13): a layered scene takes over from its still only
once every layer's picture has loaded.

WallpaperView draws a scene's still (its neutral frame) until SceneWall "covers"; covers was true as
soon as scene.json was read, while the layers' pictures were still loading (asynchronous) — for a
moment nothing was drawn: a black flash at every login with a scene wallpaper, in any skin (seen
at the end of serp's boot show «Пробуждение», which opens onto the desktop just then).
Now: each SceneLayer says whether what it draws now has loaded (the day's frame, and the night's
or the dusk's while they show); SceneWall notes the scene folder once all have; covers waits for it.

  apply.py | apply.py check | apply.py revert     (revert puts back only these pieces: other
                                                   patches share WallpaperView and the scene files)
"""
import os, sys
from pathlib import Path

SHELL = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos")
MARK = "pc-kit scene-handover"

SUBS = [
    ("widgets/SceneLayer.qml",
     "    readonly property var anim: modelData.animation || ({})\n",
     "    readonly property var anim: modelData.animation || ({})\n"
     "    // pc-kit scene-handover: what this layer draws now has loaded (the day's frame, the night's\n"
     "    // or the dusk's while they show): SceneWall covers the still only once all layers have\n"
     "    readonly property bool loadedNow: {\n"
     "        const f = layer.frame;\n"
     "        const ok = r => r.count > f && !!r.itemAt(f) && r.itemAt(f).status === Image.Ready;\n"
     "        if (!ok(frames))\n"
     "            return false;\n"
     "        if (layer.ownNight && wall.nightMix > 0 && !ok(nightFrames))\n"
     "            return false;\n"
     "        return !layer.ownTwilight || ok(twilightFrames);\n"
     "    }\n"),
    ("widgets/SceneWall.qml",
     "    Repeater {\n        model: root.layers\n\n        SceneLayer {\n            wall: root\n        }\n    }",
     "    // pc-kit scene-handover: every layer's picture has loaded; noted per scene folder, so a later\n"
     "    // hour's frames loading don't hand the screen back to the still\n"
     "    readonly property bool layersLoaded: layerItems.count > 0 && layerItems.count === layers.length\n"
     "        && Array.from({ length: layerItems.count }, (_, i) => layerItems.itemAt(i)).every(l => !!l && l.loadedNow)\n"
     "    property string loadedFor: \"\"\n"
     "    onLayersLoadedChanged: if (layersLoaded)\n"
     "        loadedFor = dir\n"
     "    readonly property bool loadedOnce: dir !== \"\" && loadedFor === dir\n"
     "    Repeater {\n        id: layerItems\n        model: root.layers\n\n        SceneLayer {\n            wall: root\n        }\n    }"),
    ("modules/background/WallpaperView.qml",
     "            readonly property bool covers: visible && scene !== null\n",
     "            readonly property bool covers: visible && scene !== null && loadedOnce  // pc-kit scene-handover: once its layers have loaded\n"),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    texts = {rel: (SHELL / rel).read_text() for rel, _, _ in SUBS}
    on = all(new in texts[rel] for rel, _, new in SUBS)
    if mode == "check":
        sys.exit(0 if on else 1)
    if mode == "revert":
        for rel, old, new in SUBS:
            texts[rel] = texts[rel].replace(new, old, 1)
        for rel in texts:
            (SHELL / rel).write_text(texts[rel])
        print("reverted")
        return
    if on:
        print("already applied")
        return
    for rel, old, new in SUBS:   # all or nothing
        if new not in texts[rel] and texts[rel].count(old) != 1:
            print(f"does not fit: {rel} (author changed it?)")
            sys.exit(2)
    for rel, old, new in SUBS:
        if new not in texts[rel]:
            texts[rel] = texts[rel].replace(old, new, 1)
    for rel in texts:
        (SHELL / rel).write_text(texts[rel])
    print("applied")


if __name__ == "__main__":
    main()
