---
topic: "Reconcile the PiCam2 on Ubuntu 24.04 + ROS 2 Jazzy supervisory-control plan with the current Vexy codebase"
slug: ros2-jazzy-supervisory-control-plan
researched: 2026-06-23
sources: [./sources.md]
---

# Research: ROS 2 Jazzy Supervisory Control Plan

> The pasted plan is directionally right: Codex should supervise high-level skills, ROS should own local feedback, and the V5 Brain should remain the actuator and safety authority. For this repo, the ideal version is not a greenfield `vex_agent_ws`; it is a staged evolution of `robot/ros2-runtime` while keeping `robot/pi-runtime` as the working fallback until parity is proven. The first real closed-loop proof should be calibrated AprilTag alignment, not object pickup or arbitrary agentic robotics.

## Research Questions

- Does the proposed architecture fit the repo's two-loop self-model requirements?
- What should change in the current `robot/ros2-runtime` scaffold before it can support the plan?
- What should remain in `robot/pi-runtime` and `robot/v5-brain` during the migration?
- Which external ROS/camera assumptions are correct for Ubuntu 24.04 + Jazzy + Camera Module 3?
- What is the safest implementation order?

## Current State

`MASTER_REQUIREMENTS.md` makes the offline self-model loop the hard demo requirement and places online control in the `pilot` vertical as a bounded, interruptible stretch path. It also says schemas and adapter interfaces belong in `contracts`, while the coprocessor and Brain remain separate runtime surfaces [S2].

The repo already has a ROS 2 Jazzy surface at `robot/ros2-runtime`. It launches `camera_ros`, a custom `vex_bridge_node`, and `foxglove_bridge`; it records through ROS bags and intentionally keeps the V5 wire protocol as newline JSON for firmware compatibility [S3][S4].

The older `robot/pi-runtime` is still valuable. It documents the System 2/System 1 split, single camera ownership, and a stronger serial reader pattern that separates acknowledgements from telemetry before logging [S6][S7].

The V5 Brain program already has the key safety behavior: short watchdog, TTLs, command clamps, stall detection, telemetry emission, and Brain-side stop behavior [S8]. That behavior should be preserved while the Pi side migrates.

The freshest committed evidence bundle says the Pi camera was healthy, but the V5 Brain was absent from the USB bus during that capture. So any ROS migration plan must keep "camera healthy" and "serial/motion healthy" as separate proof gates [S10].

## Key Findings

### 1. The Control Split Is Correct

The pasted principle is exactly right for this robot: agent loop slow, robot loop fast, V5 loop hard real-time. It also matches the repo's own docs: the Pi converts goals into short-lived intents, while the Brain validates commands, applies limits, and stops on expiry [S1][S6].

Do not give Codex raw motor, raw serial, or raw camera-loop tools. The eventual MCP server should expose only world and skill operations: status, observe, align, approach, acquire, place, recover, stop.

### 2. Do Not Create A Parallel Workspace In The Repo

The pasted `vex_agent_ws/src/...` package list is a good mental model, but it should not become a second repo layout. The current pattern is `~/ros2_ws` on the Pi with this repo's `robot/ros2-runtime` symlinked into the workspace [S3].

Recommended repo shape:

- Keep `robot/ros2-runtime` as the bringup package and launch surface.
- Add only the minimum extra ROS packages when needed. A custom `vexy_interfaces` package is justified when actions/messages land; do not split every node into its own package before the first proof.
- Keep canonical schema definitions in `contracts`; ROS messages/actions are transport bindings, not the source of truth.

### 3. Camera Setup Is Mostly Right, But Needs Rectification And Calibration

`camera_ros` is the right boundary on Ubuntu 24.04 + Jazzy. It supports Raspberry Pi cameras via libcamera, and its docs explicitly warn that full Raspberry Pi module support on Ubuntu may require manually building the Raspberry Pi libcamera fork [S11]. That matches the existing `setup_pi.sh`/architecture direction.

Two important corrections:

- `apriltag_ros` subscribes to rectified `image_rect` plus `camera_info`, not just arbitrary raw camera frames [S12]. Add `image_proc`/rectification and publish `/camera/image_rect` before trusting tag pose.
- The current launch passes a camera `fps` parameter, but current `camera_ros` docs say framerate is set through `FrameDurationLimits` if the camera exposes that control [S11]. Keep `camera_fps` as a launch argument if desired, but translate it to the actual camera control or verify the installed version supports `fps`.

The first camera gate should require a real calibration YAML, nonzero `CameraInfo`, stable timestamps, and locked/known exposure/focus settings. The Camera Module 3 Wide distortion makes this a correctness gate, not polish.

### 4. The ROS VEX Bridge Needs The Old Reader Pattern Before More Autonomy

Current `vex_bridge_node.py` writes a packet and then reads one serial line synchronously [S5]. That is fragile once the Brain is streaming telemetry, because telemetry and ack packets share one serial stream [S7]. The older `robot/pi-runtime` bridge already solved this with a reader thread, an ack map keyed by sequence number, and separate telemetry logging [S7].

Required ROS bridge changes:

- Port the reader-thread/ack-condition pattern into `vex_bridge_node`.
- Publish acks and telemetry separately, for example `/vex/ack` and `/vex/telemetry_json`, then add typed topics.
- Support the existing Brain commands `arm` and `home`, not only `stop`, `drive`, `turn`, and `set_goal` [S5][S8].
- Keep Brain-side clamps/watchdog as the final authority even if a future safety monitor also vetoes commands.

### 5. Keep JSON V1 Until The First ROS Proof Is Stable

The pasted plan says to use binary packets with CRC instead of newline JSON. That is a good protocol-v2 direction, but it should not be the next migration step. The current Brain firmware, docs, and Python bridge all speak JSON v1 [S7][S8].

Ideal sequencing:

1. Keep JSON v1 for camera, AprilTag, bridge, bag, and `AlignToTag`.
2. Write a `contracts` protocol-v2 spec for binary framing, CRC, message types, and fault semantics.
3. Switch to binary only after ROS bridge parity and first closed-loop proof, or earlier only if serial corruption becomes a real observed blocker.

### 6. MCAP Is The Raw Evidence Store, Not The Contract

The pasted plan is right to use rosbag2/MCAP from day one; MCAP supports direct ROS 2 recording and Foxglove playback/visualization [S13]. But the self-model loop still needs contract-shaped observations. In this repo, `contracts` owns the Task Telemetry Contract and `operator` consumes gap residuals [S2].

So the durable path is:

`rosbag2/MCAP raw episode -> extractor -> contract-valid session JSONL -> operator gap analysis -> revised self-model`

Do not replace the contract with "whatever was in the bag." The bag is the replayable evidence surface; the exported JSONL is the semantic contract.

## Recommended Target Architecture

```text
Codex / future MCP tools
  -> robot_mcp_server
  -> ROS services/actions
  -> world_model + skill_executor + safety_monitor
  -> typed ROS command topics / services
  -> vex_bridge_node
  -> JSON v1 serial initially, binary v2 later
  -> PROS Brain bridge
  -> motors, watchdog, clamps, telemetry

Camera Module 3 Wide
  -> Raspberry Pi libcamera fork
  -> camera_ros
  -> camera_info + image_proc rectification
  -> apriltag_ros / object_detector
  -> tracker / state_estimator
  -> world_model
  -> skill_executor
```

This preserves the pasted plan's important architecture while fitting the repo's actual surfaces.

## What Needs To Change

### `contracts/`

- Treat `control-command` as the canonical command/ack/fault schema before custom ROS messages proliferate.
- Add/confirm schemas for world observations, skill events, detections/tracks, and MCAP-to-JSONL extraction outputs.
- Define protocol-v2 binary framing as a future schema, not an immediate firmware rewrite.

### `robot/ros2-runtime/`

- Fix camera launch semantics: use the Raspberry Pi libcamera fork, pass `camera_info_url`, produce `/camera/image_rect`, and verify framerate configuration against installed `camera_ros`.
- Add `image_proc` and `apriltag_ros` launch wiring before object detection.
- Replace synchronous serial reads with the `pi-runtime` reader-thread pattern.
- Split `/vex/telemetry` into ack, raw telemetry, and typed state topics.
- Add support for the Brain's existing `arm` and `home` commands.
- Add rosbag profiles for minimal proof topics and full evidence topics.
- Add `AlignToTag` as the first action once tag pose and VEX heartbeat are green.

### `robot/pi-runtime/`

- Keep it as the Bookworm/picamera2 fallback until the Jazzy path demonstrates camera, serial, telemetry logging, and one closed-loop motion proof.
- Avoid letting new ROS work silently diverge from the proven JSON protocol and Brain command vocabulary.

### `robot/v5-brain/`

- Preserve the current watchdog, TTL, clamps, and stop behavior.
- Improve parser robustness when practical, but avoid binary protocol churn until ROS bridge parity is done.
- Continue publishing actuator telemetry at the Brain layer; the Pi can enrich it, but should not invent motor truth.

### `pilot` / MCP

- Build the MCP server last, after ROS services/actions exist.
- Expose only high-level tools: status, observe, align, approach, acquire, place, recover, stop.
- Never expose `set_motor_power`, raw serial writes, raw camera streaming, or safety disablement.

## Bringup Order

1. **Fallback ready**: keep the known `robot/pi-runtime` SD/service path available.
2. **Jazzy base**: Ubuntu 24.04 + ROS 2 Jazzy + `noble-updates`/updated system packages; verify `ros2 pkg list`.
3. **Camera**: `camera_ros` publishes `/camera/image_raw` and nonzero `/camera/camera_info`; calibration YAML loaded.
4. **Rectification**: `image_proc` publishes `/camera/image_rect`; frame IDs and timestamps make sense.
5. **AprilTag**: `apriltag_ros` detects a printed tag and publishes stable pose/TF while the robot is still.
6. **VEX bridge no-motion**: heartbeat and stop ack through ROS; no assumptions from camera success.
7. **VEX bridge motion on blocks**: short `cmd_vel` nudge, TTL expiry, and Brain-side stop all visible in telemetry.
8. **AlignToTag action**: first closed-loop proof, with yaw/lateral error feedback and a stable success window.
9. **Object detector/tracker**: wrap the current YOLO26n NCNN path as a ROS node after tag alignment works.
10. **World model and MCP**: expose high-level tools only after world/skill state is stable.

## Recommendation

Proceed with Ubuntu 24.04 + ROS 2 Jazzy + Camera Module 3 as the long-term architecture, but treat it as a staged post-MVP migration unless the offline loop is already safe. The ideal immediate slice is not "build the full robot stack"; it is:

1. Fix/verify the camera launch and calibration path.
2. Port the robust serial reader pattern into `vex_bridge_node`.
3. Add AprilTag rectification/detection.
4. Implement `AlignToTag` as the first closed-loop ROS action.
5. Record the episode to MCAP and export a contract-valid JSONL observation.

Once that slice works, object approach, acquisition, placement, and Codex/MCP supervision become natural extensions instead of a pile of hopeful nodes.

## Suggested Next Steps

- Create an ai-sdd feature brief for: "ROS 2 AlignToTag vertical slice: calibrated camera -> apriltag_ros -> VEX bridge heartbeat/motion -> AlignToTag action -> MCAP + contract JSONL export."
- Run `/wiki-ingest raw/research/ros2-jazzy-supervisory-control-plan/index.md` to synthesize this into the knowledge base.
- Do not mark the robot control stack healthy until camera proof, serial proof, and motion proof are all separately current.
