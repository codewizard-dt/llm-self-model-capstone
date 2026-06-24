---
id: vex-v5-starter-kit-configurations
title: "Research: VEX V5 Classroom Starter Kit — Configuration Space"
aliases: [VEX V5 Starter Kit Configurations, Starter Kit Design Space]
updated: 2026-06-17
sources_secondary:
  - ../../raw/research/vex-v5-booster-kit/index.md
sources:
  - ../../raw/research/vex-v5-starter-kit-configurations/index.md
  - ../../raw/research/vex-v5-starter-kit-configurations/sources.md
  - ../../raw/research/vex-v5-starter-kit-configurations/index-2.md
  - ../../raw/research/vex-v5-starter-kit-configurations/sources-2.md
tags: [research, vex-v5, configuration, design-space, typed-grammar, clawbot, speedbot]
---

# Research: VEX V5 Classroom Starter Kit — Configuration Space

A 2026-06-16 research report enumerating the full configuration space of the [[vex-v5]] Classroom Starter Kit (276-7010). **The kit officially produces two base topologies — the [[speedbot]] (drivetrain only) and the [[vex-v5-clawbot-build-instructions|Clawbot]] (Speedbot + arm + claw) — and VEX's own STEM Labs PDF states "The VEX V5 Clawbot is an extension of the VEX Speedbot."** These are the same parts at different stages of assembly, not fundamentally different robots. The enumerable design space (~15–30 valid configurations from 6 free parameters) is ideal for the capstone LLM self-model loop: the generator can exhaust it in 3–5 generations. evaluates::[[vex-v5]] grounds::[[typed-assembly-grammar]]

## Official Builds for the Classroom Starter Kit

Exactly **three named configurations** are documented by VEX for the Classroom Starter Kit:

| Build | Motors | Official source | Compatible with Starter Kit? |
|-------|--------|-----------------|------------------------------|
| **Speedbot** | 2 (drive only) | STEM Labs activities | ✓ |
| **TrainingBot** | 2 (drive only) | VEX build download page | ✓ |
| **Clawbot** | 4 (2 drive + 1 arm + 1 claw) | Included build instructions | ✓ |
| Advanced TrainingBot | 4 (2 drive + 1 arm + 1 claw, faster) | VEX build download page | ✗ (Competition Kit only) |

Speedbot and TrainingBot are functionally equivalent; both are 2-motor tank drivetrains. The Clawbot extends the Speedbot by adding the arm uprights (U-channels), the 84T:12T arm gear train, and the plastic claw assembly.

## Structural Constraint — The Steel Is Exactly Consumed

The Starter Kit's steel inventory (2× C-Channel 15-hole, 2× C-Channel 25-hole, 3× U-Channel 20-hole, 2× Angle 14×20) is **entirely used by the Clawbot build**. After disassembly, the same pieces can be rearranged but there is no structural surplus for a fundamentally different multi-section design. VEX explicitly notes: "custom-designed robots may require the structural parts to be cut and/or bent into custom pieces."

## The Enumerated Design Space

Six free parameters define all valid configurations:

> **Contradiction:** The vocabulary below (from the 2026-06-16 research) contains three fields that include options requiring additional purchases. A 2026-06-17 audit (`index-2.md`) corrected these. See the **Corrected Vocabulary** section below for the authoritative starter-kit-only spec. The stale entries are: `cartridge: ["100rpm", "600rpm"]` (cartridges sold separately), `wheel_config: ["all_standard", "all_omni"]` (kit has only 2 of each type), `end_effector: ["roller_intake"]` (Intake Roller 276-1499 is a Booster Kit part).

```json
{
  "vocabulary": {
    "motor_allocation": ["2drive+2free", "2drive+1arm+1claw", "4drive+0manip", "3drive+1manip"],
    "arm_position":     ["front", "rear", "side", "absent"],
    "end_effector":     ["claw_grasper", "bare_arm", "roller_intake", "none"],
    "wheel_config":     ["front_omni+rear_standard", "all_standard", "all_omni"],
    "arm_gear_ratio":   ["7:1", "1:1"],
    "cartridge":        ["100rpm", "200rpm", "600rpm"]
  },
  "valid_configurations": "~15–30 (many combinatorial slots are mechanically invalid)"
}
```

### Corrected Vocabulary (Starter Kit 276-7010 Only) — 2026-06-17

Three corrections from the 2026-06-17 audit (`index-2.md`):

| Field | Removed | Reason |
|---|---|---|
| `cartridge` | "100rpm", "600rpm" | 36:1 and 6:1 cartridges are sold separately; motors ship with 18:1 (200 RPM) only |
| `wheel_config` | "all_standard", "all_omni" | Kit has 2 omni + 2 standard wheels; 4 of one type is impossible |
| `end_effector` | "roller_intake" | Intake Roller 276-1499 is a Booster Kit (276-2232) part, not in starter kit |

```json
{
  "platform": "vex_v5_classroom_starter_kit_276-7010",
  "vocabulary": {
    "motor_allocation": ["2drive+2free", "2drive+1arm+1claw", "4drive", "3drive+1manip"],
    "arm_position":     ["front", "rear", "side", "absent"],
    "end_effector":     ["claw_grasper", "bare_arm", "none"],
    "wheel_config":     ["front_omni+rear_standard"],
    "arm_gear_ratio":   ["7:1", "1:1"],
    "cartridge":        ["200rpm"]
  },
  "constraints": {
    "max_motors": 4,
    "wheels": {"omni_4in": 2, "standard_4in": 2},
    "cartridge_installed": "18:1_200rpm",
    "sensors_included": ["bumper_switch_x2"]
  }
}
```

**Combinatorial impact:** raw slots drop from 1,152 to 96; after validity filtering, **~10–15 meaningful configurations** (not the ~15–30 previously stated).

> **Superseded for the project's frozen vocabulary (2026-06-24).** The project's *frozen* vocabulary in `contracts/src/contracts/vocabulary.py` diverged from this 2026-06-17 corrected research block — PR #13 trimmed `arm_position` to `{front, rear}`, swapped `end_effector` to `{claw_grasper, scoop, flywheel}`, and re-expanded `cartridge` to all three V5 cartridges `{100rpm, 200rpm, 600rpm}`; F3 then dropped `4drive` from `motor_allocation` (every config now requires a powered manipulator). Under F3's valid-config rules the buildable design space is **exactly 60 configs** (claw 12 + scoop 36 + flywheel 12), not ~10–15 — the older estimate predated the flywheel/scoop/3-cartridge vocabulary. This research summary is preserved as faithful lineage of `raw/research/vex-v5-starter-kit-configurations/index-2.md`; the authoritative live spec lives in [`MASTER_REQUIREMENTS.md`](../../../MASTER_REQUIREMENTS.md) and [`contracts/parts_catalog.json`](../../../contracts/parts_catalog.json), and the cross-links to [[typed-assembly-grammar]] carry the same callout.

What the kit **cannot** produce without add-ons: tank treads, pneumatics, 4-bar linkage arm, scissor lift, flywheel shooter, vision-based autonomy, holonomic X-drive, aluminum structure.

## Claw-Grasper-Locked Configuration Space

For this capstone the `claw_grasper` end-effector is **required** (grab/pull/throw tasks demand it). Locking that parameter cascades:

- **Motor allocation locked**: a claw needs both an arm-lift motor AND a claw motor (2 manipulation motors). This eliminates `4drive+0manip`, `3drive+1manip`, and `2drive+2free`. Only `2drive+1arm+1claw` survives.
- **Drivetrain topology locked**: H-drive needs 3 drive motors (would need 5 total with claw); 4-motor tank leaves nothing for manipulation. Only `tank_2` survives.
- **Arm cannot be absent**: a claw requires an arm → `arm_position = absent` is eliminated.

Remaining free variables with claw locked (Starter Kit only, 4 motors):

| Parameter | Remaining options | Count |
|-----------|-------------------|-------|
| Wheel config | front_omni+rear_standard only *(corrected 2026-06-17: "all_standard" and "all_omni" removed — kit has 2 omni + 2 standard, not 4 of either)* | **1** |
| Arm position | front / rear / side | **3** |
| Arm gear ratio | 7:1 / 1:1 | **2** |
| Motor cartridge | 200rpm only (one cartridge included in kit) | **1** |
| End effector | locked: claw_grasper | **1** |
| Motor allocation | locked: 2drive+1arm+1claw | **1** |

**1 × 3 × 2 = 6 combinatorial slots → ~4–6 meaningful configurations** with claw locked on the Starter Kit alone. *(Prior count of 18 was inflated by the now-corrected wheel_config field.)*

> **Chassis note:** even within these 18 slots, chassis shape is essentially fixed — the steel is exactly consumed by the Clawbot frame. "Arm position" variants (front/rear/side) represent where the arm uprights bolt onto the same chassis, not a different chassis form.

## With VEX Booster Kit (276-2232) — Configuration Count by Motor Budget

The relates_to::[[vex-v5-booster-kit]] adds ~600 passive parts and introduces four new typed primitives (`linear_actuator`, `intake`, `long_arm`, `slip_release`). It does **not** add motors — actuation remains the binding constraint. The motor budget therefore drives the configuration expansion more than the parts catalog does.

### +0 Additional Motors — 4 Smart Motors Total (Realistic for Capstone)

With claw locked, motor allocation stays `2drive+1arm+1claw`. The Booster Kit expands the space structurally and morphologically but cannot unlock a second manipulator:

| Parameter | Starter Kit | With Booster Kit, +0 motors |
|-----------|------------|------------------------------|
| Arm type | 1 (rotating gear) | **2** (rotating gear \| linear_actuator via rack-and-pinion) |
| Arm position | 3 | 3 |
| Arm gear ratio | 2 | 2 (rack adds its own ratio; rotating keeps 7:1/1:1) |
| Wheel config | 3 | 3 |
| Chassis form | ~1 (steel exactly consumed) | **~3** (surplus steel → compact / extended / elevated-arm-mount) |
| Second manipulator | 0 (no motors left) | 0 (still no motors left) |

**2 × 3 × 2 × 3 × 3 = 108 combinatorial slots → ~30–50 meaningful configurations.** Roughly 2–3× the Starter Kit alone. The main gains are chassis form variety and the linear_actuator arm type — a genuinely different grab mechanism (push-pull vs. rotate-and-grip).

> ⚠️ Two Booster Kit items need compatibility verification: the Motor Clutch (276-1098) and Intake Roller (276-1499) were designed for the legacy 3-wire motor interface; V5 Smart Motor mounting should be confirmed on receipt before treating `slip_release` and `intake` as reliable primitives.

### +2 Additional Motors — 6 Smart Motors Total

Now `2drive + 1arm + 1claw + 2free` becomes possible, unlocking a **second manipulator simultaneously**:

| New dimension | Options |
|---------------|---------|
| Second manipulator | none \| intake_roller \| slip_release | **3** |

Rough estimate: **~90–150 meaningful configurations** (the second manipulator dimension multiplies the +0 count by ~3, with validity filtering).

### +4 Additional Motors — 8 Smart Motors Total

Enables `4drive + 1arm + 1claw + 1intake + 1aux` — full mecanum/4WD chassis with complete manipulator suite. Rough estimate: **~150–300 meaningful configurations**, but this is far beyond capstone budget and build complexity.

### Summary Table

| Motor budget | Extra cost | Approx. configs (claw locked) | Notes |
|-------------|------------|-------------------------------|-------|
| **+0 motors (4 total)** | **$0** | **~30–50** | **Realistic for capstone** |
| +2 motors (6 total) | ~$106 | ~90–150 | Unlocks dual-manipulator |
| +4 motors (8 total) | ~$212 | ~150–300 | Overkill for demo |

The +0 case is the right planning assumption: the Booster Kit alone (without extra motors) still roughly doubles or triples the meaningful configuration space over the motor-constrained Starter Kit.

## Implications for the Capstone Self-Model Loop

**Speedbot = Gen 0; Clawbot = Gen 1.** The natural generation ladder is:
1. Gen 0: Speedbot (2-motor drive, simplest valid grammar sentence, baseline telemetry)
2. Gen 1: Clawbot (add arm subsystem → new grab/throw capabilities; self-model adds arm node to structural graph)
3. Gen 2–5: Mutations (swap wheel types, change arm position, adjust gear ratio) → [[task-telemetry-contract]] records gap → self-model revises

The small design space is an **asset, not a limitation**: the LLM generator exhausts the meaningful configurations in 3–5 generations, building a complete self-model calibrated against real telemetry across the full vocabulary.

relates_to::[[task-telemetry-contract]]
relates_to::[[llm-authored-self-model]]
derived_from::[[vex-v5-clawbot-build-instructions]]
grounds::[[typed-assembly-grammar]]
