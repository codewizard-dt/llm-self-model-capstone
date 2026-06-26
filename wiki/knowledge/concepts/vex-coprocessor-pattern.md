---
id: vex-coprocessor-pattern
title: VEX Coprocessor Pattern
aliases: [V5 coprocessor, V5 + Linux host, VEX external coprocessor]
updated: 2026-06-26
sources:
  - ../../raw/research/vex-v5-rpi-coprocessor-opensource/index.md
  - ../sources/robot-apriltag-ball-delivery.md
  - ../../raw/research/driver-telemetry-labeling/index.md
tags: [concept, architecture, vex-v5, coprocessor, raspberry-pi, serial, ros]
---

# VEX Coprocessor Pattern

The **two-computer architecture** used by VEXU and VEXAI teams to extend the VEX V5 Brain with a more capable Linux host. The V5 Brain handles deterministic real-time motor control (firmware-loaded RS-485 Smart Motors); the coprocessor handles everything the Brain cannot: computer vision, LLM inference, network connectivity, complex path planning, and persistent storage.

This pattern is validated by the official VAIC competition, the UT Austin GHOST team, the University of Utah RAS team, and multiple community builders. **No public project uses a Raspberry Pi 5 as the coprocessor** as of June 2026 — RPi5 is a novel substitution for the Jetson Nano, but the interface is identical.

## The Physical Constraint That Defines the Pattern

**V5 Smart Motors cannot be driven directly from a Raspberry Pi or any external board.** The Smart Port (RS-485) requires the V5 Brain to load motor firmware on boot and encrypt the control channel. Any attempt to drive V5 motors without the Brain would require reverse-engineering encrypted firmware — not practical. The V5 Brain is therefore a mandatory component; the coprocessor augments it, never replaces it. (Note: older VEX EDR motors are PWM-controllable and can be driven from RPi GPIO directly — the CUNY academic paper does this — but V5 Smart Motors are fundamentally different.)

**A user program must be running on the Brain for the user port to carry any data.** The Brain's system USB port handles program upload/management only (not motor commands); the user port is inert without a running program. This means the capstone always requires a Brain-side program — but that program can be minimal (~50–100 lines: read serial JSON → call motor API → send ack → watchdog). See derives_from::[[v5-user-programs]].

**No competition infrastructure required for non-competition use.** Without a Competition Switch or Field Management System connected, `opcontrol()` (PROS) / the main loop runs immediately after `initialize()`. The capstone does not need a competition switch, field controller, or autonomous/teleop split.

## Communication Paths

### Path 1 — USB Serial (user port) — Stage 1 / Recommended

```
Pi USB-A ──── microUSB cable ──── V5 Brain user port
/dev/ttyACM0 (user port) | /dev/ttyACM1 (system port)
115,200 baud, 8N1 | pyserial | newline-delimited JSON
Stable bidirectional for PROS C++: V5 printf()/fflush(stdout) → Pi; Pi writes → V5 getchar()/fgets(stdin)
> Note: "Pi writes → V5 stdin" is confirmed in PROS C++ (SERCTL_DISABLE_COBS + getchar()). Whether VEXcode Python sys.stdin.readline() receives from Pi is **unconfirmed** as of 2026-06-21 — no community example exists. See derives_from::[[v5-brain-python-vs-pros]].
Throughput: ~11,500 B/s; 300-byte contract in ~35ms
```

**udev rule for consistent naming:**
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="2888", MODE="0666", SYMLINK+="vex_brain"
```

### Path 2 — RS-485 Smart Port — Stage 2 / High-throughput

```
V5 Smart Port (RS-485) ──── RS-485-to-TTL module (~$3) ──── RPi GPIO UART
Pinout: Black=RS485-A, Red=RS485-B, Green=GND, Yellow=12V Power
Up to 921,600 baud (8× USB speed)
PROS API: vexGenericSerialEnable(), vexGenericSerialBaudrate(), etc.
Isolated channel: USB stays free for code upload during active demo
```

### Path 3 — rosserial (ROS bridge)

```
V5 Brain (PROS 3.x + ros_lib headers) ← USB → Linux host (rosserial_python)
rosrun rosserial_python serial_node.py _port:=/dev/ttyACM0 _baud:=115200
Stable at 100 Hz; 500 Hz+ unstable
Makes V5 Brain a ROS node: publish sensor data, subscribe to motor commands
```

## Open-Source Implementations (by confidence)

| Repo | Coprocessor | Connection | What it shows |
|---|---|---|---|
| `VEX-Robotics/VAIC_24_25` | Jetson Nano | USB serial | Full Python V5SerialComms class; camera; web dashboard |
| `VEXU-GHOST/VEXU_GHOST` | Jetson (ROS2) | USB serial | Production ROS2 Humble + V5; RPi5 Ubuntu 22.04 runs it |
| `UTAH-VEXU-Robotics/ros_lib` | Any Linux | rosserial | V5 Brain as ROS node; 100 Hz telemetry streaming |
| `RoBorregos/VEXU-Wiki` | Jetson Nano | rosserial | Full dep list; TF2 + OpenCV + Nav Stack |
| `Maotechh/VEX_communication` | Arduino/RPi | RS-485 Smart Port | Wiring + PROS API; PCB design |
| `Jordon-Notts/VEX-V5-Brain-External-Comm` | RPi | USB serial | String-based serial; PWM too noisy |

## Two-Task PROS Pattern (Brain side)

Community experience from VEX AI teams shows that combining command-receive and telemetry-send into a **single PROS task** deadlocks: blocked on `getchar()` for commands-in, unable to send telemetry-out. More critically, a single loop cannot guarantee the safety watchdog fires when the Pi disconnects mid-read. The correct PROS pattern is **two separate FreeRTOS tasks** (derives_from::[[pros-cli-brain-bridge]]):

```cpp
void receive_task(void*) {
    std::string line;
    while (true) {
        int ch = getchar();
        if (ch != EOF) {
            if (ch == '\n') { handle(line); line.clear(); }
            else if (line.size() < 512) line.push_back((char)ch);
            else line.clear();
        } else { pros::delay(2); }
    }
}

void watchdog_task(void*) {
    while (true) {
        if (pros::millis() - last_packet_ms > WATCHDOG_MS) all_stop();
        pros::delay(10);
    }
}

void opcontrol() {
    pros::Task r(receive_task,  nullptr, "rx");
    pros::Task w(watchdog_task, nullptr, "watchdog");
    while (true) pros::delay(1000);
}
```

FreeRTOS preemptive scheduling (1ms tick) lets the watchdog task run even when `getchar()` is blocked — the Pi disconnect → motors stop guarantee holds regardless of the receive task's state.

## For the Capstone

The capstone's RPi5 + V5 Brain + Pi Camera + Claude API stack follows this pattern with one addition: the LLM inference leg. The proven USB serial path (Stage 1) maps directly to `raw/research/vex-v5-telemetry-pipeline/index.md` Mode A real-time pipeline. No existing open-source project closes the LLM loop on this architecture — that is the novelty.

The current Brain bridge (`robot/v5-brain/pros_bridge/src/main.cpp`) is a buildable PROS monolith with separate receive, watchdog, telemetry, and routine tasks. It accepts the Pi's fixed control grammar, emits tagged `ack`/`telemetry`/`bridge_status` records, and exposes fixed routine slots 2-4 for bounded proof actions: 720 spin, arm up/down, and one-foot forward/back. These routine slots are command IDs inside the running bridge program, not VEXos user-program upload slots. See derives_from::[[v5-brain-python-vs-pros]].

## Bounded Release Commands

[Research: Robot AprilTag Ball Delivery](../sources/robot-apriltag-ball-delivery.md) adds a concrete example of why the coprocessor boundary needs fixed command grammar. The Pi-side ROS program can decide the sequence and vision target, but the Brain must expose a deterministic actuator primitive for the final drop. **`release` is therefore a bounded Brain command with `duration_ms`, separate from ROS-side `set_goal`, which remains unsupported by the Brain.** uses::[[vexy_ros ROS 2 Runtime]]

## Manual Driver Telemetry Variant

derived_from::[[driver-telemetry-while-using-the-controller]] adds a human-driver capture variant of the same coprocessor pattern. The V5 Brain remains actuator authority, but the V5 controller rather than ROS owns drivetrain commands. The Pi still acts as evidence recorder: it receives `/vex/telemetry`, records vision/scene-map topics, and timestamps human state labels. The architectural rule is the same as autonomous mode: the Brain owns motor safety, the Pi owns perception/storage/analysis, and only one side writes a motor subsystem at a time.

implements::[[llm-authored-self-model]]
transports::[[task-telemetry-contract]]
uses::[[raspberry-pi-5]]
uses::[[pros]]
uses::[[vaic-reference-architecture]]
relates_to::[[vex-v5]]
