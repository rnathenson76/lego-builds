#!/usr/bin/env python3
"""Phase 2: rolling chassis for the tractor and the trailer.

Writes model/chassis.mpd. See DESIGN.md for the dimension sheet.
Coordinates follow tools/ldr.py: X = rig length in LDU (0 = bumper face),
Z = width (0 = centreline), heights are LDU above ground (LDraw Y = -height).
"""
import argparse
import math
import os

import numpy as np

import ldr
from ldr import Model, rot_x, rot_y, rot_z

# ---- colours (LDraw codes) ----
BLACK, WHITE, RED = 0, 15, 4
LBG, DBG = 71, 72            # light / dark bluish grey
TAN = 19

# ---- key heights (LDU above ground) ----
HUB = 54                     # wheel centre: 2696 tyre radius
FRAME_TOP = 120              # 15 plates: clears the tie rod, matches the cab floor
FRAME_BOT = FRAME_TOP - 24
FIFTH_TOP = 144              # 18 plates: trailer underside

# ---- key positions (LDU from the bumper face) ----
STEER_X = 100                # rig stud 5
PIVOT_X = 420                # walking-beam pivot, rig stud 21
DRIVE_X = (360, 480)         # rig studs 18 and 24
FIFTH_X = 380                # rig stud 19
TRAILER_X0 = 300             # trailer front wall, rig stud 15
KINGPIN_Z = 40               # steering pivot offset from centreline

AXLE_Z = rot_y(90)           # Technic axles/pins are modelled along X; turn to Z
VERTICAL = rot_z(90)         # ... or stand them up along Y
FLIP = rot_y(180)            # mirror to the left-hand side


def top(h):
    """LDraw Y for a stud-up part whose body top is at height h."""
    return -h


def wheel(m, x, z_inner, side):
    """2695 rim + 2696 tyre whose tread spans z_inner..z_inner+32 (right side)."""
    if side > 0:
        pos, rot = (x, -HUB, z_inner + 24), None
    else:
        pos, rot = (x, -HUB, -(z_inner + 24)), FLIP
    m.add("2695.dat", LBG, pos, rot)
    m.add("2696.dat", BLACK, pos, rot)


# ---------------------------------------------------------------------------
# Tractor
# ---------------------------------------------------------------------------
def knuckle(m, side, steer_deg=0.0):
    """One steered wheel assembly, rotated steer_deg about its kingpin."""
    kz = side * KINGPIN_Z
    R = rot_y(steer_deg)

    def at(x, h, z, rot=None):
        p = R @ np.array([x - STEER_X, 0, z - kz]) + np.array([STEER_X, 0, kz])
        return (p[0], -h, p[2]), (R if rot is None else R @ rot)

    pos, r = at(STEER_X, 64, side * 30)
    m.add("3700.dat", LBG, pos, r)                       # knuckle: hole at hub height
    pos, r = at(STEER_X + 20, 72, side * 40)
    m.add("3709b.dat", DBG, pos, r)                      # steering arm, hole 2 studs aft
    pos, r = at(STEER_X, HUB, side * 70, AXLE_Z)
    m.add("32073.dat", LBG, (pos[0], -HUB, pos[2]), r)   # stub axle (axle 5)
    for zc in (50, 70):
        pos, r = at(STEER_X, HUB, side * zc)
        m.add("3713.dat", LBG, (pos[0], -HUB, pos[2]), r)  # spacer bushes
    pos, r = at(STEER_X, HUB, side * 104, None if side > 0 else FLIP)
    m.add("2695.dat", LBG, (pos[0], -HUB, pos[2]), r)
    m.add("2696.dat", BLACK, (pos[0], -HUB, pos[2]), r)
    pos, r = at(STEER_X, HUB, side * 116)
    m.add("32123a.dat", LBG, (pos[0], -HUB, pos[2]), r)


def tractor_chassis(steer_deg=0.0):
    m = Model("tractor-chassis.ldr", "BJ and the Bear - Tractor rolling chassis")

    # Step 1: frame rails and cross members
    for z in (-30, 30):
        m.add("3703.dat", BLACK, (180, top(FRAME_TOP), z))      # 1x16, x 20..340
        m.add("2730.dat", BLACK, (440, top(FRAME_TOP), z))      # 1x10, x 340..540
    for x in (260, 520):
        m.add("3020.dat", BLACK, (x, top(FRAME_BOT), 0), rot_y(90))
    m.step()

    # Step 2: front axle beam hanging below the frame
    m.add("3032.dat", DBG, (60, top(FRAME_BOT), 0))             # 4x6, under the rails
    m.add("3022.dat", DBG, (40, top(88), 0))                    # post: plate + 2 bricks
    m.add("3003.dat", DBG, (40, top(80), 0))
    m.add("3003.dat", DBG, (40, top(56), 0))
    m.add("3032.dat", DBG, (60, top(32), 0))                    # axle beam, 3 plates off the ground
    for side in (-1, 1):
        m.add("3680c01.dat", LBG, (STEER_X, top(40), side * KINGPIN_Z))  # kingpin turntables
    m.step()

    # Step 3: knuckles and front wheels
    for side in (-1, 1):
        knuckle(m, side, steer_deg)
    m.step()

    # Step 4: tie rod, lever and steering column
    s = math.radians(steer_deg)
    dz = -40 * math.sin(s)                   # arm holes swing about the kingpins
    dx = -40 * (1 - math.cos(s))
    tie_x, tie_z = STEER_X + 40 + dx, dz
    # Tie rod: a thin 5L beam resting on the arm studs (smooth, so it pivots).
    # Lever sits directly on top; both stay below the frame rails (96).
    m.add("32017.dat", DBG, (tie_x, -81, tie_z))                # 76..86, holes vertical
    for side in (-1, 1):
        m.add("3673.dat", LBG, (tie_x, -75, tie_z + side * KINGPIN_Z), VERTICAL)
    lever_x, lever_z = 180, 0
    ang = math.atan2(tie_z - lever_z, lever_x - tie_x)          # lever points at the tie rod
    m.add("6632.dat", DBG, (lever_x, -91, lever_z), rot_y(-90 + math.degrees(ang)))  # 86..96
    m.add("32062.dat", LBG, (tie_x, -86, tie_z), VERTICAL)      # axle 2: locked in lever, turns in tie rod
    m.add("3705.dat", DBG, (lever_x, -126, lever_z), VERTICAL)  # steering column 86..166
    m.add("3709b.dat", BLACK, (180, top(FRAME_TOP + 8), 0), rot_y(90))  # column bearing on the rails
    m.add("6538a.dat", DBG, (lever_x, -176, lever_z), VERTICAL)  # joiner: cab shaft drops in here
    m.step()

    # Step 5: walking-beam tandem
    for z in (-10, 10):
        m.add("3700.dat", DBG, (PIVOT_X, top(64), z))            # hangers, hole at hub height
        for h in (72, 80, 88):
            m.add("3023b.dat", DBG, (PIVOT_X, top(h), z))
    m.add("3020.dat", BLACK, (PIVOT_X, top(FRAME_BOT), 0), rot_y(90))
    for z in (-30, 30):
        m.add("3702.dat", DBG, (PIVOT_X, top(64), z))            # walking beams
    m.add("3705.dat", LBG, (PIVOT_X, -HUB, 0), AXLE_Z)          # pivot
    for x in DRIVE_X:
        m.add("3708.dat", LBG, (x, -HUB, 0), AXLE_Z)            # axle 12
    m.step()

    # Step 6: dual wheels
    for x in DRIVE_X:
        for side in (-1, 1):
            wheel(m, x, 44, side)                                # inner
            wheel(m, x, 78, side)                                # outer
            m.add("32123a.dat", LBG, (x, -HUB, side * 115))
    m.step()

    # Step 7: fifth wheel
    m.add("3403c01.dat", DBG, (FIFTH_X, top(FIFTH_TOP), 0))
    return m


# ---------------------------------------------------------------------------
# Trailer (local X: 0 = front wall; placed at TRAILER_X0 in the rig)
# ---------------------------------------------------------------------------
def trailer_chassis():
    m = Model("trailer-chassis.ldr", "BJ and the Bear - Trailer rolling chassis")
    L = 1120                                   # 56 studs
    floor = FIFTH_TOP + 8                      # top of the first floor layer

    # Step 1: bottom floor layer, black (shows as the bottom rail band)
    centre = [("3036.dat", 160)] + [("3027.dat", 320)] * 3       # 6x8 + 3 x 6x16
    edge = [("4282.dat", 320)] * 3 + [("3034.dat", 160)]         # 3 x 2x16 + 2x8, staggered
    for parts, zs in ((centre, (0,)), (edge, (-80, 80))):
        for z in zs:
            x = 0
            for part, length in parts:
                m.add(part, BLACK, (x + length / 2, top(floor), z))
                x += length
    m.step()

    # Step 2: second floor layer inside the walls, bridging the joints
    x = 0
    for part, length in [("41539.dat", 160)] + [("92438.dat", 320)] * 3:
        m.add(part, DBG, (x + length / 2, top(floor + 8), 0))
        x += length
    m.step()

    # Step 3: landing gear (swing-down legs)
    lx = 300                                   # trailer stud 15
    for side in (-1, 1):
        # Pivot 1 plate below the floor: legs reach 4 LDU below the wheels, so a
        # parked trailer sits a little high and the tractor can back under it.
        m.add("3023b.dat", BLACK, (lx, top(FIFTH_TOP), side * 70))
        m.add("3700.dat", BLACK, (lx, top(FIFTH_TOP - 8), side * 70))
        piv = FIFTH_TOP - 8 - 10
        m.add("32524.dat", LBG, (lx, -(piv - 60), side * 90), rot_x(90))
        m.add("2780.dat", BLACK, (lx, -piv, side * 80), AXLE_Z)
    m.step()

    # Step 4: rear sub-frame and axles
    bx = 960                                   # centre between axles at 900 / 1020
    for z in (-30, 30):
        m.add("3702.dat", DBG, (bx, top(64), z))
        for h in (88, 112, 136):
            m.add("3008.dat", BLACK, (bx, top(h), z))
        m.add("3460.dat", BLACK, (bx, top(144), z))
    for x in (900, 1020):
        m.add("3708.dat", LBG, (x, -HUB, 0), AXLE_Z)
    m.step()

    # Step 5: dual wheels
    for x in (900, 1020):
        for side in (-1, 1):
            wheel(m, x, 44, side)
            wheel(m, x, 78, side)
            m.add("32123a.dat", LBG, (x, -HUB, side * 115))
    return m


def rig(tractor, trailer):
    m = Model("bj-and-the-bear-chassis.ldr", "BJ and the Bear - Rolling chassis (Phase 2)")
    m.sub(tractor)
    m.step()
    m.sub(trailer, (TRAILER_X0, 0, 0))
    return m


def check(models):
    """Coarse bbox overlap report, skipping intended connections."""
    through = ("3705", "3708", "32073", "3673", "32062", "2780", "3713", "32123a", "6538a")

    def ignore(a, b):
        names = (a.part.split(".")[0], b.part.split(".")[0])
        if any(n in through for n in names):
            return True                      # axles/pins/bushes sit in holes by design
        if {"2695", "2696"} == set(names):
            return True                      # rim inside tyre
        return False

    for m in models:
        hits = [h for h in ldr.overlaps(m.parts(), tol=2.0, ignore=ignore) if h[2][1] > 4.5]  # >4.5: not just a stud
        print(f"{m.name}: {len(m.parts())} parts, {len(hits)} suspicious overlaps")
        for a, b, ov in hits:
            print(f"   {a.part:12s} @ {np.round(a.pos, 1)}  x  {b.part:12s} @ {np.round(b.pos, 1)}  overlap {np.round(ov, 1)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--steer", type=float, default=0.0, help="steering angle in degrees (render demo)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    out = a.out or os.path.join(here, "..", "model", "chassis.mpd")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    t, tr = tractor_chassis(a.steer), trailer_chassis()
    r = rig(t, tr)
    ldr.write_mpd(out, [r, t, tr])
    check([t, tr])
    print(os.path.relpath(out))
