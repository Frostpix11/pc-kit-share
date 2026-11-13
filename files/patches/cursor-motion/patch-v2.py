#!/usr/bin/env python3
"""Патч angelOS «cursor-motion» v2 (2026-11-06): поверх кода автора.

С 2026-11-05 «Живой курсор» и «Камера за курсором» есть у автора (CursorShake, catalog/Cursor,
tree.json, Mod+Ctrl+Shift+U). Здесь только то, чего у него нет:
  · размер дробный, шаг 0.25, по умолчанию 1.5 (у автора целый, 2);
  · «Смаз в движении» и «Мягкость тени» (motionBlur, motionShadowSoft);
  · «Под бит» и «Сила прыжка» (motionBeat*, angel-niri CursorKick): курсор прыгает на бочку.
Наш блок Super+Ctrl+Shift+U из user.kdl снимается, когда сочетание есть у автора.

  patch.py apply | revert | check      печатает «changed-qml», если правился QML
"""
import subprocess
import sys
from pathlib import Path

SHELL = Path.home() / ".config/quickshell/angelos"
NIRI_CFG = Path.home() / ".config/niri/cfg"
USER_KDL = NIRI_CFG / "user.kdl"
M = "  // vm-patch cursor-motion"


def slider(ru, en, hint_ru, hint_en, key, lo, hi, step, default, present="Config.cursor.motion && CursorShake.ownMotion"):
    return f'''        CatSlider {{{M}
            present: {present}
            label: I18n.t("{ru}", "{en}")
            hint: I18n.t("{hint_ru}", "{hint_en}")
            from: {int(lo * 100)}
            to: {int(hi * 100)}
            stepSize: {int(step * 100)}
            value: Math.round((Config.cursor.{key} ?? {default}) * 100)
            suffix: "%"
            onMoved: v => Config.cursor.{key} = v / 100
        }}
'''


BLUR = slider("Смаз в движении", "Motion smear", "след за курсором на скорости", "the trail behind a fast pointer", "motionBlur", 0, 3, 0.1, 1)
SOFT = slider("Мягкость тени", "Shadow softness", "насколько размыты края", "how blurred its edges are", "motionShadowSoft", 0.2, 4, 0.1, 1)
BEAT = f'''        CatToggle {{{M}
            present: Config.cursor.motion && CursorShake.ownMotion
            label: I18n.t("Под бит", "On the beat")
            hint: !CursorShake.ownKick ? I18n.t("нужна сборка angel-niri с CursorKick (pc-kit, шаг niri)", "needs angel-niri with CursorKick (pc-kit, step niri)") : I18n.t("курсор подпрыгивает на каждую бочку играющей музыки — тот же слух, что качает окна и обои", "the pointer hops on every kick of the music playing — the same hearing that springs the windows and the wallpaper")
            enabled: CursorShake.ownKick
            checked: Config.cursor.motionBeat && CursorShake.ownKick
            onToggled: c => Config.cursor.motionBeat = c
        }}
'''
HOP = slider("Сила прыжка", "Hop height", "как высоко курсор подпрыгивает на бочку", "how high the pointer hops on a kick", "motionBeatPower", 0.3, 3, 0.1, 1,
             present="Config.cursor.motion && CursorShake.ownMotion && Config.cursor.motionBeat && CursorShake.ownKick")

KEY_OLD = "Config.cursor.motionSway, Config.cursor.motionBounce, Config.cursor.motionShadow, Config.cursor.motionShadowDist, Motion.still]"
KEY_NEW = "Config.cursor.motionSway, Config.cursor.motionBlur, Config.cursor.motionBounce, Config.cursor.motionShadow, Config.cursor.motionShadowDist, Config.cursor.motionShadowSoft, Motion.still]"

SUBS = [
    ("config/SettingsSchema.qml",
     "        property real motionSize: 2         // × the cursor size, whole numbers (pixels stay even)\n",
     "        property real motionSize: 1.5       // vm-patch cursor-motion: × the cursor size, in quarters\n"
     "        property real motionBlur: 1         // vm-patch cursor-motion: smear when fast (0–3)\n"
     "        property real motionShadowSoft: 1   // vm-patch cursor-motion: shadow softness (0.2–4)\n"
     "        property bool motionBeat: false     // vm-patch cursor-motion: the pointer hops on the music's kicks (angel-niri CursorKick)\n"
     "        property real motionBeatPower: 1    // vm-patch cursor-motion: how high it hops (0.3–3)\n"),
    ("services/CursorShake.qml", KEY_OLD, KEY_NEW),
    ("services/CursorShake.qml",
     '''                    "size": n(c.motionSize, 2),
                    "sway": n(c.motionSway, 1),
                    "bounce": n(c.motionBounce, 1),
                    "shadow": n(c.motionShadow, 1),
                    "shadow_dist": n(c.motionShadowDist, 1)
                }
            }
        }, (ok, err) => root.ownMotion = !err, true);
    }
''',
     '''                    "size": n(c.motionSize, 1.5),
                    "sway": n(c.motionSway, 1),
                    "blur": n(c.motionBlur, 1),
                    "bounce": n(c.motionBounce, 1),
                    "shadow": n(c.motionShadow, 1),
                    "shadow_dist": n(c.motionShadowDist, 1),
                    "shadow_soft": n(c.motionShadowSoft, 1)
                }
            }
        }, (ok, err) => root.ownMotion = !err, true);
        // vm-patch cursor-motion: the hop on the beat: strength 0 is the probe (an older angel-niri says Err)
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
'''),
    ("modules/settings/catalog/Cursor.qml",
     '''            stepSize: 1
            value: Math.round(Config.cursor.motionSize ?? 2)
''',
     '''            stepSize: 0.25
            decimals: 2
            value: Config.cursor.motionSize ?? 1.5
'''),
    ("modules/settings/catalog/Cursor.qml",
     '''        CatSlider {
            present: Config.cursor.motion && CursorShake.ownMotion
            label: I18n.t("Клик", "Click")
''',
     BLUR + '''        CatSlider {
            present: Config.cursor.motion && CursorShake.ownMotion
            label: I18n.t("Клик", "Click")
'''),
    ("modules/settings/catalog/Cursor.qml",
     '''            onMoved: v => Config.cursor.motionShadowDist = v / 100
        }
''',
     '''            onMoved: v => Config.cursor.motionShadowDist = v / 100
        }
''' + SOFT + BEAT + HOP),
    ("modules/settings/catalog/Cursor.qml",
     '''                        Config.cursor.motionSize = 2;
                        Config.cursor.motionSway = 1;
                        Config.cursor.motionBounce = 1;
                        Config.cursor.motionShadow = 1;
                        Config.cursor.motionShadowDist = 1;
''',
     '''                        Config.cursor.motionSize = 1.5;
                        Config.cursor.motionSway = 1;
                        Config.cursor.motionBlur = 1;
                        Config.cursor.motionBounce = 1;
                        Config.cursor.motionShadow = 1;
                        Config.cursor.motionShadowDist = 1;
                        Config.cursor.motionShadowSoft = 1;
                        Config.cursor.motionBeatPower = 1;
'''),
]


def drop_old_bind():
    """Наш блок из user.kdl больше не нужен, когда камера есть в сочетаниях автора.
    Блок ищем по меткам: в старых версиях патча текст внутри мог отличаться."""
    common = NIRI_CFG / "keybinds-common.kdl"
    if not USER_KDL.exists() or not common.exists() or "toggle-cursor-camera" not in common.read_text():
        return True
    s = USER_KDL.read_text()
    a = s.find("// vm-patch cursor-motion:")
    end = "// vm-patch cursor-motion end\n"
    b = s.find(end)
    if a < 0 or b < 0:
        return True
    USER_KDL.write_text(s[:a] + s[b + len(end):])
    niri = Path.home() / ".local/bin/niri"
    if niri.exists():
        r = subprocess.run([str(niri), "validate"], capture_output=True, text=True)
        if r.returncode != 0:
            USER_KDL.write_text(s)
            print("niri не принял user.kdl без нашего блока, оставила как было:", r.stderr.strip()[-300:])
            return False
    return True


def main(mode):
    ok = True
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
    if mode == "apply" and ok:
        ok = drop_old_bind()
    if changed:
        print("changed-qml")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
