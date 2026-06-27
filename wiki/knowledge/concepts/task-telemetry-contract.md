---
id: task-telemetry-contract
title: Task Telemetry Contract
aliases: [Task Contract, Telemetry Contract, Score Contract]
updated: 2026-06-26
sources:
  - ../../raw/research/vex-v5-customization-grab-pull-throw/index.md
  - ../../raw/research/task-contract-score-redesign/index.md
  - ../sources/operator-layer-research.md
  - ../../raw/research/driver-telemetry-labeling/index.md
tags: [concept, quantification, telemetry, gap-model, task, vex-v5]
---

# Task Telemetry Contract

The data structure that bridges the [[llm-authored-self-model]]'s capability predictions and the [[reality-gap]] residuals measured from actual robot execution. **Each task has a contract with three blocks: `predicted` (what the self-model expected), `observed` (what telemetry recorded), and `gap` (the signed residual the next generation's self-model must explain).** The gap block is the ground-truth input to the design learning loop.

## Why This Structure

The capability self-model layer makes quantitative claims: "I can score from 1.5 m" or "I expect the ball to go in." Without a machine-readable residual, the LLM Critic panel can only argue in prose — it cannot numerically update the self-model. The contract gives every claim a testable, numeric post-condition that maps back to a physical parameter (moment arm, gear ratio, mass estimate, launch velocity). When observed ≠ predicted, the LLM Generator can revise exactly the parameter that caused the discrepancy.

## Score Contract (current — single task)

The robot has **one task**: get the ball into the bin. Fitness = **distance from the bin at the moment of scoring** — further is better. Gen-0 (claw) scores near 0 m; Gen-1+ (scoop / flywheel) earns positive fitness by launching from a distance. See [[task-contract-score-redesign]] for implementation details.

```json
{
  "task": "score",
  "predicted": {
    "distance_from_bin_m": 1.5,
    "success": true
  },
  "observed": {
    "ball_in_bin": true,
    "distance_from_bin_m": 1.3,
    "score_value": 1.3
  },
  "gap": {
    "distance_error_m": -0.2,
    "success_correct": true
  }
}
```

`score_value = distance_from_bin_m if ball_in_bin else 0.0`

**Telemetry sources:** drivetrain odometry for distance; AI Vision Sensor or AprilTag localization for `distance_from_bin_m`; binary `ball_in_bin` from camera detection or manual observation.

> **Historical note (pre-2026-06-23):** The original design used three sub-capability contracts — Grab (claw force/position), Pull (drivetrain load/distance), and Throw (arm velocity/range) — modelling each primitive independently. These are preserved in [[vex-v5-customization-grab-pull-throw]] and [[vex-v5-booster-kit]] as reference material. The redesign collapses them into the single outcome that matters for the evolutionary fitness loop.

## Extending to New Platforms

When the project migrates to a different platform (Stage 2: [[vex-v5]], Stage 3: ROBOTIS), the contract schema persists — only the telemetry sources change. A task contract is **platform-agnostic by design**: it measures physical outcomes (N, m, m/s), not motor port numbers. The LLM self-model accumulates gap history across generations regardless of platform.

## Relationship to the Self-Model

- **Structural self-model** → generates the morphology (arm length, gear ratio, claw geometry) used in predictions
- **Capability self-model** → derives predicted values from the catalog's physical specs
- **Predictive self-model** → forward-simulates the task to set `predicted` block
- **Gap model** → the `gap` block; residuals correct the capability and predictive layers next generation

This is Bongard & Lipson's continuous self-modeling loop, now language-grounded and task-contract-structured.

## New Contract Variants from Booster Kit (from [[vex-v5-booster-kit]])

The Booster Kit's new typed primitives generate new contract variants. Physical schemas are analogous to the Clawbot contracts above:

**Linear Pull** (rack-and-pinion with 19T rack gear):
- `predicted`: `extension_mm`, `load_mass_kg`, `success`
- `observed`: `rack_motor.torque()`, `rack_motor.position()` → mm of travel, `rack_motor.current()`
- `gap`: `extension_error_mm`, `force_error_N`

**Intake Grab** (roller-based):
- `predicted`: `object_width_mm`, `intake_velocity_RPM`, `captured`: true
- `observed`: `intake_motor.velocity()` drop (object stalls rollers), `intake_motor.current()` spike
- `gap`: `velocity_drop_ratio`, `capture_binary`

**Slip-Release Throw** (motor clutch pre-tension):
- `predicted`: `stored_energy_J`, `release_range_m`
- `observed`: `arm_motor.velocity()` before clutch slip, observed range (AI Vision / Distance)
- `gap`: `range_error_m`, `energy_loss_ratio`

These variants are platform-agnostic by the same schema; only telemetry sources change with the mechanism.

## Decisive Platform-Selection Criterion (from [[picobricks-rex-vs-vex-v5]])

> **This contract is the binding platform-selection filter.** A platform without per-actuator feedback cannot populate the `observed` block, so it produces no `gap`, and the self-model loop cannot close. On that basis the [[picobricks-rex-evolution]] (open-loop DC motors + standard RC servos with no feedback bus) was evaluated against VEX V5 and disqualified as a substrate, despite being far cheaper.

## Flywheel Artifact Mapping (2026-06-16)

Task Telemetry Contract JSON blocks map directly to [[flywheel]] artifacts. When a run completes, the contract JSON is uploaded as an artifact on the current self-model node (with `metadata.artifact_type: task-telemetry-contract`). A Flywheel hook watching `artifact.finalized` on this artifact type triggers the LLM revision agent, which creates the next child node. This closes the [[llm-authored-self-model]] feedback loop without a human step. artifact_in::[[flywheel]] tracked_by::[[research-graph-infrastructure]]

## Visual Observation Extension (from [[vision-vex-architecture]])

When a [[raspberry-pi-5]] coprocessor is added to the robot (running OpenCV + YOLO11n + AprilTag), the contract gains a fourth sensor domain — visual observations — alongside the existing motor telemetry fields. The Pi emits visual state that the Brain-side Python stub merges into the same JSON structure before logging:

```json
{
  "task": "grab",
  "predicted": {
    "torque_Nm": 1.2,
    "object_detected": true,
    "object_bbox": [120, 80, 200, 160],
    "pose": {"x": 500, "y": 0, "heading": 0}
  },
  "observed": {
    "torque_Nm": 1.4,
    "object_detected": true,
    "object_bbox": [118, 83, 198, 162],
    "pose": {"x": 487, "y": -12, "heading": 2}
  },
  "gap": {
    "torque_residual": 0.2,
    "detection_match": true,
    "bbox_iou": 0.96,
    "dx": -13, "dy": -12, "dtheta": 2
  }
}
```

**AprilTag localization**: printing tag36h11 family tags (100mm × 100mm) around the workspace lets the Pi compute the robot's pose (`{x, y, heading}`) from camera observations alone — no odometry calibration required. The LLM self-model predicts a pose after each action; the AprilTag observation is the ground-truth comparison. The `dx`, `dy`, `dtheta` residuals feed the next-generation self-model revision as spatial gap data, directly paralleling the Hart/Scassellati visual self-observation approach.

**Self-model capability layer additions**: `camera_fov_deg`, `camera_mount_height_mm`, `visual_range_mm [min, max]` — physical parameters the self-model must predict and that the visual `gap` block corrects.

extended_by::[[vision-vex-architecture]]

## PID Gap Interpretation (from [[pid-control]])

The gap block residuals are evidence about physics not captured in the self-model, specifically about the V5 motor's inner relates_to::[[pid-control]] loop failing to achieve the commanded target:

| Gap residual | Physical interpretation | Self-model revision |
|---|---|---|
| Position deficit (observed < predicted) | Friction or load higher than expected | Revise friction estimate or reduce predicted extension |
| Torque at saturation (≈2.1 Nm stall) | Load exceeded torque budget | Revise load mass, gear ratio, or arm length |
| Velocity overshoot (observed > predicted) | Inertia lower than modeled | Revise structural mass estimate downward |
| Large I accumulation before reaching target | Significant static friction floor | Add static friction term to capability model |

This table maps each gap entry to the physical parameter the LLM Generator should revise in the next generation's capability self-model.

## Transport Pipeline (from [[vex-v5-telemetry-pipeline]])

Once a contract JSON is assembled on the V5 Brain, it travels through a three-stage pipeline to reach the LLM:

| Stage | Mechanism | Details |
|---|---|---|
| **Output** | `sys.stdout.write(json + '\n')` on V5 Brain | USB serial user port, 115200 baud, ~11,500 B/s; contract (300–600 bytes) in ~35–55 ms |
| **Storage** | Append to `session_<ts>.jsonl` on Pi | JSONL per session; flush after each contract; faster than SQLite for insert-heavy workload |
| **LLM Transfer** | Mode A: `anthropic.messages.create()` per contract (1–4s, demo) | Mode B: `anthropic.messages.batches.create()` across sessions (50% cost, 24h SLA, training) |

**Fallback**: SD card on V5 Brain (`brain.sdcard.is_inserted()` + file I/O, FAT32 ≤32GB) for untethered runs without Pi connection.

**Stage 2 upgrade**: relates_to::[[pros]] `pros::Serial` opens a Smart Port as RS-485 at up to 921,600 baud — 8× USB speed, decoupled from the debug port.

## Live ContractLine Emission from the ROS Operator (2026-06-25)

`Operator.contract_result()` (`core.py:363–395`) in `vexy_ros.operator` emits a **ContractLine-compatible dict** after every operator method run. This dict includes motor samples, the vision block, gap, outcome, and source fields. The `run_index` field is incremented with each call, giving a monotonic ordering of runs within a session.

`OperatorNode` publishes each result to the `/operator/results` ROS topic as it is produced — **live, per method run** — not only at session close. This means the contract evidence stream is available in real time on the Pi during task execution, and can be recorded to MCAP or forwarded to the offline packet builder via `vexy_ros.evidence_export.contract_jsonl_from_bundle`.

emitted_by::[[vexy-ros-runtime]]
consumed_by::[[self-model-packet-builder]]

## Driver-Labeled Telemetry Windows (2026-06-26)

derived_from::[[driver-telemetry-while-using-the-controller]] extends the contract evidence path to supervised manual driving. Instead of waiting for every action to be autonomously dispatched, the Pi can record `/vex/telemetry` plus timestamped `/operator/annotation` labels while a human drives. Each label is joined to nearby telemetry and vision windows, creating observed evidence for states like contact, stall, spinout, or successful alignment. This does not replace the formal `predicted/observed/gap` contract; it supplies labeled observations that can later be summarized into contract-valid outcomes or used to train state detectors.

extended_by::[[driver-telemetry-annotation]]

platform_filter::[[picobricks-rex-vs-vex-v5]]
grounds::[[llm-authored-self-model]]
mitigates::[[reality-gap]]
derived_from::[[vex-v5-customization-grab-pull-throw]]
extended_by::[[vex-v5-booster-kit]]
physical_substrate::[[vex-v5]]
interpreted_via::[[pid-control]]
transported_by::[[vex-v5-telemetry-pipeline]]
