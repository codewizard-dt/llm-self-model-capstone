---
topic: "https://www.vexrobotics.com/go and VEX GO Competition Kit in particular how is VEX GO comparable to VEX V5 and would it be a potential stand in for this experiment?"
slug: vex-go-vs-vex-v5
researched: 2026-06-16
---

# Primary Sources — VEX GO vs VEX V5

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://www.vexrobotics.com/parts/269-6911 | 2026-06-16 | GO Brain has 4 numbered Smart Ports + 1 Eye Sensor port; 3 motors in kit; Eye Sensor detects color/object/brightness; Electromagnets pick up metal Disk cores; motor can connect directly to Battery via Switch (bypassing Brain) |
| S2 | web | https://nooby.tech/en/shop/1009-vex-go-kit-education-kit.html | 2026-06-16 | VEX GO Kit: 296 structural/motion components, 1 brain, 1 switch, 3 motors, 1 eye sensor, 1 LED bumper, 3 electromagnets, 1 rechargeable battery, 2 storage boxes; ages 7–11; VEXcode GO (Scratch blocks) |
| S3 | web | https://www.vexrobotics.com/go (via Brave snippet; 403 on direct fetch) | 2026-06-16 | Grades 3–5; VEXcode GO supports "Block-based and Python"; "Choose between two different coding languages"; Python is available (not just blocks) |
| S4 | web | https://www.vexrobotics.com/269-8115.html (via Brave snippet; 403 on direct fetch) | 2026-06-16 | GO Competition Kit is a FIELD KIT: "includes everything needed to build one of four themed games… field tiles, walls, game elements, and carrying cases"; "Robot not included. Teams will also need a VEX GO Education Kit or Bundle to compete." |
| S5 | web | https://idesign365.com/product/vex-go-competition-kit/ | 2026-06-16 | "The GO Competition Kit contains everything you need to build one of four different themed games with your VEX GO Competition Kits"; confirms this is an arena/field kit, not robot hardware |
| S6 | web | https://api.vex.com/go/home/blocks/motion.html | 2026-06-16 | Full VEX GO motor blocks API: motor position (degrees/turns ✓), motor velocity (% only), motor current (% only — "how much power the motor is using"); no torque reading; no power/W reading; no temperature reading; max torque is settable (not readable in Nm) |
| S7 | codebase | `raw/research/vex-v5-customization-grab-pull-throw/index.md` | 2026-06-16 | V5 motor telemetry API: `torque(Nm)`, `current(AMP)`, `velocity(RPM)`, `position(DEGREES)`, `power(WATT)`, `temperature(PERCENT)` — all calibrated physical units; Grab contract requires `claw_torque_Nm` and `claw_current_A` in the `observed` block |
| S8 | codebase | `wiki/knowledge/concepts/task-telemetry-contract.md` | 2026-06-16 | Contract is the binding platform-selection filter; platforms without per-actuator feedback in physical units cannot populate the observed block |
| S9 | web | https://www.vexrobotics.com/228-2560.html | 2026-06-16 | VEX IQ Smart Motor: TI MSP430 MCU at 16 MHz; quadrature encoder (0.375° resolution); current monitoring in Amps; speed in RPM; internal PID; "command motors up to 3,000 times/second" — closer to V5 than GO, still lacks torque/power readings |
| S10 | web | https://idesign365.com/product/vex-go-kit-with-storage/ | 2026-06-16 | VEX GO Kit with Storage (SKU 269-6705) priced at $299.00 |

## Excerpts

### S1 — VEX GO Kit Contents (VEX Robotics)
https://www.vexrobotics.com/parts/269-6911
> "The Brain has four numbered ports that can accept the Motors, LED Bumper, or Electromagnet."
> "The Motor changes energy into movement that can be used in a build. It can be connected directly to the Battery through the Switch. Or, the Motor can be connected to the Brain, and controlled by a VEXcode GO project."

### S3 — VEX GO product page (via Brave snippet)
https://www.vexrobotics.com/go
> "VEXcode GO brings Robotics and Computer Science to life for all students at all skill levels. Choose between two different coding languages - Block-based and Python."

### S4 — GO Competition Field Kit (via Brave snippet)
https://www.vexrobotics.com/269-8115.html
> "The GO Competition Kit includes everything needed to build one of four themed games for use with VEX GO Competition Kits. Each kit includes a field made from configurable tiles and walls. Game objects are built using the VEX plastic design system."
> "Robot not included. Teams will also need a VEX GO Education Kit or Bundle to compete."

### S6 — VEX GO Blocks API: Motion
https://api.vex.com/go/home/blocks/motion.html
> "Motor blocks can spin a motor forward or in reverse, move it to a specific position, and adjust its speed, torque, and timeout settings. They can also report encoder values to track movement and position."
> "motor position — Returns the motor's current rotational position."
> "motor velocity — Returns the motor's current velocity."
> "The motor current reporter block reports how much power the motor is using" [in percentage]

### S9 — VEX IQ Smart Motor
https://www.vexrobotics.com/228-2560.html
> "The Smart Motor does more than just make your wheels spin or arm move. The built in processor, quadrature encoder and current monitor allow for advanced control and feedback through the Robot Brain. Command speed, direction, time, revolutions and degrees. Encoder resolution is 0.375 degrees."
> "The Smart Motor uses a Texas Instruments MSP430 microcontroller running at 16 MHz to process requests, measure speed and direction, monitor current, and control the motor via an H-Bridge."
