"""angelOS Mac Pixel: macOS's cursors redrawn by hand as pixel art on angelOS Pixel's 12x12 grid,
compact (about 9 cells, angelOS Pixel's size) — 2/3/4 screen pixels a cell at sizes 24/36/48.
'.' empty, 'k' black, 'w' white, other letters from PAL. build.py adds the drop shadow."""
import math

PAL = {"k": (20, 20, 22), "w": (255, 255, 255), "g": (150, 150, 158), "r": (232, 64, 58), "G": (52, 199, 89),
       "y": (255, 204, 0), "p": (255, 140, 170), "b": (10, 132, 255), "o": (255, 149, 0), "P": (175, 82, 222),
       "H": (255, 236, 140), "Y": (255, 204, 51), "D": (214, 150, 20), "E": (150, 98, 10)}  # H/Y/D/E: the halo's golds, light to dark

D = {}  # name -> (rows, hotspot)

D["arrow"] = ("""
w.......
ww......
wkw.....
wkkw....
wkkkw...
wkkkkw..
wkkkkkw.
wkkwwww.
wkwkkw..
ww.wkkw.
....ww..""", (0, 0))

D["small"] = ("""
w......
ww.....
wkw....
wkkw...
wkkkw..
wkkkkw.
wkkwww.
wkwkw..
ww.wkw.
....ww.""", (0, 0))

HALO = """
..HHHHH..
.Y.....Y.
D.......D
.EDDDDDE."""


def _haloed(drop=2):
    """the arrow with a small golden halo threaded on it (frostpix's touch): a ring seen from the side,
    light gold on top and dark below; the tip (the hotspot) pokes up through it — the top arc runs
    behind the arrow, the front arc across it, `drop` cells below the tip"""
    W, H, A = 12, 12, (2, 0)
    ring = HALO.strip("\n").split("\n")
    g = [["."] * W for _ in range(H)]

    def put(rows, ox, oy):
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != ".":
                    g[oy + y][ox + x] = ch
    put(ring[:-1], A[0] - 2, A[1] + drop)                                # the back of the ring
    put(D["arrow"][0].strip("\n").split("\n"), A[0], A[1])              # the arrow through it
    put(ring[-1:], A[0] - 2, A[1] + drop + 3)                            # the front arc, over the arrow
    return "\n" + "\n".join("".join(r) for r in g), A


D["haloed"] = _haloed()

D["hand"] = ("""
...kk.....
..kwwk....
..kwwkkk..
..kwwkwwkk
kkkwwwwwwk
kwkwwwwwwk
kwwwwwwwwk
.kwwwwwwk.
..kwwwwwk.
..kkkkkkk.""", (3, 0))

D["open"] = ("""
..kk.kk...
.kwwkwwkk.
.kwwkwwkwk
kkwwwwwwwk
kwkwwwwwwk
kwwwwwwwwk
.kwwwwwwk.
..kwwwwwk.
...kkkkk..""", (5, 4))

D["closed"] = ("""
.kk.kk.kk.
kwwkwwkwwk
kwwwwwwwwk
kkwwwwwwwk
kwwwwwwwk.
.kwwwwwwk.
..kkkkkk..""", (5, 3))

D["ibeam"] = ("""
www.www
wkkwkkw
.wwkww.
..wkw..
..wkw..
..wkw..
..wkw..
.wwkww.
wkkwkkw
www.www""", (3, 5))

D["cross"] = ("""
...www...
...wkw...
...wkw...
www...www
wkk.k.kkw
www...www
...wkw...
...wkw...
...www...""", (4, 4))

D["ew"] = ("""
..w.....w..
.wkw...wkw.
wkkwwwwwkkw
kkkkkkkkkkk
wkkwwwwwkkw
.wkw...wkw.
..w.....w..""", (5, 3))

def _diag():
    """the diagonal resize arrow: a black line corner to corner, a 3-cell head at each end, a white rim all round"""
    k = {(1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (8, 8), (7, 8), (6, 8), (8, 7), (8, 6)} | {(i, i) for i in range(2, 8)}
    rows = []
    for y in range(10):
        row = ""
        for x in range(10):
            near = any((x + dx, y + dy) in k for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            row += "k" if (x, y) in k else "w" if near else "."
        rows.append(row)
    return "\n" + "\n".join(rows)


D["nwse"] = (_diag(), (4, 4))

D["move"] = ("""
....w....
...wkw...
..wkkkw..
.w.wkw.w.
wkkkkkkkw
.w.wkw.w.
..wkkkw..
...wkw...
....w....""", (4, 4))

D["up"] = ("""
...ww...
..wkkw..
.wkkkkw.
wkkkkkkw
wwwkkwww
..wkkw..
..wkkw..
..wkkw..
..wwww..""", (3, 0))

D["nope"] = ("""
..wwwww..
.wrrrrrw.
wrrw..wrw
wrwrw..rw
wr.wrw.rw
wr..wrwrw
wrw..wrrw
.wrrrrrw.
..wwwww..""", (4, 4))

D["X"] = ("""
ww....ww
wkw..wkw
.wkwwkw.
..wkkw..
..wkkw..
.wkwwkw.
wkw..wkw
ww....ww""", (4, 4))

D["plus"] = ("""
...kkk...
...kwk...
...kwk...
kkkkwkkkk
kwwwwwwwk
kkkkwkkkk
...kwk...
...kwk...
...kkk...""", (4, 4))

D["zoom"] = ("""
.kkkkk...
kwwwwwk..
kwwwwwk..
kwwwwwk..
kwwwwwk..
kwwwwwk..
.kkkkkkk.
......kkk
.......kk""", (3, 3))

D["pencil"] = ("""
......kk.
.....kppk
....kyykk
...kyyyk.
..kyyyk..
.kwyyk...
kwwwk....
kkwk.....
kk.......""", (0, 8))

D["dotbox"] = ("""
wwwwwwwww
wk.k.k.kw
w.......w
wk.....kw
w.......w
wk.....kw
w.......w
wk.k.k.kw
wwwwwwwww""", (4, 4))

BADGE = {
    "copy": """
.kkk.
kGwGk
kwwwk
kGwGk
.kkk.""",
    "nope": """
.kkk.
kwrrk
krwrk
krrwk
.kkk.""",
    "alias": """
kkkkk
kwwwk
kwkkk
kwkwk
kkkkk""",
    "help": """
.kkk.
kwwbk
kbwbk
kbbbk
.kwk.""",
    "menu": """
kkkkk
kwwwk
kkkkk
kwwwk
kkkkk""",
}


def ball(frame, n=8, r=4.6, c=4.0, size=9):
    """the beach ball: six coloured slices turning a slice a frame, a dark rim, a glint"""
    cols = ["r", "o", "y", "G", "b", "P"]
    rows = []
    for y in range(size):
        row = ""
        for x in range(size):
            d = math.hypot(x - c, y - c)
            if d > r:
                row += "."
            elif d > r - 1:
                row += "k"
            else:
                a = (math.atan2(y - c, x - c) / (2 * math.pi) + frame / n) % 1
                row += cols[int(a * len(cols))]
        rows.append(row)
    if size >= 7:
        rows[2] = rows[2][:2] + "w" + rows[2][3:]
    return rows


# the halo's rim as one loop, clockwise from the top left (9x4, as HALO)
RIM = [(2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 1), (8, 2), (7, 3), (6, 3), (5, 3), (4, 3), (3, 3), (2, 3),
       (1, 3), (0, 2), (1, 1)]


def spinning_halo(frame, n=8):
    """the halo turning: its golds as HALO, and a glint (white, then light gold) running round the rim,
    once round in n frames"""
    g = [list(r.replace("H", "Y")) for r in HALO.strip("\n").split("\n")]   # an even gold, so the glint shows all round
    i = frame * len(RIM) // n
    for k, ch in ((0, "w"), (1, "H"), (-1, "H")):
        x, y = RIM[(i + k) % len(RIM)]
        g[y][x] = ch
    return ["".join(r) for r in g]


def waiting(frame, n=8):
    """the beach ball with the halo spinning over it: 12x14, the ball's centre at (4, 9)"""
    g = [["."] * 12 for _ in range(14)]
    for y, r in enumerate(spinning_halo(frame, n)):
        for x, ch in enumerate(r):
            if ch != ".":
                g[y][x] = ch
    for y, r in enumerate(ball(frame, n)):
        for x, ch in enumerate(r):
            if ch != ".":
                g[5 + y][x] = ch
    return ["".join(r) for r in g], (4, 9)


def small_ball(frame, n=8):
    return ball(frame, n, r=2.7, c=2.0, size=5)
