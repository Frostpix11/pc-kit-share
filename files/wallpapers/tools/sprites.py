#!/usr/bin/env python3
"""Sprites of «Тихая гавань» (Celestia): frame sequences drawn in the scene's own art pixels.
    sprites.py <scene dir>   -> logical/{glow,smoke,glints}/NN.png + layers in scene.json
glow    the cabin window and the pier lantern, warm amber, a soft flicker, their reflections
        rippling a pixel sideways (role "light": kept at night; the music rings out of the window by the modifiers)
smoke   puffs from the chimney, growing, drifting right, thinning out by dither
glints  short light streaks on the open water, each with its own beat
Seeded: a run gives the same frames.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

SCENE = Path(sys.argv[1]).expanduser().resolve()
LOG = SCENE / "logical"
scene = json.loads((SCENE / "scene.json").read_text())
art = np.asarray(Image.open(LOG / "background.png").convert("RGB")).astype(int)
H, W = art.shape[:2]
rng = np.random.default_rng(1113)


def hexc(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def save(dirname, frames):
    (LOG / dirname).mkdir(parents=True, exist_ok=True)
    names = []
    for i, f in enumerate(frames):
        n = f"{dirname}/{i:02d}.png"
        Image.fromarray(f.astype(np.uint8), "RGBA").save(LOG / n, optimize=True)
        names.append(n)
    return names


def bounds(frames):
    a = np.zeros((H, W), bool)
    for f in frames:
        a |= f[..., 3] > 0
    ys, xs = np.nonzero(a)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def blank():
    return np.zeros((H, W, 4), int)


def put(f, x, y, c, a=255):
    if 0 <= x < W and 0 <= y < H:
        f[y, x] = [*c, a]


# ---- glow: window + lantern ----
AMBER = [hexc(c) for c in ("#ffe7b0", "#ffd38a", "#f6b56a", "#e8925a")]   # light → deep
REFL = [hexc(c) for c in ("#f3c99a", "#e3a979", "#c98a6c")]


def lit(x0, y0, x1, y1, thr):
    """the glass of a lamp in the day picture (luminance ≥ thr): its panes, not its frame"""
    box = art[y0:y1, x0:x1] @ np.array([0.3, 0.59, 0.11])
    return [(x0 + x, y0 + y) for y, x in zip(*np.nonzero(box >= thr))]


window = lit(274, 116, 280, 123, 200)
lantern = lit(197, 121, 200, 125, 215)
wrefl = lit(274, 154, 280, 161, 200)
lrefl = lit(196, 153, 200, 158, 210)
GLOW_N = 8
glow, lamp = [], []
for i in range(GLOW_N):
    f, g = blank(), blank()
    flick = [0, 0, 1, 0, 0, 1, 1, 0][i]                    # the flame dips now and then
    for (x, y) in window:
        k = min(3, (0 if y in (116, 120) else 1) + flick + ((x * 3 + y + i) % 7 == 0))
        put(f, x, y, AMBER[k])
    for (x, y) in lantern:
        k = min(3, (abs(x - 198) + abs(y - 122)) // 2 + [0, 1, 0, 0, 1, 0, 0, 0][i])
        put(g, x, y, AMBER[k])
    # reflections: every other row slides a pixel with the ripple, dimmer, broken up
    for pts in (wrefl, lrefl):
        for (x, y) in pts:
            dx = int(round(math.sin((y * 1.7) + i * math.pi / 4)))
            if (y + i) % 3 == 0:          # a dark water line runs through the reflection
                continue
            put(g, x + dx, y, REFL[min(2, (y - 153) // 3)])
    glow.append(f)
    lamp.append(g)

# ---- smoke ----
SMOKE = [hexc(c) for c in ("#f3eefa", "#d9d2ea", "#b9b1d2")]
SMOKE_N = 24
smoke = []
for i in range(SMOKE_N):
    f = blank()
    for p in range(5):                                       # five puffs in the air at once
        life = ((i / SMOKE_N) + p / 5) % 1.0
        cx = 297.5 + life * 6 + math.sin(life * 6 + p) * 1.2
        cy = 84.3 - life * 32   # born just over the cap (its top row is 86)
        r = 1.3 + life * 3.2
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(x - cx, (y - cy) * 1.15)
                if d > r:
                    continue
                # thinning: an ordered dither that eats the puff as it ages
                bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]][y % 4][x % 4] / 16
                if bayer < max(0.0, life - 0.35) ** 1.3 * 1.6:
                    continue
                shade = 0 if (y < cy - r * 0.15 and d < r * 0.8) else (2 if y > cy + r * 0.35 else 1)
                put(f, x, y, SMOKE[shade])
    smoke.append(f)

# ---- glints on the open water ----
GLINT = [hexc(c) for c in ("#f4f1ff", "#d9defa")]
GLINT_N = 16
water = []
for _ in range(400):
    x, y = int(rng.integers(40, 250)), int(rng.integers(124, 176))
    r, g, b = art[y, x]
    if b > r and b > 150 and not (185 <= x <= 245 and y < 150):   # open water, off the pier
        water.append((x, y))
spots = []
for x, y in water:
    if all(abs(x - sx) > 12 or abs(y - sy) > 5 for sx, sy, *_ in spots):
        spots.append((x, y, int(rng.integers(0, GLINT_N)), int(rng.integers(2, 5))))
    if len(spots) == 9:
        break
glints = []
for i in range(GLINT_N):
    f = blank()
    for (x, y, ph, ln) in spots:
        age = (i - ph) % GLINT_N
        if age > 3:
            continue
        n = [ln - 1, ln, ln - 1, 1][age]
        c = GLINT[0 if age in (1,) else 1]
        for k in range(max(1, n)):
            put(f, x + k - n // 2, y, c)
    glints.append(f)

layers = [l for l in scene["layers"] if l["id"] not in ("glow", "lamp", "smoke", "glints")]
for lid, frames, fps, z, role, label in (
        ("glints", glints, 4, 4, "effect", "Блики"),
        ("smoke", smoke, 6, 5, "effect", "Дым"),
        ("lamp", lamp, 2.5, 6, "light", "Фонарь и отражения"),
        ("glow", glow, 2.5, 7, "light", "Окно")):
    names = save(lid, frames)
    layers.append({
        "id": lid, "file": names[0], "z": z, "role": role, "visible": True,
        "parallax_max_logical": [0, 0], "edge_mode": "transparent",
        "bounds_logical": bounds(frames),
        "animation": {"type": "frame_sequence", "fps": fps, "frames": names},
        "label_ru": label,
    })
scene["layers"] = layers
(SCENE / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({l["id"]: l["bounds_logical"] for l in layers}))
