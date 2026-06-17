---
id: research-vex-v5-advanced-toolchains
title: Research: VEX V5 Advanced Toolchains — VS Code Extension, PROS, LemLib, vexide
updated: 2026-06-16
sources:
  - ../../raw/research/vex-v5-advanced-toolchains/index.md
tags: [research, vex, vexcode, pros, lemlib, vexide, programming, toolchain, capstone]
---

# Research: VEX V5 Advanced Toolchains — VS Code Extension, PROS, LemLib, vexide

Research conducted 2026-06-16. Companion to relates_to::[[research-vexcode-v5]]. Full report: `raw/research/vex-v5-advanced-toolchains/index.md`. Primary sources: `raw/research/vex-v5-advanced-toolchains/sources.md`.

## VS Code Extension

The VEX VS Code Extension (the official replacement for the EOL VEXcode Pro V5) supports multi-file C++ projects with a proper `src/` directory structure and full VS Code tooling: AI Copilot, Git integration, IntelliSense, and linting. **However, Python remains single-file in the VS Code Extension** — the official KB states "The VEX Extension only supports single Python file downloads currently." For a Python-based Brain stub, VS Code Extension is a developer ergonomics upgrade over relates_to::[[vexcode]], not a capability unlock. The same USB serial user port pattern is available.

## PROS — Substantive Capability Unlocks

relates_to::[[pros]] (Purdue Robotics OS) is based on **FreeRTOS** — a preemptive real-time operating system. Unlike VEXcode's cooperative task scheduler, FreeRTOS interrupts tasks on a timer, enabling truly concurrent Brain-side tasks (telemetry streaming + motor PID) without manual cooperative yields.

**`pros::Serial`**: any of the 21 V5 Smart Ports (which are physically RS-485) can be configured as a generic serial channel at up to ~921600 baud. This creates a second coprocessor data path entirely separate from the USB user port — an external SBC (Raspberry Pi, Feather) can be wired to a Smart Port via an RS-485 transceiver chip. The rosserial community has used this to bridge the V5 Brain to ROS 2. For the capstone: during demos, USB stays free for monitoring while the AI pipeline runs over Smart Port RS-485.

relates_to::[[lemlib]] adds **odometry and PID** on top of PROS: x/y position + heading tracking using IMEs, rotation sensors, and the V5 Inertial Sensor (IMU). This replaces raw motor encoder counts with pose-level telemetry `{x, y, heading}` — the self-model's capability layer can then predict and compare spatial outcomes rather than just per-motor counts.

## vexide

relates_to::[[vexide]] is an open-source Rust async runtime for the V5 Brain. Advantages: compile-time memory safety (data aborts/prefetch errors eliminated), QEMU simulation support (test Brain code without hardware), and ~100× faster trig than PROS/VEXcode. Drawbacks: Rust learning curve; smaller community than PROS. **Deferred for the capstone demo timeline.**

## Capstone Architecture Decision

**Stage 1 (Jun 29 demo)**: VEXcode V5 Python. Lowest friction, most LLM-friendly, sufficient for the telemetry stub.

**Stage 2 (post-demo)**: PROS C++ + LemLib. Two unlocks that matter: (1) FreeRTOS preemptive scheduling for concurrent telemetry/control; (2) LemLib odometry for pose-level `{x, y, heading}` telemetry that feeds richer self-model gap residuals.

derived_from::[[research-vex-v5-advanced-toolchains]]  
relates_to::[[vexcode]]  
relates_to::[[vex-v5]]  
relates_to::[[pros]]  
relates_to::[[lemlib]]  
relates_to::[[vexide]]  
relates_to::[[llm-authored-self-model]]  
relates_to::[[task-telemetry-contract]]  
relates_to::[[physical-robot-software-factory]]
