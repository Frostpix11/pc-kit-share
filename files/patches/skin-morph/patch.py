#!/usr/bin/env python3
"""VM-патч angelOS «skin-morph»: переключение Classic ↔ Golden Gate идёт через плагин skin-morph.

Плагину нужно снять экран в старой теме ДО переключения, поэтому три места, где тема
меняется (карточка темы в Настройках, мастер первого запуска, `angelos settingsSkin`),
зовут GoldenGate.setSkin(s) вместо Config.settingsUi.skin = s. setSkin отдаёт переключение
плагину (GoldenGate.morphHandler), а без плагина просто ставит тему, как раньше.

  patch.py apply | revert | check      печатает «changed-qml», если правился QML
"""
import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"
M = "  // vm-patch skin-morph"

SUBS = [
    ("services/GoldenGate.qml",
     '''    readonly property bool on: chosen
''',
     '''    readonly property bool on: chosen
    property var morphHandler: null''' + M + ''': the skin-morph plugin animates Classic <-> Golden Gate
    function setSkin(s) {''' + M + '''
        if (morphHandler && morphHandler.morph(s))
            return;
        Config.settingsUi.skin = s;
    }
'''),
    ("widgets/SettingsSkinCard.qml",
     '''import QtQuick
import qs.config
''',
     '''import QtQuick
import qs.config
import qs.services''' + M + '''
'''),
    ("widgets/SettingsSkinCard.qml",
     '''            Config.settingsUi.skin = root.skin;
''',
     '''            GoldenGate.setSkin(root.skin);''' + M + '''
'''),
    ("modules/settings/SetupAssistant.qml",
     '''        Config.settingsUi.skin = mac ? "goldengate" : "classic";
''',
     '''        GoldenGate.setSkin(mac ? "goldengate" : "classic");''' + M + '''
'''),
    ("modules/Ipc.qml",
     '''        Config.settingsUi.skin = s;
        Config.settingsUi.skinChosen = true;
''',
     '''        GoldenGate.setSkin(s);''' + M + '''
        Config.settingsUi.skinChosen = true;
'''),
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
