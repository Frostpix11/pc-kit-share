#!/usr/bin/env python3
"""Build the night scene using the author's exact pixel geometry.

The masks retain hidden surfaces, attachment points and animation overscan.
No source files are modified. Run after the image_gen atlas outputs are saved.
"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "art/original-day"
DEST = ROOT / "plugin/scenes"
SIZE = (656, 376)


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def connected_components(mask):
    labels = np.zeros(mask.shape, dtype=np.int32)
    count = 0
    for y, x in zip(*np.where(mask)):
        if labels[y, x]:
            continue
        count += 1
        labels[y, x] = count
        stack = [(y, x)]
        while stack:
            cy, cx = stack.pop()
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not labels[ny, nx]:
                    labels[ny, nx] = count
                    stack.append((ny, nx))
    return labels, count


def build():
    DEST.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, DEST / "day", dirs_exist_ok=True)
    night = DEST / "night"
    shutil.copytree(SOURCE, night, dirs_exist_ok=True)
    scene = json.loads((SOURCE / "scene.json").read_text())
    old_palette = json.loads((SOURCE / "palette.json").read_text())["rgb"]
    palette_spec = json.loads((ROOT / "art/night-palette.json").read_text())
    new_palette = palette_spec["rgb"]
    assert len(old_palette) == len(new_palette) == 48
    for layer in scene["layers"]:
        original = np.array(Image.open(SOURCE / "logical" / layer["file"]).convert("RGBA"))
        pixels = original.copy()
        layer_palette = list(new_palette)
        if layer["id"] in ("03_city", "06_balcony", "07_room", "18_chair"):
            layer_palette[23:31] = palette_spec["moonlit_surfaces"]
        elif layer["id"] in ("09_dresser", "12_desk"):
            layer_palette[28:31] = palette_spec["desk_highlights"]
        for old, new in zip(old_palette, layer_palette):
            pixels[np.all(original[:, :, :3] == old, axis=2), :3] = new
        # Windows already have distinct teal pixels in the author's architecture.
        # Light a sparse, deterministic subset of those exact connected shapes.
        if layer["id"] == "03_city":
            window_mask = np.zeros(original.shape[:2], dtype=bool)
            for color in old_palette[19:23]:
                window_mask |= np.all(original[:, :, :3] == color, axis=2)
            components, count = connected_components(window_mask)
            warm = [[67,40,51], [130,80,62], [199,137,79], [241,194,119]]
            for component in range(1, count + 1):
                area = components == component
                ys, xs = np.where(area)
                if not 2 <= len(xs) <= 45 or xs.max() - xs.min() > 10 or ys.max() - ys.min() > 12:
                    continue
                if (int(xs.min()) * 13 + int(ys.min()) * 7) % 7 > 2:
                    continue
                for old, new in zip(old_palette[19:23], warm):
                    pixels[area & np.all(original[:, :, :3] == old, axis=2), :3] = new
        Image.fromarray(pixels).save(night / "logical" / layer["file"])

    # Final extracted image_gen cutouts are the reproducible source assets.
    # Large intermediate atlases are not needed to build the finished plugin.
    shutil.copy2(ROOT / "art/sources/stars.png", night / "logical/layers/stars.png")
    scene["layers"].append({"id":"stars", "label_ru":"Звёзды", "file":"layers/stars.png",
        "z":11, "visible":True, "parallax_max_logical":[0,0], "edge_mode":"transparent",
        "bounds_logical":[0,0,656,376], "animation":{"type":"none"}})

    sprite = Image.open(ROOT / "art/sources/seraph.png").convert("RGBA")
    frames_dir = night / "logical/effects/seraph"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    # A slow three-pixel breathing/hover loop. The wallpaper engine plays these
    # frames and pauses them with the rest of the scene (fullscreen / still).
    offsets = [0, 0, 0, -1, -1, -1, -1, 0, 0, 0, 1, 1, 1, 1, 0, 0]
    for i, offset in enumerate(offsets):
        frame = Image.new("RGBA", SIZE)
        frame.paste(sprite, (264, 29 + offset))
        rel = f"effects/seraph/{i:02}.png"
        frame.save(night / "logical" / rel)
        frames.append(rel)
    scene["layers"].append({
        "id": "seraph", "label_ru": "Серафим за окном", "file": frames[0],
        "z": 27, "visible": True, "parallax_max_logical": [0.3, 0],
        "edge_mode": "transparent", "bounds_logical": [263, 27, 301, 66],
        "animation": {"type": "frame_sequence", "frames": frames, "fps": 2, "loop": True}
    })
    scene["title"] = "AngelOS 2004 — Лунная комната"
    dump(night / "scene.json", scene)
    neutral = Image.new("RGBA", SIZE)
    for layer in sorted(scene["layers"], key=lambda item: item["z"]):
        neutral.alpha_composite(Image.open(night / "logical" / layer["file"]).convert("RGBA"))
    neutral.convert("RGB").save(night / scene["neutral_pose"]["reference"])
    dump(night / "palette.json", {"rgb": new_palette})
    neutral.convert("RGB").resize((1312, 752), Image.Resampling.NEAREST).save(ROOT / "art/night-composite.png")
    print(f"Built {len(scene['layers'])} night layers, {len(frames)} seraph frames in {DEST}")


if __name__ == "__main__":
    build()
