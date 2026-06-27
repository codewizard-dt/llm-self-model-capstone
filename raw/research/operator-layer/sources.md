---
topic: the current state of the operator so we can ingest it
slug: operator-layer
researched: 2026-06-25
---

# Primary Sources — The Operator Layer

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `operator/src/operator_llm/packet_builder.py::build_operator_packet` | 2026-06-25 | Full packet structure: all 8 sections, blocked-state constants, source-refs stamping for ROS bundles |
| S2 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/core.py::Operator` | 2026-06-25 | Complete method list, localization state machine, `contract_result` schema, `OperatorTaskContract` structure |
| S3 | codebase | `operator/docs/llm_critic_architecture.md` | 2026-06-25 | F8/F9 architecture contract, Generator/Critic input-output specs, F10 blocker, implementation slice list |
| S4 | codebase | `robot/ros2-runtime/operator/GUIDEBOOK.md` | 2026-06-25 | Primitive commands, operator abstractions, task outline format, vision inputs, localization, telemetry events, contract results, SSH command format |
| S5 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py::OperatorNode` | 2026-06-25 | ROS topics (subscriptions + publishers), parameters, 0.25 s status timer |
| S6 | codebase | `robot/ros2-runtime/src/vexy_ros/evidence_export.py::contract_jsonl_from_bundle` | 2026-06-25 | Proof-export routine cited in packets: validates and serializes bundle to ContractLine JSONL |
| S7 | codebase | `operator/src/operator_llm/validate.py::validate_fixture_packets` | 2026-06-25 | Integration test confirming blocked-state invariants for both JSONL and ROS-bundle packet paths |
| S8 | codebase | `operator/tests/test_packet_builder.py` | 2026-06-25 | 5 test functions: F10 + hardware-proof blockers, ROS bundle naming, missing-contract label, fixture gap label, catalog violations |
| S9 | codebase | `operator/pyproject.toml` | 2026-06-25 | Package name `operator-llm-critic` v0.2.0, Python 3.12 constraint, pydantic + reactivex deps |
| S10 | codebase | `operator/Makefile` | 2026-06-25 | PYTHONPATH includes `../contracts/src` and `../robot/ros2-runtime/src` — confirms shared dependency |
| S11 | codebase | `operator/docs/README.md` | 2026-06-25 | Operator vertical purpose: Generator (Gen 0 + Gen N+1), Critic panel, gap analyzer, presenter/demo replay |

## Excerpts

### S1 — `build_operator_packet` sections
`operator/src/operator_llm/packet_builder.py` lines 81–140
> Sections produced: `# Operator Packet`, `## Track 1 - M1 + ROS Proof Intake`, `## Track 2 - Operator LLM Packet`, `### Source References`, `### Current SelfModel`, `### Parts Catalog Verdict`, `### Contract Evidence`, `### Gap Summary`, `### Human Constraints`, `### Generator Guardrails`

### S2 — `Operator` method list
`robot/ros2-runtime/src/vexy_ros/operator/core.py` lines 288–832
> Methods: `update_vision`, `update_telemetry`, `current_pose`, `require_allowed_method`, `contract_result`, `locate_nearest_apriltag`, `orient_to_tag`, `move_to_tag`, `grab`, `lift`, `release`, `target_distance_for_tag`, `target_pose_for_tag`, `detect_drive_health`, `has_object`

### S3 — F10 gap summary labels
`self_model_generator/docs/llm_critic_architecture.md`
> "If `self_model_generator.gap_analyzer` has produced a summary from contract-valid JSONL, packets should include that file and use the matching provenance label instead of the F10 blocked label."

### S4 — Standoff distances
`robot/ros2-runtime/operator/GUIDEBOOK.md`
> "bin: 0.38 m; ball_staging, ball_loading, or ball: 0.45 m; home: 0.45 m; any other role: operator default 0.45 m"

### S5 — OperatorNode subscriptions
`robot/ros2-runtime/src/vexy_ros/operator/node.py` lines 100–115
> Subscribes to: `/tf`, `/vision/scene_map`, `/vision/object_detections`, `/vision/object_indications`, `/vex/telemetry`, `/operator/command`

### S6 — `contract_jsonl_from_bundle` body
`robot/ros2-runtime/src/vexy_ros/evidence_export.py` lines 70–77
> `payload = contract_payload_from_bundle(bundle); line = json.dumps(payload, ..., sort_keys=True); if validate: validate_contract_line(line); return line + "\n"`

### S7 — ROS packet validation invariant
`operator/src/operator_llm/validate.py` lines 36–43
> `if "vexy_ros.evidence_export.contract_jsonl_from_bundle" not in ros_packet: raise AssertionError(...)` and `if "proof/rosbags/align_to_tag_fixture" not in ros_packet: raise AssertionError(...)`
