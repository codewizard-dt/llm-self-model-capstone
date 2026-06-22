---
topic: VEX 3-wire port spec including connector types
slug: vex-3wire-port-spec
researched: 2026-06-22
---

# Primary Sources — VEX V5 3-Wire Port Spec

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://api.vex.com/v5/home/cpp/3-Wire_Devices/index.html | 2026-06-22 | Confirmed `Servo`, `pwm_out`, and full device list for 3-wire ports; PWM outputs legacy motor controllers or servos |
| S2 | web | https://kb.vex.com/hc/en-us/articles/360035951771-Connecting-a-3-Wire-Device-to-the-V5-Brain | 2026-06-22 | 8 ports A–H; keyed so cables insert one way only; black wires must align to prevent incorrect connection |
| S3 | web | https://wiki.purduesigbots.com/vex-electronics/vex-electronics/vex-v5-brain | 2026-06-22 | Power out spec: **5 V @ 2 A total for all ports**; digital I/O voltage thresholds; analog 0–5 V 12-bit; dedicated Cortex M0 handles ADI |
| S4 | web | https://kb.vex.com/hc/en-us/articles/360038663211-Using-the-V5-3-Wire-LED-Indicator | 2026-06-22 | "The center pin needs to be aligned with the red (+5V) wire" — confirms centre pin = +5 V |
| S5 | web | https://www.vexforum.com/t/v5-3-wire-ports/64267 | 2026-06-22 | Community-confirmed pin order: "GND, 5V, and signal from left to right (black, red, white)"; "vex connectors fit into a breadboard" confirming 2.54 mm female cable ends |
| S6 | web | https://www.rchelicopterfun.com/rc-servo-connectors.html | 2026-06-22 | RC servo connector is 2.54 mm (0.1") pitch female 3-pin header; centre pin is always +V for polarity immunity; swapping GND/signal doesn't cause power damage |
| S7 | web | https://www.gobilda.com/connector-style-tjc8-servo/ | 2026-06-22 | "TJC8 connector has a specific 2.54 mm contact spacing widely used on breadboards" — industry name for standard RC servo connector |
| S8 | web | https://www.vexrobotics.com/extension-cables.html | 2026-06-22 | VEX sells female-female 3-wire extension cables described as "for interfacing VEX components with other non-VEX systems" |
| S9 | web | https://www.vexforum.com/t/powering-a-non-vex-servo-using-v5-brain/60968 | 2026-06-22 | jpearman (VEX staff) confirms `vex::pwm_out finger( Brain.ThreeWirePort.A )` as the correct API for driving a non-VEX servo from a V5 3-wire port |

---

## Excerpts

### S1 — VEXcode 3-Wire Devices API
https://api.vex.com/v5/home/cpp/3-Wire_Devices/index.html
> "Pulse Width Modulation (PWM) – Outputs a pulse-width-modulated control signal through a 3-Wire port to drive legacy motor controllers or servos."
> "Servo Motor – A position-controlled motor used to rotate mechanisms to specific angles."

### S2 — VEX KB: Connecting a 3-Wire Device to the V5 Brain
https://kb.vex.com/hc/en-us/articles/360035951771-Connecting-a-3-Wire-Device-to-the-V5-Brain
> "The V5 brain has a total of eight 3-Wire ports, labeled A-H, which can all be used as inputs or outputs that can be used with VEX EDR 3-wire legacy sensors and motor controllers."
> "The ports are keyed so you can only plug the cable in one way."
> "If you are using 3-Wire extensions, make sure the black wires are always connected to prevent connecting the device incorrectly."

### S3 — Purdue SIGBots: VEX V5 Brain
https://wiki.purduesigbots.com/vex-electronics/vex-electronics/vex-v5-brain
> "3-Wire Specifications: Power out — 5v @ 2A total for all ports"
> "Digital Input: High = 2.4 - 5.5 V  Low = 0.0 - 1.0 V"
> "Analog Input: 0 - 5 V, 12-bit"
> "Any 3-Wire port can be a digital input, digital output, analog input, or PWM motor control."

### S4 — VEX KB: Using the V5 3-Wire LED Indicator
https://kb.vex.com/hc/en-us/articles/360038663211-Using-the-V5-3-Wire-LED-Indicator
> "The LED's outer pin needs to be aligned with the 3-Wire Extension Cable's outside white (Signal) wire and the center pin needs to be aligned with the red (+5V) wire as the two components are connected."

### S5 — VEX Forum: V5 3-wire ports (pinout discussion)
https://www.vexforum.com/t/v5-3-wire-ports/64267
> Eden: "looking at the brain's side with the ADI ports and the 11-20 port row facing down, the pins should be GND, 5V, and signal from left to right. This is according to the ADI wire colors: black, red and white"
> 93870A: "white - signal, red - VCC, black - gnd. Just remembered, the vex connectors fit into a breadboard so you could test the analog value with your arduino."

### S6 — RC Helicopter Fun: RC Servo Connectors
https://www.rchelicopterfun.com/rc-servo-connectors.html
> "RC Servo Connectors are basically a 3 pin/wire Dupont style connector with pin pitch (pin spacing) at 2.54 mm on center."
> "The positive (red wire) is always in the middle of 3 pin/wire servo connectors. This provides polarity protection… Again, this is where having the center pin of the RC servo connector being the positive/power saves the day because things are generally safe if the ground and signal pins are swapped; the thing just won't work until it's plugged in correctly."

### S7 — goBILDA: TJC8 Servo Connector
https://www.gobilda.com/connector-style-tjc8-servo/
> "Hobby servos nearly all possess the same connection style, known as a TJC8 connector outside of the hobby realm. A TJC8 connector has a specific 2.54mm contact spacing widely used on breadboards, row pins, and jumper wires."

### S8 — VEX Robotics: Extension Cables
https://www.vexrobotics.com/extension-cables.html
> "These 12\" long 3-wire cables have female connectors on both ends. Use them for interfacing VEX components with other non-VEX systems."

### S9 — VEX Forum: Powering a Non-VEX Servo Using V5 Brain
https://www.vexforum.com/t/powering-a-non-vex-servo-using-v5-brain/60968
> jpearman: "vex::pwm_out finger( Brain.ThreeWirePort.A );  — configures pwm_out on legacy port A."
