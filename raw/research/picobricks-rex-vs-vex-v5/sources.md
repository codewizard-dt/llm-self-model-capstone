---
topic: "https://picobricks.com/products/rex-evolution-8in1-robotic-kit-for-adults-coding-robot-kit as an alternative to VEX V5 -- do a comprehensive compare and contrast relative to the stated goals of the project"
slug: picobricks-rex-vs-vex-v5
researched: 2026-06-16
---

# Primary Sources — PicoBricks REX Evolution vs VEX V5

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://picobricks.com/products/rex-evolution-8in1-robotic-kit-for-adults-coding-robot-kit | 2026-06-16 | Price ($164.99), 4× DC motor connections, 4× servo connections, WiFi, BT, balance sensor, buzzer, internal battery charging; 8 robot configs; RexIDE; plastic structure; 0 product reviews |
| S2 | web | https://ide.picobricks.com/rex-main/ | 2026-06-16 | ESP32E MCU; ArmBot = 3 servo motors; BalanceBot = MPU6050 acceleration sensor; SonicBot = HC-SR04; TrackerBot = IR sensor; WiBot has no sensors; RoverBot = tracked structure; OmniBot = omni wheels |
| S3 | web | https://github.com/Robotistan/REX-8in1-V2 | 2026-06-16 | "4 motor drivers and servo motor connectors"; HC-SR04, IR, MPU6050 sensor connectors; 9V battery port; ESP32E; C++ 66.5%, Python 18.9%; Arduino IDE, Thonny IDE, MicroBlocks IDE support |
| S4 | web | https://picobricks.com/products/rex-chassis-series-platforma-multi-purpose-mobile-robot-platform-red | 2026-06-16 | REX Chassis variant specifies "2× 6V 250 RPM plastic gear DC motors" — best available proxy for REX Evolution motor specs (kit page does not publish DC motor specs) |
| S5 | web | https://kb.vex.com/hc/en-us/articles/360035591332-V5-Motor-Overview | 2026-06-16 | "V5 Smart Motor provides feedback data related to position, velocity, current, torque, temperature, etc."; internal Cortex M0; full H-bridge; improvement over 393 Motor which only gave position |
| S6 | web | https://kb.vex.com/hc/en-us/articles/360044325872-Understanding-V5-Smart-Motor-11W-Performance | 2026-06-16 | Stall torque 2.1 Nm; continuous ≤ 0.735 Nm; peak power 12.75 W; PID with velocity, position, torque, feedforward; power accuracy ±1%; motor runs identically regardless of battery charge or temperature |
| S7 | web | https://zbotic.in/servo-motor-position-feedback-potentiometer-encoder-methods/ | 2026-06-16 | "Not reliably with standard RC servos — there is no feedback signal on the standard three-wire interface. Smart servo protocols (Dynamixel, Feetech SCS series, Herkulex) provide position telemetry over a half-duplex serial bus." |
| S8 | web | https://www.teachmemicro.com/esp32-meets-ai-talking-to-large-language-models-via-openrouter/ | 2026-06-16 | ESP32 can make HTTPS calls to LLM APIs (OpenRouter) over WiFi natively — demonstrates REX's WiFi-direct LLM integration path |
| S9 | codebase | `raw/research/vex-v5-customization-grab-pull-throw/index.md` | 2026-06-16 | USB serial user port = V5 LLM integration path; VEX AI demo uses Jetson Nano over this channel; `motor.torque()`, `motor.current()`, `motor.velocity()`, `motor.position()` API |
| S10 | codebase | `raw/research/vex-v5-classroom-starter-kit/index.md` | 2026-06-16 | Starter Kit (276-7010, $849.49); 4 V5 Smart Motors; 21 Smart Ports; steel structure; typed parts catalog |
| S11 | codebase | `wiki/knowledge/concepts/task-telemetry-contract.md` | 2026-06-16 | Contract schema: predicted + observed + gap JSON; `claw_motor.torque()`, `claw_motor.current()`, etc. are specific fields in the `observed` block |

## Excerpts

### S2 — Rex IDE (ide.picobricks.com)
https://ide.picobricks.com/rex-main/
> "ArmBot is a REX robot that allows the objects around it to be moved from one point to another point by remote control thanks to its robot arm. The robot arm on ArmBot consists of 3 servo motors."
> "REX 8 in 1 robot set eliminates the difficulties in circuit set up such as connection point and cable confusion with the REX Main Board using ESP32 infrastructure."
> "The REX main board is a special main board that designed to make the mechanical and electronic set up of the robots in the 8 in 1 set readily. This board, which uses the ESP32E processor, has connectors to connect all the components that are used in the REX 8 in 1 set to the circuit with a cable"

### S3 — GitHub: Robotistan/REX-8in1-V2
https://github.com/Robotistan/REX-8in1-V2
> "⚙️ 4 motor drivers and servo motors connectors to make the installation and circuit designs of 8 in 1 robots easier on the REX board, 1 connection connector for each to connect the HC-SR04, IR, and MPU6050 sensors, to connect a 9v battery to the circuit externally port and 1 buzzer and switch integrated into the card."

### S4 — REX Chassis Series Platforma (motor spec proxy)
https://picobricks.com/products/rex-chassis-series-platforma-multi-purpose-mobile-robot-platform-red
> "There are 2 pcs of 6 V 250 rpm plastic gear DC motor on the Platforma."

### S5 — VEX KB: V5 Motor Overview
https://kb.vex.com/hc/en-us/articles/360035591332-V5-Motor-Overview
> "The V5 Smart Motor provides feedback data related to position, velocity, current, torque, temperature, etc. This is a great improvement over the 393 Motor that only provided feedback related to its position."
> "The V5 Smart Motor's internal circuit board uses a full H-Bridge and its own Cortex M0 microcontroller to measure position, speed, direction, voltage, current, and temperature. The microcontroller runs its own PID (proportional–integral–derivative) with control over the velocity, position, torque, feedforward gain, and motion planning similar to industrial robots."

### S6 — VEX KB: V5 Smart Motor 11W Performance
https://kb.vex.com/hc/en-us/articles/360044325872-Understanding-V5-Smart-Motor-11W-Performance
> "In fact, the motor is capable of running at max speed until it reaches about 60% of peak power (12.75W) or 35% of stall torque (2.1Nm). The motor is also capable of producing 11W+ across 30% of the speed range."
> "The motor calculates accurate output power, efficiency, and torque, giving the user a true understanding of the motor's performance at any time. Position and angle are reported with an accuracy of .02 degrees."

### S7 — Zbotic: Servo Motor Position Feedback
https://zbotic.in/servo-motor-position-feedback-potentiometer-encoder-methods/
> "Not reliably with standard RC servos — there is no feedback signal on the standard three-wire interface. Smart servo protocols (Dynamixel, Feetech SCS series, Herkulex) provide position telemetry over a half-duplex serial bus."
