#!/usr/bin/env python3
"""The night of a Celestia scene (after the author's scripts/scene-night.py, without the event).
    night-bake.py <scene dir> <night picture, cleaned to the scene's art size>
-> logical/masks/sky.png (the open sky, if missing), logical/night/<every frame of every layer>,
   night/neutral-656x376.png, night/palette.json; scene.json gets "night" (no event, no light).
Each day colour takes the night picture's median where the day shows it (so day and night share
every edge and the dusk can flow between them); layers kept as they are: role screen / light
(the window and the lantern glow the same). The moon is the night picture's own, laid into the
night background (the day has none). Stars: single art pixels in the open sky, seeded.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

SCENE = Path(sys.argv[1]).expanduser().resolve()
NIGHT = Path(sys.argv[2]).expanduser().resolve()
LOGICAL = SCENE / "logical"
OUT = LOGICAL / "night"
COLOURS = 80
STARS = 40
scene = json.loads((SCENE / "scene.json").read_text())


def rgba(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.float64)


M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])


def to_lab(rgb):
    c = rgb / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return np.cbrt(lin @ M1.T) @ M2.T


def from_lab(lab):
    lin = np.clip(((lab @ np.linalg.inv(M2).T) ** 3) @ np.linalg.inv(M1).T, 0, 1)
    return 255 * np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


day = rgba(SCENE / scene["neutral_pose"]["reference"])[..., :3]
night = rgba(NIGHT)[..., :3]
if day.shape != night.shape:
    sys.exit(f"night {night.shape[1]}x{night.shape[0]} != scene {day.shape[1]}x{day.shape[0]}")
h, w = day.shape[:2]

# ---- the open sky: light colours connected to the top edge, above the far ridges ----
sky_path = LOGICAL / "masks/sky.png"
if not sky_path.exists():
    # the far ridges are as light and as lavender as the haze over them, no colour tells them
    # apart: the silhouette is traced by hand (art px, «Тихая гавань»), and in front of it the
    # pines (dark) are taken out
    RIDGE = [(0, 86), (60, 87), (75, 85), (100, 84), (120, 83), (140, 80), (160, 77), (170, 75),
             (183, 74), (190, 75), (200, 77), (210, 80), (220, 81), (235, 83), (250, 84), (260, 81),
             (270, 80), (280, 79), (300, 77), (320, 76)]
    rx, ry = zip(*RIDGE)
    ridge = np.interp(np.arange(w), rx, ry)
    lum = to_lab(day)[..., 0]
    sky = (np.arange(h)[:, None] < ridge[None, :]) & (lum > 0.68)
    sky_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((sky * 255).astype(np.uint8)).save(sky_path)
sky = np.asarray(Image.open(sky_path).convert("L")) / 255.0

keep_ids = [l["id"] for l in scene["layers"] if l.get("role") in ("screen", "light")]

# ---- colour: the night picture's median for each day colour ----
def key(rgb):
    rgb = rgb.astype(np.int64)
    return rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]


dk = key(day)
known, known_night = [], []
for c in np.unique(dk):
    m = dk == c
    known.append(c)
    known_night.append(np.median(night[m], axis=0))
known = np.array(known)
known_rgb = np.stack([(known >> 16) & 255, (known >> 8) & 255, known & 255], -1).astype(np.float64)
known_night = np.array(known_night)
kl = to_lab(known_rgb)


def recolour(rgb):
    cols, inv = np.unique(rgb.reshape(-1, 3), axis=0, return_inverse=True)
    d = ((to_lab(cols)[:, None, :] - kl[None]) ** 2).sum(-1)
    return known_night[d.argmin(1)][inv.reshape(-1)].reshape(rgb.shape)


base = recolour(day)
uniq = np.unique(base.clip(0, 255).astype(np.uint8).reshape(-1, 3), axis=0)
pal_img = Image.fromarray(uniq[None]).quantize(COLOURS, method=Image.Quantize.MEDIANCUT)


def snap(rgb):
    return np.asarray(Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).quantize(palette=pal_img, dither=Image.Dither.NONE).convert("RGB"))


# ---- the moon: the night picture's brightest warm-white blob high in the sky ----
nl = to_lab(night)
moon = (nl[..., 0] > 0.78) & (np.arange(h)[:, None] < h * 0.3)
ys, xs = np.nonzero(moon)
moon_box = None
if len(xs):
    # the biggest cluster: take the median spot and everything bright within 8 px of it
    cy, cx = int(np.median(ys)), int(np.median(xs))
    y0, y1, x0, x1 = max(0, cy - 8), min(h, cy + 9), max(0, cx - 8), min(w, cx + 9)
    moon_box = (x0, y0, x1, y1)


def frames_of(layer):
    a = layer.get("animation", {})
    return a["frames"] if a.get("type") == "frame_sequence" else [layer["file"]]


OUT.mkdir(parents=True, exist_ok=True)
done = []
for layer in scene["layers"]:
    if layer["id"] in keep_ids:
        continue
    for f in frames_of(layer):
        src = rgba(LOGICAL / f)
        a = src[..., 3]
        rgb = snap(recolour(src[..., :3])).astype(np.float64)
        if layer.get("role") == "background" and moon_box:
            x0, y0, x1, y1 = moon_box
            # the moon and the glow right round it, as the night picture draws it
            region = nl[y0:y1, x0:x1, 0] > nl[..., 0][sky > 0.5].mean() + 0.12
            sub = rgb[y0:y1, x0:x1]
            sub[region] = night[y0:y1, x0:x1][region]
        out = np.dstack([rgb, a]).astype(np.uint8)
        out[a == 0] = 0
        dst = OUT / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(out, "RGBA").save(dst, optimize=True)
        done.append(f)

stack = np.zeros((h, w, 3))
for layer in sorted(scene["layers"], key=lambda l: l["z"]):
    f = frames_of(layer)[0]
    im = rgba((LOGICAL / f) if layer["id"] in keep_ids else (OUT / f))
    m = im[..., 3:] / 255.0
    stack = stack * (1 - m) + im[..., :3] * m
Image.fromarray(stack.astype(np.uint8)).save(OUT / "neutral-656x376.png", optimize=True)
pal = np.array(pal_img.getpalette()[:COLOURS * 3]).reshape(-1, 3)
(OUT / "palette.json").write_text(json.dumps({"rgb": sorted(map(list, {tuple(int(v) for v in c) for c in pal}))}) + "\n")

# ---- stars, as the author's: in the open sky, off its edges, seeded, every fifth bright ----
rng = np.random.default_rng(1113)
open_sky = sky > 0.5
for _ in range(2):
    open_sky = open_sky & np.roll(open_sky, 1, 0) & np.roll(open_sky, -1, 0) & np.roll(open_sky, 1, 1) & np.roll(open_sky, -1, 1)
if moon_box:
    x0, y0, x1, y1 = moon_box
    open_sky[max(0, y0 - 4):y1 + 4, max(0, x0 - 4):x1 + 4] = False
# only the clear sky, not the clouds (warm in the day picture: pink, peach, white) — no star in front of a cloud
dl = to_lab(day)
clear = (dl[..., 2] < -0.035) & (dl[..., 1] < 0.03)
for _ in range(2):
    clear = clear & np.roll(clear, 1, 0) & np.roll(clear, -1, 0) & np.roll(clear, 1, 1) & np.roll(clear, -1, 1)
open_sky &= clear
rows = np.nonzero(sky.max(1) > 0.5)[0]
horizon = rows.max() + 1 if rows.size else h // 2
ys, xs = np.nonzero(open_sky & (np.arange(h)[:, None] < horizon * 0.85))
faint, bright = (from_lab(np.array([Lv, -0.01, -0.04])).round() for Lv in (0.66, 0.92))
stars = []
for i in rng.permutation(len(xs))[:STARS * 8]:
    if len(stars) == STARS:
        break
    x, y = int(xs[i]), int(ys[i])
    if all(abs(x - sx) + abs(y - sy) > 7 for sx, sy, *_ in stars):
        stars.append([x, y, 1 if len(stars) % 5 == 0 else 0, round(float(rng.uniform(0.35, 0.95)), 2)])

kept = {k: v for k, v in (scene.get("night") or {}).items() if k in ("depth_text",)}
scene["night"] = kept | {
    "layers": "night/",
    "keep": keep_ids,
    "neutral": "logical/night/neutral-656x376.png",
    "palette": "night/palette.json",
    "stars": {"z": 2, "faint": [int(v) for v in faint], "bright": [int(v) for v in bright], "at": stars},
}
(SCENE / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"frames": len(done), "keep": keep_ids, "moon": moon_box, "stars": len(stars), "horizon": int(horizon)}))
