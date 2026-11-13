"""Xcursor read/write (stdlib + PIL)."""
import struct
from PIL import Image

IMG = 0xFFFD0002


def read(path):
    """-> list of (nominal, xhot, yhot, delay, RGBA Image)"""
    d = open(path, "rb").read()
    ntoc = struct.unpack_from("<I", d, 12)[0]
    out = []
    for i in range(ntoc):
        t, sub, pos = struct.unpack_from("<III", d, 16 + i * 12)
        if t != IMG:
            continue
        hl, ty, nom, ver, w, h, xh, yh, dl = struct.unpack_from("<9I", d, pos)
        raw = d[pos + 36:pos + 36 + w * h * 4]
        im = Image.frombytes("RGBA", (w, h), raw, "raw", "BGRA")
        # premultiplied → straight
        px = im.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if 0 < a < 255:
                    px[x, y] = (min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a)
        out.append((nom, xh, yh, dl, im))
    return out


def write(path, images):
    """images: list of (nominal, xhot, yhot, delay, RGBA Image) → Xcursor file"""
    chunks = []
    for nom, xh, yh, dl, im in images:
        im = im.convert("RGBA")
        w, h = im.size
        px = []
        for r, g, b, a in im.getdata():
            px.append(struct.pack("<4B", b * a // 255, g * a // 255, r * a // 255, a))
        chunks.append((nom, struct.pack("<9I", 36, IMG, nom, 1, w, h, xh, yh, dl) + b"".join(px)))
    n = len(chunks)
    head = struct.pack("<4sIII", b"Xcur", 16, 0x10000, n)
    pos = 16 + n * 12
    toc, body = b"", b""
    for nom, c in chunks:
        toc += struct.pack("<III", IMG, nom, pos + len(body))
        body += c
    open(path, "wb").write(head + toc + body)
