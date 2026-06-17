---
topic: VS Code Extension and PROS for VEX V5 — how they extend possible implementations for the LLM self-model capstone
slug: vex-v5-advanced-toolchains
researched: 2026-06-16
---

# Primary Sources — VEX V5 Advanced Toolchains

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://www.vexrobotics.com/vexcode/vscode-extension | 2026-06-16 | VS Code Extension replaces Pro V5; supports AI Copilot + Git; C++ and Python for V5 |
| S2 | web | https://kb.vex.com/hc/en-us/articles/31166747528340-Downloading-and-Running-a-VEX-Project-in-VS-Code | 2026-06-16 | "The VEX Extension only supports single Python file downloads currently" — critical Python limitation |
| S3 | web | https://kb.vex.com/hc/en-us/articles/21409418167444 | 2026-06-16 | IntelliSense/linting requires C/C++ and Python VS Code extensions; VS Code Extension install steps |
| S4 | web | https://kb.vex.com/hc/en-us/articles/8608865978644-VS-Code-UI-Overview-for-V5 | 2026-06-16 | User serial port opened automatically; same USB serial mechanism as VEXcode |
| S5 | web | https://en.wikipedia.org/wiki/VEX_Robotics | 2026-06-16 | PROS based on FreeRTOS; more robust API for precise hardware control; more bare-bones for knowledgeable users |
| S6 | web | https://github.com/purduesigbots/pros | 2026-06-16 | PROS is a lightweight open-source OS for VEX V5 Brain; PROS 3 for V5; kernel depends on VEX proprietary SDK |
| S7 | web | https://github.com/ros-drivers/rosserial/issues/591 | 2026-06-16 | `pros::Serial(port, baud)` API demonstrated; rosserial bridging V5 Brain to ROS via RS-485 Smart Ports at 115200 baud |
| S8 | web | https://www.vexforum.com/t/use-v5-smart-port-as-generic-serial-device-pros/57821?page=2 | 2026-06-16 | Max baud rate ~921600 (with ~3% oscillator error); `serctl()` and `registry_bind_port()` APIs |
| S9 | web | https://www.vexforum.com/t/v5-brain-to-raspberry-pi-communication/124407 | 2026-06-16 | PROS-based V5 Brain ↔ Raspberry Pi communication via USB; community forum confirmation |
| S10 | web | https://github.com/LemLib/LemLib | 2026-06-16 | LemLib: "open-source PROS template — common algorithms like Pure Pursuit and Odometry for new and experienced teams" |
| S11 | web | https://medium.com/@vedula.parjanya/mastering-vex-v5-drivetrains-and-localization-with-pros-lemlib-the-definitive-technical-guide-811e348dc355 | 2026-06-16 | LemLib provides PID, odometry, Monte Carlo Localization; sensors: IME, tracking wheels, V5 IMU |
| S12 | web | https://wiki.purduesigbots.com/software/vex-programming-software/vexide | 2026-06-16 | vexide: Rust runtime; compile-time safety eliminates data aborts/prefetch errors; cargo-v5 CLI |
| S13 | web | https://github.com/vexide/vex-v5-qemu | 2026-06-16 | vexide uses cooperative async (not FreeRTOS); QEMU emulation supported for vexide + PROS; VEXcode not supported in QEMU |
| S14 | web | https://vexide.dev/blog/posts/summer-update-24/ | 2026-06-16 | vexide trig ~100× faster than PROS/VEXcode due to optimized libm; cargo-v5 replaces cargo-pros + pros-cli |

---

## Excerpts

### S2 — Downloading and Running a VEX Project in VS Code (Python limit)
https://kb.vex.com/hc/en-us/articles/31166747528340-Downloading-and-Running-a-VEX-Project-in-VS-Code
> "Note: The VEX Extension only supports single Python file downloads currently."

### S5 — Wikipedia: VEX Robotics (PROS description)
https://en.wikipedia.org/wiki/VEX_Robotics
> "It provides a more bare-bones environment for more knowledgeable students that allows for an industry-applicable experience. It has a more robust API that allows for more precise control of the hardware for competition-level uses in V5RC/VEX U. It is based on FreeRTOS."

### S7 — rosserial VEX V5 RS-485 issue (pros::Serial API)
https://github.com/ros-drivers/rosserial/issues/591
> "class V5RS485 { public: V5RS485(int readPortNum = 19, int writePortNum = 20, int baud = 115200) { readPort = new pros::Serial(readPortNum); writePort = new pros::Serial(writePortNum); readPort->set_baudrate(baud); writePort->set_baudrate(baud); }"

### S8 — VEX Forum: Smart Port as generic serial (baud rate limit)
https://www.vexforum.com/t/use-v5-smart-port-as-generic-serial-device-pros/57821?page=2
> "Max theoretical baud rate is 921600, however, as baud rates are not derived from a standard oscillator (typically something like 18.432MHz would be used for standard rates) there will be an error between actual baud rate and the requested baud rate, in the case of 921600, perhaps 3%."

### S10 — LemLib GitHub
https://github.com/LemLib/LemLib
> "Welcome to LemLib! This open-source PROS template aims to introduce common algorithms like Pure Pursuit and Odometry for new and experienced teams alike."

### S11 — Medium: LemLib technical guide
https://medium.com/@vedula.parjanya/mastering-vex-v5-drivetrains-and-localization-with-pros-lemlib-the-definitive-technical-guide-811e348dc355
> "By combining solid drivetrain design, precise PID control, reliable odometry, and robust Monte Carlo Localization, you equip your VEX robot to navigate and compete at a professional level. PROS and LemLib provide the perfect tools to implement these concepts effectively."

### S13 — vexide/vex-v5-qemu GitHub
https://github.com/vexide/vex-v5-qemu
> "Unlike vexide's cooperative async runtime, FreeRTOS is preemptive and uses a whole plethora of timer interrupt voodoo to perform context switching."
> "VEXcode programs aren't supported since they're more complicated to emulate."

### S14 — vexide summer update 2024
https://vexide.dev/blog/posts/summer-update-24/
> "These math functions are actually far more performant than the ones in PROS or VEXcode due to using a more optimized build of libm, with trig performance benchmarking around 100 times faster."
