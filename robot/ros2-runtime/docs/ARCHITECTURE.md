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
| `/camera/image_rect` | `sensor_msgs/Image` | `camera_rectify` | `apriltag` | 15 Hz (default) |
| `/apriltag/detections` | `apriltag_msgs/AprilTagDetectionArray` | `apriltag` | — (bag, controller) | tag dependent |
| `/tf` | `tf2_msgs/TFMessage` | `apriltag` | — (bag, Foxglove) | tag dependent |
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
```

### yolo_ros — Object Detection

`yolo_ros` (mgonzs13/yolo_ros) must be built from source; no apt package is available for Jazzy. It subscribes to `/camera/image_raw` and publishes detection arrays for game objects.

## Package Layout

```
robot/ros2-runtime/
├── CLAUDE.md (this file's sibling)
├── README.md
├── package.xml
├── setup.py / setup.cfg
├── config/
│   ├── apriltag_36h11.yaml
│   └── imx708_wide_640x480.yaml
├── launch/
│   └── vexy.launch.py          ← main entry point
├── scripts/
│   └── setup_pi.sh             ← one-time Pi setup (builds libcamera fork)
├── src/vexy_ros/
│   └── vex_bridge_node.py      ← USB serial ↔ ROS 2 bridge
└── docs/
    ├── ARCHITECTURE.md         ← this file
    └── USAGE_GUIDE.md
```
