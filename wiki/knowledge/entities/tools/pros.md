---
id: pros
title: PROS (Purdue Robotics OS)
aliases: [PROS, Purdue Robotics OS, PROS 3]
updated: 2026-06-21
sources:
  - ../../../raw/research/vex-v5-advanced-toolchains/index.md
  - ../../../raw/research/vex-v5-rpi-coprocessor-opensource/index.md
  - ../../../raw/research/vexcode-python-vs-cpp/index.md
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

> **Adding any library:** follow relates_to::[[pros-dependency-compatibility]] — pin a
> kernel-4.x release and build as a monolith (`USE_PACKAGE:=0`). On the capstone Brain
> the default hot/cold split is silently broken (program runs but display + serial
> no-op); the monolith build is the verified-working configuration.

## Toolchain

- PROS CLI for project creation, building, uploading
- Works with VS Code (community extension) or any editor
- The PROS kernel depends on VEX's proprietary SDK (not fully open at the OS layer)

### PROS CLI — Exact Commands (from derives_from::[[pros-cli-brain-bridge]])

```bash
uv add pros-cli && uv sync               # install (project uses uv, never pip; adds `pros` command)
# Linux only: sudo usermod -a -G dialout $USER  (then log out/in for USB upload permission)
pros conduct new-project ./my-project    # create a new PROS project with latest kernel
pros make                                # compile only
pros upload --slot 1                     # upload to Brain slot 1 (1–8)
pros mu --slot 1                         # make + upload in one command (most common)
pros mu                                  # same; no --slot → defaults to slot 1
pros terminal                            # stream printf output from running program (user port)
```

`pros` and `prosv5` are interchangeable aliases. Pin a default slot in `project.pros` under `upload_options: {"slot": 1}`.

**⚠️ Terminal conflict:** `pros terminal` and the Pi's pyserial cannot simultaneously hold the USB user serial port. Close the PROS terminal (and VS Code's VEX Integrated Terminal) before running the Pi bridge. This is a frequent operational gotcha.

### PROS Motor API (for Brain bridge program)

```cpp
pros::Motor m(port);                       // port 1–21; use true as 2nd arg to reverse
m.set_brake_mode(E_MOTOR_BRAKE_BRAKE);     // brake/coast/hold on zero velocity
m.move_velocity(rpm);                      // closed-loop PID; cap: ±200 (18:1), ±600 (6:1), ±100 (36:1)
m.move(value);                             // open-loop "joystick" value ±127
m.brake();                                 // stop per brake mode
m.get_actual_velocity();                   // double; achieved RPM
m.get_temperature();                       // double; °C
m.get_current_draw();                      // int32_t; mA
```

`move_velocity()` feeds the motor's internal Cortex M0 PID — the Brain does not run its own control loop. The RPM ceiling is gearset-dependent (200 for the stock 18:1 Clawbot drive). Telemetry fields (`get_actual_velocity`, `get_temperature`, `get_current_draw`) can piggyback on JSON acks to the Pi.

### JSON Parsing on the Brain

PROS has no stdlib JSON. **ArduinoJson** (header-only; copy `ArduinoJson.h` into `include/`) is the recommended parser:

```cpp
StaticJsonDocument<256> doc;              // stack-allocated; no heap churn at 50 Hz
if (deserializeJson(doc, line)) return;   // skip malformed packets
double vx = doc["vx"] | 0.0;             // with default fallback
```

Use `StaticJsonDocument`, never `DynamicJsonDocument`, in a tight loop to avoid heap fragmentation.

## Community RS-485 Coprocessor Examples (from [[vex-v5-rpi-coprocessor-opensource]])

## Capstone Implementation Status (2026-06-25)

**The PROS Brain bridge is now the active guarded firmware.** `robot/v5-brain/pros_bridge/src/main.cpp` is a buildable monolith PROS project using `pros/apix.h`, `pros::millis()`, `pros::delay()`, and `serctl(SERCTL_DISABLE_COBS, nullptr)`. It reads newline-delimited JSON from the V5 USB user/console serial port via `std::getchar()`, emits tagged `ack`/`telemetry`/`bridge_status` records, and watchdog-stops all configured motors on packet loss. The live port map is drive motors on ports 1 and 10 plus arm on port 8.

**Community confirmation of the pattern:** Multiple VEX AI competition teams use `SERCTL_DISABLE_COBS` + `printf()`/`getchar()` for bidirectional JSON over the USB user port (aadishv.dev "Robotics 5", VEX Forum `v5-brain-to-raspberry-pi-communication`). The official VAIC reference architecture (VEX-Robotics/VAIC_23_24 and VAIC_24_25) uses PROS C++ on the Brain with this exact approach.

**Multi-task pattern required in practice:** Real-world teams that combined send and receive into a single PROS task hit deadlocks (blocked on `getchar()` while needing to send). The capstone bridge uses separate FreeRTOS tasks for receive, watchdog, telemetry, and fixed routine slots. Routine slots 2-4 are serial command IDs inside the running bridge program: 2 = 720 spin, 3 = arm up/down, 4 = one foot forward/back.

**PROS C++ vs VEXcode Python (as research, not decision):** PROS C++ bidirectional serial is community-confirmed; VEXcode Python stdin receiving on the Brain is unconfirmed (no community example exists of Python on the Brain receiving from a Pi). See derives_from::[[v5-brain-python-vs-pros]].

## Community RS-485 Coprocessor Examples (from [[vex-v5-rpi-coprocessor-opensource]])

The RS-485 Smart Port path is confirmed by two open-source community references: **`Maotechh/VEX_communication`** (wiring diagram + PROS `vexGenericSerial*()` API, Chinese/English tutorial) and **`UTAH-VEXU-Robotics/ros_lib`** (rosserial bridge over USB that makes the V5 Brain a ROS node at 100 Hz). Both are confirmed working with external Linux hosts. The PROS `pros::Serial` Smart Port API is the only officially documented path to exceed the USB user port's fixed 115 200 baud ceiling. relates_to::[[vex-coprocessor-pattern]]

relates_to::[[vexcode]]  
relates_to::[[vex-v5]]  
relates_to::[[lemlib]]  
relates_to::[[vexide]]  
relates_to::[[physical-robot-software-factory]]
