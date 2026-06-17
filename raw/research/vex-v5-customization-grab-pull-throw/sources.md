---
topic: "VEX V5 Classroom Starter Kit customization — can it complete grab/pull/throw, and how to quantify"
slug: vex-v5-customization-grab-pull-throw
researched: 2026-06-16
---

# Primary Sources — VEX V5 Customization: Grab / Pull / Throw

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://kb.vex.com/hc/en-us/articles/360044325872-Understanding-V5-Smart-Motor-11W-Performance | 2026-06-16 | Stall torque 2.1 Nm, continuous operating point 35% of stall = 0.735 Nm, peak power 12.75W, stall current 2.5A limit, ±1% power accuracy, 10ms PID rate |
| S2 | web | https://www.vexrobotics.com/276-4840.html | 2026-06-16 | Motor name/SKU, gear cartridge options (6:1/18:1/36:1), both shaft sizes compatible |
| S3 | web | https://nooby.tech/en/shop/1128-vex-v5-smart-motor.html | 2026-06-16 | Cartridge descriptions: 6:1 = 600 RPM (high speed), 18:1 = 200 RPM (standard, ships default), 36:1 = 100 RPM (high torque) |
| S4 | web | https://api.vex.com/v5/home/python/Motion/motor_and_motor_group.html | 2026-06-16 | Python API: motor.torque() 0.0–2.1 Nm, motor.current(), motor.velocity() RPM/%, motor.position() degrees, motor.power() W, motor.temperature(), motor.set_max_torque() |
| S5 | web | https://kb.vex.com/hc/en-us/articles/360035591012-Selecting-a-V5-Robot-Kit | 2026-06-16 | Starter Kit vs. Super Kit vs. Competition kits; specialty motion kits (Linear Motion, Winch/Pulley, Advanced Mechanics, Tank Tread); Brain has 21 Smart Ports + 8 3-Wire |
| S6 | web | https://idesign365.com/product/v5-classroom-starter-kit/ | 2026-06-16 | "The kit is scalable, which means you can add-on any components, additional motors, metal, aluminum and pneumatics" |
| S7 | web | https://kb.vex.com/hc/en-us/articles/360035592952-Building-V5-Robot-Claws | 2026-06-16 | Claw types (single-sided, double-sided, roller); motors or pneumatics activate claws; increase-torque gear ratio for single/double claws |
| S8 | web | https://education.vex.com/stemlabs/v5/stem-labs/design-by-request/friction-grabber-manipulators | 2026-06-16 | "Friction grabber manipulators apply force between an object and a pad, and then rely on the frictional force between the object and pad to manipulate the object" |
| S9 | web | https://kb.vex.com/hc/en-us/articles/360035592932-Selecting-a-V5-Assembly | 2026-06-16 | Catapult and flywheel described as "specialized manipulators designed to fling or throw"; catapult uses lever arm + elastic bands; flywheel uses two contra-rotating wheels or single wheel + friction plate |
| S10 | web | https://kb.vex.com/hc/en-us/articles/10004528511412-Understanding-V5-Mechanical-Launching-Systems | 2026-06-16 | V5 Flywheel Weight specs; rotational inertia; flywheel mounting to 48T/60T/72T/84T gears or versahub; asymmetry/vibration mitigation |
| S11 | codebase | `wiki/knowledge/sources/vex-v5-clawbot-build-instructions.md` | 2026-06-16 | Clawbot motor assignments: drive at ports 1/6/10 (300mm), claw at port 3 (600mm), arm at port 8 (900mm); 7:1 arm gear ratio (84T:12T); 12T claw gear |
| S12 | web | https://kb.vex.com/hc/en-us/articles/360035590932-Using-Gear-Ratios-with-the-V5-Motor | 2026-06-16 | "For most arms the 7:1 increase torque gear ratio... is sufficient by driving the 12T gear with a 200 RPM motor and attaching an 84T driven gear to the arm" |

---

## Excerpts

### S1 — Understanding V5 Smart Motor (11W) Performance
https://kb.vex.com/hc/en-us/articles/360044325872-Understanding-V5-Smart-Motor-11W-Performance
> "the motor is capable of running at max speed until it reaches about 60% of peak power (12.75W) or 35% of stall torque (2.1Nm)"
> "Stall current is limited to 2.5A to keep heat under control without affecting peak power output."
> "The microcontroller runs its own PID (proportional-integral derivative) with velocity control, position control, torque control, feedforward gain, and motion planning similar to industrial robots. PID is internally calculated at a 10 millisecond rate."

### S4 — VEX V5 Python Motor API
https://api.vex.com/v5/home/python/Motion/motor_and_motor_group.html
> "torque – Returns the amount of torque currently being applied by the motor or motor group. torque returns the amount of torque currently being applied by the motor or motor group in a range from 0.0 to 22.0 inch-pounds (InLb) or 0.0 to 2.1 Newton-meters (Nm)."
> "velocity – Returns the motor's or motor group's current velocity in % or rpm. current – Returns the current drawn by the motor or motor group. power – Returns the amount of electrical power the motor or motor group is consuming."

### S6 — iDesign365 V5 Classroom Starter Kit
https://idesign365.com/product/v5-classroom-starter-kit/
> "The kit is scalable, which means you can add-on any components, additional motors, metal, aluminum and pneumatics to build on your program as students push their robot design further."

### S9 — Selecting a V5 Assembly
https://kb.vex.com/hc/en-us/articles/360035592932-Selecting-a-V5-Assembly
> "Flywheels, slingshots, and catapults are specialized manipulators which are designed to fling or throw game pieces."
> "Catapults throw game pieces with a lever arm. The game piece is placed on one side of the lever arm in a game piece holder and elastic bands or latex tubing are attached to the other side of the lever."
> "Flywheels throw game pieces by having the game piece come in contact with a spinning wheel."

### S12 — Using Gear Ratios with the V5 Motor
https://kb.vex.com/hc/en-us/articles/360035590932-Using-Gear-Ratios-with-the-V5-Motor
> "For most arms the 7:1 increase torque gear ratio explained above is sufficient by driving the 12T gear with a 200 RPM motor and attaching an 84T driven gear to the arm."
