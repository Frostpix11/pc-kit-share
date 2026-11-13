#!/usr/bin/env python3
"""VM-патч angelOS «mac-settings-lights»: в Golden Gate у окна Настроек нет второго ряда кнопок.

На angel-niri (Niri.nativeMinimize) angelOS сам рисует окну Настроек мак-полосу: светофор
(закрыть, свернуть, развернуть) и название. MacView рисовал ещё свой светофор вверху сайдбара —
выходил дубль. Теперь свой светофор прячется, пока полосу рисует angel-niri; без angel-niri
(обычный niri, полосы нет) он остаётся, чтобы окно не осталось без кнопок.

  patch.py apply | revert | check      печатает «changed-qml», если правился QML
"""
import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"
M = "  // vm-patch mac-settings-lights"

SUBS = [
    ("modules/settings/views/MacView.qml",
     '''        Row {
            id: lights
            x: GoldenGate.px(20)''',
     '''        Row {
            id: lights
            visible: !Niri.nativeMinimize''' + M + ''': angel-niri draws the title bar with its own lights
            x: GoldenGate.px(20)'''),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    files = {f for f, _, _ in SUBS}
    texts = {f: (SHELL / f).read_text() for f in files if (SHELL / f).exists()}
    missing = 0
    for f, old, new in (SUBS if mode != "revert" else list(reversed(SUBS))):
        s = texts.get(f)
        if s is None:
            print(f"нет файла {f}"); missing += 1; continue
        if mode == "revert":
            if new in s:
                texts[f] = s.replace(new, old, 1)
            continue
        if new in s:
            continue
        if s.count(old) == 1:
            if mode == "apply":
                texts[f] = s.replace(old, new, 1)
            else:
                missing += 1
        else:
            print(f"ВНИМАНИЕ: {f} у автора изменился, кусок не найден: {old.strip()[:70]}"); missing += 1
    if mode == "check":
        sys.exit(1 if missing else 0)
    changed = []
    for f, s in texts.items():
        p = SHELL / f
        if p.read_text() != s:
            p.write_text(s); changed.append(f)
    for f in changed:
        print(("откат " if mode == "revert" else "поставлен ") + f)
    if any(f.endswith(".qml") for f in changed):
        print("changed-qml")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
