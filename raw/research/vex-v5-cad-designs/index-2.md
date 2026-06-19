---
topic: "VEX V5 CAD files for additional bot types — Hero Bots (Flex/Dex/Axel/Striker/Disco/Moby) and advanced/Super-Kit configurations"
slug: vex-v5-cad-designs
researched: 2026-06-18
sources: [./sources-2.md]
prior: [./index.md]
---

# Research: CAD Files for VEX V5 Hero Bots & Advanced Configurations

> Builds on [index.md](index.md) (which covered the Clawbot CAD models, Starter-Kit builds, purchasable expansions, and 3D-printable parts). This update answers a narrower question: **can you get CAD files for the Hero Bots and more advanced robots?** The key finding: **VEX does NOT publish downloadable full-assembly CAD for any Hero Bot** — only interactive 3D build instructions (`instructions.online`) and per-part STEP files. To get a Hero Bot *as a CAD model* you either (a) reconstruct it in the Onshape VEX V5 parts library by following the official 3D build, or (b) download a community-made STEP/SolidWorks version. Several of the latter exist on GrabCAD, including a current-season **Override concept robot** (May 2026, STEP) and full **Super Kit** (120 files) and **WPI RBE1001** (262 files) part/robot libraries.

## Research Questions

1. Does VEX publish downloadable CAD (STEP/SolidWorks) for the Hero Bots (Flex, Dex, Axel, Striker, Disco, Moby)?
2. What community-made CAD exists for Hero Bots and advanced/Super-Kit robots?
3. How would you obtain a Hero Bot as an editable CAD model for the capstone?

---

## Key Findings

### 1. VEX publishes NO full-assembly CAD for Hero Bots — only 3D build instructions + per-part STEP [S18][S19][S20]

Every Hero Bot ships as:
- **Interactive 3D build instructions** at `instructions.online` (step-by-step, rotatable, but NOT a downloadable CAD file)
- **PDF build instructions** + a **Parts List** (BOM) on the build-instructions page
- **Per-part STEP files** — downloadable individually from each part's product page at vexrobotics.com

There is **no "download Axel.step / Striker.sldasm"** button anywhere on VEX's site. This is by design: Hero Bots are meant to be *built physically* from the Competition Starter Kit and disassembled into the next year's Hero Bot with the same parts. [S19][S20]

**Implication for the capstone**: the authoritative digital reference for any Hero Bot's morphology is its `instructions.online` 3D build (visual ground truth) plus its Parts List (the exact BOM / typed-grammar vocabulary). To get an *editable* assembly you must rebuild it.

### 2. Hero Bot dimensions & motor configs are documented (useful even without CAD) [S21][S22]

| Hero Bot | Game (Season) | Notable config |
|----------|---------------|----------------|
| **Axel** | High Stakes (2024-25) | ~350mm × 280mm; 2 motor groups (Arm + Pusher); arm + passive intake flaps |
| **Dex** | Push Back (2025-26) | Competition Starter Kit build; drivable with built-in Drive program |
| **Flex** | Override (2026-27) | Current season Hero Bot |
| **Striker** | Over Under (2023-24) | Two variants (Starter Kit + Super Kit); virtual version in VEXcode VR |
| **Disco** | Spin Up (2022-23) | Has "Introduction / Modifying / Coding" articles |
| **Moby** | Tipping Point (2021-22) | PDF only |

Competition design constraint worth recording: **total motor power ≤ 88W** (mix of 11W and 5.5W Smart Motors), robot must use **V5 System parts only**. [S22]

The VEXcode VR virtual playgrounds contain virtual Hero Bot models (e.g. Axel) with accurate dimensions and motor groups, but these are **not exportable CAD** — they live inside the simulator. [S21]

### 3. Community-made CAD for advanced robots (the practical path to editable files) [S23][S24][S25][S26][S27]

GrabCAD is the richest source. Notable VEX V5 entries beyond the Clawbot (from [index.md](index.md) S4):

| Model | Author / Date | Format | Files | Downloads | What it is |
|-------|--------------|--------|-------|-----------|------------|
| **Vex V5 Override** | Cameron Myers, May 2026 | STEP | 1 | 39 | "VEX Override Concept Robot - Fielding Mode" — a current-season (2026-27) Hero-Bot-style concept robot in editable STEP [S23] |
| **Vex Super Kit Cad Files** | Erdem Karayel, Apr 2020 | SolidWorks 2019 | 120 | 341 | Full V5 **Competition Super Kit + Classroom Super Kit** part library — the advanced/aluminum/HS parts not in the Starter Kit [S24] |
| **RBE1001 VEX V5** | Graham Ornstein, Apr 2022 | SolidWorks + STEP | 262 | 203 | WPI RBE1001 course: full **robot models + field** — a complete advanced-build reference [S25] |
| **VexU Configurable Motor Cartridge** | Oct 2020 | — | — | — | Configurable cartridge part (100/200/600 RPM) [S26] |
| **Vex V5 Legacy Pneumatic Cylinder parts** | Nov 2023 | — | — | — | Pneumatics parts (not in any Starter Kit) [S26] |

> **Provenance caveat:** The "Vex V5 Override" upload carries a public comment alleging it was copied from another source ("Ts was stolen"). Treat community CAD as visualization/reference, not authoritative geometry — same caveat as the CMFDesign concept model in [index.md](index.md). The **Onshape VEX V5 Parts Library** (official, [index.md](index.md) S6) remains the trustworthy source for accurate per-part geometry.

### 4. Onshape is the canonical way to author a Hero Bot / advanced robot as editable CAD [S27][S28]

- The official **Onshape VEX V5 Parts Library** (100+ parts, free education account) is purpose-built to *assemble robots from predesigned parts* — you follow a Hero Bot's `instructions.online` 3D build and place the same parts to recreate it as a live, editable assembly. [index.md](index.md) S6
- Community-shared Onshape docs exist: a **VEXU team's public V5 part library** [S27], a **Push Back field + elements** doc [S28], and various team "design reveal" robots (most teams decline to share the actual robot file). [S28]
- Advanced competition robots shown in these reveals use configs well beyond the Starter Kit: 6× 11W motors geared to 450 RPM, 3.25" omni + traction wheels, odometry pods, linear intakes, color-sort mechanisms — illustrating the upper end of the design space if the project expands hardware. [S28]

---

## Constraints (additional to index.md)

1. **No official Hero Bot assembly CAD exists** — plan to reconstruct from `instructions.online` + Parts List, or accept a community STEP/SolidWorks version with unverified provenance.
2. **Community CAD provenance is unreliable** — use the official Onshape library for geometry that must be accurate; use GrabCAD/STEP uploads for visualization and rough layout only.
3. **Most Hero Bots / advanced robots require the Competition Starter or Super Kit**, not the Classroom Starter Kit ([index.md](index.md) §3) — the CAD is only useful if the matching hardware (aluminum, HS shafts, 8 motors, sensors) is in scope.
4. **Super Kit / advanced parts (pneumatics, aluminum, HS gears) are a different vocabulary** than the Starter Kit grammar — adding them meaningfully enlarges the typed-grammar search space and the procurement budget.

---

## Recommendation

**For the capstone, treat "Hero Bot CAD" as a reconstruction task, not a download:**

1. **Primary**: For any Hero Bot you want to model, open its `instructions.online` 3D build + Parts List, then rebuild it in the **Onshape VEX V5 Parts Library**. This yields an accurate, editable assembly and a clean BOM you can transcribe into `vex_v5_catalog.json`. This is the only path that gives both correct geometry *and* the typed-grammar vocabulary.
2. **Fast visualization**: Pull the **GrabCAD Super Kit (120 files)** and **RBE1001 (262 files)** libraries as ready-made SolidWorks/STEP references for advanced parts and a complete robot+field, and the **Vex V5 Override** STEP for a current-season concept robot — good enough for renders and rough layout, not for authoritative dimensions.
3. **Scope check first**: Hero Bots presuppose the Competition Starter/Super Kit. Before investing in their CAD, confirm via `/decision-create` whether the project stays on the Classroom Starter Kit grammar ([index.md](index.md) recommends Tier 1–3 there) or expands to Super-Kit hardware. The CAD effort only pays off if the hardware is in the plan.

---

## Next Steps

- `/wiki-ingest raw/research/vex-v5-cad-designs/index-2.md` — fold the Hero Bot / advanced-CAD findings into the same source page created from `index.md`
- `/task-add "Reconstruct the current Hero Bot (Flex / Override) in Onshape from instructions.online + Parts List; export BOM into vex_v5_catalog.json"`
- `/decision-create` — "Stay on Classroom Starter Kit grammar vs. expand to Competition/Super Kit (aluminum, HS, 8 motors, pneumatics)"; this gates whether Hero Bot CAD is worth building
- Optional reference downloads (GrabCAD account required): Super Kit CAD (S24), RBE1001 robot+field (S25), Vex V5 Override STEP (S23)
