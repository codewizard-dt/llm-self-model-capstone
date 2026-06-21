---
topic: How do V5 user programs work, how do competition teams control the robot, and can the RPi send motor commands without a pre-loaded Brain program?
slug: v5-user-programs
researched: 2026-06-21
sources: [./sources.md]
---

# Research: V5 User Programs — Why They're Mandatory and How Simple They Can Be

> **Short answer: No, you cannot skip the user program. The RPi cannot send motor commands directly to the V5 Brain without a program already running on it.** V5 Smart Motors use a proprietary RS-485 protocol the RPi cannot speak, and the Brain's USB port carries nothing useful without a running program. However, the user program required is trivially simple for the capstone's Pi-first architecture — a bare `while True` loop reading serial and calling motor APIs. Competition-style `autonomous()`/`opcontrol()` splits are irrelevant; without a competition switch the main loop just runs. The program is uploaded once and triggered from the Brain's touchscreen.

---

## Research Questions

1. Why does a user program need to run on the Brain — what exactly does it do that can't be bypassed?
2. Can the RPi ever control V5 motors directly (via any USB or RS-485 path) without a Brain program?
3. How do competition teams structure their programs, and is any of that structure relevant for the capstone?
4. How minimal can the "user program" be for a Pi-first coprocessor architecture?
5. How is a user program uploaded and triggered, outside of a competition environment?

---

## Current State (Codebase)

- `robot/v5-brain/pros_bridge/src/main.cpp` — PROS C++ starter sketch: `initialize()` sets up SERCTL_DISABLE_COBS; `opcontrol()` is the main serial receive loop. This is exactly the minimal-program pattern.
- `robot/pi-runtime/docs/ARCHITECTURE.md` — "System 1 runs on the V5 Brain. Owns motors and timing."
- `robot/pi-runtime/docs/TOMORROW_BRINGUP.md` — specifies Brain must "read newline-delimited JSON from the user serial stream" — implies program running and listening.

---

## Key Findings

### 1. Why you cannot bypass the user program

**V5 Smart Motors communicate via a proprietary RS-485 protocol at high baud rates that the RPi cannot speak.** [S1, S2] When a V5 Brain powers on, VEXos loads firmware to each connected Smart Motor over the Smart Port RS-485 bus. The motor then responds only to commands from the Brain using this proprietary protocol. No publicly documented API or library allows an external device to control V5 Smart Motors without the Brain managing the RS-485 link.

**The Brain exposes two USB serial ports when connected to a host; neither allows motor control without a running user program:** [S3]
- **System port** (`/dev/ttyACM1` typically): used by VEXcode and PROS CLI to upload programs, list files, query Brain status. The V5 Serial Protocol this port uses supports program management commands (upload, run, stop, list) — **not real-time motor commands**.
- **User port** (`/dev/ttyACM0` typically): carries stdio (`print()`/`printf()` output) from a **running user program** only. "If you try to communicate with the Brain over the user port nothing will happen" without a program running. [S3]

Even the system port cannot be used for motor control — the V5 Serial Protocol only handles program upload and Brain management. No packet type in the documented protocol sends motor setpoints. [S3]

**Conclusion: A user program is structurally mandatory.** There is no path — USB, RS-485, or otherwise — that allows an external device to command V5 motors without a program running on the Brain.

### 2. What the user program actually does

The user program is the **translation layer** between the RPi's high-level commands and the motor's proprietary RS-485 protocol:

```
RPi (Python, full stack) → serial JSON → User Port → User Program → VEXos motor API → RS-485 → Smart Motor
```

The user program does not need to be sophisticated. For the thin-executor architecture, it just needs to:
1. Read newline-delimited JSON from serial (stdin)
2. Parse command type and parameters
3. Call `motor.spin(vx)` / `motor.stop()` (or equivalent)
4. Write a JSON ack to stdout
5. Stop motors if no command arrives for >250ms (watchdog)

This is 50–100 lines of code.

### 3. Competition structure — what teams do and what applies to the capstone

**Competition programs have three entry points:** [S4, S5]
- `initialize()` — runs on startup, always, regardless of competition state
- `autonomous()` — triggered by the Field Management System (FMS) or Competition Switch for the 15-second autonomous period
- `opcontrol()` / `competition_initialize()` — triggered by FMS for driver control; also runs a human controller (V5 Controller joystick) for the 1:45 driver control period

**The critical non-competition behavior:** [S4, S5]

> "If no competition control is connected, this function will run immediately following initialize()."

Without a Competition Switch or FMS connected to the Brain's competition port, `opcontrol()` runs immediately after `initialize()`. **For the capstone, no competition infrastructure is needed.** The program is just `initialize()` + a main loop in `opcontrol()`.

**Competition teams write programs in advance** because:
- Autonomous period requires pre-programmed behavior (no human input allowed)
- Teams tune PID gains, record paths, test routines — all offline
- The competition switch triggers the correct phase automatically at match time

**None of this applies to the capstone.** There is no autonomous/teleop split, no competition switch, no FMS. The capstone program is just a command loop.

### 4. How minimal the user program can be (for the capstone)

The absolute minimum that satisfies the capstone's needs:

```cpp
// PROS C++
void initialize() {
    serctl(SERCTL_DISABLE_COBS, nullptr);
}

void opcontrol() {
    // configure motors
    pros::Motor left(1), right(10, true);
    uint32_t last_cmd_ms = pros::millis();
    std::string line;
    while (true) {
        int ch = getchar();
        if (ch != EOF && ch != '\n') { line.push_back(ch); }
        else if (ch == '\n') {
            // parse line, call left.move_velocity() / right.move_velocity()
            last_cmd_ms = pros::millis();
            printf("{\"ack\":\"ok\"}\n"); fflush(stdout);
            line.clear();
        }
        if (pros::millis() - last_cmd_ms > 250) {
            left.brake(); right.brake();
        }
        pros::delay(5);
    }
}
```

That's it. No autonomous. No competition switch handling. One loop.

The Python equivalent (if `sys.stdin.readline()` works on Brain — unconfirmed) is even shorter:
```python
from vex import *
import sys, ujson
left = Motor(Ports.PORT1)
right = Motor(Ports.PORT10, True)
while True:
    line = sys.stdin.readline()
    if line:
        cmd = ujson.loads(line)
        if cmd.get('cmd') == 'drive':
            left.spin(FORWARD, cmd['vx'], PERCENT)
        print('{"ack":"ok"}')
```

### 5. Uploading and running a program outside competition

**Upload:** Connect Brain to Mac/PC via USB → VEXcode (or PROS CLI `pros upload`) → choose slot 1–8. Takes ~5–15 seconds. Once uploaded, stays in the slot permanently (survives power cycles).

**Run:** Power on Brain → tap the slot on the touchscreen → program runs until manually stopped or power cut. No computer connection needed at runtime.

**Trigger from Brain's own V5 Controller** (alternative): Controller can select and start programs wirelessly.

**Auto-run on boot** (if needed): some PROS projects can be configured to auto-start on power-up, but this requires additional configuration.

**The built-in "Drive program":** VEXos includes a pre-loaded program that maps V5 Controller joysticks to motor ports — usable without any user-uploaded code. However, this only works with the physical V5 Controller. It does not expose a serial interface. **This does not help the capstone.** [S6]

---

## Constraints

1. A user program must be uploaded to the Brain before the Pi can send any commands
2. The program must be running (slot selected and started from Brain touchscreen) for the user port to carry data
3. No competition switch or FMS needed for non-competition use
4. Motor port assignments must be known at program-write time (or configurable via serial on startup)
5. Program upload requires USB cable + host computer running VEXcode or PROS CLI — not the Pi's pyserial

---

## Solution Comparison

| Question | Answer |
|---|---|
| Can RPi control motors without a user program? | **No.** V5 motors use proprietary RS-485; system port only handles program management; user port is inert without running program. |
| Does the program need competition structure (auto/teleop split)? | **No.** Without competition switch, opcontrol() runs immediately. One loop is enough. |
| How complex does the user program need to be? | **Minimal.** 50–100 lines — parse serial JSON, call motor API, send ack, run watchdog. |
| How is the program loaded and started? | Upload once via USB + VEXcode/PROS CLI. Start by tapping slot on Brain touchscreen. |
| Can the RPi start/stop the program? | Not via the user port. Theoretically via the system port (V5 Serial Protocol `run` command), but this is a dev tooling interface, not a production control path. |
| Does the program survive power cycles? | **Yes.** Programs stay in their slot permanently. |

---

## Recommendation (as research, not decision)

**The user program is non-negotiable — accept it, minimize it.** The capstone needs exactly one tiny program on the Brain: a loop that reads serial commands and relays them to motors. Write it once, upload it once, run it from the touchscreen at the start of a session.

**For non-competition use, ignore all competition structure.** No `autonomous()`. No competition switch. Just `initialize()` + a main loop in `opcontrol()` (PROS) or a plain `while True` (Python).

**The workflow is:**
1. Upload the Brain program once (via laptop + USB)
2. At the start of each session: power on Brain → tap slot → run
3. Pi connects via serial and starts sending commands

**This is exactly what the current `main.cpp` sketch does.** It needs motor port wiring and `vx`/`omega` JSON parsing added — both are a couple of hours of work, not an architectural decision.

---

## Next Steps

- Resolve the Python vs PROS language choice (see `raw/research/v5-brain-python-vs-pros/index.md` — the 10-minute stdin test resolves this on first bringup)
- Add motor port constants and `vx`/`omega` parsing to `main.cpp`
- Define which Brain slot the program lives in (slot 1 suggested — easiest to reach on touchscreen)
- Consider: should program auto-start on Brain boot? (PROS supports this but requires config)
- To create a task: `/task-add V5 Brain program — wire motor ports and complete JSON parsing`
