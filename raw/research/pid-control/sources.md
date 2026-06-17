---
topic: what is proportional-integral-derivative
slug: pid-control
researched: 2026-06-16
---

# Primary Sources — Proportional-Integral-Derivative (PID) Control

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://en.wikipedia.org/wiki/Proportional%E2%80%93integral%E2%80%93derivative_controller | 2026-06-16 | Formal definition; three-term descriptions (P/I/D); mathematical formula u(t); historical background |
| S2 | web | https://docs.wpilib.org/en/stable/docs/software/advanced-controls/introduction/introduction-to-pid.html | 2026-06-16 | "P drives position error to zero, D drives velocity error to zero, I drives accumulated error to zero"; discrete formula; PI controller block diagram |
| S3 | web | https://www.emergentmind.com/topics/proportional-integral-derivative-pid-controllers | 2026-06-16 | "Proportional term reduces rise time; derivative term damps overshoot and oscillations, at the cost of amplifying high-frequency noise" |
| S4 | web | https://nhsjs.com/2025/zeroing-in-the-power-of-pid-in-next-gen-robotics/ | 2026-06-16 | VEX V5-specific: 20ms sampling interval; Ziegler-Nichols tuning; integral windup capping; implemented in VEXcode real-time control loop |
| S5 | web | https://kb.vex.com/hc/en-us/articles/360035591332-V5-Motor-Overview | 2026-06-16 | V5 Smart Motor Cortex M0 runs its own internal PID for velocity, position, torque, feedforward; 0.02° position accuracy |
| S6 | web | https://mardigiorgio.github.io/blog/vex-v5-odometry-pid-math/ | 2026-06-16 | VEX V5 tuning sequence: raise Kp → add Kd → add Ki with integral clamp; exit conditions; separate gain sets per motion type |
| S7 | web | https://ascendrobotics.gitbook.io/ascend/vex-robotics/coding/vexcode-pro/advanced/coding-pids/drive-pid-tutorial | 2026-06-16 | "No two robots have the same set of constants"; motor-encoder-based PID for drive distance in VEXcode |
| S8 | web | https://wiki.purduesigbots.com/software/control-algorithms/pid-controller | 2026-06-16 | Integral windup: "if a PID controller is supposed to raise a robot arm, and the robot is disabled for ten minutes, integral windup would accumulate and cause wild oscillations"; PROS PIDLib reference |
| S9 | web | https://ascendrobotics.gitbook.io/ascend/vex-robotics/coding/vexcode-pro/advanced/coding-pids/turn-pid-tutorial | 2026-06-16 | Zone-activation anti-windup: "We'll only activate it when the robot is within 10 degrees of the target position, to avoid integral windup" |

---

## Excerpts

### S1 — Wikipedia: PID Controller (three terms)
https://en.wikipedia.org/wiki/Proportional%E2%80%93integral%E2%80%93derivative_controller
> "The proportional (P) component responds to the current error value by producing an output that is directly proportional to the magnitude of the error. This provides immediate correction based on how far the system is from the desired setpoint. The integral (I) component, in turn, considers the cumulative sum of past errors to address any residual steady-state errors that persist over time, eliminating lingering discrepancies. Lastly, the derivative (D) component predicts future error by assessing the rate of change of the error, which helps to mitigate overshoot and enhance system stability."

### S2 — WPILib Introduction to PID
https://docs.wpilib.org/en/stable/docs/software/advanced-controls/introduction/introduction-to-pid.html
> "Roughly speaking: the proportional term drives the position error to zero, the derivative term drives the velocity error to zero, and the integral term drives the total accumulated error-over-time to zero. All three terms are added together to produce the control signal."

### S4 — NHSJS: Zeroing In — PID in Next-Gen Robotics (VEX V5 specific)
https://nhsjs.com/2025/zeroing-in-the-power-of-pid-in-next-gen-robotics/
> "PID constants were manually tuned using step-response testing, following the Ziegler-Nichols heuristic. Integral windup was mitigated by capping the integral term. All PID logic was implemented in VEX code using a real-time control loop with a 20 ms sampling interval."

### S5 — VEX Library: V5 Motor Overview (internal PID)
https://kb.vex.com/hc/en-us/articles/360035591332-V5-Motor-Overview
> "The microcontroller runs its own PID (proportional–integral–derivative) with control over the velocity, position, torque, feedforward gain, and motion planning similar to industrial robots."

### S8 — Purdue SIGBots: PID Controller (integral windup)
https://wiki.purduesigbots.com/software/control-algorithms/pid-controller
> "Naive PID controllers can suffer from integral windup if some external condition prevents the setpoint from being reached for an extended period of time, causing a huge value to load into the integral term and leading to undesired behavior. For example, if a PID controller is supposed to raise a robot arm, and the robot is disabled for ten minutes, integral windup would accumulate and cause wild oscillations."

### S9 — Ascend Robotics: Turn PID Tutorial (zone activation)
https://ascendrobotics.gitbook.io/ascend/vex-robotics/coding/vexcode-pro/advanced/coding-pids/turn-pid-tutorial
> "We'll only activate it when the robot is within 10 degrees of the target position, to avoid integral windup."
