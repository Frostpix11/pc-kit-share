#!/usr/bin/env python3
"""pc-kit patch tray-menu-fresh (Celestia, 2026-11-06): a tray menu asks the app afresh at each opening.

QsMenuOpener kept the menu held between openings, so Quickshell sent AboutToShow only the first
time. Apps that refresh their items on AboutToShow (Telegram's «Отключить / Включить уведомления»)
showed the old text until they were restarted. Letting go of the handle and taking it again at
opening (not at closing: a chosen item is triggered after the menu closes) makes every opening
work as the first: a new DBusMenu, AboutToShow, GetLayout; `settle` already waits for the items.
At closing the menu is let go too, on the next turn, so the tray's menu and a pinned icon's never
hold one app's menu between them.

Not temporary: the author's 89feddf has the same code, so this one stays after the update.

  apply.py | apply.py check | apply.py revert
"""
import os, sys
from pathlib import Path

F = Path(os.environ.get("ANGELOS_SHELL") or Path.home() / ".config/quickshell/angelos") / "modules/bar/TrayMenu.qml"
SUBS = [
    ('''        opening = true;
        openingSince = Date.now();
        settle.restart();
''',
     '''        opening = true;
        openingSince = Date.now();
        // celestia tray-menu-fresh: let go and take it again: AboutToShow goes out at every opening,
        // an app's items that change only then (Telegram's notifications) are not stale
        const held = handle;
        handle = null;
        handle = held;
        settle.restart();
'''),
    # the tray's menu and a pinned icon's are two: one left holding the app's menu would keep the
    # other's letting go from reaching it. A chosen item runs in close()'s turn, this is the next
    ('''            root.openers.forEach(o => o.destroy());
            root.openers = [];
''',
     '''            root.openers.forEach(o => o.destroy());
            root.openers = [];
            // celestia tray-menu-fresh: closed, the app's menu is held by nobody (a pinned icon has a TrayMenu of its own)
            if (!root.opening)
                root.handle = null;
'''),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    t = F.read_text()
    if mode == "check":
        sys.exit(0 if all(new in t for _, new in SUBS) else 1)
    if mode == "revert":
        for old, new in SUBS:
            t = t.replace(new, old, 1)
        F.write_text(t)
        print("reverted")
        return
    if all(new in t for _, new in SUBS):
        print("already applied")
        return
    for old, new in SUBS:
        if new not in t and t.count(old) != 1:
            print("does not fit (author changed TrayMenu.qml?)")
            sys.exit(2)
    for old, new in SUBS:
        if new not in t:
            t = t.replace(old, new, 1)
    F.write_text(t)
    print("applied")


if __name__ == "__main__":
    main()
