#!/usr/bin/env python3
"""STARBRICK - a 20 second procedural sci-fi brick film.

Every model, material, light, camera move and animation in the film is built
by this script. Bricks are modelled to real system dimensions (8 mm stud pitch,
9.6 mm brick, 3.2 mm plate) with hollow undersides, tubes, bevelled edges,
textured slope faces and slight per-brick colour variation, then rendered in
Cycles.

Run with the standalone ``bpy`` module (Blender 4.5):

    python video/starbrick.py --shot 2 --out renders/shot2 [--preview]

Shots (24 fps, 480 frames in total):
    1  0-3 s   Sunrise over a brick-built planet
    2  3-8 s   Hero starfighter flyby
    3  8-13 s  Zero-G assembly of an orbital station
    4  13-17 s Dogfight - laser hit, the enemy ship blows apart into bricks
    5  17-20 s Title: the debris assembles into STARBRICK
"""
import argparse
import math
import os
import random
import sys

import bpy  # must be imported before bmesh/mathutils
import bmesh
from mathutils import Euler, Matrix, Vector, noise

FPS = 24
RES = (1280, 536)          # 2.39:1, letterboxed into 1280x720 at assembly
PLATE = 0.4                # one unit = 8 mm stud pitch
BRICK = 1.2
GAP = 0.012                # clearance between neighbouring bricks
BEV = 0.028
STUD_R, STUD_H = 0.3, 0.2125
TOP_T, WALL_T = 0.125, 0.15
GLARE_TYPE, GLARE_SIZE = "FOG_GLOW", 0.8
TOY = 0.008                # metres per unit: lens apertures use real toy scale

SHOT_FRAMES = {1: 72, 2: 120, 3: 120, 4: 96, 5: 72}
PLANET_R = 26.0

# --------------------------------------------------------------------------
# Colours (sRGB hex of the classic ABS palette)
# --------------------------------------------------------------------------
COL = {
    "white": "F2F3F2", "lgray": "A0A5A9", "dgray": "6C6E68", "black": "1B1E22",
    "red": "C91A09", "dred": "720E0F", "blue": "0055BF", "dblue": "0A3463",
    "orange": "FE8A18", "yellow": "F2CD37", "green": "237841",
    "bgreen": "4B9F4A", "tan": "E4CD9E", "dtan": "958A73", "sand": "6074A1",
    "teal": "069D9F", "lime": "BBE90B",
}
TRANS = {
    "t_lblue": "AEEFEC", "t_clear": "FCFCFC", "t_orange": "F08F1C",
    "t_red": "C91A09", "t_dblue": "0020A0", "t_yellow": "F5CD2F",
    "t_green": "84B68D", "t_smoke": "635F52",
}


def lin(hexstr):
    c = [int(hexstr[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


# --------------------------------------------------------------------------
# Scene reset & render settings
# --------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.denoising_prefilter = "ACCURATE"
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 12
    sc.cycles.volume_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 4.0
    sc.cycles.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.film_transparent = False
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    MATS.clear()
    PARTS.clear()
    return sc


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
MATS = {}


def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return nt, out


def _abs_surface(nt, color, rough=(0.12, 0.19), bump=0.02, bump_scale=140,
                 sss=0.10):
    """Moulded ABS: slight subsurface, IOR 1.54, soft roughness variation,
    micro surface undulation and per-brick colour drift."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    off = nt.nodes.new("ShaderNodeVectorMath")
    off.operation = "MULTIPLY_ADD"
    nt.links.new(tc.outputs["Object"], off.inputs[0])
    off.inputs[1].default_value = (1, 1, 1)
    rnd3 = nt.nodes.new("ShaderNodeCombineXYZ")
    for i in range(3):
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = "MULTIPLY"
        m.inputs[1].default_value = 97.0 * (i + 1)
        nt.links.new(oi.outputs["Random"], m.inputs[0])
        nt.links.new(m.outputs[0], rnd3.inputs[i])
    nt.links.new(rnd3.outputs[0], off.inputs[2])

    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.2
    nz.inputs["Detail"].default_value = 2.0
    nt.links.new(off.outputs[0], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = 0.3
    mr.inputs[2].default_value = 0.7
    mr.inputs[3].default_value = rough[0]
    mr.inputs[4].default_value = rough[1]
    nt.links.new(nz.outputs["Fac"], mr.inputs[0])

    fine = nt.nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = bump_scale
    fine.inputs["Detail"].default_value = 2.0
    nt.links.new(off.outputs[0], fine.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.01
    nt.links.new(fine.outputs["Fac"], bp.inputs["Height"])

    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Color"].default_value = (*color, 1)
    vm = nt.nodes.new("ShaderNodeMapRange")
    vm.inputs[3].default_value = 0.955
    vm.inputs[4].default_value = 1.045
    nt.links.new(oi.outputs["Random"], vm.inputs[0])
    nt.links.new(vm.outputs[0], hsv.inputs["Value"])

    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(hsv.outputs[0], bs.inputs["Base Color"])
    nt.links.new(mr.outputs[0], bs.inputs["Roughness"])
    nt.links.new(bp.outputs[0], bs.inputs["Normal"])
    bs.inputs["IOR"].default_value = 1.54
    bs.inputs["Subsurface Weight"].default_value = sss
    bs.inputs["Subsurface Radius"].default_value = tuple(0.2 + 0.8 * c for c in color)
    bs.inputs["Subsurface Scale"].default_value = 0.06
    return bs, oi


def mat_solid(name, textured=False):
    key = (name, "tex" if textured else "solid")
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(f"{name}_{key[1]}")
    nt, out = _nodes(m)
    color = lin(COL[name])
    if textured:  # the grainy spark-eroded finish of slope faces
        bs, _ = _abs_surface(nt, color, rough=(0.42, 0.55), bump=0.12,
                             bump_scale=420)
    else:
        bs, _ = _abs_surface(nt, color)
    nt.links.new(bs.outputs[0], out.inputs[0])
    MATS[key] = m
    return m


def mat_trans(name, glow=0.0):
    key = (name, "glow%.1f" % glow)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(f"{name}_{key[1]}")
    nt, out = _nodes(m)
    color = lin(TRANS[name])
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Transmission Weight"].default_value = 1.0
    bs.inputs["Roughness"].default_value = 0.03
    bs.inputs["IOR"].default_value = 1.52
    if glow > 0:
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(oi.outputs["Color"], sep.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = glow
        nt.links.new(sep.outputs[0], mul.inputs[0])
        bs.inputs["Emission Color"].default_value = (*color, 1)
        nt.links.new(mul.outputs[0], bs.inputs["Emission Strength"])
    nt.links.new(bs.outputs[0], out.inputs[0])
    MATS[key] = m
    return m


def mat_metal(name, hexcol, rough=0.16):
    key = (name, "metal")
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    nt, out = _nodes(m)
    bs, _ = _abs_surface(nt, lin(hexcol), rough=(rough, rough + 0.08),
                         bump=0.015, sss=0.0)
    bs.inputs["Metallic"].default_value = 1.0
    nt.links.new(bs.outputs[0], out.inputs[0])
    MATS[key] = m
    return m


def mat_glow_additive(name, rgb, strength, falloff=2.0, axial=False):
    """Additive emissive shell: bright at grazing core, fades at the rim.
    Strength is scaled by the object colour's red channel so it can be
    keyframed per object."""
    key = (name, "add")
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    nt, out = _nodes(m)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = falloff
    nt.links.new(inv.outputs[0], pw.inputs[0])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(oi.outputs["Color"], sep.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(pw.outputs[0], mul.inputs[0])
    nt.links.new(sep.outputs[0], mul.inputs[1])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.inputs[1].default_value = strength
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    if axial:  # fade along the local axis (generated z: 0 far end -> 1 origin)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sx = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sx.inputs[0])
        ap = nt.nodes.new("ShaderNodeMath")
        ap.operation = "POWER"
        ap.inputs[1].default_value = 2.5
        nt.links.new(sx.outputs["Z"], ap.inputs[0])
        m3 = nt.nodes.new("ShaderNodeMath")
        m3.operation = "MULTIPLY"
        nt.links.new(mul2.outputs[0], m3.inputs[0])
        nt.links.new(ap.outputs[0], m3.inputs[1])
        mul2 = m3
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    nt.links.new(mul2.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    MATS[key] = m
    return m


# --------------------------------------------------------------------------
# Part geometry (all generated, cached and shared between instances)
# --------------------------------------------------------------------------
PARTS = {}


def lathe(bm, prof, cx=0.0, cy=0.0, z0=0.0, segs=32, axis_x=False):
    """Surface of revolution around z. prof = [(r, z), ...] walked so that
    normals face outward. Horizontal bands are flat shaded, the rest smooth."""
    rings = []
    for r, z in prof:
        if r < 1e-6:
            rings.append([bm.verts.new((cx, cy, z0 + z))])
        else:
            rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * i / segs),
                                        cy + r * math.sin(2 * math.pi * i / segs),
                                        z0 + z)) for i in range(segs)])
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        flat = abs(prof[k][1] - prof[k + 1][1]) < 1e-6
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1 and len(b) == 1:
                continue
            if len(b) == 1:
                f = bm.faces.new((a[i], a[j], b[0]))
            elif len(a) == 1:
                f = bm.faces.new((a[0], b[j], b[i]))
            else:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.smooth = not flat


def stud_profile(r=STUD_R, h=STUD_H, b=0.03):
    p = [(r, 0.0), (r, h - b)]
    for t in (30, 60):
        a = math.radians(t)
        p.append((r - b + b * math.cos(a), h - b + b * math.sin(a)))
    p += [(r - b, h), (0.0, h)]
    return p


def rounded_cyl_profile(r, h, b=0.035, bottom=True):
    """Closed cylinder r x h with small rounded top (and bottom) edges."""
    p = []
    if bottom:
        p.append((0.0, 0.0))
        p.append((r - b, 0.0))
        for t in (-60, -30):
            a = math.radians(t)
            p.append((r - b + b * math.cos(a), b + b * math.sin(a)))
        p.append((r, b))
    else:
        p.append((r, 0.0))
    p.append((r, h - b))
    for t in (30, 60):
        a = math.radians(t)
        p.append((r - b + b * math.cos(a), h - b + b * math.sin(a)))
    p += [(r - b, h), (0.0, h)]
    return p


def _bevel_all(bm, offset=BEV):
    bm.normal_update()
    res = bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=offset,
                          offset_type="OFFSET", segments=3, profile=0.5,
                          affect="EDGES", clamp_overlap=True)
    for f in bm.faces:
        f.smooth = False
    for f in res["faces"]:
        f.smooth = True


def _finish(bm, key):
    me = bpy.data.meshes.new(key)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(None)
    me.materials.append(None)
    PARTS[key] = me
    return me


def part_brick(l, w, hp, studs=True, hollow=True):
    """Rectangular brick/plate/tile, l along x, w along y, hp in plates.
    Origin at the centre of the bottom face."""
    key = f"brick_{l}x{w}x{hp}_{int(studs)}{int(hollow)}"
    if key in PARTS:
        return PARTS[key]
    h = hp * PLATE
    bm = bmesh.new()
    res = bmesh.ops.create_cube(bm, size=1.0)
    for v in res["verts"]:
        v.co.x = (l / 2 - GAP) if v.co.x > 0 else -(l / 2 - GAP)
        v.co.y = (w / 2 - GAP) if v.co.y > 0 else -(w / 2 - GAP)
        v.co.z = h if v.co.z > 0 else 0.0
    bm.normal_update()
    if hollow:
        bottom = [f for f in bm.faces if f.normal.z < -0.9]
        bmesh.ops.inset_region(bm, faces=bottom, thickness=WALL_T, depth=0.0,
                               use_even_offset=True)
        bmesh.ops.inset_region(bm, faces=bottom, thickness=0.0, depth=0.0)
        for v in bottom[0].verts:
            v.co.z = h - TOP_T
    _bevel_all(bm)
    if studs:
        for i in range(l):
            for j in range(w):
                lathe(bm, stud_profile(), i + 0.5 - l / 2, j + 0.5 - w / 2, h)
    if hollow:
        ch = h - TOP_T
        if l >= 2 and w >= 2:
            for i in range(1, l):
                for j in range(1, w):
                    lathe(bm, [(0.3, ch), (0.3, 0.0), (0.407, 0.0), (0.407, ch)],
                          i - l / 2, j - w / 2, 0.0, segs=24)
        elif l >= 2 or w >= 2:
            n = max(l, w)
            for i in range(1, n):
                x, y = (i - l / 2, 0.0) if l > 1 else (0.0, i - w / 2)
                lathe(bm, [(0.0, 0.0), (0.2, 0.0), (0.2, ch)], x, y, 0.0, segs=16)
    return _finish(bm, key)


def _prism(bm, poly, depth, axis="z", lo=0.0):
    """Extrude a convex polygon. axis z: poly in xy, extruded z in [lo, lo+depth].
    axis y: poly in xz, extruded y in [lo, lo+depth]."""
    def mk(p, d):
        if axis == "z":
            return bm.verts.new((p[0], p[1], lo + d))
        return bm.verts.new((p[0], lo + d, p[1]))
    a = [mk(p, 0) for p in poly]
    b = [mk(p, depth) for p in poly]
    bm.faces.new(a)
    bm.faces.new(b)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def _inside(poly, x, y, margin):
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
               for i in range(n))
    s = 1 if area > 0 else -1
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        L = math.hypot(ex, ey)
        cross = (ex * (y - y0) - ey * (x - x0)) / L
        if s * cross < margin:
            return False
    return True


def part_wedge(poly, hp, studs=True, key=None):
    """Plate/brick with an arbitrary convex footprint (wedge plates, wings).
    Poly is in absolute stud coordinates; origin stays at (0,0,0)."""
    key = key or "wedge_" + "_".join(f"{x:.2f},{y:.2f}" for x, y in poly) + f"_{hp}{int(studs)}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    # shrink the footprint slightly for the clearance gap
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    sp = [(x - (x - cx) * 0.004 - math.copysign(GAP, x - cx) * 0.5,
           y - (y - cy) * 0.004 - math.copysign(GAP, y - cy) * 0.5) for x, y in poly]
    _prism(bm, sp, hp * PLATE, "z")
    _bevel_all(bm)
    if studs:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        for i in range(math.floor(min(xs)), math.ceil(max(xs))):
            for j in range(math.floor(min(ys)), math.ceil(max(ys))):
                if _inside(poly, i + 0.5, j + 0.5, 0.36):
                    lathe(bm, stud_profile(), i + 0.5, j + 0.5, hp * PLATE)
    return _finish(bm, key)


def part_slope(l, w, hp=3, lip=0.5):
    """Slope brick descending towards +x; top row of studs at the back."""
    key = f"slope_{l}x{w}x{hp}"
    if key in PARTS:
        return PARTS[key]
    h = hp * PLATE
    bm = bmesh.new()
    x0, x1 = -l / 2 + GAP, l / 2 - GAP
    prof = [(x0, 0.0), (x1, 0.0), (x1, lip * PLATE), (x0 + 1.0, h), (x0, h)]
    _prism(bm, prof, w - 2 * GAP, "y", lo=-w / 2 + GAP)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.x > 0.2 and f.normal.z > 0.2:
            f.material_index = 1
    _bevel_all(bm)
    for j in range(w):
        lathe(bm, stud_profile(), x0 + 0.5 - GAP, j + 0.5 - w / 2, h)
    return _finish(bm, key)


def part_fin(prof, thick=1.0, key=None):
    """Vertical tile-like fin: profile in xz, thickness along y (centred)."""
    key = key or "fin_" + "_".join(f"{x:.2f},{z:.2f}" for x, z in prof) + f"_{thick}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    _prism(bm, prof, thick - 2 * GAP, "y", lo=-thick / 2 + GAP)
    _bevel_all(bm)
    return _finish(bm, key)


def part_round(d, hp, studs=True):
    """Round brick/plate, diameter d studs (1 or 2)."""
    key = f"round_{d}x{hp}_{int(studs)}"
    if key in PARTS:
        return PARTS[key]
    h = hp * PLATE
    bm = bmesh.new()
    lathe(bm, rounded_cyl_profile(d / 2 - GAP, h), segs=40 if d > 1 else 32)
    if studs:
        if d == 1:
            lathe(bm, stud_profile(), 0, 0, h)
        else:
            for i in (-0.5, 0.5):
                for j in (-0.5, 0.5):
                    lathe(bm, stud_profile(), i, j, h)
    return _finish(bm, key)


def part_bar(length, r=0.2):
    key = f"bar_{length}_{r}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    lathe(bm, rounded_cyl_profile(r, length, b=r * 0.45), segs=20)
    return _finish(bm, key)


def part_engine():
    """Stack of three round 2x2 bricks laid on its side with a flared nozzle."""
    key = "engine"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    r = 1.0 - GAP
    for k in range(3):
        lathe(bm, rounded_cyl_profile(r, BRICK - 2 * GAP), z0=k * BRICK + GAP, segs=48)
    # nozzle bell (metal), inner cavity where the glow disc sits
    lathe(bm, [(0.55, -0.02), (0.72, -0.35), (0.86, -0.8), (0.92, -0.8),
               (0.78, -0.33), (0.62, 0.02)], segs=48)
    for f in bm.faces:
        if min(v.co.z for v in f.verts) < -0.01:
            f.material_index = 1
    return _finish(bm, key)


def part_disc(r, t=0.08):
    key = f"disc_{r}_{t}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    lathe(bm, rounded_cyl_profile(r, t, b=0.02), segs=40)
    return _finish(bm, key)


def part_sphere(r=1.0, segs=48, rings=24):
    key = f"sphere_{r}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    for f in bm.faces:
        f.smooth = True
    return _finish(bm, key)


def part_capsule(r, length):
    key = f"capsule_{r}_{length}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    prof = [(0.0, 0.0)]
    for t in range(1, 8):
        a = math.radians(-90 + t * 90 / 8)
        prof.append((r * math.cos(a), r + r * math.sin(a)))
    prof.append((r, r))
    prof.append((r, length - r))
    for t in range(1, 8):
        a = math.radians(t * 90 / 8)
        prof.append((r * math.cos(a), length - r + r * math.sin(a)))
    prof.append((0.0, length))
    lathe(bm, prof, segs=16)
    for f in bm.faces:
        f.smooth = True
    return _finish(bm, key)


def part_plume(r, length):
    """Exhaust cone along -z from origin."""
    key = f"plume_{r}_{length}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    prof = [(0.0, -length), (r * 0.35, -length * 0.75), (r * 0.8, -length * 0.35),
            (r, -length * 0.08), (r * 0.9, 0.0), (0.0, 0.0)]
    lathe(bm, prof, segs=24)
    for f in bm.faces:
        f.smooth = True
    return _finish(bm, key)


def part_ring(r, width):
    key = f"ring_{r}_{width}"
    if key in PARTS:
        return PARTS[key]
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=96, radius=r)
    ring_outer = list(bm.verts)
    inner = [bm.verts.new((v.co.x * (r - width) / r, v.co.y * (r - width) / r, 0)) for v in ring_outer]
    n = len(inner)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((ring_outer[i], ring_outer[j], inner[j], inner[i]))
        f.smooth = True
    return _finish(bm, key)


# --------------------------------------------------------------------------
# Object helpers
# --------------------------------------------------------------------------
def coll_new(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def place(mesh, mat, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, coll=None,
          mat2=None, name="part"):
    ob = bpy.data.objects.new(name, mesh)
    (coll or bpy.context.scene.collection).objects.link(ob)
    for i, slot in enumerate(ob.material_slots):
        slot.link = "OBJECT"
        slot.material = mat if i == 0 or mat2 is None else mat2
    ob.location = loc
    ob.rotation_euler = rot
    if parent is not None:
        ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0), parent=None, coll=None):
    ob = bpy.data.objects.new(name, None)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    ob.parent = parent
    return ob


def kf(ob, f, loc=None, rot=None, scale=None, color=None):
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=f)
    if rot is not None:
        ob.rotation_euler = rot
        ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        ob.scale = scale if hasattr(scale, "__len__") else (scale,) * 3
        ob.keyframe_insert("scale", frame=f)
    if color is not None:
        ob.color = color if len(color) == 4 else (*color, 1)
        ob.keyframe_insert("color", frame=f)


def ease_io(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** p


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


class Model:
    """Collects bricks under one parent empty. Positions are stud units with
    the part origin at the centre of its bottom face."""

    def __init__(self, name, coll, loc=(0, 0, 0)):
        self.root = empty(name, loc, coll=coll)
        self.coll = coll
        self.parts = []

    def add(self, mesh, color, x, y, zp, rz=0.0, rx=0.0, ry=0.0, mat=None, mat2=None):
        if mat is None:
            if color in TRANS:
                mat = mat_trans(color)
            else:
                mat = mat_solid(color)
                mat2 = mat2 or mat_solid(color, textured=True)
        ob = place(mesh, mat, (x, y, zp * PLATE), (rx, ry, rz), self.root,
                   self.coll, mat2)
        self.parts.append(ob)
        return ob

    def brick(self, x0, y0, zp, l, w, hp, color, **kw):
        """Axis aligned brick with footprint corner (x0, y0)."""
        return self.add(part_brick(l, w, hp, **kw), color, x0 + l / 2, y0 + w / 2, zp)


# --------------------------------------------------------------------------
# World / lighting / camera / compositing
# --------------------------------------------------------------------------
def world_space(star_gain=1.0, nebula=1.0, ambient=0.0006):
    w = bpy.data.worlds.new("space")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vec = tc.outputs["Generated"]

    def star_layer(scale, radius, sharp, gain, seedoff):
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Location"].default_value = (seedoff, seedoff * 2, seedoff * 3)
        nt.links.new(vec, mp.inputs[0])
        vo = nt.nodes.new("ShaderNodeTexVoronoi")
        vo.voronoi_dimensions = "3D"
        vo.inputs["Scale"].default_value = scale
        nt.links.new(mp.outputs[0], vo.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs[1].default_value = 0.0
        mr.inputs[2].default_value = radius
        mr.inputs[3].default_value = 1.0
        mr.inputs[4].default_value = 0.0
        nt.links.new(vo.outputs["Distance"], mr.inputs[0])
        sh = nt.nodes.new("ShaderNodeMath")
        sh.operation = "POWER"
        sh.inputs[1].default_value = 2.0
        nt.links.new(mr.outputs[0], sh.inputs[0])
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(vo.outputs["Color"], sep.inputs[0])
        br = nt.nodes.new("ShaderNodeMath")
        br.operation = "POWER"
        br.inputs[1].default_value = sharp
        nt.links.new(sep.outputs[0], br.inputs[0])
        m1 = nt.nodes.new("ShaderNodeMath")
        m1.operation = "MULTIPLY"
        nt.links.new(sh.outputs[0], m1.inputs[0])
        nt.links.new(br.outputs[0], m1.inputs[1])
        m2 = nt.nodes.new("ShaderNodeMath")
        m2.operation = "MULTIPLY"
        m2.inputs[1].default_value = gain * star_gain
        nt.links.new(m1.outputs[0], m2.inputs[0])
        # slight colour temperature variation
        tint = nt.nodes.new("ShaderNodeMix")
        tint.data_type = "RGBA"
        tint.inputs[6].default_value = (1.0, 0.78, 0.6, 1)
        tint.inputs[7].default_value = (0.7, 0.82, 1.0, 1)
        nt.links.new(sep.outputs[1], tint.inputs[0])
        cm = nt.nodes.new("ShaderNodeVectorMath")
        cm.operation = "SCALE"
        nt.links.new(tint.outputs[2], cm.inputs[0])
        nt.links.new(m2.outputs[0], cm.inputs["Scale"])
        return cm.outputs[0]

    s1 = star_layer(420, 0.12, 14.0, 14.0, 0.0)
    s2 = star_layer(110, 0.06, 60.0, 260.0, 5.3)

    # faint nebula / milky band
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(vec, nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    e = cr.color_ramp.elements
    e[0].position, e[0].color = 0.45, (0, 0, 0, 1)
    e[1].position, e[1].color = 0.78, (0.10, 0.035, 0.16, 1)
    mid = e.new(0.62)
    mid.color = (0.012, 0.03, 0.06, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs[0])
    nb = nt.nodes.new("ShaderNodeVectorMath")
    nb.operation = "SCALE"
    nb.inputs["Scale"].default_value = 0.12 * nebula
    nt.links.new(cr.outputs[0], nb.inputs[0])

    a1 = nt.nodes.new("ShaderNodeVectorMath")
    a1.operation = "ADD"
    nt.links.new(s1, a1.inputs[0])
    nt.links.new(s2, a1.inputs[1])
    a2 = nt.nodes.new("ShaderNodeVectorMath")
    a2.operation = "ADD"
    nt.links.new(a1.outputs[0], a2.inputs[0])
    nt.links.new(nb.outputs[0], a2.inputs[1])

    cam_bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(a2.outputs[0], cam_bg.inputs["Color"])
    amb = nt.nodes.new("ShaderNodeBackground")
    amb.inputs["Color"].default_value = (0.35, 0.45, 0.7, 1)
    amb.inputs["Strength"].default_value = ambient
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(amb.outputs[0], mix.inputs[1])
    nt.links.new(cam_bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])


def sun(name, direction, strength, color=(1, 1, 1), angle=0.6):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.color = color
    ld.angle = math.radians(angle)
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    d = Vector(direction).normalized()
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return ob


def area(name, loc, target, power, size=10.0, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.size = size
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.visible_camera = False
    look_at(ob, target)
    return ob


def point(name, loc, power, color=(1, 1, 1), radius=0.3, parent=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = power
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.parent = parent
    ob.visible_camera = False
    return ob


def look_at(ob, target):
    d = Vector(target) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(lens=35, fstop=4.0, focus=None, sensor=36):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.1
    cd.clip_end = 20000
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop * TOY
    cd.dof.aperture_blades = 7
    cd.dof.aperture_rotation = math.radians(12)
    if focus is not None:
        cd.dof.focus_object = focus
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def aim_camera_frames(cam, frames, pos_fn, target_fn, roll_fn=None):
    """Bake a camera move frame by frame from position/target functions."""
    for f in frames:
        p = Vector(pos_fn(f))
        t = Vector(target_fn(f))
        q = (t - p).to_track_quat("-Z", "Y")
        e = q.to_euler()
        if roll_fn:
            e = (q @ Euler((0, 0, roll_fn(f))).to_quaternion()).to_euler()
        kf(cam, f, loc=p, rot=e)
    fix_euler(cam)


def fix_euler(ob):
    """Unwrap baked euler keys so interpolation never spins the long way."""
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        if fc.data_path != "rotation_euler":
            continue
        prev = None
        for kp in fc.keyframe_points:
            if prev is not None:
                while kp.co[1] - prev > math.pi:
                    kp.co[1] -= 2 * math.pi
                while kp.co[1] - prev < -math.pi:
                    kp.co[1] += 2 * math.pi
            prev = kp.co[1]
        fc.update()


def _fcurves(action):
    try:
        return list(action.fcurves)
    except AttributeError:
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out += list(bag.fcurves)
        return out


def compositing(bloom=0.6, streaks=0.0, dispersion=0.012, threshold=2.5):
    sc = bpy.context.scene
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    cur = rl.outputs["Image"]

    def glare(src, gtype, **inputs):
        g = nt.nodes.new("CompositorNodeGlare")
        g.glare_type = gtype
        g.quality = "HIGH"
        for k, v in inputs.items():
            if k in g.inputs:
                g.inputs[k].default_value = v
        nt.links.new(src, g.inputs["Image"])
        return g.outputs[0]

    cur = glare(cur, GLARE_TYPE, Threshold=threshold, Strength=bloom, Size=GLARE_SIZE,
                Smoothness=0.5)
    if streaks > 0:
        cur = glare(cur, "STREAKS", Threshold=threshold * 3, Strength=streaks,
                    Streaks=2, **{"Streaks Angle": 0.0, "Fade": 0.93,
                                  "Tint": (0.55, 0.75, 1.0, 1.0)})
    ld = nt.nodes.new("CompositorNodeLensdist")
    ld.inputs["Distortion"].default_value = -0.008
    ld.inputs["Dispersion"].default_value = dispersion
    ld.use_fit = True if hasattr(ld, "use_fit") else None
    nt.links.new(cur, ld.inputs["Image"])
    cb = nt.nodes.new("CompositorNodeColorBalance")
    cb.correction_method = "LIFT_GAMMA_GAIN"
    cb.lift = (0.985, 1.0, 1.02)
    cb.gamma = (1.0, 1.0, 1.0)
    cb.gain = (1.03, 1.0, 0.97)
    nt.links.new(ld.outputs[0], cb.inputs["Image"])
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(cb.outputs[0], comp.inputs["Image"])


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
def build_planet(coll, radius=PLANET_R, seed=3):
    """Voxel planet made from 1x1 bricks plus a floating cloud layer of 1x1
    plates and a thin lit atmosphere shell. Returns the root empty."""
    root = empty("planet", coll=coll)
    rng = random.Random(seed)
    off = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))
    b11 = part_brick(1, 1, 3, hollow=False)
    p11 = part_brick(1, 1, 1, hollow=False)
    zr = int(radius / BRICK) + 2
    ir = int(radius) + 2
    for k in range(-zr, zr + 1):
        z = (k + 0.5) * BRICK
        for i in range(-ir, ir):
            for j in range(-ir, ir):
                p = Vector((i + 0.5, j + 0.5, z))
                d = p.length
                if not (radius - 1.6 < d <= radius):
                    continue
                n = p.normalized()
                e = 0.0
                amp, fr = 1.0, 1.2
                for _ in range(4):
                    e += amp * noise.noise(n * fr + off)
                    amp *= 0.5
                    fr *= 2.1
                lat = abs(n.z)
                if lat > 0.86 - 0.08 * e:
                    c = "white"
                elif e < -0.18:
                    c = "dblue"
                elif e < 0.04:
                    c = "blue"
                elif e < 0.1:
                    c = "tan"
                elif e < 0.32:
                    c = "green" if noise.noise(n * 6 + off) > -0.1 else "bgreen"
                elif e < 0.5:
                    c = "dtan"
                else:
                    c = "white"
                m = mat_solid(c)
                if c in ("green", "bgreen", "tan") and rng.random() < 0.04:
                    m = mat_trans("t_yellow", 1.2)   # city lights
                place(b11, m, (p.x, p.y, z - BRICK / 2), parent=root,
                      coll=coll, mat2=mat_solid(c, True), name="pv")
    # clouds
    cmat = mat_solid("white")
    rc = radius + 1.2
    for k in range(-int(rc / PLATE), int(rc / PLATE) + 1, 3):
        z = k * PLATE
        for i in range(-int(rc) - 1, int(rc) + 1):
            for j in range(-int(rc) - 1, int(rc) + 1):
                p = Vector((i + 0.5, j + 0.5, z))
                d = p.length
                if not (rc - 0.6 < d <= rc + 0.6):
                    continue
                n = p.normalized()
                cn = noise.noise(n * 2.6 + off * 1.7) + 0.5 * noise.noise(n * 6 + off)
                if cn > 0.55 and abs(n.z) < 0.8:
                    place(p11, cmat, (p.x, p.y, z), parent=root, coll=coll,
                          mat2=cmat, name="cloud")
    return root


def atmosphere(coll, parent, radius, sun_dir):
    """Scattering rim: additive emission, strongest at grazing angles on the
    sunlit side."""
    m = bpy.data.materials.new("atmo")
    nt, out = _nodes(m)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    rim = nt.nodes.new("ShaderNodeMath")
    rim.operation = "POWER"
    rim.inputs[1].default_value = 3.5
    nt.links.new(lw.outputs["Facing"], rim.inputs[0])
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = Vector(sun_dir).normalized()
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    lit = nt.nodes.new("ShaderNodeMapRange")
    lit.inputs[1].default_value = -0.15
    lit.inputs[2].default_value = 0.8
    nt.links.new(dot.outputs["Value"], lit.inputs[0])
    # forward scattering: looking towards the sun through the limb
    vdir = nt.nodes.new("ShaderNodeVectorMath")
    vdir.operation = "DOT_PRODUCT"
    vdir.inputs[1].default_value = Vector(sun_dir).normalized()
    nt.links.new(geo.outputs["Incoming"], vdir.inputs[0])
    fwd = nt.nodes.new("ShaderNodeMapRange")
    fwd.inputs[1].default_value = 0.0
    fwd.inputs[2].default_value = -1.0
    nt.links.new(vdir.outputs["Value"], fwd.inputs[0])
    fwp = nt.nodes.new("ShaderNodeMath")
    fwp.operation = "POWER"
    fwp.inputs[1].default_value = 90.0
    nt.links.new(fwd.outputs[0], fwp.inputs[0])
    fws = nt.nodes.new("ShaderNodeMath")
    fws.operation = "MULTIPLY_ADD"
    fws.inputs[1].default_value = 3.0
    nt.links.new(fwp.outputs[0], fws.inputs[0])
    nt.links.new(lit.outputs[0], fws.inputs[2])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(rim.outputs[0], mul.inputs[0])
    nt.links.new(fws.outputs[0], mul.inputs[1])
    # thin at the silhouette edge itself (fade the outermost grazing rays)
    edge = nt.nodes.new("ShaderNodeMapRange")
    edge.inputs[1].default_value = 1.0
    edge.inputs[2].default_value = 0.93
    nt.links.new(lw.outputs["Facing"], edge.inputs[0])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    nt.links.new(edge.outputs[0], mul2.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.inputs[6].default_value = (0.22, 0.5, 1.0, 1)
    tint.inputs[7].default_value = (1.0, 0.62, 0.32, 1)
    nt.links.new(fwp.outputs[0], tint.inputs[0])
    nt.links.new(tint.outputs[2], em.inputs["Color"])
    sm = nt.nodes.new("ShaderNodeMath")
    sm.operation = "MULTIPLY"
    sm.inputs[1].default_value = 1.6
    nt.links.new(mul2.outputs[0], sm.inputs[0])
    nt.links.new(sm.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    ob = place(part_sphere(1.0, 96, 48), m, parent=parent, coll=coll, name="atmo")
    ob.scale = (radius,) * 3
    ob.visible_shadow = False
    return ob


HERO = dict(main="white", second="lgray", dark="dgray", accent="red",
            canopy="t_smoke", glow="t_orange", bolt=(1.0, 0.08, 0.04),
            wing=dict(root_le=3.0, tip_le=-3.5, te=-8.0, tip_te=-8.0, span=10.0))
ENEMY = dict(main="black", second="dgray", dark="dgray", accent="dred",
             canopy="t_red", glow="t_green", bolt=(0.2, 1.0, 0.25),
             wing=dict(root_le=0.0, tip_le=4.0, te=-6.0, tip_te=-1.0, span=9.0))


def _mirror(poly, s):
    poly = [(x, y * s) for x, y in poly]
    return poly[::-1] if s < 0 else poly


def build_fighter(coll, pal, name="fighter"):
    """Original brick-built starfighter, nose along +x, built like a display
    model: layered wedge plates, tiled skins with selective exposed studs.
    Returns (model, engine glow objects, gun muzzle empties)."""
    M = Model(name, coll)
    main, sec, dark, acc = pal["main"], pal["second"], pal["dark"], pal["accent"]
    wg = pal["wing"]
    te = wg["te"]
    # keel: long pointed wedge under everything
    M.add(part_wedge([(te, -2), (6, -2), (12.5, -0.45), (12.5, 0.45), (6, 2), (te, 2)],
                     1, studs=False), dark, 0, 0, 0)
    # fuselage core
    te = int(te)
    x0 = te
    while x0 < 0:  # lower course in bricks up to 4 long
        l = min(4, -x0)
        M.brick(x0, -1, 1, l, 2, 3, main)
        x0 += l
    M.brick(0, -1, 1, 4, 2, 3, main)
    M.brick(4, -1, 1, 2, 2, 3, sec)
    x0 = te
    while x0 < -4:  # upper course behind the cockpit
        l = min(4, -4 - x0)
        M.brick(x0, -1, 4, l, 2, 3, main)
        x0 += l
    M.brick(-4, -1, 4, 2, 2, 3, dark)
    M.add(part_slope(4, 2), pal["canopy"], 0, 0, 4)
    M.brick(2, -1, 4, 4, 2, 1, main)
    M.brick(2, -1, 5, 2, 2, 1, main, studs=False)
    M.brick(4, -1, 5, 2, 2, 1, acc, studs=False)
    # nose
    M.add(part_slope(4, 2), main, 8, 0, 1)
    M.add(part_wedge([(10, -1), (12.2, -0.3), (12.2, 0.3), (10, 1)], 1, studs=False),
          acc, 0, 0, 1)
    # spine: exposed studs, greebles, antenna
    M.brick(te, -1, 7, 4, 2, 1, dark)
    M.add(part_round(1, 1), sec, -3.5, -0.5, 7)
    M.add(part_round(1, 1), acc, -3.5, 0.5, 7)
    M.add(part_bar(3.0, 0.1), mat=mat_metal("steel", "B8BCC0", 0.25),
          color=None, x=-2.5, y=-0.5, zp=7, ry=math.radians(-72))
    # tail fin
    M.add(part_fin([(te, 0), (te + 3, 0), (te + 1.1, 3.6), (te, 3.6)], 1.0), sec, 0, 0, 8)
    M.add(part_fin([(te, 3.6), (te + 1.1, 3.6), (te + 0.9, 4.0), (te, 4.0)], 1.0), acc,
          0, 0, 8)

    def le(y):
        return wg["root_le"] + (wg["tip_le"] - wg["root_le"]) * (y - 1) / (wg["span"] - 1)

    def tex(y):
        return te + (wg["tip_te"] - te) * (y - 1) / (wg["span"] - 1)

    span = wg["span"]
    muzzles, glows = [], []
    for s in (1, -1):
        # underside, flaps, tiled upper skin and leading edge stripe
        M.add(part_wedge(_mirror([(te, 1), (wg["root_le"], 1), (wg["tip_le"], span),
                                  (wg["tip_te"], span)], s), 1, studs=False), dark, 0, 0, 1)
        M.add(part_wedge(_mirror([(te, 1), (te + 1, 1), (wg["tip_te"] + 1, span),
                                  (wg["tip_te"], span)], s), 1), dark, 0, 0, 2)
        M.add(part_wedge(_mirror([(te + 1, 1), (wg["root_le"], 1), (wg["tip_le"], span),
                                  (wg["tip_te"] + 1, span)], s), 1, studs=False),
              main, 0, 0, 2)
        M.add(part_wedge(_mirror([(le(4) - 1.3, 4), (le(4), 4), (le(span), span),
                                  (le(span) - 1.3, span)], s), 1, studs=False), acc, 0, 0, 3)
        # a panel of exposed studs mid-wing for surface texture
        M.add(part_wedge(_mirror([(tex(5) + 1.5, 5), (tex(5) + 4.5, 5), (tex(8) + 4.5, 8),
                                  (tex(8) + 1.5, 8)], s), 1), sec, 0, 0, 3)
        # intake scoop at the wing root
        M.add(part_slope(2, 1), dark, 3.0, s * 1.5, 3) if wg["root_le"] > 2 else None
        # wingtip gun: round brick, barrel with collar, small muzzle lens
        yt = s * (span + 0.5)
        gx = wg["tip_te"] + 0.5
        M.add(part_round(1, 3), dark, gx, yt, 1)
        M.add(part_bar(6.5, 0.16), mat=mat_metal("gunmetal", "5A5E63", 0.22),
              color=None, x=gx - 0.5, y=yt, zp=2.5, ry=math.radians(90))
        M.add(part_round(1, 1, studs=False), sec, gx + 2.6, yt, 2.5,
              ry=math.radians(90))
        M.add(part_round(1, 1, studs=False), dark, gx + 4.2, yt, 2.5,
              ry=math.radians(90))
        tip = empty(f"muzzle{s}", (gx + 6.3, yt, 2.5 * PLATE), parent=M.root, coll=coll)
        muzzles.append(tip)
        gcol = "t_red" if pal is HERO else "t_green"
        M.add(part_disc(0.2, 0.06), None, gx + 6.0, yt, 2.5, ry=math.radians(90),
              mat=mat_trans(gcol, 6.0))
        # engine pod on a dark mounting plate
        ey = s * 3.2
        ex = te - 0.4
        M.add(part_engine(), sec, ex, ey, 6.5, ry=math.radians(90),
              mat=mat_solid(sec), mat2=mat_metal("nozzle", "3A3D41", 0.3))
        M.add(part_round(2, 1, studs=False), dark, ex + 3.6, ey, 6.5,
              ry=math.radians(90))
        M.brick(te, ey - 1, 3, 3, 2, 1, dark)
        disc = M.add(part_disc(0.62), None, ex - 0.4, ey, 6.5, ry=math.radians(90),
                     mat=mat_trans(pal["glow"], 60.0))
        glows.append(disc)
        pc = (1.0, 0.42, 0.1) if pal is HERO else (0.3, 1.0, 0.45)
        pl = place(part_plume(0.6, 4.5), mat_glow_additive(f"plume_{name}", pc, 6.0, 1.5,
                                                          axial=True),
                   (ex - 0.5, ey, 6.5 * PLATE), (0, math.radians(90), 0), M.root, coll,
                   name="plume")
        pl.visible_shadow = False
        glows.append(pl)
        lt = point(f"englight{s}", (ex - 2.2, ey, 6.5 * PLATE), 18, pc, 0.5, M.root)
        glows.append(lt)
    return M, glows, muzzles


def build_station(coll):
    """Orbital station: stacked core with lit windows, docking collar,
    solar arrays and an antenna mast. Returns list of (object, order)."""
    M = Model("station", coll)
    # base collar
    M.brick(-4, -4, 0, 8, 8, 1, "dgray")
    for x0, y0, l, w in [(-5, -3, 1, 6), (4, -3, 1, 6), (-3, -5, 6, 1), (-3, 4, 6, 1)]:
        M.brick(x0, y0, 0, l, w, 1, "lgray")
    # core: staggered running bond, windows on alternate courses
    z = 1
    for course in range(7):
        c = "white" if course not in (2, 5) else "lgray"
        if course % 2 == 0:
            M.brick(-2, -2, z, 4, 2, 3, c)
            M.brick(-2, 0, z, 4, 2, 3, c)
        else:
            M.brick(-2, -2, z, 2, 4, 3, c)
            M.brick(0, -2, z, 2, 4, 3, c)
        if course in (1, 3, 5):
            for x0, y0, l, w in [(-3, -1, 1, 2), (2, -1, 1, 2), (-1, -3, 2, 1), (-1, 2, 2, 1)]:
                ob = M.brick(x0, y0, z, l, w, 3, "t_yellow")
                ob.material_slots[0].material = mat_trans("t_yellow", 0.7)
        z += 3
    # docking ring half-way up
    M.brick(-3, -3, 7, 6, 6, 1, "dgray")
    # arms and solar panels
    for s in (1, -1):
        x0 = 2 if s > 0 else -10
        M.brick(x0, -1, 14, 8, 2, 1, "lgray")
        M.brick(x0 + (6 if s > 0 else 0), -1, 15, 2, 2, 3, "dgray")
        px = 10 if s > 0 else -18
        M.brick(px, -4, 15, 8, 8, 1, "lgray")
        for i in range(8):
            for j in range(4):
                M.brick(px + i, -4 + j * 2, 16, 1, 2, 1, "dblue", studs=False)
    # habitat ring on the arm level: 14 curved-ish 1x4 plate segments, two
    # plates thick, plus two extra spokes along y
    RR = 9.0
    for k in range(14):
        a = 2 * math.pi * (k + 0.5) / 14
        for zp, c in ((14, "lgray"), (15, "white")):
            M.add(part_brick(4, 1, 1, studs=(zp == 15)), c, RR * math.cos(a), RR * math.sin(a),
                  zp, rz=a + math.pi / 2)
    for s in (1, -1):
        M.brick(-1, 2 if s > 0 else -9, 14, 2, 7, 1, "lgray")
        M.add(part_round(2, 3), "dgray", 0, s * RR, 16)
    # top: dish + mast + beacon
    M.brick(-2, -2, z, 4, 4, 1, "dgray")
    M.add(part_round(2, 3), "lgray", 0, 0, z + 1)
    M.add(part_round(2, 1), "white", 0, 0, z + 4)
    M.add(part_bar(6.0, 0.16), mat=mat_metal("mast", "B8BCC0", 0.2), color=None,
          x=0, y=0, zp=z + 5)
    bea = M.add(part_round(1, 1, studs=False), None, 0, 0, z + 5 + 6.0 / PLATE,
                mat=mat_trans("t_red", 40.0))
    return M, bea


# --------------------------------------------------------------------------
# Loose debris (for parallax, bokeh and the final title)
# --------------------------------------------------------------------------
DEBRIS_KINDS = [(1, 2, 1), (1, 1, 3), (2, 2, 1), (1, 4, 1), (2, 3, 1), (1, 2, 3),
                (1, 1, 1), (2, 4, 1)]
DEBRIS_COLS = ["white", "lgray", "dgray", "red", "blue", "yellow", "black",
               "orange", "tan", "sand"]


def scatter_debris(coll, n, center, extent, frames, drift=0.02, seed=7, spin=1.0,
                   stream=(0, 0, 0)):
    rng = random.Random(seed)
    obs = []
    for i in range(n):
        l, w, hp = rng.choice(DEBRIS_KINDS)
        c = rng.choice(DEBRIS_COLS)
        mesh = part_brick(l, w, hp) if rng.random() > 0.15 else part_slope(2, 2)
        p = Vector(center) + Vector((rng.uniform(-1, 1) * extent[0],
                                     rng.uniform(-1, 1) * extent[1],
                                     rng.uniform(-1, 1) * extent[2]))
        r0 = Euler((rng.uniform(0, 6.3), rng.uniform(0, 6.3), rng.uniform(0, 6.3)))
        av = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * spin * 0.05
        v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * drift \
            + Vector(stream)
        ob = place(mesh, mat_solid(c), p, r0, coll=coll, mat2=mat_solid(c, True),
                   name="debris")
        f0, f1 = frames
        kf(ob, f0, loc=p, rot=r0)
        kf(ob, f1, loc=p + v * (f1 - f0),
           rot=Euler(Vector(r0) + av * (f1 - f0)))
        linearize(ob)
        obs.append(ob)
    return obs


def linearize(ob, extrapolate=True):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.extrapolation = "LINEAR" if extrapolate else "CONSTANT"


# --------------------------------------------------------------------------
# Shots
# --------------------------------------------------------------------------
def common_space(sun_dir, star_gain=1.0, ambient=0.0006, key=5.0):
    """sun_dir points from the scene towards the sun."""
    world_space(star_gain=star_gain, ambient=ambient)
    sun("key", sun_dir, key, (1.0, 0.94, 0.86), 0.5)


def sun_disc(coll, direction, dist=4000.0, size=40.0, strength=400.0):
    m = bpy.data.materials.new("sundisc")
    nt, out = _nodes(m)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.93, 0.82, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    ob = place(part_sphere(1.0), m, Vector(direction).normalized() * dist,
               coll=coll, name="sundisc")
    ob.scale = (size,) * 3
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    return ob


def shot1(sc):
    """Sunrise over the brick planet."""
    n = SHOT_FRAMES[1]
    coll = coll_new("planet")
    # sun sits behind the planet limb and rises into view
    sdir = Vector((-0.97, 0.05, 0.24)).normalized()
    common_space(sdir, star_gain=1.0, key=6.0)
    R = PLANET_R
    pl = build_planet(coll, R)
    atmosphere(coll, pl, R + 2.2, sdir)
    sun_disc(coll, sdir, 4000, 22, 900)
    area("fill", -sdir * 90 + Vector((0, -40, -20)), (0, 0, 0), 60000, 40, (0.35, 0.5, 1.0))
    cam = camera(lens=50, fstop=22.0)
    cam.data.dof.focus_distance = 52.0
    up = (Vector((0, 0, 1)) - sdir * sdir.z).normalized()
    side = sdir.cross(up)
    for f in range(1, n + 1):
        t = (f - 1) / (n - 1)
        pl.rotation_euler = (0.25, 0.0, math.radians(-8 + 10 * t))
        pl.keyframe_insert("rotation_euler", frame=f)

    def cpos(f):
        t = (f - 1) / (n - 1)
        return -sdir * lerp(60, 56, t) + up * lerp(R - 2.2, R + 2.6, ease_io(t)) \
            + side * lerp(-3.0, 1.0, t)

    aim_camera_frames(cam, range(1, n + 1, 2), cpos,
                      lambda f: cpos(f) + sdir * 100 - up * 7.0 + side * 2.0,
                      lambda f: math.radians(lerp(-5.0, -2.5, (f - 1) / (n - 1))))
    compositing(bloom=0.8, streaks=0.35, threshold=2.0)
    return n


def planet_backdrop(coll, loc, scale, sun_dir, rot=(0.25, 0, 0)):
    """Reuse the planet as a large backdrop via a collection instance."""
    pcoll = bpy.data.collections.new("planet_src")
    pl = build_planet(pcoll, PLANET_R)
    atmosphere(pcoll, pl, PLANET_R + 2.2, sun_dir)
    scale *= 18.0 / PLANET_R
    inst = bpy.data.objects.new("planet_inst", None)
    inst.instance_type = "COLLECTION"
    inst.instance_collection = pcoll
    coll.objects.link(inst)
    inst.location = loc
    inst.scale = (scale,) * 3
    inst.rotation_euler = rot
    return inst


def shot2(sc):
    """Hero flyby past camera, whip pan to the engines."""
    n = SHOT_FRAMES[2]
    coll = coll_new("flyby")
    sd = Vector((-1.0, -0.35, 0.45)).normalized()
    common_space(sd, star_gain=0.8, key=5.5)
    area("planetshine", (0, 0, -60), (0, 0, 0), 30000, 60, (0.3, 0.45, 1.0))
    planet_backdrop(coll, (60, 900, -380), 22.0, sd, rot=(-0.75, 0.0, 0.5))
    M, glows, _ = build_fighter(coll, HERO, "hero")
    ship = M.root
    # path: from deep in front, curving past camera right->left, banking
    start, mid, end = Vector((40, 190, -4)), Vector((6.0, -3.0, -3.2)), Vector((-110, -170, -12))

    def pos(f):
        t = (f - 1) / (n - 1)
        # quadratic bezier with speed ramp that brakes near the camera slightly
        u = 0.5 * t + 0.5 * math.copysign(abs(t) ** 1.6, t)
        a = start.lerp(mid, u)
        b = mid.lerp(end, u)
        return a.lerp(b, u)

    for f in range(1, n + 2):
        p = pos(f)
        v = (pos(f + 1) - pos(f - 1)).normalized()
        q = v.to_track_quat("X", "Z")
        bank = math.radians(lerp(-8, 38, ease_io((f - 35) / 60)))
        e = (q @ Euler((bank, 0, 0)).to_quaternion()).to_euler()
        kf(ship, f, loc=p, rot=e)
    fix_euler(ship)
    tgt = empty("focus", coll=coll)
    for f in range(1, n + 1):
        kf(tgt, f, loc=pos(f) + Vector((0, 0, 1.2)))
    cam = camera(lens=30, fstop=5.6, focus=tgt)
    campos = Vector((0, -10, 0.5))

    def tpos(f):
        lag = pos(max(1, f - 3)).lerp(pos(f), 0.6)
        return lag + Vector((0, 0, 1.5))

    aim_camera_frames(cam, range(1, n + 1),
                      lambda f: campos + Vector((0.06 * math.sin(f / 7.0), -0.02 * f,
                                                 0.01 * f + 0.05 * math.sin(f / 5.3))),
                      tpos, lambda f: math.radians(-3))
    scatter_debris(coll, 26, (0, 50, 0), (45, 70, 20), (1, n), drift=0.02, seed=21)
    compositing(bloom=0.7, streaks=0.25)
    return n


def shot3(sc):
    """Parts drift in from all sides and click together into the station."""
    n = SHOT_FRAMES[3]
    coll = coll_new("assembly")
    sd = Vector((0.55, -1.0, 0.6)).normalized()
    common_space(sd, star_gain=0.7, key=5.0)
    area("planetshine", (0, 0, -80), (0, 0, 10), 40000, 80, (0.3, 0.45, 1.0))
    area("rim", (-40, 60, -15), (0, 0, 10), 25000, 30, (0.75, 0.85, 1.0))
    planet_backdrop(coll, (-150, 700, -420), 20.0, sd, rot=(0.4, 0.2, 1.2))
    M, beacon = build_station(coll)
    rng = random.Random(5)
    parts = list(M.parts)
    parts.sort(key=lambda o: (o.location.z, rng.random()))
    N = len(parts)
    camdir = Vector((math.cos(math.radians(-52)), math.sin(math.radians(-52)), 0.2)).normalized()
    land_first, land_last, fly = 24, 102, 18
    for idx, ob in enumerate(parts):
        final = ob.location.copy()
        frot = Euler(ob.rotation_euler)
        tl = int(land_first + (land_last - land_first) * idx / max(1, N - 1))
        tl += rng.randint(-2, 2)
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.2, 1.0))).normalized()
        if d.dot(camdir) > 0.35:     # keep incoming parts out of the lens
            d = (d - 2 * d.dot(camdir) * camdir).normalized()
        far = final + d * rng.uniform(22, 36)
        spin = Vector((rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-3, 3)))
        drift = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.03
        hover = final + Vector((0, 0, 0.7))
        for f in range(1, n + 1):
            if f <= tl - fly:
                p = far + drift * (f - (tl - fly))
                r = Vector(frot) + spin
                rr = spin * (1 + 0.004 * (f - (tl - fly)))
                r = Vector(frot) + rr
            elif f < tl - 4:
                t = (f - (tl - fly)) / (fly - 4)
                u = ease_io(t) * 0.6 + ease_out(t, 2) * 0.4
                p = far.lerp(hover, u)
                r = Vector(frot) + spin * (1 - ease_out(t, 2))
            elif f < tl:
                t = (f - (tl - 4)) / 4
                p = hover.lerp(final + Vector((0, 0, -0.04)), t * t)
                r = Vector(frot)
            else:
                t = (f - tl)
                p = final + Vector((0, 0, -0.04 * math.exp(-t * 0.8) * math.cos(t * 1.8)))
                r = Vector(frot)
            kf(ob, f, loc=p, rot=Euler(r))
        linearize(ob)
    # beacon blinks once the station is complete
    beacon.color = (0, 0, 0, 1)
    for f in range(1, n + 1):
        on = 1.0 if (f > land_last + 2 and (f // 8) % 2 == 0) else 0.0
        kf(beacon, f, color=(on, on, on, 1))
    cam = camera(lens=32, fstop=5.6)
    cam.data.dof.focus_distance = 40.0
    aim_camera_frames(cam, range(1, n + 1, 2),
                      lambda f: (lerp(44, 38, ease_io(f / n)) * math.cos(math.radians(-70 + 38 * f / n)),
                                 lerp(44, 38, ease_io(f / n)) * math.sin(math.radians(-70 + 38 * f / n)),
                                 lerp(3, 13, f / n)),
                      lambda f: (0, 0, lerp(8, 10, f / n)))
    scatter_debris(coll, 25, (0, 0, 10), (45, 45, 20), (1, n), drift=0.015, seed=31)
    compositing(bloom=0.6, streaks=0.2)
    return n


def laser(coll, rgb, name):
    core = place(part_capsule(0.11, 5.0), mat_glow_additive(
        name + "_core", tuple(0.5 + 0.5 * c for c in rgb), 22.0, 0.6),
        coll=coll, name=name)
    halo = place(part_capsule(0.28, 5.6), mat_glow_additive(
        name + "_halo", rgb, 2.0, 2.5), (0, 0, -0.3), parent=core, coll=coll)
    for o in (core, halo):
        o.visible_shadow = False
    lt = point(name + "_l", (0, 0, 2.5), 0, rgb, 0.3, core)
    return core, lt


def shot4(sc):
    """Chase: the hero lands a hit and the enemy flies apart brick by brick."""
    n = SHOT_FRAMES[4]
    coll = coll_new("dogfight")
    sd = Vector((0.3, 0.9, 0.6)).normalized()
    common_space(sd, star_gain=0.8, key=5.5)
    area("planetshine", (0, 0, -60), (0, 0, 0), 30000, 60, (0.3, 0.45, 1.0))
    planet_backdrop(coll, (500, 250, -520), 22.0, sd, rot=(0.1, 0.4, 2.0))
    H, _, hm = build_fighter(coll, HERO, "hero")
    E, eglow, _ = build_fighter(coll, ENEMY, "enemy")
    hit = 58
    # both ships fly along +x in a co-moving frame; debris streams past
    for f in range(1, n + 1):
        t = f / FPS
        kf(H.root, f, loc=(0, 3.0 * math.sin(t * 1.3), 1.2 * math.sin(t * 1.9)),
           rot=(math.radians(-14 * math.cos(t * 1.3)), math.radians(2 * math.sin(t * 1.9)), 0))
        if f <= hit + 1:
            kf(E.root, f, loc=(34, -6 + 5 * math.sin(t * 1.7 + 1), 4 + 1.5 * math.sin(t * 2.3)),
               rot=(math.radians(-22 * math.cos(t * 1.7 + 1)), 0, math.radians(4 * math.sin(t))))
    ecenter = Vector((34, -6 + 5 * math.sin(hit / FPS * 1.7 + 1), 4 + 1.5 * math.sin(hit / FPS * 2.3)))
    linearize(E.root)

    bolts = []
    # hero volleys: (fire frame, target offset, hits?)
    shots = [(8, Vector((0, 5, 3)), False), (22, Vector((0, -4, -2)), False),
             (36, Vector((0, 3, -1)), False), (48, Vector((0, 0, 0.8)), True)]
    for k, (f0, off, is_hit) in enumerate(shots):
        for mi, mz in enumerate(hm):
            core, lt = laser(coll, HERO["bolt"], f"hb{k}{mi}")
            sc.frame_set(f0)
            p0 = mz.matrix_world.translation.copy()
            tgt_f = hit if is_hit else f0 + 14
            sc.frame_set(min(tgt_f, hit))
            tgt = E.root.matrix_world.translation + off if not is_hit else ecenter.copy()
            v = (tgt - p0) / (tgt_f - f0)
            q = v.normalized().to_track_quat("Z", "Y").to_euler()
            core.scale = (0, 0, 0)
            kf(core, f0 - 1, loc=p0, rot=q, scale=0.0)
            kf(core, f0, loc=p0, rot=q, scale=1.0)
            fe = tgt_f if is_hit else f0 + 26
            kf(core, fe, loc=p0 + v * (fe - f0), rot=q, scale=1.0)
            kf(core, fe + 1, loc=p0 + v * (fe + 1 - f0), rot=q, scale=0.0)
            linearize(core, extrapolate=False)
            lt.data.energy = 0
            lt.data.keyframe_insert("energy", frame=f0 - 1)
            lt.data.energy = 80
            lt.data.keyframe_insert("energy", frame=f0)
            lt.data.keyframe_insert("energy", frame=fe)
            lt.data.energy = 0
            lt.data.keyframe_insert("energy", frame=fe + 1)
            bolts.append(core)
    # enemy return fire zips past the camera
    for k, f0 in enumerate((16, 30)):
        core, lt = laser(coll, ENEMY["bolt"], f"eb{k}")
        sc.frame_set(f0)
        p0 = E.root.matrix_world.translation.copy()
        tgt = Vector((-40, -14 + 6 * k, 6 - 4 * k))
        v = (tgt - p0) / 18
        q = v.normalized().to_track_quat("Z", "Y").to_euler()
        kf(core, f0 - 1, loc=p0, rot=q, scale=0.0)
        kf(core, f0, loc=p0, rot=q, scale=1.0)
        kf(core, f0 + 20, loc=p0 + v * 20, rot=q, scale=1.0)
        kf(core, f0 + 21, loc=p0 + v * 21, rot=q, scale=0.0)
        linearize(core, extrapolate=False)
        lt.data.energy = 0
        lt.data.keyframe_insert("energy", frame=f0 - 1)
        lt.data.energy = 80
        lt.data.keyframe_insert("energy", frame=f0)
        lt.data.keyframe_insert("energy", frame=f0 + 20)
        lt.data.energy = 0
        lt.data.keyframe_insert("energy", frame=f0 + 21)

    # --- the explosion ---------------------------------------------------
    rng = random.Random(9)
    baked = {ob: [] for ob in E.parts}
    for f in range(1, hit + 1):
        sc.frame_set(f)
        for ob in E.parts:
            baked[ob].append(ob.matrix_world.copy())
    for ob in E.parts:
        ob.parent = None
        ob.animation_data_clear()
        prev = Euler((0, 0, 0))
        for f in range(1, hit + 1):
            mw = baked[ob][f - 1]
            prev = mw.to_euler("XYZ", prev)
            kf(ob, f, loc=mw.translation, rot=prev)
        mw = baked[ob][-1]
        p = mw.translation.copy()
        r = prev
        v = (p - ecenter)
        v = (v.normalized() if v.length > 1e-3 else Vector((0, 0, 1))) * rng.uniform(0.25, 0.7) \
            + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.12
        av = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.35
        for f in range(hit + 1, n + 1):
            dt = f - hit
            kf(ob, f, loc=p + v * dt * (1.0 - 0.004 * dt), rot=Euler(Vector(r) + av * dt))
        linearize(ob)
    for g in eglow:
        if g.type == "LIGHT":
            g.data.keyframe_insert("energy", frame=hit)
            g.data.energy = 0
            g.data.keyframe_insert("energy", frame=hit + 1)
        else:
            kf(g, hit, scale=g.scale.copy())
            kf(g, hit + 1, scale=0.0)
    # fireball: glowing trans plates flung outward, cooling as they go
    fire_cols = ["t_yellow", "t_orange", "t_orange", "t_red"]
    for i in range(70):
        c = rng.choice(fire_cols)
        mesh = part_round(1, 1) if rng.random() < 0.6 else part_brick(1, 1, 1, hollow=False)
        ob = place(mesh, mat_trans(c, 22.0), ecenter, coll=coll, name="fire")
        d = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
        sp = rng.uniform(0.35, 1.3)
        r0 = Euler((rng.uniform(0, 6), rng.uniform(0, 6), rng.uniform(0, 6)))
        av = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.6
        kf(ob, hit - 1, loc=ecenter, rot=r0, scale=0.0, color=(0, 0, 0, 1))
        for f in range(hit, n + 1, 2):
            dt = f - hit
            heat = math.exp(-dt / rng.uniform(6, 16))
            kf(ob, f, loc=ecenter + d * sp * dt * (1 - 0.01 * dt), rot=Euler(Vector(r0) + av * dt),
               scale=1.0, color=(heat, heat, heat, 1))
    flash = place(part_sphere(1.0), mat_glow_additive("flash", (1.0, 0.55, 0.2), 8.0, 2.5),
                  ecenter, coll=coll, name="flash")
    flash.visible_shadow = False
    kf(flash, hit - 1, scale=0.0, color=(1, 1, 1, 1))
    kf(flash, hit, scale=2.0, color=(1, 1, 1, 1))
    kf(flash, hit + 3, scale=5.0, color=(0.45, 0.45, 0.45, 1))
    kf(flash, hit + 12, scale=8.0, color=(0, 0, 0, 1))
    ring = place(part_ring(1.0, 0.05), mat_glow_additive("shock", (0.55, 0.75, 1.0), 3.0, 0.4),
                 ecenter, (math.radians(70), math.radians(10), 0), coll=coll, name="shock")
    ring.visible_shadow = False
    kf(ring, hit, scale=0.1, color=(1, 1, 1, 1))
    kf(ring, hit + 8, scale=14.0, color=(0.5, 0.5, 0.5, 1))
    kf(ring, hit + 24, scale=30.0, color=(0, 0, 0, 1))
    fl = point("boom", ecenter, 0, (1.0, 0.6, 0.3), 2.0)
    for f, e in ((hit - 1, 0), (hit, 20000), (hit + 3, 9000), (hit + 18, 800), (n, 0)):
        fl.data.energy = e
        fl.data.keyframe_insert("energy", frame=f)
    # camera: over-the-shoulder behind the hero, subtle handheld drift
    cam = camera(lens=32, fstop=11.0)
    rs = random.Random(3)
    ph = [rs.uniform(0, 6) for _ in range(6)]

    def cpos(f):
        t = f / FPS
        base = Vector((-27, 11.0, 9.5))
        shake = Vector((0.15 * math.sin(t * 7 + ph[0]), 0.12 * math.sin(t * 9 + ph[1]),
                        0.1 * math.sin(t * 11 + ph[2])))
        if f >= hit:
            k = math.exp(-(f - hit) / 6.0)
            shake += Vector((0.0, 0.5 * k * math.sin((f - hit) * 2.1), 0.4 * k * math.sin((f - hit) * 2.7)))
        return base + shake

    aim_camera_frames(cam, range(1, n + 1), cpos,
                      lambda f: Vector((17, -3.0, 0.5)) + Vector((0, 0.6 * math.sin(f / 13), 0)))
    cam.data.dof.focus_distance = 30.0
    scatter_debris(coll, 70, (20, 0, 0), (60, 30, 18), (1, n), drift=0.02, seed=41,
                   stream=(-2.2, 0, 0))
    compositing(bloom=0.9, streaks=0.3)
    return n


FONT = {
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
}


def shot5(sc):
    """Title: bricks converge into STARBRICK, a light sweeps across."""
    n = SHOT_FRAMES[5]
    coll = coll_new("title")
    world_space(star_gain=0.6, ambient=0.0004)
    word = "STARBRICK"
    width = len(word) * 6 - 1
    cells = []
    for li, ch in enumerate(word):
        for r, row in enumerate(FONT[ch]):
            for c, px in enumerate(row):
                if px == "#":
                    cells.append((li * 6 + c - width / 2 + 0.5, (6 - r) - 3.0, li))
    rng = random.Random(77)
    b11 = part_brick(1, 1, 3)
    gold = mat_metal("pearlgold", "C9A44C", 0.2)
    chrome = mat_metal("chrome", "D8DCE0", 0.1)
    obs = []
    for (x, z, li) in cells:
        # brick lies on its back: studs face the camera (-y)
        final = Vector((x, BRICK / 2, z))
        frot = Euler((math.radians(90), 0, 0))
        ob = place(b11, gold, final, frot, coll=coll, mat2=gold, name="title")
        start = final + Vector((rng.uniform(-40, 40), rng.uniform(-20, 60), rng.uniform(-25, 25)))
        spin = Vector((rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(-8, 8)))
        tl = int(14 + li * 2.2 + rng.uniform(0, 8))
        for f in range(1, n + 1):
            if f < tl:
                t = f / tl
                u = ease_out(t, 3)
                p = start.lerp(final + Vector((0, -0.5, 0)), u)
                r = Vector(frot) + spin * (1 - ease_out(t, 2))
            else:
                t = f - tl
                p = final + Vector((0, -0.5 * math.exp(-t * 0.9) * math.cos(t * 1.6), 0))
                r = Vector(frot)
            kf(ob, f, loc=p, rot=Euler(r))
        linearize(ob)
        obs.append(ob)
    # underline of chrome 1x2 tiles
    for i in range(-12, 12):
        ob = place(part_brick(2, 1, 1, studs=False), chrome, (i * 2 + 1, 0.2, -4.6),
                   (math.radians(90), 0, 0), coll=coll, mat2=chrome, name="line")
        start = Vector((i * 2 + 1 + rng.uniform(-6, 6), rng.uniform(10, 40), -4.6 + rng.uniform(-10, 10)))
        tl = 30 + abs(i)
        for f in range(1, n + 1):
            u = ease_out(min(1, f / tl), 3)
            kf(ob, f, loc=start.lerp(Vector((i * 2 + 1, 0.2, -4.6)), u))
        linearize(ob)
    # lighting: soft top key, cool rim, and a narrow warm strip light sweeping
    # metals read through what they reflect: a big soft source behind the
    # camera, a cool rim from above and a narrow warm strip whose reflection
    # sweeps across the letters
    area("key", (0, -120, 34), (0, 0, 0), 90000, 50, (1.0, 0.93, 0.85))
    area("rim", (0, 30, 40), (0, 0, 0), 20000, 30, (0.5, 0.65, 1.0))
    area("under", (0, -60, -40), (0, 0, 0), 15000, 30, (0.45, 0.6, 1.0))
    sweep = area("sweep", (-90, -100, 4), (0, 0, 0), 120000, 1.0, (1.0, 0.82, 0.55))
    sweep.data.shape = "RECTANGLE"
    sweep.data.size, sweep.data.size_y = 3.0, 70.0
    for f, x in ((34, -150), (70, 150)):
        sweep.location = (x, -100, 4)
        look_at(sweep, (0, 0, 0))
        sweep.keyframe_insert("location", frame=f)
        sweep.keyframe_insert("rotation_euler", frame=f)
    cam = camera(lens=35, fstop=8.0)
    cam.data.dof.focus_distance = 62.0
    aim_camera_frames(cam, range(1, n + 1, 2),
                      lambda f: (lerp(4, -1, ease_io(f / n)), lerp(-68, -61, ease_io(f / n)),
                                 lerp(-3, 1.0, ease_io(f / n))),
                      lambda f: (lerp(1.5, 0, f / n), 0, -0.4))
    compositing(bloom=0.6, streaks=0.45, threshold=2.0)
    return n


SHOTS = {1: shot1, 2: shot2, 3: shot3, 4: shot4, 5: shot5}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--scale", type=int, default=100, help="resolution percentage")
    ap.add_argument("--frames", default=None, help="e.g. 1-120 or 1,40,80")
    ap.add_argument("--save-blend", default=None)
    ap.add_argument("--threads", type=int, default=0)
    a = ap.parse_args(argv)

    sc = reset_scene()
    n = SHOTS[a.shot](sc)
    sc.frame_start, sc.frame_end = 1, n
    sc.cycles.samples = a.samples
    sc.render.resolution_percentage = a.scale
    if a.threads:
        sc.render.threads_mode = "FIXED"
        sc.render.threads = a.threads
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
    os.makedirs(a.out, exist_ok=True)
    if a.frames and ("," in a.frames or "-" not in a.frames):
        for f in [int(x) for x in a.frames.split(",")]:
            path = os.path.join(a.out, f"{f:04d}.png")
            if os.path.exists(path):
                continue
            sc.frame_set(f)
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
    else:
        if a.frames:
            s, e = a.frames.split("-")
            sc.frame_start, sc.frame_end = int(s), int(e)
        sc.render.filepath = os.path.join(os.path.abspath(a.out), "")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
