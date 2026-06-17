---
topic: "exactly how autonomous the claw is for the VEX V5 Clawbot — does it have force sensing, position feedback, limit switches, or auto-stop on stall? Can it detect when it has gripped an object, or must the driver/program explicitly control open/close timing?"
slug: vex-v5-clawbot-claw-autonomy
researched: 2026-06-16
sources: [./sources.md]
---

# Research: VEX V5 Clawbot Claw Autonomy

> The standard Clawbot claw has **no hardware force sensing, no limit switches, and no auto-stall detection** — just a motor encoder. The official curriculum programs it with a fixed `spin_for(DIRECTION, N, DEGREES)` call; the programmer hard-codes how many degrees to close. An advanced programmer CAN implement a "spin-until-stall" pattern by polling `velocity()` and `current()` in a loop (no dedicated API call exists for it), or use `set_max_torque()` + a long `spin_for` + timeout as a simpler workaround. Neither is provided out of the box. The grab task is physically trivial to execute but **not autonomously self-detecting** — the rich telemetry (position, torque, current) only becomes observable signal if the program is written to read it.

---

## Research Questions

1. Does the standard Clawbot claw have hardware force sensing, limit switches, or bumper switches mounted on it?
2. Does VEXcode V5 provide a built-in "spin until stall" API, or must the programmer implement it?
3. What is the default/canonical way to program claw open/close in the official curriculum?
4. Can grip success (object contacted) be detected programmatically, and if so, how?
5. Does the kit include any sensors that could be added to the claw for object detection?

---

## Current State (Codebase)

Existing wiki source `vex-v5-customization-grab-pull-throw.md` already documents the motor telemetry API and states the stall-detect heuristic: `velocity < 5 RPM AND current > 1.5 A → gripped boolean`. That page treats this as an achievable software pattern. This report confirms the hardware/API substrate behind that claim and documents exactly what is and isn't built-in.

---

## Key Findings

### 1. No hardware sensing on the claw [S1, S2, S3]

The standard Clawbot build (VEX 276-6009-750 Rev6) uses:
- 1× V5 Smart Motor 11W driving a 12T gear on the claw fingers
- 2× #32 rubber bands for passive-return (spring open when motor relaxes)
- **No bumper switch, limit switch, force sensor, or proximity sensor** mounted on the claw

The Classroom Starter Kit (276-7010) **does include** two 3-Wire Bumper Switches v2, but they are **not part of the standard Clawbot assembly** — they are included for the sensor curriculum lessons as a separate add-on exercise. The 41-step build guide does not route them to the claw. [S3]

### 2. Canonical programming is pure degree-based positioning [S4]

The official VEX STEM Labs "Speedy Delivery" Lab 5 (Programming the Claw — Python) shows exactly:

```python
claw_motor.set_position(0, DEGREES)
claw_motor.set_timeout(2, SECONDS)       # only safety: time-out, not stall-out
claw_motor.spin_for(FORWARD, 90, DEGREES)  # open
claw_motor.spin_for(REVERSE, 30, DEGREES)  # close
```

No object detection. No current monitoring. The timeout is the only guard — if the motor doesn't complete in 2 seconds it gives up. The curriculum challenge ("close the claw on an aluminum can without crushing the sides") requires students to manually tune the degree value by trial and error. [S4]

### 3. No dedicated stall-detect or "spin-until-contact" API [S5, S6]

The VEXcode V5 motor/motor-group API exposes:
- **Control**: `spin()`, `spin_for()`, `spin_to_position()`, `spin_at_voltage()`, `stop()`
- **Config**: `set_velocity()`, `set_max_torque()`, `set_stopping()`, `set_timeout()`
- **Sensing**: `velocity()`, `current()`, `torque()`, `power()`, `position()`, `efficiency()`, `temperature()`
- **Status**: `is_spinning()` → bool (currently rotating), `is_done()` → bool (movement command complete)

There is **no `is_stalled()` method** and **no `spin_until_stall()` command**. The `set_timeout()` mechanism is the only built-in protection against indefinite stall. [S5]

### 4. Grip detection IS possible with custom code — two patterns [S5, S6, S7]

**Pattern A — polling loop (competition-style):**
```python
claw_motor.spin(FORWARD, 50, PERCENT)
while claw_motor.velocity(RPM) > 5 or claw_motor.current(AMP) < 1.5:
    wait(10, MSEC)
claw_motor.stop(HOLD)   # gripped
```
This mirrors what `vex-v5-customization-grab-pull-throw.md` describes. It is a well-known VEX competition pattern but requires explicit custom code; ~10 lines of Python.

**Pattern B — torque-limit + long spin_for + timeout (simpler):**
```python
claw_motor.set_max_torque(30, PERCENT)   # low enough to not crush; high enough to hold
claw_motor.set_timeout(3, SECONDS)
claw_motor.spin_for(FORWARD, 720, DEGREES)  # far more than needed
# motor naturally stops when it hits the object (torque-limited stall)
# spin_for completes at timeout if no object found
```
This produces a gentle "squeeze until contact" without a polling loop. The timeout acts as the failure mode. Object position is then read from `claw_motor.position()`.

### 5. Motor encoder gives excellent object-size proxy [S6]

Position accuracy is **0.02 degrees**. If the claw is zeroed (fully open = 0°), then `claw_motor.position()` after grip tells the controller exactly how far it closed — directly mapping to the gripped object's diameter. This is the "object width proxy" in the Task Telemetry Contract.

### 6. Stall current is hardware-capped at 2.5 A [S7]

The V5 Smart Motor's internal controller limits stall current to 2.5 A regardless of program commands. This means neither Pattern A nor B will damage the motor from sustained grip — the motor is safe to leave against a load.

---

## Constraints

Any grip-detect solution must work with:
- 1× V5 Smart Motor 11W, 18:1 cartridge (200 RPM no-load), 12T gear train
- Rubber-band return force (claw springs open when motor stops/coasts)
- No 3-wire ports consumed by the standard Clawbot build (bumper switches could be added on free 3-wire ports of the Brain)
- VEXcode V5 Python API (MicroPython on ZYNQ; 10 ms PID loop)

---

## Solution Comparison

| Approach | Mechanism | Autonomy Level | Custom Code | Object Size Proxy | Crush Risk |
|----------|-----------|---------------|-------------|------------------|------------|
| A. Fixed degrees (default) | `spin_for(N, DEGREES)` | None — blind | 1 line | Indirect (pre-tuned) | Must tune per object |
| B. Polling loop | Poll velocity + current | High | ~10 lines | Yes — `position()` after stop | Low (stop on contact) |
| C. Torque-limit + timeout | `set_max_torque()` + long `spin_for()` | Medium | 3 lines | Yes — `position()` after stop | Very low (torque capped) |
| D. Bumper switch on claw | Mount 3-wire switch inside fingers | High (hardware) | 2 lines | Coarse (binary contact) | None |

**Option D** (adding a bumper switch) is the most reliable hardware approach. The Starter Kit even includes the switches; they just need to be physically mounted on the claw fingers. However this changes the robot's morphology beyond the standard build.

---

## Recommendation

For the capstone's Task Telemetry Contract, **Pattern C (torque-limit + long spin_for)** is the right default autonomous grip:
- 3 lines of code, no polling loop
- Motor stops naturally on contact; position is read afterward
- Current and torque telemetry are still readable post-grip
- No added hardware

The **autonomy level is medium**: the program can grip any object without knowing its size in advance, and can detect grip via final position. What it **cannot** do without extra code is distinguish "successfully gripped a 50 g object" from "gripped nothing and hit the mechanical stop" — that distinction requires comparing final position against the expected open position (trivial: `if claw_motor.position() > 5: # something was gripped`).

**The grab task is NOT "too easy" for the capstone** in the sense that the interesting signal is the telemetry, not the mechanical action:
- The naive implementation (fixed degrees) produces zero interesting telemetry for the self-model
- The torque-limit approach surfaces `position()` as object-size signal and `current()` / `torque()` as grip-force signal
- Grip failure (object slipped, missed, or not present) is detectable but requires the program to check
- The gap between "predicted grip position" and "observed grip position" is the residual the LLM reads to revise the self-model's capability estimates

The capstone's novelty is in the LLM interpreting this telemetry loop — the mechanical grip itself is straightforward by design.

---

## Next Steps

- No new hardware needed for the base grab telemetry loop — Pattern C uses the standard Clawbot as-is
- `/task-add` a task to implement Pattern C in the capstone's autonomous grab primitive and wire `position()` + `current()` readings into the Task Telemetry Contract `observed` block
- If finer grip control is needed later, mount one of the included bumper switches inside the claw fingers (Option D) — no purchase required
