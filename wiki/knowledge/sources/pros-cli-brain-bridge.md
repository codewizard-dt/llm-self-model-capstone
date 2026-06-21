---
id: pros-cli-brain-bridge
title: Research: PROS CLI Workflow + The Exact Brain-Side C++ Bridge Program
updated: 2026-06-21
sources:
  - ../../raw/research/pros-cli-brain-bridge/index.md
tags: [source, pros, vex, cpp, serial, motor, cli, bridge, coprocessor, json]
---

# Research: PROS CLI Workflow + The Exact Brain-Side C++ Bridge Program

Research conducted 2026-06-21. Full report: `raw/research/pros-cli-brain-bridge/index.md`.

## PROS CLI — The Four-Command Workflow

**Install, create, build, and upload with four commands** (all on a laptop; the Pi never builds C++):

```bash
pip3 install pros-cli                    # install; Linux needs: sudo usermod -a -G dialout $USER
pros conduct new-project ./vexy-brain    # scaffold project with latest kernel
pros mu --slot 1                         # make + upload to slot 1 (most common shortcut)
pros terminal                            # stream printf output from the running program
```

`pros` and `prosv5` are interchangeable aliases. `pros upload --slot N` uploads to slot N (1–8); omitting `--slot` defaults to slot 1. The slot can be pinned in `project.pros` under `upload_options: {"slot": 1}` so bare `pros mu` always hits the right slot. Programs persist in their slot across power cycles.

**Critical operational constraint: `pros terminal` and the Pi's pyserial cannot both hold the user serial port simultaneously.** Close the PROS terminal (or VS Code's VEX Integrated Terminal) before running the Pi bridge. Failing to do this is a common gotcha and the terminal silently captures all data.

## Motor Translation — One API Call

The V5 Smart Motor runs its own hardware PID. **The Brain program does not compute voltages or control loops — it hands the motor a setpoint via `move_velocity(rpm)` and the motor achieves it:**

```cpp
left_drive.move_velocity(base + turn);    // PID holds this RPM
right_drive.move_velocity(base - turn);
```

RPM ceiling is gearset-dependent: **±200 for the stock 18:1 Clawbot drive**, ±600 for 6:1 (flywheel), ±100 for 36:1 (high-torque arm). Converting the Pi's normalized `vx` (−0.35…0.35) to RPM:

```cpp
int16_t base = (int16_t)(vx / MAX_LINEAR * DRIVE_MAX_RPM);    // 18:1 → 200 RPM
int16_t turn = (int16_t)(omega / MAX_OMEGA * DRIVE_MAX_RPM);
left_drive.move_velocity(base + turn);
right_drive.move_velocity(base - turn);
```

Other useful calls: `motor.brake()` (stop per brake mode), `motor.set_brake_mode(E_MOTOR_BRAKE_BRAKE)`, `motor.get_actual_velocity()`, `motor.get_temperature()`, `motor.get_current_draw()` (these last three are the telemetry fields that piggyback on acks).

## Two-Task Program Architecture

**The current single-loop `main.cpp` sketch has a latent safety bug: a blocked `getchar()` prevents the watchdog from firing.** Because PROS uses FreeRTOS with a preemptive 1ms tick, the fix is a second independent task:

- **Receive task**: reads `getchar()`, assembles lines, parses JSON, calls motor velocity API, updates `last_packet_ms`.
- **Watchdog task** (separate FreeRTOS task): runs every 10ms, checks `pros::millis() - last_packet_ms`; if over threshold, brakes all motors.

Because the scheduler is preemptive, the watchdog task runs even when the receive task is blocked on `getchar()`. The Pi disconnect → motors stop is now guaranteed.

```cpp
void opcontrol() {
    pros::Task r(receive_task,  nullptr, "rx");
    pros::Task w(watchdog_task, nullptr, "watchdog");
    while (true) pros::delay(1000);    // tasks do the work
}
```

## JSON Parsing — ArduinoJson

**Recommended parser: ArduinoJson** (header-only embedded library; drop `ArduinoJson.h` into `include/`). Use `StaticJsonDocument<256>` for stack allocation — avoids heap fragmentation at 50Hz command rates:

```cpp
StaticJsonDocument<256> doc;
if (deserializeJson(doc, line)) return;   // malformed → ignore
double vx = doc["vx"] | 0.0;
```

The Clawbot command packet is ~200–300 bytes; `StaticJsonDocument<256>` is sufficient. Avoid `DynamicJsonDocument` in a tight loop.

## Reference Port Map (Clawbot)

```cpp
constexpr int LEFT_PORT = 1, RIGHT_PORT = 10, CLAW_PORT = 3, ARM_PORT = 8;
pros::Motor left_drive(LEFT_PORT);
pros::Motor right_drive(RIGHT_PORT, true);   // true = reversed
pros::Motor claw(CLAW_PORT);
pros::Motor arm(ARM_PORT);
```

Confirmed from the official 276-6009-750 Rev6 build instructions wiring diagram.

relates_to::[[pros]]  
relates_to::[[vex-v5]]  
relates_to::[[vex-coprocessor-pattern]]  
relates_to::[[v5-brain-python-vs-pros]]  
relates_to::[[v5-user-programs]]  
relates_to::[[task-telemetry-contract]]
