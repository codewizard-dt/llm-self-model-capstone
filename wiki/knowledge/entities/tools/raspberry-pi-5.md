---
id: raspberry-pi-5
title: Raspberry Pi 5
aliases: [Pi 5, Raspberry Pi 5, RPi 5]
updated: 2026-06-16
sources:
  - ../../../raw/research/vision-vex-architecture/index.md
  - ../../../raw/research/rpi5-camera-module-3-cost/index.md
  - ../../../raw/research/rpi-complete-kits/index.md
  - ../../../raw/research/rpi-complete-kits/index-2.md

tags: [tool, hardware, raspberry-pi, coprocessor, vision, ai]
---

# Raspberry Pi 5

The recommended AI/vision coprocessor for the capstone's VEX V5 robot. In the two-computer architecture, the Pi 5 handles all compute-intensive, non-deterministic work — computer vision, object detection, AprilTag localization, LLM inference, and telemetry aggregation — while the relates_to::[[vex-v5]] Brain runs a tight, deterministic motor control loop.

## Pricing (as of April 2026)

Three rounds of LPDDR4-driven price hikes since October 2025 have raised costs significantly above launch. Prices at authorized US resellers (PiShop.us, April 12 2026):

| Model | Launch | Current | Rise |
|-------|--------|---------|------|
| 1GB | $45 (Dec 2025) | $45 | 0% |
| 2GB | $50 | $65 | +30% |
| 4GB | $60 | $110 | +83% |
| 8GB | $80 | $175 | +119% |
| 16GB | $120 | $305 | +154% |

For the capstone (headless camera node), **4GB at $110 is the practical sweet spot**. The 2GB ($65) or 1GB ($45) is sufficient for pure streaming with no desktop. Buy from authorized resellers (PiShop.us, Adafruit, CanaKit) to avoid grey-market markups. See relates_to::[[rpi5-camera-module-3-cost]] for full system cost breakdown.

## Hardware

- Quad-core Arm Cortex-A76 at 2.4 GHz (2.5× faster than Pi 4 for general compute)
- RAM variants: 1 GB, 2 GB, 4 GB, 8 GB, 16 GB LPDDR4X (see pricing table above)
- CSI camera port — **22-pin 0.5mm "mini" FPC** (different from Pi 4's 15-pin; adapter cable required for Camera Module 3, included in camera box since Dec 4 2025)
- 2× USB 3.0, 2× USB 2.0 ports — one USB-A takes the V5 serial link, leaving ports free for a USB webcam
- Weight: **~46–47g** bare PCB; full on-robot system (board + official case + Camera Module 3 + 10,000 mAh power bank) ≈ **280–350g** — well within Clawbot chassis capacity
- Draws up to 5A at 5V peak, but the **camera-coprocessor workload (YOLO + AprilTags + serial bridge) draws only ~3–5W** in practice — a standard 5V/3A USB-C power bank is sufficient for capstone use (see `Power` section)
- Mounting: 56mm × 85mm PCB with M2.5 holes at the four corners — bolt to VEX rear chassis plate with M2.5 standoffs; velcro power bank flat on upper rail

## Vision Performance

| Stack | Resolution | FPS (Pi 5 CPU, no accelerator) |
|---|---|---|
| OpenCV color/blob | 640×480 | 30+ |
| YOLO11n (NCNN, INT8) | 640×480 | 8–10 |
| YOLO11n (NCNN, INT8) | 240×240 | 25+ |
| YOLO26n (ONNX) | 640×640 | ~7.8 |
| YOLOv8s (Hailo-8L M.2) | 640×640 | 41 (optional $70 HAT) |

For the capstone's slow manipulation tasks, 8 FPS is sufficient. YOLO model loading takes ~3 seconds first inference; plan a warm-up phase.

## Pi-to-V5 Serial Link

```
Pi USB-A ←──── microUSB cable ────→ V5 Brain user port
Device: /dev/ttyACM0 (or /dev/ttyACM1)
Baud: 115200, pyserial
Protocol: newline-delimited JSON
```

udev rule for consistent naming: `SUBSYSTEM=="tty", ATTRS{idVendor}=="2888", MODE="0666", SYMLINK+="vex_brain"`

## Software (Pi-side)

Three cooperating scripts:
- `vision_loop.py` — capture frame → YOLO11n NCNN → `apriltag.detect()` → emit `{detections, pose}` JSON
- `serial_bridge.py` — receive V5 telemetry → merge with vision → **append to `session_<ts>.jsonl`** → send commands to V5
- `llm_loop.py` — read latest contract from JSONL → call Claude API (Mode A real-time) → parse revised self-model → write next motor command

## Telemetry Storage

JSONL (newline-delimited JSON) is the storage format for incoming task contracts: one file per session (`session_YYYYMMDD_HHMMSS.jsonl`), append-only write, `flush()` after each contract. JSONL is faster than SQLite for insert-heavy workloads on Pi SD card, and is directly consumable by the Anthropic Batch API for post-session bulk analysis. A 32GB Pi microSD holds ~3 million sessions. See relates_to::[[vex-v5-telemetry-pipeline]] for the full pipeline specification.

## Power

Pi 5's rated peak is 5V/5A (25W), but the **actual capstone workload (YOLO + AprilTags + serial bridge, no USB peripherals except the V5 cable) draws only ~3–5W**. A standard **10,000 mAh USB-C PD power bank at 5V/3A** runs 12–15 hours at this workload — no high-wattage bank required. The Pi 5 will log a "low voltage" OS warning when powered from a 3A supply; this is cosmetic and does not affect stability at these power levels.

If full USB peripheral current is needed, the **52Pi PD Expansion Board (~$20)** steps down a 30W+ PD bank to clean 5V/8A and eliminates the warning.

**Do not power from the V5 battery** — the V5 1100mAh Li-Ion is motor-rated, not safe for the Pi's peak draw.

See derives_from::[[rpi-complete-kits-mobile-power]] for full mobile-power option comparison.

relates_to::[[vex-v5]]
relates_to::[[pi-camera-module-3]]
relates_to::[[raspberry-pi-build-hat]]
used_by::[[physical-robot-software-factory]]
extends::[[task-telemetry-contract]]
