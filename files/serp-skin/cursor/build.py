#!/usr/bin/env python3
"""angelOS Serp — the serp skin's cursor: soft vector shapes in the skin's colours.

A light, rounded arrow with a dark rim and a soft shadow, a drop (a bead in the skin's accent) by its
tail — the drop the skin arrives with (skin-morph). Waiting is a ring a liquid arc runs around.
Every shape is drawn from vectors for each size (24…96), 8× supersampled, so no size is a
scaled copy of another. The names and their aliases are angelOS Mac Pixel's (links.json).

  build.py sheet OUT.png     every cursor on one sheet (the waiting ones' first frames)
  build.py theme DIR         the Xcursor theme: DIR/cursors (+ alias links), DIR/index.theme
"""
import json
import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xc  # noqa: E402

SIZES = (24, 32, 36, 48, 64, 72, 96)   # 64-96: the living pointer drawn big (angel-niri 0017 takes the nearest)
S = 8                                   # supersampling
TXT = (238, 236, 250)                   # the body
RIM = (30, 28, 46)                      # the rim
ACC = (150, 156, 222)                   # the accent: serp's lavender
RED = (232, 120, 140)                   # «no»
FRAMES, DELAY = 12, 55


# ---------------------------------------------------------------- drawing
class Pen:
    """draws in 24-unit coordinates onto an L mask of one size, supersampled"""
    def __init__(self, size):
        self.size, self.u = size, size * S / 24
        self.mask = Image.new("L", (size * S, size * S))
        self.d = ImageDraw.Draw(self.mask)

    def p(self, x, y):
        return (x * self.u, y * self.u)

    def poly(self, pts, fill=255):
        self.d.polygon([self.p(*q) for q in pts], fill=fill)

    def rect(self, x0, y0, x1, y1, r=0.0, fill=255):
        self.d.rounded_rectangle([*self.p(x0, y0), *self.p(x1, y1)], radius=r * self.u, fill=fill)

    def circle(self, cx, cy, r, fill=255):
        self.d.ellipse([*self.p(cx - r, cy - r), *self.p(cx + r, cy + r)], fill=fill)

    def ring(self, cx, cy, r, w, fill=255):
        self.circle(cx, cy, r + w / 2, fill)
        self.circle(cx, cy, r - w / 2, 0)

    def line(self, pts, w, fill=255):
        self.d.line([self.p(*q) for q in pts], fill=fill, width=max(1, round(w * self.u)), joint="curve")
        for q in (pts[0], pts[-1]):
            self.circle(*q, w / 2, fill)

    def arc(self, cx, cy, r, w, a0, a1, fill=255):
        box = [*self.p(cx - r, cy - r), *self.p(cx + r, cy + r)]
        self.d.arc(box, a0, a1, fill=fill, width=max(1, round(w * self.u)))
        for a in (a0, a1):
            self.circle(cx + math.cos(math.radians(a)) * (r - w / 2), cy + math.sin(math.radians(a)) * (r - w / 2), w / 2, fill)


def soften(m, u):
    """round every corner a hair (blur, threshold back)"""
    return m.filter(ImageFilter.GaussianBlur(0.35 * u)).point(lambda v: 255 if v > 127 else 0)


def grow(m, px):
    k = max(1, int(px)) * 2 + 1
    return m.filter(ImageFilter.MaxFilter(k))


class Layer:
    """one coloured piece: its mask gets a rim of its own"""
    def __init__(self, size, colour, rim=1.5):
        self.pen, self.colour, self.rim = Pen(size), colour, rim


def compose(size, layers, rotate=0, shadow=True):
    """layers bottom → top; each: rim (dark) then body (colour). Then down to size, a soft shadow"""
    canvas = Image.new("RGBA", (size * S, size * S))
    u = size * S / 24
    for L in layers:
        m = soften(L.pen.mask, u)
        if rotate:
            m = m.rotate(rotate, resample=Image.BICUBIC, center=(size * S / 2, size * S / 2))
            m = m.point(lambda v: 255 if v > 127 else 0)
        rim = grow(m, L.rim * u * 0.5) if L.rim else m
        canvas.paste(Image.new("RGBA", canvas.size, RIM + (255,)), (0, 0), rim)
        canvas.paste(Image.new("RGBA", canvas.size, L.colour + (255,)), (0, 0), m)
    im = canvas.resize((size, size), Image.LANCZOS)
    if not shadow:
        return im
    a = im.split()[3].filter(ImageFilter.GaussianBlur(size / 24 * 1.1)).point(lambda v: int(v * 0.42))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(a)
    out = Image.new("RGBA", im.size)
    out.alpha_composite(sh, (round(size / 24 * 0.5), round(size / 24 * 1.1)))
    out.alpha_composite(im)
    return out


# ---------------------------------------------------------------- the shapes (24-unit coordinates)
ARROW = [(3, 2.5), (3, 18.8), (7.1, 15.1), (9.9, 21.1), (12.4, 19.9), (9.7, 14.1), (15.3, 13.9)]


def arrow(size, bead=True, badge=None, frame=0):
    body = Layer(size, TXT)
    body.pen.poly(ARROW)
    layers = [body]
    if bead:
        b = Layer(size, ACC, 1.2)
        b.pen.circle(16.2, 18.6, 2.0)
        layers.append(b)
    if badge:
        layers += badge(size, frame)
    return compose(size, layers), (3, 2.5)


def _badge(size, colour=ACC):
    b = Layer(size, colour, 1.2)
    b.pen.circle(17, 17, 4.6)
    return b


def mark(size, colour, draw):
    m = Layer(size, colour, 0)
    draw(m.pen)
    return m


def badge_plus(size, f):
    return [_badge(size), mark(size, TXT, lambda p: (p.rect(14.6, 16.2, 19.4, 17.8, 0.6), p.rect(16.2, 14.6, 17.8, 19.4, 0.6)))]


def badge_help(size, f):
    def q(p):
        p.arc(17, 15.6, 1.7, 1.25, 180, 400)
        p.line([(17.9, 16.6), (17, 17.5), (17, 18.0)], 1.25)
        p.circle(17, 19.6, 0.75)
    return [_badge(size), mark(size, TXT, q)]


def badge_link(size, f):
    return [_badge(size), mark(size, TXT, lambda p: (p.line([(15, 19), (19, 15)], 1.3), p.line([(16.4, 15), (19, 15), (19, 17.6)], 1.3)))]


def badge_menu(size, f):
    return [_badge(size), mark(size, TXT, lambda p: [p.rect(14.6, y, 19.4, y + 1.0, 0.5) for y in (15, 16.6, 18.2)])]


def badge_no(size, f):
    def no(p):
        p.ring(17, 17, 3.0, 1.2)
        p.line([(15, 19), (19, 15)], 1.2)
    return [_badge(size, RED), mark(size, TXT, no)]


def spinner_layers(size, frame, cx, cy, r, w):
    track = Layer(size, (88, 86, 120), 1.2)
    track.pen.ring(cx, cy, r, w)
    a0 = frame / FRAMES * 360 - 90
    arc = Layer(size, ACC, 0)
    arc.pen.arc(cx, cy, r + w / 2, w, a0, a0 + 120)
    bead = Layer(size, ACC, 1.0)
    bx, by = cx + math.cos(math.radians(a0 + 120)) * r, cy + math.sin(math.radians(a0 + 120)) * r
    bead.pen.circle(bx, by, w * 0.8)
    return [track, arc, bead]


def badge_spin(size, frame):
    return spinner_layers(size, frame, 17.2, 17.2, 3.6, 1.6)


def wait(size, frame):
    return compose(size, spinner_layers(size, frame, 12, 12, 7.0, 2.4)), (12, 12)


def hand(size, kind="point"):
    L = Layer(size, TXT)
    p = L.pen
    if kind == "point":
        p.rect(8.3, 1.6, 11.5, 13, 1.6)                    # the finger
        for x0, x1 in ((11.3, 13.9), (13.7, 16.1), (15.9, 18.1)):
            p.rect(x0, 9.0, x1, 14, 1.2)                     # the curled ones
        p.rect(6.0, 10.5, 18.1, 21.5, 3.2)                   # the palm
        p.poly([(6.3, 13.2), (3.4, 11.6), (2.5, 13.0), (6.2, 18.5)])   # the thumb
        return compose(size, [L]), (9.9, 1.8)
    if kind == "open":
        for x0, x1, y0 in ((6.4, 8.9, 5.6), (9.0, 11.6, 3.2), (11.7, 14.3, 3.8), (14.4, 16.9, 6.0)):
            p.rect(x0, y0, x1, 14, 1.25)
        p.rect(6.0, 10.5, 17.6, 21.2, 3.2)
        p.poly([(6.3, 14.0), (3.4, 11.4), (2.4, 12.8), (6.2, 18.8)])
        return compose(size, [L]), (11, 11)
    for x0, x1 in ((6.4, 8.9), (9.0, 11.6), (11.7, 14.3), (14.4, 16.9)):   # closed: knuckles
        p.rect(x0, 8.6, x1, 14, 1.25)
    p.rect(6.0, 10.5, 17.6, 20.2, 3.2)
    p.poly([(6.3, 13.6), (4.4, 13.0), (4.0, 14.6), (6.2, 17.6)])
    return compose(size, [L]), (11, 11)


def ibeam(size, vertical=False):
    L = Layer(size, TXT)
    p = L.pen
    p.rect(11.1, 4.0, 12.9, 20.0, 0.9)
    for y in (3.0, 19.2):
        p.rect(8.6, y, 15.4, y + 1.8, 0.9)
    return compose(size, [L], rotate=90 if vertical else 0), (12, 12)


def cross(size, plus=False):
    L = Layer(size, TXT)
    p = L.pen
    if plus:
        p.rect(11.0, 4.5, 13.0, 19.5, 1.0)
        p.rect(4.5, 11.0, 19.5, 13.0, 1.0)
        return compose(size, [L]), (12, 12)
    for a, b in (((11.0, 3.5), (13.0, 9.6)), ((11.0, 14.4), (13.0, 20.5)), ((3.5, 11.0), (9.6, 13.0)), ((14.4, 11.0), (20.5, 13.0))):
        p.rect(*a, *b, 1.0)
    dot = Layer(size, ACC, 1.0)
    dot.pen.circle(12, 12, 1.4)
    return compose(size, [L, dot]), (12, 12)


def nope(size):
    L = Layer(size, RED)
    L.pen.ring(12, 12, 7.0, 2.6)
    L.pen.line([(7.3, 16.7), (16.7, 7.3)], 2.6)
    return compose(size, [L]), (12, 12)


def x_cursor(size):
    L = Layer(size, TXT)
    L.pen.line([(6, 6), (18, 18)], 2.6)
    L.pen.line([(6, 18), (18, 6)], 2.6)
    return compose(size, [L]), (12, 12)


def dotbox(size):
    L = Layer(size, TXT)
    L.pen.rect(5.5, 5.5, 18.5, 18.5, 3)
    L.pen.rect(8.0, 8.0, 16.0, 16.0, 1.8, fill=0)
    dot = Layer(size, ACC, 1.0)
    dot.pen.circle(12, 12, 1.6)
    return compose(size, [L, dot]), (12, 12)


def double(size, rot=0, bar=False):
    """a two-headed arrow, left ↔ right, turned by rot degrees (counter-clockwise)"""
    L = Layer(size, TXT)
    p = L.pen
    p.rect(6.5, 10.9, 17.5, 13.1, 0.8)
    p.poly([(2.6, 12), (7.6, 7.4), (7.6, 16.6)])
    p.poly([(21.4, 12), (16.4, 7.4), (16.4, 16.6)])
    layers = [L]
    if bar:
        b = Layer(size, ACC, 1.2)
        b.pen.rect(11.1, 4.2, 12.9, 19.8, 0.9)
        layers.append(b)
    return compose(size, layers, rotate=rot), (12, 12)


def single(size, rot=0):
    """an arrow pointing up, turned by rot degrees (counter-clockwise)"""
    L = Layer(size, TXT)
    p = L.pen
    p.poly([(12, 3.0), (17.4, 9.4), (6.6, 9.4)])
    p.rect(10.9, 8.5, 13.1, 20.5, 0.8)
    hx, hy = 12 - 9 * math.sin(math.radians(rot)), 12 - 9 * math.cos(math.radians(rot))
    return compose(size, [L], rotate=rot), (hx, hy)


def fourway(size):
    L = Layer(size, TXT)
    p = L.pen
    p.rect(10.9, 6, 13.1, 18, 0.8)
    p.rect(6, 10.9, 18, 13.1, 0.8)
    for pts in ([(12, 2.2), (15.6, 6.4), (8.4, 6.4)], [(12, 21.8), (15.6, 17.6), (8.4, 17.6)],
                [(2.2, 12), (6.4, 8.4), (6.4, 15.6)], [(21.8, 12), (17.6, 8.4), (17.6, 15.6)]):
        p.poly(pts)
    dot = Layer(size, ACC, 1.0)
    dot.pen.circle(12, 12, 1.7)
    return compose(size, [L, dot]), (12, 12)


def zoom(size, sign):
    L = Layer(size, TXT)
    p = L.pen
    p.ring(10, 10, 5.6, 2.2)
    p.line([(14.3, 14.3), (20, 20)], 2.8)
    m = Layer(size, ACC, 0)
    m.pen.rect(7.2, 9.2, 12.8, 10.8, 0.6)
    if sign == "+":
        m.pen.rect(9.2, 7.2, 10.8, 12.8, 0.6)
    return compose(size, [L, m]), (10, 10)


def pencil(size):
    L = Layer(size, TXT)
    L.pen.poly([(4.2, 19.8), (5.2, 15.6), (16.2, 4.6), (19.4, 7.8), (8.4, 18.8)])
    tip = Layer(size, ACC, 1.0)
    tip.pen.poly([(4.2, 19.8), (5.2, 15.6), (8.4, 18.8)])
    return compose(size, [L, tip]), (4.3, 19.7)


def mirror(fr):
    im, (x, y) = fr
    return im.transpose(Image.FLIP_LEFT_RIGHT), (24 - x, y)


def anim(fn):
    return lambda s: [fn(s, f) for f in range(FRAMES)]


CURSORS = {
    "left_ptr": lambda s: [arrow(s)], "wayland-cursor": lambda s: [arrow(s)],
    "right_ptr": lambda s: [mirror(arrow(s))],
    "center_ptr": lambda s: [single(s, 0)],
    "hand2": lambda s: [hand(s, "point")], "hand1": lambda s: [hand(s, "open")], "move": lambda s: [hand(s, "closed")],
    "all-scroll": lambda s: [fourway(s)],
    "xterm": lambda s: [ibeam(s)], "vertical-text": lambda s: [ibeam(s, True)],
    "cross": lambda s: [cross(s)], "crosshair": lambda s: [cross(s)], "plus": lambda s: [cross(s, True)],
    "crossed_circle": lambda s: [nope(s)], "X_cursor": lambda s: [x_cursor(s)], "dotbox": lambda s: [dotbox(s)],
    "pencil": lambda s: [pencil(s)],
    "zoom-in": lambda s: [zoom(s, "+")], "zoom-out": lambda s: [zoom(s, "-")],
    "copy": lambda s: [arrow(s, False, badge_plus)], "dnd_no_drop": lambda s: [arrow(s, False, badge_no)],
    "link": lambda s: [arrow(s, False, badge_link)], "question_arrow": lambda s: [arrow(s, False, badge_help)],
    "context-menu": lambda s: [arrow(s, False, badge_menu)],
    "left_ptr_watch": anim(lambda s, f: arrow(s, False, badge_spin, f)), "wait": anim(wait),
    "sb_h_double_arrow": lambda s: [double(s)], "left_side": lambda s: [double(s)],
    "sb_v_double_arrow": lambda s: [double(s, 90)], "top_side": lambda s: [double(s, 90)],
    "bottom_right_corner": lambda s: [double(s, -45)], "ul_angle": lambda s: [double(s, -45)], "lr_angle": lambda s: [double(s, -45)],
    "bottom_left_corner": lambda s: [double(s, 45)], "ur_angle": lambda s: [double(s, 45)], "ll_angle": lambda s: [double(s, 45)],
    "sb_up_arrow": lambda s: [single(s, 0)], "top_tee": lambda s: [single(s, 0)],
    "sb_down_arrow": lambda s: [single(s, 180)], "bottom_tee": lambda s: [single(s, 180)],
    "sb_left_arrow": lambda s: [single(s, 90)], "left_tee": lambda s: [single(s, 90)],
    "sb_right_arrow": lambda s: [single(s, -90)], "right_tee": lambda s: [single(s, -90)],
}
# the column / row splitters (col-resize, row-resize) are aliases of these in links.json; give them the bar
CURSORS["sb_h_double_arrow"] = lambda s: [double(s, 0, True)]
CURSORS["sb_v_double_arrow"] = lambda s: [double(s, 90, True)]


def sheet(out):
    size, cols, pad = 48, 9, 14
    names = sorted(CURSORS)
    cw = size * 2 + pad
    W, H = cols * cw + pad, ((len(names) + cols - 1) // cols) * (cw + 16) + pad
    sh = Image.new("RGBA", (W, H), (120, 116, 168, 255))
    d = ImageDraw.Draw(sh)
    for k, n in enumerate(names):
        im, (hx, hy) = CURSORS[n](size)[0]
        big = im.resize((size * 2, size * 2), Image.LANCZOS)
        x, y = (k % cols) * cw + pad, (k // cols) * (cw + 16) + pad
        sh.alpha_composite(big, (x, y))
        cx, cy = x + hx * 4, y + hy * 4
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], outline=(255, 60, 60, 255))
        d.text((x, y + size * 2 + 1), n[:16], fill=(255, 255, 255, 255))
    sh.save(out)


def theme(dst):
    dst = Path(dst)
    cur = dst / "cursors"
    cur.mkdir(parents=True, exist_ok=True)
    for n, fn in CURSORS.items():
        images = []
        for s in SIZES:
            frames = fn(s)
            for im, (hx, hy) in frames:
                images.append((s, round(hx * s / 24), round(hy * s / 24), DELAY if len(frames) > 1 else 0, im))
        xc.write(cur / n, images)
    for name, target in json.loads((HERE / "links.json").read_text()).items():
        q = cur / name
        if q.exists() or q.is_symlink():
            q.unlink()
        os.symlink(target, q)
    (dst / "index.theme").write_text("[Icon Theme]\nName=angelOS Serp\n"
                                     "Comment=The serp skin's cursor: soft, rounded, with the skin's drop\n")


if __name__ == "__main__":
    {"sheet": sheet, "theme": theme}[sys.argv[1]](sys.argv[2])
