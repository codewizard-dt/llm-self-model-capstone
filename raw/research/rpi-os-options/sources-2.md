---
topic: "RPi OS options — addendum sources (camera path confirmed)"
slug: rpi-os-options
researched: 2026-06-23
prior: [./sources.md]
---

# Primary Sources — RPi OS Options Addendum

Builds on [sources.md](sources.md). S1–S20 are in the prior file; this file adds S21–S28.

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S21 | web | https://github.com/erykpawelek/libcamera_ros2_setup | 2026-06-23 | Exact build guide for Pi 5 + Camera Module 3 + Ubuntu 24.04 + ROS 2 Jazzy; last commit Nov 2025; 0 open issues; confirms build in 5–15 min; single fix is using RPi libcamera fork instead of upstream |
| S22 | web | https://github.com/mgonzs13/yolo_ros | 2026-06-23 | `yolo_ros` v4.6.1, Jazzy-ready, YOLOv11 native support, 1.1k stars; lifecycle node; uses ultralytics backend |
| S23 | web | https://docs.ros.org/en/jazzy/p/apriltag_ros/ | 2026-06-23 | `apriltag_ros` on Jazzy: apt-installable, camera-calibration-aware 6-DOF pose, outputs to TF2 |
| S24 | web | https://github.com/christianrauch/camera_ros | 2026-06-23 | `camera_ros` node (164 stars, updated 2026-06-22, v0.7.0); distro-agnostic; requires RPi libcamera fork for IMX708 on Ubuntu |
| S25 | web | https://github.com/PhantomCybernetics/picam_ros2 | 2026-06-23 | Fallback camera driver for ROS 2 on Pi 5 CSI camera; Docker-friendly; does not require building libcamera from source |
| S26 | web | https://github.com/ika-rwth-aachen/ros2_unbag | 2026-06-23 | `ros2 unbag`: exports ros2 bag recordings to CSV/JSON/images — enables `ros2 bag` → JSON → Claude API workflow |
| S27 | web | https://github.com/insite-gmbh/RosProsExample | 2026-06-23 | Working example of VEX V5 + ROS serial bridge via USB — confirms pyserial in a ROS node is the correct pattern; rosserial_vex_v5 is ROS1 only |
| S28 | web | https://discourse.openrobotics.org/t/installation-and-configuration-of-the-raspberry-pi-camera-on-a-ros-2-jazzy-raspberry-pi-5/45177 | 2026-06-23 | Open Robotics official discourse post linking ARLunan/Raspberry-Pi-Camera-ROS as the reference guide for V1/V2/V3 cameras on Ubuntu 24.04 + Jazzy + Pi 5 |

---

## Excerpts

### S21 — erykpawelek/libcamera_ros2_setup README
https://github.com/erykpawelek/libcamera_ros2_setup
> Repository topics: `camera-module-3`, `libcamera`, `raspberry-pi-5`, `ros2-jazzy`, `ubuntu-24-04`
> Explicitly confirmed: Camera Module 3 (IMX708) ✓, Pi 5 ✓, Ubuntu 24.04 ✓, ROS 2 Jazzy ✓

### S21 — Known failure mode from the same repo
> "no cameras available" → Cause: Upstream libcamera lacks RPi 5 + Camera Module 3 support. Solution: Use RPi fork explicitly (already included in this guide).

### S24 — camera_ros README
https://github.com/christianrauch/camera_ros
> "Option B: Using Raspberry Pi Fork (Full Camera Module 3 Support) - RECOMMENDED: `git clone https://github.com/raspberrypi/libcamera.git` [instead of upstream]"

### S26 — ros2_unbag README
https://github.com/ika-rwth-aachen/ros2_unbag
> "Exports to CSV, JSON, PCD, images. Pluggable processors for custom transformations."
