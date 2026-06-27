---
id: llm-authored-self-model
title: LLM-Authored Robot Self-Model
aliases: [Robot Self-Model, Self-Description, LLM Self-Modeling]
updated: 2026-06-25
sources:
  - ../../raw/chatgpt-ai-powered-software-factory.md
  - ../../raw/Feasibility of a Human-Built Generational Robot Software Factory.pdf
  - ../../raw/research/apriltags/index.md
tags: [concept, capstone-idea, novel, self-model, llm, robotics, primary-idea]
---

# LLM-Authored Robot Self-Model

**The core novel idea for this capstone**: given a finite, typed parts catalog, instruct an LLM to author and iteratively revise a *structured self-model* of the robot it is designing — a language-readable, human-explainable, multi-LLM-critiqueable description of what the robot *is* and what it *can do* — and update that self-model from real-world performance.

## The Lineage (and the Gap)

Hod Lipson's lab established the *numerical* self-modeling baseline:
- **Bongard, Zykov & Lipson (2006)** — "Resilient Machines Through Continuous Self-Modeling," *Science* 314(5802): 1118–1121. DOI: 10.1126/science.1133687. A 4-legged robot with no prior knowledge of its body actuates itself, infers candidate self-models, drives behavior from the best model, re-models when a leg is removed. Continuous, numerical, not language.
- **Kwiatkowski & Lipson (2019)** — "Task-Agnostic Self-Modeling Machines," *Science Robotics* 4(26): eaau9354. DOI: 10.1126/scirobotics.aau9354. A robot arm builds a self-model from random motion (~1,000 trajectories) using deep learning; uses it to complete tasks and detect damage. Still numerical.

The closest published prior work on **language-grounded** self-modeling (predating LLMs):
- **Justin Hart & Brian Scassellati (2017)** — *"Robot Self-Modeling"* (IEEE-RAS) — a robot builds a symbolic self-model from observation; language-grounded but pre-LLM, no adversarial critique, no typed-parts vocabulary. Hart is now at UT Austin (hart@cs.utexas.edu) applying LLMs to service robots. relates_to::[[justin-hart]]
- **Hart & Scassellati (2011)** — *"A Robotic Model of the Ecological Self"* (IEEE-RAS Humanoid Robots) — self as ecologically situated agent; phenomenological framing.

The closest 2024–2026 LLM work:
- **RoboMorph** (arXiv 2407.08626, Qiu et al., 2024/2026) — LLM generates robot designs within a *structured grammar*; evolutionary selection. Closest to this idea on the design-generation side, but generates designs (not self-models), simulation-only, no critique loop.
- **SAS-Prompt** (arXiv 2504.20459 / ICRA 2025, Ben Amor et al.) — LLM observes past robot behavior → numerically optimizes control parameters in-prompt. Closest on the "LLM iterates on the robot" side, but controller-only, no morphology, no self-model.

**The gap**: no published paper makes the self-model *language-authored, language-grounded, and LLM-critiqued*.

## What the Self-Model Is

Given a finite, typed parts vocabulary (the [[typed-assembly-grammar]] grounding), the self-model is a layered structured document the LLM authors:

1. **Structural self-model** — a typed graph: parts as nodes, connections as typed port-edges. Example: `"drive_module×2 → chassis_rail → sensor_mast(low) → passive_plow"`. Enumerable *because* the parts set is finite; bounded by the vocabulary.

2. **Capability self-model** — what that structure can do, derived from the catalog's physical specs: reach, torque budget, max step height, sensing field, center-of-mass, stable support polygon.

3. **Predictive self-model** — given this body + a candidate controller, what motion results toward the goal (e.g., stair climbing). Grounded against simulation.

4. **Gap model** — after physical execution, what the self-model *predicted* vs. what telemetry *observed*. This residual feeds the next design revision — Bongard's continuous-self-modeling loop, now in language.

## The Full Loop

```
Generator LLM  →  authors self-model from finite parts + physical specs
                         (structural + capability + predicted behavior)
Critic LLM panel →  attacks the self-model before any physical build:
                         "your CoM is too high for a 20cm step edge"
                         "torque budget insufficient for the drive load"
                         "sensor mast occludes front camera"
Simulation      →  scores the predicted behavior
Physical build  →  human assembles; robot attempts the goal (e.g. stairs)
Telemetry       →  observed failure updates the self-model
                         (corrects structural / capability / predictive layers)
→ repeat, with a better-calibrated self-model next generation
```

The self-model becomes the **single shared artifact** the generator authors, critics attack, simulation validates, and reality calibrates.

## Why This Is Novel

Lipson's robots built self-models *numerically* from motor-babbling — no language, no human-readable representation, no adversarial critique. RoboMorph generates designs but has no self-understanding; it proposes structures but cannot explain *why* a design will fail. This idea makes the self-model:
- **Language-grounded**: readable, revisable, and explainable without retraining anything
- **Authored**: the LLM writes it from a catalog (grounded in real specs), not learned from scratch
- **Critiqued**: the multi-LLM panel ([[multi-llm-adversarial-critique]]) attacks it pre-build, replacing expensive failed physical trials

## Novelty Claim

> "An LLM authors and iteratively revises a structured, language-readable self-model of a modular physical robot over a finite typed parts vocabulary. A multi-LLM critic panel attacks the self-model before fabrication. Real-world telemetry corrects the model each generation. This replaces Lipson's numerical self-modeling with a language-explainable, human-auditable representation that compounds across generations."

## The Killer Demo

Show the **self-model evolving in plain language**, not just the body:
- Gen 1 self-model: *"I traverse flat ground. Predicted: 2m/min."* → runs → *falls at first step* → self-model update: *"CoM at 18cm; insufficient grip geometry for step edges ≥12cm"*
- Gen 5 self-model: *"Added lift linkage. CoM lowered to 11cm. Predicted: clear 18cm step."* → runs → success
- Audience watches the robot's *self-knowledge* improve in readable prose. That is the "holy shit" moment.

## Grounding Requirement

A self-model is only worth anything if it's **grounded** — otherwise it's just the LLM imagining a body. Grounding comes from three places:
1. The finite parts catalog with real physical specs ([[typed-assembly-grammar]])
2. Simulation validation against URDF/SDF geometry
3. The [[reality-gap]] residual that corrects the model against real telemetry

Without these three, the self-model floats free of physics.

## Alignment with Gauntlet Directions

- **Direction A** (ML + LLM): the forward/residual model + evolutionary search (ML) + the self-model authoring/critique (LLM)
- **Direction B** (philosophically different agents): an agent that *models itself* and explains its own failure modes
- Ambition > polish: the killer demo is clear, the research question is real, the build is staged and feasible

## Quantification via Task Telemetry Contracts (2026-06-16)

The capability self-model layer's predictions are made testable by [[task-telemetry-contract]] — per-task JSON blocks with `predicted`, `observed`, and `gap` fields derived from motor telemetry (`torque()`, `current()`, `velocity()`, `position()`). This is the machine-readable form of the gap model: every claim the self-model makes about force, speed, or range becomes a numeric residual after physical execution. The LLM Generator reads these residuals to revise exactly the parameter (moment arm, gear ratio, mass estimate) that caused the discrepancy. On the [[vex-v5]] platform this is: grab contract (claw torque/current), pull contract (drive torque / wheel radius), throw contract (arm angular velocity × arm length → range prediction). grounds::[[task-telemetry-contract]]

## Dobby Architecture → Capstone Implementation Pattern (2026-06-16)

relates_to::[[justin-hart]]'s 2024 Dobby paper (arXiv:2310.06303) provides the concrete LLM-robot interface architecture for this concept. The mapping:

| Dobby Component | Capstone Analog |
|----------------|-----------------|
| GPT-4 agent (function calling) | LLM Generator (authors/revises self-model) |
| History buffer | Self-model document (structural + capability + predictive layers) |
| Action Classes (title + pre/post-conditions + function) | Typed assembly grammar primitives with physical specs |
| Cosine-similarity embedding matcher | Self-model revision validator |
| Environmental state updates | Task telemetry contract residuals (gap JSON) |
| Greedy plan validator | Multi-LLM Critic panel |
| Non-blocking execution | Physical build (human executes while LLM analyzes) |

**The single addition** the capstone makes: promote the history buffer to a *structured self-model document* — the persistent shared artifact the LLM both reads and revises. Dobby has no self-model; it reasons about the world but not about the robot's own body/capabilities. That gap is unclaimed. derived_from::[[justin-hart-self-modeling]]

## Confirmed Field Gap (2026-06-16)

Two parallel tracks exist in 2024-2026 that have not merged:
1. **Numerical self-models** (Lipson→Kwiatkowski 2019 → 3D Gaussian Splatting 2025): data-driven geometric self-models, no language
2. **LLM+Robotics** (Dobby 2024, RoboMorph 2024, SAS-Prompt ICRA 2025): LLMs for conversation/design/control, no self-model

**No published paper combines**: LLM authoring + language-readable self-model + multi-agent critique + reality correction via telemetry residuals. The capstone's novelty claim is confirmed unoccupied.

## Flywheel Integration (2026-06-16)

[[flywheel]] (Paradigma) provides the durable DAG substrate for tracking self-model evolution. Each revision cycle maps 1:1 to Flywheel's "Encoding the Scientific Method" pattern: hypothesis = self-model node content; experiment = task run (execution); observation = [[task-telemetry-contract]] JSON (artifact); revision = child node. Multi-LLM critics become parallel branches from the same parent. The generational lineage (Gen 0 → Gen N) is the graph ancestry. Hooks on `artifact.finalized` can trigger autonomous LLM revision without a human step. infrastructure::[[flywheel]] tracked_by::[[research-graph-infrastructure]]

## Vision Capability Layer (from [[vision-vex-architecture]])

When a [[raspberry-pi-5]] coprocessor is added (OpenCV + YOLO11n + AprilTags), the self-model gains a **visual capability sub-layer** alongside the motor/mechanical layers. The LLM must now author and predict:

- `camera_fov_deg` — field of view; determines what the robot can see from a given pose
- `camera_mount_height_mm` — height above ground; governs detection range and angles
- `visual_range_mm [min, max]` — for a given object size, the pixel area that YOLO reliably detects
- `detectable_objects` — list of object types (by YOLO class) the robot can perceive

This directly realizes the Hart/Scassellati **visual self-observation** lineage within the language-grounded framing: the robot predicts a visual outcome ("after the arm extends, the object will be in the lower-left quadrant"), observes the actual detection, and uses the bounding-box IoU residual to correct the self-model's spatial predictions. The [[task-telemetry-contract]] visual extension (`predicted.object_bbox`, `observed.object_bbox`, `gap.bbox_iou`, `gap.pose`) is the machine-readable form of this loop.

**AprilTag localization enriches gap analysis**: instead of only encoder-count residuals, the self-model now receives spatial pose residuals (`dx`, `dy`, `dtheta`) from AprilTag observations — a much richer correction signal that lets the LLM Generator update the self-model's kinematic geometry directly.

extended_by::[[vision-vex-architecture]]

## F8 Self-Model Packet Builder — Concrete Preparation Artifact (2026-06-25)

The `self_model_generator` package (`self-model-generator`, `self_model_generator/src/self_model_generator/`) is the **concrete artifact that prepares evidence for the F8 Generator**. It implements `build_self_model_packet`, which assembles a structured Markdown document covering the current SelfModel, parts catalog verdict, contract evidence, gap summary, and generator guardrails. This is the machine-readable package the Generator LLM reads to produce a revised self-model.

The architecture follows a **Generator/Critic pattern** (defined in `self_model_generator/docs/llm_critic_architecture.md`):
- **Generator** (F8): reads the assembled packet and authors a revised SelfModel
- **Three stateless Critics** (F9): physics, torque, and CoM/geometry — each attacks the Generator's output independently before it is accepted

The packet builder is complete and tested. The **only remaining blocker** before the Generator can be implemented is **F10 (gap analyzer)**: until F10 lands, gap summary sections in packets are either `BLOCKED_F10_GAP` (no input) or `FIXTURE_BACKED_GAP` (fixture-supplied). The packet builder's `validate_fixture_packets` integration test verifies these invariants hold.

implemented_by::[[self-model-packet-builder]]
relates_to::[[operator-layer-research]]

derives_from::[[agent-evolution-factory]]  
grounded_by::[[typed-assembly-grammar]]  
mitigates::[[reality-gap]]  
critiqued_by::[[multi-llm-adversarial-critique]]  
physical_substrate::[[physical-robot-software-factory]]  
quantified_by::[[task-telemetry-contract]]
