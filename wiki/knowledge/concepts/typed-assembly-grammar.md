---
id: typed-assembly-grammar
title: Typed Assembly Grammar
aliases: [Restricted Design Language, Typed Parts Grammar, Searchable Assembly Grammar]
updated: 2026-06-22
sources:
  - ../../raw/Feasibility of a Human-Built Generational Robot Software Factory.pdf
  - ../../raw/Feasibility of a Software-Factory Approach to Learning Robots That Assemble Additional Robots from M.pdf
tags: [concept, robotics, morphology, search, representation]
---

# Typed Assembly Grammar

The central feasibility constraint shared by the robot-factory reports: **morphology search must happen over a restricted, typed design language — not unrestricted free-form CAD.** A robot is represented as a composition of *typed modules* (wheelbases, arm segments, sensor masts, gripper choices, gear trains, body layouts) with declared ports, not as arbitrary solids.

## Why It Makes the Problem Tractable

The finite port counts, fixed actuator classes, and assembly tolerances of real kits make the design problem **implementable only when constrained** — "that limitation is not a weakness; it is what makes the concept implementable." A typed grammar gives:
- a bounded, searchable design space (evolution/LLM search converges)
- guaranteed buildability (every generated design maps to real parts + fixtures)
- a clean data contract between designer and builder (port maps, BOM, assembly steps)

## Research Lineage

- **Lipson & Pollack (2000)** — evolved robots from basic building blocks ([[hod-lipson]])
- **Matthews et al.** — optimized voxel soft-robot designs from structured parameterizations
- **DERL** — co-optimized morphology *and* control under environmental tasks
- **Text2Robot** — added manufacturability + electronics-placement constraints to generated body-control designs

None of these search over arbitrary geometry; all search over structured parameterizations.

## Concrete Form

The generational report gives a machine-readable example: a JSON manifest with `constraints` (`max_ports`, `max_unique_part_types`, `must_include`, `forbid_closed_loops`, `max_build_steps`), a `morphology` block (`chassis`, `wheel_diameter_mm`, `sensor_mast`, `tool`), and an `electronics.hub_ports` map. This is exactly the kind of **internal self-representation** a generating model would emit and mutate.

## Enumerated Design Space — VEX V5 Classroom Starter Kit (from [[vex-v5-starter-kit-configurations]])

The Starter Kit's design space has been explicitly enumerated. The grammar's vocabulary is small and bounded by 6 free parameters:

> **Contradiction:** The vocabulary below was corrected on 2026-06-17 (source: `raw/research/vex-v5-starter-kit-configurations/index-2.md`). Three fields included options requiring additional purchases. See the corrected spec immediately below.

~~Stale (2026-06-16):~~
```json
{
  "motor_allocation": ["2drive+2free", "2drive+1arm+1claw", "4drive", "3drive+1manip"],
  "arm_position":     ["front", "rear", "side", "absent"],
  "end_effector":     ["claw_grasper", "bare_arm", "roller", "none"],
  "wheel_config":     ["front_omni+rear_standard", "all_standard", "all_omni"],
  "arm_gear_ratio":   ["7:1", "1:1"],
  "cartridge":        ["100rpm", "200rpm", "600rpm"]
}
```

**Corrected (2026-06-17) — Starter Kit 276-7010 only:**
```json
{
  "motor_allocation": ["2drive+2free", "2drive+1arm+1claw", "4drive", "3drive+1manip"],
  "arm_position":     ["front", "rear", "side", "absent"],
  "end_effector":     ["claw_grasper", "bare_arm", "none"],
  "wheel_config":     ["front_omni+rear_standard"],
  "arm_gear_ratio":   ["7:1", "1:1"],
  "cartridge":        ["200rpm"]
}
```

| Removed entry | Reason |
|---|---|
| `cartridge: "100rpm"`, `"600rpm"` | 36:1 and 6:1 cartridges are sold separately; motors ship with 18:1 (200 RPM) installed |
| `wheel_config: "all_standard"`, `"all_omni"` | Kit has 2 omni + 2 standard wheels; 4 of one type is impossible without a purchase |
| `end_effector: "roller"` | Intake Roller (276-1499) is a Booster Kit (276-2232) part, not in the Starter Kit |

Valid combinations ≈ **10–15** (corrected from the prior ~15–30; the true raw slot count is 96, down from 1,152). **This small, finite space is exactly what makes the grammar "typed" in the Lipson sense** — the LLM generator can enumerate and search it exhaustively. The capstone generation ladder maps naturally: [[speedbot]] = Gen 0 (simplest valid sentence), Clawbot = Gen 1 (full vocabulary), mutations = Gen 2–5 (search over the remaining valid sentences).

## Concrete Exemplar: VEX V5 Clawbot (276-6009-750 Rev6)

The [[vex-v5-clawbot-build-instructions]] document is the clearest real-world instantiation of a typed assembly grammar in this project's orbit. Every part carries a VEX SKU; the build steps are ordered assembly instructions with a per-step BOM; port assignments map directly to the `electronics.hub_ports` block; gear ratios produce the `capability_model` parameters (torque budget, reach). The 41 build steps are exactly the `assembly_steps` array in the generation manifest YAML — each with an `action` and implicit `verify`. The hacksaw-cut constraint (step 28) maps to `constraints.requires_cutting: true`.

The Clawbot is **not** the full grammar — it is one valid sentence in it. The grammar's **vocabulary** is the full VEX V5 parts catalog; the **rules** are the port counts, fastener compatibility, and structural load limits. The LLM generator's job is to author new sentences (morphologies) from that vocabulary. derives_from::[[vex-v5-clawbot-build-instructions]]

## Booster Kit Vocabulary Expansion (from [[vex-v5-booster-kit]])

The Booster Kit (276-2232) is a concrete example of **vocabulary expansion** — new word types added to the grammar without changing its rules. Four new node types it introduces:

- **`linear_actuator`** — 19T rack gear + Gear Kit pinion + motor → rack-and-pinion linear motion; enables precise linear pull/extension (distinct from rotary drive pull)
- **`intake`** — intake rollers; continuously-rolling grab as alternative to the fixed-jaw claw
- **`long_arm`** — 12" shafts; longer `arm_length` directly raises throw release velocity (`v = ω × arm_length`) and reach
- **`slip_release`** — motor clutches; slip-gear catapult release + passive overload protection

The existing Clawbot vocabulary (`claw_grab`, `drive_pull`, `arm_throw`) remains; the Booster Kit adds branches without removing any. Each new type brings physical parameters (rack pitch, roller diameter, shaft length, clutch torque limit) the self-model's capability layer must encode in `vex_v5_catalog.json`.

## Launch-Disc Vocabulary Expansion (from [[vex-launch-disc-parts]])

A **flywheel disc launcher** is a new end-effector node type that extends the grammar without changing its rules. It is an exclusive swap: `flywheel_launcher` replaces `claw_grasper` / `bare_arm` and requires the `cartridge: 600rpm` constraint. Three individual part purchases are the minimum to add this node type:

| SKU | Part | Grammar role |
|-----|------|-------------|
| 276-5842 | V5 Motor 6:1 Cartridge (600 RPM) | Sets `cartridge: 600rpm` on the arm motor |
| 217-6449 | Straight Flex Wheel 3" OD 60A | Flywheel contact surface at end-effector |
| 217-7947 | VersaHex Adapters v2 1/4" Sq. 8-pack | Shaft adapter to mount flex wheel on V5 HS shaft |

The corrected grammar end-effector field now becomes:

```json
{
  "end_effector": ["claw_grasper", "bare_arm", "none", "flywheel_launcher"]
}
```

With the constraint:

```json
{
  "constraints": {
    "flywheel_launcher_requires_cartridge": "600rpm"
  }
}
```

Because all 4 Starter Kit motors are in use on the Clawbot, `flywheel_launcher` forces `motor_allocation` to reassign the arm motor — making it a morphologically exclusive choice. An additional Smart Motor (276-4840) lifts this exclusivity by adding a 5th motor. See full mechanism detail: [[vex-flywheel-disc-launcher]].

## Aesthetic Vocabulary Extension (from [[aesthetic-vocabulary]])

The functional grammar covers motor allocation, arm position, wheel config, gear ratio, and end effector. A separate non-functional layer extends it with **visual self-expression** parameters the LLM can author independently of functional choices:

```json
{
  "aesthetic_vocabulary": {
    "body_panel":      { "material": ["corrugated_plastic","craft_foam","cardboard","acrylic","3d_print","none"],
                         "position": ["left_side","right_side","top_deck","front_face","rear_skirt"] },
    "surface_markings":{ "tape_pattern": ["none","stripes","chevron","solid_block","diagonal"],
                         "identity_label": ["sticker_numeral","painted_numeral","none"] },
    "appendages":      { "type": ["none","antennae","swept_fins","dorsal_ridge","cage_frame","whiskers"],
                         "material": ["pipe_cleaner","craft_wire","foam","cardboard","3d_print"] },
    "accent_lighting": { "type": ["none","neopixel_strip","neopixel_ring"],
                         "pattern": ["solid","breathing","chase","generation_pulse"] }
  }
}
```

This layer is **non-functional** — it does not affect motor commands or telemetry contracts. Its value: makes generations visually distinct, lets the LLM embed hypotheses in visible form ("wide side panels = testing mass distribution"), and creates a photographable narrative arc across generations. All materials attach via existing VEX square holes (velcro, zip ties, or screws at 0.5" spacing) with no modification to the metal. See [[aesthetic-vocabulary]] for the full material catalog and cost tiers.

## CAD as Ground Truth for the Grammar Vocabulary (from [[vex-v5-cad-designs]])

The grammar's vocabulary = the parts catalog. CAD is the authoritative source for what parts exist, how they assemble, and what their physical parameters are.

**Three tiers of VEX V5 CAD fidelity:**

| Tier | Source | Use |
|------|--------|-----|
| **Concept/visualization** | CMFDesign TinkerCAD (869 remixes), Sketchfab | Renders, student reference — no part numbers or tolerances |
| **Engineering assembly** | GrabCAD V5 Clawbot (61 SolidWorks files, mated for motion); Vex Super Kit 120-file library; RBE1001 262-file WPI library | Layout planning, geometry reference |
| **Official per-part STEP** | Every vexrobotics.com product page has a `.step` download | Authoritative geometry; import into any CAD package |

**Best starting point:** The **Onshape VEX V5 Parts Library** (100+ parts, free education account, 500k+ placements) — create an Onshape Education account, open the VEX Library app, assemble any build by following `instructions.online`. This is how to build a Hero Bot as editable CAD when VEX publishes no full-assembly download for them.

**Official build map (kit-gated):** Only 4 builds from the Classroom Starter Kit (Speedbot, TrainingBot, Clawbot, Advanced TrainingBot); all Hero Bots (Flex, Dex, Axel, Striker, Disco…) require the Competition Starter Kit. This gates which morphologies are physically available for each generation of the self-model loop.

**Novel configurations via purchase:** Mecanum/Omni/Flex wheels, Tank Tread Kit, Linear Motion Kit, Winch & Pulley Kit, additional motor cartridges — each maps to a new grammar node.

**3D-printable extensions:** Community designs that bolt into VEX metal exist on Thingiverse and Printables. Critical dimension: **0.500" hole spacing / 1/8" square shaft** (shared by all V5, IQ, EDR structural parts). Use holes only, no snaps. Fully legal for the capstone (non-competition use).

references::[[vex-v5-cad-designs]]

## Passive-Scoop Vocabulary Extension — No-Purchase Morphology Mutation (from [[clawbot-scoop-replacement]])

The standard `claw_grasper` end-effector can be replaced with a **`passive_scoop`** sourced from a household kitchen item (serving spoon, powder scoop, ladle) without purchasing any VEX parts. This is the first grammar mutation that costs $0 and uses non-VEX material.

The mounting interface at the arm tip exposes two parallel C-channel bracket faces **1" apart** with two #8-32 holes **0.5" apart** (standard VEX grid). Any item with a handle ≤ ~22 mm wide can be clamped there by drilling two 11/64" clearance holes and reusing the original screws + hex nuts.

The corrected grammar end-effector field now becomes:

```json
{
  "end_effector": ["claw_grasper", "bare_arm", "none", "flywheel_launcher", "passive_scoop"]
}
```

With the constraint:

```json
{
  "constraints": {
    "passive_scoop_requires_motor": false,
    "passive_scoop_frees_motor_port": true
  }
}
```

**Self-model consequence:** `passive_scoop` sets `grip_force: null`, changes the `grab` primitive from `set_max_torque + spin_for(degrees)` to `scoop_under + arm_lift`, and frees one V5 Smart Motor for future reuse. The LLM self-model must note: "I cannot grip; I can only scoop objects I can slide under."

**Ranked household candidates:** plastic serving spoon (★★★★★) > stainless serving spoon (★★★★) > plastic powder/coffee scoop (★★★★) > zip-tie mount with any item (★★★).

references::[[clawbot-scoop-replacement]]

## Game Object Node (from [[game-object-selection]])

The grammar requires a `game_object` node declaring the physical properties of the object the robot manipulates. All three handling morphologies (claw, passive scoop, flywheel) constrain this node differently — the object must satisfy the intersection of all active morphologies. The GEN-0 default (racquetball) sits in the **55–65 mm** window where claw, scoop, and flywheel constraints all overlap:

```json
{
  "game_object": {
    "type": "racquetball",
    "diameter_mm": 57,
    "weight_g": 40,
    "material": "hollow_rubber",
    "compressibility": "medium",
    "color": "blue_or_green",
    "cost_usd": 2.0
  }
}
```

The game object's physical parameters feed directly into [[task-telemetry-contract]] `predicted` blocks: `diameter_mm` drives the claw position proxy; `weight_g` drives the catapult range prediction; `compressibility` drives the flywheel energy-transfer model. See full selection rationale and alternative candidates: [[game-object-selection]].

constrained_by::[[physical-robot-software-factory]]  
relates_to::[[reality-gap]]  
derived_from::[[feasibility-human-built-generational-factory]]  
exemplified_by::[[vex-v5-clawbot-build-instructions]]  
enumerated_by::[[vex-v5-starter-kit-configurations]]  
base_sentence::[[speedbot]]  
expanded_by::[[vex-v5-booster-kit]]  
extended_by::[[aesthetic-vocabulary]]  
references::[[vex-v5-cad-designs]]
expanded_by::[[vex-flywheel-disc-launcher]]
expanded_by::[[clawbot-scoop-replacement]]
constrained_by::[[game-object-selection]]
