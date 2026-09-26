#!/usr/bin/env python3
"""Make a Lego-style instruction booklet (PDF) from a stepped LDraw model.

usage: booklet.py MODEL.mpd OUT.pdf --title T [--subtitle S] [--cameras C.json]
                  [--notes N.json] [--checklist N.json]

Pages: cover, parts inventory, one page per step (parts-for-this-step
callout + render), then an optional checklist page. Step images come from
LeoCAD (headless); part thumbnails are rendered one part at a time.
Handles single-level models (no sub-assembly callouts yet).
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFont

import ldr
from bom import COLOURS

W, H = 2480, 1754                       # A4 landscape at 300 dpi
MARGIN = 90
INK = (27, 42, 52)
MUTED = (96, 108, 118)
CALLOUT = (221, 236, 247)
CALLOUT_EDGE = (120, 170, 210)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CACHE = os.path.join(tempfile.gettempdir(), "bj-booklet-cache")
LEOCAD_STYLE = ["--shading", "full", "-ss", "6", "--aa-samples", "8"]


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def leocad(args):
    cmd = ["xvfb-run", "-a", "leocad", "-l", os.environ.get("LDRAWDIR", "/usr/share/ldraw")] + args
    subprocess.run(cmd, capture_output=True, text=True, timeout=600)


def white_bg(im):
    """LeoCAD renders on a flat background (dark in step mode). Flood-fill it
    from the border to white, so dark parts that match it are kept, then trim."""
    im = im.convert("RGB")
    key = (255, 0, 255)
    w, h = im.size
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if im.getpixel(xy) != key:
            ImageDraw.floodfill(im, xy, key, thresh=12)
    mask = Image.eval(ImageChops.difference(im, Image.new("RGB", im.size, key)).convert("L"),
                      lambda v: 255 if v > 0 else 0)
    out = Image.new("RGB", im.size, "white")
    out.paste(im, mask=mask)
    box = mask.getbbox()
    return out.crop(box) if box else out


def parse_steps(path):
    steps, cur = [], []
    with open(path) as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "1":
                cur.append((" ".join(t[14:]).lower(), int(t[1])))
            elif t[:2] == ["0", "STEP"]:
                if cur:
                    steps.append(cur)
                cur = []
    if cur:
        steps.append(cur)
    return steps


def step_images(model, n, cams, size=(1800, 1300)):
    out = []
    with tempfile.TemporaryDirectory() as d:
        for i in range(1, n + 1):
            lat, lon = cams[i - 1] if cams and i - 1 < len(cams) else (30, -35)
            leocad(["-i", os.path.join(d, "s.png"), "-w", str(size[0]), "-h", str(size[1]),
                    "-f", str(i), "-t", str(i), "--camera-angles", str(lat), str(lon)]
                   + LEOCAD_STYLE + [model])
            files = sorted(glob.glob(os.path.join(d, "s*.png")))
            if not files:
                raise RuntimeError(f"LeoCAD produced no image for step {i}")
            out.append(white_bg(Image.open(files[-1])))
            for f in files:
                os.remove(f)
    return out


def thumb(part, colour, px=420):
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5(f"{part}|{colour}|{px}".encode()).hexdigest()
    path = os.path.join(CACHE, key + ".png")
    if not os.path.exists(path):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "p.ldr")
            with open(src, "w") as f:
                f.write(f"0 part\n1 {colour} 0 0 0 1 0 0 0 1 0 0 0 1 {part}\n")
            leocad(["-i", os.path.join(d, "t.png"), "-w", str(px), "-h", str(px),
                    "--camera-angles", "30", "-35"] + LEOCAD_STYLE + [src])
            white_bg(Image.open(os.path.join(d, "t.png"))).save(path)
    return Image.open(path)


def fit(im, w, h):
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def colour_name(c):
    return COLOURS.get(c, (f"colour {c}",))[0]


def cover(title, subtitle, hero, nparts, nsteps):
    p = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(p)
    d.rectangle([0, 0, W, 260], fill=(201, 26, 9))
    d.text((MARGIN, 60), title, font=font(96, True), fill="white")
    d.text((MARGIN, 180), subtitle, font=font(48), fill="white")
    img = fit(hero, W - 2 * MARGIN, H - 520)
    p.paste(img, ((W - img.width) // 2, 320))
    d.text((MARGIN, H - 130), f"{nparts} parts  ·  {nsteps} steps", font=font(44, True), fill=INK)
    return p


def inventory(counts, title):
    p = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(p)
    d.text((MARGIN, 60), title, font=font(64, True), fill=INK)
    cols, cell_w, cell_h = 6, (W - 2 * MARGIN) // 6, 330
    y0 = 190
    for i, ((part, col), n) in enumerate(counts):
        cx, cy = MARGIN + (i % cols) * cell_w, y0 + (i // cols) * cell_h
        im = fit(thumb(part, col), cell_w - 60, 170)
        p.paste(im, (cx + (cell_w - im.width) // 2, cy + (180 - im.height) // 2))
        d.text((cx + 20, cy + 185), f"{n}x", font=font(44, True), fill=INK)
        pid = part[:-4] if part.endswith(".dat") else part
        d.text((cx + 20, cy + 238), f"{pid}  {colour_name(col)}", font=font(24), fill=MUTED)
        d.text((cx + 20, cy + 270), ldr.title(part)[:34], font=font(22), fill=MUTED)
    return p


def step_page(num, total, parts, img, note):
    p = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(p)
    d.text((MARGIN, 40), str(num), font=font(150, True), fill=INK)
    d.text((W - MARGIN - 260, H - 90), f"{num} / {total}", font=font(36), fill=MUTED)

    # parts callout
    counts = collections.Counter(parts)
    items = [fit(thumb(pt, c), 230, 170) for (pt, c) in counts]
    cw = sum(max(i.width, 120) + 50 for i in items) + 40
    x0, y0 = MARGIN + 260, 60
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + 280], radius=24, fill=CALLOUT, outline=CALLOUT_EDGE, width=4)
    x = x0 + 30
    for im, ((pt, c), n) in zip(items, counts.items()):
        p.paste(im, (x, y0 + 20 + (170 - im.height) // 2))
        d.text((x, y0 + 200), f"{n}x", font=font(52, True), fill=INK)
        x += max(im.width, 120) + 50

    # note
    top = y0 + 320
    if note:
        d.text((MARGIN, top), note, font=font(38), fill=INK)
        top += 60 * (note.count("\n") + 1) + 20

    big = fit(img, W - 2 * MARGIN, H - top - 120)
    p.paste(big, ((W - big.width) // 2, top + (H - top - 120 - big.height) // 2))
    return p


def checklist_page(title, lines):
    p = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(p)
    d.text((MARGIN, 60), title, font=font(72, True), fill=INK)
    y = 220
    for ln in lines:
        d.rounded_rectangle([MARGIN, y + 8, MARGIN + 48, y + 56], radius=8, outline=INK, width=4)
        d.text((MARGIN + 80, y), ln, font=font(42), fill=INK)
        y += 60 * (ln.count("\n") + 1) + 40
    return p


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("out")
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--cameras")
    ap.add_argument("--notes", help="JSON: {step number: note text}")
    ap.add_argument("--checklist", help="JSON: {title: str, items: [str]}")
    a = ap.parse_args()

    steps = parse_steps(a.model)
    cams = json.load(open(a.cameras)) if a.cameras else None
    notes = {int(k): v for k, v in json.load(open(a.notes)).items()} if a.notes else {}
    print(f"{len(steps)} steps; rendering...")
    imgs = step_images(a.model, len(steps), cams)

    allparts = collections.Counter(pc for s in steps for pc in s)
    ordered = sorted(allparts.items(), key=lambda kv: (ldr.title(kv[0][0]), kv[0][1]))
    pages = [cover(a.title, a.subtitle, imgs[-1], sum(allparts.values()), len(steps)),
             inventory(ordered, "Parts")]
    for i, (s, im) in enumerate(zip(steps, imgs), 1):
        pages.append(step_page(i, len(steps), s, im, notes.get(i, "")))
    if a.checklist:
        c = json.load(open(a.checklist))
        pages.append(checklist_page(c["title"], c["items"]))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    pages[0].save(a.out, save_all=True, append_images=pages[1:], resolution=300)
    print(f"{len(pages)} pages -> {a.out}")
