---
topic: "Reconcile the PiCam2 on Ubuntu 24.04 + ROS 2 Jazzy supervisory-control plan with the current Vexy codebase"
slug: ros2-jazzy-supervisory-control-plan
researched: 2026-06-23
---

# Primary Sources - ROS 2 Jazzy Supervisory Control Plan

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | user attachment | `/Users/kelly/.codex/attachments/22072cd2-30e3-41ad-868a-d74ad8b418b3/pasted-text.txt:1-620` | 2026-06-23 | The proposed supervisory architecture, node graph, safety split, ROS graph, logging plan, and recommendation that first proof be AprilTag alignment. |
| S2 | codebase | `MASTER_REQUIREMENTS.md:38-170` | 2026-06-23 | Authoritative project requirements: offline self-model loop, vertical ownership, schemas in `contracts`, `pilot` as online-control stretch, and milestone order. |
| S3 | codebase | `robot/ros2-runtime/docs/ARCHITECTURE.md:5-162` | 2026-06-23 | Current Jazzy runtime surface: camera_ros, VEX bridge, Foxglove, JSON wire protocol, rosbag feedback loop, and planned AprilTag/YOLO additions. |
| S4 | codebase | `robot/ros2-runtime/launch/vexy.launch.py:31-84` | 2026-06-23 | Current launch wiring for camera, VEX bridge, and Foxglove, including the `fps` launch parameter that needs verification against `camera_ros`. |
| S5 | codebase | `robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py:1-188` | 2026-06-23 | Current ROS serial bridge implementation: String topics, heartbeat timer, command validation, synchronous serial write/read, and supported commands. |
| S6 | codebase | `robot/pi-runtime/docs/ARCHITECTURE.md:5-44` | 2026-06-23 | Existing System 2/System 1 safety split and the one-camera-owner rule from the Bookworm runtime. |
| S7 | codebase | `robot/pi-runtime/src/vexy_system2/bridge.py:51-125` and `robot/pi-runtime/docs/PROTOCOL.md:71-87` | 2026-06-23 | Proven serial reader pattern that separates acks from telemetry, plus protocol rule that telemetry and acks share one serial stream. |
| S8 | codebase | `robot/v5-brain/pros_bridge/src/main.cpp:22-300` | 2026-06-23 | Brain-side safety and control behavior: watchdog, telemetry tick, clamps, stall checks, arm/home/drive/turn commands, and stop handling. |
| S9 | codebase | `robot/pi-runtime/docs/YOLO26N_NCNN.md:3-130` | 2026-06-23 | Current YOLO26n NCNN runtime path on `vexy`, including venv isolation, model artifacts, smoke-test timings, and camera ownership note. |
| S10 | codebase | `robot/pi-runtime/docs/evidence/vexy-log-bundle-20260622-111004/SUMMARY.md:1-30` | 2026-06-23 | Evidence split: camera service healthy while the V5 Brain was absent from the USB bus in that capture. |
| S11 | web | https://github.com/christianrauch/camera_ros | 2026-06-23 | `camera_ros` supports Raspberry Pi cameras through libcamera, may require Raspberry Pi libcamera fork on Ubuntu, publishes image/camera_info topics, loads camera calibration, and sets framerate through camera controls. |
| S12 | web | https://index.ros.org/r/apriltag_ros/ | 2026-06-23 | `apriltag_ros` detects AprilTags, publishes pose/id/metadata, and subscribes to rectified `image_rect` plus `camera_info`. |
| S13 | web | https://mcap.dev/guides/getting-started/ros-2 | 2026-06-23 | ROS 2 can record directly to MCAP with `rosbag2-storage-mcap`, and Foxglove can play ROS 2 MCAP bags. |
| S14 | web | https://github.com/ros2/ros2/releases | 2026-06-23 | ROS 2 Jazzy release notes list Debian packages for Ubuntu 24.04 Noble and caution that systems must be up to date for runtime dependencies. |

## Excerpts

### S1 - Pasted plan

> "Agent loop = slow supervisory loop"

> "Do AprilTag alignment before object pickup."

### S2 - Master requirements

> "contracts holds the frozen schemas every vertical imports"

> "m6 online-control"

### S3 - ROS 2 runtime architecture

> "The V5 Brain retains exclusive authority over actuators"

> "The wire protocol to the V5 Brain is intentionally unchanged"

### S4 - ROS launch

> `"fps": LaunchConfiguration("camera_fps")`

### S5 - ROS bridge

> "Published: /vex/telemetry (std_msgs/String)"

> `line = self._serial.readline()`

### S6 - Pi runtime architecture

> "The Pi should never be the only safety layer."

> "The Pi camera pipeline is exclusive."

### S7 - Pi runtime bridge and protocol

> "Telemetry lines share the same serial stream"

> `self.acks[int(packet["ack"])] = packet`

### S8 - PROS Brain bridge

> `constexpr uint32_t WATCHDOG_MS = 300;`

> `stop_all("watchdog");`

### S9 - YOLO26n NCNN docs

> "Prefer `YOLO(\"yolo26n_ncnn_model\")` for Pi runtime inference."

### S10 - Evidence bundle summary

> "the VEX V5 Brain is not present on the Pi USB bus."

### S11 - camera_ros

https://github.com/christianrauch/camera_ros

> "supports V4L2 and Raspberry Pi cameras"

> "build the \"raspberrypi\" fork"

> "`~/camera_info` `sensor_msgs/msg/CameraInfo`"

### S12 - apriltag_ros

https://index.ros.org/r/apriltag_ros/

> "detect AprilTags in images and publish their pose"

> "`image_rect` (`raw`, type: `sensor_msgs/msg/Image`)"

### S13 - MCAP ROS 2 guide

https://mcap.dev/guides/getting-started/ros-2

> "ROS 2 supports recording directly to MCAP"

> "Foxglove supports playing back local and remote ROS 2"

### S14 - ROS 2 releases

https://github.com/ros2/ros2/releases

> "Debian packages for Ubuntu 24.04 (Noble)."

> "Your system must be up-to-date"
