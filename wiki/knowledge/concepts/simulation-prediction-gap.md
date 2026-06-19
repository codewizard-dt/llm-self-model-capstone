---
id: simulation-prediction-gap
title: Simulation & Prediction — What's Spec'd vs. What's Missing
updated: 2026-06-19
tags: [concept, simulation, prediction, self-model, gap-model, architecture]
---

# Simulation & Prediction — What's Spec'd vs. What's Missing

Assessment of how fully specified the prediction and simulation layers are in the capstone architecture. Short answer: the **prediction schema is solid**; the **simulation step is a named placeholder with no implementation**.

## What Is Well-Specified

The `predicted` block of the relates_to::[[task-telemetry-contract]] is the concrete prediction layer, fully spec'd at the schema level with derivation formulas:

| Task | Predicted fields | Derivation |
|---|---|---|
| Grab | `object_width_mm`, `grip_force_N`, `success` | Motor torque spec × moment arm |
| Pull | `load_mass_kg`, `distance_m` | Drive torque / wheel radius |
| Throw | `range_m`, `object_mass_g` | `v₀ = ω × arm_length → R = v₀² sin(2θ) / g` |
| Visual (Pi) | `object_bbox`, `pose {x, y, heading}` | Camera FOV × mount geometry |

The **PID gap interpretation table** maps each residual type to the specific physical parameter the self-model should revise on the next generation:

| Gap residual | Physical interpretation | Self-model revision |
|---|---|---|
| Position deficit | Friction / load higher than modeled | Revise friction estimate |
| Torque at saturation | Load exceeded torque budget | Revise load mass, gear ratio, or arm length |
| Velocity overshoot | Inertia lower than modeled | Revise structural mass estimate downward |
| Large I accumulation | Significant static friction floor | Add static friction term to capability model |

This makes the feedback side of prediction well-reasoned: every gap entry has a named physical cause and a named corrective action.

## What Is a Named Placeholder

The relates_to::[[llm-authored-self-model]] loop diagram lists:

```
Simulation → scores the predicted behavior
```

That step has **no physics engine, no URDF/SDF pipeline, no tool choice, and no implementation notes**. The same page's Grounding Requirement section lists "simulation validation against URDF/SDF geometry" as one of three required grounding sources — but the wiki has no page, task, or decision on which simulator, how models get built, or what "scores the predicted behavior" means in practice.

The relates_to::[[reality-gap]] page reinforces the need for a "layered simulation stack" (geometry/kinematics → brick-specific mechanics → hardware-in-the-loop) but again names no tool and specifies no pipeline.

The multi-LLM critic panel (`critiqued_by::[[multi-llm-adversarial-critique]]`) is referenced in the self-model page but has no wiki page of its own.

## Layer-by-Layer Status

| Layer | Status |
|---|---|
| Predicted values — what to predict, from what formula | Spec'd in contract schemas |
| Gap residuals — how to measure prediction error | Spec'd with PID interpretation table |
| Self-model revision — what to change when gap is non-zero | Described conceptually; no prompt templates |
| Simulation — forward-validate predicted behavior pre-build | **Named but unspecified — main open hole** |
| Multi-LLM critic panel — attacks self-model pre-build | Referenced; no dedicated page or prompt design |

## Demo Viability Without Simulation

The capstone can ship the Jun 29 demo without the simulation step. The telemetry contract loop (predict → execute → observe → gap → revise) runs entirely on real hardware — simulation is the "before fabrication" validity check. Skipping it means the robot builds and fails faster, which is still a valid and demonstrable loop. Simulation becomes more important in later generations when the goal is to reduce wasted physical build cycles.

## Open Decisions

1. **Which simulator?** Candidates never evaluated in the wiki: PyBullet (Python-native, URDF), MuJoCo (precision contact physics, free since 2022), Gazebo (ROS-native), or a pure kinematic model in NumPy (no physics, but enough to validate reach/range predictions from the throw contract formula).
2. **How are URDF models generated?** The typed-assembly grammar grounding requires that each self-model variant map to a simulatable geometry — this pipeline (Onshape STEP → URDF) is undesigned.
3. **Multi-LLM critic prompt templates** — what system prompt does a Critic receive? What schema does it return findings in? Unspecified.

relates_to::[[llm-authored-self-model]]
relates_to::[[task-telemetry-contract]]
relates_to::[[reality-gap]]
relates_to::[[typed-assembly-grammar]]
relates_to::[[physical-robot-software-factory]]
