---
id: lego-spike-prime
title: LEGO Education SPIKE Prime
aliases: [SPIKE Prime, SPIKE]
updated: 2026-06-16
sources:
  - ../../../raw/Feasibility of a Human-Built Generational Robot Software Factory.pdf
  - ../../../raw/Feasibility of a Software Factory for LEGO-Based Self-Assembling Learning Robots.pdf
  - ../../../raw/research/lego-spike-prime/index.md
tags: [tool, hardware, lego, platform, robotics]
---

# LEGO Education SPIKE Prime

LEGO's current educational robotics platform and the **recommended Stage-1 base** for a physical-robot software factory across the feasibility reports. Core set ~$429.95 (528 elements); hub has 6 LPF2 ports, IMU, 6-axis gyro, speaker, 5×5 LED matrix, rechargeable battery; programmable via SPIKE app blocks and **embedded MicroPython** (run, run_for_degrees, run_to_absolute_position, set_duty_cycle).

## Why Stage 1, Not Forever

Best LEGO-native first prototype because hardware, sensors, app, Python path, and Raspberry Pi integration are already aligned — but it is an **app-mediated, memory/processing-constrained microcontroller**. Serious autonomy (perception, planning, orchestration) must be **offloaded** to external compute (Raspberry Pi Build HAT or workstation). No native camera — pair with external webcam / Pi camera. Lifecycle risk: at least one regional LEGO Education page flags retirement on **June 30, 2026**.

## Hardware Profile (2026-06-16 research)

Precise specs confirmed via the [[research-lego-spike-prime]] report:

| Component | Spec |
|-----------|------|
| Hub MCU | STM32F413 ARM Cortex-M4 @ ~100 MHz |
| Hub RAM / Flash | 320 KB SRAM / ~1–1.5 MB |
| Ports | 6 LPF2 I/O (auto-detect) |
| Motors | 1 Large + 2 Medium Angular (absolute encoder, ±3°) |
| Sensors | Distance (ultrasonic, 0–2 m, 1 mm), Force (0–10 N, ±0.65 N), Color (8-color + reflect/ambient) |
| Elements | ~528 Technic pieces (503–557 by source) |
| MSRP / secondary | $429.95 / ~$566 new-sealed (appreciating 6.2%/yr) |

The **320 KB RAM confirms zero on-hub LLM inference** — the hub is a pure sensor/actuator peripheral. **No native camera** (supplement with USB/Pi camera). The finite typed parts vocabulary is the grounding the [[llm-authored-self-model]] needs.

## Integration Paths (external compute)

1. **[[pybricks]]** — *recommended.* Alternative open-source firmware; clean `pybricks.pupdevices` Python API; offline hub programs; survives the SPIKE App retirement.
2. **[[raspberry-pi-build-hat]]** — onboard Raspberry Pi, 4 LPF2 ports over serial; good for a self-contained camera-equipped demo.
3. Native SPIKE App MicroPython — limited; tied to the retiring ecosystem; not recommended.

## Lifecycle (confirmed)

**Official end-of-sales: June 30, 2026** — one day after the June 29 capstone showcase. LEGO.com stock already depleted; Amazon (B07QN7ZJF9) and eBay carry sealed units. SPIKE App: no new features after that date. Successor [[lego-cs-ai-kit]] is a classroom curriculum tool, **not** a research-platform replacement. Mitigation: buy now; keep the generation-manifest representation platform-agnostic so Stage 2 ([[vex-v5]]) is a vocabulary swap.

used_by::[[physical-robot-software-factory]]  
controlled_by::[[pybricks]]  
controlled_by::[[raspberry-pi-build-hat]]  
superseded_by::[[lego-cs-ai-kit]]  
grounds::[[llm-authored-self-model]]  
relates_to::[[vex-v5]]  
relates_to::[[feasibility-human-built-generational-factory]]  
relates_to::[[research-lego-spike-prime]]
