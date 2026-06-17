---
id: typed-assembly-grammar
title: Typed Assembly Grammar
aliases: [Restricted Design Language, Typed Parts Grammar, Searchable Assembly Grammar]
updated: 2026-06-15
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

Valid combinations ≈ 15–30 (many slots are mechanically invalid). **This small, finite space is exactly what makes the grammar "typed" in the Lipson sense** — the LLM generator can enumerate and search it exhaustively. The capstone generation ladder maps naturally: [[speedbot]] = Gen 0 (simplest valid sentence), Clawbot = Gen 1 (full vocabulary), mutations = Gen 2–5 (search over the remaining valid sentences).

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

constrained_by::[[physical-robot-software-factory]]  
relates_to::[[reality-gap]]  
derived_from::[[feasibility-human-built-generational-factory]]  
exemplified_by::[[vex-v5-clawbot-build-instructions]]  
enumerated_by::[[vex-v5-starter-kit-configurations]]  
base_sentence::[[speedbot]]  
expanded_by::[[vex-v5-booster-kit]]  
extended_by::[[aesthetic-vocabulary]]
