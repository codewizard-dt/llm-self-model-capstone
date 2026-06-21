---
id: vision-vex-architecture
title: "Research: Vision into VEX V5 Architecture (Raspberry Pi + Webcam)"
updated: 2026-06-16
sources:
  - ../../raw/research/vision-vex-architecture/index.md
tags: [source, research, vision, raspberry-pi, vex-v5, computer-vision, architecture]
---

# Research: Vision into VEX V5 Architecture (Raspberry Pi + Webcam)

A research report (2026-06-16) synthesizing community documentation, VEX forums, and official Raspberry Pi specs to define the canonical two-computer architecture for adding vision to a VEX V5 robot for the capstone project.

**The central recommendation**: treat the VEX V5 Brain as a deterministic motor/sensor controller and put all AI, vision, and telemetry aggregation on a relates_to::[[raspberry-pi-5]], connected via USB serial (microUSB on V5 → USB-A on Pi) with a JSON-over-pyserial protocol at 115200 baud. The V5 Brain (Xilinx ZYNQ running MicroPython) has no camera interface, no pip, and no spare compute for inference — the coprocessor split is the only viable path.

**The Pi vision stack**: OpenCV (30+ FPS color/blob detection, zero deps), Ultralytics YOLO11n with NCNN quantization (~8–10 FPS at 640×480 on Pi 5 CPU alone; 25+ FPS at 240×240), and the `apriltag` Python library (`uv pip install apriltag`) for workspace localization — a single `detector.detect(gray_frame)` call returns tag ID + 3D pose. For the capstone's slow manipulation tasks, 8 FPS is more than sufficient.

**Camera options**: USB webcam (Logitech C270/C920; plug-and-play via `cv2.VideoCapture(0)`, lowest friction) vs. relates_to::[[pi-camera-module-3]] (12MP Sony IMX708, PDAF autofocus, 75°/120° FOV, 1080p50, $25; connects over CSI ribbon so USB bandwidth is fully available for the V5 serial link; lower latency ~40ms vs ~100ms). Start with a USB webcam for the Stage 1 demo; upgrade to Module 3 if latency matters.

**Capstone impact**: vision extends the relates_to::[[task-telemetry-contract]] with `predicted.object_detected`, `observed.object_detected`, `observed.pose` fields — giving the relates_to::[[llm-authored-self-model]] a perception capability layer and enabling AprilTag-based spatial residuals in the gap model, directly paralleling the Hart/Scassellati visual self-observation lineage.

derived_from::[[vex-v5]]
extends::[[task-telemetry-contract]]
extends::[[llm-authored-self-model]]
uses::[[raspberry-pi-5]]
uses::[[pi-camera-module-3]]
