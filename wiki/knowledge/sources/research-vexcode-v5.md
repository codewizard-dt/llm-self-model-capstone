---
id: research-vexcode-v5
title: Research: VEXcode V5 — Functionality, Implementation, and Limitations
updated: 2026-06-16
sources:
  - ../../raw/research/vexcode-v5/index.md
tags: [research, vex, vexcode, software, programming, capstone]
---

# Research: VEXcode V5 — Functionality, Implementation, and Limitations

Research conducted 2026-06-16 via Brave Search. Full report: `raw/research/vexcode-v5/index.md`. Primary sources register: `raw/research/vexcode-v5/sources.md`.

## What It Is

relates_to::[[vexcode]] is the official programming environment for all VEX platforms. **VEXcode V5** specifically targets the VEX V5 Brain and offers three modes in a single environment: **Blocks** (Scratch-style visual), **Python** (text, MicroPython dialect), and **C++** (text, proprietary SDK). The Blocks code viewer renders equivalent Python/C++ in real time, enabling a smooth beginner-to-advanced progression. The environment is **free** and available as a web app (`codev5.vex.com`, Chrome-based, no install), desktop (Windows and macOS), and mobile (iPad, Android, Amazon Fire). Chrome Apps for Chromebook were discontinued by Google effective July 2025; the web version is now the Chromebook path.

VEXcode V5 4.0 (late 2024) added AI Vision Sensor support (AprilTag detection, competition and classroom object classification), Switch Blocks for easing Blocks→Text transitions, a Read Blocks Aloud accessibility feature, and a direct link to the full API reference at `api.vex.com`.

## Technical Implementation

**Hardware**: The relates_to::[[vex-v5]] Brain runs on a **Xilinx ZYNQ XC7Z010 SoC** (dual-core ARM Cortex-A9 + FPGA). User code runs on CPU1; VEXos (the proprietary OS) runs on CPU0. The FPGA handles peripheral I/O but is not user-programmable. Power consumption is notably high even at idle due to the ZYNQ's quiescent draw.

**Python runtime**: VEXcode Python uses **MicroPython** (v1.13 as of VEXcode 2.0.7). All hardware objects are exposed via `from vex import *`; a `Brain` object is automatically created at project start. Standard Python file I/O is available; `pip install` is not.

**C++ runtime**: The C++ standard library is **pre-loaded into Brain memory** rather than compiled into each user binary. VEXcode's task scheduler is cooperative (not preemptive) and relies on undocumented parts of the proprietary VEX SDK.

**Communication**: When connected via USB, the V5 Brain exposes two serial ports: a *system port* (program upload and Brain control) and a *user port* (stdio debug terminal — user programs can print/read here). This user port is the integration channel used in the VEX AI platform, where a Jetson Nano sends processed vision data to the V5 Brain over USB serial; the Brain then forwards it via VEXlink to a partner robot.

## Limitations

- **No external Python packages**: MicroPython environment; `math`, basic collections, and `vex` are available, but NumPy, scikit-learn, and other CPython packages cannot run on the Brain.
- **No Wi-Fi on Brain**: all external AI computation must flow through USB serial, VEXnet radio, or Bluetooth.
- **Cooperative scheduler**: long-blocking code in VEXcode C++ can starve other tasks.
- **Single-file project model** in the main VEXcode V5 app; multi-file requires VS Code Extension or PROS.
- **SD card required** for persistent file logging; no onboard flash for user data.
- **Web version requires Chrome**; Safari, Firefox, and Edge are not supported.
- **VEXcode Pro V5 is EOL** — replaced by the VEX VS Code Extension.

## Toolchain Landscape

| Tool | Target | Languages | Notes |
|------|--------|-----------|-------|
| VEXcode V5 | Students K–college | Blocks, Python, C++ | Main environment; free; active |
| VEX VS Code Extension | Proficient coders | Python, C++ | Replaced Pro V5; multi-file |
| PROS (Purdue) | Competition | C/C++ | FreeRTOS; community-maintained |

## Capstone Relevance

**Recommended architecture for the LLM self-model loop**: run a lightweight Python stub on the V5 Brain (VEXcode V5 Python) that emits JSON telemetry (motor position, velocity, torque, current) over the USB serial user port. The LLM and self-model logic run on a connected host machine (laptop or Raspberry Pi), reading telemetry and writing motor commands back over the same link. This mirrors the VEX AI Jetson Nano pattern and sidesteps all MicroPython limitations — the host machine has full CPython, NumPy, and LLM tooling.

derived_from::[[research-vexcode-v5]]  
relates_to::[[vexcode]]  
relates_to::[[vex-v5]]  
relates_to::[[task-telemetry-contract]]  
relates_to::[[physical-robot-software-factory]]  
relates_to::[[llm-authored-self-model]]
