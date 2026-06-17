---
topic: list of references of VEX V5 projects/github repos where they have opensourced their setup of autonomous robot that is controlled with rpi 5 with or without the camera module. also look for examples where they used telemetry as feedback. also look for examples where they used llms to model its behavior
slug: vex-v5-rpi-coprocessor-opensource
researched: 2026-06-17
sources: [./sources.md]
---

# Research: VEX V5 + Raspberry Pi Coprocessor — Open-Source Repos, Telemetry Feedback & LLM Behavior Modeling

> **No public repo uses a Raspberry Pi 5 specifically with the VEX V5 Brain** — the capstone's exact combination is novel. The closest open-source prior art uses Jetson Nano (official VEX VAIC competition) or generic Linux hosts (UTAH ROS lib). The communication contract is the same regardless of coprocessor: USB serial via `/dev/ttyACM0` at 115 200 baud. Telemetry-as-feedback is well established in the PROS / ROS community via `rosserial` streaming at up to 100 Hz. No open-source project has applied an LLM to model or revise VEX V5 robot behavior — this is the capstone's primary research novelty.

---

## Research Questions

1. Are there open-source GitHub repos combining VEX V5 + Raspberry Pi (any model) for autonomous robot control?
2. What communication protocols do working projects use between the V5 Brain and an external Linux coprocessor?
3. Do any projects use a camera module (Pi Camera or equivalent) alongside the V5 Brain for vision-driven autonomy?
4. Are there VEX V5 projects that use telemetry as closed-loop feedback (not just logging)?
5. Are there any VEX V5 (or adjacent VEX) projects that apply LLMs to model or adapt robot behavior?

---

## Current State (Codebase)

No code exists yet. Relevant existing wiki / raw research:

- `raw/research/vex-v5-telemetry-pipeline/index.md` — defines the USB serial pipeline, JSONL format, Mode A/B Claude API patterns (do not repeat here)
- `raw/research/ut-vexu-team/index.md` — identifies GHOST (team 1565X) as the UT Austin VEXU team; `VEXU-GHOST/VEXU_GHOST` is their open-source framework
- `raw/research/vexcode-v5/index.md` — recommends VEXcode Python with `sys.stdout` telemetry

---

## Key Findings

### 1. Official VEX AI Competition (VAIC) — Closest Architecture Match

The most directly applicable open-source reference is the **official VAIC repos** from VEX Robotics [S1][S2]. These define the canonical V5 Brain + coprocessor architecture:

- **Coprocessor**: Jetson Nano (not RPi5), but the serial interface is identical
- **Connection**: USB micro-B from V5 Brain user port → Jetson USB; appears as `/dev/ttyACM0` (user port) and `/dev/ttyACM1` (system port) — same as on a Raspberry Pi
- **Python class `V5SerialComms`** handles bidirectional serial at 115 200 baud; Jetson sends object-detection results; V5 Brain parses an `AI_RECORD` struct and uses GPS sensor fusion for field position
- **Camera**: Intel RealSense depth camera (not Pi Camera), with a web dashboard streaming live frames
- **Telemetry direction**: primarily coprocessor→V5 (AI vision data), but also V5→coprocessor (GPS position, IMU state)
- **Web dashboard**: Jetson runs a websocket server; team sees real-time camera, depth, object positions, and Jetson stats

VAIC 23/24: `https://github.com/VEX-Robotics/VAIC_23_24`
VAIC 24/25: `https://github.com/VEX-Robotics/VAIC_24_25`

Both repos include `JetsonExample/` (Python) and `V5Example/` (VEXcode C++ or Python). The Jetson example is fully open-source Python, easy to adapt for a Raspberry Pi.

---

### 2. VEXU-GHOST / UT Austin — Full V5 + Linux Framework [S3]

The UT Austin VEXU championship team (see `raw/research/ut-vexu-team/index.md`) open-sourced their entire software stack:

- **Repo**: `https://github.com/VEXU-GHOST/VEXU_GHOST`
- **Stack**: VEX V5 Brain (PROS) + Nvidia Jetson running **ROS2 Humble** (Ubuntu 22.04)
- **Communication**: serial over USB between V5 Brain and Jetson; PROS kernel on Brain side, ROS2 nodes on Jetson side
- **Scope**: path planning, localization, sensor fusion, motion control — a production-grade competition framework

While they use a Jetson, the repo's ROS2 architecture would run unchanged on a Raspberry Pi 5 running Ubuntu 22.04 (ROS2 Humble is officially supported on RPi5).

---

### 3. UTAH VEXU Robotics — rosserial for V5 Brain [S4][S5]

The University of Utah VEXU team open-sourced a `rosserial` bridge specifically for the V5 Brain:

- **Repo**: `https://github.com/UTAH-VEXU-Robotics/ros_lib`
- **What it does**: runs `rosserial` on the V5 Brain (PROS 3.x), making the Brain a ROS node; any ROS-capable Linux host (laptop, Jetson, Raspberry Pi) acts as the ROS master
- **Protocol**: ROS message serialisation over USB serial; tested at 100 Hz; higher rates (500 Hz+) unstable
- **Example messages**: sensor data (IMU, encoders), odometry — classic telemetry-as-feedback pattern
- **Host setup**: `rosrun rosserial_python serial_node.py _port:=/dev/ttyACM0 _baud:=115200`

This is the most directly reusable library for a V5 Brain + Raspberry Pi 5 + ROS2 setup.

Related: `https://github.com/UTAH-VEXU-Robotics/rosserial` (their forked rosserial with V5 support)

---

### 4. RoBorregos VEXU Wiki — Documented Jetson + V5 + ROS Stack [S6]

ITESM Tecnológico de Monterrey's VEXU team (2022) documented their full setup:

- **Repo**: `https://github.com/RoBorregos/VEXU-Wiki`
- **Stack**: ROS Melodic on Jetson Nano ↔ V5 Brain via rosserial; also Arduino UNO as a secondary bridge
- **Telemetry**: `rosrun rosserial_python serial_node.py _port:=/dev/ttyACM1 _baud:=115200`
- **Dependencies listed**: PROS, ROS-Melodic, TensorFlow 2, OpenCV-GPU, ROS Navigation Stack, Rosserial
- **Scope**: full autonomous navigation stack with AI vision

The RPi5 can run all of this — ROS2 equivalent packages exist, and TensorFlow / OpenCV are available for ARM64.

---

### 5. Maotechh/VEX_communication — RS-485 Smart Port Tutorial [S7]

A community tutorial (Chinese + English) for connecting VEX V5 Brain to Arduino or Raspberry Pi via the RS-485 Smart Port (higher bandwidth than USB serial):

- **Repo**: `https://github.com/Maotechh/VEX_communication`
- **Protocol**: Smart Port RS-485 → RS-485-to-TTL module → RPi GPIO UART
- **Pinout**: Black = RS485-A, Red = RS485-B, Green = GND, Yellow = 12V Power
- **V5 API used**: `vexGenericSerialEnable()`, `vexGenericSerialBaudrate()`, `vexGenericSerialWriteChar()`, `vexGenericSerialReceive()` (from PROS `vex_apiuser.h`)
- **Why use this over USB**: up to 921 600 baud (8× USB); isolated channel so USB stays free for code upload

This is the RS-485 path documented in `raw/research/vex-v5-telemetry-pipeline/index.md` as Stage 2.

---

### 6. Jordon-Notts/VEX-V5-Brain-External-Comm — VEXU Prototype [S8]

An individual VEXU developer investigated external controller → V5 Brain for "Over Under" season:

- **Repo**: `https://github.com/Jordon-Notts/VEX-V5-Brain-External-Comm`
- **Devices tested**: Arduino Uno and Raspberry Pi as external senders
- **Protocols explored**: PWM-like pulse timing (too noisy, ~5ms error), then string-based serial (`'x90,y100'` format)
- **Takeaway**: string-based serial over USB is the simplest approach; PWM pulse-width encoding is too error-prone for precision

---

### 7. joshuaferrara/VEX-Robotics-Internet-Control-Server — Telemetry Display via Web [S9]

An older project (VEX Cortex, not V5) showing RPi + web server + telemetry display:

- **Repo**: `https://github.com/joshuaferrara/VEX-Robotics-Internet-Control-Server`
- **Architecture**: VEX Cortex ↔ Serial ↔ Raspberry Pi ↔ Internet ↔ Web Server ↔ Browser client
- **Telemetry**: battery voltage, WiFi signal displayed on web dashboard in real time
- **Relevance**: same topology (RPi as gateway), V5 user port replaces Cortex serial

---

### 8. EvolvedAwesome/VEXSerial — VEX Cortex + RPi Packet Library [S10]

Packet-based serial library for VEX Cortex (predecessor to V5) + Raspberry Pi:

- **Repo**: `https://github.com/EvolvedAwesome/VEXSerial`
- **Protocol**: UART via RPi GPIO pins 8 and 10; RobotC on Cortex side; pyserial on Pi
- **Relevance**: shows the pyserial pattern; V5 equivalent uses USB serial (same pyserial code, different device path)

---

### 9. Griffin Tabor — RPi + Lidar + ROS on VEX Hardware ($150 Budget) [S11]

WPI undergraduate project (now faculty member):

- **URL**: `https://gftabor.github.io/project/autonomous-vex-robotics/`
- **GitHub**: `https://github.com/gftabor`
- **Hardware**: VEX mechanical components + Raspberry Pi + planar lidar + encoders ($150 total autonomy budget)
- **Software**: ROS + PCL (Point Cloud Library); later Google Cartographer (SLAM) + ROS Nav Stack
- **Achievement**: WPI Provost Award in Computer Science Department; believed to be first fully autonomous individually-programmed VEX robot at competition
- **Note**: Uses VEX mechanics as the robot body; the V5 Brain is not the primary controller — RPi runs the full autonomy stack

---

### 10. CUNY Academic Paper — RPi as Full Brain for VEX Hardware [S12]

Academic paper describing an undergraduate robotics course project:

- **URL**: `https://academicworks.cuny.edu/ny_pubs/1061/`
- **Title**: "Development of a Raspberry PI-Controlled VEX Robot for a Robotics Technology Course"
- **Key decision**: RPi **replaces** the VEX Cortex entirely — drives VEX motors directly via RPi GPIO
- **Goal**: vision-based control using Pi Camera; Linux environment enables Python3 + advanced algorithms
- **Constraint note**: uses older VEX EDR motors (PWM-controllable), not V5 Smart Motors (RS-485/encrypted)
- **Relevance**: shows that RPi-as-sole-brain is viable for VEX mechanical hardware, though V5 Smart Motors require the V5 Brain for motor firmware

---

### 11. vexide/vex-v5-serial — Rust Serial Protocol Implementation [S13]

- **Repo**: `https://github.com/vexide/vex-v5-serial`
- **What it does**: Rust implementation of the full VEX V5 serial communications protocol (USB and Bluetooth)
- **Relevance**: if the capstone needs to speak the V5 system protocol (not just user-port print), this library documents the packet format — useful for reading Brain status from a host

---

### 12. LLM Behavior Modeling — No VEX V5 Projects Found

Across all searches, **zero open-source projects were found that apply an LLM to model, plan, or adapt VEX V5 robot behavior**. The LLM+robotics space is active in academic research (VLA models, ProgPrompt, SMART-LLM [S14]) but none targets VEX V5 hardware.

The VEX AIM platform (a newer, simpler product) had one workshop in 2025 exploring LLMs for student learning [S15] — not for autonomous control.

**This is the capstone's primary research contribution.** The pattern of: V5 Brain emits telemetry → Pi 5 collects it → LLM revises a self-model → Pi writes updated motor targets back to V5 Brain has not been open-sourced anywhere.

---

### 13. RPi5-Specific — No VEX V5 Combinations Found

The Raspberry Pi 5 was released in late 2023. No GitHub repos or forum threads found that specifically pair an RPi5 with a VEX V5 Brain. The RPi5 runs Raspberry Pi OS (Debian Bookworm) which supports:
- ROS2 Jazzy (Ubuntu 24.04 officially; unofficial RPi OS builds exist)
- Python 3.11+ with pyserial
- Pi Camera Module 3 via libcamera API
- Hailo AI Kit (NPU) for on-device ML inference [S16]

All existing VEXU coprocessor patterns (USB serial, RS-485, ROS) work identically on an RPi5.

---

## Constraints

1. **V5 Smart Motors cannot be driven directly from RPi GPIO** — the Smart Port uses RS-485 with encrypted firmware loading; the V5 Brain must remain in the loop as motor controller
2. **No RPi5 + V5 Brain combination has been open-sourced** — no firmware image, udev rules, or tested pyserial config specific to RPi5 exists publicly
3. **VAIC uses Jetson Nano** (official) — the VAIC CUDA-based CV models do not run on RPi5's CPU alone; Pi Camera Module 3 replaces the RealSense for the capstone
4. **rosserial support for ROS2 is community-maintained** — the official UTAH lib targets ROS1 Melodic; ROS2 migration exists but is less tested
5. **RPi5 camera pipeline**: Pi Camera Module 3 uses `libcamera` (not V4L2 directly); OpenCV integration requires `picamera2` Python library

---

## Solution Comparison

| Approach | USB Serial (user port) | RS-485 Smart Port | rosserial (ROS) |
|---|---|---|---|
| **Baud rate** | 115 200 fixed | Up to 921 600 | 115 200 (tested stable at 100 Hz) |
| **Host lib** | pyserial | pyserial + RS-485 adapter | rosserial_python |
| **Bidirectional** | Yes (V5 can `sys.stdin.read()`) | Yes | Yes (full ROS msg protocol) |
| **Brain code** | VEXcode Python `print()` | PROS `vexGenericSerial*()` | PROS + ros_lib header |
| **Overhead** | Minimal | Minimal | ROS message serialisation |
| **Raspberry Pi hardware** | USB-A port (zero extra hardware) | GPIO UART + RS-485 module (~$3) | USB-A port |
| **VEXU legality** | Legal (VEXU) | Legal (VEXU) | Legal (VEXU) |
| **Open-source examples** | VAIC 23/24, VAIC 24/25 | Maotechh/VEX_communication | UTAH-VEXU ros_lib, RoBorregos wiki |
| **Best for capstone** | ✅ Stage 1 (demo) | Stage 2 (higher throughput) | Optional (adds ROS overhead) |

---

## Recommendation

**For the capstone**: use **USB serial (user port)** with `pyserial` on the Raspberry Pi 5. No extra hardware. Direct adaptation of VAIC `JetsonExample/V5Comm.py` → replace Jetson with RPi5, replace RealSense with Pi Camera Module 3 and `picamera2`. The telemetry pipeline is already specified in `raw/research/vex-v5-telemetry-pipeline/index.md`.

**Primary references to study:**

1. `VEX-Robotics/VAIC_24_25` — most recent official coprocessor reference architecture
2. `UTAH-VEXU-Robotics/ros_lib` — if ROS integration is desired
3. `VEXU-GHOST/VEXU_GHOST` — most complete ROS2 + V5 framework (by the UT team)

**For the LLM layer**: no prior art exists on VEX V5. The capstone is pioneering. Closest adjacent academic work: SMART-LLM (Purdue, multi-agent LLM task planning for robots) and BrainBody-LLM (closed-loop LLM with runtime feedback errors for correction) [S17].

---

## Next Steps

- `/wiki-ingest raw/research/vex-v5-rpi-coprocessor-opensource/index.md` — add to knowledge base
- `/task-add Adapt VAIC JetsonExample V5Comm.py for Raspberry Pi 5 (replace Jetson USB path, add udev rule)` — concrete first implementation step
- `/task-add Integrate Pi Camera Module 3 (picamera2) with serial_bridge.py — produce annotated frame + telemetry contract` — vision layer
- Consider `/decision-create`: should the capstone adopt ROS2 (VEXU-GHOST pattern) or stay with bare pyserial (simpler, VAIC-aligned)?
