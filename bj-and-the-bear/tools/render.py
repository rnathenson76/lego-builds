#!/usr/bin/env python3
"""Render views of an LDraw model with LeoCAD (headless, via xvfb-run).

usage: render.py MODEL.mpd OUT_PREFIX [--submodel NAME] [--views v1,v2,...]
Views: front34, rear34, side, top, bottom, front (see VIEWS below).
"""
import argparse
import os
import subprocess

VIEWS = {
    # name: leocad args
    "front34": ["--camera-angles", "25", "-40"],
    "rear34": ["--camera-angles", "25", "140"],
    "side": ["--viewpoint", "left", "--orthographic"],
    "top": ["--viewpoint", "top", "--orthographic"],
    "bottom": ["--viewpoint", "bottom", "--orthographic"],
    "front": ["--viewpoint", "front", "--orthographic"],
    "low34": ["--camera-angles", "8", "-35"],
}


def render(model, out, view, sub=None, w=1600, h=900):
    cmd = ["xvfb-run", "-a", "leocad", "-l", os.environ.get("LDRAWDIR", "/usr/share/ldraw"),
           "-i", out, "-w", str(w), "-h", str(h), "--aa-samples", "4", "--shading", "full",
           "-ss", "6"] + VIEWS[view]
    if sub:
        cmd += ["-s", sub]
    cmd.append(model)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    ok = os.path.exists(out)
    print(("ok   " if ok else "FAIL ") + out + ("" if ok else "\n" + r.stdout + r.stderr))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("prefix")
    ap.add_argument("--submodel")
    ap.add_argument("--views", default="front34,side,top")
    ap.add_argument("--size", default="1600x900")
    a = ap.parse_args()
    w, h = (int(v) for v in a.size.split("x"))
    for v in a.views.split(","):
        render(a.model, f"{a.prefix}-{v}.png", v, a.submodel, w, h)
