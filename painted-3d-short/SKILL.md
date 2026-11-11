---
name: painted-3d-short
description: Make a vertical Short (20–30 s) in the studio's "3D vẽ tay" style - a Blender blockout of real places, repainted by Flow as hand-painted backgrounds, projected back on the 3D set so the camera can move, with all motion (snow, leaves, birds, gauges, screens, day→night, freezing) done in code and by cross-fading Flow edits of the same painting. No Muse, no characters acting. Use for jobs with paint3d, and for What If / science / place explainers where places and things carry the story.
---

# 3D vẽ tay (painted-3D Short)

Approved by the owner 2026-11-10 ("ok phết nhỉ, đưa vào studio đi") after the test "Nếu Mặt Trời tắt?" (27 s, 5 shots).
That video is the worked example in `example/` — read `example/scene.py`, `example/build.py`, `example/jobs.json`,
`example/jobs2.json` and look at `example/check.jpg`, `example/paint.jpg`, `example/blockout.jpg` before making a new one.
Copy the example's two scripts and change them; do not start from an empty file.

What this style is good at: a place that CHANGES (noon → pitch black → lamps on, a street freezing, water rising, a room
at day and at night), close views of objects with code-drawn moving parts (thermometer column, clock hands, a screen
typing, a countdown), slow forward camera moves through a painted world. What it cannot do: people or animals acting,
talking heads, fast action. Write scripts where things and places are the subject. No people in the paintings unless the
script needs a still figure seen from far away.

Tools (`tools/`): `p3d.py` (Blender side), `film.py` (joins shots, text layer, sound), `tts.mjs` (voice + word times),
`restyle.mjs` (Flow). Style reference for every repaint: `refs/style.jpg`.

## 1. Script (step "Claude viết kịch bản")

- 20–30 s, keep it under 30 s: 5–7 spoken lines, ~55–75 Vietnamese words. One narrator ("bạn" for the viewer).
- What If / explainer order: the premise as a question or a flat statement in line 1 (consequence in the first 3 s) →
  2–3 situations that escalate → the science with real numbers → a last image that stays. Facts and numbers must be
  true: look them up, and put the sources in SPEC.md and the YouTube description.
- One line = one shot (sometimes two short lines share a shot). 4–6 shots. For each shot decide: the place, the camera,
  what CHANGES during the shot (a state edit) and what MOVES by code. A shot where nothing changes and nothing moves is
  a slide: give it at least one of the two.
- Reuse a camera for a before/after (shot 3 of the example is shot 1's frame going dark): same painting, edited.
- Giải Ngố IT videos end with the channel's closing line only when the job's rules ask for it.

Write `script.json` = `{ "title", "lines": [{ "id": "l1", "vo": "<spoken line, numbers written as words>" }] }`.

## 2. Voice first

`cd <work dir> && node ~/.claude/skills/painted-3d-short/tools/tts.mjs` → `out/voice.mp3`, `out/timing.json`
(line and word times; it prints the frame each line starts at). VN speed stays 1.0. Shots are cut on these times:
a shot ends 3–5 frames before the first line of the next shot starts; the last shot runs to the printed length.
If the total is over 30 s, cut words and run it again. Exit 3 = ElevenLabs refused: use the VClip twin voice
(skill vclip-tts) and write the same `out/timing.json` (word times from whisper via the studio's scripts/wordtimes.mjs).

## 3. The set (scene.py)

Copy `example/scene.py`. It is three parts: the set, the shots, the code animation.

- Real sizes in metres, z up. Build everything with `b = B()` (`b.box / b.cyl / b.ball(material, size, location, rot)`)
  and finish with `b.done("set")`; `M(name, "#hex", roughness, emission, "#emit")` makes a material; `P(b, x, y, rz)`
  places parts in a local frame. Use own `random.Random(seed)` generators so the set is the same in every run (the
  paintings are tied to the geometry).
- Blockout only: boxes, cylinders and balls in clear flat colours. Flow adds the detail. But every object that must be
  in the painting has to be in the blockout at its true place and size, because the painting is projected back on it.
- Light: `outdoor(sun_dir, energy, sky=...)` for streets and landscapes; indoor rooms add area lights by hand (see
  ~/Projects/blender-shorts/office/office.py). Then `start()`.
- Shots: `id: (camera pos, target, lens, dolly forward m, frames, [(frames folder, painting name), ...])`. Tall frame
  768×1376; the 36 mm sensor is the long side, so a 20–24 mm lens is a wide view and 30–40 mm a close one. Subjects sit
  near the middle; keep important things out of the bottom 25 % (captions) and the right edge.
- Dolly is forward only and small: 0.5–0.9 m in a wide street view, 0.15–0.3 m when something is within 2 m of the lens.
  Never move the camera sideways or backwards from the painted view (the edges smear).
- A place far from the others (the beach in the example) is just built somewhere else on the same ground.

Stills: `blender -b --factory-startup --python-exit-code 1 -P scene.py -- --stills` → `out/still_<id>.png`. LOOK at
them (one sheet). Fix framing now: the subject large enough, nothing important hidden behind a nearer thing, the
thing a code part will be drawn over in clear view.

## 4. Flow paints (two rounds)

Round 1, repaint each still (`jobs.json`, one job per shot that has its own camera): refs = [the still,
`refs/style.jpg`], aspect "9:16", prompt = the fixed opening of the example (repaint the FIRST image in the STYLE of the
SECOND, keep composition and every object's place and size, no people, no text) + what the place is, the light, and
materials. Rules:
- Say where the sun/moon/lamps are and that they stay exactly where the blockout has them.
- A thing code will animate is painted EMPTY/blank: "the glass tube is EMPTY and pale", "the screen is a plain dark
  rectangle", "the clock face has no hands".
- Dark scenes are asked for in the prompt (the blockout is always lit): name the one light source.

`node ~/.claude/skills/painted-3d-short/tools/restyle.mjs out/jobs.json out/paint` (all Flow accounts in parallel,
~2–5 min a picture). Then remove the ✦ mark from every picture:
`~/.local/share/unmark-venv/bin/python ~/Projects/video-studio/scripts/unmark.py out/paint/s1.jpg`. LOOK at the
paintings: objects must sit where the blockout has them; repaint one that drifted.

Round 2, state edits (`jobs2.json`): ref = [the painting], prompt opens with "Edit this painting, keeping every line,
object and brush stroke in exactly the same place (the result must overlay the original pixel for pixel) … Only this
changes: …". Name it `s<id><letter>` (s1n night, s4f frost). Never repaint a second state from the blockout: two
repaints never line up; an edit does.

A job that fails with "unusual activity" is a flagged Flow account, not the prompt: send that one job again (another
account takes it). "violate policies" is the prompt: reword it. Flow pictures cost no credits.

Start rendering round-1 shots while round 2 is drawing: `--proj --shots 1,2` and `--passes s3a,s4` render only what
has its painting.

## 5. Code animation (in scene.py, after `start()`)

- Ready-made: `fx_snow({shot: (first frame, all-in frame)})`, `fx_leaves((x, y), {shots})`,
  `fx_birds({shot: (start point, velocity)})`, `fx_motes(lo, hi, {shots})` (dust in window light). Each returns a
  setter for `render()`.
- Own parts: `poly(name, points, flat("name", "#hex"))` makes a flat shape; a setter `(shot id, frame)` shows, moves and
  scales it. Put it a few cm IN FRONT of the blockout object it marks (a shape inside the blockout is hidden) and make
  it a little narrower than the painted thing, so a few pixels of drift do not show.
- Tie motion to the voice: read `out/timing.json` and key on the frame a word is said (the example's thermometer
  reaches −18 on "mười tám"). Share the same curve function with build.py when a number is also shown as text.
- Snow and other near-lens things stay ≥ 1.7 m from the camera.

Render: `blender -b --factory-startup --python-exit-code 1 -P scene.py -- --proj --shots <ids>`; run up to 3 Blender
processes side by side (split the shots), never more.

## 6. Build (build.py)

Copy `example/build.py`: `Film([(frames, [(folder, 0, 0), (edit folder, fade first frame, fade length)]), …])`, a
`draw(d, g, shot, i, t)` for the video's own text (title words, countdowns, numbers; `label()` with outline),
`F.segments(); F.text(draw); F.mix(bed=…, sfx=[…]); F.check()`. Run with Pillow:
`uv run --no-project --with pillow python build.py`.

- Captions come from the word times automatically (y 1385). Own text stays inside x 60–940, y 220–1500; ≥ 0.35 s per
  word + 1 s on screen; at most one text block besides the caption at a time.
- A light going out is fast (7 frames); frost, ice, dusk take 1.5–2.5 s.
- Music: one bed per video, a genre the last videos did not use:
  `node ~/Projects/video-studio/scripts/music-find.mjs search "<mood, genre>" --min 30` then `get "<title>" out/bed.mp3`
  (keep the CC BY credit line). Sound effects that match what is seen:
  `node ~/Projects/video-studio/scripts/sfx-gen.mjs <name> "<english description>" <seconds> --to out/sfx`.
- LOOK at `out/check.jpg` (two frames per shot): text readable and on time with the caption, code parts in the right
  place, no doubled edges, state changes visible. Fix and rebuild before handing over.

## 7. In the studio (job.paint3d)

Work in `p3d/` inside the video folder (scene.py, build.py, script.json, out/). The studio reads:
`studio-script.json` (lines for the review page), `SPEC.md`, then after the build `renders/preview.mp4` (copy of
`p3d/out/final.mp4`), `renders/storyboard.jpg` (copy of `p3d/out/check.jpg`), `p3d/out/timing.json`, and
`studio-notes.md` (length, shots, which paintings were redone, Flow accounts flagged, music credit, fact sources).

## Lessons already paid for

- EEVEE world volume blocks sun and sky: no volumes; haze belongs in the painting.
- Doubled windows/monitors came from surfaces the painted camera could not see taking the paint of what stood in front;
  `p3d.py` handles it with a depth map + fill picture. What is left: an object Flow painted a few pixels off its
  blockout can ghost when the camera passes close — keep dollies short near objects.
- Windows that show an outside view need a glass box in the opening in `--proj` (see office.py), or the frame doubles
  on the view behind.
- Trees: trunk + two or three branches + many overlapping balls read as a tree after Flow; a single ball does not.
- Text or letters on signs come back garbled: ask for "no text, no letters" and draw words in build.py.
- Flow ~2–5 min per picture, a whole video 30–40 min; most of it is waiting for Flow.
