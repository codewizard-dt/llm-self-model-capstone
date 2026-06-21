---
topic: How do V5 user programs work, how do competition teams control the robot, and can the RPi send motor commands without a pre-loaded Brain program?
slug: v5-user-programs
researched: 2026-06-21
---

# Primary Sources — V5 User Programs

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://www.reddit.com/r/vex/comments/hmu5rc/vex_v5_with_a_rpi_or_arduino/ | 2026-06-21 | V5 Smart Motors use digital RS-485 communication; "you would have to fake the signals sent from the v5 brain to the smart motors" |
| S2 | web | https://www.vexforum.com/t/identifying-sensors-as-being-compatible-with-cortex-and-or-v5/83519 | 2026-06-21 | "All sensors with a smart port communicate over RS-485 using a proprietary protocol and are not compatible with any system other than V5" |
| S3 | web | https://vexide.dev/blog/posts/serial-deep-dive/ | 2026-06-21 | System port = program upload only; user port = stdio from running program; "If you try to communicate with the Brain over the user port nothing will happen" |
| S4 | web | https://ascendrobotics.gitbook.io/ascend/vex-robotics/coding/pros | 2026-06-21 | "If no competition control is connected, this function will run immediately following initialize()" |
| S5 | web | https://www.vexforum.com/t/pros-c-drive-code-help/93383 | 2026-06-21 | Confirms: without competition switch, opcontrol() runs immediately; PROS template structure |
| S6 | web | https://kb.vex.com/hc/en-us/articles/360035590432-Running-the-Drive-Program-with-the-V5-Brain | 2026-06-21 | Built-in "Drive program" maps V5 Controller joysticks to motors; works without user code but requires V5 Controller, not serial |
| S7 | web | https://kb.vex.com/hc/en-us/articles/360035590812-Running-User-Programs-with-the-V5-Brain | 2026-06-21 | User programs: tap slot on Brain touchscreen to run; program runs until manually stopped |
| S8 | web | https://kb.roboticseducation.org/hc/en-us/articles/25869787659031-Troubleshooting-the-V5-Field-Controller | 2026-06-21 | Competition status shows "User program: 3 (Slot 3 is running; 0 would be no program running)" — confirms slot-based execution model |
| S9 | codebase | `robot/v5-brain/pros_bridge/src/main.cpp` | 2026-06-21 | Current Brain sketch: initialize() + opcontrol() loop; confirms the minimal-program pattern is already being used |
| S10 | codebase | `robot/pi-runtime/docs/TOMORROW_BRINGUP.md` | 2026-06-21 | Bringup steps assume a program is already uploaded and running on the Brain |

---

## Excerpts

### S1 — Reddit: VEX V5 With a RPi or Arduino
https://www.reddit.com/r/vex/comments/hmu5rc/vex_v5_with_a_rpi_or_arduino/
> "With v5 smart motors, they have microprocessors inside them to control speed. The v5 brain uses digital communication to tell the motor how fast it should be spinning, meaning to control a v5 motor from an RPi or Arduino you would have to fake the signals sent from the v5 brain to the smart motors, and trick the motors into thinking they are connected to a v5 brain."

### S2 — VEX Forum: Identifying sensors compatible with Cortex and V5
https://www.vexforum.com/t/identifying-sensors-as-being-compatible-with-cortex-and-or-v5/83519
> "All of the sensors with a smart port (4P4C connector) communicate over RS-485 using a proprietary protocol and are not compatible with the Cortex (or any system other then the V5 for that matter)."

### S3 — vexide: A Deep Dive Into the V5 Serial Protocol
https://vexide.dev/blog/posts/serial-deep-dive/
> "The system port is used for communicating with the Brain over the serial protocol, and the user port is used for viewing user program stdio output (this is often called the debug terminal)."
> "If you try to communicate with the Brain over the user port nothing will happen."
> "Commands are high level abstractions over common sequences of packet exchanges. A great example of this is the UploadProgram command."

### S4 — Ascend Robotics PROS guide
https://ascendrobotics.gitbook.io/ascend/vex-robotics/coding/pros
> "If no competition control is connected, this function will run immediately following initialize()."

### S5 — VEX Forum: PROS C++ drive code help
https://www.vexforum.com/t/pros-c-drive-code-help/93383
> "This function will be started in its own task with the default priority and stack size whenever the robot is enabled via the Field Management System or the VEX Competition Switch in the operator control mode. If no competition control is connected, this function will run immediately following initialize()."

### S6 — VEX Library: Running the Drive Program
https://kb.vex.com/hc/en-us/articles/360035590432-Running-the-Drive-Program-with-the-V5-Brain
> "The Drive program is a default program built into the VEX V5 Robot Brain so it can be used with Smart Motors, Sensors, and the VEX V5 Controller without programming. The Drive program maps the Controller's joysticks and buttons to control specific Smart Ports on the Brain."

### S8 — RECF: Troubleshooting the V5 Field Controller
https://kb.roboticseducation.org/hc/en-us/articles/25869787659031-Troubleshooting-the-V5-Field-Controller
> "Errors are shown in orange, in this case, the team is running old firmware (VEXOS) in their V5 Robot Brain and has also not started their user program."
> "User program: 3 (Slot 3 is running; 0 would be no program running)"
