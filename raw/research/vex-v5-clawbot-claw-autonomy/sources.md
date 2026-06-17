---
topic: "exactly how autonomous the claw is for the VEX V5 Clawbot — does it have force sensing, position feedback, limit switches, or auto-stop on stall? Can it detect when it has gripped an object, or must the driver/program explicitly control open/close timing?"
slug: vex-v5-clawbot-claw-autonomy
researched: 2026-06-16
---

# Primary Sources — VEX V5 Clawbot Claw Autonomy

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `wiki/knowledge/sources/vex-v5-clawbot-build-instructions.md` | 2026-06-16 | Confirmed standard build has no sensors on claw; 1 motor + rubber bands; no bumper/limit switch in 41-step assembly |
| S2 | codebase | `wiki/knowledge/sources/vex-v5-customization-grab-pull-throw.md` | 2026-06-16 | Documented `velocity < 5 RPM AND current > 1.5 A → gripped boolean` heuristic and motor telemetry API surface |
| S3 | web | https://kb.vex.com/hc/en-us/articles/360035591012-Selecting-a-V5-Robot-Kit | 2026-06-16 | Confirmed Classroom Starter Kit includes 2 bumper switches but they are for sensor curriculum lessons, not part of Clawbot assembly |
| S4 | web | https://education.vex.com/stemlabs/v5/stem-labs/speedy-delivery/programming-the-claw-python | 2026-06-16 | Official curriculum claw code: `spin_for(FORWARD/REVERSE, N, DEGREES)` + `set_timeout(2, SECONDS)` only; no stall/object detection |
| S5 | web | https://api.vex.com/v5/home/blocks/motion/smart_motor.html | 2026-06-16 | Full motor API: confirmed no `is_stalled()`, no `spin_until_stall()`; `is_spinning()`, `is_done()`, `velocity()`, `current()`, `torque()`, `set_max_torque()`, `set_timeout()` all present |
| S6 | web | https://kb.vex.com/hc/en-us/articles/360044325872-Understanding-V5-Smart-Motor-11W-Performance | 2026-06-16 | Position accuracy 0.02°; stall current hardware-capped at 2.5 A; PID runs internally with velocity/position/torque control; no thermal damage risk from sustained grip |
| S7 | web | https://www.vexrobotics.com/276-4840.html | 2026-06-16 | Motor spec: built-in encoder tracks position and velocity; stall current 2.5 A; consistent performance regardless of battery state |

---

## Excerpts

### S3 — Selecting a V5 Robot Kit (VEX Library)
https://kb.vex.com/hc/en-us/articles/360035591012-Selecting-a-V5-Robot-Kit
> "The Classroom Starter Kit Includes everything needed to build the V5 Clawbot which will provide an engaging hands-on teaching tool. In addition, two 3-Wire Bumper Switches are included to show the relationship between sensors and robot behavior."

### S4 — Programming the Claw — Python (VEX STEM Labs)
https://education.vex.com/stemlabs/v5/stem-labs/speedy-delivery/programming-the-claw-python
> "Now that you can open the claw, you will want to close it as well. Return to your ClawControl project and add an additional claw_motor.spin_for() command to have the Claw Motor spin closed for 30 degrees."
> "Program the Clawbot to securely close the claw on an empty 12-ounce aluminum can without crushing the sides."
> Code shown: `claw_motor.set_timeout(2, SECONDS)` — "stops it after that time" if the motor doesn't complete the rotation. No current/velocity monitoring described.

### S5 — Smart Motor Blocks API (VEXcode Documentation)
https://api.vex.com/v5/home/blocks/motion/smart_motor.html
> "set motor max torque – Sets how hard a motor or motor group is allowed to push while spinning."
> "motor is done — Boolean: movement completion"
> "motor is spinning — Boolean: current rotation state"
> "motor current — Reports how much electrical current the motor or motor group is using."
> "motor torque — Reports how much torque the motor or motor group is using."
> *(No dedicated stall detection command listed.)*

### S6 — Understanding V5 Smart Motor 11W Performance (VEX Library)
https://kb.vex.com/hc/en-us/articles/360044325872-Understanding-V5-Smart-Motor-11W-Performance
> "The motor's internal circuit board has a full H-Bridge and its own Cortex M0 microcontroller to measure position, speed, direction, voltage, current, and temperature."
> "Stall current is limited to 2.5A to keep heat under control without affecting peak power output."
> "Position and angle are reported with an accuracy of .02 degrees."
> "The motor calculates accurate output power, efficiency, and torque, giving the user a true understanding of the motors performance at any time."

### S7 — V5 Smart Motor & Gear Cartridges (VEX Robotics product page)
https://www.vexrobotics.com/276-4840.html
> "Use the built-in encoder to track a robot's rotational position and velocity"
> "The motor runs at a slightly lower voltage than the batteries minimum voltage, and the motor's power is accurately controlled to +/-1%. This means the motor will perform the same for every match and every autonomous run regardless of battery charge or motor temperature."
