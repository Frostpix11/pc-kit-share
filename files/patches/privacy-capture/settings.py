#!/usr/bin/env python3
"""Патч angelOS «privacy-capture», часть «настройки»: галочка «Приватность в записи экрана».

Настройки → Скриншоты и запись → Запись экрана. Config.capture.recordPrivacy (по умолчанию да)
читает ~/.local/bin/niri-record-region (наш кусок rec/02): да — на рабочем столе wf-recorder
(окна, скрытые режимом приватности, закрыты и в записи), в полноэкранной игре gpu-screen-recorder,
рекордеры меняет rec-switch.py; нет — всё время gpu-screen-recorder, как у автора.

  settings.py apply | revert | check      печатает «changed-qml», если правился QML
"""

import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"
M = "  // kit-patch privacy"

SUBS = [
    ("config/SettingsSchema.qml",
     '''        property string recordCodec: "auto" // auto (NVENC on NVIDIA, else VA-API, else x264) | nvenc | vaapi | x264
''',
     '''        property string recordCodec: "auto" // auto (NVENC on NVIDIA, else VA-API, else x264) | nvenc | vaapi | x264
        property bool recordPrivacy: true   // kit-patch privacy: Win+Shift+R keeps privacy mode's windows hidden (wf-recorder on the desk, gpu-screen-recorder in a fullscreen game)
'''),
    ("modules/settings/catalog/Capture.qml",
     '''        // services/Capture: gpu-screen-recorder's replay buffer
        CatToggle {''',
     '''        // kit-patch privacy: Win+Shift+R and privacy mode (~/.local/share/angelos-kit/patches/privacy-capture)
        CatToggle {''' + M + '''
            label: I18n.t("Приватность в записи экрана", "Privacy mode in screen recording")
            hint: Config.capture.recordPrivacy !== false ? I18n.t("Win+Shift+R: окна, скрытые режимом приватности (Win+Shift+X), закрыты и в записи, его можно включать прямо во время записи. На рабочем столе пишет wf-recorder через композитор — около ядра процессора; в полноэкранной игре сам переключается на gpu-screen-recorder, игре почти бесплатно. При выходе из игры — миг стоп-кадра, чтобы скрытое не мелькнуло; в конце один файл. Выключи — запись всегда через gpu-screen-recorder, легче, но скрытые окна в ней видны", "Win+Shift+R: windows privacy mode hides (Win+Shift+X) stay hidden in the recording too, and it can be switched mid-recording. On the desk wf-recorder records through the compositor — about a CPU core; in a fullscreen game it switches to gpu-screen-recorder by itself, nearly free for the game. Leaving the game shows a moment's still frame so nothing hidden flashes by; one file at the end. Off — always gpu-screen-recorder, lighter, but hidden windows show in it") : I18n.t("Выключено: Win+Shift+R всегда пишет через gpu-screen-recorder — легче всего, но окна, скрытые режимом приватности, в записи видны. Включи — скрытые окна закрыты и в записи (рабочий стол через wf-recorder, игра через gpu-screen-recorder). Действует со следующей записи", "Off: Win+Shift+R always records through gpu-screen-recorder — lightest, but windows privacy mode hides do show in it. On — hidden windows stay hidden in the recording (the desk through wf-recorder, a game through gpu-screen-recorder). Takes effect from the next recording")
            checked: Config.capture.recordPrivacy !== false
            onToggled: v => Config.capture.recordPrivacy = v
        }
        // services/Capture: gpu-screen-recorder's replay buffer
        CatToggle {'''),
]


def main(mode: str) -> int:
    ok, changed = True, False
    for rel, old, new in SUBS:
        p = SHELL / rel
        if not p.exists():
            print(f"нет файла {rel}"); ok = False; continue
        s = p.read_text()
        if mode == "check":
            ok &= new in s
            continue
        if mode == "revert":
            if new in s:
                p.write_text(s.replace(new, old, 1)); changed = True
            continue
        if new in s:
            continue
        if s.count(old) != 1:
            print(f"ВНИМАНИЕ: {rel} у автора изменился — галочка «Приватность в записи экрана» не встала"); ok = False
            continue
        p.write_text(s.replace(old, new, 1)); changed = True
    if changed:
        print("настройки: " + ("откатил" if mode == "revert" else "применил"))
        print("changed-qml")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
