# Nếu Mặt Trời tắt? — What If short in the painted-3D style (example of skill painted-3d-short).
#   blender -b --factory-startup --python-exit-code 1 -P scene.py -- --stills      blockout stills → out/still_<id>.png (sent to Flow)
#   blender -b --factory-startup --python-exit-code 1 -P scene.py -- --proj        final frames from the paintings in out/paint
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/.claude/skills/painted-3d-short/tools"))
from p3d import *

# ---------------------------------------------------------------- palette
ROAD = M("road", "#6f7178", 0.95)
WALK = M("walk", "#c9c2b4", 0.9)
GROUND = M("ground", "#d8c9a4", 0.95)
HOUSE = [M("house%d" % i, c, 0.9) for i, c in enumerate(["#f2d58a", "#e9a48a", "#a9d3c4", "#f3ead8", "#9fc3e6", "#e8b7c6", "#c9d98f", "#f0b46a"])]
SHUT = [M("shut%d" % i, c, 0.7) for i, c in enumerate(["#2f6f78", "#3f7d4a", "#8a4b32", "#2f5fa5", "#b5462f"])]
GLASS = M("glass", "#3b5878", 0.3)
RAIL = M("rail", "#3a3d45", 0.5)
SLAB = M("slab", "#e9e3d6", 0.8)
TILE = M("tile", "#c4583a", 0.8)
STEEL = M("steel", "#c9d2da", 0.3)
AWN = [M("awn%d" % i, c, 0.8) for i, c in enumerate(["#d9413a", "#2f6fb5", "#f0b429", "#2e9b6a", "#f3ead7"])]
SIGN = [M("sign%d" % i, c, 0.6) for i, c in enumerate(["#d9413a", "#f0b429", "#2f6fb5", "#ffffff"])]
POLE = M("pole", "#8d8f93", 0.8)
WIRE = M("wire", "#22242a", 0.6)
TRUNK = M("trunk", "#7a5a3c", 0.9)
LEAFM = [M("pl0", "#3f8f3a", 0.9), M("pl1", "#5fae3f", 0.9), M("pl2", "#2f7440", 0.9)]
RED = M("red", "#d9413a", 0.5)
BLUE = M("blue", "#2f6fb5", 0.5)
DARK = M("dark", "#2a2c33", 0.5)
WHITE = M("white", "#fbf8f0", 0.5)
WOOD = M("wood", "#a8743f", 0.7)
CHROME = M("chrome", "#aab2ba", 0.3)
POTM = M("pot", "#c9632e", 0.8)
SUNM = M("sunball", "#fff3b0", 0.5, 6.0, "#ffe680")
MOONM = M("moonball", "#eef2fa", 0.9, 0.6, "#eef2fa")
SEA = M("sea", "#2f7f9a", 0.25)
SAND = M("sand", "#e7d3a1", 0.95)
ROCK = M("rock", "#7d7f86", 0.9)
HULL = M("hull", "#2f6fb5", 0.6)
BASKET = M("basket", "#8a6a3f", 0.9)
LAMPH = M("lamph", "#f6e7b8", 0.6)

# ---------------------------------------------------------------- the street: runs along +y, road x -2.5..2.5
b = B()
b.box(GROUND, (420, 420, 0.2), (0, 0, -0.1))
b.box(ROAD, (5.0, 52, 0.04), (0, 18, 0.02))
for s in (-1, 1):
    b.box(WALK, (1.0, 52, 0.14), (s * 3.0, 18, 0.07))
rh = random.Random(21)
TANKS = []


def house(s, y0, w, floors, k):
    H = floors * 3.2
    body = HOUSE[k % len(HOUSE)]
    yc = y0 + w / 2
    xf = s * 3.5
    b.box(body, (6.0, w - 0.06, H), (s * 6.5, yc, H / 2))
    sh = SHUT[(k * 3 + 1) % len(SHUT)]
    b.box(sh, (0.08, w * 0.62, 2.5), (xf - s * 0.03, yc, 1.25))  # roller door
    b.box(AWN[k % len(AWN)], (1.3, w * 0.86, 0.06), (xf - s * 0.62, yc, 2.82), (0, s * 0.22, 0))
    if k % 3 != 1:
        b.box(SIGN[k % len(SIGN)], (0.1, w * 0.7, 0.55), (xf - s * 0.06, yc, 3.05 + 0.3))
    for f in range(1, floors):
        z = f * 3.2
        b.box(SLAB, (1.0, w * 0.92, 0.12), (xf - s * 0.5, yc, z))
        b.box(RAIL, (0.04, w * 0.92, 0.05), (xf - s * 0.98, yc, z + 0.95))
        for j in range(7):
            b.box(RAIL, (0.03, 0.03, 0.9), (xf - s * 0.98, yc + (j / 6 - 0.5) * w * 0.9, z + 0.5))
        for e in (-1, 1):
            b.box(GLASS, (0.08, 0.95, 1.9), (xf - s * 0.03, yc + e * w * 0.22, z + 1.1))
            b.box(sh, (0.06, 0.3, 1.9), (xf - s * 0.06, yc + e * (w * 0.22 + 0.62), z + 1.1))
        if rh.random() < 0.6:
            b.box(POTM, (0.22, 0.22, 0.2), (xf - s * 0.75, yc + rh.uniform(-1, 1) * w * 0.3, z + 0.16))
            b.ball(LEAFM[k % 3], (0.5, 0.5, 0.5), (xf - s * 0.75, yc + rh.uniform(-1, 1) * w * 0.3, z + 0.5))
        if rh.random() < 0.45:
            b.box(WHITE, (0.3, 0.8, 0.55), (xf - s * 0.18, yc + w * 0.36, z + 2.55))  # air conditioner
    b.box(SLAB, (6.1, w - 0.02, 0.5), (s * 6.5, yc, H + 0.25))
    if k % 2 == 0:
        tx = s * rh.uniform(4.6, 6.0)
        for e in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            b.box(RAIL, (0.05, 0.05, 0.9), (tx + e[0] * 0.4, yc + e[1] * 0.4, H + 0.95))
        b.cyl(STEEL, (1.1, 1.1, 1.4), (tx, yc, H + 2.1))
        b.cyl(STEEL, (1.1, 1.1, 0.25), (tx, yc, H + 2.9), top=0.3)
    else:
        b.box(TILE, (3.6, w + 0.2, 0.1), (s * 6.0, yc, H + 1.1), (0, s * 0.45, 0))


for s in (-1, 1):
    y = -8.0
    k = 0 if s < 0 else 4
    while y < 40:
        w = rh.choice((3.6, 4.0, 4.4))
        fl = rh.choice((2, 3, 3, 4))
        if s > 0 and 8 < y < 30:
            fl = min(fl, 3)  # the sun stands over the right side of the street
        if s > 0 and 3 < y + w / 2 < 8:
            fl = 3
        house(s, y, w, fl, k)
        y += w
        k += 1
for j, x in enumerate((-7.5, -2.5, 2.5, 7.5)):  # the houses that close the street
    b.box(HOUSE[(j * 3 + 2) % len(HOUSE)], (5.0, 6, 9.6 + 3.2 * (j % 2)), (x, 45, 4.8 + 1.6 * (j % 2)))
    for f in range(3):
        b.box(GLASS, (1.0, 0.08, 1.8), (x - 1.0, 41.97, f * 3.2 + 1.5))
        b.box(GLASS, (1.0, 0.08, 1.8), (x + 1.0, 41.97, f * 3.2 + 1.5))
    b.box(TILE, (5.2, 3.6, 0.1), (x, 43.6, 10.6 + 3.2 * (j % 2)), (0.45, 0, 0))
POLES = [2.0, 16.0, 30.0]
for y in POLES:
    b.cyl(POLE, (0.24, 0.24, 8.4), (-2.75, y, 4.2), seg=10)
    b.box(POLE, (1.5, 0.1, 0.1), (-2.75, y, 7.6))
    b.box(POLE, (1.1, 0.1, 0.1), (-2.75, y, 6.9))
    b.box(STEEL, (0.4, 0.3, 0.5), (-2.75, y - 0.25, 6.2))
for a_, c_ in zip(POLES, POLES[1:]):
    L = c_ - a_
    for dx, z in ((-0.7, 7.68), (-0.25, 7.68), (0.3, 7.68), (0.7, 7.68), (-0.5, 6.98), (0.0, 6.98), (0.5, 6.98), (0.1, 6.3), (0.2, 6.15)):
        b.box(WIRE, (0.03, L, 0.03), (-2.75 + dx, (a_ + c_) / 2, z - 0.12))
for y, z, y2 in ((16, 6.9, 19.5), (16, 6.3, 12.5), (30, 6.9, 26.5), (2, 6.3, 5.5)):  # wires across the street to the houses
    dx, dy, dz = 6.2, y2 - y, 1.2
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    b.box(WIRE, (L, 0.03, 0.03), (0.35, (y + y2) / 2, z - 0.6), (0, math.asin(dz / L), math.atan2(dy, dx)))
for y in (9.0, 23.0, 36.0):  # street lamps
    b.cyl(POLE, (0.16, 0.16, 6.0), (2.75, y, 3.0), seg=10)
    b.box(POLE, (1.3, 0.1, 0.1), (2.15, y, 5.95))
    b.box(LAMPH, (0.5, 0.26, 0.14), (1.55, y, 5.86))
# the tree on the left pavement
TREE = Vector((-2.95, 11.0, 0))
b.cyl(TRUNK, (0.5, 0.5, 3.4), (TREE.x, TREE.y, 1.7), top=0.7, seg=10)
b.cyl(TRUNK, (0.28, 0.28, 1.8), (TREE.x + 0.5, TREE.y + 0.2, 3.9), (0, 0.6, 0), top=0.6, seg=8)
b.cyl(TRUNK, (0.28, 0.28, 1.8), (TREE.x - 0.3, TREE.y - 0.4, 3.9), (0.5, -0.4, 0), top=0.6, seg=8)
rt = random.Random(5)
for j in range(16):
    a = rt.uniform(0, 6.28)
    r = rt.uniform(0.2, 1.7)
    b.ball(LEAFM[j % 3], (rt.uniform(1.4, 2.2),) * 3, (TREE.x + 0.6 + r * math.cos(a) * 0.8, TREE.y + r * math.sin(a), rt.uniform(4.3, 6.4)))
# motorbike parked on the left
p = P(b, -2.3, 4.6, 0.0)
for yy in (-0.62, 0.62):
    p.cyl(DARK, (0.56, 0.56, 0.12), (0, yy, 0.3), (0, math.pi / 2, 0), seg=14)
    p.cyl(CHROME, (0.24, 0.24, 0.13), (0, yy, 0.3), (0, math.pi / 2, 0), seg=10)
p.box(RED, (0.3, 0.9, 0.3), (0, 0.0, 0.55))
p.box(DARK, (0.32, 0.75, 0.1), (0, -0.2, 0.78))
p.box(RED, (0.34, 0.2, 0.55), (0, 0.5, 0.75), (-0.3, 0, 0))
p.box(CHROME, (0.62, 0.05, 0.05), (0, 0.62, 1.08))
p.box(WHITE, (0.16, 0.08, 0.14), (0, 0.72, 0.95))
# tea stall on the right pavement, with a big wall thermometer (shot 4)
TH = Vector((3.42, 5.7, 0))
p = P(b, 2.75, 5.0, 0.0)
p.box(BLUE, (0.6, 0.6, 0.04), (0, 0, 0.46))
for e in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
    p.box(BLUE, (0.04, 0.04, 0.46), (e[0] * 0.26, e[1] * 0.26, 0.23))
p.cyl(STEEL, (0.2, 0.2, 0.22), (0.08, 0.1, 0.59))
p.cyl(STEEL, (0.2, 0.2, 0.08), (0.08, 0.1, 0.74), top=0.4)
for j, (gx, gy) in enumerate(((-0.14, -0.12), (-0.02, -0.2), (-0.2, 0.08))):
    p.cyl(WHITE, (0.07, 0.07, 0.1), (gx, gy, 0.53), top=1.2)
for j, (sx, sy, m_) in enumerate(((-0.6, 0.1, RED), (0.1, -0.65, RED), (-0.35, -0.6, BLUE))):
    p.cyl(m_, (0.3, 0.3, 0.3), (sx, sy, 0.15), top=0.8, seg=10)
b.box(WHITE, (0.03, 0.3, 0.95), (TH.x - 0.05, TH.y, 1.55))  # thermometer board
b.box(WOOD, (0.04, 0.36, 1.01), (TH.x - 0.03, TH.y, 1.55))
b.cyl(STEEL, (0.05, 0.05, 0.7), (TH.x - 0.075, TH.y, 1.6), seg=8)
b.ball(STEEL, (0.1, 0.1, 0.1), (TH.x - 0.075, TH.y, 1.2))
for j in range(13):
    b.box(DARK, (0.01, 0.06 if j % 3 == 0 else 0.035, 0.008), (TH.x - 0.068, TH.y + 0.075, 1.26 + j * 0.052))
b.box(WIRE, (0.015, 0.015, 0.75), (2.95, 5.75, 2.42))  # hanging bulb under the awning
b.ball(LAMPH, (0.13, 0.13, 0.16), (2.95, 5.75, 2.0))
# sun and a pale daytime moon
SUN_D = Vector((math.sin(math.radians(8)) * math.cos(math.radians(34)), math.cos(math.radians(8)) * math.cos(math.radians(34)), math.sin(math.radians(34))))
MOON_D = Vector((math.sin(math.radians(-13)) * math.cos(math.radians(46)), math.cos(math.radians(-13)) * math.cos(math.radians(46)), math.sin(math.radians(46))))
b.ball(SUNM, (13, 13, 13), tuple(SUN_D * 150), sub=3)
b.ball(MOONM, (6, 6, 6), tuple(MOON_D * 150), sub=3)
# ---------------------------------------------------------------- the beach (shot 5), behind the street, looking -y
b.box(SAND, (160, 16, 0.3), (0, -42, 0.1))
b.box(SEA, (400, 150, 0.2), (0, -124, 0.12))
for j in range(9):  # wet edge and long low waves
    b.box(WHITE, (rt.uniform(8, 30), 0.25, 0.04), (rt.uniform(-12, 12), -49.5 - j * j * 0.9, 0.24))
b.ball(HULL, (2.4, 7.0, 2.0), (2.6, -55, 0.5))
b.box(RED, (2.2, 6.0, 0.14), (2.6, -55, 0.95))
b.box(WHITE, (1.4, 1.8, 1.3), (2.6, -56.2, 1.6))
b.box(TILE, (1.7, 2.2, 0.1), (2.6, -56.2, 2.3))
b.cyl(WOOD, (0.1, 0.1, 3.4), (2.6, -54.0, 2.6), seg=8)
b.cyl(BASKET, (1.9, 1.9, 0.7), (-1.6, -44.5, 0.6), (0.25, 0.1, 0), top=0.72, seg=16)
b.cyl(DARK, (1.75, 1.75, 0.04), (-1.6, -44.42, 0.94), (0.25, 0.1, 0), seg=16)
b.box(WOOD, (0.08, 1.9, 0.05), (-1.2, -44.9, 1.02), (0.3, 0.1, 0.5))
px, py = -3.6, -46.5  # coconut palm leaning toward the sea
for j in range(7):
    b.cyl(TRUNK, (0.36 - j * 0.02, 0.36 - j * 0.02, 1.25), (px + j * 0.16, py - j * 0.22, 0.8 + j * 1.05), (0.2, 0.15, 0), seg=8)
cx, cyy, cz = px + 1.05, py - 1.5, 7.9
for j in range(9):
    a = j * math.tau / 9
    b.box(LEAFM[j % 3], (3.4, 0.7, 0.06), (cx + 1.5 * math.cos(a), cyy + 1.5 * math.sin(a), cz - 0.45), (0, 0.42, a))
b.ball(TRUNK, (0.5, 0.5, 0.5), (cx, cyy, cz - 0.2))
for (x, y, s_) in ((4.6, -45.5, 1.5), (5.6, -46.4, 1.0), (3.9, -46.6, 0.7), (-6.5, -49.5, 1.2)):
    b.ball(ROCK, (s_ * 1.3, s_, s_ * 0.8), (x, y, 0.3 + s_ * 0.2), sub=1)
for (x, y, sx, sz) in ((-60, -185, 60, 14), (-20, -190, 40, 8), (70, -188, 50, 10)):  # islands on the horizon
    b.ball(LEAFM[2], (sx, 20, sz), (x, y, 0), sub=2)
setob = b.done("set")

outdoor(sun_dir=(0.45, -0.25, 0.86), energy=4.0, sky="#8fc4f2")
start()

# ---------------------------------------------------------------- shots, cut on the voice (out/timing.json: l2 at frame 92, l3 210, l4 340, l5 505)
# id: (camera, target, lens, dolly forward in m, frames, painting passes [(frames folder, painting name)])
C1 = ((0.5, -2.0, 1.6), (-0.1, 20.0, 7.6), 20)
SHOTS = {
    1: (C1[0], C1[1], C1[2], 0.7, 88, [("s1", "1")]),
    2: ((-1.2, 12.0, 1.6), tuple(Vector((-1.2, 12.0, 1.6)) + (SUN_D * 30) + Vector((-1.0, 0, -5.5))), 30, 0.5, 118, [("s2", "2")]),
    3: (C1[0], C1[1], C1[2], 0.9, 130, [("s3a", "1"), ("s3b", "1n"), ("s3c", "1l")]),  # shot 1's frame: noon -> black -> lamps on
    4: ((0.95, 3.75, 1.4), (3.5, 5.6, 1.38), 31, 0.2, 165, [("s4", "4"), ("s4f", "4f")]),  # thermometer, then frost
    5: ((0.3, -41.5, 2.1), (1.5, -58.0, 2.5), 22, 0.5, 148, [("s5", "5"), ("s5f", "5f")]),  # the sea, then ice
}
START4 = 88 + 118 + 130  # first frame of shot 4 in the film

# ---------------------------------------------------------------- code animation (made after start(), so it keeps its flat colours)
birds = fx_birds({1: ((-16, 34, 15.5), (5.2, -0.8, 0.5)), 2: ((-13, 40, 21), (4.6, 0.5, 0.7))})
leaves = fx_leaves((TREE.x + 1.1, TREE.y), {1})
snow = fx_snow({4: (112, 160), 5: (50, 125)})

# the red column of the thermometer (shot 4): falls to -18 on "mười tám", to -73 on "bảy mươi ba"
REDM = flat("redm", "#e2332b")
merc = poly("merc", [(0, -0.013, 0), (0, 0.013, 0), (0, 0.013, 1), (0, -0.013, 1)], REDM)
mbulb = poly("mercb", [(0, 0.04 * math.cos(a_ * math.tau / 12), 0.04 * math.sin(a_ * math.tau / 12)) for a_ in range(12)], REDM)
Z0, ZK = 1.2, (1.26, 0.624 / 120.0)  # bulb; column top = 1.26 + (T + 80) * 0.0052
TM = json.load(open(os.path.join(OUT, "timing.json"), encoding="utf8"))
W4 = {w["w"].strip(".,"): round(w["t"] * 24) - START4 for w in next(l for l in TM["lines"] if l["id"] == "l4")["words"]}
K18, K73 = W4["mười"], W4["bảy"]  # frames (in shot 4) where the two numbers are said


def temp(i):  # build.py draws the number with the same curve
    return 28 - 46 * ease(K18 - 40, K18 + 2, i) - 55 * ease(K73 - 34, K73 + 2, i)


def set_merc(sid, i):
    on = PROJ and sid == 4
    merc.hide_render = mbulb.hide_render = not on
    if on:
        x = TH.x - 0.145  # in front of the painted tube and bulb, never inside the blockout shapes
        merc.location = (x, TH.y, Z0)
        merc.scale = (1, 1, ZK[0] + (temp(i) + 80) * ZK[1] - Z0)
        mbulb.location = (x, TH.y, Z0)


render(SHOTS, [birds, leaves, snow, set_merc], nostill={3})
