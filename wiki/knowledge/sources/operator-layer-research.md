---
id: operator-layer-research
title: "Research: Operator Layer — Current State"
updated: 2026-06-25
sources:
  - ../../../../raw/research/operator-layer/index.md
tags: [source, operator, ros2, llm-packet-builder, f8, f9, f10, contracts]
---

# Research: Operator Layer — Current State

derived_from::[[raw/research/operator-layer/index.md]]
relates_to::[[vexy-ros-runtime]]
relates_to::[[self-model-packet-builder]]
relates_to::[[task-telemetry-contract]]
relates_to::[[llm-authored-self-model]]

## Summary

**The robot-control operator and offline self-model generator are separate concerns.** The first is a live ROS 2 runtime (`vexy_ros.operator`) that drives the physical robot on the Raspberry Pi via AprilTag-guided navigation and a typed set of task abstraction methods. The second is an offline packet builder (`self_model_generator`, package `self-model-generator`) that assembles structured Markdown evidence packets for the F8 Generator/F9 Critic loop. Both are implemented, tested, and documented.

**The ROS 2 operator node (`OperatorNode`, node name `vexy_operator`) is feature-complete for ball-delivery tasks.** `Operator` in `core.py` implements six task methods — `locate_nearest_apriltag`, `orient_to_tag`, `move_to_tag`, `grab`, `lift`, `release` — plus dead-reckoning localization fallback, stuck/spinout fault detection via drive-health checking, `has_object` inference from manipulator telemetry, and per-method `contract_result` emission to `/operator/results`. The node subscribes to `/tf`, `/vision/scene_map`, `/vision/object_detections`, and `/vex/telemetry`, and publishes structured events on `/operator/events` and periodic status on `/operator/status`.

**The offline packet builder (`self_model_generator/src/self_model_generator/packet_builder.py`) implements both input paths**: standard ContractLine JSONL (via `contract_jsonl_path`) and ROS-bundle intake via `vexy_ros.evidence_export.contract_jsonl_from_bundle` (via `ros_bundle_path`). The output is a structured Markdown document with two tracks: Track 1 covers the contract surface, ROS proof routine, and hardware proof status; Track 2 covers the current SelfModel, parts catalog verdict, contract evidence, gap summary, human constraints, and generator guardrails. F10 (gap analyzer) now has a first slice: gap summary sections are labeled `BLOCKED_F10_GAP` when no `gap_summary_path` is provided, or provenance-labeled as fixture, live, or replay when a summary is supplied. The packet builder cross-checks the summary source metadata against the actual `ContractLine` evidence before building the generator packet.

**The architecture bridge document** (`self_model_generator/docs/llm_critic_architecture.md`, owner: Grace Huang) defines the Generator/Critic architecture: one Generator LLM and three stateless Critics (physics, torque, CoM/geometry). It names F10 gap-analyzer as the remaining blocker and lists six implementation slices remaining for the full F8/F9 system.

## Key Claims

1. **Two distinct concerns**: (a) `self_model_generator/src/self_model_generator` — offline Python package for LLM packet assembly; (b) `robot/ros2-runtime/src/vexy_ros/operator` — live ROS 2 node controlling the robot.
2. **ROS operator is feature-complete** for ball-delivery: all six task methods implemented, dead-reckoning localization, stuck/spinout detection, and live `ContractLine`-compatible result emission per method run.
3. **Both packet-builder input paths work**: JSONL direct and ROS-bundle via `contract_jsonl_from_bundle`, with bundle path stamping `source_refs["ros_export_routine"]` for traceability.
4. **F10 gap analyzer has a first slice**: gap sections use `BLOCKED_F10_GAP` when no summary is supplied, or fixture/live/replay provenance labels when summary source metadata matches the packet evidence.
5. **F8 Generator and F9 Critics are not yet implemented**: architecture doc defines their contracts but lists them as future slices; packet builder is the completed prerequisite.
6. **Task outline drives allowed methods**: `OperatorTaskContract` parses `task_outline_json` into a `method_plan`; ad-hoc SSH commands are only accepted if their action appears in the loaded outline.
7. **No second schemas**: both the robot-control operator and self-model generator import from `contracts/` — no local telemetry, self-model, or parts definitions.

## Constraints Recorded

- Generator cannot read oracle parameters (information separation enforced by packet builder's guardrails section).
- ROS operator must run on Pi (0.25 s control loop); Generator/Critics run offline.
- `OperatorNode` cannot start without a valid workspace map.
- `OperatorTaskContract` rejects an empty method plan.
- `operator/` pins Python ≥3.12,<3.13.
