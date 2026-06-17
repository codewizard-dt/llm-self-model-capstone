---
id: vex-v5-clawbot-claw-autonomy
title: "Research: VEX V5 Clawbot Claw Autonomy"
aliases: [Clawbot Claw Autonomy, Clawbot Grip Detection]
updated: 2026-06-16
sources:
  - ../../raw/research/vex-v5-clawbot-claw-autonomy/index.md
tags: [source, vex-v5, clawbot, autonomy, claw, grip-detection, telemetry, motor-api]
---

# Research: VEX V5 Clawbot Claw Autonomy

A 2026-06-16 deep-dive into exactly how autonomous the standard Clawbot claw is: whether it has hardware force sensing, limit switches, or a built-in "spin until stall" API. **The claw has no hardware sensing whatsoever; the official curriculum programs it with a hard-coded degree count; and there is no `is_stalled()` API. Autonomous grip-on-contact requires ~3 lines of custom code using `set_max_torque()` + a long `spin_for()` + `set_timeout()`.** The grab task is mechanically trivial but telemetrically rich — the interesting signal for the [[llm-authored-self-model]] loop only appears if the program explicitly reads it. grounds::[[task-telemetry-contract]] relates_to::[[vex-v5]] relates_to::[[vexcode]]

## Hardware Reality

The standard Clawbot claw (276-6009-750 Rev6, 41-step build) uses **1× V5 Smart Motor 11W driving a 12T gear + 2× #32 rubber bands** for passive return. **No bumper switch, limit switch, force sensor, or proximity sensor is mounted on the claw.** The Classroom Starter Kit (276-7010) includes two 3-Wire Bumper Switches v2, but they are included for a separate sensor curriculum module — the standard 41-step Clawbot assembly does not route them to the claw.

## Official Curriculum Programming Pattern

VEX STEM Labs "Speedy Delivery" Lab 5 (Programming the Claw — Python) shows the canonical approach:

```python
claw_motor.set_position(0, DEGREES)
claw_motor.set_timeout(2, SECONDS)       # only guard: time-out, not stall-out
claw_motor.spin_for(FORWARD, 90, DEGREES)  # open
claw_motor.spin_for(REVERSE, 30, DEGREES)  # close
```

No object detection. No current/velocity monitoring. Students tune the degree value by trial and error. The curriculum challenge ("close the claw on an empty 12-ounce can without crushing the sides") is a manual calibration exercise, not an autonomous sensing exercise.

## Motor API: What Exists and What Doesn't

The VEXcode V5 motor API exposes rich telemetry but **no dedicated stall detection**:

| Category | Available |
|----------|-----------|
| Control | `spin()`, `spin_for()`, `spin_to_position()`, `spin_at_voltage()`, `stop()` |
| Config | `set_velocity()`, `set_max_torque()`, `set_stopping()`, `set_timeout()` |
| Sensing | `velocity()`, `current()`, `torque()`, `power()`, `position()` |
| Status | `is_spinning()` (bool), `is_done()` (bool) |
| **Missing** | ~~`is_stalled()`~~, ~~`spin_until_stall()`~~ |

`set_timeout()` is the only built-in stall protection — it stops the motor if a movement command isn't completed in time.

## Two Autonomous Grip Patterns

**Pattern A — polling loop (competition-style, ~10 lines):**
```python
claw_motor.spin(FORWARD, 50, PERCENT)
while claw_motor.velocity(RPM) > 5 or claw_motor.current(AMP) < 1.5:
    wait(10, MSEC)
claw_motor.stop(HOLD)
```

**Pattern B — torque-limit + long spin_for (3 lines, recommended for capstone):**
```python
claw_motor.set_max_torque(30, PERCENT)   # won't crush; still holds
claw_motor.set_timeout(3, SECONDS)
claw_motor.spin_for(FORWARD, 720, DEGREES)  # far more than claw range
# motor stops naturally on contact; position() readable immediately after
```

Pattern B produces a gentle "squeeze until contact" without a polling loop. The motor's 2.5 A hardware stall-current cap makes sustained grip safe. Object-size proxy: `claw_motor.position()` after grip (0.02° accuracy).

## Implication for the Capstone

**The naive `spin_for(N, DEGREES)` approach produces zero interesting telemetry** — the degree count is pre-baked, contact is not detected, and the self-model receives no feedback. **Pattern B surfaces `position()` as an object-size signal and `current()`/`torque()` as grip-force signals** — exactly the [[task-telemetry-contract]] `observed` block fields. Grip failure (empty claw hit the mechanical stop) is distinguishable by `position() > OPEN_THRESHOLD`. The capstone's difficulty lives in the LLM interpretation loop above the grip, which is the design intent.
