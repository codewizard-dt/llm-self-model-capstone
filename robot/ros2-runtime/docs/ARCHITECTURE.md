# Architecture — vexy_ros ROS 2 Jazzy Coprocessor Stack

## Overview

The robot is a VEX V5 Clawbot augmented with a Raspberry Pi 5 AI coprocessor. The Pi runs a ROS 2 Jazzy stack (`vexy_ros`) that handles computer vision, session recording, and the LLM self-model feedback loop. The V5 Brain retains exclusive authority over actuators via a deterministic PROS C++/FreeRTOS program.

## Migration Rationale — pi-runtime → ros2-runtime

The original `robot/pi-runtime` was written in Python against Bookworm/picamera2 with a custom asyncio serial bridge. It was replaced because three capabilities were needed that the Bookworm stack could not cleanly provide:

| Capability | pi-runtime (Bookworm) | ros2-runtime (Ubuntu 24.04 + Jazzy) |
|---|---|---|
| Session recording for LLM | Manual JSONL writes | `ros2 bag record -a` — single command captures everything |
| AprilTag localization | Hand-rolled, no calibration model | `apriltag_ros` consumes `/camera/camera_info` natively |
| Headless visualization | SSH + custom scripts | `foxglove_bridge` → browser UI, zero local display needed |

The wire protocol to the V5 Brain is intentionally unchanged (protocol version 1, newline-delimited JSON). The ROS bridge uses a continuous reader thread so Brain acknowledgements, streaming telemetry, and bridge faults are demultiplexed before any motion proof is interpreted.

## Two-Computer Model

```
┌─────────────────────────────────────┐     USB-A ↔ USB-C      ┌─────────────────────────┐
│         Raspberry Pi 5              │ ←─────────────────────→ │      VEX V5 Brain        │
│         Ubuntu 24.04 LTS            │    V5 user serial        │   PROS C++ / FreeRTOS    │
│         ROS 2 Jazzy                 │    115200 baud           │                          │
│                                     │    newline-delimited JSON│  Motor controllers       │
│  ┌─────────────┐  ┌──────────────┐  │                          │  IMU / sensors           │
│  │ camera_node │  │ vex_bridge   │  │                          │  Battery monitor         │
│  │ (camera_ros)│  │ (vexy_ros)   │  │                          │  Watchdog timer          │
│  └─────────────┘  └──────────────┘  │                          └─────────────────────────┘
│         │                │          │
│  /camera/image_raw   /vex/cmd       │
│  /camera/camera_info /vex/ack       │
│                      /vex/telemetry │
│                      /vex/bridge_status │
│         │                │          │
│  ┌──────┴────────────────┴────────┐ │
│  │       ROS 2 topic graph        │ │
│  └────────────────────────────────┘ │
│              │                      │
│   ros2 bag record -a                │
│              │                      │
│   ┌──────────▼──────────────┐       │
│   │  .bag → JSON → Claude   │       │  ← LLM self-model loop
│   │  API (feedback loop)    │       │
│   └─────────────────────────┘       │
└─────────────────────────────────────┘
         ↑ Camera Module 3 (IMX708)
```

## Camera Stack

```
IMX708 sensor
    │
    ▼
RPi libcamera fork          ← github.com/raspberrypi/libcamera
    │                         (upstream libcamera lacks the IMX708 driver)
    ▼
camera_ros (camera_node)    ← github.com/christianrauch/camera_ros
    │                         wraps libcamera; exposes standard ROS 2 topics
    ├─▶ /camera/image_raw       (sensor_msgs/Image,      15–30 Hz)
    └─▶ /camera/camera_info     (sensor_msgs/CameraInfo, 15–30 Hz)
          │
          ▼
image_proc rectify_node
    └─▶ /camera/image_rect      (sensor_msgs/Image,      15–30 Hz)
          │
          ▼
apriltag_ros apriltag_node
    ├─▶ /apriltag/detections    (apriltag_msgs/AprilTagDetectionArray)
    └─▶ /tf                     (tf2_msgs/TFMessage)
          │
          ▼
vexy_ros scene_map_node
    └─▶ /vision/scene_map       (std_msgs/String JSON map coordinates)
```

The RPi libcamera fork is built from source inside the colcon workspace (`~/ros2_ws`) rather than installed via apt. This is required because the apt package (`libcamera0`) ships the upstream version, which does not include the IMX708 pipeline handler needed for Camera Module 3. `camera_ros` loads calibration through `camera_info_url`; the launch file sets libcamera frame timing with `FrameDurationLimits` because frame rate is exposed as a duration control rather than a direct `fps` parameter.

## VEX Serial Bridge

```
/vex/cmd (std_msgs/String)
    │  JSON command packet
    ▼
vex_bridge_node
    │  validates + clamps velocities
    │  assigns seq number
    │  writes to serial @ 115200 baud
    ▼
auto-detected V5 user serial ──USB──▶ V5 Brain
    ◀──────────────── newline-delimited JSON
    │
    ▼
/vex/ack (std_msgs/String)
/vex/telemetry (std_msgs/String)
/vex/bridge_status (std_msgs/String)
```

### Protocol v1 — Outbound Commands

All packets are compact JSON terminated with `\n`. Fields common to every packet:

| Field | Type | Description |
|---|---|---|
| `v` | int | Protocol version — always `1` |
| `seq` | int | Monotonically increasing sequence counter |
| `type` | string | `"cmd"` or `"heartbeat"` |
| `sent_ms` | int | `time.monotonic()` in ms at send time |
| `ttl_ms` | int | Brain discards packet if not acted on within this window (1–5000) |

Command-specific fields (`type == "cmd"`):

| `cmd` | Extra fields |
|---|---|
| `stop` | — |
| `drive` | `vx` (m/s, ±0.35), `vy` (m/s, ±0.35), `omega` (rad/s, ±0.60) |
| `turn` | `omega` (rad/s, ±0.60) |
| `set_goal` | `goal` (string) |
| `heartbeat` | — (can also use `type == "heartbeat"` directly) |

### Protocol v1 — Inbound Acks

```json
{"v":1,"ack":1,"type":"ack","state":"ok","recv_ms":124,"battery_mv":12300,"heading_deg":0.0,"fault":null}
```

Ack records are published on `/vex/ack`, keyed by the `ack` sequence. Telemetry/sample/event records are published on `/vex/telemetry`. Malformed JSON, unsupported protocol versions, missing acks, stale telemetry, and serial disconnects are published on `/vex/bridge_status`.

### Heartbeat

`vex_bridge_node` fires a heartbeat automatically every 150 ms when no command has been sent. This keeps the V5 Brain's watchdog alive and prevents an automatic motor stop.

## Full Topic Graph

| Topic | Message Type | Publisher | Subscriber | Rate |
|---|---|---|---|---|
| `/camera/image_raw` | `sensor_msgs/Image` | `camera` | — (bag, apriltag, yolo) | 15 Hz (default) |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | `camera` | — (bag, apriltag) | 15 Hz (default) |
| `/camera/image_rect` | `sensor_msgs/Image` | `camera_rectify` | `apriltag`, `yolo_ncnn` | 15 Hz (default) |
| `/apriltag/detections` | `apriltag_msgs/AprilTagDetectionArray` | `apriltag` | — (bag, controller) | tag dependent |
| `/tf` | `tf2_msgs/TFMessage` | `apriltag` | — (bag, Foxglove) | tag dependent |
| `/vision/object_detections` | `std_msgs/String` | `yolo_ncnn`, `yellow_ball_detector` | `object_indication` | model/color dependent |
| `/vision/object_indications` | `std_msgs/String` | operator / `object_indication` | `scene_map` | on-demand |
| `/vision/scene_map` | `std_msgs/String` | `scene_map` | `task_plan`, bag, operator | tag dependent |
| `/task_plan/request` | `std_msgs/String` | operator / online loop | `task_plan` | on-demand |
| `/task_plan/current` | `std_msgs/String` | `task_plan` | bag, operator | on-demand |
| `/align_to_tag/goal` | `std_msgs/String` | operator / controller | `align_to_tag` | on-demand |
| `/align_to_tag/cancel` | `std_msgs/String` | operator / controller | `align_to_tag` | on-demand |
| `/align_to_tag/feedback` | `std_msgs/String` | `align_to_tag` | — (bag, Foxglove) | control-period dependent |
| `/align_to_tag/result` | `std_msgs/String` | `align_to_tag` | — (bag, Foxglove) | terminal |
| `/vex/cmd` | `std_msgs/String` | external / LLM loop | `vex_bridge` | on-demand |
| `/vex/ack` | `std_msgs/String` | `vex_bridge` | — (bag, controller) | heartbeat/cmd dependent |
| `/vex/telemetry` | `std_msgs/String` | `vex_bridge` | — (bag) | Brain sample dependent |
| `/vex/bridge_status` | `std_msgs/String` | `vex_bridge` | — (bag, controller) | fault/status dependent |

## LLM Self-Model Feedback Loop

```
┌──────────────┐     ros2 bag record -a     ┌──────────────┐
│  Robot runs  │ ─────────────────────────▶ │  .bag file   │
│  task        │                            └──────┬───────┘
└──────────────┘                                   │
                                           ros2 bag convert
                                                   │ (or custom extractor)
                                                   ▼
                                            JSON payload
                                                   │
                                           Claude API call
                                                   │
                                                   ▼
                                       ┌───────────────────────┐
                                       │  Revised self-model    │
                                       │  → new predictions     │
                                       │  → next task contract  │
                                       └───────────────────────┘
```

The bag captures all topics simultaneously — camera frames, VEX telemetry, any additional sensor topics — providing a complete, time-synchronized ground truth for the LLM to compare against the robot's prior predictions.

## Vision Extensions

### apriltag_ros — Workspace Localization

`apriltag_ros` subscribes to `/camera/image_rect` and `/camera/camera_info` and publishes calibration-aware 6-DOF tag poses. Tag-pose proof is only valid once `/camera/camera_info` contains nonzero measured calibration values.

```
/camera/image_raw  ──▶  image_proc  ──▶  /camera/image_rect  ──▶  apriltag_ros  ──▶  /apriltag/detections
/camera/camera_info ──▶
                                                                     └──────▶  /tf
```

### SceneMap — Workspace Coordinates

`scene_map` consumes `/tf` tag transforms and the active workspace JSON map,
then publishes `/vision/scene_map`. `/apriltag/detections` is still recorded as
the detector activity/ID stream. The default map is
`config/maps/table-grab-toss-v1.json`, which follows the wiki reference in
`wiki/knowledge/concepts/apriltag-workspace-layout.md` and
`wiki/knowledge/sources/apriltag-larger-workspace-map.md`: a 150 cm x 200 cm
floor arena, 200 mm `tag36h11` tags, tag `0` at the bin, tag `1` at ball
staging, and tag `2` at home. The published JSON carries ROS-friendly
meter/radian values and wiki-friendly `x_mm`, `y_mm`, `heading_deg` values.

The node also accepts `/vision/object_indications` for operator- or
detector-provided untagged object hints in camera-relative coordinates. YOLO
NCNN boxes are projected into that same surface by `object_indication`, keeping
object coordinates in one scene-map contract.

The `camera_in_robot_json` launch argument records the measured PiCam2 mount
offset in the robot body frame, so the node can publish robot-center
coordinates instead of only camera coordinates.

### AlignToTag — Bounded Local Control

`align_to_tag` is the first local-control skill. It consumes `/apriltag/detections`, `/vex/ack`, and `/vex/bridge_status`; publishes bounded fixed-grammar `/vex/cmd` packets; and emits JSON feedback/result topics. It sends a final `stop` command on success, cancel, timeout, stale tag, stale ack, or bridge fault. No LLM or API call is in this loop.

### YOLO NCNN and TaskPlan

`yolo_ncnn` is an optional in-package node. It subscribes to
`/camera/image_rect`, loads NCNN `.param`/`.bin` model exports directly with the
lightweight Python `ncnn` runtime, and publishes `/vision/object_detections`
JSON. `object_indication` uses calibrated CameraInfo plus per-class dimensions
to estimate camera-relative object positions, then publishes
`/vision/object_indications` for `scene_map`.

`task_plan` consumes `/vision/scene_map` and `/task_plan/request`. Requests use
targets such as `tag:0` or `object:bin`. Tag plans can dispatch to the proven
`align_to_tag` primitive when `dispatch:true`; object plans are mapped but
non-dispatchable until a bounded object/go-to-pose controller is implemented
and proven with MCAP plus `/vex/ack` and `/vex/telemetry`.

The yellow ball is supported as `object:yellow_ball` through a lightweight HSV
detector, plus the same label can be emitted by a future NCNN model.

## Package Layout

```
robot/ros2-runtime/
├── CLAUDE.md (this file's sibling)
├── README.md
├── package.xml
├── setup.py / setup.cfg
├── config/
│   ├── apriltag_36h11.yaml
│   ├── imx708_wide_640x480.yaml
│   └── maps/table-grab-toss-v1.json
├── launch/
│   └── vexy.launch.py          ← main entry point
├── scripts/
│   └── setup_pi.sh             ← one-time Pi setup (builds libcamera fork)
├── src/vexy_ros/
│   ├── scene_map_node.py       ← AprilTag map-coordinate publisher
│   ├── vision_map.py           ← pure map geometry helpers
│   ├── evidence_export.py      ← proof bundle → ContractLine JSONL
│   └── vex_bridge_node.py      ← USB serial ↔ ROS 2 bridge
└── docs/
    ├── ARCHITECTURE.md         ← this file
    └── USAGE_GUIDE.md
```
