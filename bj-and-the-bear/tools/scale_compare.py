#!/usr/bin/env python3
"""Compare the rig at several body scales while keeping the same wheels.

The body is drawn from the 1:24 layout, scaled by 24/scale. The 2695/2696
wheels stay the same physical size, so at smaller scales they read as
oversized. Two constraints come from the wheels, not the scale:
  * the frame top stays just above the tires (14 plates), so the body is
    lifted to sit on it;
  * axles in a tandem stay at least 6 studs apart (5.4-stud tires + gap).
All rows use the same px/stud, so the length differences are true to size.
Writes renders/scale-compare.svg.
"""
from pathlib import Path

STUD = 9.0
PLATE = STUD * 0.4
MARGIN = 30
ROW_PLATES = 70           # vertical space per row, in plates
WHEEL_R = 6.75            # plates, fixed (2696 tire)
FRAME_TOP = 14            # plates, fixed by the wheels
SCALES = [24, 28, 30, 33]
W_STUDS = 92

COL = {
    "red": "#C91A09", "white": "#FFFFFF", "black": "#1B2A34",
    "gold": "#AA7F2E", "silver": "#A0A5A9", "glass": "#7FA8C9",
    "tire": "#212121", "grid": "#E3E6E9", "text": "#1B2A34",
}
shapes = []


def row(scale, top):
    k = 24 / scale
    base = top + ROW_PLATES * PLATE            # ground line in px

    def X(s):                                   # 1:24 studs -> px
        return MARGIN + s * k * STUD

    def Y(p):                                   # 1:24 plates -> px, body lifted onto the frame
        return base - (FRAME_TOP + (p - FRAME_TOP) * k) * PLATE

    def rect(x0, x1, y0, y1, fill, sw=0.8):
        shapes.append(f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{X(x1) - X(x0):.1f}" '
                      f'height="{Y(y0) - Y(y1):.1f}" fill="{fill}" stroke="{COL["black"]}" stroke-width="{sw}"/>')

    def poly(pts, fill):
        p = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in pts)
        shapes.append(f'<polygon points="{p}" fill="{fill}" stroke="{COL["black"]}" stroke-width="0.8"/>')

    def wheel(x_px):
        cy = base - WHEEL_R * PLATE
        r = WHEEL_R * PLATE
        shapes.append(f'<circle cx="{x_px:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{COL["tire"]}"/>')
        shapes.append(f'<circle cx="{x_px:.1f}" cy="{cy:.1f}" r="{r * 0.52:.1f}" fill="{COL["silver"]}"/>')

    def tandem(center_s):
        """Two axles around a 1:24 centre; at least 6 real studs apart."""
        gap = max(7 * k, 6.0) * STUD
        c = X(center_s)
        return c - gap / 2, c + gap / 2

    # ground + grid
    for s in range(0, W_STUDS + 1, 4):
        x = MARGIN + s * STUD
        shapes.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{base}" stroke="{COL["grid"]}" stroke-width="0.5"/>')
    shapes.append(f'<line x1="{MARGIN}" y1="{base}" x2="{MARGIN + W_STUDS * STUD}" y2="{base}" stroke="{COL["text"]}" stroke-width="1"/>')

    # tractor (1:24 layout)
    rect(1, 32, 12, 14, COL["black"])
    rect(0, 1, 5, 10, COL["silver"])
    rect(1, 12, 15, 43, COL["red"])
    rect(1, 4, 43, 44, COL["red"])
    poly([(4, 43), (7, 50), (12, 50), (12, 43)], COL["red"])
    rect(8.5, 11.5, 50, 52, COL["red"])
    rect(1.3, 4.5, 31, 40, COL["glass"], 0.5)
    rect(1, 12, 29, 31, COL["white"], 0.3)
    poly([(7, 29), (7, 38), (8.5, 39), (12, 39), (12, 29)], COL["white"])
    for y, c in ((28, "gold"), (27, "white"), (26, "gold")):
        rect(1, 12, y, y + 1, COL[c], 0)
    rect(8, 13, 8, 12, COL["silver"])
    rect(12.2, 13.0, 14, 55, COL["silver"])
    rect(20.5, 24.5, 14, 16, COL["black"])
    wheel(X(5))
    for x in tandem(24.5):
        wheel(x)

    # trailer
    t0, t1 = 17.5, 89.5
    rect(t0 - 2.5, t0, 34, 52, COL["red"])
    rect(t0, t1, 40, 54, COL["red"])
    rect(t0, t1, 29, 40, COL["white"])
    for y, c in ((28, "gold"), (27, "white"), (26, "gold")):
        rect(t0, t1, y, y + 1, COL[c], 0)
    rect(t0, t1, 18, 26, COL["red"])
    rect(t0, t1, 17, 18, COL["black"])
    rect(t0 + 18, t0 + 19, 4, 17, COL["silver"])
    for x in tandem(t1 - 9.5):
        wheel(x)

    # label
    trailer = 72 * k
    rig = 89.5 * k
    width = 12 * k
    over = (1.05 * scale / 24 - 1.05) / 1.05 * 100
    label = (f"1:{scale}  |  body ~{width:.0f} wide  |  trailer ~{trailer:.0f} studs  |  "
             f"rig ~{rig:.0f} studs ({rig * 0.8:.0f} cm)  |  wheels {over:+.0f}% oversize")
    shapes.append(f'<text x="{MARGIN}" y="{top + 12}" font-family="sans-serif" font-size="13" '
                  f'font-weight="bold" fill="{COL["text"]}">{label}</text>')


for i, sc in enumerate(SCALES):
    row(sc, 30 + i * (ROW_PLATES * PLATE + 26))

W = MARGIN * 2 + W_STUDS * STUD
H = 30 + len(SCALES) * (ROW_PLATES * PLATE + 26) + 10
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}">'
       '<rect width="100%" height="100%" fill="#FFFFFF"/>'
       f'<text x="{MARGIN}" y="20" font-family="sans-serif" font-size="15" font-weight="bold" fill="{COL["text"]}">'
       'Same 13x24 wheels, smaller body: scale comparison (grid = 4 studs, all rows same px/stud)</text>'
       + "".join(shapes) + "</svg>")
out = Path(__file__).resolve().parent.parent / "renders" / "scale-compare.svg"
out.write_text(svg)
print(out)
