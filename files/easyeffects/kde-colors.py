#!/usr/bin/env python3
"""angelOS palette (qt6ct colors/angelos.conf, written by angelOS's qt-theme.py) -> a KDE
color scheme ~/.local/share/color-schemes/angelOS.colors. Kirigami apps (EasyEffects) take their
colours from a KDE scheme, not from qt6ct; with none installed they fall back to light Breeze.

  kde-colors.py [APP]   also make APP (its ~/.config/APPrc) use the scheme
"""
import configparser
import sys
from pathlib import Path

HOME = Path.home()
SRC = HOME / ".config/qt6ct/colors/angelos.conf"
DST = HOME / ".local/share/color-schemes/angelOS.colors"
# QPalette roles in qt6ct's order
ROLES = ["WindowText", "Button", "Light", "Midlight", "Dark", "Mid", "Text", "BrightText",
         "ButtonText", "Base", "Window", "Shadow", "Highlight", "HighlightedText", "Link",
         "LinkVisited", "AlternateBase", "NoRole", "ToolTipBase", "ToolTipText",
         "PlaceholderText", "Accent"]


def rgb(h):
    h = h.strip().lstrip("#")[-6:]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def s(c):
    return ",".join(map(str, c))


def main():
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(SRC)
    act = dict(zip(ROLES, map(rgb, cp["ColorScheme"]["active_colors"].split(","))))
    dis = dict(zip(ROLES, map(rgb, cp["ColorScheme"]["disabled_colors"].split(","))))
    accent = act["Highlight"]
    neg, neu, pos = (237, 102, 120), (232, 180, 90), (110, 200, 140)

    def group(bg, alt, fg):
        return {
            "BackgroundNormal": s(bg), "BackgroundAlternate": s(alt),
            "ForegroundNormal": s(fg), "ForegroundInactive": s(act["PlaceholderText"]),
            "ForegroundActive": s(accent), "ForegroundLink": s(act["Link"]),
            "ForegroundVisited": s(act["LinkVisited"]), "ForegroundNegative": s(neg),
            "ForegroundNeutral": s(neu), "ForegroundPositive": s(pos),
            "DecorationFocus": s(accent), "DecorationHover": s(mix(accent, (255, 255, 255), .2)),
        }

    out = configparser.ConfigParser(interpolation=None)
    out.optionxform = str
    out["General"] = {"ColorScheme": "angelOS", "Name": "angelOS"}
    out["KDE"] = {"contrast": "4"}
    out["Colors:Window"] = group(act["Window"], act["AlternateBase"], act["WindowText"])
    out["Colors:View"] = group(act["Base"], act["AlternateBase"], act["Text"])
    out["Colors:Button"] = group(act["Button"], act["Midlight"], act["ButtonText"])
    out["Colors:Selection"] = group(accent, mix(accent, act["Base"], .3), act["HighlightedText"])
    out["Colors:Tooltip"] = group(act["ToolTipBase"], act["AlternateBase"], act["ToolTipText"])
    out["Colors:Complementary"] = group(act["Dark"], act["Window"], act["WindowText"])
    out["Colors:Header"] = group(act["Dark"], act["Window"], act["WindowText"])
    out["ColorEffects:Disabled"] = {"Color": s(dis["Text"]), "ColorAmount": "0", "ColorEffect": "0",
                                    "ContrastAmount": "0.65", "ContrastEffect": "1",
                                    "IntensityAmount": "0.1", "IntensityEffect": "2"}
    out["ColorEffects:Inactive"] = {"ChangeSelectionColor": "false", "Enable": "false"}
    out["WM"] = {"activeBackground": s(act["Dark"]), "activeForeground": s(act["WindowText"]),
                 "inactiveBackground": s(act["Window"]),
                 "inactiveForeground": s(act["PlaceholderText"])}
    DST.parent.mkdir(parents=True, exist_ok=True)
    with open(DST, "w") as f:
        out.write(f, space_around_delimiters=False)

    if len(sys.argv) > 1:
        # where KColorSchemeManager (autosave) keeps the app's choice
        rc = HOME / ".config" / (sys.argv[1] + "rc")
        app = configparser.ConfigParser(interpolation=None, strict=False)
        app.optionxform = str
        app.read(rc)
        if not app.has_section("UiSettings"):
            app.add_section("UiSettings")
        app["UiSettings"]["ColorScheme"] = "angelOS"
        with open(rc, "w") as f:
            app.write(f, space_around_delimiters=False)


if __name__ == "__main__":
    main()
