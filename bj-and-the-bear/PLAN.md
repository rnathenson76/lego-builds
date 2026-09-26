# BJ and the Bear — Kenworth K100 Aerodyne + Reefer Trailer

Build plan. **Status: plan agreed. Phase 1 (reference and dimensions) is in progress.**

## 1. Goal

A functional Lego model of BJ McKay's season 1 rig from *BJ and the Bear* (1979):

- **Tractor:** a 1978/79 Kenworth K100 Aerodyne cabover with the raised-roof
  sleeper and tandem drive axles.
- **Trailer:** a matching refrigerated trailer ("reefer").
- **Paint:** red, white and black with gold pinstripes. Phase 1 confirms the
  exact layout from reference photos.

## 2. Scale: set by the wheels

| Item | Value |
|---|---|
| Wheel | **2695** Model Team rim 30 mm, with **2696** tire 13 x 24 (Ø 43.2 mm) |
| Real tire | 11R22.5, about 1.05 m tall |
| **Scale** | **about 1:24.** 1 stud (8 mm) is about 19 cm real, and 1 brick height is about 23 cm real |
| Wheels on hand | **18.** That matches the real wheel count exactly: steer 2 + drive 8 + trailer 8 |

### Target dimensions (approximate; Phase 1 checks them against references)

| Element | Real | Model |
|---|---|---|
| Body width | 96 in / 2.44 m | **12 studs** (agreed) |
| Width over the dual tires | about 2.44 m | about 12–13 studs |
| Tractor length | about 6–6.5 m | about 30–34 studs |
| Trailer length | 45 ft (13.7 m) | **about 71 studs** (agreed; 45 ft to start) |
| Trailer height (13'6") | 4.1 m | about 18 bricks |
| Whole rig | about 17 m | about 90 studs (about 72 cm); see DESIGN.md |

## 3. Decisions so far

| Topic | Decision |
|---|---|
| Wheels | 18 of 2695 + 2696, already owned |
| Width | 12-wide |
| Trailer type | Refrigerated trailer, as in season 1, **45 ft** |
| Booklets | **Separate** tractor and trailer books |
| Bear figure | Not included |
| Feature list | Agreed as written in section 4 |
| Stripes and livery | Built from tiles and brick color changes. **No stickers** |
| Trailer walls | **Smooth tiles**, not panels |
| Function | **Functional** (feature list in section 4) |
| Deliverables, in order | Design + renders, then parts list, then build files + **Lego-style instruction booklet** |
| Parts check | After the plan is agreed, we check the parts inventory together before committing to the build |

## 4. Functional features (proposed)

Features are grouped by priority so that a missing part only drops the lower
ones.

**Must have**
1. **Working steering.** The front axle steers through a rack, turned by a
   "hand of god" knob. A knob at the rear of the sleeper roof or behind the cab
   keeps it hidden.
2. **Tilting cab.** A cabover without a tilting cab isn't a real K100. The cab
   pivots forward on hinges at the front of the frame and reveals a
   brick-built engine (a Cummins or CAT style inline-6).
3. **Detachable trailer.** A fifth wheel with a kingpin. The trailer lifts off,
   and there is a pivot for turning.
4. **Opening doors.** Both cab doors, plus the trailer's rear barn doors on
   hinges.

**Nice to have**

5. **Trailer landing gear** that lowers, either cranked or on simple
   sliding legs, so the trailer stands on its own.
6. **Walking-beam suspension** on the tractor's tandem drive axles (a pivot
   between the two axles).
7. **Opening sleeper door or window.** (No Bear figure.)

**Not planned** (too much complexity for the payoff): working lights, a
motorized drive, and trailer steering.

## 5. Model breakdown

The model is designed and delivered as submodels. Each one is a separate chunk
in the LDraw file and a separate section of the booklet:

```
bj-and-the-bear.mpd
├── tractor
│   ├── chassis          frame rails, steer axle and steering, drive tandem, fifth wheel
│   ├── engine           brick-built engine under the cab
│   ├── fuel-tanks       chrome/silver tanks, steps, battery box
│   ├── cab              front, grille, headlights, windshield, doors, tilt hinge
│   ├── sleeper          Aerodyne raised roof, side windows
│   └── details          stacks, air horns, mirrors, mudflaps, air lines
└── trailer
    ├── frame            main rails, kingpin plate, landing gear, tandem bogie
    ├── box              tiled side, roof and front walls
    ├── reefer-unit      refrigeration unit on the front wall
    └── rear             barn doors, lights, underride bar
```

### Construction approach

- **Stripes:** built SNOT-style (studs not on top). Tiles on sideways-facing
  studs make the stripe bands in white, black and gold. For the gold, the
  choice is Pearl Gold or Tan/Yellow; I'll check which reads best in renders.
- **Trailer walls:** SNOT tiles on brackets over a brick frame. A 64-stud side
  needs **a lot of tiles**. The parts check will probably hinge on this, so
  I'll give tile counts per size and color early, in Phase 3.
- **Wheels:** check how the 2695 hub mounts in LDraw (rim geometry) during
  Phase 2. Duals are two rims side by side on one axle.

## 6. Tooling (verified working in this environment)

- **LDraw parts library + LeoCAD**, run headless. They render the model and
  each building step to PNG. I've tested this with the 2695/2696 wheel.
- **Nicer renders:** LeoCAD renders with LDraw-style edges. POV-Ray is also
  installed if we want photo-style shots later.
- **Instruction booklet:** I'd write a script that goes step by step. For each
  step it renders the step image with the new parts highlighted and earlier
  steps faded, builds the Lego-style "parts for this step" callout from the
  LDraw file, and adds a submodel callout wherever a sub-assembly happens.
  All of that is assembled into a **PDF booklet**.
- **Optional polish, on your side:** the same `.mpd` file opens in **BrickLink
  Studio** (free desktop app). Studio has photoreal rendering and its own
  Instruction Maker if you want an official-looking alternative.
- **Parts list:** a CSV, plus a **BrickLink Wanted List XML**. You can upload
  the XML to BrickLink to compare against your inventory, or to buy what's
  missing.

## 7. Phases and review gates

We check in with each other at every ✋ gate before moving on.

| Phase | Work | Output | Gate |
|---|---|---|---|
| **1. Reference and dimensions** | Collect reference photos and specs for the K100 Aerodyne and the trailer. Map the stripes. Scale everything to the stud grid. | `DESIGN.md` with a dimension sheet, stripe map and color list | ✋ Confirm proportions and colors |
| **2. Rolling chassis** | Frame, all 18 wheels, steering, suspension, fifth wheel, trailer frame and landing gear | LDraw submodels plus renders | ✋ Check the mechanics and stance |
| **3. Bodywork design** | Cab, sleeper, engine, trailer box, reefer unit, stripes | Full model file plus **renders** (front 3/4, rear 3/4, side, cab tilted, doors open) | ✋ Design review. We iterate on looks here |
| **4. Parts list** | Full BOM from the model, with part counts by color | `parts/*.csv` + BrickLink XML | ✋ **Inventory check.** You compare against your parts, and we substitute where needed |
| **5. Build files** | Final `.mpd` with building steps | `model/bj-and-the-bear.mpd` | — |
| **6. Instruction booklet** | Generated PDFs: one tractor book and one trailer book | `instructions/*.pdf` | ✋ Proof-read |

## 8. Repository layout

```
bj-and-the-bear/
├── PLAN.md            this file
├── DESIGN.md          Phase 1: dimensions, references, stripe map
├── model/             .mpd / .ldr files
├── renders/           PNG renders
├── parts/             BOM CSV + BrickLink XML
├── instructions/      booklet PDFs
└── tools/             render and booklet scripts
```

## 9. Risks

- **I can't see the model the way you can.** I write LDraw coordinates as text
  and check them through renders. Expect a few rounds of iteration per
  submodel, especially at the Phase 3 gate.
- **Tile quantities.** Smooth-tiled trailer walls in white could need several
  hundred tiles. That is the most likely shortfall in the parts check.
- **Old wheel geometry.** The 2695 rim is an old Model Team part. Mounting the
  duals and fitting them between the fenders needs a test early in Phase 2.
- **Library age.** The Ubuntu LDraw library is the 2023 release. Parts newer
  than that won't be available to me. That's fine for this build, but it's
  worth knowing when substituting parts.

## 10. Open questions

None at the moment. All planning questions are answered (see section 3).
