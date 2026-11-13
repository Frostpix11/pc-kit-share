#!/usr/bin/env python3
"""pc-kit patch halo-game-sleep (Celestia, 2026-11-03): over a full-screen game or film with nothing
to show (Settings → Halo → over full screen: nothing, or a timer not ringing) the Halo's overlay
window goes away. Measured: it redrew ~165 frames a second for nobody over CS2 (niri sync-trace),
an overlay niri had to mix into every game frame. Something to show (a timer's end) brings it back.

  apply.py | apply.py check | apply.py revert     (original kept as HaloWindow.qml.angelos-orig)
"""
import os, shutil, sys
from pathlib import Path

F = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos") / "modules/halo/HaloWindow.qml"
MARK = "celestia halo-game-sleep"
OLD = '    color: "transparent"\n    WlrLayershell.namespace: "angelos-halo"\n'
NEW = OLD + """    // celestia halo-game-sleep: over a full-screen game or film with nothing to show, no window at
    // all (it redrew 165 times a second for nobody); a timer's end brings it back at once
    visible: !(full && !shown)
"""

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    t = F.read_text()
    if mode == "check":
        sys.exit(0 if MARK in t else 1)
    o = F.with_name(F.name + ".angelos-orig")
    if mode == "revert":
        if o.exists(): shutil.copy2(o, F); print("reverted")
        return
    if MARK in t:
        print("already applied"); return
    if t.count(OLD) != 1:
        print("does not fit (author changed HaloWindow.qml?)"); sys.exit(2)
    shutil.copy2(F, o)   # the author's file as it is now (an update may have changed it)
    F.write_text(t.replace(OLD, NEW, 1)); print("applied")

if __name__ == "__main__":
    main()
