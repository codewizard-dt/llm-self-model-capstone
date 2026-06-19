---
topic: "VEX V5 CAD designs — Clawbot TinkerCAD/Sketchfab models, all builds assembable from the Starter Kit, targeted VEX purchases for novel body configurations, and 3D-printable parts that integrate with the V5 Starter Kit"
slug: vex-v5-cad-designs
researched: 2026-06-18
sources: [./sources.md]
---

# Research: VEX V5 CAD Designs — Starter Kit Builds, Purchasable Expansions & 3D-Printable Parts

> The VEX V5 Clawbot has a high-fidelity SolidWorks assembly on GrabCAD (61 files, mated for full motion) and a conceptual TinkerCAD/Sketchfab version by CMFDesign (869 remixes). Official 3D-interactive instructions exist at `instructions.online` for every VEX build. The **Classroom Starter Kit** supports exactly four official builds: Speedbot, TrainingBot, V5 Clawbot, and Advanced TrainingBot. Novel body configurations come from targeted purchases (Mecanum/Omni/Flex wheels, Tank Tread, specialty motion kits) or 3D-printed parts designed to the 0.500″ hole-spacing / 1/8″ square-shaft standard that all VEX structural metal and motion parts share.

---

## Research Questions

1. What publicly available CAD models exist for the VEX V5 Clawbot (TinkerCAD, Sketchfab, GrabCAD, Onshape)?
2. What are all official VEX V5 builds, and which ones are achievable from the Classroom Starter Kit alone?
3. What targeted VEX purchases (beyond the Starter Kit) unlock novel body-type configurations?
4. What 3D-printable designs exist that integrate with the VEX V5 Starter Kit?
5. What critical dimensions govern 3D-printable VEX-compatible part design?

---

## Current State (Codebase)

- `raw/research/vex-v5-starter-kit-configurations/index.md` — full configurational grammar (motors, gear ratios, wheel types, arm positions) for the Classroom Starter Kit
- `raw/research/vex-v5-starter-kit-configurations/index-2.md` — correction pass: only `front_omni+rear_standard` wheel config and `200rpm` cartridge are valid in the Starter Kit alone
- `raw/research/vex-v5-booster-kit/index.md` — Booster Kit (276-2232, $214.49) adds rack gears, intake rollers, motor clutches, long shafts
- `wiki/knowledge/concepts/typed-assembly-grammar.md` — grammar whose vocabulary = parts catalog; CAD is the reference for what parts exist and how they assemble
- No prior research covers CAD sources, 3D printing, or the full official build list

---

## Key Findings

### 1. The Three Provided CAD Models [S1][S2][S3]

All three are by the same creator, **CMFDesign (@CMFDesign)**, and represent a single design:

| Platform | URL | Details |
|----------|-----|---------|
| **TinkerCAD** | `tinkercad.com/things/bNzncGpA3CP-clawbot-v5` | "Concept claw robot, parts inspired by VEX Robotics" — 215 likes, **869 remixes**, Staff Pick, CC BY-NC-ND 3.0, created Sept 24 2021 |
| **Sketchfab** | `sketchfab.com/3d-models/clawbot-v5-d42cfe4740834ff4af28cbec9614d192` | Same model exported to Sketchfab for 3D viewing — 590.9k triangles, 337k vertices, 247 downloads, CC BY 4.0, March 2022 |
| **YouTube** | `youtube.com/watch?v=o8Pg0BuJoUEA` | "VEX Robotics Concept Clawbot" — showcase animation of the TinkerCAD model |

**Important caveat**: This is a *concept* model — "parts inspired by VEX Robotics", not exact reproductions of official VEX parts. It is excellent for visualization and student reference but does not carry part numbers or precise tolerances for actual CAD assembly. Its 869 remixes make it the most-forked open VEX V5 design online.

### 2. High-Fidelity CAD Sources [S4][S5][S6][S7]

**GrabCAD — VEX Robotics V5 Clawbot** (the engineering-grade reference):
- URL: `grabcad.com/library/vex-robotics-v5-clawbot-1`
- By Michael Mohn, October 18, 2018
- **61 SolidWorks files** — made from the official VEX STEP file, converted to SolidWorks parts, and fully **mated for motion** (arm raises, claw opens/closes)
- 1,537 downloads, categories: Educational, Robotics
- Tags: clawbot, v5, vrc, edr, robotics, vex
- This is the most-used engineering reference for V5 Clawbot CAD

**Official STEP Files (vexrobotics.com)**:
- Every VEX V5 part has a downloadable `.step` (`.stp`) file on its product listing page at vexrobotics.com [S5]
- STEP is universal — compatible with SolidWorks, Autodesk Inventor, Fusion 360, Solid Edge, Onshape, and most other CAD packages

**Onshape VEX V5 Parts Library** (the most accessible cloud-native option):
- 100+ V5 parts and assemblies, free for educators via Onshape Education account [S6][S7]
- Parts placed **500,000+ times** in assemblies
- Correct appearances, materials, weights, and part numbers applied to each component
- Recent additions: 5.5W motors, anti-static traction wheels, Over Under game field, configurable bearing inserts, rubber bumper [S7]
- Access: Onshape App Store → "VEX Library" → insert into any Onshape document

**SJTU VEX Open Source** (SolidWorks, competition-community maintained):
- URL: `sjtu-vex.github.io/open-source/`
- Libraries: Sticker, V5RC Part, VEX PRO Part, Pneumatic, Standard Part, Field Elements
- Updated continuously — last update May 2026 [S8]
- SolidWorks 2020+ format; includes screw configurations, HS gear inserts, pneumatics

### 3. All Official VEX V5 Builds & Their Kit Requirements [S9]

| Build | Kit Required | Description |
|-------|-------------|-------------|
| **Speedbot** | Classroom Starter Kit | Basic 2-motor tank drivetrain; can move forward/reverse and turn |
| **TrainingBot (Classroom)** | Classroom Starter or Super Kit | Quick-build standard drivetrain |
| **V5 Clawbot** | Classroom Starter Kit | Robotic arm with gripping claw on drivetrain base |
| **Advanced TrainingBot (Classroom)** | Classroom Starter or Super Kit | Gripping arm on TrainingBot chassis |
| **TrainingBot (Competition)** | Competition Starter or Super Kit | Quick-build drivetrain for competition use |
| **Advanced TrainingBot (Competition)** | Competition Starter or Super Kit | Arm + claw on TrainingBot; includes AI Vision Sensor mount |
| **Flex** (2026-27 Override Hero Bot) | Competition Starter Kit | Hero robot for current season |
| **Dex** (2025-26 Push Back Hero Bot) | Competition Starter Kit | — |
| **Axel** (2024-25 High Stakes Hero Bot) | Competition Starter Kit | — |
| **Striker** (2023-24 Over Under Hero Bot) | Competition Starter Kit or Super Kit | Two variants |
| **Disco** (2022-23 Spin Up Hero Bot) | Competition Starter Kit | — |
| **Moby** (2021-22 Tipping Point Hero Bot) | Competition Starter Kit | — |
| **Crunch** (2020-21 Change Up Hero Bot) | Competition Starter Kit | — |
| **Lift** (2019-20 Tower Takeover Hero Bot) | Competition Starter Kit | — |
| **Flip** (2018-19 Turning Point Hero Bot) | Competition Starter Kit | — |
| **Super Flip** | Competition Super Kit | Super variant of Flip |
| **Flex (Sensors)** | Beyond Competition Starter Kit | Sensor-enhanced Flex |
| **Dex (Sensors)** | Beyond Competition Starter Kit | Sensor-enhanced Dex |

**3D Build Instructions** are available at `instructions.online` for all named builds; PDF instructions at `content.vexrobotics.com`.

**From the Classroom Starter Kit alone**: Speedbot, TrainingBot (Classroom), V5 Clawbot, Advanced TrainingBot (Classroom) — these four builds constitute the entire official design space for the kit.

### 4. Targeted VEX Purchases for Novel Body Type Configurations [S10][S11][S12]

**Drivetrain / Wheel Expansions:**

| Part | What it enables | Shaft compat. |
|------|----------------|---------------|
| 4" Omni-Directional Wheels (add 2 more) | Full 4-omni holonomic drivetrain; H-drive | Standard 1/8" sq. or 1/4" sq. |
| 3.25" Omni-Directional Wheels | Lower CG, smaller robot footprint | All V5 shafts |
| 4" Mecanum Wheels | True omnidirectional drive (strafe + turn simultaneously) | Standard 1/8" sq. |
| 2" Mecanum Wheels (VRC legal Jan 2024) | Compact mecanum, intake use | HS 1/4" sq. + VersaHex Adapters |
| 2" Omni-Directional Wheels (VRC legal Jan 2024) | Compact intake / support wheels | Standard shafts |
| 2.75" Anti-Static Traction Wheels | Lower clearance, intake / support | Standard shafts |
| Flex Wheels 30A/40A/60A | Roller intakes, flywheels, drivetrain traction | VersaHex Adapters required |
| Tank Tread Kit | Track/crawler drivetrain — traverses obstacles | N/A (tread links) |
| Tank Tread Upgrade Kit | Better traction on track drive | — |

**Arm / Manipulator Expansions:**

| Part | What it enables |
|------|----------------|
| Claw Kit v2 (276-6010) | Standalone grasping end-effector (same as Starter Kit claw) |
| Intake Rollers (276-1499, from Booster Kit) | Roller-intake mechanism |
| Motor Clutch (276-1098, from Booster Kit) | Slip-release for catapult/throw; overload protection |
| Additional V5 Smart Motors (~$52.99 each) | Lifts motor cap above 4 |

**Specialty Kits:**

| Kit | Unlocks |
|-----|---------|
| Advanced Mechanics and Motion Kit | More gears, motion primitives |
| Linear Motion Kit | Rack-and-pinion precise linear slides and lifts |
| Winch and Pulley Kit | Elevator lifts, pulley-driven arms |
| Metal & Hardware Kit (276-2161) | Extra shafts, collars, screws, standoffs |
| Booster Kit (276-2232, $214.49) | All of the above in one bundle + extra steel channels |

**Motor Gear Cartridges (change velocity/torque ratio):**
- 36:1 → 100 RPM (red, high torque — arm lift, precise positioning)
- 18:1 → 200 RPM (green, default, included in kit)
- 6:1 → 600 RPM (blue, high speed — flywheel, fast intake)

**Structure Add-ons:**
- C-Channels (8 sizes), U-Channels, Angles, Plates, Bars — all sold individually
- Aluminum Structure Kits (same shapes, fraction of steel weight)
- Gusset Pack (276-1110) — angle, plus, and pivot gussets for chassis bracing

### 5. 3D-Printable VEX V5 Compatible Designs [S13][S14][S15][S16][S17]

#### Critical Dimensions (mandatory for VEX-compatible 3D prints)

All VEX structural parts (V5, IQ, EDR) share the same mechanical standard:

| Dimension | Value | Notes |
|-----------|-------|-------|
| **Hole spacing** | **0.500" (12.70mm)** | All C-channels, U-channels, angles, plates |
| **Standard shaft** | **0.125" square (3.18mm)** | 1/8" square — used in Starter Kit |
| **High-strength shaft** | **0.250" square (6.35mm)** | 1/4" square — used in Competition kits |
| **Screw standard** | **#8-32** | Star Drive or Hex Drive |
| **Mounting hole diameter** | **~4.2mm** | For IQ connector pins / V5 #8-32 screws |
| **Motor output gear** | **8-tooth plastic** | On V5 Smart Motor output shaft |

**Design rule (from VEX IQ spec, applies to V5):** Use holes only (no snap geometry) — snaps cannot achieve both precision and durability with FDM printing. Mount with existing VEX screws, standoffs, and shaft hardware.

#### Existing Community Printable Parts

**Thingiverse:**
| Thing | URL suffix | Description |
|-------|-----------|-------------|
| V5 VEX CAD 3D model parts (AlexGale) | `thing:3586650` | CAD-library versions of V5 Brain, Battery, Motor, C-bars, gears, 4" wheel — for modeling reference |
| VEX Robotics plastic parts (RJ_12) | `thing:1872558` | Official VEX plastic parts made 3D-printer-friendly; "identical to legal VEX parts" (R7b) |
| Vex claw kit (Greaser57) | `thing:1987075` | Printable claw assembly; needs 4 standoffs + spring metal |
| Vex Claw prototype (3D_Printable) | `thing:420524` | Prototype VEX robotics claw |

**Printables.com (tag: vexv5 / vexrobotics):**
| Model | URL suffix | Description |
|-------|-----------|-------------|
| Vex Rover Wheel (Gabe) | `model/698733` | Full printable wheel — 6.5mm × 6.5mm axle hole (for 1/4" HS shaft with tolerance) |
| Vectored Intake Wheels for VEX V5 | `model/1293156` | Two-part vectored intake wheels with countersinks; built for V5 compat |
| VEX V5 Direct Drive adapter | `model/698466` | Converts plastic 8-tooth motor output to 0.5" hex → enables Flex Wheels on V5 motors (VEX U legal only) |
| VEX Robotics 3" and 4" Wheel Hub Inserts | `model/1303938` | Hub inserts for standard VEX wheel sizes |

**STLFinder (aggregator — spans Thingiverse, Printables, Cults3D, etc.):**
- Search `vex v5`: Printable V5 chassis (2-motor, 4-motor variants), shaft collars, spacers
- Notable: "A Printable chassis for use with V5 VEX robotics parts: The bot is built by adding 2 motors, gears and wheels."

**GitHub:**
- Flex Wheel cutting guides: `github.com/owen169/Flex-Wheel-Guides` — precise cutting jigs for all Flex Wheel sizes

#### 3D Printing Rules in Competition Context
- **VRC (school competition)**: 3D printed parts NOT permitted (2024-25: allowed only as non-functional decorations; 2025-26: banned entirely)
- **VEX U (university)**: 3D printing fully allowed
- **This capstone (non-competition educational use)**: No restrictions — 3D printing is fully viable

---

## Constraints

1. **CMFDesign model is conceptual, not engineering-grade** — it is the most popular V5 Clawbot model online (869 remixes) but lacks exact VEX part numbers and tolerances; use GrabCAD (SolidWorks) or Onshape library for accurate assemblies
2. **Classroom Starter Kit only supports 4 official builds** — radical shape changes require either purchasing additional parts or 3D printing
3. **0.500" hole spacing is non-negotiable** — any 3D-printed structural part must hit this grid or it cannot bolt to existing VEX metal
4. **Snap geometry doesn't survive FDM printing** at required precision — all printed parts must use existing VEX fasteners through holes
5. **High-strength shafts (1/4" square) are not in the Classroom Starter Kit** — Starter Kit uses 1/8" square shafts; some printed wheel designs assume the HS shaft
6. **Onshape free tier requires Education account** — sign up with educator email to access the 100+ part library

---

## Solution Comparison

| Approach | Cost | CAD Quality | Requires 3D Printer | Kit Impact |
|----------|------|-------------|--------------------|---------| 
| **Official builds (Clawbot, Speedbot, etc.)** | $0 | VEX-official instructions.online | No | Starter Kit only |
| **VEX targeted purchases** (wheels, kits) | $10–$250 per item | No new CAD needed | No | Expands physical config space |
| **3D-printed structural/end-effectors** | ~$0–$5 filament | Must design to 0.500" spec | Yes | Extends any config at low cost |
| **GrabCAD/Onshape assembly (modeling only)** | $0 | Engineering-grade | No | Pre-build planning only |

---

## Recommendation

**For the capstone LLM self-model loop, use a three-tier design-space expansion:**

1. **Tier 1 (Gen 0–3): Official Starter Kit builds** — use the GrabCAD SolidWorks assembly and Onshape parts library to plan and visualize Speedbot→Clawbot→Advanced TrainingBot mutations in CAD before physical assembly. The `instructions.online` 3D builds at the VEX build page are the ground-truth morphology references.

2. **Tier 2 (Gen 4–6): Targeted VEX purchases** — expand the typed grammar with one or two specific add-ons: Mecanum wheels for a novel drivetrain topology, additional 100 RPM cartridges for the arm, or the Booster Kit if broader exploration is warranted. Each purchase maps directly to a new grammar node.

3. **Tier 3 (Gen 7+): 3D-printed novel parts** — for shapes beyond what VEX sells, design to the 0.500" hole-spacing / #8-32 screw standard. Start with the CMFDesign Sketchfab model as a visualization reference, then prototype with the Printables vectored-intake wheel or a custom end-effector. The key constraint: use holes not snaps, and print at 100% infill for structural parts.

**For immediate wiki value**: Ingest the GrabCAD and Onshape references as knowledge entries — they are the CAD ground-truth for the morphology grammar.

---

## Next Steps

- `/wiki-ingest raw/research/vex-v5-cad-designs/index.md` — synthesize into `wiki/knowledge/sources/` and update `wiki/knowledge/concepts/typed-assembly-grammar.md` with CAD references
- `/task-add "Add Onshape VEX V5 parts library access to project — create free Education account, document 100+ part list as vex_v5_catalog.json entries"` 
- `/task-add "Download GrabCAD V5 Clawbot SolidWorks assembly and extract per-part STEP files for the typed grammar vocabulary"`
- `/decision-create` — choose whether Tier 2 (buy Mecanum wheels) or Tier 3 (print custom end-effector) is the first Gen 4 experiment; key trade-off is cost vs. novelty
- If 3D printing is available: download `printables.com/model/1293156` (Vectored Intake Wheels) as the first non-standard end-effector prototype
