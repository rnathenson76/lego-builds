# Handoff: reusable LEGO instruction-booklet generator

**Status: not started.** This folder (`lego-builds/booklet/`) is where the tool
will live. The doc hands the work to a new session. Written 2026-09-27 from the
BJ and the Bear truck session (branch `claude/admiring-newton-q91tvn`).

## 1. Goal

A standalone, reusable command that turns any stepped LDraw model into a
LEGO-style instruction booklet, as both a **printable PDF** and an **HTML
page**. It must work for any build in this repo:
- the BJ and the Bear truck now
- the Minecraft squirrel later (it will move into this repo from
  `rnathenson76/MinecraftMods/lego/`)
- future projects

It should be usable like:

```sh
lego-booklet path/to/model.mpd -o out/ --title "BJ and the Bear" [--submodel NAME]
#  -> out/<name>.pdf, out/<name>/index.html (+ images), out/<name>-parts.csv/.xml
```

## 2. Decisions already made with the user

| Topic | Decision |
|---|---|
| Location | A folder inside `lego-builds`: **`booklet/`**. Not a separate repo |
| Outputs | **Both PDF and HTML** |
| Split | The generator is built in its own session. The truck session carries on separately and will switch to the tool once it's ready |
| Working style | The user wants **a plan communicated and discussed before building**. Present the plan, answer the open questions (section 7) with recommendations, and wait for a go-ahead |

## 3. Starting points: two existing generators

### A. Truck session generator (the base to start from)

This is on branch `claude/admiring-newton-q91tvn`, not yet merged, under
`bj-and-the-bear/tools/`:

| File | What it does |
|---|---|
| `booklet.py` | Parses `0 STEP` from a single-level model. Renders each step with LeoCAD (`-f N -t N`, camera per step). Renders part thumbnails one part at a time (cached in `/tmp/bj-booklet-cache`). Builds A4-landscape pages with PIL: cover, parts inventory grid, one page per step with a "parts for this step" callout and a note, and an optional checklist page. Saves a multi-page PDF |
| `ldr.py` | LDraw helpers: part lookup in the library, recursive bounding boxes, rotations, a `Model`/`Part` writer with steps, a coarse overlap checker |
| `bom.py` | Counts parts by colour, expanding submodels. Writes CSV and a BrickLink wanted-list XML, with an LDraw→BrickLink id map and a colour map |
| `render.py` | Named LeoCAD views (front34, side, top, bottom…) |

- **Example inputs:** `bj-and-the-bear/model/front-axle-test.mpd` (35 parts,
  12 steps) with `front-axle-test.cameras.json`, plus
  `instructions/front-axle-test.notes.json` and `.checklist.json`.
- **Example output:** `instructions/front-axle-test.pdf`.
- **Multi-submodel test input:** `bj-and-the-bear/model/chassis.mpd`, three
  models (rig → tractor + trailer).

What it lacks:
- sub-assembly callouts (submodels)
- faded earlier steps / new-part emphasis
- HTML output
- in-file metadata (cameras and notes are side JSON files today)
- multiple steps per page
- page numbers on the cover and inventory pages

### B. MinecraftMods squirrel generator (take the good ideas)

This is in `rnathenson76/MinecraftMods`, under `lego/`. It's a public repo:
clone read-only with
`GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/rnathenson76/minecraftmods`.

| File | What it does |
|---|---|
| `tools/make_booklet.py` | Builds `booklet/index.html` from `booklet/steps.json`. Includes autocrop, part-image CSS variables, colour swatches, callouts, per-model parts lists, and "any colour" hidden parts (colour −1) |
| `tools/render/render.mjs` + `render.html` | three.js `LDrawLoader` in headless Chromium (Playwright). **Earlier steps are drawn faded** (colours remapped to 1000+c). It has several candidate views, a steady zoom per section (`minRadius`), sections/sub-assemblies (`s.section`, `s.asm`), and hero shots |
| `models/*.mpd` | Scrawny squirrel (~112 parts) and buff squirrel (~2,000 parts), both with build steps. **Good test inputs, especially for scale and performance** |

Its limits: it's tied to the squirrel project. `steps.json` comes from
`squirrel_lego.py`, the paths are hard-coded, and the renderer needs Node,
three.js, Chromium and a local LDraw library.

**Recommendation from the truck session:** keep LeoCAD for rendering. It's one
apt install, runs headless, and does step ranges, `--fade-steps`,
`--highlight` and per-step cameras. Keep the squirrel's HTML ideas: faded
earlier steps, sub-assembly sections, per-model parts lists and "any colour"
parts. Evaluate three.js only if LeoCAD can't meet a requirement.

## 4. Requirements (proposed; confirm them in the plan)

1. **Input:** any LDraw `.ldr`/`.mpd` with `0 STEP` metas, including files
   exported from BrickLink Studio or LDCad. Submodels referenced inside a step
   become **sub-assembly callouts**, built first in their own frame (or inline,
   configurable).
2. **Per-step metadata in the model file**, so no side files are needed. For
   example:
   - `0 !BOOKLET CAMERA <lat> <lon>`
   - `0 !BOOKLET NOTE <text>`
   - `0 !BOOKLET PAGEBREAK`
   - `0 !BOOKLET ANYCOLOUR` (hidden parts)

   Side JSON can stay as an optional override. Keep the LPub3D/Studio metas in
   mind (`0 !LPUB …`, `0 ROTSTEP`), and at least don't choke on them.
3. **Rendering:**
   - The finished model shown in full colour.
   - **Earlier steps faded**, so new parts stand out.
   - A steady zoom within a sub-assembly.
   - Part thumbnails cached across runs.
4. **Outputs:**
   - PDF, A4 landscape (Letter as an option), with a cover, a parts inventory,
     steps (1–4 per page, automatic), sub-assembly frames, a checklist or
     notes page, and page numbers.
   - HTML: the same content, responsive, working offline, with images alongside
     it.
   - Parts CSV and a BrickLink XML (reuse `bom.py`).
5. **CLI plus an importable Python package.** Put a `README.md` in `booklet/`
   with install steps and examples.
6. **Tests:** fast unit tests (step parsing, BOM counts, metadata) that don't
   need LeoCAD, plus a slow "golden" run on `front-axle-test.mpd` and the
   scrawny squirrel.

## 5. Environment notes (cloud container)

- **Installs:**
  - `sudo apt-get update && sudo apt-get install -y leocad ldraw-parts xvfb`.
    Run `apt-get update` first: a stale index gives 404s.
  - `pip install numpy pillow pymupdf cairosvg`. PyMuPDF is used to rasterise
    PDFs for self-review.
  - The LDraw library installs to `/usr/share/ldraw`. It's the **2023
    release**, so newer parts are missing; some ids have moved (e.g. 4185 →
    4185a, 6538 → 6538a, 32123 → 32123a).
- **Network:** `library.ldraw.org` and most reference sites are blocked by the
  proxy. The apt mirrors, PyPI and npm work.
- **LeoCAD quirks:**
  - Run it under `xvfb-run -a`.
  - `-i out.png -f N -t N` writes `outNN.png` (numbered), so glob for it.
  - Step renders use a **dark grey background**; normal renders are white.
    Black parts are close to the dark grey, so **don't colour-key the
    background**. Flood-fill it from the image border (see `white_bg()` in
    `booklet.py`).
  - The camera framing fits the whole model, which gives a steady zoom.
  - Useful flags: `--shading full -ss 6 --aa-samples 8`.
- **Self-review:** there's no PDF viewer. Rasterise pages with PyMuPDF and look
  at contact sheets. That's how the truck booklet's black-parts bug was
  caught.

## 6. Acceptance checks

- `lego-booklet bj-and-the-bear/model/front-axle-test.mpd` reproduces the
  current PDF's content, now with faded earlier steps and in-file metadata,
  and also writes HTML.
- `chassis.mpd` produces sub-assembly callouts (tractor chassis and trailer
  chassis) in one booklet, or one booklet per submodel with `--submodel`.
- The scrawny squirrel `.mpd` from MinecraftMods produces a sensible booklet
  with no project-specific code.
- The buff squirrel (~2,000 parts) finishes in reasonable time. Record it.

## 7. Open questions for the user (answer with recommendations in the plan)

1. **Page size:** A4 or US Letter by default?
2. **Styling:** close to official LEGO (callout boxes, big step numbers), or
   the squirrel booklet's web look?
3. **Sub-assemblies:** always their own framed pages, or inline callouts when
   they're small?
4. **The truck repo's `tools/booklet.py`:** should the new session leave it
   alone? (Recommended: yes. The truck session switches over once the tool is
   ready.)

## 8. Git

- Work in **`booklet/` only** to avoid conflicts with the truck session.
- The starter code is on `claude/admiring-newton-q91tvn`. Fetch that branch
  and copy the files in. **Don't edit `bj-and-the-bear/`.**
- Commit and push to the branch your session is given.
