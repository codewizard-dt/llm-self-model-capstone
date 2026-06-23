---
id: rpi-coprocessor-os-options
title: RPi Coprocessor OS Options
updated: 2026-06-23
sources:
  - ../../raw/research/rpi-os-options/index.md
  - ../../raw/research/rpi-os-options/index-2.md
tags: [concept, raspberry-pi, os, ros2, hailo, coprocessor]
---

# RPi Coprocessor OS Options

The four viable OS/stack configurations for the Pi 5 AI coprocessor, evaluated against the capstone's constraints (VEX V5 USB serial JSON bridge, Camera Module 3 CSI, YOLO11n + AprilTag, LLM feedback loop).

relates_to::[[raspberry-pi-5]]
relates_to::[[pi-camera-module-3]]
relates_to::[[ros2-jazzy]]
relates_to::[[hailo-ai-hat]]
relates_to::[[oak-d]]
relates_to::[[foxglove-studio]]
relates_to::[[vex-coprocessor-pattern]]
derived_from::[[rpi-os-options]]

## Decision Matrix

| | **Bookworm + PiCam2** | **Ubuntu 24.04 + Jazzy + PiCam2** | **Ubuntu 24.04 + Jazzy + OAK-D** | **Trixie + Hailo + PiCam2** |
|---|---|---|---|---|
| New hardware | No | No | $79–$249 OAK-D | $70–$130 AI HAT+ |
| Camera setup | Native | RPi libcamera fork build (15–30 min) | USB plug-in | Native |
| FPS | ~8–10 | ~8–10 | ~15–30 | **30+** |
| ROS 2 | No | Yes | Yes | No |
| LLM loop | Custom JSONL | `ros2 bag` → JSON | `ros2 bag` → JSON | Custom JSONL |
| Showcase risk | **None** | Medium | High | High |
| Long-term quality | Medium | **High** | Very High | Medium/High |

## Camera Module 3 on Ubuntu 24.04 — The Critical Clarification

`picamera2` is Raspberry Pi OS–only. However, Camera Module 3 works on Ubuntu 24.04 + ROS 2 Jazzy via the **Raspberry Pi fork of libcamera** — not upstream libcamera (which lacks IMX708 support). The fix is one `git clone` swap, with a documented guide (`erykpawelek/libcamera_ros2_setup`, Nov 2025, 0 open issues) and 85–90% first-attempt success. See relates_to::[[ros2-jazzy]] for the exact build commands.

## Upgrade Sequencing (post-Jun-29 showcase)

1. **FPS upgrade first**: Add Hailo AI HAT+ 13 TOPS ($70) to current Bookworm — `sudo apt install hailo-all`, picamera2 `hailo/detect.py` example, 30+ FPS immediately. No reflash.
2. **Platform upgrade later**: Migrate to Ubuntu 24.04 + ROS 2 Jazzy on a spare SD card. Build libcamera fork, port 3 Python modules → ROS nodes, add `foxglove_bridge` + `ros2 bag`. ~6–12 hours.
3. **Stereo depth eventually**: Replace PiCam2 with OAK-D for true 3D object localization and richer Task Telemetry Contract gap residuals.

## Invariant: VEX V5 Serial Bridge

Regardless of OS choice, the VEX V5 serial bridge is always a **custom pyserial node** — `rosserial_vex_v5` has no Jazzy package. The protocol (USB, `/dev/ttyACM0`, 115200 baud, newline-delimited JSON) is identical across all options.
