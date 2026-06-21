---
id: vexcode
title: VEXcode
aliases: [VEXcode V5, VEXcode V5 Python, VEXcode Blocks, VEXcode Text]
updated: 2026-06-20
sources:
  - ../../../raw/research/vex-v5-classroom-starter-kit/index.md
  - ../../../raw/research/vexcode-v5/index.md
  - ../../../raw/research/vexcode-python-vs-cpp/index.md
tags: [tool, software, vex, programming, education]
---

# VEXcode

The official programming environment for all VEX platforms (123, GO, IQ, EXP, V5, AIM, AIR). **VEXcode V5** targets the relates_to::[[vex-v5]] Brain and is the coding layer the free relates_to::[[stem-labs]] curriculum is built on. Available at https://www.vexrobotics.com/vexcode and as a web app at https://codev5.vex.com.

## Modes

Three modes coexist in one environment, sharing the same IDE layout:

| Mode | Interface | Target learner |
|------|-----------|---------------|
| **Blocks** | Scratch-style drag-and-drop | Beginners; K–middle school |
| **Python** | Text (MicroPython dialect) | Intermediate; middle–college |
| **C++** | Text (proprietary SDK) | Advanced; competition |

When working in Blocks, a live **Code Viewer** renders the equivalent Python or C++ alongside the canvas, providing a bridge from visual to text. Switch Blocks (added in v4.0) ease the Blocks→Text transition on real hardware.

## Platforms and Installation

| Platform | How | Notes |
|----------|-----|-------|
| **Web** (`codev5.vex.com`) | No install; Chrome-based | Chromebook, Mac, Windows; always current |
| **Desktop** | Installer (Win / macOS) | Windows on ARM (Copilot+, Surface) supported |
| **Mobile** | App Store / Google Play | iPad, Android, Amazon Fire |
| ~~Chrome App~~ | ~~Chrome Web Store~~ | **EOL July 2025** — switch to web version |

Web version has full feature parity with the desktop app. Web version requires a Chrome-based browser; Safari, Firefox, and Edge are not supported.

## Technical Implementation (V5)

**Hardware**: the V5 Brain runs a **Xilinx ZYNQ XC7Z010 SoC** (dual-core ARM Cortex-A9 + FPGA). User code runs on CPU1; VEXos runs on CPU0. The FPGA manages peripheral I/O but is not user-programmable. Quiescent power draw is high (Zynq characteristic).

**Python runtime**: **MicroPython** (v1.13 as of VEXcode 2.0.7). All hardware objects are exposed via `from vex import *`; a `Brain` object is auto-created at project start. Standard Python file I/O is available. External packages (`pip install`) are **not** supported.

**C++ runtime**: C++ standard library is **pre-loaded into Brain memory** rather than compiled into each binary. The task scheduler is **cooperative** (non-preemptive), backed by undocumented parts of the proprietary VEX SDK.

**Program slots**: programs download to one of **8 named slots** on the V5 Brain. The Brain's color touchscreen lets users select and run any slot without reconnecting to a computer.

**Device configuration**: a graphical Devices panel maps physical hardware (motors, sensors) to named software objects before coding begins. Project templates (Clawbot, Drivetrain, etc.) come pre-configured.

## Communication and External Integration

When the V5 Brain connects to a host computer via USB, two serial ports are exposed:

- **System port** — program upload and Brain control (used by VEXcode, PROS-CLI, vexide)
- **User port** — stdio debug terminal; user Python/C++ code can `print()` and `input()` here

This user port is the **primary integration channel for external AI computation**. VEX's own VEX AI demo uses a Jetson Nano ↔ V5 Brain USB serial link for exactly this purpose: the Jetson sends processed vision data to the Brain, which displays it on-screen and forwards it to a partner robot via VEXlink.

Additional connection options: VEXnet radio (via Controller), Bluetooth (V5 Radio).

Data logging to **SD card** (CSV via standard file I/O) is supported.

## Limitations

- **No external Python packages**: MicroPython; NumPy, scikit-learn, and CPython-only libs cannot run on Brain.
- **No Wi-Fi on Brain**: external compute must reach the Brain through USB serial, VEXnet, or Bluetooth.
- **Cooperative scheduler**: long-blocking C++ code can starve other tasks; no RTOS preemption.
- **Single-file project model** in main app: multi-file architectures need the VS Code Extension or PROS.
- **SD card required** for persistent file storage; no onboard user flash.
- **Web version requires Chrome** — Safari, Firefox, Edge not supported.
- **No pip**: cannot install third-party MicroPython packages through VEXcode.
- **`input()` does not work** in VEXcode Python — confirmed on VEX forum.
- **Python stdin receiving from Pi is unconfirmed**: No community example shows Python code running *on the Brain* receiving data from a coprocessor via `sys.stdin.readline()`. A VEX forum thread about `std::cin/scanf()` in VEXcode C++ reports "The brain supports it but I suspect the VEXcode console does not" — the same concern applies to Python. See derives_from::[[v5-brain-python-vs-pros]].
- **Cooperative scheduler + blocking readline = watchdog risk**: If a Python `sys.stdin.readline()` call blocks while the Pi is disconnected, a watchdog `Thread` won't tick (cooperative means the blocked thread holds the scheduler). `uselect.poll()` could mitigate this, but its availability on VEX's custom MicroPython 1.13 port is unconfirmed.

## Toolchain Landscape

| Tool | Languages | Notes |
|------|-----------|-------|
| **VEXcode V5** (this) | Blocks, Python (MicroPython), C++ | Main environment; free; active; beginner-to-college |
| **VEX VS Code Extension** | Python, C++ | Replaced EOL VEXcode Pro V5; multi-file; professional tooling |
| **PROS** (Purdue) | C/C++ | FreeRTOS preemptive; community-maintained; competition-level |

**VEXcode Pro V5 is EOL** — it has been replaced by the VS Code Extension. Do not build new workflows around it.

## Python vs C++ API Comparison (VEXcode V5)

Full reference: <https://api.vex.com/v5/home/> · Python: <https://api.vex.com/v5/home/python/> · C++: <https://api.vex.com/v5/home/cpp/>

**Functional parity is essentially complete** — both languages bind the same underlying VEX V5 SDK. Every device (motors, sensors, brain, vision, VEXlink, pneumatics, arm, competition template) is reachable from either language. The Motor page confirms: `position`, `velocity`, `current`, `power`, `torque`, `efficiency`, `temperature` are in both.

**Naming convention:** Python uses `snake_case`; C++ uses `camelCase` and `vex::` namespace. Example: `spin_to_position()` (Py) ↔ `spinToPosition()` (C++). Small per-page method divergences exist — always verify on the device's specific doc page rather than assuming mechanical case-conversion works.

**Doc taxonomy differs structurally:**

| Capability | Python location | C++ location |
|---|---|---|
| Smart motors | `Motion/` | `Motors_and_MotorControllers/` |
| IMU / Inertial | `Inertial.html` (top-level) | under `Smart_Port_Devices/` |
| Vision + AI Vision | `Vision/` (top-level) | under `Smart_Port_Devices/` |
| Distance/Optical/Rotation/GPS | `Sensing/` (top-level) | under `Smart_Port_Devices/` |
| Brain screen / SD card | `Screen.html`, `SDcard.html` (top-level) | under `Brain/` |
| 6-axis arm / pneumatics / magnet | top-level pages | under `CTE_Workcell/` |
| Std-library reference | `MicroPython_libraries.html` | *(none — pre-loaded stdlib)* |

**Runtime:** MicroPython (Python) is ~10–300× slower than compiled C++ for tight loops. Both run the **same cooperative VEXcode scheduler**. PID/real-time control is the C++ norm in the competition community. Python is appropriate for high-level logic, sensor orchestration, screen UI, and non-time-critical scripts.

> **Contradiction (on-Brain language):** Prior research (`vexcode-v5`) recommended **VEXcode V5 Python** for the on-Brain layer. The actual codebase (`robot/v5-brain/pros_bridge/src/main.cpp`) uses **PROS C++** with `pros::apix.h` and FreeRTOS. The PROS choice is defensible (better real-time, preemptive scheduler), but it should be recorded as a formal decision. See derives_from::[[research-vexcode-python-vs-cpp]].

## Recent Updates (v4.0, 2024)

- AI Vision Sensor: AprilTag detection + classroom/competition object classification (VRC High Stakes 2024–25 game elements, balls, rings, cubes)
- Switch Blocks for Blocks→Text progression
- Read Blocks Aloud accessibility feature
- Stop Project command for fine-grained execution control
- Direct link to full API docs at `api.vex.com` from within the IDE

## VS Code Extension — What It Adds (and Doesn't)

The VEX VS Code Extension (replacing the EOL VEXcode Pro V5) supports multi-file **C++** with a proper `src/` directory, AI Copilot, Git integration, and IntelliSense. **Python remains single-file in the VS Code Extension** — the official KB confirms "The VEX Extension only supports single Python file downloads currently." If staying in Python, VS Code Extension is a developer ergonomics upgrade only; no new Brain capabilities are added. Same USB serial user port applies. For advanced C++ projects, VS Code Extension is the right choice over VEXcode's built-in editor. See derived_from::[[research-vex-v5-advanced-toolchains]].

**Toolchain ladder for the capstone**:
- VEXcode V5 Python → VS Code Extension C++ → relates_to::[[pros]] C++ + relates_to::[[lemlib]] → relates_to::[[vexide]] Rust

relates_to::[[vex-v5]]  
relates_to::[[stem-labs]]  
relates_to::[[task-telemetry-contract]]  
relates_to::[[physical-robot-software-factory]]  
relates_to::[[llm-authored-self-model]]  
relates_to::[[pros]]  
relates_to::[[lemlib]]  
relates_to::[[vexide]]
