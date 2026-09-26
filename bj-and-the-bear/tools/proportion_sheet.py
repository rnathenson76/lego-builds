#!/usr/bin/env python3
"""Draw a side-elevation proportion sheet of the rig on the stud grid.

All positions are in studs (x, from the front bumper face) and plates
(y, from the ground). 1 stud = 8 mm, 1 plate = 3.2 mm, scale 1:28.
The 2695/2696 wheels are kept, so they read about 17% oversize.
Writes renders/proportion-sheet.svg.
"""
from pathlib import Path

STUD = 12.0            # px per stud in the drawing
PLATE = STUD * 0.4     # a plate is 3.2 mm, 0.4 of a stud
W_STUDS, H_PLATES = 76, 54
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
# 1:28 body on the 1:24 wheels. Wheelbase 16 studs (~141 in); 3-stud gap
# between the cab and the reefer unit, as in the reference photos.
STEER, DRIVE1, DRIVE2 = 4.5, 17.5, 23.5
FIFTH = 19
rect(1, 27, 12, 14, COL["black"])                       # frame rails
rect(0, 1, 5, 10, COL["silver"])                        # bumper
rect(1, 10, 15, 39, COL["red"])                         # cab + sleeper box
rect(1, 3.5, 39, 40, COL["red"])                        # front roof / visor
shapes.append(f'<polygon points="{X(3.5)},{Y(39)} {X(6)},{Y(45)} {X(10)},{Y(45)} {X(10)},{Y(39)}" '
              f'fill="{COL["red"]}" stroke="{COL["black"]}" stroke-width="1"/>')  # Aerodyne raised roof
rect(7, 9.5, 45, 47, COL["red"])                        # roof pod
shapes.append(f'<polygon points="{X(4)},{Y(40)} {X(5.5)},{Y(44)} {X(7)},{Y(44)} {X(7)},{Y(40)}" '
              f'fill="{COL["glass"]}" stroke="{COL["black"]}" stroke-width="0.6"/>')  # upper sleeper window
rect(1.3, 4, 29, 37, COL["glass"], sw=0.6)              # door window
rect(1, 10, 27, 29, COL["white"], sw=0.4)               # white band under the windows
shapes.append(f'<path d="M{X(10)},{Y(27)} L{X(10)},{Y(36)} L{X(7)},{Y(36)} Q{X(6)},{Y(36)} {X(6)},{Y(34)} L{X(6)},{Y(27)} Z" '
              f'fill="{COL["white"]}" stroke="{COL["black"]}" stroke-width="0.4"/>')  # white rear sleeper panel
for y, c in ((26, "gold"), (25, "white"), (24, "gold")):   # pinstripes
    rect(1, 10, y, y + 1, COL[c], sw=0)
rect(7.5, 11.5, 8, 12, COL["silver"])                   # fuel tank + steps
rect(10.2, 11.0, 14, 50, COL["silver"])                 # exhaust stack
rect(FIFTH - 1.5, FIFTH + 1.5, 14, 16, COL["black"])    # fifth wheel
for x in (STEER, DRIVE1, DRIVE2):
    wheel(x)

# ---- trailer ----
T0 = FIFTH - 4          # kingpin 4 studs back from the trailer front
T1 = T0 + 56            # 40 ft = 56 studs
rect(T0 - 2, T0, 30, 45, COL["red"], label="reefer")    # refrigeration unit
rect(T0, T1, 36, 47, COL["red"])                        # upper red
rect(T0, T1, 27, 36, COL["white"], label="40 ft reefer: 56 studs, stacked bricks + plates")
for y, c in ((26, "gold"), (25, "white"), (24, "gold")):
    rect(T0, T1, y, y + 1, COL[c], sw=0)
rect(T0, T1, 17, 24, COL["red"])                        # lower red
rect(T0, T1, 16, 17, COL["black"])                     # floor / side rail
rect(T0 + 15, T0 + 16, 4, 16, COL["silver"])           # landing gear
for x in (T1 - 11, T1 - 5):
    wheel(x)

# ---- dimensions ----
dim(0, 27, 52, "tractor 27 studs")
dim(0, T1, -7, f"whole rig {T1:.0f} studs ({T1 * 8 / 10:.0f} cm)")
dim(STEER, (DRIVE1 + DRIVE2) / 2, 20.5, "wheelbase 16 (141 in)")
vdim(T1 + 1.2, 0, 47, "47 plates")
vdim(-1.5, 0, 45, "45 pl")
for x, name in ((STEER, "steer"), (DRIVE1, "drive"), (DRIVE2, "drive"), (T1 - 11, "trailer"), (T1 - 5, "trailer")):
    text(x, -3.6, name, size=9)
text(FIFTH, 14.8, "5th", size=8, color="#FFFFFF")
text(T0 + 15.5, 2.2, "legs", size=8, anchor="start")

W = X(W_STUDS) + MARGIN
H = Y(-9) + MARGIN
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}">'
       '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
       f'<path d="M0,0 L10,5 L0,10 z" fill="{COL["text"]}"/></marker></defs>'
       f'<rect width="100%" height="100%" fill="#FFFFFF"/>'
       + "".join(shapes) +
       f'<text x="{MARGIN}" y="22" font-family="sans-serif" font-size="14" font-weight="bold" fill="{COL["text"]}">'
       'BJ and the Bear rig: side proportion sheet (grid = 4 studs x 1 brick; 1:28 body, 13x24 wheels)</text></svg>')

out = Path(__file__).resolve().parent.parent / "renders" / "proportion-sheet.svg"
out.parent.mkdir(exist_ok=True)
out.write_text(svg)
print(out)
