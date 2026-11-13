#!/usr/bin/env python3
"""Патч angelOS «cursor-motion»: «Живой курсор» и «Камера за курсором» в настройках.

Курсор рисует angel-niri с cursor_fx (сборка ce52b4a8-vm-fx / kit): наклон в движении, смаз на
скорости, пружина и кольцо при клике, тень, размер. Шелл хранит настройки в Config.cursor.motion*
и шлёт их композитору (Niri.request SetCursorFx) — при старте и при каждом изменении. Без такой
сборки niri отвечает ошибкой: переключатель серый с подсказкой.

Камера за курсором (angel-niri camera.rs): Super+Ctrl+Shift+U приближает экран к курсору и плавно
ведёт за ним (пружина, безопасная зона, размытие в движении), ещё раз — назад. Настройки
Config.cursor.camera* (разрешить, приближение, плавность, размытие) → SetCursorCamera; сочетание —
блок в ~/.config/niri/cfg/user.kdl (файл пользователя, обновления его не трогают).

  Classic:      Настройки → Курсор → «Живой курсор», «Камера за курсором»
  Golden Gate:  Настройки → Клавиатура и мышь → Курсор (свой пункт; туда же ведёт «cursor»)

  patch.py apply | revert | check      печатает «changed-qml», если правился QML
"""
import subprocess
import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"
USER_KDL = Path.home() / ".config/niri/cfg/user.kdl"
BIND = """// vm-patch cursor-motion: камера за курсором (Настройки → Курсор); снимается patch.py revert
binds {
    Super+Ctrl+Shift+U repeat=false hotkey-overlay-title="Камера за курсором: приблизить / назад" { spawn-sh "exec \\"$HOME/.local/bin/niri\\" msg action toggle-cursor-camera"; }
}
// vm-patch cursor-motion end
"""
M = "  // vm-patch cursor-motion"


def slider(label_ru, label_en, hint_ru, hint_en, key, lo, hi, step, default, pct=True):
    if pct:
        val = f"Math.round((Config.cursor.{key} ?? {default}) * 100)"
        moved = f"v => Config.cursor.{key} = v / 100"
        rng = f"from: {int(lo * 100)}\n            to: {int(hi * 100)}\n            stepSize: {int(step * 100)}"
        suffix = '"%"'
    else:
        val = f"Config.cursor.{key} ?? {default}"
        moved = f"v => Config.cursor.{key} = v"
        rng = f"from: {lo}\n            to: {hi}\n            stepSize: {step}\n            decimals: 2"
        suffix = '"×"'
    return f'''        CatSlider {{{M}
            present: Config.cursor.motion && CursorShake.ownMotion
            label: I18n.t("{label_ru}", "{label_en}")
            hint: I18n.t("{hint_ru}", "{hint_en}")
            {rng}
            value: {val}
            suffix: {suffix}
            onMoved: {moved}
        }}
'''


GROUP = f'''    // vm-patch cursor-motion: the living pointer drawn by angel-niri (cursor_fx) — any cursor theme,
    // Classic and Golden Gate alike (services/CursorShake sends it to the compositor)
    CatGroup {{
        name: "motion"
        title: I18n.t("Живой курсор", "Motion cursor")
        icon: "sparkle"
        CatToggle {{{M}
            label: I18n.t("Живой курсор", "Motion cursor")
            hint: !CursorShake.ownMotion ? I18n.t("нужна сборка angel-niri с cursor_fx (pc-kit, шаг niri)", "needs angel-niri with cursor_fx (pc-kit, step niri)") : Motion.still ? I18n.t("сейчас выключен: в «Движении» стоит «без анимаций»", "off for now: Motion is set to no animation") : I18n.t("курсор наклоняется в движении, смазывается на скорости, пружинит при клике с кольцом и парит над тенью — с любой темой курсора", "the pointer leans as it moves, smears when fast, springs on a click with a ring and floats over its shadow — with any cursor theme")
            enabled: CursorShake.ownMotion
            checked: Config.cursor.motion && CursorShake.ownMotion
            onToggled: c => Config.cursor.motion = c
        }}
{slider("Размер", "Size", "во сколько раз больше обычного", "how many times bigger than usual", "motionSize", 1, 3, 0.25, 1.5, pct=False)}{slider("Наклон", "Lean", "как сильно курсор наклоняется по ходу движения", "how far the pointer leans into its motion", "motionSway", 0, 3, 0.1, 1)}{slider("Смаз в движении", "Motion smear", "след за курсором на скорости", "the trail behind a fast pointer", "motionBlur", 0, 3, 0.1, 1)}{slider("Клик", "Click", "пружина и кольцо при нажатии; 0 — без них", "the dip and ring on a click; 0 — none", "motionBounce", 0, 3, 0.1, 1)}{slider("Тень", "Shadow", "насколько тёмная; 0 — без тени", "how dark; 0 — no shadow", "motionShadow", 0, 3, 0.1, 1)}{slider("Дальность тени", "Shadow distance", "как далеко она падает — как высоко парит курсор", "how far it falls — how high the pointer floats", "motionShadowDist", 0, 3, 0.1, 1)}{slider("Мягкость тени", "Shadow softness", "насколько размыты края", "how blurred its edges are", "motionShadowSoft", 0.2, 4, 0.1, 1)}        CatToggle {{{M}
            present: Config.cursor.motion && CursorShake.ownMotion
            label: I18n.t("Под бит", "On the beat")
            hint: !CursorShake.ownKick ? I18n.t("нужна сборка angel-niri с CursorKick (pc-kit, шаг niri)", "needs angel-niri with CursorKick (pc-kit, step niri)") : I18n.t("курсор подпрыгивает на каждую бочку играющей музыки — тот же слух, что качает окна и обои", "the pointer hops on every kick of the music playing — the same hearing that springs the windows and the wallpaper")
            enabled: CursorShake.ownKick
            checked: Config.cursor.motionBeat && CursorShake.ownKick
            onToggled: c => Config.cursor.motionBeat = c
        }}
{slider("Сила прыжка", "Hop height", "как высоко курсор подпрыгивает на бочку", "how high the pointer hops on a kick", "motionBeatPower", 0.3, 3, 0.1, 1).replace("Config.cursor.motion && CursorShake.ownMotion", "Config.cursor.motion && CursorShake.ownMotion && Config.cursor.motionBeat && CursorShake.ownKick")}        CatCustom {{{M}
            wide: true
            present: Config.cursor.motion && CursorShake.ownMotion
            CatBox {{
                PxButton {{
                    compact: true
                    icon: "refresh"
                    text: I18n.t("Как было по умолчанию", "Back to defaults")
                    onClicked: {{
                        Config.cursor.motionSize = 1.5;
                        Config.cursor.motionSway = 1;
                        Config.cursor.motionBlur = 1;
                        Config.cursor.motionBounce = 1;
                        Config.cursor.motionShadow = 1;
                        Config.cursor.motionShadowDist = 1;
                        Config.cursor.motionShadowSoft = 1;
                        Config.cursor.motionBeatPower = 1;
                    }}
                }}
            }}
        }}
    }}
    // vm-patch cursor-motion: the camera that follows the pointer (angel-niri camera.rs)
    CatGroup {{
        name: "camera"
        title: I18n.t("Камера за курсором", "Camera follows the pointer")
        icon: "search"
        CatToggle {{{M}
            label: I18n.t("Камера за курсором", "Follow the pointer")
            hint: !CursorShake.ownCamera ? I18n.t("нужна сборка angel-niri с камерой (pc-kit, шаг niri)", "needs angel-niri with the camera (pc-kit, step niri)") : I18n.t("Super + Ctrl + Shift + U — экран приближается к курсору и плавно едет за ним, смазываясь в движении; ещё раз — назад. Курсор, клики и окна работают как обычно.", "Super + Ctrl + Shift + U — the screen zooms in on the pointer and glides after it, smearing as it moves; again — back out. The pointer, clicks and windows work as usual.")
            enabled: CursorShake.ownCamera
            checked: Config.cursor.camera && CursorShake.ownCamera
            onToggled: c => Config.cursor.camera = c
        }}
        CatSlider {{{M}
            present: Config.cursor.camera && CursorShake.ownCamera
            label: I18n.t("Приближение", "Zoom")
            hint: I18n.t("во сколько раз крупнее", "how many times closer")
            from: 1.25
            to: 3.5
            stepSize: 0.05
            decimals: 2
            value: Config.cursor.cameraZoom ?? 1.8
            suffix: "×"
            onMoved: v => Config.cursor.cameraZoom = v
        }}
{slider("Плавность", "Smoothness", "как мягко камера догоняет курсор", "how softly the camera catches up", "cameraSmooth", 0.3, 3, 0.1, 1).replace("Config.cursor.motion && CursorShake.ownMotion", "Config.cursor.camera && CursorShake.ownCamera")}{slider("Размытие в движении", "Motion blur", "смаз экрана на быстром проезде и при приближении; 0 — без него", "the screen smears on a fast pan and while zooming; 0 — none", "cameraBlur", 0, 3, 0.1, 1).replace("Config.cursor.motion && CursorShake.ownMotion", "Config.cursor.camera && CursorShake.ownCamera")}        CatCustom {{{M}
            wide: true
            present: Config.cursor.camera && CursorShake.ownCamera
            CatBox {{
                PxButton {{
                    compact: true
                    icon: "sparkle"
                    text: I18n.t("Приблизить / назад", "Zoom in / back")
                    onClicked: CursorShake.cameraToggle()
                }}
            }}
        }}
    }}
    CatGroup {{
        name: "shake-find-pointer"'''

SUBS = [
    ("config/SettingsSchema.qml",
     '''        property string beforeMac: ""       // the cursor the Golden Gate skin's arrow replaced (services/Cursors)
    }''',
     '''        property string beforeMac: ""       // the cursor the Golden Gate skin's arrow replaced (services/Cursors)
        property bool motion: true          // vm-patch cursor-motion: the living pointer (angel-niri cursor_fx), any theme
        property real motionSize: 1.5       // vm-patch cursor-motion: × the cursor size
        property real motionSway: 1         // vm-patch cursor-motion: lean into motion (0–3)
        property real motionBlur: 1         // vm-patch cursor-motion: smear when fast (0–3)
        property real motionBounce: 1       // vm-patch cursor-motion: click dip + ring (0–3)
        property real motionShadow: 1       // vm-patch cursor-motion: shadow darkness (0–3)
        property real motionShadowDist: 1   // vm-patch cursor-motion: how far the shadow falls (0–3)
        property real motionShadowSoft: 1   // vm-patch cursor-motion: shadow softness (0.2–4)
        property bool camera: true          // vm-patch cursor-motion: Super+Ctrl+Shift+U zooms in and follows the pointer (angel-niri camera.rs)
        property real cameraZoom: 1.8       // vm-patch cursor-motion: × (1.25–3.5)
        property real cameraSmooth: 1       // vm-patch cursor-motion: how slowly it glides (0.3–3)
        property real cameraBlur: 1         // vm-patch cursor-motion: smear of pans and zoom (0–3)
        property bool motionBeat: false     // vm-patch cursor-motion: the pointer hops on the music's kicks (angel-niri CursorKick)
        property real motionBeatPower: 1    // vm-patch cursor-motion: how high it hops (0.3–3)
    }'''),
    ("services/CursorShake.qml",
     '''    // the arrow of the current theme, again when the theme changes
    readonly property string theme: Cursors.active || "default"''',
     '''    // vm-patch cursor-motion: the living pointer — angel-niri (cursor_fx) draws it, whatever the
    // theme; these settings go to it at start and on every change. Stock niri says Err: ownMotion
    // stays false and Settings greys the switch out
    property bool ownMotion: false
    readonly property string motionKey: Config.ready ? [Config.cursor.motion, Config.cursor.motionSize, Config.cursor.motionSway, Config.cursor.motionBlur, Config.cursor.motionBounce, Config.cursor.motionShadow, Config.cursor.motionShadowDist, Config.cursor.motionShadowSoft, Motion.still].join("|") : ""
    onMotionKeyChanged: motionApply.restart()
    function _motion() {
        if (!Config.ready)
            return;
        const c = Config.cursor;
        const n = (v, d) => (typeof v === "number" && isFinite(v)) ? v : d;
        Niri.request({
            "Action": {
                "SetCursorFx": {
                    "on": !!c.motion && !Motion.still,
                    "size": n(c.motionSize, 1.5),
                    "sway": n(c.motionSway, 1),
                    "blur": n(c.motionBlur, 1),
                    "bounce": n(c.motionBounce, 1),
                    "shadow": n(c.motionShadow, 1),
                    "shadow_dist": n(c.motionShadowDist, 1),
                    "shadow_soft": n(c.motionShadowSoft, 1)
                }
            }
        }, (ok, err) => root.ownMotion = !err, true);
        // the hop on the beat: strength 0 is the probe (an older angel-niri says Err)
        Niri.request({
            "Action": {
                "CursorKick": {
                    "strength": 0
                }
            }
        }, (ok, err) => root.ownKick = !err, true);
    }
    // vm-patch cursor-motion: the pointer hops on the music's kicks (angel-niri CursorKick), with
    // the drum hearing that springs the windows (services/Bass); off by default. Bass runs while
    // someone listens: this counts itself in with the layered wallpapers' counter
    property bool ownKick: false
    readonly property bool beatOn: ownKick && Config.ready && !!Config.cursor.motion && !Motion.still && Config.cursor.motionBeat === true
    property bool _beatListening: false
    onBeatOnChanged: {
        if (beatOn === _beatListening)
            return;
        _beatListening = beatOn;
        Bass.walls += beatOn ? 1 : -1;
    }
    Connections {''' + M + '''
        target: Bass
        enabled: root.beatOn && Lyrics.isSong
        function onKicked() {
            const c = Config.cursor;
            const p = (typeof c.motionBeatPower === "number" && isFinite(c.motionBeatPower)) ? c.motionBeatPower : 1;
            // a light kick lower, a hard one higher; the song's first kicks a step more
            Niri.action("CursorKick", {
                "strength": p * (0.6 + 0.4 * Bass.punch) * (Bass.hype > 0.5 ? 1.3 : 1)
            });
        }
    }
    Timer {''' + M + '''
        id: motionApply
        interval: 80
        running: true
        onTriggered: root._motion()
    }
    // vm-patch cursor-motion: the camera that follows the pointer (angel-niri camera.rs) —
    // allowed or not and how; Super+Ctrl+Shift+U (user.kdl) or cameraToggle() moves it in and out
    property bool ownCamera: false
    readonly property string cameraKey: Config.ready ? [Config.cursor.camera, Config.cursor.cameraZoom, Config.cursor.cameraSmooth, Config.cursor.cameraBlur].join("|") : ""
    onCameraKeyChanged: cameraApply.restart()
    function _camera() {
        if (!Config.ready)
            return;
        const c = Config.cursor;
        const n = (v, d) => (typeof v === "number" && isFinite(v)) ? v : d;
        Niri.request({
            "Action": {
                "SetCursorCamera": {
                    "allowed": !!c.camera,
                    "zoom": n(c.cameraZoom, 1.8),
                    "smooth": n(c.cameraSmooth, 1),
                    "blur": n(c.cameraBlur, 1)
                }
            }
        }, (ok, err) => root.ownCamera = !err, true);
    }
    function cameraToggle() {
        Niri.request({
            "Action": {
                "ToggleCursorCamera": {}
            }
        }, null, true);
    }
    Timer {''' + M + '''
        id: cameraApply
        interval: 80
        running: true
        onTriggered: root._camera()
    }

    // the arrow of the current theme, again when the theme changes
    readonly property string theme: Cursors.active || "default"'''),
    ("modules/settings/catalog/Cursor.qml",
     '''    CatGroup {
        name: "shake-find-pointer"''', GROUP),
    # Classic: Personalisation → Cursor
    ("modules/settings/tree.json",
     '''          "blocks": [
            "cursor/pixel-themes",
            "cursor/size-compatibility"
          ],''',
     '''          "blocks": [
            "cursor/pixel-themes",
            "cursor/motion",
            "cursor/camera",
            "cursor/size-compatibility"
          ],'''),
    # Golden Gate: its own page after Mouse
    ("modules/settings/tree.json",
     '''            "blocks": [
              "mouse/mouse",
              "mouse/@"
            ],
            "more": [
              "cursor/size-compatibility"
            ]
          },''',
     '''            "blocks": [
              "mouse/mouse",
              "mouse/@"
            ],
            "more": [
              "cursor/size-compatibility"
            ]
          },
          {
            "id": "mac-cursor",
            "ru": "Курсор",
            "en": "Pointer",
            "icon": "cursor",
            "hintRu": "живой курсор и камера за курсором",
            "hintEn": "motion cursor and the camera that follows it",
            "blocks": [
              "cursor/motion",
              "cursor/camera"
            ],
            "more": [
              "cursor/size-compatibility",
              "cursor/shake-find-pointer"
            ]
          },'''),
    ("modules/settings/tree.json",
     '''      "cursor": {
        "page": "mac-mouse"
      },''',
     '''      "cursor": {
        "page": "mac-cursor"
      },'''),
]


def kdl(mode):
    """The key in user.kdl: added / taken out / there? A config niri rejects is put back."""
    s = USER_KDL.read_text() if USER_KDL.exists() else ""
    if mode == "check":
        return BIND in s
    if mode == "apply" and BIND not in s:
        new = s + ("" if s.endswith("\n") or not s else "\n") + BIND
    elif mode == "revert" and BIND in s:
        new = s.replace(BIND, "")
    else:
        return True
    USER_KDL.parent.mkdir(parents=True, exist_ok=True)
    USER_KDL.write_text(new)
    niri = Path.home() / ".local/bin/niri"
    if niri.exists():
        r = subprocess.run([str(niri), "validate"], capture_output=True, text=True)
        if r.returncode != 0:
            USER_KDL.write_text(s)
            print("niri не принял сочетание, user.kdl как было:", r.stderr.strip()[-300:])
            return False
    return True


def main(mode):
    ok = kdl(mode)
    changed = False
    for rel, old, new in SUBS:
        p = SHELL / rel
        s = p.read_text()
        if mode == "check":
            if new not in s:
                ok = False
            continue
        if mode == "apply":
            if new in s:
                continue
            if s.count(old) != 1:
                print(f"не нашёл место в {rel}"); ok = False; continue
            p.write_text(s.replace(old, new)); changed = True
        else:
            if new not in s:
                continue
            p.write_text(s.replace(new, old)); changed = True
    if changed:
        print("changed-qml")
    return 0 if ok else 1


def author_took_it():
    """С 2026-11-05 курсор есть у автора: этот патч на его коде встал бы частями и шелл не загрузился
    бы (Duplicate property name). Тогда работает patch-v2.py, только наши отличия."""
    return "motion: true          // the living pointer" in (SHELL / "config/SettingsSchema.qml").read_text()


if __name__ == "__main__":
    if author_took_it():
        sys.exit(subprocess.call([sys.executable, str(Path(__file__).with_name("patch-v2.py")), *sys.argv[1:]]))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
