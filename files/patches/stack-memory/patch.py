#!/usr/bin/env python3
"""VM-патч angelOS «stack-memory»: Лента ↔ Desktop (стекинг angel-niri) помнит каждую сторону.

Новый файл services/StackMemory.qml (из files/) + кусок в WindowConfig.setFloatAll (и Ipc.stacking
отвечает, куда идёт переключение, а не старый режим): в Classic
переключение режима идёт через StackMemory.run (свёрнутые/открытые окна как были на той
стороне, места окон в Desktop, фокус). Плагин skin-morph зовёт
StackMemory сам при Classic (Лента) ↔ Golden Gate.

  patch.py apply | revert | check      печатает «changed-qml», если правился QML
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHELL = Path.home() / ".config/quickshell/angelos"
M = "  // vm-patch stack-memory"
NEW = ["services/StackMemory.qml"]

SUBS = [
    ("services/WindowConfig.qml",
     '''        if (Config.windows.floatAll === on)
            return;
        Config.windows.floatAll = on;
''',
     '''        if (Config.windows.floatAll === on)
            return;
        if (Niri.nativeMinimize && typeof StackMemory !== "undefined") {''' + M + ''': each side's windows come back as they were
            StackMemory.run(on ? "strip" : "desk", on ? "desk" : "strip", () => {
                if (Config.windows.floatAll === on)
                    return;
                Config.windows.floatAll = on;
                root.modeFlipped(on, false);
                Sounds.play(on ? "desktopOn" : "desktopOff");
            }, null);
            return;
        }
        Config.windows.floatAll = on;
'''),
    ("modules/Ipc.qml",
     '''        return WindowConfig.floatAll ? "on" : "off";
''',
     '''        return (typeof StackMemory !== "undefined" && StackMemory.heading) || (WindowConfig.floatAll ? "on" : "off");''' + M + ''': the switch waits for the windows
'''),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    missing = 0
    changed = []
    for f in NEW:
        dst, src = SHELL / f, HERE / "files" / f
        if mode == "revert":
            if dst.exists():
                dst.unlink(); changed.append(f)
        elif not dst.exists() or dst.read_text() != src.read_text():
            if mode == "apply":
                dst.write_text(src.read_text()); changed.append(f)
            else:
                missing += 1
    files = {f for f, _, _ in SUBS}
    texts = {f: (SHELL / f).read_text() for f in files if (SHELL / f).exists()}
    for f, old, new in SUBS:
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
