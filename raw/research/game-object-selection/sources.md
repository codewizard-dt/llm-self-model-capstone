---
topic: "What kind of object would be best in terms of graspability, scoopability, and launchability — various ball types and alternatives that would not be damaging or damaged when launched"
slug: game-object-selection
researched: 2026-06-22
---

# Primary Sources — Game Object Selection

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `wiki/knowledge/sources/clawbot-scoop-replacement.md` | 2026-06-22 | Passive scoop mounting dimensions: 1" bracket gap, plastic serving-spoon bowl ~70–80 mm wide; scoop action is "slide under + arm lift" |
| S2 | codebase | `wiki/knowledge/sources/vex-v5-customization-grab-pull-throw.md` | 2026-06-22 | Claw grip force (~42 N stall / 14.7 N continuous), object width proxy via motor position; slow catapult: ~0.45 m/s, suitable for ~50 g objects, 0.25–0.5 m range |
| S3 | codebase | `wiki/knowledge/sources/clawbot-scoop-replacement.md` | 2026-06-22 | Scoop morphology consequence: "I can only scoop objects I can slide under"; freed motor port; Task Telemetry Contract change |
| S4 | codebase | `wiki/knowledge/sources/vex-launch-disc-parts.md` | 2026-06-22 | Flywheel uses 3" OD, 60A flex wheels (217-6449); 6:1 cartridge → ~4200 RPM → ~22 m/s rim speed; single-flywheel + backplate design |
| S5 | web | https://wiki.purduesigbots.com/hardware/shooting-mechanisms/flywheel | 2026-06-22 | Compression physics: 1–2 mm compression optimal; "hard as baseballs" balls hurt flywheel consistency; single flywheel most accurate design |
| S6 | web | https://www.fhs-robotics.com/wp-content/uploads/2018/12/Nothing-But-Net.pdf | 2026-06-22 | VEX Nothing But Net: 4" (~100 mm) diameter polyurethane foam balls; proven flywheel game object at VRC scale |
| S7 | web | https://kb.vex.com/hc/en-us/articles/10004528811412-Understanding-V5-Mechanical-Launching-Systems | 2026-06-22 | VEX official: "most common way of launching objects is spinning a wheel at high speeds and feeding the object in"; bearing-based launcher draws half the current of bushing-based; flywheel weights increase moment of inertia for shot-to-shot consistency |
| S8 | web | https://education.vex.com/stemlabs/v5/stem-labs/robosoccer/vex-v5-ball-launcher | 2026-06-22 | VEX RoboSoccer lab uses Vision Sensor + colored ball + intake roller to pull ball in and shoot it — confirms ball (not disc) is a supported launcher game piece in VEX curriculum |
| S9 | web | https://www.usaracquetball.com/play/rules/2-courts-and-equipment | 2026-06-22 | Official racquetball specs: 2¼" (57.15 mm) diameter, ~1.4 oz (~39.7 g), hardness 55–60 durometers, bounces 68–72" from 100" drop |
| S10 | web | https://wiki.purduesigbots.com/hardware/shooting-mechanisms/flywheel | 2026-06-22 | Compression figure corrected: "If a 4" Nothing but Net ball (foam) must fit through a 3.65" gap, it will compress … by a total of 0.35"" — confirmed 9–12% compression (not 1–2 mm) |
| S11 | web | https://www.robots.education/store/p23/robot-claw-gripper.html | 2026-06-22 | Robot education gripper product page explicitly recommends "colored foam balls — the kind you can find at any value, hobby, or department store" for robot claws |

---

## Excerpts

### S5 — Purdue SIGBots Wiki: Flywheel
https://wiki.purduesigbots.com/hardware/shooting-mechanisms/flywheel
> "Double flywheels are larger, and heavier, but most importantly need more compression because of the reduced contact time with the ball."
> "A single flywheel is by far the most common flywheel used in Vex because of its consistency and accuracy. Single flywheels use a single wheel spinning at high RPMs with a back plate (most commonly Lexan or ABS). The back plate is formed around the wheel and tuned for the right amount of compression (varies based on the object being fired)."

### S6 — VEX Nothing But Net Game Manual (FHS Robotics PDF)
https://www.fhs-robotics.com/wp-content/uploads/2018/12/Nothing-But-Net.pdf
> "Ball – A green polyurethane foam spherical Scoring Object with a diameter of 4". Each Ball weighs [~50–80 g]"

### S7 — VEX Library: Understanding V5 Mechanical Launching Systems
https://kb.vex.com/hc/en-us/articles/10004528811412-Understanding-V5-Mechanical-Launching-Systems
> "The most common way of launching objects with a V5 robot is by spinning a wheel at high speeds and then feeding the object into the wheel."
> "The difference in current draw was significant, with the bushing-based launcher drawing more than double the current of the bearing-based launcher."

### S8 — VEX V5 RoboSoccer Ball Launcher Lab
https://education.vex.com/stemlabs/v5/stem-labs/robosoccer/vex-v5-ball-launcher
> "The VEX V5 Ball Launcher includes a Vision Sensor mounted above the robot, angled downward. This robot can be programmed to turn until the Vision Sensor detects a colored ball, and then drive toward it. When the Vision Sensor detects that the robot is close enough to the ball, the robot can pull it in using its intake, and then shoot it out at a target or goal."

---

## Excerpts (new sources)

### S9 — USA Racquetball: Rules — Courts and Equipment
https://www.usaracquetball.com/play/rules/2-courts-and-equipment
> "The standard racquetball shall be close to 2 1/4 inches in diameter; weigh approximately 1.4 ounces; have a hardness of 55-60 inches durometer; and bounce 68-72 inches from a 100-inch drop at a temperature of 70-74 degrees Fahrenheit."

### S10 — Purdue SIGBots Wiki: Flywheel (compression detail)
https://wiki.purduesigbots.com/hardware/shooting-mechanisms/flywheel
> "If a 4\" Nothing but Net ball (foam) must fit through a 3.65\" gap, it will bend or compress the backing material and/or itself by a total of 0.35\"."

### S11 — robots.education: Robot Claw / Gripper
https://www.robots.education/store/p23/robot-claw-gripper.html
> "We recommend colored foam balls – the kind you can find at any value, hobby, or department store."

---

## Inferences (no primary source)

- Wiffle ball diameter (~73 mm) and weight (~20 g) are well-established standard dimensions; cited as general knowledge.
- Serving-spoon bowl dimensions (~70–80 mm wide, 45–55 mm deep) are inferred from common kitchen spoon dimensions; not measured against the specific spoon used in the capstone build.
