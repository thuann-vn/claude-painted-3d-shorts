# Joins the rendered shots of a painted-3D short, draws the text layer and mixes the sound (skill painted-3d-short).
# A video's build.py imports it and runs with a Python that has Pillow:
#     ~/Projects/blender-shorts/bookstreet/.venv/bin/python build.py
#     import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/painted-3d-short/tools")); from film import *
#     F = Film([(frames, [(folder, 0, 0), (folder2, fade first frame, fade length), ...]), ...])
#     F.segments(); F.text(draw); F.mix(bed="out/bed.mp3", sfx=[...]); F.check()
# Reads out/timing.json (tts.mjs) and out/voice.mp3; frames in out/f/<folder>/NNN.png (768x1376 → 1080x1920).
import subprocess, os, json, math
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 24
FF = ["ffmpeg", "-v", "error", "-y"]
ENC = ["-r", "24", "-an", "-c:v", "libx264", "-crf", "15", "-pix_fmt", "yuv420p"]
FIT = "scale=1080:-2:flags=lanczos,crop=1080:1920"
FONT = "/Users/admin/Projects/video-studio/assets/fonts/BeVietnamPro-ExtraBold.ttf"
YEL, WHITE, INK = (255, 214, 64), (255, 255, 255), (16, 18, 26)
_fonts = {}


def font(size):
    size = max(1, int(size))
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def ease(a, b, i):
    u = max(0.0, min(1.0, (i - a) / (b - a)))
    return u * u * (3 - 2 * u)


def pop(i, a, n=5):
    """0→1 over n frames from frame a (use as a size factor for text that pops in)"""
    u = max(0.0, min(1.0, (i - a) / n))
    return 1 - (1 - u) ** 3


def label(d, xy, s, size, fill=WHITE, sw=None, anchor="mm", maxw=None):
    """text with a dark outline. Keep it inside x 60–940, y 220–1500 (the Shorts buttons cover the rest)."""
    f = font(size)
    if maxw:
        while size > 20 and d.textlength(s, font=f) > maxw:
            size -= 2
            f = font(size)
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=sw if sw is not None else max(4, size // 7), stroke_fill=INK)


def timing(path="out/timing.json"):
    return json.load(open(path, encoding="utf8"))


def word_frame(tm, line_id, word, nth=0):
    """global frame at which a word of a line is spoken (nth occurrence), for cues that must land on the voice"""
    ln = next(l for l in tm["lines"] if l["id"] == line_id)
    hits = [w for w in ln["words"] if w["w"].strip(".,!?…:;\"'").lower() == word.lower()]
    return round(hits[nth]["t"] * FPS)


def caption_cues(tm, max_chars=24):
    """caption pieces from the word times: break after punctuation or when a piece gets long"""
    cues = []
    for ln in tm["lines"]:
        piece, t0 = [], None
        ws = ln["words"]
        for k, w in enumerate(ws):
            if t0 is None:
                t0 = w["t"]
            piece.append(w["w"])
            s = " ".join(piece)
            last = k == len(ws) - 1
            rest = len(" ".join(x["w"] for x in ws[k + 1:]))
            soon = any(x["w"][-1] in ",.!?…:;" for x in ws[k + 1:k + 3])  # a comma or full stop is 1–2 words away: break there instead
            if last or (w["w"][-1] in ",.!?…:;" and len(s) >= 10) or (len(s) >= max_chars and rest >= 8 and not soon):
                cues.append([t0, None, s.rstrip(",")])
                piece, t0 = [], None
        cues[-1][1] = ln["end"] + 0.25
    for a, b in zip(cues, cues[1:]):
        if a[1] is None:
            a[1] = b[0]
    return cues


class Film:
    def __init__(self, cut, src="out/f", work="out"):
        self.cut, self.src, self.work = cut, src, work
        self.start = [0]
        for n, _ in cut:
            self.start.append(self.start[-1] + n)
        self.total = self.start[-1]
        self.tm = timing(os.path.join(work, "timing.json"))
        need = math.ceil(self.tm["duration"] * FPS)
        if self.total < need - 2:
            print(f"!! the picture ({self.total} frames) is shorter than the voice ({need} frames)")

    def shot_at(self, g):
        sh = max(k for k in range(len(self.cut)) if g >= self.start[k])
        return sh, g - self.start[sh]

    def segments(self):
        os.makedirs(f"{self.work}/seg", exist_ok=True)
        lst = []
        for n, (a, layers) in enumerate(self.cut):
            o = f"{self.work}/seg/{n}.mp4"
            cmd = FF[:]
            for folder, _, _ in layers:
                cmd += ["-framerate", "24", "-i", f"{self.src}/{folder}/%03d.png"]
            fc, cur = "", "[0:v]"
            for k, (folder, st, ln) in enumerate(layers[1:], 1):
                fc += f"{cur}[{k}:v]blend=all_expr='A+(B-A)*clip((N-{st})/{max(1, ln)},0,1)'[b{k}];"
                cur = f"[b{k}]"
            fc += f"{cur}{FIT}[o]"
            subprocess.run(cmd + ["-filter_complex", fc, "-map", "[o]", "-frames:v", str(a)] + ENC + [o], check=True)
            lst.append(f"file '{os.path.abspath(o)}'")
        open(f"{self.work}/seg/list.txt", "w").write("\n".join(lst))

    def text(self, draw=None, captions=True, cap_y=1385, cap_size=58):
        """one transparent PNG per frame: draw(d, g, shot index, frame in shot, seconds) adds the video's own text; captions follow the voice"""
        os.makedirs(f"{self.work}/txt", exist_ok=True)
        cues = caption_cues(self.tm) if captions else []
        for g in range(self.total):
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            t = g / FPS
            sh, i = self.shot_at(g)
            if draw:
                draw(d, g, sh, i, t)
            for a, e, p in cues:
                if a <= t < e:
                    label(d, (W / 2 - 30, cap_y), p, cap_size, maxw=860)
            im.save(f"{self.work}/txt/{g:04d}.png")

    def mix(self, bed=None, bed_from=0.0, bed_vol=0.3, sfx=(), out="out/final.mp4"):
        """sfx: (file, start s, volume, length s or None, loop True/False). Voice = out/voice.mp3 from 0."""
        T = self.total / FPS
        cmd = FF + ["-f", "concat", "-safe", "0", "-i", f"{self.work}/seg/list.txt", "-framerate", "24", "-i", f"{self.work}/txt/%04d.png", "-i", f"{self.work}/voice.mp3"]
        fc, mixin = "[2:a]volume=1.5[vo];", ["[vo]"]
        k = 3
        if bed:
            cmd += ["-i", bed]
            fc += f"[{k}:a]atrim={bed_from}:{bed_from + T:.2f},asetpts=PTS-STARTPTS,volume={bed_vol},afade=t=in:d=0.5,afade=t=out:st={T - 1.2:.2f}:d=1.2[bed];"
            mixin.append("[bed]")
            k += 1
        for n, (f, at, vol, ln, loop) in enumerate(sfx):
            cmd += ["-i", f]
            ln = min(ln if ln else 1e9, T - at)
            chain = ("aloop=loop=-1:size=2e9," if loop else "") + (f"atrim=0:{ln:.2f}," if ln < 1e8 else "") + f"volume={vol}"
            if loop:
                chain += f",afade=t=in:d=1.2,afade=t=out:st={max(0, ln - 1.2):.2f}:d=1.2"
            fc += f"[{k}:a]{chain},adelay={int(at * 1000)}:all=1[s{n}];"
            mixin.append(f"[s{n}]")
            k += 1
        fc += "".join(mixin) + f"amix=inputs={len(mixin)}:normalize=0,loudnorm=I=-14:TP=-1.5,atrim=0:{T:.3f}[a];[0:v][1:v]overlay=0:0[v]"
        subprocess.run(cmd + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{T:.3f}", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "24",
                              "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
        self.out = out
        print("film", round(T, 2), "s →", out)

    def check(self, out="out/check.jpg", per_shot=2):
        """contact sheet: per_shot frames of every shot, to LOOK at before calling the video done"""
        fr = []
        for k, (n, _) in enumerate(self.cut):
            fr += [self.start[k] + round(n * (j + 0.5) / per_shot) for j in range(per_shot)]
        sel = "+".join(f"eq(n\\,{g})" for g in fr)
        subprocess.run(FF + ["-i", self.out, "-vf", f"select='{sel}',scale=270:480,tile={len(fr)}x1", "-frames:v", "1", out], check=True)
        print("check sheet →", out)
