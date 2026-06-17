---
topic: VEXcode V5 — functionality, implementation, and limitations (install/v5 page)
slug: vexcode-v5
researched: 2026-06-16
sources: [./sources.md]
---

# Research: VEXcode V5 — Functionality, Implementation, and Limitations

> VEXcode V5 is VEX Robotics' official multi-modal coding environment for the V5 Brain, available free in Blocks/Python/C++ modes. It runs across web browser, desktop (Win/Mac), and mobile. Internally, Python runs as MicroPython on the V5 Brain's Xilinx ZYNQ SoC; C++ uses a proprietary cooperative task scheduler with a pre-loaded standard library. Key limitations for advanced use: no external Python packages, MicroPython constraints, no native Wi-Fi on the Brain, and a single-file project model in the main app. The VS Code Extension and PROS are the escape hatches for teams needing full toolchain control.

---

## Research Questions

1. What programming modes and platforms does VEXcode V5 support?
2. How is VEXcode V5 installed and what are the system requirements?
3. What is the internal technical implementation (Python runtime, Brain hardware, communication protocol)?
4. What can be accessed via the Python/C++ API (sensors, motors, serial, data)?
5. What are the hard limitations that constrain advanced or AI-driven use?

---

## Current State (Codebase)

The wiki already has a stub entity page at `wiki/knowledge/entities/tools/vexcode.md` covering the basics: Blocks/Python/C++ modes, 8 program slots, free download, and STEM Labs integration. This research report goes substantially deeper into implementation details and limitations relevant to the capstone's LLM-self-model project.

---

## Key Findings

### Functionality

**Three coding modes in one environment** [S1][S2]:
- **Blocks** — Scratch-style drag-and-drop; aimed at beginners. Blocks are readable aloud (accessibility). Switch blocks added in v4.0 to ease transition to text.
- **Python** — Text-based Python programming; MicroPython dialect. Code Viewer in Blocks mode shows the equivalent Python in real time.
- **C++** — Full C++ text programming; shared IDE, same download workflow.

**Available platforms** [S4][S5]:
- **Web app** (`codev5.vex.com`) — Chrome-based, no install required, always current. Available on Chromebook, Mac, and Windows with a Chrome browser. This is now the Chromebook path since Google discontinued Chrome Apps (effective July 2025).
- **Desktop app** — Windows and macOS native installers. Windows on ARM (Copilot+ PCs, Surface) is explicitly supported as of recent releases.
- **Mobile** — iPad (iOS App Store), Android, Amazon Fire tablet.
- ~~Chrome App~~ — End-of-life July 2025; VEX recommends web version.

**Notable recent features (VEXcode V5 4.0, 2024)** [S6]:
- AI Vision Sensor support: AprilTag detection + competition/classroom object classification (balls, rings, cubes, VRC High Stakes game elements)
- Read Blocks Aloud accessibility feature
- Switch blocks for Blocks→Text progression
- Direct link to full API docs from within the IDE
- Stop project command for enhanced execution control

**Brain slots**: Programs compile and download to one of **8 named slots** on the V5 Brain [S7]. The Brain's color touchscreen shows slot names; programs can be selected and run without reconnecting to a computer.

**Robot configuration**: A graphical Devices panel maps physical hardware (motors, sensors) to named software objects before coding begins. Project templates (Clawbot, Drivetrain) come pre-configured [S8].

**Data logging**: Python can write CSV files to an SD card inserted in the V5 Brain [S9]. Standard Python file I/O is available (as of MicroPython v1.13 update in VEXcode 2.0.7).

**Serial / USB communication**: The V5 Brain exposes two USB serial ports when connected to a host computer [S10]:
- *System port* — used by VEXcode/PROS-CLI/vexide for program upload and brain control.
- *User port* — stdio debug terminal; user programs can print to it and read from it.
This is the integration path for connecting an external AI computer (Raspberry Pi, laptop) to the V5 Brain — the VEX AI demo explicitly uses a Jetson Nano communicating with a V5 Brain via this USB serial link [S11].

**Robot-to-robot**: VEXlink API allows two V5 robots to communicate wirelessly [S11].

---

### Implementation (Technical Architecture)

**Brain hardware** [S12][S13]:
- SoC: Xilinx ZYNQ XC7Z010 (dual-core ARM Cortex-A9 + FPGA programmable logic)
- RAM: mounted externally on the Brain PCB
- CPU1 runs user code (robot programs); CPU0 runs VEXos (the proprietary OS)
- The FPGA handles peripheral I/O but is not user-programmable
- Power: large quiescent current draw noted; competition battery drains faster than expected even at idle

**Python runtime** [S14]:
- MicroPython — a lean reimplementation of Python 3 targeting microcontrollers
- VEXcode 2.0.7 uses MicroPython v1.13; earlier releases used 1.12
- All VEX hardware objects are exposed via `from vex import *`; a `Brain` object is automatically instantiated at program start

**C++ runtime** [S13]:
- C++ standard library is **pre-loaded into Brain memory**, not compiled into each user binary — this reduces program size but ties user code to the library version on the Brain
- VEXcode relies on **undocumented parts of the proprietary VEX SDK** for its cooperative (non-preemptive) task scheduler
- User programs run as code compiled for ARM Cortex-A9 and loaded into CPU1

**Communication protocol** [S15]:
- V5 Serial Protocol: binary protocol over USB serial; used by VEXcode, PROS-CLI, and the vexide community toolkit
- Connection options: direct USB (fastest; two ports), VEXnet radio (via controller), Bluetooth (V5 Radio in Bluetooth mode)

**Project structure** (VEXcode main app) [S16]:
- Single-file Python or C++ programs; device config stored as project metadata
- Projects save to `.v5code`-style files on the host machine
- **VEXcode Pro V5 is EOL** — replaced by the VS Code Extension, which supports multi-file projects

**VS Code Extension** [S17]:
- Official VEX extension for Visual Studio Code
- Supports V5, IQ 2nd Gen, EXP, CTE, AIM, AIR platforms
- Python and C++ supported
- Full VS Code editor features: multi-file projects, IntelliSense, extensions marketplace
- Recommended for students considering professional coding careers

**PROS** (third-party, community) [S18]:
- C/C++ environment maintained by Purdue University ACM SIGBots
- FreeRTOS (preemptive scheduler) rather than VEXcode's cooperative one
- Better documentation in some areas; more flexible file structure
- Recommended for advanced/competition teams needing full toolchain control

---

## Constraints

Any solution using VEXcode V5 Python on the V5 Brain must account for:

1. **MicroPython, not CPython**: Standard library is stripped. Some modules (e.g., `math`) are present but `pip install` is impossible. Third-party Python packages (NumPy, scikit-learn, etc.) cannot run on the Brain.
2. **No native network**: The V5 Brain has no Wi-Fi or Ethernet. All external AI computation must flow through the USB serial user port or VEXnet/Bluetooth radio link.
3. **Cooperative scheduler**: VEXcode C++ tasks are cooperative, not preemptive. Long-blocking user code can starve other tasks.
4. **Proprietary SDK dependency**: VEXcode's internals rely on undocumented SDK functions; community reimplementations (vexide/PROS) reverse-engineer around this.
5. **Program slot limit**: 8 slots — sufficient for most use but not unlimited.
6. **Single-file project model** in the main VEXcode app: complex multi-module architectures require the VS Code Extension or PROS.
7. **SD card required** for persistent file logging; Brain has no onboard flash for user data.
8. **Web-based VEXcode requires Chrome**: Safari, Firefox, and Edge are not supported.
9. **iPad / tablet version**: Feature parity with desktop is not guaranteed; primarily suitable for Blocks mode.

---

## Solution Comparison

| Approach | VEXcode V5 (main app) | VEX VS Code Extension | PROS (Purdue) |
|---|---|---|---|
| **Languages** | Blocks, Python (MicroPython), C++ | Python, C++ | C/C++ only |
| **Project model** | Single-file | Multi-file | Multi-file, RTOS |
| **Scheduler** | Cooperative | Cooperative | FreeRTOS (preemptive) |
| **Target user** | Students K–12/college | Proficient coders | Competition/advanced |
| **Toolchain** | Proprietary, self-contained | VS Code ecosystem | Open, CLI-based |
| **Documentation** | Excellent (api.vex.com) | Good | Good (but aging) |
| **External libraries** | None (MicroPython) | Limited | Limited (C++ headers) |
| **Platform** | Web / desktop / mobile | Desktop (VS Code) | Desktop CLI |
| **Maintenance** | Active (VEX) | Active (VEX) | Community (Purdue) |

---

## Recommendation

**For the capstone's LLM self-model project**: use **VEXcode V5 Python** on the V5 Brain for all robot-side code (motor commands, sensor reads, data logging), and run the LLM and self-model logic on an **external computer** (laptop or Raspberry Pi) communicating via the USB serial *user port*.

This follows the exact architecture VEX uses for the VEX AI platform (Jetson Nano ↔ V5 Brain via USB serial). It sidesteps MicroPython's library limitations entirely: the LLM, NumPy, and all ML tooling live on the host machine; only lightweight telemetry commands cross the serial link.

**Implementation outline**:
1. Flash a simple Python stub to the V5 Brain (VEXcode V5 app) that reads motor telemetry (position, velocity, current, torque) and sensor readings, then emits JSON over `sys.stdout` (the user serial port).
2. On the host, open the user serial port with `pyserial`; feed telemetry into the LLM pipeline.
3. LLM updates the self-model; host writes motor commands back over the same serial link; stub reads `sys.stdin` and executes them.

**Risks and mitigations**:
- *Serial latency*: USB serial is adequate for non-real-time telemetry. Avoid relying on it for tight control loops; keep PID on the Brain.
- *MicroPython version drift*: VEX upgrades MicroPython versions; pin the Brain firmware to a known version before a competition or demo.
- *VEXcode Pro V5 EOL*: Do not build workflows around VEXcode Pro V5; use the main VEXcode V5 app or VS Code Extension.

**Alternative if constraints change**: If multi-file C++ architecture is needed (e.g., more complex task scheduling), adopt the VS Code Extension with the VEX SDK. If open-source toolchain control is paramount, adopt PROS + vexide.

---

## Next Steps

- Run `/wiki-ingest raw/research/vexcode-v5/index.md` to synthesize this into the knowledge base and update the `wiki/knowledge/entities/tools/vexcode.md` entity page.
- Consider `/task-add Implement V5 Brain serial telemetry stub in VEXcode V5 Python` to build the robot-side communication layer.
- Consider `/decision-create Choose between VEXcode V5, VS Code Extension, and PROS for capstone robot code` if the team needs to formally commit to a toolchain.
