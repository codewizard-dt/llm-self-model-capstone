---
id: vex-v5-clawbot-build-instructions
title: "VEX V5 Clawbot Build Instructions (276-6009-750 Rev6)"
aliases: [Clawbot Build Instructions, VEX Clawbot, V5 Clawbot]
updated: 2026-06-16
sources:
  - ../../raw/276-6009-750-Rev6.pdf
tags: [source, vex-v5, hardware, build-instructions, clawbot, typed-grammar, robotics]
---

# VEX V5 Clawbot Build Instructions (276-6009-750 Rev6)

A 41-step illustrated build guide (©2023 VEX Robotics) for the **V5 Clawbot** — the canonical starter robot bundled with the VEX V5 Classroom Starter Kit (276-7010). The Clawbot is the standard "Gen 0" reference morphology for the VEX V5 system: it ships as the first build students assemble, and its typed parts and port assignments are the ground truth for the Stage-2 vocabulary in the [[physical-robot-software-factory]] capstone. derives_from::[[vex-v5]] exemplifies::[[typed-assembly-grammar]] relates_to::[[physical-robot-software-factory]]

## Robot Configuration

**Drivetrain**: 4-wheel, tank-drive. Rear pair: 2× 4" standard wheels (276-6299-000), each direct-coupled to a V5 Smart Motor 11W (276-4840). Front pair: 2× 4" Omni-Directional wheels (276-6298-000), passive — low-friction front casters that allow tank turning without scrubbing. 2 motors consumed.

**Lift arm**: Single-motor arm with a **84T High-Strength gear (276-3438-331) driven by a 12T Metal Pinion (276-2250-008)**, giving a **7:1 gear reduction**. The arm pivots on a 7x pitch shaft running through two vertical C-channels that are hacksaw-cut to length. 1 motor consumed.

**Claw**: Motorized two-finger gripper using injection-molded plastic claw parts (black + red) with a **12T Gear (276-6010-011)**, driven by 1× V5 Smart Motor 11W. Two #32 rubber bands provide passive return force. 1 motor consumed.

**Total: 4× V5 Smart Motor 11W.** All four are the same part (276-4840-000 / 276-4840-001).

## Electronics & Wiring

| Component | Part # | Qty |
|-----------|--------|-----|
| V5 Robot Brain | 276-4810 | 1 |
| V5 Robot Battery Li-Ion 1100mAh | 276-4811 | 1 |
| V5 Robot Radio | 276-4831 | 1 |
| 180mm V5 Power Cable (battery→Brain) | 276-4817-100 | 1 |
| 300mm V5 Smart Cable (drive motors) | 276-4861-020 | 3 |
| 600mm V5 Smart Cable (claw motor) | 276-4860-030 | 1 |
| 900mm V5 Smart Cable (arm motor) | 276-4860-010 | 3 (1 used) |

**Port assignments** (inferred from cable routing in steps 22 + 41):
- Port 1: right drive motor (300mm cable)
- Port 6: left drive motor (300mm cable)
- Port 10: second right-side reference (300mm cable)
- Port 3 / Port 8: claw (600mm) and arm (900mm) — exact ports confirmed on first VEXcode program load

## Structure & Fasteners

All structural members are **steel**, not plastic — the "industrial not educational" characteristic that makes VEX V5 the Stage-2 platform:
- 2× C-Channel 1x2x1x15 (276-2232-028)
- 2× C-Channel 1x2x1x25 (276-2232-029)
- 3× U-Channel 2x2x2x20 (276-6009-001)
- 2× Angle 2x2x14x20 (276-6009-002)
- Fasteners: #8-32 star drive screws + hex nuts throughout

**Hacksaw cut required** (step 28): one U-channel must be cut to length; the instructions note "ask a parent/mentor for help." In a generation-manifest context this translates to `constraints.requires_cutting: true` — a field the self-model must encode to warn the human builder.

## Typed Parts Vocabulary (Stage-2 Catalog Seed)

Every part carries a VEX SKU, making this document the **real-world instantiation of the typed assembly grammar** for Stage 2. Key actuation and sensing nodes:

| Type | Part # | Count |
|------|--------|-------|
| `v5_smart_motor_11w` | 276-4840 | 4 |
| `v5_robot_brain` | 276-4810 | 1 |
| `v5_robot_battery` | 276-4811 | 1 |
| `wheel_4in_standard` | 276-6299-000 | 2 |
| `wheel_4in_omni` | 276-6298-000 | 2 |
| `gear_84t_high_strength` | 276-3438-331 | 1 |
| `gear_12t_metal_pinion` | 276-2250-008 | 1 |
| `gear_12t_bore` | 276-6010-011 | 1 |
| `c_channel_1x2x1x15` | 276-2232-028 | 2 |
| `c_channel_1x2x1x25` | 276-2232-029 | 2 |
| `u_channel_2x2x2x20` | 276-6009-001 | 3 |

## Relevance to the Capstone

**The Clawbot is the "Gen 0" self-model baseline**: the LLM self-model loop's first generation would describe itself from this morphology — "I am a 4-wheel tank-drive with a 7:1 geared arm and a geared claw. Predicted: I can lift objects under ~X kg to ~Y cm height." The typed parts list is the seed for `vex_v5_catalog.json`. The port assignments are the `electronics.hub_ports` block. The 7:1 gear ratio is a `capability_model` parameter (torque budget, reach). The hacksaw-cut constraint maps to a `build_warnings` field. This document is the ground truth for the entire Stage-2 generation manifest format.

used_by::[[physical-robot-software-factory]]
exemplifies::[[typed-assembly-grammar]]
relates_to::[[feasibility-human-built-generational-factory]]
