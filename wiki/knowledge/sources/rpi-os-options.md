---
id: rpi-os-options
title: Research — RPi OS Options for the Capstone (+ Addendum)
updated: 2026-06-23
sources:
  - ../../raw/research/rpi-os-options/index.md
  - ../../raw/research/rpi-os-options/index-2.md
tags: [source, research, raspberry-pi, ros2, hardware, os, coprocessor]
---

# Research: RPi OS Options for the Capstone

Researched 2026-06-23. Two documents: `index.md` (initial four-option comparison) and `index-2.md` (addendum correcting the Ubuntu camera finding). Both are synthesized here.

relates_to::[[raspberry-pi-5]]
relates_to::[[pi-camera-module-3]]
relates_to::[[rpi-coprocessor-os-options]]
relates_to::[[ros2-jazzy]]
relates_to::[[hailo-ai-hat]]
relates_to::[[oak-d]]
relates_to::[[foxglove-studio]]

## Four Options Compared

Four OS/stack choices were evaluated for the Pi 5 coprocessor:

1. **Bookworm + PiCam2 + custom Python** — current state; lowest risk; ~8–10 FPS YOLO11n
2. **Ubuntu 24.04 + ROS 2 Jazzy + PiCam2** — best long-term architecture (no new hardware); camera path achievable via RPi libcamera fork
3. **Ubuntu 24.04 + ROS 2 Jazzy + OAK-D** — cleanest robotics architecture; stereo depth; requires OAK-D hardware ($79–$249)
4. **Trixie + Hailo AI HAT+** — Pi-native stack; 30+ FPS YOLO; requires AI HAT+ hardware ($70–$130)

## Key Findings

**F1 (corrected in addendum):** `picamera2` is officially Raspberry Pi OS–only. However, Camera Module 3 works on Ubuntu 24.04 + ROS 2 Jazzy via the **Raspberry Pi fork of libcamera** (not upstream). The guide `erykpawelek/libcamera_ros2_setup` (last commit Nov 2025, 0 open issues) explicitly targets Pi 5 + IMX708 + Ubuntu 24.04 + Jazzy. Build takes 15–30 min; **85–90% first-attempt success rate**. The original report called Option 2 "the worst of all worlds" — this was overstated.

**F2:** ROS 2 Jazzy + Ubuntu 24.04 installs cleanly with `ros-jazzy-ros-base` if the `noble-updates` apt repo is included (not just base `noble`). `rosserial_vex_v5` has **no Jazzy package** — the VEX V5 serial bridge is always a custom pyserial node.

**F3 (corrected):** ROS 2 Jazzy has concrete value for this capstone's architecture:
- `yolo_ros` (v4.6.1, 1.1k stars) — YOLOv11n as a lifecycle node, standard `DetectionArray` topics
- `apriltag_ros` (apt, official Jazzy) — camera-calibration-aware 6-DOF pose into TF2 (better accuracy than pure-Python `apriltag`)
- `foxglove_bridge` (apt) — real-time browser debugging of bounding boxes + poses; invaluable for headless Pi demos
- `ros2 bag` → `ros2 unbag` → JSON → Claude API — cleaner LLM self-model revision feedback loop than custom JSONL

**F4:** OAK-D connects via USB, bypassing libcamera entirely, making it the cleanest Ubuntu+ROS combination. `depthai-ros` on Jazzy currently requires building `depthai-core` from source (~$79–$249 hardware; 80–100 ms combined inference latency).

**F5:** **Hailo AI HAT+** (Hailo-8L, 13 TOPS) is fully supported on both Bookworm and Trixie (re-added to Trixie in fall 2025 after being missing at launch). Install: `sudo apt install dkms hailo-all`. Prices: 13 TOPS $70, 26 TOPS $110, AI HAT+ 2 (40 TOPS + 8 GB RAM) $130. Delivers 30+ FPS YOLOv8/v11 — 3× current throughput. **Lowest-risk post-showcase upgrade**: near-zero code change, no reflash needed.

**F6:** Trixie caution — ships Python 3.13, which causes compat issues (Open WebUI requires Docker; pip packages may need pins). Recommend Bookworm for Hailo to avoid Python 3.13 friction.

## Recommendation (post-addendum)

| When | Action |
|------|--------|
| Before Jun 29 | Stay on Bookworm. Demo the self-model loop. |
| Post-showcase — FPS bottleneck | Add Hailo AI HAT+ 13 TOPS ($70) on Bookworm |
| Post-showcase — platform architecture | Migrate to Ubuntu 24.04 + ROS 2 Jazzy + PiCam2 (libcamera fork build, then port 3 Python modules to ROS nodes) |
| Eventually | Ubuntu 24.04 + ROS 2 Jazzy + OAK-D for stereo depth |

Migration timeline for Ubuntu + Jazzy: ~6–12 hours focused work (flash + Jazzy + libcamera build + 3 ROS nodes + integration test). Do on a spare SD card with Bookworm as fallback.
