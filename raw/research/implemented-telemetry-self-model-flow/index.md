---
topic: "Implemented telemetry, gap analyzer, self-model generator, critic, and robot IO flow"
slug: "implemented-telemetry-self-model-flow"
researched: 2026-06-28
sources: [./sources.md]
charts: [./charts.md]
---

# Research: Implemented Telemetry to Self-Model Flow

The implemented system already has a complete code-defined path from robot serial JSON through ROS demux/export, `ContractLine` evidence, gap summary generation, deterministic self-model revision, deterministic critic review, approved `TaskEnvelope` export, and robot command execution. The critic is not only a stub: `run_critic_panel` exists and runs physics, torque, and CoM geometry checks. The main implementation gap found is command vocabulary drift: the contracts package defines `claw`, while ROS/operator/V5 firmware implement `grab`, `lift`, and `release`.

## Research Questions

- What files actually define each payload shape in the telemetry-to-gap-to-generator path?
- Which implemented functions transform raw robot/ROS output into `ContractLine` evidence?
- Which implemented functions consume gap summaries and produce revised self-models?
- Does the critic exist, and what are its inputs and outputs?
- How does critic-approved output reach the robot, and what does the robot emit back?

## Current State (Codebase)

The core evidence payload is `ContractLine`, defined in `contracts/src/contracts/contract_line.py`, with `session_id`, `generation`, `round`, `task`, `motor_samples`, `predicted`, `gap`, and optional `outcome`, `vision`, and `source` [S1]. `SelfModel` is defined in `contracts/src/contracts/self_model.py` and carries config, structural, capability, predictive, gap model, and reasoning layers [S2]. `TaskEnvelope` is a task-file wrapper around `ContractLine` plus an operator outline [S4].

On the robot side, `robot/v5-brain/pros_bridge/src/main.cpp` reads newline-delimited command JSON, handles command cases, emits ack JSON, and emits telemetry JSON with motor samples [S15]. ROS demuxes those Brain lines into ack, telemetry, or status events with `BrainStreamDemux`, then publishes them from `VexBridgeNode` [S11][S12]. Telemetry is persisted as topic JSONL by `TelemetryWriterNode` [S9].

The bridge into offline evidence is implemented in two places: `evidence_export.py` converts proof/operator bundles into `ContractLine` payloads [S8], and `Operator.contract_result` creates ContractLine-shaped results from live operator actions [S14]. The gap analyzer reads `ContractLine` JSONL, validates each line as `ContractLine`, computes residual summaries and diagnoses, and returns a gap summary with a generator handoff [S5].

The offline loop is implemented in `loop_closure.py`: `generate_self_model_candidate` revises a `SelfModel` from gap residuals, `run_critic_panel` returns an approval report from three deterministic reviews, and `export_task_envelope` requires approval before producing a robot-facing `TaskEnvelope` [S7].

## Key Findings

- The raw robot output shape is implemented directly in V5 firmware, not just in Python contracts. `emit_ack` and `emit_telemetry` define the actual newline JSON emitted by the Brain [S15].
- `ContractLine` is the central evidence boundary for the offline loop. ROS exports and operator results both converge into this shape before the gap analyzer reads them [S1][S8][S14].
- The gap analyzer output shape is a plain dict with `schema_version`, `kind`, `source`, `residuals`, `diagnoses`, and `generator_handoff`; it is not currently a Pydantic contract [S5].
- The self-model generator and critic are deterministic Python functions today. They are implemented enough to revise predictive/gap fields and approve or reject a candidate through physics, torque, and geometry checks [S7].
- Critic-approved output reaches the robot as a `TaskEnvelope` JSON file consumed by `OperatorNode._consume_task_file`, then as normalized `/vex/cmd` packets sent over serial [S4][S10][S11][S13][S14].
- There is vocabulary drift between contracts and runtime: `contracts/control_command.py` defines `claw`, but `bridge_protocol.py`, operator packet generation, and V5 firmware implement `grab`, `lift`, and `release` [S3][S10][S14][S15].

## Chart Pack

See [charts.md](./charts.md). It contains seven Mermaid charts, each with nine nodes or fewer:

- V5 serial output classification
- ROS evidence to `ContractLine` JSONL
- `ContractLine` JSONL to gap summary
- Gap summary to `SelfModel` candidate
- `SelfModel` candidate to critic report
- Critic approval to robot task file
- Robot command execution back to evidence

Every chart node and named input/output has a table link to the file that defines or emits it.

## Constraints

- Any future implementation should preserve `ContractLine` as the evidence boundary unless the contracts package is intentionally changed [S1].
- Gap summary consumers should treat residual key names as stable because `generate_self_model_candidate` looks up residual keys directly, such as `force_error_N` and `duration_error_s` [S5][S7].
- Robot command work must resolve or explicitly document the `claw` versus `grab`/`lift`/`release` split before treating `ControlCommand` as the single source of truth [S3][S10][S14][S15].
- Task files must remain `TaskEnvelope`-valid for `OperatorNode._consume_task_file` to accept them [S4][S13].

## Recommendation

Use [charts.md](./charts.md) as the implementation-derived infrastructure map. For follow-up engineering, first reconcile the command vocabulary across `contracts/src/contracts/control_command.py`, `robot/ros2-runtime/src/vexy_ros/bridge_protocol.py`, `robot/ros2-runtime/src/vexy_ros/operator/_core.py`, and `robot/v5-brain/pros_bridge/src/main.cpp`. That is the main inconsistency exposed by tracing the actual imports, serializers, and firmware handlers.

## Next Steps

- File a task to reconcile control-command vocabulary across contracts, ROS bridge, operator primitives, and V5 firmware.
- Optionally add a typed Pydantic model for gap summaries if they are becoming a durable boundary rather than an internal dict.
- Use the `wiki-ingest` skill on this report when you want it synthesized into the knowledge base.
