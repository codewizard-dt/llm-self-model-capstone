---
id: pi-camera-module-3
title: Raspberry Pi Camera Module 3
aliases: [Pi Camera Module 3, Camera Module 3, IMX708]
updated: 2026-06-16
sources:
  - ../../../raw/research/vision-vex-architecture/index.md
  - ../../../raw/research/rpi5-camera-module-3-cost/index.md
tags: [tool, hardware, camera, raspberry-pi, vision]
---

# Raspberry Pi Camera Module 3

The **recommended camera upgrade** for the capstone's vision system once USB-webcam basics are proven. Connects over the Pi 5's CSI ribbon port — keeping USB bandwidth fully available for the V5 serial link.

## Specifications (official, Jan 2030 EOL)

| Spec | Value |
|---|---|
| Sensor | Sony IMX708 (back-illuminated, stacked CMOS) |
| Resolution | 11.9 MP (4608 × 2592) |
| Pixel size | 1.4μm × 1.4μm |
| Autofocus | Phase Detection Autofocus (PDAF) — ultra-fast |
| HDR | Yes (up to 3 MP output) |
| FoV (standard) | 75° diagonal |
| FoV (Wide variant) | 120° diagonal |
| Video modes | 1080p50, 720p120 |
| Dimensions | 25 × 24 × 11.5mm |
| Ribbon cable | 200mm, 15×1mm FPC (standard); Pi 5 adapter (22-pin) included since Dec 4 2025 |
| Price | $25 (standard / NoIR) / $35 (Wide / Wide NoIR) — unchanged since Jan 2023 |
| In production | Until at least January 2030 |

Variants: standard (75°), Wide (120°), NoIR (no IR filter for night-vision with IR lighting), NoIR Wide.

## Advantages over USB Webcam

- **Lower latency**: ~40ms vs ~100ms for USB webcam
- **Lighter**: 11.5mm-high PCB module vs bulky webcam enclosure
- **No USB contention**: CSI interface is independent of the USB bus used for V5 serial
- **Flexible routing**: 200mm ribbon cable gives freedom in mounting position
- **PDAF autofocus**: stays sharp as robot/objects move — important for YOLO detections
- **Picamera2 Python library**: pre-installed in Raspberry Pi OS; integrates cleanly with OpenCV

## Software

```python
from picamera2 import Picamera2
import cv2

cam = Picamera2()
cam.configure(cam.create_preview_configuration({"size": (640, 480)}))
cam.start()
frame = cam.capture_array()  # returns numpy array, pass to OpenCV/YOLO
```

## Capstone Integration

For the Stage 1 demo (Jun 29 2026), the Wide variant (120° FOV) is the stronger choice — wider field of view means the robot sees more of the workspace and captures AprilTag landmarks at more angles. Mount the module on a VEX angle bracket at the front-top of the chassis using the ribbon cable's flexibility to reach the Pi's CSI port anywhere on the robot frame.

## Pi 5 Cable Note

The Pi 5 uses a **22-pin 0.5mm "mini" FPC** camera connector; Camera Module 3 ships with a 15-pin 1mm standard cable. **As of December 4, 2025, Camera Module 3 ships with both cables** (150mm standard + 200mm Pi 5 adapter) — no extra purchase needed for new orders. Standalone adapter cables from Raspberry Pi cost $1–$3.

## Pricing Context

Camera Module 3 pricing ($25/$35) has been **unaffected by the 2025–2026 LPDDR4 shortage** that drove Pi 5 board prices up 83–154%. The IMX708 sensor has a separate supply chain. See derived_from::[[rpi5-camera-module-3-cost]] for full system cost estimates.

relates_to::[[raspberry-pi-5]]
used_by::[[physical-robot-software-factory]]
