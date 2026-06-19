---
id: vex-v5-cad-designs
title: Research — VEX V5 CAD Designs, Starter Kit Builds, Purchasable Expansions & 3D-Printable Parts
updated: 2026-06-18
sources:
  - ../../raw/research/vex-v5-cad-designs/index.md
  - ../../raw/research/vex-v5-cad-designs/sources.md
tags: [cad, vex-v5, 3d-printing, morphology, builds]
---

# Research: VEX V5 CAD Designs, Starter Kit Builds & 3D-Printable Parts

A survey of every publicly available CAD model for the VEX V5 Clawbot and related builds, the complete official build list with per-kit requirements, targeted purchases that unlock novel body-type configurations, and the 3D-printable design ecosystem for VEX-compatible parts.

relates_to::[[typed-assembly-grammar]]  
relates_to::[[vex-v5]]  
relates_to::[[vex-v5-starter-kit-configurations]]  
relates_to::[[vex-v5-booster-kit]]  
relates_to::[[3d-printing-file-formats]]

---

## CAD Model Sources

**Three tiers of fidelity exist for the VEX V5 Clawbot:**

**1. Conceptual/visualization (not engineering-grade):** The most popular model online is the CMFDesign Clawbot V5 — available on [TinkerCAD](https://www.tinkercad.com/things/bNzncGpA3CP-clawbot-v5) (869 remixes, Staff Pick, CC BY-NC-ND 3.0, Sept 2021), [Sketchfab](https://sketchfab.com/3d-models/clawbot-v5-d42cfe4740834ff4af28cbec9614d192) (590.9k triangles, CC BY 4.0, March 2022), and a [YouTube showcase animation](https://www.youtube.com/watch?v=o8Pg0BuJoUEA). **Caveat: "parts inspired by VEX Robotics" — lacks exact VEX part numbers and tolerances.** Good for renders and student reference; unsuitable for precise assembly planning.

**2. Engineering-grade assembly:** The [GrabCAD VEX Robotics V5 Clawbot](https://grabcad.com/library/vex-robotics-v5-clawbot-1) by Michael Mohn (Oct 2018) is **61 SolidWorks files** converted from the official VEX STEP file, with all parts mated for full motion (arm raises, claw opens/closes). 1,537 downloads. This is the most-used engineering reference. The [Vex Super Kit CAD Files](https://grabcad.com/library/vex-super-kit-cad-files-1) (Erdem Karayel, 2020, 120 files, SolidWorks 2019) covers the Competition + Classroom Super Kit parts; [RBE1001 VEX V5](https://grabcad.com/library/rbe1001-vex-v5-1) (WPI course, 2022, 262 files) includes a complete robot + field. uses::[[onshape]]

**3. Official per-part STEP:** Every VEX V5 part has a downloadable `.step` file on its vexrobotics.com product page (universal format — SolidWorks, Inventor, Fusion 360, Onshape). This is the authoritative geometry source.

**Cloud-native option:** The **Onshape VEX V5 Parts Library** (free education account, 100+ parts with correct appearances/materials/weights/part numbers, 500,000+ placements) is the fastest way to build assemblies. The SJTU VEX Open Source ([sjtu-vex.github.io/open-source/](https://sjtu-vex.github.io/open-source/)) is a SolidWorks community library updated through May 2026, covering V5RC parts, VEX PRO, pneumatics, and field elements.

uses::[[onshape]]

---

## Official VEX V5 Builds & Kit Requirements

VEX publishes 18 named V5 robot builds. **Only 4 are achievable from the Classroom Starter Kit (276-7010):**

| Build | Kit Required |
|-------|-------------|
| **Speedbot** | Classroom Starter Kit |
| **TrainingBot (Classroom)** | Classroom Starter or Super Kit |
| **V5 Clawbot** | Classroom Starter Kit |
| **Advanced TrainingBot (Classroom)** | Classroom Starter or Super Kit |

All Hero Bots (Flex, Dex, Axel, Striker, Disco, Moby, Crunch, Lift, Flip) require the **Competition Starter Kit**. Super Flip and sensor variants require the Competition Super Kit. All builds have 3D interactive instructions at `instructions.online` and PDF instructions. **No full-assembly CAD is published by VEX for any build** — only per-part STEP + interactive 3D instructions.

derives_from::[[vex-v5-starter-kit-configurations]]

---

## Novel Body Configurations via VEX Purchases

**Drivetrain expansions:** 4" Mecanum Wheels → true omnidirectional drive; 4" + 3.25" Omni Wheels → H-drive; 2" Mecanum/Omni (VRC legal since Jan 2024); Flex Wheels (30A/40A/60A) → roller intakes + flywheels; Tank Tread Kit → crawler drive. **Motor cartridges:** 36:1 (100 RPM, high torque), 6:1 (600 RPM, high speed) — both sold separately.

**Specialty kits** (individually purchasable): Advanced Mechanics and Motion Kit, Linear Motion Kit (rack-and-pinion), Winch and Pulley Kit (elevators), Metal & Hardware Kit (276-2161, bulk fasteners/shafts). **Booster Kit (276-2232, $214.49)** consolidates most of the above plus extra steel channels.

**Structure:** C-Channels (8 sizes, steel or aluminum, holes on 0.500" increments), U-Channels, Angles, Plates, Bars, Gusset Packs — all individually purchasable. Aluminum Structure Kits cut weight while preserving hole compatibility.

derives_from::[[vex-v5-booster-kit]]

---

## 3D-Printable VEX-Compatible Parts

**Critical dimensions** (shared across V5, IQ, EDR — use these for any printable VEX part):

| Dimension | Value |
|-----------|-------|
| Hole spacing | 0.500" (12.70mm) |
| Standard shaft | 0.125" square (3.18mm) |
| HS shaft | 0.250" square (6.35mm) |
| Screw | #8-32 |
| Mounting hole | ~4.2mm |

**Design rule:** holes only — no snap geometry (snaps cannot achieve precision + durability in FDM). Mount with existing VEX #8-32 screws, standoffs, and shaft hardware.

**Community designs:** Thingiverse `thing:1872558` (VEX plastic parts, 3D-printer-friendly, identical to official parts), `thing:1987075` (printable claw kit). Printables `model/1293156` (vectored intake wheels, V5-compatible), `model/698733` (rover wheel, 6.5mm sq axle hole), `model/698466` (8-tooth motor to 0.5" hex adapter — VEX U only), `model/1303938` (3"/4" wheel hub inserts). GitHub: `github.com/owen169/Flex-Wheel-Guides` (Flex Wheel cutting jigs).

**Competition rules note:** 3D printed parts are **not permitted in VRC** (banned entirely in 2025-26); allowed in VEX U; **fully legal for this capstone** (non-competition educational use).

---

## Three-Tier Expansion Strategy for the Capstone

1. **Tier 1 (Gen 0–3):** Official Starter Kit builds — plan mutations in Onshape or GrabCAD before physical assembly; use `instructions.online` as morphology ground truth
2. **Tier 2 (Gen 4–6):** Targeted purchases — Mecanum wheels (new drivetrain topology), additional 100 RPM cartridges (arm performance), or Booster Kit; each maps to a new typed-grammar node
3. **Tier 3 (Gen 7+):** 3D-printed custom parts — design to 0.500" / #8-32 spec; start with Printables `model/1293156` as first non-standard end-effector prototype

constrained_by::[[typed-assembly-grammar]]
