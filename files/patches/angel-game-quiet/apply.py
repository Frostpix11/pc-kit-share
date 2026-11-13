#!/usr/bin/env python3
"""pc-kit patch angel-game-quiet (Celestia, 2026-11-03): while a game fills the angel's screen
(Shell.gaming and her screen fullscreen) she says nothing (the line is let go, like the shell's
other sounds over a fullscreen window) and her typing voice is muted (a line already running when
the game starts). Alt-tabbed out (her screen not covered) she talks as before.

  apply.py | apply.py check | apply.py revert     (originals kept as <file>.angelos-orig)
"""
import os, shutil, sys
from pathlib import Path

SHELL = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos")
MARK = "celestia angel-game-quiet"
EDITS = {
    "services/Angel.qml": [(
"""    function say(msg, acts, ms, silent) {
        if (!shown || !msg)
            return;
""",
"""    function say(msg, acts, ms, silent) {
        if (!shown || !msg)
            return;
        // celestia angel-game-quiet: a game fills her screen, nobody reads or hears her: let it go
        if (Shell.gaming && Shell.fullscreenOn(screenName))
            return;
""")],
    "modules/y2k/AngelHelper.qml": [(
"""                    readonly property bool on: Sounds.enabled("voice") && !StreamMode.quiet && Sounds.ready
""",
"""                    // celestia angel-game-quiet: no pips while a game fills her screen
                    readonly property bool on: Sounds.enabled("voice") && !StreamMode.quiet && Sounds.ready && !(Shell.gaming && Shell.fullscreenOn(Angel.screenName))
""")],
}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    files = {rel: SHELL / rel for rel in EDITS}
    applied = all(MARK in f.read_text() for f in files.values())
    if mode == "check":
        sys.exit(0 if applied else 1)
    if mode == "revert":
        for f in files.values():
            o = f.with_name(f.name + ".angelos-orig")
            if o.exists():
                shutil.copy2(o, f)
        print("reverted"); return
    if applied:
        print("already applied"); return
    texts = {rel: f.read_text() for rel, f in files.items()}
    for rel, pairs in EDITS.items():
        for old, _ in pairs:
            if texts[rel].count(old) != 1:
                print(f"does not fit {rel} (author changed it?):\n{old[:160]}"); sys.exit(2)
    for rel, pairs in EDITS.items():
        f = files[rel]
        o = f.with_name(f.name + ".angelos-orig")
        shutil.copy2(f, o)   # the author's file as it is now (an update may have changed it)
        t = texts[rel]
        for old, new in pairs:
            t = t.replace(old, new, 1)
        f.write_text(t)
    print("applied")


if __name__ == "__main__":
    main()
