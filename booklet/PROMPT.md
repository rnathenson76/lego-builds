# Prompt for the booklet-generator session

Copy everything below the line into a new Claude Code session on
`rnathenson76/lego-builds`.

---

We're building a reusable LEGO instruction-booklet generator in the `booklet/`
folder of this repo. It turns any stepped LDraw model (`.ldr`/`.mpd`) into a
LEGO-style booklet, output as both a printable PDF and an HTML page, plus a
parts list (CSV and BrickLink XML).

Start by reading `booklet/HANDOFF.md`. It covers:
- the goal and the decisions already made
- the two existing generators to build from (the truck session's
  `bj-and-the-bear/tools/booklet.py` on branch `claude/admiring-newton-q91tvn`,
  and the squirrel booklet in the public repo `rnathenson76/MinecraftMods`,
  under `lego/`)
- proposed requirements and acceptance checks
- environment setup and LeoCAD quirks
- open questions

The starter code and the test models are on `claude/admiring-newton-q91tvn`,
so fetch that branch first.

How I like to work: **make a plan, tell me about it, and discuss it with me
before you build.** Your first reply should be the plan, with your
recommendations on the open questions in section 7 of the handoff. Only work
inside `booklet/`. Don't change `bj-and-the-bear/`, because another session is
working on the truck.
