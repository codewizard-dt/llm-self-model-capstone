---
id: nvidia-jetpack
title: NVIDIA JetPack SDK
aliases: [JetPack, JetPack SDK, NVIDIA JetPack]
updated: 2026-06-17
sources:
  - ../../../raw/research/jetson-nano-vs-rpi5/index.md
tags: [tool, software, nvidia, sdk, edge-ai]
---

# NVIDIA JetPack SDK

The mandatory OS and software stack for all Jetson platforms. Every Jetson device runs JetPack — it is not optional. JetPack bundles the Jetson Linux Driver Package (L4T), Ubuntu root filesystem, CUDA, cuDNN, TensorRT, DeepStream, and the Isaac robotics SDK.

## Versions Relevant to Capstone Evaluation

| JetPack | Ubuntu base | Python | Supported Jetsons |
|---|---|---|---|
| 4.6 | 18.04 | **3.6 (EOL)** | Nano, Xavier NX, AGX Xavier |
| 5.x | 20.04 | 3.8 | Xavier NX, AGX Xavier, Orin |
| 6.x | 22.04 | 3.10+ | Orin family only |

## Setup Requirements

- **Jetson Nano (JetPack 4.6)**: requires NVIDIA SDK Manager running on a separate **x86 Ubuntu PC** to flash. The micro-SD path exists but requires manual patching. Total setup time estimate: 2–4 hours including library compatibility work.
- **Jetson Orin Nano Super (JetPack 6.x)**: SD card image available, but an existing unit shipped with JetPack 5.x must update firmware first before inserting the JetPack 6.x SD card.

## Python Ecosystem Friction (JetPack 4.6 / Jetson Nano)

JetPack 4.6 ships Python 3.6, which reached EOL in December 2021. Modern libraries (Ultralytics YOLO, pyserial 3.5+, OpenCV-Python 4.8+) do not install without either: (a) a 3rd-party patched OS image (Qengineering project), or (b) manual wheel building. This is a significant development velocity cost compared to Raspberry Pi OS Bookworm (Python 3.11, standard `pip`).

## What JetPack Adds

- **CUDA + TensorRT**: GPU-accelerated inference — meaningful when running >30 FPS YOLO on high-resolution video
- **DeepStream**: streaming AI analytics pipeline
- **Isaac SDK**: robotics perception and navigation
- **VPI**: vision programming interface with GPU/NVENC backends

For the capstone (8–10 FPS inference on slow manipulation tasks, Claude API for LLM), **none of these additions are needed**. The friction outweighs the benefit.

relates_to::[[jetson-nano]]
relates_to::[[jetson-orin-nano-super]]
compared_in::[[jetson-nano-vs-rpi5]]
