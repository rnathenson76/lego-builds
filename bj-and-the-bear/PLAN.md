# BJ and the Bear — Kenworth K100 Aerodyne + Reefer Trailer

Build plan. **Status: Phases 1–2 are done (dimensions; rolling chassis in `model/chassis.mpd`). The chassis is waiting for review before Phase 3 (bodywork).**

## 1. Goal

A functional Lego model of BJ McKay's season 1 rig from *BJ and the Bear* (1979):

- **Tractor:** a 1978/79 Kenworth K100 Aerodyne cabover with the raised-roof
  sleeper and tandem drive axles.
- **Trailer:** a matching refrigerated trailer ("reefer").
- **Paint:** red, white and black with gold pinstripes. Phase 1 confirms the
  exact layout from reference photos.

## 2. Scale

**1:28 body on the 13x24 wheels** (2695 + 2696). The wheels read about 17%
oversize. We chose this over true 1:24 to keep the model a manageable length.
`DESIGN.md` has the full dimension sheet.

| Item | Model |
|---|---|
| Body width | **10 studs** (about 11 over the dual tires) |
| Tractor | 27 studs, wheelbase 16 |
| Trailer | **40 ft = 56 studs**, 30-plate walls |
| Whole rig | **71 studs, about 57 cm long and 15 cm tall** |
| Wheels | All 18 used: steer 2 + drive 8 + trailer 8 |

## 3. Decisions so far

| Topic | Decision |
|---|---|
| Wheels | 18 of 2695 + 2696, already owned |
| Scale / width | 1:28 body on the 13x24 wheels, 10-wide (changed from 1:24, 12-wide, to shorten the model) |
| Trailer type | Refrigerated trailer, as in season 1, **40 ft** (changed from 45 ft) |
| Booklets | **Separate** tractor and trailer books |
| Bear figure | Not included |
| Feature list | Agreed as written in section 4 |
| Stripes and livery | Built from tiles and brick color changes. **No stickers** |
| Trailer walls | **Stacked bricks and plates** (smooth sides, 1-plate stripes). Changed from SNOT tiles |
| Pinstripes | Gold, white, gold |
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

- **Stripes:** built from colored plate layers (gold, white, gold) that line
  up across the cab and the trailer. The cab corners and front may use SNOT
  where the stripes wrap around.
- **Trailer walls:** stacked 1 × 8 bricks and plates. `DESIGN.md` section 4
  has the first part estimate. Gold 1 × 8 plates are the likely shortage.
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
- **Gold plates.** The pinstripes need about 28 gold 1 × 8 plates. Pearl Gold
  1 × 8 plates are rare, so Tan or Yellow are the fallbacks.
- **Tight width.** At 10-wide, the steering, the walking beam and the
  frame share about 4 studs between the inner duals. Phase 2 proves this
  first.
- **Old wheel geometry.** The 2695 rim is an old Model Team part. Mounting the
  duals and fitting them between the fenders needs a test early in Phase 2.
- **Library age.** The Ubuntu LDraw library is the 2023 release. Parts newer
  than that won't be available to me. That's fine for this build, but it's
  worth knowing when substituting parts.

## 10. Open questions

None at the moment. All planning questions are answered (see section 3).
