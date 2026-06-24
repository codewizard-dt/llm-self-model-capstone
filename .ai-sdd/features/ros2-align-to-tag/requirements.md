# ros2-align-to-tag - Requirements

| Field | Value |
|---|---|
| Feature ID | `ros2-align-to-tag` |
| Vertical | `coprocessor` / `pilot` boundary |
| Root | `robot/ros2-runtime/` |
| Stack | Python 3.11 on Ubuntu 24.04 + ROS 2 Jazzy |
| Status | Approved for slice planning |
| Source | `raw/research/ros2-jazzy-supervisory-control-plan/index.md` |

---

## Goal

Prove the first ROS 2 closed-loop robot-control slice for Vexy: calibrated Camera Module 3 frames feed rectified AprilTag pose, the ROS VEX bridge proves heartbeat/stop/motion against the V5 Brain, an `AlignToTag` action sends only short bounded commands until the robot reaches tag-alignment tolerance or reports a typed failure, and the run records both raw MCAP evidence and contract-valid JSONL semantics.

This is the bridge from "ROS 2 camera works" to "ROS 2 can safely close a local feedback loop around the real robot." It intentionally keeps Codex out of the fast loop: Codex may supervise, review evidence, and choose high-level skills, but ROS and Brain-side safety own the live loop.

---

## In Scope

- Keep the committed runtime in `robot/ros2-runtime/`, matching the Pi deployment model where the repo package is symlinked into `~/ros2_ws/src/`.
- Preserve `robot/pi-runtime/` as the working Bookworm fallback until this Jazzy path proves parity.
- Update Jazzy launch/config so Camera Module 3 publishes:
  - raw image topic for viewing and bags
  - nonzero calibrated `CameraInfo`
  - rectified image topic suitable for AprilTag pose
- Add launch/config wiring for `image_proc` and `apriltag_ros`.
- Verify or correct current `camera_ros` frame-rate handling against the installed version; do not assume the existing `fps` parameter is honored.
- Port the proven `robot/pi-runtime` serial reader pattern into the ROS bridge so command acknowledgements and streaming telemetry are not confused on the shared serial stream.
- Keep the current newline JSON v1 V5 wire protocol until this slice is stable.
- Expose typed-enough ROS topics for bridge command, acknowledgement, telemetry, heartbeat, and fault state.
- Implement a minimal `AlignToTag` skill/action surface in `robot/ros2-runtime/`.
- Make `AlignToTag` issue only bounded, interruptible movement commands with TTL/stop semantics preserved by the V5 Brain.
- Record a ROS bag/MCAP proof run and export a contract-valid JSONL observation for downstream `contracts/` and `operator/` use.
- Add a short runbook that separates camera proof, tag proof, serial/ack proof, motion proof, and closed-loop proof.

---

## Out Of Scope

- Binary protocol v2, CRC framing, or a Brain/RPi protocol rewrite.
- MCP server tools, external agent control, or an open-ended online task interface.
- Full world model, object tracking, `AcquireEntity`, pickup/place behavior, YOLO object selection, or bin scoring.
- Removing or deprecating `robot/pi-runtime/`.
- Replacing the Brain safety model; V5 remains final actuator authority.
- Large ROS package split. A custom interface package is allowed only if the action/message definitions make it clearly simpler than local Python message conventions.
- New camera hardware or depth hardware.
- Contract schema redesign beyond whatever exporter fields are required for this slice.

---

## Acceptance

1. Jazzy base is operational on the Pi: `/opt/ros/jazzy` is present, the package builds in `~/ros2_ws`, and the repo-owned runtime remains `robot/ros2-runtime/`.
2. Camera proof is real: Camera Module 3 publishes live images, calibrated nonzero `CameraInfo`, stable frame IDs, and timestamps.
3. Rectification proof is real: `image_proc` produces a rectified image topic that can be consumed by downstream nodes.
4. AprilTag proof is real: `apriltag_ros` detects a configured printed tag from the rectified image stream and publishes stable pose/TF while the robot is stationary.
5. Serial proof is real: the ROS bridge can send heartbeat/stop and receive the expected V5 acknowledgement without conflating it with telemetry.
6. Fault behavior is explicit: missing ack, stale telemetry, serial disconnect, and Brain timeout surface as faults and cause safe stop behavior.
7. Motion proof is bounded: a short command can move the robot on blocks or in a safe fixture, then stop through TTL/watchdog behavior visible in telemetry.
8. `AlignToTag` proof is closed-loop: with a visible tag, the action publishes feedback including yaw/lateral/distance error, confidence, and safety/fault state; it reaches configured tolerance or returns an explicit failure.
9. Codex is not in the fast loop. The action continues to obey fixed control grammar and safety bounds even if no LLM call occurs during execution.
10. Evidence is saved: at least one MCAP bag captures camera, tag, bridge, command, ack, telemetry, and action feedback topics for the run.
11. Semantics are exported: at least one contract-valid JSONL observation is generated from the proof run and can be validated by the existing contract tooling.
12. Documentation identifies the exact commands used for camera proof, tag proof, serial proof, motion proof, closed-loop proof, bag capture, and JSONL export.

---

## Constraints

- Use `uv` for Python environments and `ruff` for Python lint/format checks; no pip/poetry/black/isort/flake8 workflow drift.
- ROS runtime Python remains Python 3.11 unless the existing vertical conventions are explicitly revised.
- All durable schemas live under `contracts/`; ROS messages/actions are transport bindings, not a second source of truth.
- The V5 Brain remains PROS C++ and remains the final authority for clamps, TTLs, watchdogs, and stop behavior.
- Commands must be fixed grammar and interruptible. No raw motor power, raw serial write, raw camera stream, or safety-disable surfaces.
- The feature must distinguish camera success, tag success, serial ack success, motion success, and closed-loop success in both docs and evidence.

---

## Decisions

| # | Decision | Proposed Resolution | Status |
|---|---|---|---|
| D1 | Runtime layout | Continue evolving `robot/ros2-runtime/`; do not add a parallel committed `vex_agent_ws` tree for this slice. | `closed` |
| D2 | First proof task | Make calibrated AprilTag `AlignToTag` the first closed-loop proof before object pickup or open-ended tasks. | `closed` |
| D3 | Wire protocol | Keep newline JSON v1 until this slice is stable; defer binary protocol v2/CRC. | `closed` |
| D4 | Bridge architecture | Port the existing `robot/pi-runtime` reader-thread ack/telemetry split into the ROS bridge before treating motion proof as meaningful. | `closed` |
| D5 | Evidence split | Treat MCAP as raw time-series evidence and contract-valid JSONL as the semantic self-model/operator feedback surface. | `closed` |
| D6 | Agent boundary | No MCP/open-ended agent tools in this feature; expose `AlignToTag` as the bounded skill boundary first. | `closed` |

---

## Planning Status

Human approval received in-session on 2026-06-24. The feature is decomposed into slices and wired by `pipeline.yaml`; each slice still needs the planner -> implementer -> reviewer loop before implementation.
