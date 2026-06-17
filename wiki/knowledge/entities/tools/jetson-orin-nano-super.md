---
id: jetson-orin-nano-super
title: NVIDIA Jetson Orin Nano Super
aliases: [Jetson Orin Nano Super, Orin Nano Super, Jetson Orin Nano]
updated: 2026-06-17
sources:
  - ../../../raw/research/jetson-nano-vs-rpi5/index.md
tags: [tool, hardware, nvidia, coprocessor, edge-ai, comparison]
---

# NVIDIA Jetson Orin Nano Super

The current NVIDIA entry-level Jetson developer kit ($249), announced December 2024. It is the recommended successor to the EOL Jetson Nano — same footprint, far more capable (67 TOPS vs 0.5 TOPS). Runs relates_to::[[nvidia-jetpack]] 6.x (Ubuntu 22.04, Python 3.10+).

## Specs

- CPU: 6× Cortex-A78AE @ 1.7 GHz
- GPU: 1024-core Ampere + 32 Tensor Cores
- AI: 67 TOPS (MAXN mode), 40 TOPS (15W mode)
- RAM: 8 GB LPDDR5
- Power: 7–25W via **DC jack 7–20V** (not USB-C)
- Thermal: active cooling fan required for >15W sustained

## Why Not Used in the Capstone

Despite being a strong platform, the Orin Nano Super is wrong for the capstone on three grounds:

1. **Power connector**: requires 7–20V DC supply — **standard USB-C power banks do not work**. On-robot deployment requires a dedicated voltage regulator.
2. **Cost**: $249 dev kit + ~$180 Intel RealSense camera = ~$430 total. Pi 5 4GB + Pi Camera Module 3 = $135.
3. **Overkill**: 67 TOPS for tasks that need 8 FPS inference at 0.5–2 Hz. The Pi 5 meets the capstone's real requirements.

High demand and backorder issues were reported in early 2025. See relates_to::[[jetson-nano-vs-rpi5]] for the comparison and relates_to::[[raspberry-pi-5]] for the chosen alternative.

relates_to::[[jetson-nano]]
relates_to::[[nvidia-jetpack]]
relates_to::[[raspberry-pi-5]]
compared_in::[[jetson-nano-vs-rpi5]]
