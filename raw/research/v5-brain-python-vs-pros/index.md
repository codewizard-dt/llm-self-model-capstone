---
topic: V5 Brain program language choice — VEXcode Python (MicroPython) thin executor vs PROS C++ thin executor vs PROS C++ smart brain (LemLib trajectory)
slug: v5-brain-python-vs-pros
researched: 2026-06-21
sources: [./sources.md]
---

# Research: V5 Brain Program — Python vs PROS C++ (Both Sides)

> The capstone architecture (ARCHITECTURE.md) has already settled on a **thin-executor** role for the V5 Brain: the Pi does all planning, vision, and LLM inference; the Brain validates commands, clamps velocities, actuates motors, and stops safely on watchdog expiry. This report covers three candidate implementations of that role — VEXcode Python, PROS C++ thin executor, and PROS C++ with LemLib trajectory control — with equal treatment of each. The critical open empirical question is whether VEXcode Python's `sys.stdin.readline()` can receive data from the Pi over the USB user port; no community source confirms this.

---

## Research Questions

1. Can VEXcode Python (MicroPython 1.13) receive JSON commands from the Pi over the USB user serial port?
2. Does the VEXcode cooperative scheduler allow a watchdog thread to tick during a blocking `readline()` call?
3. What does the PROS C++ thin-executor pattern look like, and how confirmed is it in the community?
4. What does PROS C++ + LemLib (Smart Brain) add, and does the capstone need it?
5. What is the minimum empirical test to resolve the Python vs C++ question on physical hardware?

---

## Current State (Codebase)

The architecture is already split and documented:

**Pi side — fully built** (`robot/pi-runtime/`):
- `bridge.py`: TCP server that bridges planner → `FakeV5Brain` (sim) or `SerialV5Brain` (real hardware via pyserial). `SerialV5Brain.handle()` writes a JSON packet to serial and reads one back with a 0.4s timeout.
- `protocol.py`: Defines the wire format — newline-delimited UTF-8 JSON, fields `v/seq/type/cmd/ttl_ms`, commands `heartbeat/stop/drive/turn/set_goal`, max TTL 1000ms, velocity clamped to ±0.35 linear / ±0.60 omega.
- `PROTOCOL.md`: Formal spec including V5 response fields (`battery_mv`, `heading_deg`, `fault`).
- `ARCHITECTURE.md`: "System 1 (Brain) owns motors and timing. System 2 (Pi) owns camera capture and planning."
- `TOMORROW_BRINGUP.md`: Language-agnostic requirement — Brain must "read newline-delimited JSON from the user serial stream, validate and clamp commands, emit newline-delimited JSON acks, stop motors on stale heartbeat or expired command."

**V5 Brain side — starter sketch only** (`robot/v5-brain/pros_bridge/src/main.cpp`):
- PROS C++, explicitly labeled "not yet proven against the physical Brain"
- `serctl(SERCTL_DISABLE_COBS, nullptr)` in `initialize()`
- Single `opcontrol()` loop: `getchar()` char-by-char into a 512-byte line buffer, `handle_line()` on `'\n'`
- Handles: heartbeat (acks), stop (sets estop flag), drive (TODOs: parse vx/omega, command drivetrain)
- Watchdog: `pros::millis() - last_packet_ms > 250` → `stop_drive()`
- Motor ports not yet wired (all TODOs)

---

## Key Findings

### Branch A — VEXcode Python (MicroPython)

**What is confirmed:**

- VEXcode Python uses **MicroPython 1.13** with a **cooperative (not preemptive) scheduler**. Tasks must call `wait()` to yield; a blocked call prevents other threads from running [S1, S3].
- `print()` / `sys.stdout.write()` work for Brain→Pi telemetry — this is the established VEXcode Python output path [S1, S2].
- VEXcode Python has a `Thread` class. Threads are cooperative: `wait(N, MSEC)` yields [S5].
- `input()` built-in does **not** work in VEXcode Python [S6].
- MicroPython 1.13's `sys.stdin.readline()` **blocks until a newline** — it does not time out or yield [S7, S8].

**What is NOT confirmed:**

- Whether `sys.stdin.readline()` on the V5 Brain actually receives data sent from the Pi over the USB user port. All community examples of "Python reading from serial on V5" are Python running on the Pi (or computer) side, talking to the Brain's user port — **no source shows Python code running on the Brain receiving from the Pi** [S9, S10, S11].
- A VEX forum thread about `std::cin/scanf()` in VEXcode C++ reports "The brain supports it but I suspect the VEXcode console does not" [S6]. This is C++, not Python, but raises the same concern: **the VEXcode IDE console may intercept stdin before user programs see it**.
- Whether `uselect` module is available on VEX's MicroPython 1.13 port. `uselect.poll()` would allow non-blocking `stdin` reads with a timeout; standard MicroPython 1.13 includes it, but VEX's port is a custom build [S12].

**The watchdog problem:**

With a cooperative scheduler, if `sys.stdin.readline()` blocks waiting for a line:
- The watchdog thread does not tick during the block
- If the Pi disconnects while the Brain is inside `readline()`, the watchdog never fires
- The robot could remain in its last commanded state indefinitely

Two potential mitigations, both unconfirmed on VEX:
1. `uselect.poll(sys.stdin, timeout_ms=100)` — poll for available bytes before reading; if no bytes in 100ms, check watchdog. Requires `uselect` to be available AND `sys.stdin` to be poll-able.
2. A separate `Thread` with a `Brain.timer()` check — only works if the cooperative scheduler actually runs the thread while `readline()` blocks (unlikely; cooperative means it won't).

**What Python buys:**
- Simpler toolchain: VEXcode V5 app, single-file project, no separate build system
- Readable, maintainable code closer to the Pi-side Python
- Fast iteration: edit → download → run without PROS project setup
- For the thin executor role (parse JSON → set motor velocity → print ack), MicroPython speed is not the constraint; latency/correctness of stdin is

---

### Branch B — PROS C++ Thin Executor (current sketch)

**What is confirmed:**

- `serctl(SERCTL_DISABLE_COBS, nullptr)` disables COBS encoding on the console/user USB serial port. This makes `printf()` output plain newline-delimited text readable by pyserial on the Pi [S2, S13].
- `getchar()` / `fgets(stdin)` for receiving, `printf()` + `fflush(stdout)` for sending — bidirectional JSON over USB serial is **community-confirmed** by multiple VEX AI teams [S2, S13, S14].
- PROS uses **FreeRTOS with a preemptive 1ms-tick scheduler**. A separate watchdog task will preempt the serial reader regardless of whether `getchar()` is blocking [S15].
- The VAIC reference architecture (VEX's official AI competition framework) uses PROS C++ on the Brain with this exact pattern [S16].
- Real-world pattern: two separate PROS tasks — one sends data (telemetry out), one receives (commands in). When a single combined task blocks on `getchar()` it can't send; splitting avoids the deadlock [S13].
- The current `main.cpp` sketch already has the right structure: `initialize()` calls `SERCTL_DISABLE_COBS`, `opcontrol()` has the receive loop with `pros::delay(10)` yielding, and the watchdog via `pros::millis()`.

**What PROS C++ costs:**
- Toolchain complexity: PROS CLI install, PROS project template, separate C++ build system
- C++ verbosity: more boilerplate for JSON parsing (no stdlib JSON in PROS; need hand-rolled or a tiny header-only lib like `ArduinoJson` ported to PROS)
- The current sketch hand-rolls JSON with `line.find()` — fragile for a real protocol. A minimal JSON parser is needed.
- Cannot use VEXcode Python debugging tools alongside PROS

**Watchdog reliability:**
- In PROS C++, the watchdog check in `opcontrol()` at `pros::millis() - last_packet_ms > WATCHDOG_MS` works even if `getchar()` returns `EOF` immediately on disconnect
- A higher-reliability pattern: separate FreeRTOS task at high priority that checks `pros::millis()` and calls `stop_drive()` — preempts the receive task immediately

---

### Branch B variant — PROS C++ Smart Brain (LemLib)

**What LemLib adds:**
- Odometry: continuous pose estimation (x, y, heading) from wheel encoders + IMU
- Outer PID trajectory control: `chassis.moveToPose(x, y, theta)`, `chassis.follow(path)` (pure pursuit)
- Changes the command protocol: Pi sends goal poses instead of velocity vectors; Brain autonomously navigates to them

**What it requires:**
- V5 Inertial Sensor (IMU) — not included in the base Starter Kit, must be purchased separately (~$40)
- LemLib installed as a PROS template: `pros conductor fetch LemLib`
- Odometry configuration: track width, wheel diameter, IME vs tracking wheel choice
- Tuning: PID gains must be empirically tuned for each robot configuration (and re-tuned on every morphology change)

**Fit with the capstone:**
- The current protocol sends `vx/omega` (velocity vectors), not poses — LemLib would require a protocol redesign
- The self-model loop benefits from richer gap residuals (position error vs. pose goal) rather than just velocity/torque
- BUT: adds significant hardware cost, tuning complexity, and protocol complexity
- The thin executor already captures the most important telemetry: per-motor `position/velocity/torque/current` from the hardware inner PID — the gap the LLM needs is already present without LemLib
- LemLib is optimized for VRC autonomous navigation on a fixed field; the capstone's manipulation tasks (grab, pull, throw) are single-motor actions that don't need pose-level trajectory control

**Verdict on LemLib:** Out of scope for the thin-executor architecture. Worth revisiting if the capstone adds navigation tasks requiring repeatable field positioning.

---

## Constraints

Any Brain program must:
1. Read newline-delimited JSON from the USB user port (Pi → Brain)
2. Write newline-delimited JSON acks back (Brain → Pi)
3. Enforce TTL expiry: stop if `ttl_ms` elapsed since command recv
4. Enforce watchdog: stop if no heartbeat/command for 250ms
5. Clamp velocities (already done in Pi-side `protocol.py`; Brain should double-clamp for safety)
6. Be uploadable via VEXcode or PROS CLI without a connected Pi

---

## Solution Comparison

| Criteria | A: VEXcode Python | B: PROS C++ Thin Executor | B+: PROS C++ + LemLib |
|---|---|---|---|
| **Stdin confirmed working** | ❌ Unconfirmed — no community example of Brain receiving from Pi in Python | ✅ Confirmed — multiple VAIC teams, SERCTL_DISABLE_COBS + getchar() | ✅ Same as B |
| **Watchdog reliability** | ⚠️ Risk: cooperative scheduler may not tick watchdog thread during blocking readline() | ✅ FreeRTOS preemptive; watchdog task never starved | ✅ Same as B |
| **Toolchain complexity** | Low — VEXcode V5 app, single file | Medium — PROS CLI, project template, C++ build | High — PROS + LemLib template + IMU hardware |
| **Code maintainability** | High — Python, readable | Medium — C++, more boilerplate | Low — complex PID tuning, odometry config |
| **JSON parsing** | Medium — `ujson` available in MicroPython | Low — hand-rolled string search OR need tiny lib | Low — same as B |
| **Speed concern** | None — 50Hz thin executor, not compute-bound | None | None |
| **Protocol changes needed** | None — already fits vx/omega | None — fits vx/omega | Yes — requires pose commands |
| **Hardware additions** | None | None | IMU sensor ~$40 |
| **Community precedent** | None for Brain-side receive | Strong (VAIC, multiple teams) | Strong for competition, not for capstone pattern |
| **Iteration speed** | Fast | Medium | Slow |

---

## Critical Open Question

**Can VEXcode Python's `sys.stdin.readline()` receive data from the Pi?**

This is a binary empirical question resolvable with a 10-minute physical test when the Brain arrives:

```python
# Upload this to the Brain as a VEXcode Python project
import sys
from vex import *
brain = Brain()
while True:
    line = sys.stdin.readline()
    if line:
        sys.stdout.write('got:' + line)
```

Send a line from the Pi: `echo '{"test":1}' > /dev/ttyACM1`

- If the Brain echoes it back → Python stdin reading works → Branch A is viable
- If nothing comes back → VEXcode console intercepts stdin → PROS C++ is needed

---

## Recommendation (as research, not decision)

**PROS C++ thin executor (Branch B) is the lower-risk path** because bidirectional USB serial is community-confirmed, the watchdog is reliable with FreeRTOS, and the current sketch already implements the right structure.

**VEXcode Python (Branch A) is viable if stdin works** — and the toolchain and iteration advantages are real. The Python path is not ruled out by any confirmed fact; it is only blocked by an untested question about whether VEXcode exposes stdin to user programs.

**The recommended scoping approach:**
1. On first physical bringup, run the 10-line Python stdin test above before committing to either path
2. If Python stdin works: consider Branch A for the thin executor — it's simpler and keeps the codebase in one language
3. If Python stdin doesn't work: Branch B (current sketch) is ready to extend — add motor port config and a minimal JSON field extractor
4. Branch B+ (LemLib) is not needed for the thin executor role; revisit only if navigation tasks are added

---

## Next Steps

- **Empirical test** (highest priority): test Python stdin reading on physical V5 Brain before choosing a language
- To create a task for physical bringup: `/task-add V5 Brain first bringup — verify serial echo and motor ports`
- To document the architecture choice once confirmed: `/decision-create V5 Brain program language — Python vs PROS C++`
- If PROS C++: extend `main.cpp` to wire motor ports, add a minimal JSON field parser for `vx`/`omega`, split into send/receive tasks
- If Python: write `robot/v5-brain/python_bridge/main.py`, verify `uselect` availability for non-blocking stdin, validate watchdog behavior
