#!/usr/bin/env python3
"""pc-kit patch halo-game-notify (Celestia, 2026-11-11): notifications over a full-screen game.
Settings → Halo → «Over a full-screen game» gets a third choice, «A timer's end and notifications»
(value "notify"): a notification shows in the Halo for its usual 3.5 s and goes, and its sound plays
(y2k.quietFullscreen keeps every other shell sound quiet in the game). Over a full screen the Halo
takes no clicks/hover then (but for a ringing timer or the stream's chat), so the pill can't be held
by a stray pointer and never sits in the game's top-centre. halo-game-sleep removes the window again
once it is empty.
Also fixes the author's "timer" choice: it took notifications in a game (no corner card) but never
showed them; now only "notify" takes them, the others leave them to the bell as intended.
No *.angelos-orig: HaloWindow.qml carries halo-game-sleep too, revert puts back the exact text.
  apply.py | apply.py check | apply.py revert
"""
import os, sys
from pathlib import Path

S = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos")
M = "celestia halo-game-notify"
PATCH = {
    "services/Halo.qml": [
        ('''    readonly property bool takesNotifications: Config.ready && !!Config.halo.enabled && Config.halo.notify !== false && !hidden && !(gameOn && Config.halo.overFullscreen !== "timer")
''',
         '''    // celestia halo-game-notify: over a game only when asked ("notify"); "timer" took them and showed nothing
    readonly property bool takesNotifications: Config.ready && !!Config.halo.enabled && Config.halo.notify !== false && !hidden && !(gameOn && Config.halo.overFullscreen !== "notify")
'''),
    ],
    "modules/halo/HaloWindow.qml": [
        ('''    readonly property var baseItems: (full ? Halo.items.filter(i => Config.halo.overFullscreen === "timer" && i.kind === "ring" || i.kind === "chat" && StreamMode.onAir) : Halo.items).filter(i => !i.only || i.only === modelData.name)
''',
         '''    // celestia halo-game-notify: "notify" = a timer's end and notifications
    readonly property var baseItems: (full ? Halo.items.filter(i => ["timer", "notify"].includes(Config.halo.overFullscreen) && i.kind === "ring" || Config.halo.overFullscreen === "notify" && i.kind === "notif" || i.kind === "chat" && StreamMode.onAir) : Halo.items).filter(i => !i.only || i.only === modelData.name)
'''),
        ('''    mask: Region {
        item: win.shown ? hit : win.dodging ? peekZone : null
''',
         '''    mask: Region {
        // celestia halo-game-notify: over a full screen a notification takes no pointer (the game keeps it, nothing holds the pill)
        item: win.shown && !(win.full && !win.items.some(i => i.kind === "ring" || i.kind === "chat")) ? hit : win.dodging ? peekZone : null
'''),
    ],
    "modules/settings/catalog/Halo.qml": [
        ('''                {
                    label: I18n.t("Только конец таймера", "A timer's end only"),
                    value: "timer"
                }
            ]
            currentValue: Config.halo.overFullscreen
''',
         '''                {
                    label: I18n.t("Только конец таймера", "A timer's end only"),
                    value: "timer"
                },
                // celestia halo-game-notify
                {
                    label: I18n.t("Таймер и уведомления (со звуком)", "A timer's end and notifications (with sound)"),
                    value: "notify"
                }
            ]
            currentValue: Config.halo.overFullscreen
'''),
    ],
    "services/Sounds.qml": [
        ('''        if (!inGame.includes(name) && Config.y2k.quietFullscreen && fullscreenNow())
            return;
''',
         '''        // celestia halo-game-notify: a notification's sound plays in the game when the Halo shows it there
        if (!inGame.includes(name) && !(name === "notify" && Config.halo.overFullscreen === "notify") && Config.y2k.quietFullscreen && fullscreenNow())
            return;
'''),
    ],
}

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    texts = {f: (S / f).read_text() for f in PATCH}
    on = all(new in texts[f] for f, subs in PATCH.items() for _, new in subs)
    if mode == "check":
        sys.exit(0 if on else 1)
    if mode == "revert":
        for f, subs in PATCH.items():
            t = texts[f]
            for old, new in subs:
                t = t.replace(new, old, 1)
            if t != texts[f]:
                (S / f).write_text(t)
        print("reverted"); return
    if on:
        print("already applied"); return
    for f, subs in PATCH.items():
        for old, new in subs:
            if new not in texts[f] and texts[f].count(old) != 1:
                print(f"does not fit (author changed {f}?)"); sys.exit(2)
    for f, subs in PATCH.items():
        t = texts[f]
        for old, new in subs:
            if new not in t:
                t = t.replace(old, new, 1)
        if t != texts[f]:
            (S / f).write_text(t)
    print("applied")

if __name__ == "__main__":
    main()
