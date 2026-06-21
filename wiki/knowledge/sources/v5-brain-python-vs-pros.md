---
id: v5-brain-python-vs-pros
title: Research: V5 Brain Program — Python vs PROS C++ (Both Sides)
updated: 2026-06-21
sources:
  - ../../raw/research/v5-brain-python-vs-pros/index.md
tags: [source, vex, vexcode, pros, micropython, serial, architecture, brain, coprocessor]
---

# Research: V5 Brain Program — Python vs PROS C++ (Both Sides)

Research conducted 2026-06-21. Full report: `raw/research/v5-brain-python-vs-pros/index.md`. Sources register: `raw/research/v5-brain-python-vs-pros/sources.md`.

## Architecture Is Already Settled as Thin-Executor

The codebase's `robot/pi-runtime/docs/ARCHITECTURE.md` formally establishes the split: **System 1 (Brain) owns motors and timing; System 2 (Pi) owns camera capture and planning.** The language question is solely about implementing a thin executor — parse JSON commands from the Pi, relay setpoints to the motors' built-in PID, send acks, and stop safely on watchdog expiry. No outer trajectory PID is required by this role; the V5 Smart Motors run hardware PID internally.

## Branch A — VEXcode Python (MicroPython)

**Confirmed:** `print()` / `sys.stdout.write()` work for Brain→Pi output. The `Thread` class exists but the scheduler is **cooperative** — threads must call `wait()` to yield. `input()` does not work. `sys.stdin.readline()` blocks until a newline and does not time-out or yield.

**Unconfirmed and the critical risk:** Whether `sys.stdin.readline()` on the V5 Brain actually receives data sent by the Pi over the USB user port. No community source shows Python code *running on the Brain* receiving from a Pi — all bidirectional Python examples have Python on the Pi side. A VEX forum thread about `std::cin/scanf()` in VEXcode C++ reports "The brain supports it but I suspect the VEXcode console does not," raising the same concern for Python.

**Watchdog problem:** With the cooperative scheduler, if `readline()` blocks while waiting for a packet, the watchdog thread does not tick. If the Pi disconnects mid-wait, the robot never stops. `uselect.poll()` with a timeout could mitigate this, but `uselect` availability on VEX's custom MicroPython 1.13 port is unconfirmed.

**What Python buys:** simpler toolchain (VEXcode app, single file, no build system), fast iteration, same language as Pi-side code, readable.

## Branch B — PROS C++ Thin Executor

**Confirmed by the community:** `serctl(SERCTL_DISABLE_COBS, nullptr)` disables COBS encoding on the USB user port, making `printf()` output plain newline-delimited text. `getchar()`/`fgets(stdin)` for receiving and `printf()`/`fflush(stdout)` for sending — **bidirectional JSON is confirmed** by multiple VEX AI competition teams and is the pattern in the official VAIC reference architecture (VEX-Robotics/VAIC_23_24 and VAIC_24_25).

**Preemptive scheduler:** PROS uses FreeRTOS with a 1ms preemptive tick. A watchdog task at high priority will preempt the serial reader regardless of whether `getchar()` is blocking. Real-world teams hit deadlocks when combining send and receive in a single task and moved to two separate PROS tasks (one for commands-in, one for telemetry-out).

**What PROS costs:** PROS CLI toolchain, C++ verbosity, no stdlib JSON parser (current sketch hand-rolls `line.find()`), cannot share VEXcode debugging tools.

## Branch B+ — PROS C++ + LemLib (Smart Brain)

Adds odometry (x/y/heading) and outer PID trajectory control (`chassis.moveToPose()`). **Out of scope for the thin executor:** requires a V5 Inertial Sensor (~$40, not in base Starter Kit), a protocol redesign (Pi sends goal poses instead of velocity vectors), and PID re-tuning every time the robot morphology changes. The Task Telemetry Contract already captures per-motor position/velocity/torque from the hardware inner PID — the LLM self-model loop has the gap residuals it needs without LemLib.

## Resolution Test

A **10-minute empirical test** on first physical bringup resolves the Branch A/B question:

```python
# Upload to Brain as VEXcode Python project
import sys
from vex import *
brain = Brain()
while True:
    line = sys.stdin.readline()
    if line:
        sys.stdout.write('got:' + line)
```

`echo '{"test":1}' > /dev/ttyACM1` from the Pi. Echo received → Python viable. No response → PROS C++ required.

relates_to::[[research-vexcode-python-vs-cpp]]  
relates_to::[[research-vex-v5-advanced-toolchains]]  
relates_to::[[vex-coprocessor-pattern]]  
relates_to::[[pid-control]]  
uses::[[pros]]  
uses::[[vexcode]]  
uses::[[lemlib]]
