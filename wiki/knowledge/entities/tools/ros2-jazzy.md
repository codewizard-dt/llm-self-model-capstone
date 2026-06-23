---
id: ros2-jazzy
title: ROS 2 Jazzy Jalisco
aliases: [ROS 2 Jazzy, ROS2 Jazzy, Jazzy, ROS 2]
updated: 2026-06-23
sources:
  - ../../../raw/research/rpi-os-options/index.md
  - ../../../raw/research/rpi-os-options/index-2.md
tags: [tool, software, ros, robotics, middleware]
---

# ROS 2 Jazzy Jalisco

The current LTS release of ROS 2 (Robot Operating System 2). Jazzy targets **Ubuntu 24.04 LTS** and is supported until 2029. It is the canonical robotics middleware for multi-component pipelines, providing typed message passing, TF2 coordinate frames, lifecycle nodes, and tooling (ros2 bag, Foxglove).

relates_to::[[raspberry-pi-5]]
relates_to::[[pi-camera-module-3]]
relates_to::[[foxglove-studio]]
relates_to::[[oak-d]]
relates_to::[[vex-coprocessor-pattern]]
derived_from::[[rpi-os-options]]

## Install on Pi 5

Requires Ubuntu 24.04 LTS (not Raspberry Pi OS). Binary packages via apt:
```bash
sudo apt install ros-jazzy-ros-base
```
**Critical:** must use the `noble-updates` apt repo, not just base `noble` — Jazzy packages depend on library versions only in `noble-updates`.

## Camera Module 3 on Ubuntu + Jazzy

`picamera2` is officially Raspberry Pi OS–only. However, Camera Module 3 works on Ubuntu 24.04 + Jazzy by building the **Raspberry Pi fork of libcamera** (not upstream):
```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/raspberrypi/libcamera.git   # RPi fork — has IMX708 support
git clone https://github.com/christianrauch/camera_ros.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -y --skip-keys=libcamera
colcon build --packages-select libcamera camera_ros
source install/setup.bash
ros2 run camera_ros camera_node
# Publishes /camera/image_raw and /camera/camera_info
```
Build time: 15–30 min on Pi 5. **85–90% first-attempt success rate.** Guide: `github.com/erykpawelek/libcamera_ros2_setup` (last commit Nov 2025, 0 open issues).
Fallback: `picam_ros2` (PhantomCybernetics) — Docker-friendly alternative that doesn't require building libcamera.

## Key Packages for the Capstone

| Package | Install | Value |
|---------|---------|-------|
| `yolo_ros` (mgonzs13) | source build | YOLOv11n lifecycle node; publishes `DetectionArray` topics; v4.6.1, 1.1k stars |
| `apriltag_ros` | `apt install ros-jazzy-apriltag-ros` | Camera-calibration-aware 6-DOF pose; outputs to TF2 transform tree |
| `foxglove_bridge` | `apt install ros-jazzy-foxglove-bridge` | Real-time browser debug at `ws://mypi.local:8765` |
| `camera_ros` | workspace build (see above) | Camera Module 3 → `/camera/image_raw` |

## VEX V5 Serial Bridge

`rosserial_vex_v5` has **no Jazzy package** (no version for distro jazzy on index.ros.org). The VEX V5 serial bridge is always a thin custom pyserial node regardless of OS. Example pattern:
```python
import serial, json, rclpy
from rclpy.node import Node

class VEXInterface(Node):
    def __init__(self):
        super().__init__('vex_interface')
        self.ser = serial.Serial('/dev/ttyACM0', 115200)
        # subscribe/publish ROS topics, read/write JSON over serial
```

## ros2 bag + LLM Feedback Loop

`ros2 bag record -a -o mission_1` captures all topics with timestamps. Export via `ros2 unbag` → JSON → Claude API. This is a cleaner repeatable LLM self-model revision loop than custom JSONL construction.

## Migration Timeline

To migrate from Bookworm custom Python: ~6–12 hours focused work:
1. Flash Ubuntu 24.04 to second SD card (keep Bookworm as fallback)
2. Install Jazzy, build libcamera fork (~1.5–2.5 hr)
3. Port 3 Python modules → ROS nodes: camera/YOLO node, AprilTag node, VEX serial node (~2–4 hr)
4. Add `foxglove_bridge` + `ros2 bag record`, integration test (~1–2 hr)

Recommended: attempt post-Jun-29 showcase on a spare SD card.
