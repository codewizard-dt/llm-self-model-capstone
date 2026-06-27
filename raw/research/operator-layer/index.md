---
topic: the current state of the operator so we can ingest it
slug: operator-layer
researched: 2026-06-25
sources: [./sources.md]
---

# Research: The Operator Layer — Current State

> The operator layer is complete across two distinct concerns: (1) a **ROS 2 runtime** (`vexy_ros.operator`) that drives the physical robot via AprilTag-guided navigation and task abstraction methods, and (2) an **LLM packet builder** (`operator_llm`) that assembles structured evidence packets for the offline F8/F9 generator/critic loop. Both are tested and documented. The main open dependency is F10 (gap analyzer), which keeps residual-summary sections blocked or fixture-backed in the current operator packet.

## Research Questions

1. What does the `operator/` package contain and what is its purpose?
2. What does `robot/ros2-runtime/src/vexy_ros/operator/` contain and how does it differ?
3. How do the two operator concerns relate to the contracts layer?
4. What is currently blocked, and what remains for F8/F9?
5. What ROS topics/interfaces does the OperatorNode expose?

---

## Current State (Codebase)

### operator/ — Offline LLM Packet Builder

**Package**: `operator-llm-critic` v0.2.0 (`operator/pyproject.toml`)
**Python**: ≥3.12,<3.13
**Runtime deps**: `pydantic>=2.12`, `reactivex>=4.1.0`
**PYTHONPATH**: `src:../contracts/src:../robot/ros2-runtime/src` (from `operator/Makefile`)

Source lives in `operator/src/operator_llm/` with three files:

| File | Symbols | Purpose |
|------|---------|---------|
| `packet_builder.py` | `build_packet_from_files`, `build_operator_packet`, `_*_block` helpers, blocked-state constants | Assembles a Markdown evidence packet for the F8 Generator |
| `validate.py` | `validate_fixture_packets`, `main` | Validates the two canonical packet types against their blocked-state invariants |
| `__init__.py` | `__all__` | Public surface (minimal) |

**`build_operator_packet`** (`packet_builder.py:81–140`) produces a structured Markdown document with sections:
- Track 1 (M1 + ROS Proof Intake): contract surface + ROS proof routine + hardware proof status
- Track 2 (Operator LLM Packet): source refs, current SelfModel, parts catalog verdict, contract evidence, gap summary, human constraints, generator guardrails

**`build_packet_from_files`** (`packet_builder.py:42–78`) is the file-level entry point; accepts optional `contract_jsonl_path`, `ros_bundle_path`, `gap_summary_path`. When a ROS bundle is supplied it calls `vexy_ros.evidence_export.contract_jsonl_from_bundle` and stamps `source_refs["ros_export_routine"]` accordingly.

**Blocked-state constants** (all in `packet_builder.py`):
- `BLOCKED_F10_GAP` — emitted when no gap summary is provided
- `BLOCKED_NO_CONTRACT_EVIDENCE` — emitted when no contract lines exist
- `BLOCKED_HARDWARE_PROOF` — emitted when contract lines exist but none have a `raw_session_path`
- `FIXTURE_BACKED_GAP` — label for fixture-supplied gap summaries

**`validate_fixture_packets`** (`validate.py:21–47`) runs both the "contract-JSONL path" and "ROS-bundle path" packet types through assertion checks that confirm blocked labels appear (or don't) in the right sections. It serves as a living integration test of the packet builder's invariants.

**Tests** (`operator/tests/test_packet_builder.py`): 5 test functions exercise:
- F10 + hardware-proof blockers with a contract fixture
- ROS bundle intake naming the proof-export routine and preserving `raw_session_path`
- Missing-contract blocked label
- Fixture-backed gap-summary labeling
- Catalog violations exposed without operator-local schemas

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

`operator/docs/llm_critic_architecture.md` (created 2026-06-24, owner: Grace Huang) is the architecture bridge doc for F8/F9. It:
- Defines Generator and three stateless Critics (physics, torque, CoM/geometry)
- Specifies input/output contracts for both
- Names F10 gap-analyzer as the remaining blocker for full F8 Generator implementation
- Lists 6 implementation slices (operator-packet-builder → generator-prompt → generator-gap-revision → critic-prompt-panel → critic-review-aggregation → planted-fault-critic-tests)
- Confirms offline LLM work is allowed to run outside the Pi

`robot/ros2-runtime/operator/GUIDEBOOK.md` documents the ROS operator from the operator's perspective: primitive commands, operator abstractions, task outline format, vision inputs, localization, telemetry events, contract results, and ad-hoc SSH commands.

### Evidence Export Integration

`vexy_ros.evidence_export.contract_jsonl_from_bundle` (`evidence_export.py:70–77`) is the proof-export routine cited in operator packets. It:
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

Neither `operator/` nor `vexy_ros/operator/` defines their own telemetry or self-model schemas — they import from `contracts`.

---

## Key Findings

1. **Two distinct operator concerns exist** [S1, S2]: (a) `operator/src/operator_llm` is a Python package for offline LLM packet assembly; (b) `robot/ros2-runtime/src/vexy_ros/operator` is the live ROS 2 node that controls the robot. Both are implemented and tested.

2. **The ROS operator is feature-complete for ball-delivery tasks** [S2, S4]: `Operator` implements all six task methods (`locate_nearest_apriltag`, `orient_to_tag`, `move_to_tag`, `grab`, `lift`, `release`), dead-reckoning localization, stuck/spinout fault detection, manipulator telemetry for `has_object`, and `contract_result` emission.

3. **The packet builder implements both input paths** [S1]: standard ContractLine JSONL and ROS-bundle intake via `vexy_ros.evidence_export.contract_jsonl_from_bundle`. The bundle path stamps `source_refs["ros_export_routine"]` for traceability.

4. **F10 gap analyzer has a first slice** [S3]: Gap summary sections are blocked (`BLOCKED_F10_GAP`) when no `gap_summary_path` is provided, or labeled with fixture/live/replay provenance when the supplied summary source metadata matches the packet evidence.

5. **F8 Generator and F9 Critics are not yet implemented** [S3]: The architecture doc defines their input/output contracts but lists them as future slices. The packet builder is the completed prerequisite for both.

6. **Task outline drives allowed methods** [S2]: `OperatorTaskContract` parses the `task_outline_json` parameter into a `method_plan`. Ad-hoc SSH commands are only accepted if their action appears in the loaded task outline.

7. **Contract results are emitted live** [S2]: Every operator method run publishes a `ContractLine`-compatible dict to `/operator/results`, incrementing `run_index` per call.

---

## Constraints

- **No second schemas**: `operator/` must import from `contracts/`, not define its own telemetry, self-model, or parts shapes.
- **F10 gap required for full F8**: Until broader F10 coverage lands, gap summary sections in packets must use provenance-backed labels or remain `BLOCKED_F10_GAP`.
- **Generator cannot read oracle parameters**: Information separation is enforced by the packet builder (generator guardrails section).
- **ROS operator runs on Pi**: Fast control loop (0.25 s status timer) must stay on-Pi; Generator/Critics run offline.
- **AprilTag map required**: `OperatorNode` cannot start without a valid workspace map (either `workspace_map_path` or `tag_anchors_json`).
- **Task outline required**: `OperatorTaskContract` rejects an empty method plan.
- **Python 3.12 only**: `operator/` pins `>=3.12,<3.13`.

---

## Recommendation

The operator layer is well-implemented across both concerns. For wiki ingestion, treat the two operator concerns as distinct components:

1. **`operator_llm` (Offline Packet Builder)** — a separate component entry under `knowledge/entities/components/`
2. **`vexy_ros.operator` (ROS 2 Operator Node)** — extend or update the existing `vexy-ros-runtime` component page

The LLM/Critic architecture doc (`operator/docs/llm_critic_architecture.md`) is a significant source that should be ingested as a knowledge/sources page and linked to the `llm-authored-self-model` concept.

**Next Steps**:
- `/wiki-ingest raw/research/operator-layer/index.md` — this report
- Create component page for `operator_llm` packet builder
- Update `vexy-ros-runtime` component page to include the operator node and GUIDEBOOK content
- Ingest `operator/docs/llm_critic_architecture.md` as a source document
- `/task-add` for F8 Generator prompt skeleton (next implementation slice per architecture doc)
