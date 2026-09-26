#!/usr/bin/env python3
"""Draw a side-elevation proportion sheet of the rig on the stud grid.

All positions are in studs (x, from the front bumper face) and plates
(y, from the ground). 1 stud = 8 mm, 1 plate = 3.2 mm, scale about 1:24.
Writes renders/proportion-sheet.svg.
"""
from pathlib import Path

STUD = 12.0            # px per stud in the drawing
PLATE = STUD * 0.4     # a plate is 3.2 mm, 0.4 of a stud
W_STUDS, H_PLATES = 100, 60
MARGIN = 40
WHEEL_R_PLATES = 6.75  # 2696 tire: 108 LDU diameter -> 54 LDU radius = 6.75 plates

COL = {
    "red": "#C91A09", "white": "#FFFFFF", "black": "#1B2A34",
    "gold": "#AA7F2E", "silver": "#A0A5A9", "glass": "#7FA8C9",
    "tire": "#212121", "grid": "#D9DDE1", "text": "#1B2A34",
}

shapes = []


def X(s):
    return MARGIN + s * STUD


def Y(p):
    return MARGIN + (H_PLATES - p) * PLATE


def rect(x0, x1, y0, y1, fill, stroke="#1B2A34", sw=1.0, label=None):
    shapes.append(
        f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{(x1 - x0) * STUD:.1f}" '
        f'height="{(y1 - y0) * PLATE:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    if label:
        text((x0 + x1) / 2, (y0 + y1) / 2, label, size=10)


def wheel(x):
    cy = WHEEL_R_PLATES
    r = WHEEL_R_PLATES * PLATE
    shapes.append(f'<circle cx="{X(x):.1f}" cy="{Y(cy):.1f}" r="{r:.1f}" fill="{COL["tire"]}"/>')
    shapes.append(f'<circle cx="{X(x):.1f}" cy="{Y(cy):.1f}" r="{r * 0.52:.1f}" fill="{COL["silver"]}"/>')


def text(x, y, s, size=11, anchor="middle", color=None):
    shapes.append(
        f'<text x="{X(x):.1f}" y="{Y(y) + size / 3:.1f}" font-family="sans-serif" font-size="{size}" '
        f'text-anchor="{anchor}" fill="{color or COL["text"]}">{s}</text>')


def dim(x0, x1, y, label):
    """Horizontal dimension line at plate height y."""
    shapes.append(f'<line x1="{X(x0):.1f}" y1="{Y(y):.1f}" x2="{X(x1):.1f}" y2="{Y(y):.1f}" '
                  f'stroke="{COL["text"]}" stroke-width="0.8" marker-start="url(#a)" marker-end="url(#a)"/>')
    text((x0 + x1) / 2, y + 1.6, label, size=10)


def vdim(x, y0, y1, label):
    shapes.append(f'<line x1="{X(x):.1f}" y1="{Y(y0):.1f}" x2="{X(x):.1f}" y2="{Y(y1):.1f}" '
                  f'stroke="{COL["text"]}" stroke-width="0.8" marker-start="url(#a)" marker-end="url(#a)"/>')
    shapes.append(f'<text x="{X(x) + 4:.1f}" y="{Y((y0 + y1) / 2):.1f}" font-family="sans-serif" '
                  f'font-size="10" fill="{COL["text"]}">{label}</text>')


# ---- grid (every 4 studs / every 3 plates = 1 brick) ----
for s in range(0, W_STUDS + 1, 4):
    shapes.append(f'<line x1="{X(s)}" y1="{Y(0)}" x2="{X(s)}" y2="{Y(H_PLATES)}" stroke="{COL["grid"]}" stroke-width="0.5"/>')
    if s % 8 == 0:
        text(s, -2.2, str(s), size=8)
for p in range(0, H_PLATES + 1, 3):
    shapes.append(f'<line x1="{X(0)}" y1="{Y(p)}" x2="{X(W_STUDS)}" y2="{Y(p)}" stroke="{COL["grid"]}" stroke-width="0.5"/>')

# ---- tractor ----
STEER, DRIVE1, DRIVE2 = 5, 24, 31
FIFTH = 26.5
rect(1, 35, 11, 13, COL["black"])                       # frame rails
rect(0, 1, 5, 9, COL["silver"])                         # bumper
rect(1, 12, 9, 44, COL["red"])                          # cab + sleeper box
rect(1, 12, 44, 50, COL["red"])                         # Aerodyne raised roof
rect(1.3, 5.5, 29, 40, COL["glass"], sw=0.6)            # door window
rect(8.5, 11.2, 45, 48, COL["glass"], sw=0.6)           # Aerodyne upper sleeper window
rect(1, 12, 17, 19, COL["white"], sw=0.4)               # placeholder stripe band
rect(1, 12, 16.5, 17, COL["gold"], sw=0)                # placeholder pinstripe
rect(12, 19, 7, 12, COL["silver"])                      # fuel tank / steps
rect(12.3, 13.1, 13, 54, COL["silver"])                 # exhaust stack
rect(FIFTH - 2, FIFTH + 2, 13, 16, COL["black"])        # fifth wheel
for x in (STEER, DRIVE1, DRIVE2):
    wheel(x)

# ---- trailer ----
T0 = FIFTH - 5          # kingpin 5 studs back from the trailer front
T1 = T0 + 72            # 45 ft = 72 studs
rect(T0 - 3, T0, 34, 52, COL["silver"], label="reefer")  # refrigeration unit
rect(T0, T1, 18, 54, COL["white"], label="45 ft reefer box, 72 studs, SNOT tiled walls")
rect(T0, T1, 17, 18, COL["black"])                     # floor / side rail
rect(T0 + 18, T0 + 19, 4, 17, COL["silver"])           # landing gear
for x in (T1 - 13, T1 - 6):
    wheel(x)

# ---- dimensions ----
dim(0, 35, 57.5, "tractor 35 studs (6.7 m)")
dim(0, T1, -7, f"whole rig {T1:.1f} studs ({T1 * 8 / 10:.0f} cm model / {T1 * 0.192:.1f} m real)")
dim(STEER, (DRIVE1 + DRIVE2) / 2, 20.5, "wheelbase 22.5 (170 in)")
vdim(T1 + 1.2, 0, 54, "54 plates = 13'6\"")
vdim(-1.5, 0, 50, "50 pl")
for x, name in ((STEER, "steer"), (DRIVE1, "drive"), (DRIVE2, "drive"), (T1 - 13, "trailer"), (T1 - 6, "trailer")):
    text(x, -3.6, name, size=9)
text(FIFTH, 14.5, "5th", size=8, color="#FFFFFF")
text(T0 + 18.5, 2.2, "legs", size=8, anchor="start")

W = X(W_STUDS) + MARGIN
H = Y(-9) + MARGIN
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}">'
       '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
       f'<path d="M0,0 L10,5 L0,10 z" fill="{COL["text"]}"/></marker></defs>'
       f'<rect width="100%" height="100%" fill="#FFFFFF"/>'
       + "".join(shapes) +
       f'<text x="{MARGIN}" y="22" font-family="sans-serif" font-size="14" font-weight="bold" fill="{COL["text"]}">'
       'BJ and the Bear rig: side proportion sheet (grid = 4 studs x 1 brick; 1:24)</text></svg>')

out = Path(__file__).resolve().parent.parent / "renders" / "proportion-sheet.svg"
out.parent.mkdir(exist_ok=True)
out.write_text(svg)
print(out)
