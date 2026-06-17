---
id: pros
title: PROS (Purdue Robotics OS)
aliases: [PROS, Purdue Robotics OS, PROS 3]
updated: 2026-06-16
sources:
  - ../../../raw/research/vex-v5-advanced-toolchains/index.md
tags: [tool, software, vex, programming, rtos, competition, open-source]
---

# PROS (Purdue Robotics OS)

An open-source C/C++ development environment for the relates_to::[[vex-v5]] Brain, maintained by students at Purdue University through Purdue ACM SIGBots. Originally created in 2012 for Purdue's VEX U team BLRS; open-sourced in 2013. PROS 3 is the current version for V5.

## Key Differentiator: FreeRTOS

Unlike relates_to::[[vexcode]]'s cooperative task scheduler, PROS uses **FreeRTOS** — an industry-standard preemptive real-time operating system. Tasks are interrupted on a timer rather than yielding voluntarily. This enables truly concurrent Brain-side tasks: a telemetry streaming task at 20 Hz and a PID motor control loop can run simultaneously without the programmer managing cooperative yields.

## pros::Serial — Smart Ports as RS-485 Channels

Any V5 Smart Port (physically RS-485) can be configured as a generic serial device:

```cpp
pros::Serial port(19, 115200);   // Smart Port 19 at 115200 baud
port.write(data, len);
port.read_byte();
```

Maximum baud rate: ~921,600 (8× the USB user port's fixed 115,200). This creates a coprocessor data link independent of the USB connection — an external SBC or microcontroller can be wired to a Smart Port via a standard RS-485 transceiver chip. The rosserial community uses this to bridge the V5 Brain to ROS 2.

**Capstone relevance (Stage 2)**: `pros::Serial` is the high-throughput telemetry channel for the self-model loop. USB stays free for monitoring/upload while task contract JSON streams over Smart Port to the relates_to::[[raspberry-pi-5]] at up to 921,600 baud. See relates_to::[[vex-v5-telemetry-pipeline]].

## Multi-File C++ Projects

PROS projects are standard C++ with `include/` and `src/` directories — arbitrary file counts, proper header/source separation, full CMake-like build system. Complex architectures (PID, odometry, serial frame encoding, self-model query API) can be cleanly organized.

## Community Templates

- uses::[[lemlib]] — odometry, PID, pure pursuit path following, Monte Carlo Localization
- OkapiLib — older motion profiling library (largely superseded by LemLib)

## Toolchain

- PROS CLI for project creation, building, uploading
- Works with VS Code (community extension) or any editor
- The PROS kernel depends on VEX's proprietary SDK (not fully open at the OS layer)

relates_to::[[vexcode]]  
relates_to::[[vex-v5]]  
relates_to::[[lemlib]]  
relates_to::[[vexide]]  
relates_to::[[physical-robot-software-factory]]
