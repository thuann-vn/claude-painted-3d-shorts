# Painted-3D machinery for Blender 5.2 (skill painted-3d-short). A scene script imports it:
#     import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/painted-3d-short/tools")); from p3d import *
#     ... build the set with B() / M() ...        lights: outdoor(...) or your own
#     start()                                     camera, render settings, projection material (after this: code objects)
#     ... code-animation objects: poly(), flat(), fx_snow(), fx_leaves(), fx_birds(), fx_motes() ...
#     render(SHOTS, [setter, ...], nostill={...})
# Run:  blender -b --factory-startup --python-exit-code 1 -P scene.py -- --stills            first frame of each shot → out/still_<id>.png
#       blender -b --factory-startup --python-exit-code 1 -P scene.py -- --proj [--shots 1,2] [--passes s3b,s4f]   final frames → out/f/<folder>/NNN.png
# Flags: --wide = 1376x768 (16:9); default is tall 768x1376 (9:16, the size Flow returns).
import bpy, bmesh, math, random, sys, os
import numpy as np
from mathutils import Vector, Matrix, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STILLS = "--stills" in argv
PROJ = "--proj" in argv
WIDE = "--wide" in argv
ONLY = [int(x) for x in argv[argv.index("--shots") + 1].split(",")] if "--shots" in argv else None
PASSF = set(argv[argv.index("--passes") + 1].split(",")) if "--passes" in argv else None
_script = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a in ("-P", "--python") and i + 1 < len(sys.argv)), __file__)
HERE = os.path.dirname(os.path.abspath(_script))
OUT = os.path.join(HERE, "out")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
KEEP = {}      # shot id → camera matrix of the painted view (frame 0)
CODE_OBS = []  # code-animation objects (kept out of the depth map of the painted view)
MATS = {}


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1]


MATS = {}


def M(name, hexc=None, rough=0.85, emit=0.0, emit_hex=None):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexc)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.25
    if emit or emit_hex:
        b.inputs["Emission Color"].default_value = lin(emit_hex or hexc)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m


def bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


class B:
    """many primitives in one mesh, one material slot per colour"""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _place(self, verts, m, size, loc, rot, smooth):
        bm = self.bm
        bmesh.ops.scale(bm, vec=size, verts=verts)
        if rot != (0, 0, 0):
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rot[0], 3, "X"), verts=verts)
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rot[1], 3, "Y"), verts=verts)
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rot[2], 3, "Z"), verts=verts)
        bmesh.ops.translate(bm, vec=loc, verts=verts)
        i = self.mi(m)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i
            f.smooth = smooth

    def box(self, m, size, loc, rot=(0, 0, 0)):
        self._place(bmesh.ops.create_cube(self.bm, size=1)["verts"], m, size, loc, rot, False)

    def ball(self, m, size, loc, rot=(0, 0, 0), sub=2):
        self._place(bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=0.5)["verts"], m, size, loc, rot, True)

    def cyl(self, m, size, loc, rot=(0, 0, 0), top=1.0, seg=12):
        v = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=0.5, radius2=0.5 * top, depth=1)["verts"]
        self._place(v, m, size, loc, rot, True)

    def done(self, name, parent=None):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        return ob



def flat(name, hexc, strength=1.0):
    m_ = bpy.data.materials.new(name)
    m_.use_nodes = True
    for n_ in list(m_.node_tree.nodes):
        m_.node_tree.nodes.remove(n_)
    o_ = m_.node_tree.nodes.new("ShaderNodeOutputMaterial")
    e_ = m_.node_tree.nodes.new("ShaderNodeEmission")
    e_.inputs["Color"].default_value = lin(hexc)
    e_.inputs["Strength"].default_value = strength
    m_.node_tree.links.new(e_.outputs[0], o_.inputs["Surface"])
    return m_


def rot2(x, y, a):
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


class P:
    """place boxes in a local frame at (ox, oy), turned by rz"""

    def __init__(self, b, ox, oy, rz=0.0):
        self.b, self.ox, self.oy, self.rz = b, ox, oy, rz

    def w(self, loc):
        x, y = rot2(loc[0], loc[1], self.rz)
        return (self.ox + x, self.oy + y, loc[2])

    def box(self, m, size, loc, rot=(0, 0, 0)):
        self.b.box(m, size, self.w(loc), (rot[0], rot[1], rot[2] + self.rz))

    def cyl(self, m, size, loc, rot=(0, 0, 0), top=1.0, seg=12):
        self.b.cyl(m, size, self.w(loc), (rot[0], rot[1], rot[2] + self.rz), top=top, seg=seg)

    def ball(self, m, size, loc, sub=2):
        self.b.ball(m, size, self.w(loc), (0, 0, self.rz), sub=sub)



def ease(a, b, i):
    """smooth 0→1 while i goes a→b"""
    u = max(0.0, min(1.0, (i - a) / (b - a)))
    return u * u * (3 - 2 * u)


def poly(name, pts, m_):
    """a flat code-animation shape (one face), hidden until a setter shows it. Create after start()."""
    me_ = bpy.data.meshes.new(name)
    me_.from_pydata(pts, [], [list(range(len(pts)))])
    me_.materials.append(m_)
    ob_ = bpy.data.objects.new(name, me_)
    col.objects.link(ob_)
    ob_.visible_shadow = False
    ob_.hide_render = True
    CODE_OBS.append(ob_)
    return ob_


def outdoor(sun_dir=(0.45, -0.25, 0.86), energy=4.0, color=(1.0, 0.95, 0.85), sky="#8fc4f2", strength=1.0):
    """blockout light for an outdoor set: one sun + sky colour. Indoor sets add their own area lights instead."""
    sd = bpy.data.lights.new("sun", "SUN")
    so = bpy.data.objects.new("sun", sd)
    col.objects.link(so)
    so.rotation_euler = (-Vector(sun_dir).normalized()).to_track_quat("-Z", "Y").to_euler()
    sd.angle, sd.energy, sd.color = math.radians(2), energy, color
    world(sky, strength)
    return so


def world(sky="#8fc4f2", strength=1.0):
    w = bpy.data.worlds.new("w")
    scene.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = lin(sky)
    bg.inputs["Strength"].default_value = strength


cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d)
col.objects.link(cam)
scene.camera = cam
cam_d.clip_start, cam_d.clip_end = 0.05, 1000
projector = pt = ku = kv = None
W_ = H_ = 0
occlusion_maps = None


def look(pos, tgt, lens):
    cam.location = pos
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens


def start(dome_at=(0, 0, 0), dome_size=400, exposure=-0.2):
    """camera + EEVEE settings + sky dome + projection material; in --proj every material so far becomes the projection.
    Call once, after the whole set and its lights exist and before any code-animation object."""
    global projector, pt, ku, kv, W_, H_, occlusion_maps
    if scene.world is None:
        world()
    db = B()
    db.ball(M("_dome", "#ffffff"), (dome_size,) * 3, dome_at, sub=3)  # the painted sky lands here
    dome = db.done("dome")
    dome.hide_render = not PROJ
    dome.visible_shadow = False
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = (1376, 768) if WIDE else (768, 1376)
    scene.render.image_settings.file_format = "PNG"
    scene.render.fps = 24
    ee = scene.eevee
    ee.taa_render_samples = 32
    for k, v in dict(use_shadows=True, use_raytracing=True, shadow_ray_count=2, shadow_step_count=6).items():
        try:
            setattr(ee, k, v)
        except Exception as e:
            print("eevee setting skipped", k, e)
    try:
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "Medium High Contrast"
        scene.view_settings.exposure = exposure
    except TypeError as e:
        print("look", e)
    W_, H_ = scene.render.resolution_x, scene.render.resolution_y
    projector = bpy.data.objects.new("projector", None)
    col.objects.link(projector)
    pm = bpy.data.materials.new("proj")
    pm.use_nodes = True
    pn = pm.node_tree
    for n_ in list(pn.nodes):
        pn.nodes.remove(n_)
    po = pn.nodes.new("ShaderNodeOutputMaterial")
    pe = pn.nodes.new("ShaderNodeEmission")
    pt = pn.nodes.new("ShaderNodeTexImage")
    pt.extension = "EXTEND"
    pc = pn.nodes.new("ShaderNodeTexCoord")
    pc.object = projector
    sx_ = pn.nodes.new("ShaderNodeSeparateXYZ")
    cx_ = pn.nodes.new("ShaderNodeCombineXYZ")


    def mth(op, a, b):
        n_ = pn.nodes.new("ShaderNodeMath")
        n_.operation = op
        for k_, v_ in ((0, a), (1, b)):
            if isinstance(v_, (int, float)):
                n_.inputs[k_].default_value = v_
            else:
                pn.links.new(v_, n_.inputs[k_])
        return n_.outputs[0]


    pn.links.new(pc.outputs["Object"], sx_.inputs[0])
    negz = mth("MULTIPLY", sx_.outputs["Z"], -1.0)
    ku = pn.nodes.new("ShaderNodeValue")
    kv = pn.nodes.new("ShaderNodeValue")
    pn.links.new(mth("ADD", mth("MULTIPLY", mth("DIVIDE", sx_.outputs["X"], negz), ku.outputs[0]), 0.5), cx_.inputs[0])
    pn.links.new(mth("ADD", mth("MULTIPLY", mth("DIVIDE", sx_.outputs["Y"], negz), kv.outputs[0]), 0.5), cx_.inputs[1])
    pn.links.new(cx_.outputs[0], pt.inputs["Vector"])
    # Occlusion: a surface the painted camera cannot see must not get the paint of what stands in front of it (that is what
    # doubled the window frames, monitors and mugs when the camera moved). A depth map of the painted view decides it; hidden
    # surfaces take a "fill" picture instead: the painting with every foreground thing replaced by the colours behind it.
    MW, MH = W_ // 2, H_ // 2
    bgimg = bpy.data.images.new("bgfill", MW, MH)
    dimg = bpy.data.images.new("pdepth", MW, MH, float_buffer=True)
    dimg.colorspace_settings.name = "Non-Color"
    pb = pn.nodes.new("ShaderNodeTexImage")
    pb.image, pb.extension = bgimg, "EXTEND"
    pd = pn.nodes.new("ShaderNodeTexImage")
    pd.image, pd.extension, pd.interpolation = dimg, "EXTEND", "Closest"
    pn.links.new(cx_.outputs[0], pb.inputs["Vector"])
    pn.links.new(cx_.outputs[0], pd.inputs["Vector"])
    occ = mth("GREATER_THAN", negz, mth("ADD", mth("MULTIPLY", pd.outputs["Color"], 1.03), 0.05))
    pmix = pn.nodes.new("ShaderNodeMix")
    pmix.data_type = "RGBA"
    pn.links.new(occ, pmix.inputs["Factor"])
    pn.links.new(pt.outputs["Color"], pmix.inputs["A"])
    pn.links.new(pb.outputs["Color"], pmix.inputs["B"])
    pn.links.new(pmix.outputs["Result"], pe.inputs["Color"])
    pn.links.new(pe.outputs[0], po.inputs["Surface"])


    def shift(a, dy, dx):
        """a moved by (dy, dx) with the edge repeated"""
        p = np.pad(a, ((1, 1), (1, 1)) + ((0, 0),) * (a.ndim - 2), mode="edge")
        return p[1 + dy:1 + dy + a.shape[0], 1 + dx:1 + dx + a.shape[1]]


    N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


    def occlusion_maps(camM, lens):
        """depth of the painted view (ray cast) and the fill picture, written into dimg / bgimg"""
        dg = bpy.context.evaluated_depsgraph_get()
        ku_ = lens / 36.0 * (1 if W_ >= H_ else H_ / W_)
        kv_ = lens / 36.0 * (W_ / H_ if W_ >= H_ else 1)
        org = camM.translation
        rot = camM.to_3x3()
        d = np.full((MH, MW), 1e4, np.float32)
        for j in range(MH):
            vy = ((j + 0.5) / MH - 0.5) / kv_
            for i in range(MW):
                dc = Vector((((i + 0.5) / MW - 0.5) / ku_, vy, -1.0))
                L = dc.length
                hit, loc, _n, _i, _o, _m = scene.ray_cast(dg, org, rot @ (dc / L))
                if hit:
                    d[j, i] = (loc - org).length / L
        far = d.copy()
        for _ in range(16):
            for dy, dx in N8:
                far = np.maximum(far, shift(far, dy, dx))
        fg = d < far * 0.88
        img = pt.image
        w, h = img.size
        px = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(px)
        colr = px.reshape(h, w, 4)[::h // MH, ::w // MW][:MH, :MW].copy()
        known = ~fg
        for _ in range(90):
            if known.all():
                break
            acc = np.zeros_like(colr)
            cnt = np.zeros((MH, MW), np.float32)
            kc = colr * known[..., None]
            for dy, dx in N8:
                acc += shift(kc, dy, dx)
                cnt += shift(known.astype(np.float32), dy, dx)
            new = (~known) & (cnt > 0)
            colr[new] = acc[new] / cnt[new][:, None]
            known |= new
        colr[..., 3] = 1
        bgimg.pixels.foreach_set(colr.ravel())
        bgimg.update()
        dm = d.copy()
        for dy, dx in N8:  # a little farther at silhouettes, so the edge of a thing in front still takes its own paint
            dm = np.maximum(dm, shift(d, dy, dx))
        dimg.pixels.foreach_set(np.repeat(dm[..., None], 4, axis=2).ravel())
        dimg.update()

    if PROJ:
        for ob_ in bpy.data.objects:
            if ob_.type in ("MESH", "CURVE", "FONT"):
                if not ob_.data.materials:
                    ob_.data.materials.append(pm)
                for k_ in range(len(ob_.data.materials)):
                    ob_.data.materials[k_] = pm
        scene.view_settings.look = "None"
        scene.view_settings.exposure = 0
        ee.taa_render_samples = 16


def render(SHOTS, setters=(), nostill=()):
    """SHOTS: id → (camera pos, target, lens mm, dolly forward in m, frames, [(frames folder, painting name), ...]).
    Painting name N means out/paint/sN.jpg; several passes = the same camera with different paintings (cross-faded in build.py).
    setters: functions (shot id, frame) that place the code-animation objects (hide them when PROJ is False)."""
    total = 0
    for sid, (p0, t0, lens, dolly, N, passes) in SHOTS.items():
        p0, t0 = Vector(p0), Vector(t0)
        look(p0, t0, lens)
        bpy.context.view_layer.update()
        KEEP[sid] = cam.matrix_world.copy()
    for sid, (p0, t0, lens, dolly, N, passes) in SHOTS.items():
        p0, t0 = Vector(p0), Vector(t0)
        fw = (t0 - p0).normalized() * dolly
        if (ONLY and sid not in ONLY) or (STILLS and sid in nostill):
            continue
        for folder, name in (passes if PROJ else passes[:1]):
            if PROJ and PASSF and folder not in PASSF:
                continue
            if PROJ:
                projector.matrix_world = KEEP[sid]
                pt.image = bpy.data.images.load(os.path.join(OUT, "paint", "s%s.jpg" % name))
                for o_ in CODE_OBS:
                    o_.hide_viewport = True
                bpy.context.view_layer.update()
                occlusion_maps(KEEP[sid], lens)
                for o_ in CODE_OBS:
                    o_.hide_viewport = False
                # the 36 mm sensor lies along the longer side of the picture
                ku.outputs[0].default_value = lens / 36.0 * (1 if W_ >= H_ else H_ / W_)
                kv.outputs[0].default_value = lens / 36.0 * (W_ / H_ if W_ >= H_ else 1)
            for i in ([0] if STILLS else range(N)):
                t = 0.0 if STILLS else i / max(1, N - 1)
                look(p0 + fw * t, t0 + fw * t, lens)
                for f_ in setters:
                    f_(sid, i)
                scene.render.filepath = os.path.join(OUT, "still_%d.png" % sid if STILLS else "f/%s/%03d.png" % (folder, i))
                bpy.ops.render.render(write_still=True)
        total += N
    print("@@done", total)


# ---------------------------------------------------------------- ready-made code animation (call after start())
# Each returns a setter(shot id, frame) for render(). Shapes use flat emission colours, so they sit on the painting like cut paper.
def fx_snow(shots, n=320, color="#eef4ff", seed=3):
    """snow in front of the lens. shots: id → (first frame, frame when every flake is in). Flakes stay ≥ 1.7 m away (nearer = white blobs)."""
    rb = random.Random(seed)
    m_ = flat("snowm", color)
    fl = []
    for _ in range(n):
        s_ = rb.uniform(0.005, 0.011)
        fk = poly("snow", [(s_ * math.cos(a_ * math.tau / 8), s_ * math.sin(a_ * math.tau / 8), 0) for a_ in range(8)], m_)
        fl.append((fk, rb.uniform(-1, 1), rb.uniform(0, 1), rb.uniform(0, 7), rb.uniform(0.55, 1.1), rb.uniform(0, 6.28)))

    def setter(sid, i):
        on = PROJ and sid in shots and i >= shots[sid][0]
        ts = i / 24
        k = 0.0 if not on else min(1.0, (i - shots[sid][0]) / max(1, shots[sid][1] - shots[sid][0]))
        for n_, (fk, lx, ld, z0, sp, ph) in enumerate(fl):
            show = on and n_ < k * len(fl)
            fk.hide_render = not show
            if show:
                base = KEEP[sid]
                dist = 1.7 + ld * 6.0
                w = base @ Vector((lx * dist * 0.42 + 0.08 * math.sin(ts * 1.3 + ph), 0, -dist))
                w.z = base.translation.z + 3.2 - ((z0 + ts * sp * 0.9) % 6.4)
                fk.location = w
                fk.rotation_euler = cam.rotation_euler
    return setter


def fx_leaves(center, shots, n=16, top=6.0, spread=1.8, colors=("#e9b93a", "#7fb24a", "#d98a3a"), size=0.09, seed=4):
    """leaves tumbling down around a tree. center: (x, y) of the crown; shots: ids where they show."""
    rb = random.Random(seed)
    ms = [flat("leafc%d" % j, c_) for j, c_ in enumerate(colors)]
    lv = []
    for k_ in range(n):
        lf = poly("leaf", [(-size, 0, 0), (0, size / 2, 0), (size, 0, 0), (0, -size / 2, 0)], ms[k_ % len(ms)])
        lv.append((lf, rb.uniform(-spread, spread), rb.uniform(-spread, spread), rb.uniform(0, top), rb.uniform(0.7, 1.2), rb.uniform(0, 6.28)))

    def setter(sid, i):
        on = PROJ and sid in shots
        ts = i / 24
        for lf, dx, dy, z0, sp, ph in lv:
            lf.hide_render = not on
            if on:
                lf.location = (center[0] + dx + 0.35 * math.sin(ts * 1.6 + ph), center[1] + dy + 0.3 * math.cos(ts * 1.3 + ph), top - ((z0 + ts * sp * 1.1) % top))
                lf.rotation_euler = (ts * 2.1 * sp + ph, ts * 1.4 + ph, ts * 0.9 + ph)
    return setter


def fx_birds(paths, n=7, color="#2a2c33", span=0.95, seed=3):
    """a small flock crossing the sky. paths: id → (start point, velocity m/s)."""
    rb = random.Random(seed)
    m_ = flat("birdm", color)
    birds = []
    for k_ in range(n):
        root = bpy.data.objects.new("bird", None)
        col.objects.link(root)
        wings = []
        for e in (-1, 1):
            w_ = poly("birdw", [(0, -0.22, 0), (0, 0.3, 0), (e * span, -0.05, 0), (e * span * 0.53, 0.12, 0)], m_)
            w_.parent = root
            wings.append((w_, e))
        birds.append((root, wings, rb.uniform(0, 6.28), rb.uniform(7, 9.5), k_))

    def setter(sid, i):
        on = PROJ and sid in paths
        ts = i / 24
        for root, wings, ph, hz, k_ in birds:
            for w_, e in wings:
                w_.hide_render = not on
            if not on:
                continue
            p0_, v_ = Vector(paths[sid][0]), Vector(paths[sid][1])
            off = Vector(((k_ % 3) * -2.3 - (k_ // 3) * 1.1, (k_ % 2) * 2.5, ((k_ * 37) % 5) * 0.7 - (k_ // 3) * 1.6))
            root.location = p0_ + off + v_ * ts + Vector((0, 0, 0.25 * math.sin(ts * 2 + ph)))
            root.rotation_euler = (0.9, 0, math.atan2(v_.y, v_.x) - math.pi / 2)  # tipped so the wings show from below
            fl_ = 0.75 * math.sin(ts * hz + ph)
            for w_, e in wings:
                w_.rotation_euler = (0, -e * fl_, 0)
    return setter


def fx_motes(lo, hi, shots, n=90, color="#fff0c4", seed=5):
    """dust motes drifting in window light inside the box lo..hi (indoor sets)."""
    rb = random.Random(seed)
    m_ = flat("mote", color)
    mo = []
    for _ in range(n):
        s_ = rb.uniform(0.003, 0.006)
        ob_ = poly("mote", [(s_ * math.cos(a_ * math.tau / 8), s_ * math.sin(a_ * math.tau / 8), 0) for a_ in range(8)], m_)
        mo.append((ob_, Vector((rb.uniform(lo[0], hi[0]), rb.uniform(lo[1], hi[1]), rb.uniform(lo[2], hi[2]))), rb.uniform(0, 6.28), rb.uniform(0.5, 1.2)))

    def setter(sid, i):
        on = PROJ and sid in shots
        ts = i / 24
        for ob_, p_, ph_, sp_ in mo:
            ob_.hide_render = not on
            if on:
                ob_.location = p_ + Vector((0.06 * math.sin(ts * 1.1 * sp_ + ph_), 0.05 * math.cos(ts * 0.9 * sp_ + ph_), 0.05 * sp_ * ts + 0.03 * math.sin(ts * 1.7 + ph_)))
                ob_.rotation_euler = cam.rotation_euler
    return setter
