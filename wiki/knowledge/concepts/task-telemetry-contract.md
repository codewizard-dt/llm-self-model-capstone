---
id: task-telemetry-contract
title: Task Telemetry Contract
aliases: [Task Contract, Telemetry Contract, Grab/Pull/Throw Contract]
updated: 2026-06-16
sources:
  - ../../raw/research/vex-v5-customization-grab-pull-throw/index.md
tags: [concept, quantification, telemetry, gap-model, task, vex-v5]
---

# Task Telemetry Contract

The data structure that bridges the [[llm-authored-self-model]]'s capability predictions and the [[reality-gap]] residuals measured from actual robot execution. **Each task primitive (grab, pull, throw, …) has a contract with three blocks: `predicted` (what the self-model expected), `observed` (what telemetry recorded), and `gap` (the signed residual the next generation's self-model must explain).** The gap block is the ground-truth input to the design learning loop.

## Why This Structure

The capability self-model layer makes quantitative claims: "I can grip with 14.7 N" or "I can throw 0.4 m." Without a machine-readable residual, the LLM Critic panel can only argue in prose — it cannot numerically update the self-model. The contract gives every claim a testable, numeric post-condition that maps back to a physical parameter (moment arm, gear ratio, mass estimate, friction coefficient). When observed ≠ predicted, the LLM Generator can revise exactly the parameter that caused the discrepancy.

## Grab Contract (VEX V5 Clawbot)

```json
{
  "task": "grab",
  "predicted": {
    "object_width_mm": 40,
    "grip_force_N": 14.7,
    "success": true
  },
  "observed": {
    "claw_position_delta_deg": 120,
    "claw_current_A": 1.8,
    "claw_torque_Nm": 0.9,
    "gripped": true
  },
  "gap": { "force_error_N": -0.9, "width_error_mm": 5 }
}
```

**Telemetry sources:** `claw_motor.torque()`, `claw_motor.current()`, `claw_motor.position()`, `claw_motor.velocity()`

**Grip binary signal:** `velocity < 5 RPM AND current > 1.5 A` → object gripped — *this requires custom polling code; VEXcode V5 has no built-in `is_stalled()` API. Recommended capstone pattern: `set_max_torque(30, PERCENT)` + `spin_for(720, DEGREES)` + `set_timeout(3, SECONDS)` — motor soft-stops on contact, then read `position()`. See [[vex-v5-clawbot-claw-autonomy]].*

## Pull Contract (VEX V5 Clawbot)

```json
{
  "task": "pull",
  "predicted": { "load_mass_kg": 2.0, "distance_m": 0.5, "success": true },
  "observed": {
    "pull_force_N": 22.4,
    "velocity_ratio": 0.77,
    "distance_m": 0.5,
    "energy_J": 11.2
  },
  "gap": { "force_error_N": 6.6, "efficiency_loss": 0.23 }
}
```

**Telemetry sources:** `(left.torque() + right.torque()) / wheel_radius`, `actual_velocity / set_velocity`, `drivetrain.position()`

## Throw Contract (VEX V5 Clawbot arm)

```json
{
  "task": "throw",
  "predicted": { "range_m": 0.4, "object_mass_g": 50 },
  "observed": {
    "release_velocity_ms": 0.38,
    "observed_range_m": 0.25,
    "arm_velocity_at_release_RPM": 27.1
  },
  "gap": { "range_error_m": -0.15, "velocity_loss_ratio": 0.16 }
}
```

**Telemetry sources:** `arm_motor.velocity()` at release → computed `v₀ = ω × arm_length` → `R = v₀² sin(2θ) / g`. Observed range: AI Vision Sensor or Distance Sensor.

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

platform_filter::[[picobricks-rex-vs-vex-v5]]
grounds::[[llm-authored-self-model]]
mitigates::[[reality-gap]]
derived_from::[[vex-v5-customization-grab-pull-throw]]
extended_by::[[vex-v5-booster-kit]]
physical_substrate::[[vex-v5]]
interpreted_via::[[pid-control]]
transported_by::[[vex-v5-telemetry-pipeline]]
