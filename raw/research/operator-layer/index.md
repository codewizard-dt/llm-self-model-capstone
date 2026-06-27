---
topic: the current state of the operator so we can ingest it
slug: operator-layer
researched: 2026-06-25
sources: [./sources.md]
---

# Research: The Operator Layer — Current State

> The robot-control operator and offline self-model generator are separate concerns: (1) a **ROS 2 runtime** (`vexy_ros.operator`) that drives the physical robot via AprilTag-guided navigation and task abstraction methods, and (2) an **offline self-model generator** (`self_model_generator`) that assembles structured evidence packets for the F8/F9 generator/critic loop. Both are tested and documented. F10 now has a first gap-summary slice, and F8/F9 have a deterministic first loop-closure slice.

## Research Questions

1. What does the `self_model_generator/` package contain and what is its purpose?
2. What does `robot/ros2-runtime/src/vexy_ros/operator/` contain and how does it differ?
3. How do the live operator and offline self-model generator relate to the contracts layer?
4. What is currently blocked, and what remains for F8/F9?
5. What ROS topics/interfaces does the OperatorNode expose?

---

## Current State (Codebase)

### self_model_generator/ — Offline Self-Model Generator

**Package**: `self-model-generator` (`self_model_generator/pyproject.toml`)
**Python**: ≥3.12,<3.13
**Runtime deps**: `pydantic>=2.12`, `reactivex>=4.1.0`
**PYTHONPATH**: `src:../contracts/src:../robot/ros2-runtime/src` (from `self_model_generator/Makefile`)

Source lives in `self_model_generator/src/self_model_generator/` with packet-building and loop-closure modules:

| File | Symbols | Purpose |
|------|---------|---------|
| `packet_builder.py` | `build_packet_from_files`, `build_self_model_packet`, `_*_block` helpers, blocked-state constants | Assembles a Markdown evidence packet for the F8 Generator |
| `gap_analyzer.py` | `build_gap_summary_from_jsonl`, `analyze_contract_lines`, `write_gap_summary` | Builds provenance-labeled F10 residual/diagnosis summaries |
| `loop_closure.py` | `generate_self_model_candidate`, `run_critic_panel`, `export_task_envelope` | Runs the deterministic first F8/F9 loop-closure slice |
| `validate.py` | `validate_fixture_packets`, `validate_loop_closure_fixture`, `main` | Validates packet and loop-closure fixture invariants |
| `__init__.py` | `__all__` | Public surface |

**`build_self_model_packet`** (`packet_builder.py`) produces a structured Markdown document with sections:
- Track 1 (M1 + ROS Proof Intake): contract surface + ROS proof routine + hardware proof status
- Track 2 (Self-Model Generator Packet): source refs, current SelfModel, parts catalog verdict, contract evidence, gap summary, human constraints, generator guardrails

**`build_packet_from_files`** (`packet_builder.py:42–78`) is the file-level entry point; accepts optional `contract_jsonl_path`, `ros_bundle_path`, `gap_summary_path`. When a ROS bundle is supplied it calls `vexy_ros.evidence_export.contract_jsonl_from_bundle` and stamps `source_refs["ros_export_routine"]` accordingly.

**Blocked-state constants** (all in `packet_builder.py`):
- `BLOCKED_F10_GAP` — emitted when no gap summary is provided
- `BLOCKED_NO_CONTRACT_EVIDENCE` — emitted when no contract lines exist
- `BLOCKED_HARDWARE_PROOF` — emitted when contract lines exist but none have a `raw_session_path`
- `FIXTURE_BACKED_GAP` — label for fixture-supplied gap summaries

**`validate_fixture_packets`** (`validate.py:21–47`) runs both the "contract-JSONL path" and "ROS-bundle path" packet types through assertion checks that confirm blocked labels appear (or don't) in the right sections. It serves as a living integration test of the packet builder's invariants.

**Tests** (`self_model_generator/tests/`): packet, gap analyzer, fixture-loader, and loop-closure tests exercise:
- F10 + hardware-proof blockers with a contract fixture
- ROS bundle intake naming the proof-export routine and preserving `raw_session_path`
- Missing-contract blocked label
- Fixture-backed gap-summary labeling
- Catalog violations exposed without self_model_generator-local schemas
- Generator revision from gap summary
- Deterministic three-lane critic review
- Approval-gated `TaskEnvelope` export

### robot/ros2-runtime/src/vexy_ros/operator/ — ROS 2 Runtime

This is the **on-robot** operator — it runs as a ROS 2 node on the Raspberry Pi, consumes live sensor streams, and drives the VEX V5 Brain via primitive commands.

**Three files**:

| File | Key symbols | Purpose |
|------|-------------|---------|
| `core.py` | `Operator`, `OperatorTaskContract`, `TelemetrySnapshot`, `VisionSnapshot`, `OperatorEvent`, `OperatorResult`, helper data classes | Pure-Python business logic, no ROS dependency |
| `node.py` | `OperatorNode`, `RosCommandSink` | ROS 2 node wrapper; subscribes to topics, delegates to `Operator` |
| `__init__.py` | — | Package init |

#### `Operator` class (`core.py:288–832`)

The `Operator` is the Pi-side orchestration brain above V5 primitives. It:

- **Requires** on construction: `april_tag_map`, `camera_in_robot` (Pose2D), `task_contract` (ContractLine mapping + method plan), optional `task_outline`, `config`, `clock`, `event_sink`
- **Maintains state**: `vision` (VisionSnapshot), `telemetry` (TelemetrySnapshot | None), `map_pose` (Pose2D | None), `localization_source` ("apriltag" | "dead_reckoning" | "unknown"), `last_command`, `last_target_distance_m`
- **Methods** (the operator abstractions):
  - `locate_nearest_apriltag()` — finds nearest mapped tag or sends `turn`
  - `orient_to_tag(tag_index)` — aligns yaw, then `stop`
  - `move_to_tag(tag_index, *, target_distance_m)` — drives toward map-derived standoff pose; emits stuck/spinout events on drive-health failure
  - `grab()`, `lift()`, `release()` — claw/manipulator primitives
  - `detect_drive_health(tag_index)` — checks wheel velocity vs visual progress to detect stuck/slip/disabled
  - `has_object()` — infers object in claw from manipulator telemetry
- **Localization**: AprilTag-primary with dead-reckoning fallback (`_update_pose_from_vision`, `_advance_dead_reckoning`)
- **Standoff distances** by tag role: `bin`→0.38m, `ball_staging`/`ball_loading`/`ball`/`home`→0.45m, default→0.45m
- **Contract result** (`contract_result` method, `core.py:363–395`): emits a `ContractLine`-compatible dict with motor samples, vision block, gap, outcome, and source; increments `run_index` per call

**`OperatorTaskContract`** (`core.py:228–247`): a frozen dataclass wrapping the raw ContractLine mapping + a parsed `method_plan` (tuple of `OperatorMethodCall`). Validates the contract line shape and enforces at least one operator method.

#### `OperatorNode` (`node.py:50–360`)

ROS 2 node class extending `rclpy.node.Node` (node name: `"vexy_operator"`).

**ROS parameters** (declared on init):
- `camera_in_robot_json` (default: `{"x_m":0,"y_m":0,"yaw_rad":0}`)
- `workspace_map_path` or `tag_anchors_json`
- `task_contract_json`
- `task_outline_json`
- `command_topic` → `/operator/command`
- `event_topic` → `/operator/events`
- `result_topic` → `/operator/results`
- `status_topic` → `/operator/status`

**Subscriptions**:
- `/tf` (TFMessage) — AprilTag transforms → `_on_tf`
- `/vision/scene_map` (String/JSON) — scene context → `_on_scene_map`
- `/vision/object_detections` (String/JSON) → `_on_object_detections`
- `/vision/object_indections` (String/JSON) → `_on_object_indications`
- `/vex/telemetry` (String/JSON) → `_on_telemetry`
- `/operator/command` (String/JSON) → `_on_command` (ad-hoc SSH commands)

**Publishers**:
- `/operator/events` — structured JSON event stream
- `/operator/results` — ContractLine-compatible result per method run
- `/operator/status` — periodic status (every 0.25 s timer)

**Events published** (from GUIDEBOOK.md and core.py):
`apriltag_searching`, `apriltag_map_loaded`, `apriltag_located`, `oriented`, `arrived`, `stuck`, `spinout`, `grabbed`, `command_rejected`, `pose_estimated`

### Operator Docs

`self_model_generator/docs/llm_critic_architecture.md` (created 2026-06-24, owner: Grace Huang) is the architecture bridge doc for F8/F9. It:
- Defines Generator and three stateless Critics (physics, torque, CoM/geometry)
- Specifies input/output contracts for both
- Documents the first deterministic loop-closure slice in `self_model_generator.loop_closure`
- Lists remaining hardening/adaptor slices: broader residual coverage, planted-fault critic tests, and external LLM prompt adapters
- Confirms offline LLM work is allowed to run outside the Pi

`robot/ros2-runtime/operator/GUIDEBOOK.md` documents the ROS operator from the operator's perspective: primitive commands, operator abstractions, task outline format, vision inputs, localization, telemetry events, contract results, and ad-hoc SSH commands.

### Evidence Export Integration

`vexy_ros.evidence_export.contract_jsonl_from_bundle` (`evidence_export.py:70–77`) is the proof-export routine cited in self-model packets. It:
1. Accepts a bundle dict (from `bundle_from_tag_action_summary` or `bundle_from_proof_dir`)
2. Calls `contract_payload_from_bundle` to build the ContractLine payload
3. Serializes to JSON, validates against the ContractLine schema, and appends `\n`

This function is the bridge between ROS bag/proof data and the LLM packet builder.

### Contracts Layer (shared schemas)

`contracts/src/contracts/` provides all durable data models:
- `ContractLine` — per-task telemetry envelope with motor samples, gap, outcome, vision, source
- `SelfModel` / `SelfModelConfig` — versioned robot self-description (generation, config, structural, capability, predictive, gap_model, reasoning)
- `PartsCatalog` / `validate_config` — finite parts vocabulary and buildability rules
- `vocabulary` — shared enums (motor allocation, end effector, cartridge)

Neither `self_model_generator/` nor `vexy_ros/operator/` defines its own telemetry or self-model schemas — both import from `contracts`.

---

## Key Findings

1. **Two distinct concerns exist** [S1, S2]: (a) `self_model_generator/src/self_model_generator` is the offline Python package for self-model packet assembly and first loop-closure slices; (b) `robot/ros2-runtime/src/vexy_ros/operator` is the live ROS 2 node that controls the robot. Both are implemented and tested.

2. **The ROS operator is feature-complete for ball-delivery tasks** [S2, S4]: `Operator` implements all six task methods (`locate_nearest_apriltag`, `orient_to_tag`, `move_to_tag`, `grab`, `lift`, `release`), dead-reckoning localization, stuck/spinout fault detection, manipulator telemetry for `has_object`, and `contract_result` emission.

3. **The packet builder implements both input paths** [S1]: standard ContractLine JSONL and ROS-bundle intake via `vexy_ros.evidence_export.contract_jsonl_from_bundle`. The bundle path stamps `source_refs["ros_export_routine"]` for traceability.

4. **F10 gap analyzer has a first slice** [S3]: Gap summary sections are blocked (`BLOCKED_F10_GAP`) when no `gap_summary_path` is provided, or labeled with fixture/live/replay provenance when the supplied summary source metadata matches the packet evidence.

5. **F8/F9 have a deterministic first slice** [S3]: `self_model_generator.loop_closure` can emit a candidate `SelfModel`, run physics/torque/CoM critic checks, and export an approved next `TaskEnvelope`. External LLM prompt adapters remain future work.

6. **Task outline drives allowed methods** [S2]: `OperatorTaskContract` parses the `task_outline_json` parameter into a `method_plan`. Ad-hoc SSH commands are only accepted if their action appears in the loaded task outline.

7. **Contract results are emitted live** [S2]: Every operator method run publishes a `ContractLine`-compatible dict to `/operator/results`, incrementing `run_index` per call.

---

## Constraints

- **No second schemas**: `self_model_generator/` must import from `contracts/`, not define its own telemetry, self-model, or parts shapes.
- **F10 gap required for full F8**: Until broader F10 coverage lands, gap summary sections in packets must use provenance-backed labels or remain `BLOCKED_F10_GAP`.
- **Generator cannot read oracle parameters**: Information separation is enforced by the packet builder (generator guardrails section).
- **ROS operator runs on Pi**: Fast control loop (0.25 s status timer) must stay on-Pi; Generator/Critics run offline.
- **AprilTag map required**: `OperatorNode` cannot start without a valid workspace map (either `workspace_map_path` or `tag_anchors_json`).
- **Task outline required**: `OperatorTaskContract` rejects an empty method plan.
- **Python 3.12 only**: `self_model_generator/` pins `>=3.12,<3.13`.

---

## Recommendation

For wiki ingestion, treat the live robot-control operator and offline self-model generator as distinct components:

1. **`self_model_generator` (Offline Self-Model Generator)** — a separate component entry under `knowledge/entities/components/`
2. **`vexy_ros.operator` (ROS 2 Operator Node)** — extend or update the existing `vexy-ros-runtime` component page

The LLM/Critic architecture doc (`self_model_generator/docs/llm_critic_architecture.md`) is a significant source that should be ingested as a knowledge/sources page and linked to the `llm-authored-self-model` concept.

**Next Steps**:
- `/wiki-ingest raw/research/operator-layer/index.md` — this report
- Create or update the component page for `self_model_generator`
- Update `vexy-ros-runtime` component page to include the operator node and GUIDEBOOK content
- Ingest `self_model_generator/docs/llm_critic_architecture.md` as a source document
- `/task-add` for F8 Generator prompt skeleton (next implementation slice per architecture doc)
