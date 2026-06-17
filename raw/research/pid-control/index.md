---
topic: what is proportional-integral-derivative
slug: pid-control
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Proportional-Integral-Derivative (PID) Control

> A PID controller is a feedback loop mechanism that continuously computes an *error* (setpoint minus measured value) and applies a corrective output that is the sum of three terms: **P** (proportional to current error), **I** (proportional to accumulated past error), and **D** (proportional to rate of change of error). It is the most widely used control algorithm in industry and robotics. For the capstone, PID is operative at two levels: *inside* every VEX V5 Smart Motor (hardware PID on the Cortex M0), and *outside* in user code (software PID for trajectory and pose control via LemLib). Understanding PID is prerequisite for interpreting the motor telemetry the LLM self-model reads.

---

## Research Questions

1. What are the three PID terms and what does each one do?
2. What is the mathematical formulation?
3. How are Kp, Ki, Kd tuned in practice?
4. How does PID operate inside VEX V5 Smart Motors specifically?
5. What are the failure modes (integral windup, overshoot, noise sensitivity)?

---

## Current State (Codebase)

No Brain-side code exists yet. LemLib (in the Stage 2 toolchain plan at `wiki/knowledge/entities/tools/lemlib.md`) uses PID internally for drivetrain distance and heading control. VEX V5 Smart Motor API (`motor.velocity()`, `motor.torque()`, etc.) exposes the output of the motor's internal PID loop. Understanding PID is required to interpret these values in the self-model gap layer.

---

## Key Findings

### What PID Is

A PID controller is a **feedback control loop**: it reads a measurement (Process Variable, PV), compares it to a target (Setpoint, SP), computes the error `e(t) = SP − PV`, and outputs a control signal `u(t)` that drives the system toward the target [S1]:

```
u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·(de/dt)
```

The three terms are summed to produce `u(t)`. Each term has a gain coefficient (Kp, Ki, Kd) that scales its contribution.

---

### The Three Terms

**P — Proportional** [S1][S2]:
- Output proportional to the *current* error: `Kp · e(t)`
- Large error → large correction; small error → small correction
- Effect: drives the system toward the setpoint; reduces rise time
- Problem alone: never fully reaches the setpoint — there is always a small residual "steady-state error" because the moment the error approaches zero, the correction also approaches zero

**I — Integral** [S1][S2]:
- Output proportional to the *accumulated past* error: `Ki · ∫e(τ)dτ`
- Sums all past errors over time; grows whenever the system sits off-target
- Effect: eliminates steady-state error that P alone cannot fix (the integral "remembers" persistent small errors and builds up correction force until they vanish)
- Problem: slow to act (accumulates over time); can cause *overshoot* if the integral builds up while the system is blocked (see integral windup below)

**D — Derivative** [S1][S3]:
- Output proportional to the *rate of change* of error: `Kd · (de/dt)`
- Predicts where the error is heading by looking at how fast it is changing
- Effect: damps oscillation and overshoot — when the system is approaching the setpoint fast, the derivative is large and opposing, slowing the approach; acts as a "brake"
- Problem: amplifies high-frequency sensor noise (takes the derivative of a noisy signal → noisy output); often implemented with a low-pass filter

**Intuitive summary** [S2]:
> "The proportional term drives the position error to zero, the derivative term drives the velocity error to zero, and the integral term drives the total accumulated error-over-time to zero."

---

### Mathematical Formulation

Continuous form:
```
u(t) = Kp·e(t) + Ki·∫₀ᵗ e(τ)dτ + Kd·(de/dt)
```

Discrete form (for digital implementation with sample period Δt):
```
u[n] = Kp·e[n] + Ki·Δt·Σe[k] + Kd·(e[n] - e[n-1])/Δt
```

In VEX V5 implementations, the loop typically runs at **20 ms** intervals (50 Hz) [S4]. The encoder provides position in degrees; error = `desired_position - motor.position(DEGREES)`.

---

### PID Inside VEX V5 Smart Motors [S5]

This is critical for the capstone: **every V5 Smart Motor contains its own Cortex M0 microcontroller that runs a hardware PID loop internally**:

> "The microcontroller runs its own PID (proportional–integral–derivative) with control over the velocity, position, torque, feedforward gain, and motion planning similar to industrial robots."

When user code calls `motor.spin_for(FORWARD, 200, MM)`, VEXcode sends a target to the motor's internal PID controller, which then closes the loop at the hardware level — independently of the user code's main loop. This is why VEX V5 motor control is more precise than typical hobby servos: the inner PID loop runs at hardware speed, not at the 20 ms user-code rate.

The telemetry the self-model reads (`motor.torque()`, `motor.current()`, `motor.velocity()`, `motor.position()`) is the **output of the motor's internal PID** — it reflects what the motor actually achieved, which may differ from what was commanded.

**Two-level PID architecture in the capstone**:
- **Inner loop** (hardware, automatic): motor PID → controls actual motor shaft to match commanded velocity/position
- **Outer loop** (user code, optional): trajectory PID → computes motor commands to reach a goal pose (LemLib does this for the drivetrain)

---

### Tuning (Kp, Ki, Kd)

Practical VEX V5 tuning sequence [S6][S7]:

1. **Set Ki = 0, Kd = 0.** Increase Kp until the robot reaches the target quickly but overshoots slightly (oscillation at the setpoint).
2. **Add Kd.** Increase until oscillation is damped and the system settles smoothly. Too much Kd → sluggish response or noise amplification.
3. **Add small Ki.** Use only if the robot cannot reach the target due to static friction (it stalls just short). Too much Ki → integral windup (see below).

**Ziegler-Nichols method** [S4]: increase Kp until the system oscillates with constant amplitude → record critical gain Ku and oscillation period Tu → compute Kp = 0.6Ku, Ki = 2Kp/Tu, Kd = KpTu/8. Provides a starting point, not a final answer.

**Key insight**: no two robots have the same gain values — weight, drivetrain friction, gear ratio, and motor wear all affect the optimal gains [S7]. The LLM self-model's capability layer should treat Kp/Ki/Kd as robot-specific parameters that must be measured, not assumed.

---

### Failure Modes

**Integral windup** [S8][S9]:
- If the system is blocked (e.g., robot hits a wall) or far from the setpoint for a long time, the integral term accumulates (winds up) to a very large value.
- When the block is removed, the large integral causes wild overshoot and oscillation.
- **Fix**: cap the integral term (clamp it to ±max_integral); or only activate integral when close to the target (zone activation).
- VEX V5 example: "We'll only activate it when the robot is within 10 degrees of the target position, to avoid integral windup." [S9]

**Overshoot**:
- Too-high Kp or too-low Kd causes the system to overshoot the setpoint; oscillates around it.
- Fix: increase Kd; decrease Kp.

**Derivative noise amplification** [S3]:
- Kd takes the derivative of the error signal. If the encoder reads are noisy, Kd amplifies noise → erratic output.
- Fix: apply a low-pass filter to the derivative term; or use a filtered velocity measurement rather than numerical differentiation.

**Steady-state error** (with P only):
- System settles near but not at the setpoint — the correction force goes to near-zero before the error reaches zero.
- Fix: add integral term (Ki > 0).

---

### Relevance to the Self-Model

The capstone's **task telemetry contract** (`wiki/knowledge/concepts/task-telemetry-contract.md`) captures:
```json
{
  "predicted": { "position_deg": 720, "torque_Nm": 0.8 },
  "observed":  { "position_deg": 695, "torque_Nm": 1.1 },
  "gap":       { "delta_position_deg": -25, "delta_torque_Nm": +0.3 }
}
```

The gap is the **residual between what the inner motor PID achieved and what the outer trajectory PID commanded**. The LLM self-model reads these residuals to revise its capability predictions (e.g., "claw motor has higher friction than predicted — revise grip torque estimate upward").

Understanding PID explains *why* the residuals exist and what the LLM is correcting:
- Position gap → inner PID couldn't reach the commanded target (friction, load, windup)
- Torque gap → load was higher/lower than predicted
- Velocity gap → inertia was different from the model

---

## Constraints

- VEX V5 user code typically runs the outer PID loop at 20 ms intervals
- The inner motor PID is closed and not directly configurable from VEXcode Python (VEXcode Python exposes high-level commands; the VS Code Extension C++ exposes lower-level torque/feedforward parameters)
- Integral windup mitigation is mandatory in any robust VEX V5 PID implementation
- Gains are robot-specific and must be re-tuned when morphology changes (a Gen 2 robot with different mass/geometry will need new gains)

---

## Recommendation

**For the capstone demo (Stage 1, VEXcode V5 Python)**: the inner motor PID is sufficient — just call `motor.spin_for()` and let the hardware PID do its job. Read the telemetry afterward.

**For Stage 2 (PROS + LemLib)**: LemLib implements an outer PID loop for drivetrain position/heading. Use the VEX V5-specific tuning sequence: raise Kp, add Kd, add small Ki with integral clamp. Treat tuned gains as part of the robot's "physical parameters" — they belong in the self-model's capability layer alongside torque budget and gear ratios.

**For the LLM self-model**: frame PID gaps as evidence about unmodeled physics:
- Persistent position deficit → underestimated friction or inertia
- Torque at saturation → load exceeded capability prediction
- Velocity overshoot → inertia lower than modeled (lighter-than-expected structure)

---

## Next Steps

- Run `/wiki-ingest raw/research/pid-control/index.md` to add PID as a concept page in the wiki.
- No immediate task needed — VEXcode V5 Python uses the motor's built-in PID transparently.
- When starting Stage 2 PROS work: `/task-add Tune LemLib PID gains for Clawbot drivetrain (drive + heading)`
