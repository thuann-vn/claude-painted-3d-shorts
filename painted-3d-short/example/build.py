# Nếu Mặt Trời tắt? — joins the shots, draws the text and mixes the sound (example of skill painted-3d-short).
#   ~/Projects/blender-shorts/bookstreet/.venv/bin/python build.py
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/.claude/skills/painted-3d-short/tools"))
from film import *

# (frames, [(folder, fade-in first frame, fade length)]): the first folder is the base, later ones fade in over it
F = Film([(88, [("s1", 0, 0)]), (118, [("s2", 0, 0)]),
          (130, [("s3a", 0, 0), ("s3b", 4, 7), ("s3c", 62, 34)]),      # noon → black in 7 frames → lamps come on
          (165, [("s4", 0, 0), ("s4f", 50, 60)]),                       # frost creeps over the tea stall
          (148, [("s5", 0, 0), ("s5f", 26, 36)])])                      # the sea freezes
T2, T3, T4, T5 = (F.start[k] / FPS for k in (1, 2, 3, 4))
K18 = word_frame(F.tm, "l4", "mười") - F.start[3]
K73 = word_frame(F.tm, "l4", "bảy") - F.start[3]
YEAR = word_frame(F.tm, "l4", "Một", 1) - F.start[3]  # "Một năm sau"


def temp(i):  # the same curve as the red column in scene.py
    return 28 - 46 * ease(K18 - 40, K18 + 2, i) - 55 * ease(K73 - 34, K73 + 2, i)


def draw(d, g, sh, i, t):
    if sh == 0 and 14 <= i <= 84:  # the premise, on the sunny street
        k = pop(i, 14)
        label(d, (W / 2, 470), "MẶT TRỜI", 118 * k, YEL)
        label(d, (W / 2, 600), "VỪA TẮT", 118 * k)
    if sh == 1:  # 8:20 runs down to 0:00 while the last light is on its way
        left = math.ceil(500 * (1 - ease(6, 110, i)))
        label(d, (W / 2, 1010), "%d:%02d" % (left // 60, left % 60), 210, YEL if left > 30 else (255, 96, 80), sw=12)
        label(d, (W / 2, 1160), "ánh sáng cuối còn tới sau", 52)
    if sh == 3:  # the temperature beside the thermometer
        T = temp(i)
        when = "hôm nay" if i < K18 - 40 else ("sau 1 tuần" if i < YEAR else "sau 1 năm")
        c = (255, 150, 70) if T > 5 else ((150, 215, 255) if T > -40 else (190, 200, 255))
        label(d, (760, 700), ("%d°C" % round(T)).replace("-", "−"), 150, c, sw=11)
        label(d, (760, 820), when, 52)


F.segments()
F.text(draw)
F.mix(bed="out/bed.mp3", bed_from=18, bed_vol=0.32, out="out/final.mp4", sfx=[
    ("out/sfx/clock-tick-fast.mp3", T2, 0.35, T3 - T2, True),
    ("out/sfx/sun-power-down.mp3", T3 + 4 / 24, 0.9, None, False),
    ("out/sfx/cold-wind-howl.mp3", T4, 0.3, None, True),
    ("out/sfx/ice-freeze-crack.mp3", T5 + 1.0, 0.6, None, False)])
F.check()
