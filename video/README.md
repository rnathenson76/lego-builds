# STARBRICK

A 20-second sci-fi brick film, built and animated entirely in code
(`starbrick.py`) and path-traced in Blender Cycles.

| Time | Shot |
|---|---|
| 0–3 s | Sunrise over a planet built from ~11,000 bricks |
| 3–8 s | Hero starfighter flyby |
| 8–13 s | Zero-G assembly of an orbital station |
| 13–17 s | Dogfight: a laser hit blows the enemy apart brick by brick |
| 17–20 s | The debris assembles into the STARBRICK title |

What it does:
- **Bricks.** Parts are modelled to real system dimensions (8 mm pitch,
  9.6 mm bricks, 3.2 mm plates). They have hollow undersides, tubes,
  bevelled edges, textured slope faces and slight per-brick colour drift.
- **Plastic.** ABS is shaded with IOR 1.54, light subsurface scattering,
  varying roughness and micro-surface bump.
- **Lens.** Depth of field uses real miniature-scale apertures, so the film
  reads like macro toy photography. Motion blur uses a 180° shutter.
- **Look.** AgX colour management, fog-glow bloom, anamorphic streaks,
  slight chromatic aberration and a light grade. Grain and the 2.39:1
  letterbox are added at assembly.

Reproduce (needs `pip install bpy==4.5.14` on Python 3.11, plus ffmpeg):

    video/render_all.sh 28 /path/to/python-with-bpy   # ~5 h on 4 CPU cores
    video/assemble.sh video/starbrick.mp4
