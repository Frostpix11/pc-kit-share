#!/usr/bin/env python3
"""angelOS Mac Pixel — Golden Gate's cursor: macOS's cursors (after ful1e5/apple_cursor, GPL-3.0)
redrawn by hand as compact pixel art (designs.py) on the 12x12 grid of angelOS Pixel: 2/3/4 screen pixels
a cell at sizes 24/36/48. A soft macOS-like drop shadow one cell down-right. The arrow wears a small golden halo.

  build.py sheet OUT.png        preview of every cursor (all frames of the animated ones)
  build.py theme DIR            the Xcursor theme: cursors/ (+ the source's link names), index.theme
"""
import os
import sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import xc  # noqa: E402
from designs import BADGE, D, PAL, small_ball, waiting  # noqa: E402

SRC = HERE / "src/macOS/cursors"           # only for the link names
GRID, SIZES, SHADOW = 12, (24, 36, 48), (0, 0, 0, 72)
FRAMES, DELAY = 8, 90

def grid(rows, pal=PAL, w=GRID, h=GRID):
    if isinstance(rows, str):
        rows = [r for r in rows.strip("\n").split("\n")]
    w, h = max(w, max(len(r) for r in rows)), max(h, len(rows))
    im = Image.new("RGBA", (w, h))
    for y, row in enumerate(rows[:h]):
        for x, ch in enumerate(row[:w]):
            if ch in pal:
                im.putpixel((x, y), pal[ch] + (255,))
    return im


def tf(im, hot, op):
    x, y = hot
    if op == "mirror":
        return im.transpose(Image.FLIP_LEFT_RIGHT), (GRID - 1 - x, y)
    if op == "flip":
        return im.transpose(Image.FLIP_TOP_BOTTOM), (x, GRID - 1 - y)
    if op == "transpose":
        return im.transpose(Image.TRANSPOSE), (y, x)
    return im, hot


def base(name, op=None):
    rows, hot = D[name]
    im = grid(rows)
    return tf(im, hot, op) if op else (im, hot)


def badge(kind, frame=0):
    """small arrow + a 5x5 badge at its foot (macOS's copy/alias/help…); progress: the small ball"""
    im, hot = base("small")
    rows = small_ball(frame, FRAMES) if kind == "ball" else BADGE[kind]
    im.alpha_composite(grid(rows, PAL, 5, 5), (5, 5))
    return im, hot


def zoom(sign):
    im, hot = base("zoom")
    for c in [(2, 3), (3, 3), (4, 3)] + ([(3, 2), (3, 4)] if sign == "+" else []):
        im.putpixel(c, PAL["k"] + (255,))
    return im, hot


def anim(fn):
    return lambda: [fn(f) for f in range(FRAMES)]


def wait(f):
    rows, hot = waiting(f, FRAMES)
    return grid(rows), hot


TIP = {"left_ptr", "wayland-cursor", "right_ptr", "copy", "dnd_no_drop", "link", "question_arrow",
       "context-menu", "left_ptr_watch", "pencil"}
CURSORS = {
    "left_ptr": lambda: [base("haloed")], "wayland-cursor": lambda: [base("haloed")],
    "right_ptr": lambda: [base("arrow", "mirror")],
    "center_ptr": lambda: [base("up")],
    "hand2": lambda: [base("hand")], "hand1": lambda: [base("open")], "move": lambda: [base("closed")],
    "all-scroll": lambda: [base("move")],
    "xterm": lambda: [base("ibeam")], "vertical-text": lambda: [base("ibeam", "transpose")],
    "cross": lambda: [base("cross")], "crosshair": lambda: [base("cross")], "plus": lambda: [base("plus")],
    "crossed_circle": lambda: [base("nope")], "X_cursor": lambda: [base("X")], "dotbox": lambda: [base("dotbox")],
    "pencil": lambda: [base("pencil")],
    "zoom-in": lambda: [zoom("+")], "zoom-out": lambda: [zoom("-")],
    "copy": lambda: [badge("copy")], "dnd_no_drop": lambda: [badge("nope")], "link": lambda: [badge("alias")],
    "question_arrow": lambda: [badge("help")], "context-menu": lambda: [badge("menu")],
    "left_ptr_watch": anim(lambda f: badge("ball", f)), "wait": anim(wait),
    "sb_h_double_arrow": lambda: [base("ew")], "left_side": lambda: [base("ew")],
    "sb_v_double_arrow": lambda: [base("ew", "transpose")], "top_side": lambda: [base("ew", "transpose")],
    "bottom_right_corner": lambda: [base("nwse")], "ul_angle": lambda: [base("nwse")], "lr_angle": lambda: [base("nwse")],
    "bottom_left_corner": lambda: [base("nwse", "mirror")], "ur_angle": lambda: [base("nwse", "mirror")],
    "ll_angle": lambda: [base("nwse", "mirror")],
    "sb_up_arrow": lambda: [base("up")], "top_tee": lambda: [base("up")],
    "sb_down_arrow": lambda: [base("up", "flip")], "bottom_tee": lambda: [base("up", "flip")],
    "sb_left_arrow": lambda: [base("up", "transpose")], "left_tee": lambda: [base("up", "transpose")],
    "sb_right_arrow": lambda: [tf(*base("up", "transpose"), "mirror")], "right_tee": lambda: [tf(*base("up", "transpose"), "mirror")],
}


def shadowed(im):
    out = Image.new("RGBA", im.size); W, H = im.size
    for y in range(H):
        for x in range(W):
            if im.getpixel((x, y))[3] and x + 1 < W and y + 1 < H and not im.getpixel((x + 1, y + 1))[3]:
                out.putpixel((x + 1, y + 1), SHADOW)
    out.alpha_composite(im)
    return out


def sheet(out):
    from PIL import ImageDraw
    z, pad, cols = 8, 18, 8
    items = sorted(CURSORS)
    rows = []
    for n in items:
        fr = CURSORS[n]()
        rows.append((n, [shadowed(im) for im, _ in fr][:4], fr[0][1]))
    cw = GRID * z + pad
    W = cols * cw * 1 + 40; H = ((len(rows) + cols - 1) // cols) * (cw + 20) + 20
    sh = Image.new("RGBA", (W, H), (118, 108, 140, 255)); d = ImageDraw.Draw(sh)
    for k, (n, ims, hot) in enumerate(rows):
        x, y = (k % cols) * cw + 20, (k // cols) * (cw + 20) + 10
        big = ims[0].resize((ims[0].width * z * GRID // max(GRID, ims[0].width), ims[0].height * z * GRID // max(GRID, ims[0].width)), Image.NEAREST)
        sh.alpha_composite(big, (x, y))
        d.rectangle([x + hot[0] * z, y + hot[1] * z, x + hot[0] * z + z - 1, y + hot[1] * z + z - 1], outline=(255, 60, 60, 255))
        d.text((x, y + GRID * z + 2), n[:17] + (f" {len(CURSORS[n]())}f" if len(CURSORS[n]()) > 1 else ""), fill=(255, 255, 255, 255))
    sh.save(out)


def theme(dst):
    dst = Path(dst); cur = dst / "cursors"
    cur.mkdir(parents=True, exist_ok=True)
    for n, fn in CURSORS.items():
        fr = fn()
        images = []
        for s in SIZES:
            z = s // GRID
            off = 0 if n in TIP else z // 2
            for im, (hx, hy) in fr:
                big = shadowed(im)
                images.append((s, hx * z + off, hy * z + off, DELAY if len(fr) > 1 else 0, big.resize((big.width * z, big.height * z), Image.NEAREST)))
        xc.write(cur / n, images)
    for p in SRC.iterdir():
        if p.is_symlink() and os.readlink(p) in CURSORS:
            q = cur / p.name
            if q.exists() or q.is_symlink():
                q.unlink()
            os.symlink(os.readlink(p), q)
    (dst / "index.theme").write_text("[Icon Theme]\nName=angelOS Mac Pixel\n"
                                     "Comment=Golden Gate: macOS's cursors as 12x12 pixel art (after ful1e5/apple_cursor, GPL-3.0)\n")


if __name__ == "__main__":
    {"sheet": sheet, "theme": theme}[sys.argv[1]](sys.argv[2])
