---
id: pid-control-research
title: Research: What Is PID Control?
updated: 2026-06-16
sources:
  - ../../raw/research/pid-control/index.md
tags: [research, pid, control-theory, vex-v5, robotics, concept]
---

# Research: What Is PID Control?

Research conducted 2026-06-16. Full report: `raw/research/pid-control/index.md`. Primary sources: `raw/research/pid-control/sources.md`.

## The Three Terms

relates_to::[[pid-control]] (Proportional-Integral-Derivative) is a feedback control loop that computes an error `e(t) = setpoint − measured_value` and outputs a corrective signal:

```
u(t) = Kp·e(t)  +  Ki·∫e(τ)dτ  +  Kd·(de/dt)
```

**P** responds to the *current* error — large error → large correction; eliminates rise time but leaves a steady-state offset because the correction approaches zero as the error does. **I** accumulates *past* error over time, building up force until that offset vanishes — the "memory" term. **D** looks at the *rate of change* of error and acts as a brake, preventing overshoot by opposing fast approaches to the setpoint.

Tuning sequence for relates_to::[[vex-v5]] robots (Purdue SIGBots / VEX community): raise Kp until oscillation, add Kd to damp it, add small Ki only to fix static-friction stall near the target. Gains are robot-specific (weight, friction, gear ratio all matter) — re-tune whenever morphology changes.

## V5 Smart Motor Internal PID

**Critical capstone fact**: every V5 Smart Motor contains its own Cortex M0 microcontroller running a **hardware PID loop** for velocity, position, torque, and feedforward. This inner loop closes at hardware speed — user code commands are *setpoints* fed to this inner loop, not direct motor voltages. The telemetry API (`motor.torque()`, `motor.velocity()`, `motor.position()`) exposes the *output* of this inner loop: what was actually achieved, which may differ from what was commanded.

This creates a **two-level PID architecture** in the capstone: (1) inner hardware PID inside each V5 motor (automatic, always active); (2) outer software PID in user code for trajectory control (relates_to::[[lemlib]] implements this for drivetrain distance + heading). The inner loop runs at hardware speed; the outer loop runs at 20 ms intervals in user code.

## Integral Windup — The Key Failure Mode

If the system is blocked (motor stalls against a wall, arm hits a hard stop), the integral term keeps accumulating while the error persists — "winding up." When the block is removed, the huge accumulated integral causes wild overshoot and oscillation. **Fix**: clamp the integral to ±max_integral, or use zone activation (only enable I when within N units of target — e.g., "within 10 degrees").

## Gap Residuals as PID Evidence

The relates_to::[[task-telemetry-contract]] gap block captures PID output residuals, which are evidence about unmodeled physics:
- **Position deficit** (observed < predicted) → underestimated friction or overestimated torque budget
- **Torque saturation** (observed ≈ 2.1 Nm stall) → load exceeded capability prediction
- **Velocity overshoot** (observed > predicted) → inertia lower than modeled

The LLM self-model reads these residuals to revise exactly the physical parameter (moment arm, gear ratio, mass, friction coefficient) that caused the discrepancy.

derived_from::[[research-pid-control]]  
relates_to::[[pid-control]]  
relates_to::[[vex-v5]]  
relates_to::[[lemlib]]  
relates_to::[[task-telemetry-contract]]  
relates_to::[[llm-authored-self-model]]
