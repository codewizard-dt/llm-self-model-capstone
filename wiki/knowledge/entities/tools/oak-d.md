---
id: oak-d
title: Luxonis OAK-D
aliases: [OAK-D, OAK-D-S2, OAK-D-Lite, DepthAI, Luxonis]
updated: 2026-06-23
sources:
  - ../../../raw/research/rpi-os-options/index.md
tags: [tool, hardware, camera, depth, robotics, vision]
---

# Luxonis OAK-D

A spatial AI camera from Luxonis combining stereo depth perception, an Intel Myriad X VPU (4 TOPS onboard), and an RGB sensor in a single USB device. Unlike the Pi Camera Module 3, it **connects via USB** (no libcamera/CSI dependency) and runs inference on its own processor — offloading the Pi 5 CPU.

relates_to::[[raspberry-pi-5]]
relates_to::[[pi-camera-module-3]]
relates_to::[[ros2-jazzy]]
relates_to::[[rpi-coprocessor-os-options]]
derived_from::[[rpi-os-options]]

## Key Specifications (OAK-D / OAK-D-S2)

| Feature | Value |
|---------|-------|
| Depth sensing | Stereo (two grayscale sensors) |
| On-device compute | 4 TOPS (Intel Myriad X VPU) |
| Inference latency | 80–100 ms combined (stereo depth + NN) |
| Interface | USB 3.0 (plug-in, no CSI, no libcamera) |
| ROS support | `depthai-ros` package |

## Variants and Pricing

- **OAK-D** (original): ~$149; superseded by OAK-D-S2
- **OAK-D-S2**: ~$149; cleaner body, more CCM options — recommended successor
- **OAK-D-Lite**: ~$79–99; lighter, smaller; fewer features
- **OAK-D-SR** (Short Range): optimized for 30 cm–1 m; relevant for close manipulation tasks

## Why OAK-D for Robotics

**Stereo depth = real 3D object localization.** Detections include an (x, y, z) world-space position, not just pixel coordinates. For the capstone's Task Telemetry Contract, this means gap residuals can include true 3D spatial error, not just 2D image-plane estimates.

Also eliminates the libcamera/Ubuntu friction entirely — OAK-D is a USB device recognized via DepthAI SDK on any Linux OS:
```bash
pip install depthai
python -c "import depthai; print(depthai.Device())"
```

## ROS 2 Integration

`depthai-ros` is the official ROS 2 driver. For Jazzy, `depthai-core` currently requires building from source (kilted branch); binary apt packages not yet available:
```bash
git clone --branch kilted https://github.com/luxonis/depthai-core.git
# build + install, then build depthai-ros
```

A DepthAI ROS 3.0 (Kilted) release was announced in 2025 with RVC4 support, RGBD node, and colored pointclouds.

## Capstone Tradeoffs vs. PiCam2

| | OAK-D | Pi Camera Module 3 |
|---|---|---|
| Cost | $79–$149 (new hardware) | $25 (already owned) |
| Interface | USB (works on any OS) | CSI ribbon (Raspberry Pi OS native) |
| Depth | Yes (stereo) | No |
| FPS at full YOLO | ~15–30 (onboard VPU) | ~8–10 (CPU only) |
| Ubuntu 24.04 compat | Native (USB) | Requires libcamera fork build |
| Inference latency | 80–100 ms | ~40–60 ms |

**Best used when:** stereo depth or 3D spatial localization is architecturally required, and new hardware budget is available post-showcase.
