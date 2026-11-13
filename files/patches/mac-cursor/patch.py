#!/usr/bin/env python3
"""VM-патч angelOS: курсор Golden Gate — angelOS Mac Pixel (macOS-курсоры пиксель-артом 12x12,
~/vm-setup/cursor-mac), когда тема стоит; иначе как у автора (macOS / capitaine-cursors).

  patch.py apply | revert | check
"""
import sys
from pathlib import Path

F = Path.home() / ".config/quickshell/angelos/services/Cursors.qml"
OLD = '''    readonly property string macTheme: macInstalled ? "macOS" : "capitaine-cursors"'''
NEW = '''    readonly property string macTheme: other.includes("angelOS-MacPixel") ? "angelOS-MacPixel" : macInstalled ? "macOS" : "capitaine-cursors"  // vm-patch mac-cursor: свой пиксельный мак-курсор'''


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    s = F.read_text()
    if mode == "check":
        sys.exit(0 if NEW in s else 1)
    if mode == "revert":
        if NEW in s:
            F.write_text(s.replace(NEW, OLD, 1)); print("откат Cursors.qml"); print("changed-qml")
        return
    if NEW in s:
        print("уже стоит Cursors.qml")
    elif s.count(OLD) == 1:
        F.write_text(s.replace(OLD, NEW, 1)); print("поставлен Cursors.qml"); print("changed-qml")
    else:
        print("ВНИМАНИЕ: Cursors.qml у автора изменился, строка не найдена — не встал"); sys.exit(1)


if __name__ == "__main__":
    main()
