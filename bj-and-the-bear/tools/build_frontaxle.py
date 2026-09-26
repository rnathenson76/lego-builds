#!/usr/bin/env python3
"""Front-axle test module: the tractor's steering in isolation.

Same geometry as tractor-chassis.ldr (tools/build_chassis.py), plus a short
stub of frame and a knob on the steering column so it can be steered by hand.
Writes model/front-axle-test.mpd, with steps in physical build order.
"""
import os

import ldr
from ldr import Model, rot_x, rot_y
from build_chassis import (AXLE_Z, BLACK, DBG, FLIP, FRAME_BOT, FRAME_TOP, HUB, KINGPIN_Z, LBG,
                           STEER_X, VERTICAL, top)

# Camera for each step (latitude, longitude), saved next to the model.
FRONT_LEFT = (30, -35)
REAR_LEFT = (55, -150)


def build():
    m = Model("front-axle-test.ldr", "BJ and the Bear - Front axle test module")
    cams = []

    def step(cam=FRONT_LEFT):
        cams.append(cam)
        m.step()

    # 1: axle beam and kingpin turntables
    m.add("3032.dat", DBG, (60, top(32), 0))
    for side in (-1, 1):
        m.add("3680c01.dat", LBG, (STEER_X, top(40), side * KINGPIN_Z))
    step()

    # 2: knuckles
    for side in (-1, 1):
        m.add("3700.dat", LBG, (STEER_X, top(64), side * 30))
    step()

    # 3: steering arms (holes line up over the knuckle, 2 studs back)
    for side in (-1, 1):
        m.add("3709b.dat", DBG, (STEER_X + 20, top(72), side * 40))
    step()

    # 4: post in front of the wheels
    m.add("3003.dat", DBG, (40, top(56), 0))
    m.add("3003.dat", DBG, (40, top(80), 0))
    m.add("3022.dat", DBG, (40, top(88), 0))
    step()

    # 5: tie rod rests on the arm studs; pins go down through it into the arms
    tie_x = STEER_X + 40
    m.add("32017.dat", LBG, (tie_x, -81, 0))
    for side in (-1, 1):
        m.add("3673.dat", LBG, (tie_x, -75, side * KINGPIN_Z), VERTICAL)
    step(REAR_LEFT)

    # 6: lever on a 2-long axle through the tie rod's centre hole
    m.add("6632.dat", LBG, (180, -91, 0), rot_y(-90))
    m.add("32062.dat", LBG, (tie_x, -86, 0), VERTICAL)
    step(REAR_LEFT)

    # 7: stub axles and spacer bushes
    for side in (-1, 1):
        m.add("32073.dat", LBG, (STEER_X, -HUB, side * 70), AXLE_Z)
        for zc in (50, 70):
            m.add("3713.dat", LBG, (STEER_X, -HUB, side * zc))
    step()

    # 8: wheels and retaining half-bushes
    for side in (-1, 1):
        rot = None if side > 0 else FLIP
        m.add("2695.dat", LBG, (STEER_X, -HUB, side * 104), rot)
        m.add("2696.dat", BLACK, (STEER_X, -HUB, side * 104), rot)
        m.add("32123a.dat", LBG, (STEER_X, -HUB, side * 116))
    step()

    # 9: frame stub: cross plate onto the post
    m.add("3032.dat", DBG, (60, top(FRAME_BOT), 0))
    step()

    # 10: two short frame rails (any 1x10 bricks will do for the test)
    for z in (-30, 30):
        m.add("2730.dat", BLACK, (120, top(FRAME_TOP), z))
    step()

    # 11: column bearing across the rails
    m.add("3709b.dat", BLACK, (180, top(FRAME_TOP + 8), 0), rot_y(90))
    step(REAR_LEFT)

    # 12: steering column down through the bearing into the lever, joiner, knob
    m.add("3705.dat", DBG, (180, -126, 0), VERTICAL)
    m.add("6538a.dat", DBG, (180, -166, 0), VERTICAL)       # joiner 156..176 over the column top
    m.add("4519.dat", DBG, (180, -196, 0), VERTICAL)        # axle 3: 166..226 into the joiner
    m.add("4185a.dat", LBG, (180, -220, 0), rot_x(90))      # knob to steer by hand
    step(REAR_LEFT)
    return m, cams


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "model", "front-axle-test.mpd")
    m, cams = build()
    ldr.write_mpd(out, [m])
    import json
    with open(os.path.splitext(out)[0] + ".cameras.json", "w") as f:
        json.dump(cams, f)
    print(os.path.relpath(out), len(m.parts()), "parts,", len(cams), "steps")
