---
id: vex-v5-rpi-coprocessor-opensource
title: Research — VEX V5 + RPi Coprocessor Open-Source Repos, Telemetry Feedback & LLM Behavior Modeling
updated: 2026-06-17
sources:
  - ../../../raw/research/vex-v5-rpi-coprocessor-opensource/index.md
tags: [source, vex-v5, raspberry-pi, coprocessor, telemetry, llm, open-source, community]
---

# Research — VEX V5 + RPi Coprocessor Open-Source Repos, Telemetry Feedback & LLM Behavior Modeling

A systematic survey of open-source GitHub repos and community projects that combine VEX V5 with an external Linux coprocessor, use robot telemetry as closed-loop feedback, or apply LLMs to model robot behavior. **The RPi5 + VEX V5 combination is novel — no public project has open-sourced this exact pairing.** The closest prior art uses Jetson Nano (official VAIC) or generic Linux hosts (UTAH rosserial). Communication protocol and device paths are identical across coprocessors: `/dev/ttyACM0` at 115 200 baud.

The survey found **13 relevant repos/projects** across three categories (coprocessor architecture, telemetry feedback, LLM application) and confirmed that **no open-source project applies an LLM to model or adapt VEX V5 robot behavior** — this remains the capstone's primary research contribution. derives_from::[[vex-v5-coprocessor-pattern]] relates_to::[[task-telemetry-contract]]

## Canonical Reference Architecture

The relates_to::[[vaic-reference-architecture]] repos (`VEX-Robotics/VAIC_23_24`, `VEX-Robotics/VAIC_24_25`) define the gold-standard V5 + coprocessor stack. The Jetson's `V5Comm.py` Python class handles serial to the V5 Brain at 115 200 baud; the V5 Brain runs a `V5SerialComms` C++ class and fills an `AI_RECORD` struct. The camera (Intel RealSense) and web dashboard (websocket server) are the Jetson-specific parts; both are straightforwardly replaced with Pi Camera Module 3 + `picamera2` and a lightweight Flask server on the relates_to::[[raspberry-pi-5]].

## VEXU Team Frameworks

**`VEXU-GHOST/VEXU_GHOST`** (relates_to::[[ut-ieee-ras]] championship team) is the most complete open framework: VEX V5 Brain + Jetson running **ROS2 Humble** (Ubuntu 22.04). This is directly portable to RPi5 running Ubuntu 22.04 — ROS2 Humble has official ARM64 support. **`UTAH-VEXU-Robotics/ros_lib`** provides a rosserial bridge making the V5 Brain a ROS node, stable at 100 Hz over USB. **`RoBorregos/VEXU-Wiki`** (Tec de Monterrey, 2022) documents the full dependency chain: PROS + ROS Melodic + TF2 + OpenCV-GPU + Nav Stack + rosserial at 115 200 baud.

## Communication Paths

Two routes are confirmed viable and open-sourced. The **USB user port** (pyserial, `/dev/ttyACM0`, 115 200 baud fixed) requires zero extra hardware and is the Stage 1 choice for the capstone. The **RS-485 Smart Port** (up to 921 600 baud, isolated channel) needs a $3 RS-485-to-TTL module; `Maotechh/VEX_communication` documents the wiring and PROS API. Both paths are VEXU-legal.

## LLM Behavior Modeling — Gap Confirmed

No open-source project was found that applies an LLM to model, plan, or revise VEX V5 robot behavior. The LLM+robotics space is academically active (SMART-LLM at Purdue, BrainBody-LLM, VLA models) but none targets VEX hardware. This confirms the capstone's novelty: V5 Brain emits telemetry → Pi 5 collects JSONL → LLM revises self-model → Pi writes next motor targets back to V5 Brain. relates_to::[[llm-authored-self-model]]
