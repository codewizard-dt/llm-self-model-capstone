---
id: jetson-nano
title: NVIDIA Jetson Nano
aliases: [Jetson Nano, Jetson Nano B01, Jetson Nano 4GB]
updated: 2026-06-17
sources:
  - ../../../raw/research/jetson-nano-vs-rpi5/index.md
tags: [tool, hardware, nvidia, coprocessor, edge-ai, comparison]
---

# NVIDIA Jetson Nano

The Jetson Nano is NVIDIA's entry-level edge AI board, released March 2019. It is the coprocessor used in the **official VEX AI Competition (VAIC) reference architecture** — the closest open-source prior art to the capstone's Pi 5 coprocessor design. See relates_to::[[vaic-reference-architecture]].

**As of June 2026, the Jetson Nano developer kit is EOL (discontinued).** The SOM (system-on-module) remains available until January 2027. The recommended successor is the relates_to::[[jetson-orin-nano-super]] ($249).

## Specs

- CPU: 4× Cortex-A57 @ 1.47 GHz
- GPU: 128-core NVIDIA Maxwell (0.5 TOPS INT8)
- RAM: 4 GB LPDDR4
- Power: 5W (micro-USB mode) or 10W (MAXN, 5V/4A barrel jack + J48 jumper required)
- OS: relates_to::[[nvidia-jetpack]] 4.6 (Ubuntu 18.04, Python 3.6 default)

## Why the Capstone Uses Pi 5 Instead

The Jetson Nano's GPU (CUDA + TensorRT) delivers 30+ FPS for YOLOv5 inference — but the capstone's manipulation tasks run at 0.5–2 Hz, making 8–10 FPS from the Pi 5 CPU more than sufficient. The Pi 5 outperforms the Nano on every CPU-bound workload (~3× faster, Cortex-A76 vs A57), costs far less ($135 total vs module + camera), and avoids JetPack's Python 3.6 library compatibility problems. See relates_to::[[jetson-nano-vs-rpi5]] for the full comparison.

**The serial protocol is identical**: the VAIC `V5Comm.py` class runs unchanged on Pi 5 — `/dev/ttyACM0`, 115200 baud, pyserial. See relates_to::[[vex-coprocessor-pattern]].

## When Jetson (Orin) Would Be Preferred

- On-device LLM inference (no cloud Claude API)
- >30 FPS high-resolution object detection required
- CUDA-mandatory libraries (NVIDIA Isaac ROS, cuSpatial, DeepStream)
- Production deployment with >1-hour sustained runtime

relates_to::[[vaic-reference-architecture]]
relates_to::[[raspberry-pi-5]]
relates_to::[[nvidia-jetpack]]
relates_to::[[vex-coprocessor-pattern]]
compared_in::[[jetson-nano-vs-rpi5]]
