---
id: pid-control
title: PID Control (Proportional-Integral-Derivative)
aliases: [PID, PID controller, P controller, PI controller, PD controller]
updated: 2026-06-16
sources:
  - ../../raw/research/pid-control/index.md
tags: [concept, control-theory, pid, robotics, vex-v5]
---

# PID Control (Proportional-Integral-Derivative)

A feedback control algorithm that continuously computes an error `e(t) = setpoint − measured_value` and applies a corrective output that is the weighted sum of three terms:

```
u(t) = Kp·e(t)  +  Ki·∫₀ᵗ e(τ)dτ  +  Kd·(de/dt)
```

It is the most widely used control algorithm in industrial and robotics systems. Variants: P-only, PI, PD, PID (all three terms).

## The Three Terms

| Term | Formula | What it corrects | Failure if over-tuned |
|------|---------|-----------------|----------------------|
| **P** (Proportional) | `Kp · e(t)` | Current error; reduces rise time | Oscillation (too much Kp) |
| **I** (Integral) | `Ki · ∫e(τ)dτ` | Accumulated past error; eliminates steady-state offset | Integral windup (accumulated while blocked) |
| **D** (Derivative) | `Kd · (de/dt)` | Rate of change of error; damps overshoot | Noise amplification (differentiates noisy signal) |

**Intuitive summary**: P drives position error to zero; D drives velocity error to zero; I drives accumulated error to zero.

## Mathematics (Discrete Form)

For digital implementation at sample period Δt:
```
u[n] = Kp·e[n] + Ki·Δt·Σe[k] + Kd·(e[n] - e[n-1])/Δt
```

Standard VEX V5 control loops run at **20 ms** intervals (50 Hz).

## Tuning Sequence (VEX V5)

1. Set Ki = 0, Kd = 0. Raise **Kp** until the robot reaches the target with slight oscillation.
2. Add **Kd** to dampen oscillation. Stop when the system settles cleanly.
3. Add small **Ki** only if static friction prevents reaching the target. Pair with integral clamp.

Gains are **robot-specific** — weight, friction, gear ratio, and inertia all change them. Re-tune whenever morphology changes (a new arm or end-effector may require completely different Ki/Kd).

## Failure Modes

**Integral windup** (most common): if the system is blocked for an extended time (motor stalls, arm hits a hard stop), the integral accumulates to a huge value. When unblocked, wild overshoot and oscillation occur.  
**Fix options**: (1) **Clamp** the integral term to ±max_integral; (2) **Zone activation** — only enable I when within N units of the target (e.g., "only when within 10 degrees").

**Overshoot**: Kp too high or Kd too low. Fix: increase Kd, decrease Kp.

**Derivative noise amplification**: D takes the derivative of sensor readings, amplifying noise. Fix: apply a low-pass filter to the derivative term, or use a filtered velocity measurement.

## PID in VEX V5 Smart Motors

**Every V5 Smart Motor has its own Cortex M0 microcontroller running a hardware PID loop** for velocity, position, torque, and feedforward gain — similar to industrial servo drives. This inner loop closes at hardware speed. User code sends *setpoints* to this inner loop; the motor PID closes the loop automatically.

When user code calls `motor.spin_for(200, MM)`, VEXcode sends a target position to the motor's inner PID. The motor achieves the target (or not) and reports back via the telemetry API.

**Two-level PID architecture in the capstone**:
- **Inner** (hardware, always active): V5 motor PID → controls shaft to match commanded position/velocity
- **Outer** (user code, optional): trajectory PID in relates_to::[[lemlib]] → computes drive commands to reach a goal pose (distance + heading)

The outer loop runs at 20 ms; the inner loop runs at hardware speed inside the motor.

## PID Gap Residuals as Self-Model Evidence

The relates_to::[[task-telemetry-contract]] gap block captures residuals between what the inner motor PID achieved and what the outer trajectory PID expected. These residuals are **physical evidence** about unmodeled parameters:

| Gap residual | What it means | Self-model correction |
|---|---|---|
| Position deficit | More friction than predicted | Revise friction estimate upward |
| Torque at saturation | Load exceeded torque budget | Revise load mass or gear ratio |
| Velocity overshoot | Inertia lower than modeled | Revise mass estimate downward |
| Large I accumulation | Significant static friction | Add friction term to capability model |

This connects directly to the relates_to::[[llm-authored-self-model]] gap model: the LLM Generator reads the signed residuals and revises the capability self-model's physical parameters (moment arm, gear ratio, mass, friction coefficient) that explain the discrepancy.

relates_to::[[task-telemetry-contract]]  
relates_to::[[llm-authored-self-model]]  
relates_to::[[vex-v5]]  
relates_to::[[lemlib]]  
relates_to::[[reality-gap]]
