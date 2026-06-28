---
topic: "Implemented telemetry, gap analyzer, self-model generator, critic, and robot IO flow"
slug: "implemented-telemetry-self-model-flow"
researched: 2026-06-28
---

# Primary Sources - Implemented Telemetry to Self-Model Flow

| ID | Type | Locator | Accessed | What it contributed |
|---|---|---|---|---|
| S1 | codebase | `contracts/src/contracts/contract_line.py::ContractLine` | 2026-06-28 | Defines the contract evidence line consumed by the gap analyzer: session, generation, round, task, motor samples, predicted, gap, optional outcome/vision/source. |
| S2 | codebase | `contracts/src/contracts/self_model.py::SelfModel` | 2026-06-28 | Defines the self-model payload revised by the generator and reviewed by the critic. |
| S3 | codebase | `contracts/src/contracts/control_command.py::ControlEnvelope`, command classes, `AckLine` | 2026-06-28 | Defines the typed command envelope/variants and Brain ack shape. |
| S4 | codebase | `contracts/src/contracts/task_envelope.py::TaskEnvelope` | 2026-06-28 | Defines task file shape: `contract: ContractLine` plus `outline: TaskOutline`. |
| S5 | codebase | `self_model_generator/src/self_model_generator/gap_analyzer.py` | 2026-06-28 | Defines JSONL ingestion, residual summarization, diagnoses, generator handoff, and gap summary writing. |
| S6 | codebase | `self_model_generator/src/self_model_generator/packet_builder.py` | 2026-06-28 | Defines the implemented packet boundary that combines self-model, parts catalog, contract evidence, source refs, constraints, and gap summary. |
| S7 | codebase | `self_model_generator/src/self_model_generator/loop_closure.py` | 2026-06-28 | Defines generator candidate revision, deterministic critic panel, and TaskEnvelope export. |
| S8 | codebase | `robot/ros2-runtime/src/vexy_ros/evidence_export.py` | 2026-06-28 | Defines proof/operator evidence conversion into contract-valid payloads. |
| S9 | codebase | `robot/ros2-runtime/src/vexy_ros/telemetry_writer_node.py::TelemetryWriterNode` | 2026-06-28 | Defines per-topic ROS JSONL writing for telemetry topics. |
| S10 | codebase | `robot/ros2-runtime/src/vexy_ros/bridge_protocol.py` | 2026-06-28 | Defines ROS-side command packet normalization and JSON line encoding. |
| S11 | codebase | `robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py::VexBridgeNode` | 2026-06-28 | Defines `/vex/cmd` consumption, serial write, serial reader loop, and ack/telemetry/status publishing. |
| S12 | codebase | `robot/ros2-runtime/src/vexy_ros/bridge_demux.py::BrainStreamDemux` | 2026-06-28 | Defines classification of Brain JSON lines into ack, telemetry, or status events. |
| S13 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode` | 2026-06-28 | Defines TaskEnvelope file consumption, outline run setup, and operator result publication. |
| S14 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/_core.py::Operator.contract_result`, `packet_from_primitive` | 2026-06-28 | Defines operator-produced ContractLine-shaped results and primitive command packet creation. |
| S15 | codebase | `robot/v5-brain/pros_bridge/src/main.cpp` | 2026-06-28 | Defines V5 Brain serial receive, command handling, ack emission, telemetry emission, and motor sample JSON. |

## Excerpts

### S1 - ContractLine shape

`contracts/src/contracts/contract_line.py::ContractLine`

> `session_id`, `generation`, `round`, `task`, `motor_samples`, `predicted`, and `gap` are required model fields; `outcome`, `vision`, and `source` are optional model fields.

### S2 - SelfModel shape

`contracts/src/contracts/self_model.py::SelfModel`

> `SelfModel` includes `generation`, `parent_generation`, `config`, `structural`, `capability`, `predictive`, `gap_model`, and non-empty `reasoning`.

### S3 - Control and ack shapes

`contracts/src/contracts/control_command.py`

> `ControlEnvelope` carries `v`, `seq`, `sent_ms`, and `ttl_ms`; command subclasses add verbs such as `stop`, `drive`, `turn`, `arm`, `claw`, `flywheel`, and `routine`.

> `AckLine` carries `v`, `type`, `ack`, `state`, `recv_ms`, `fault`, and optional health fields.

### S4 - TaskEnvelope shape

`contracts/src/contracts/task_envelope.py::TaskEnvelope`

> `TaskEnvelope` contains `contract: ContractLine` and `outline: TaskOutline`.

### S5 - Gap analyzer outputs

`self_model_generator/src/self_model_generator/gap_analyzer.py`

> `read_contract_lines_jsonl` validates each non-empty JSONL line as `ContractLine`.

> `analyze_contract_lines` returns `schema_version`, `kind`, `source`, `residuals`, `diagnoses`, and `generator_handoff`.

### S6 - Generator packet inputs

`self_model_generator/src/self_model_generator/packet_builder.py::build_self_model_packet`

> The packet is built from `SelfModel`, `PartsCatalog`, `ContractLine` evidence, source references, human constraints, and an optional gap summary.

### S7 - Loop closure transforms

`self_model_generator/src/self_model_generator/loop_closure.py`

> `generate_self_model_candidate` increments generation, sets parent generation, updates predictive and gap model fields from residuals, and returns a `SelfModel`.

> `run_critic_panel` runs physics, torque, and CoM geometry reviews and returns `kind`, `approved`, and `reviews`.

> `export_task_envelope` requires critic approval and returns a `TaskEnvelope`.

### S8 - Evidence export

`robot/ros2-runtime/src/vexy_ros/evidence_export.py`

> `contract_payload_from_bundle` builds `schema_version`, `session_id`, `generation`, `round`, `task`, `motor_samples`, `predicted`, `gap`, `outcome`, `vision`, and `source`.

### S9 - Telemetry writer

`robot/ros2-runtime/src/vexy_ros/telemetry_writer_node.py::TelemetryWriterNode`

> `TelemetryWriterNode` subscribes to telemetry topics, parses JSON, injects wall time and run id, writes compact JSON lines, and flushes per message.

### S10 - Bridge protocol

`robot/ros2-runtime/src/vexy_ros/bridge_protocol.py`

> `normalize_outbound` validates protocol version, `seq`, packet `type`, clamps `ttl_ms`, and normalizes supported command fields.

> `encode_packet` serializes compact JSON plus newline as UTF-8 bytes.

### S11 - ROS VEX bridge

`robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py::VexBridgeNode`

> `_on_cmd` parses `/vex/cmd` JSON, validates it, and sends it to serial.

> `_publish_event` publishes demuxed events to `/vex/ack`, `/vex/telemetry`, or bridge status.

### S12 - Brain stream demux

`robot/ros2-runtime/src/vexy_ros/bridge_demux.py::BrainStreamDemux`

> `consume_line` JSON-decodes a Brain line, classifies the record, returns ack/telemetry/status events, and tracks pending acks.

### S13 - Operator task file flow

`robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode`

> `_consume_task_file` validates task JSON as `TaskEnvelope`, converts it to `OperatorTaskContract`, and starts the outline run.

> `_publish_contract_result` publishes `operator.contract_result(...)` as compact JSON.

### S14 - Operator packet/result flow

`robot/ros2-runtime/src/vexy_ros/operator/_core.py`

> `Operator.contract_result` builds a ContractLine-shaped payload from task contract, telemetry motor samples, predicted data, gap, outcome, vision, and source.

> `packet_from_primitive` creates protocol command packets and passes them through `normalize_outbound`.

### S15 - V5 Brain IO

`robot/v5-brain/pros_bridge/src/main.cpp`

> `receive_task` reads stdin until newline and passes complete lines to `handle_line`.

> `handle_line` accepts heartbeat, stop, drive, turn, routine, arm, release, grab, lift, and set_goal command cases.

> `emit_ack` emits protocol-v1 ack JSON with battery, watchdog, estop, motion, port, routine, motor port, and fault fields.

> `emit_telemetry` emits protocol-v1 telemetry JSON with battery, watchdog, motion, routine, motor port, drive position/velocity, and `motor_samples`.
