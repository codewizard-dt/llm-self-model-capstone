---
id: vaic-reference-architecture
title: VEX AI Competition (VAIC) Reference Architecture
aliases: [VAIC, VEX AI Competition, VAIC repos]
updated: 2026-06-17
sources:
  - ../../../raw/research/vex-v5-rpi-coprocessor-opensource/index.md
tags: [tool, reference, vex, coprocessor, architecture, open-source, competition]
---

# VEX AI Competition (VAIC) Reference Architecture

The official open-source implementation by VEX Robotics for the **VEX AI Competition** — a fully autonomous (no driver) VEX V5 competition using an on-board AI coprocessor. The repos are the most authoritative and complete V5 + external coprocessor reference available.

**GitHub**: `https://github.com/VEX-Robotics/VAIC_23_24` (23/24 season)  
**GitHub**: `https://github.com/VEX-Robotics/VAIC_24_25` (24/25 season — most current)

## Architecture

```
V5 Brain (VEXcode C++/Python)         Jetson Nano (Python)
─────────────────────────────         ──────────────────────────────
AI_RECORD struct (C++ side)           V5Comm.py  ← USB serial, 115200 baud
parse AI data from Jetson      ←──── V5SerialComms class
GPS + IMU sensor fusion                Intel RealSense depth camera
VEXlink (V5↔V5 partner robot)         Object detection (YOLO/CV model)
                                       Web dashboard (websocket, hotspot AP)
                                       v5GPS.py (GPS position parsing)
```

Two major code components per repo:
- **`JetsonExample/`** — Python; powers the coprocessor; reads camera, runs CV model, manages V5 serial comms; open-source Python, directly portable
- **`V5Example/ai_demo/`** — VEXcode C++ project; parses `AI_RECORD` struct from Jetson; integrates GPS sensor; transmits via VEXlink to partner robot

## Portability to Raspberry Pi 5

The Jetson is used for CUDA-accelerated inference. **For the capstone**, the relevant Python code (serial comms, data parsing, web dashboard) is coprocessor-agnostic. Direct substitutions:

| VAIC (Jetson) | Capstone (RPi5) |
|---|---|
| `V5Comm.py` serial class | Same pyserial code, `/dev/ttyACM0` |
| Intel RealSense depth camera | relates_to::[[pi-camera-module-3]] + `picamera2` |
| CUDA YOLO inference | NCNN INT8 YOLO11n on Pi 5 CPU (8–10 FPS) |
| NVIDIA JetPack OS | Raspberry Pi OS (Bookworm) or Ubuntu 22.04 |
| Jetson hotspot AP | Pi 5 WiFi hotspot (same pattern) |

## Telemetry Direction

Primarily **coprocessor → V5** (AI vision data, GPS offsets). Also **V5 → coprocessor** (GPS position, IMU state). This is the reverse direction from the capstone's primary flow (V5 motor telemetry → Pi → LLM), but the serial link is bidirectional and the Python `V5SerialComms` class handles both directions.

## VEXU Legality

VAIC is a separate competition track from VEXU (VEX U). VEXU teams in V5RC are allowed external coprocessors; the communication pattern is the same. All code in the VAIC repos is legal for VEXU teams to study and adapt.

## Jetson Nano Status (June 2026)

The VAIC reference architecture uses the relates_to::[[jetson-nano]], which **reached EOL as a developer kit** (module available until Jan 2027). Research (see relates_to::[[jetson-nano-vs-rpi5]]) confirmed that the capstone's Pi 5 substitution is correct: the serial protocol (`V5Comm.py`, `/dev/ttyACM0`, 115200 baud) is identical between Jetson and Pi 5, and the Pi 5 outperforms the Nano on all CPU-bound tasks while costing far less.

relates_to::[[vex-v5]]
relates_to::[[raspberry-pi-5]]
relates_to::[[vex-coprocessor-pattern]]
relates_to::[[jetson-nano]]
used_by::[[ut-ieee-ras]]
