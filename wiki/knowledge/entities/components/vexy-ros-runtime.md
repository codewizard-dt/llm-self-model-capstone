---
id: vexy-ros-runtime
title: vexy_ros ROS 2 Runtime
aliases: [vexy_ros, ROS2 runtime, ROS 2 runtime, VEXY ROS runtime, robot/ros2-runtime]
updated: 2026-06-25
sources:
  - ../../../../robot/ros2-runtime/README.md
  - ../../../../robot/ros2-runtime/docs/ARCHITECTURE.md
  - ../../../../robot/ros2-runtime/docs/USAGE_GUIDE.md
  - ../../../../robot/ros2-runtime/launch/vexy.launch.py
  - ../../../../robot/ros2-runtime/setup.py
  - ../../sources/robot-apriltag-ball-delivery.md
tags: [component, ros2, jazzy, raspberry-pi, vex-v5, vision, serial, runtime]
---

# vexy_ros ROS 2 Runtime

`robot/ros2-runtime/` is the current Raspberry Pi 5 coprocessor runtime for the VEX V5 robot. It is an `ament_python` ROS 2 Jazzy package named `vexy_ros`, intended to replace the legacy Bookworm `robot/pi-runtime` path with an Ubuntu 24.04 + ROS 2 stack that can run camera vision, AprilTag mapping, bounded local skills, V5 serial control, Foxglove debug, and MCAP evidence capture.

runs_on::[[raspberry-pi-5]]
uses::[[ros2-jazzy]]
uses::[[pi-camera-module-3]]
uses::[[vex-coprocessor-pattern]]
uses::[[robot-workspace-map]]
uses::[[apriltag-workspace-layout]]
feeds::[[task-telemetry-contract]]
relates_to::[[foxglove-studio]]
relates_to::[[vex-v5]]

## Runtime Shape

The launched stack is a two-computer architecture:

| Side | Responsibility |
|---|---|
| Raspberry Pi 5 | Camera capture, image rectification, AprilTag detection, scene mapping, object detection/projection, local task dispatch, bounded local skills, session recording, Foxglove bridge, serial bridge |
| VEX V5 Brain | Deterministic actuator authority, motor safety, watchdog, command acknowledgements, telemetry samples |

The Pi talks to the Brain through newline-delimited JSON over the V5 user serial interface at 115200 baud. The serial bridge keeps command acknowledgements, telemetry samples, and bridge faults on separate ROS topics so "serial transport worked" is not confused with "the robot physically moved as intended."

## Launched Nodes

`ros2 launch vexy_ros vexy.launch.py` currently launches:

| Node | Package | Function |
|---|---|---|
| `camera` | `camera_ros` | Camera Module 3 via the Raspberry Pi libcamera fork; publishes `/camera/image_raw` and `/camera/camera_info` |
| `camera_rectify` | `image_proc` | Rectifies raw camera frames into `/camera/image_rect` using calibrated CameraInfo |
| `apriltag` | `apriltag_ros` | Detects tag36h11 AprilTags from rectified frames; publishes `/apriltag/detections` and `/tf` |
| `scene_map` | `vexy_ros` | Converts tag transforms and object indications into workspace-map coordinates on `/vision/scene_map` |
| `yolo_ncnn` | `vexy_ros` | Optional NCNN YOLO detector over rectified frames; disabled by default until a model path is supplied |
| `yellow_ball_detector` | `vexy_ros` | Default lightweight HSV detector for the `yellow_ball` object label |
| `object_indication` | `vexy_ros` | Projects 2D detections into camera-relative object indications using CameraInfo and class dimensions |
| `task_plan` | `vexy_ros` | Turns `tag:*`, `home:tag`, `object:*`, and `survey:all` requests into bounded plans |
| `align_to_tag` | `vexy_ros` | Bounded visible-tag alignment skill that publishes fixed-grammar `/vex/cmd` packets |
| `survey_scan` | `vexy_ros` | Bounded rotate-in-place survey skill for `survey:all` plans |
| `vex_bridge` | `vexy_ros` | USB serial bridge between `/vex/cmd` and Brain ack/telemetry/status streams |
| `foxglove_bridge` | `foxglove_bridge` | Browser debug bridge on port 8765 |

## Core Topics

| Topic | Shape | Meaning |
|---|---|---|
| `/camera/image_raw` | `sensor_msgs/Image` | Raw Camera Module 3 frames |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | Intrinsics/calibration loaded from `camera_info_url` |
| `/camera/image_rect` | `sensor_msgs/Image` | Rectified image stream for tags and object detectors |
| `/apriltag/detections` | `apriltag_msgs/AprilTagDetectionArray` | Tag IDs and image-space detections |
| `/tf` | `tf2_msgs/TFMessage` | Tag pose transforms from `apriltag_ros` |
| `/vision/object_detections` | `std_msgs/String` JSON | YOLO or color-detector boxes |
| `/vision/object_indications` | `std_msgs/String` JSON | Camera-relative object coordinate hints |
| `/vision/scene_map` | `std_msgs/String` JSON | Robot, tag, and object coordinates in the active workspace map |
| `/task_plan/request` | `std_msgs/String` JSON | Operator/online-loop target request |
| `/task_plan/current` | `std_msgs/String` JSON | Current bounded plan and dispatchability state |
| `/align_to_tag/*` | `std_msgs/String` JSON | Goal, cancel, feedback, and result channels for tag alignment |
| `/survey/*` | `std_msgs/String` JSON | Goal, cancel, feedback, and result channels for survey scan |
| `/vex/cmd` | `std_msgs/String` JSON | Fixed grammar commands to the Brain |
| `/vex/ack` | `std_msgs/String` JSON | Brain acknowledgements keyed by command sequence |
| `/vex/telemetry` | `std_msgs/String` JSON | Brain telemetry, motor samples, and events |
| `/vex/bridge_status` | `std_msgs/String` JSON | Bridge health, serial faults, malformed packets, missing acks |

## Implemented Behaviors

### Camera and AprilTag Localization

The camera path is Camera Module 3 -> Raspberry Pi libcamera fork -> `camera_ros` -> `image_proc` -> `apriltag_ros`. The launch file requires `camera_info_url` to be a URL, not a plain path, because rectification and tag-pose proof depend on camera calibration data. The checked-in calibration file is a starter config; physical tag-pose proof still depends on measured calibration.

`scene_map` consumes tag transforms and a JSON workspace map. The default map is `table-grab-toss-v1`; `VEXY_MAP=gen0-grab-toss-v1` selects the current Gen 0 arena map. The map output includes ROS-friendly meter/radian values and wiki-friendly millimeter/degree values.

### Object Detection and Mapping

Two object-detection paths feed the same `/vision/object_detections` topic:

- `yellow_ball_detector` runs by default and uses HSV/circularity thresholds for the `yellow_ball` label.
- `yolo_ncnn` is optional and disabled by default; it requires an NCNN `.param`/`.bin` export and a model path.

`object_indication` projects detections into camera-relative object hints using CameraInfo and configured class dimensions. `scene_map` then transforms those hints into workspace coordinates. These coordinates are estimates; precise object localization still needs a tag, measurement, or a proven object controller.

### Task Planning and Local Skills

`task_plan` accepts target requests such as `tag:0`, `home:tag`, `object:yellow_ball`, `object:bin`, and `survey:all`.

Tag and home plans can dispatch to `align_to_tag`, which refuses to start without a fresh visible tag and current VEX ack, clamps command bounds, and sends `stop` on success, cancel, timeout, stale tag, stale ack, or bridge fault.

Survey plans can dispatch to `survey_scan`, which refuses to start without fresh `/vex/ack`, fresh `/vex/telemetry`, motion enabled, no estop, and healthy drive ports. It rotates in place, reports observed tags, and stops on cancel, stale inputs, bridge fault, or safety telemetry.

Object plans are mapped but intentionally not motion-dispatchable yet. They report that an object go-to-pose controller is not proven.

### VEX Serial Bridge

`vex_bridge_node` subscribes to `/vex/cmd`, validates/clamps packets, assigns sequence numbers, writes compact JSON to the Brain, and demultiplexes inbound lines into:

- `/vex/ack` for command acknowledgements.
- `/vex/telemetry` for motor samples and event records.
- `/vex/bridge_status` for bridge state and faults.

The protocol version is `v: 1`. Supported command values include `stop`, `drive`, `turn`, `set_goal`, and the current release command path used by the proof/delivery utilities. Linear velocity is clamped to +/-0.35 m/s, angular velocity to +/-0.6 rad/s, and `ttl_ms` to 1-5000 ms. The bridge sends automatic heartbeats every 150 ms when no command has arrived.

## `/vex/cmd` Command Reference

All commands are JSON objects carried inside `std_msgs/String.data` on `/vex/cmd`. The serial bridge normalizes them, serializes compact newline-delimited JSON, and sends them to the Brain.

Common fields:

| Field | Required | Meaning |
|---|---:|---|
| `v` | yes | Protocol version; currently `1` |
| `seq` | yes | Integer sequence number used to match Brain acks |
| `type` | yes | Usually `"cmd"`; `"heartbeat"` is reserved for bridge-generated keepalive packets |
| `cmd` | yes for `type:"cmd"` | One of `stop`, `drive`, `turn`, `set_goal`, `release` |
| `sent_ms` | recommended | Pi-side monotonic timestamp in ms |
| `ttl_ms` | recommended | Command freshness/lifetime; Pi clamps to 1-5000 ms |
| `reason` | optional | Human-readable proof/debug reason; used by stop/proof utilities |

The Brain emits an ack for every valid packet with an integer `seq`. Rejections appear as `/vex/ack` records with `state:"rejected"` and a `fault` reason.

### `stop`

Stops the drivetrain immediately and clears the active motion TTL.

```json
{"v":1,"seq":1,"type":"cmd","cmd":"stop","sent_ms":123,"ttl_ms":200,"reason":"operator_stop"}
```

If the packet text contains `operator_estop`, the Brain latches estop. After that, `drive`, `turn`, and `release` are rejected with `estop_latched` until the Brain program is restarted or the latch behavior is changed.

### `drive`

Commands differential-drive motion using forward velocity plus yaw rate.

```json
{"v":1,"seq":2,"type":"cmd","cmd":"drive","sent_ms":123,"ttl_ms":180,"vx":0.14,"vy":0.0,"omega":0.20}
```

Operation:

- Pi-side protocol accepts `vx`, `vy`, and `omega`; it clamps `vx`/`vy` to +/-0.35 m/s and `omega` to +/-0.6 rad/s.
- The current Brain firmware uses only `vx` and `omega`. `vy` is ignored because the Clawbot drivetrain is differential-drive.
- The Brain further clamps executed `vx` to +/-0.18 m/s and `omega` to +/-0.6 rad/s.
- The Brain converts `vx` and `omega` into left/right motor RPM using a 4 in wheel circumference and 0.28 m track width.
- The command is rejected when estop is latched or the expected drive motor ports are missing.

The Brain stops when the motion TTL expires, the watchdog expires, or a later `stop`/`release`/invalid safety condition stops the drivetrain.

### `turn`

Commands an in-place rotation. It is equivalent to `drive` with `vx` forced to `0.0` by the Brain.

```json
{"v":1,"seq":3,"type":"cmd","cmd":"turn","sent_ms":123,"ttl_ms":180,"omega":0.35}
```

Operation:

- Pi-side protocol clamps `omega` to +/-0.6 rad/s.
- The Brain clamps `omega` to +/-0.6 rad/s and uses the lower turn-only RPM limit.
- The command is rejected when estop is latched or drive ports are missing.

`survey_scan` and tag-reacquisition proof routines use this command for bounded rotate-in-place scans.

### `set_goal`

Accepted by the Pi-side protocol for compatibility with higher-level planning messages, but not implemented as Brain behavior.

```json
{"v":1,"seq":4,"type":"cmd","cmd":"set_goal","sent_ms":123,"ttl_ms":200,"goal":"collect_cube"}
```

Current Brain behavior:

- Stops the drivetrain.
- Acks with `state:"rejected"` and `fault:"unsupported_goal"`.

Use `/task_plan/request` for ROS-side goals. `set_goal` should not be treated as a motion command.

### `release`

Runs the release motor for a bounded duration. This is used by `vexy_deliver_ball` after the robot reaches the bin tag.

```json
{"v":1,"seq":5,"type":"cmd","cmd":"release","sent_ms":123,"ttl_ms":200,"duration_ms":650,"reason":"drop_ball_in_bin"}
```

Operation:

- Pi-side protocol defaults `duration_ms` to 650 ms and clamps it to 1-1500 ms.
- The Brain stops the drivetrain before starting release motion.
- The Brain runs the release motor at 100 RPM, delays for the clamped duration, then brakes the release motor.
- The command is rejected when estop is latched or the release motor port is missing.

### `heartbeat`

Heartbeat packets use `type:"heartbeat"` rather than `type:"cmd"`. Controllers do not need to publish them directly; `vex_bridge_node` sends one every 150 ms when no command has arrived.

```json
{"v":1,"seq":6,"type":"heartbeat","sent_ms":123,"ttl_ms":200}
```

Operation:

- Updates the Brain's last-packet timestamp.
- Produces an `ok` ack.
- Does not move motors.
- Prevents the Brain watchdog from stopping motion solely because the command stream is idle.

### Safety Envelope

The current Pi and Brain clamps are intentionally conservative but not identical:

| Limit | Pi-side protocol | Brain execution |
|---|---:|---:|
| `vx` | +/-0.35 m/s | +/-0.18 m/s |
| `vy` | +/-0.35 m/s | ignored |
| `omega` | +/-0.6 rad/s | +/-0.6 rad/s |
| command `ttl_ms` | 1-5000 ms | drive/turn motion TTL clamped to 20-500 ms |
| `release.duration_ms` | 1-1500 ms | 1-1500 ms |
| idle watchdog | bridge sends heartbeat every 150 ms | Brain stops drivetrain after 250 ms without a valid packet |

For proof runs, task success must be judged from `/vex/ack`, `/vex/telemetry`, and the relevant vision/result topics together. A command ack alone only proves that the Brain parsed and accepted the packet.

### Evidence and Proof Utilities

The package installs runtime nodes plus utility commands:

| Command | Purpose |
|---|---|
| `vexy_export_contract_jsonl` | Convert proof bundles into contract-valid JSONL, validating against `contracts.ContractLine` when available |
| `vexy_tag_action_proof` | Run/summarize tag-action proof routines |
| `vexy_run_calibrated_tag_proof` | Record MCAP, run tag-action proof, write summary, and export contract JSONL |
| `vexy_scene_observation_proof` | No-motion proof for current detections, scene map, object plans, and survey plans |
| `vexy_calibrate_camera` | Checkerboard calibration capture helper |
| `vexy_deliver_ball` | Current delivery routine: scan, approach ball staging tag, approach bin tag, release |

The standard evidence path is `ros2 bag record` or proof-runner MCAP capture, followed by bundle summarization and JSONL export into the offline self-model loop.

## AprilTag Ball Delivery Routine

[Research: Robot AprilTag Ball Delivery](../../sources/robot-apriltag-ball-delivery.md) adds the current end-to-end delivery routine. `vexy_deliver_ball` scans the workspace, approaches the `ball_staging` AprilTag (`1`), approaches the `bin` AprilTag (`0`), then sends the bounded `release` command. **The routine deliberately reuses the existing `run_scan` and `approach_tag` proof helpers rather than introducing an unproven map-pose controller.**

The same source clarifies the bridge contract boundary: `set_goal` remains a ROS-side planning compatibility value and is rejected by the Brain, while physical ball release is a distinct `release` command with a clamped `duration_ms`. uses::[[robot-apriltag-ball-delivery]] uses::[[vex-coprocessor-pattern]]

## Verification Coverage

The runtime has focused unit coverage under `robot/ros2-runtime/tests/` for:

- serial demux, heartbeat bounds, missing-ack faults, bad JSON, unsupported protocol, release duration bounds
- tag alignment start/fail/stop behavior, stale input handling, cancellation, and command clamps
- survey scan start/fail/stop behavior, stale input handling, safety telemetry, cancellation, and goal clamps
- task plans for tag, home, survey, object, missing target, and bearing normalization
- scene-map geometry, workspace map parsing, object coordinate mapping, and pose JSON shape
- yellow-ball detection and OpenCV image encoding conversion
- object indication projection from detections and CameraInfo
- proof export, observation proof summaries, tag-action proof summaries, camera calibration YAML, and launch-file contract expectations

## Current Boundaries

- The ROS 2 runtime is the active coprocessor path, but it still depends on the V5 Brain-side PROS program for real actuator authority and safety.
- Object detection is implemented, but object-driven motion is not yet proven; object plans remain non-dispatchable.
- YOLO NCNN is available only when a model export and Python `ncnn` runtime are installed on the Pi.
- Camera pose proof requires measured calibration; the checked-in calibration is only a starter config.
- Hardware proof should use `/vex/ack` plus `/vex/telemetry`; an ack alone proves transport, not task success.
