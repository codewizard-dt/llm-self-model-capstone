---
topic: "flywheel indexer mechanism — load a ball/disc and hold it, then shoot on command — for both 1-motor and 2-motor VEX V5 flywheel setups"
slug: vex-flywheel-indexer
researched: 2026-06-19
---

# Primary Sources — VEX V5 Flywheel Indexer Mechanisms

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `raw/research/vex-flywheel-structure-parts/index.md` | 2026-06-19 | Motor budget: 4 motors total, 1-motor flywheel frees Port 3 (claw motor, 18:1), 2-motor flywheel leaves no free motor |
| S2 | web | https://wiki.purduesigbots.com/hardware/shooting-mechanisms/flywheel | 2026-06-19 | Double flywheel uses 2 motors; ratchet described as coasting mechanism; indexer not covered in detail on this page |
| S3 | web | https://www.vexforum.com/t/sooo-spin-up-meta-is/102027?page=25 | 2026-06-19 | Community consensus: "Without pneumatics or free motors, a ratchet seems like your best option" |
| S4 | web | https://wiki.purduesigbots.com/hardware/shooting-mechanisms/linear-puncher | 2026-06-19 | Linear puncher mechanism: rack-and-pinion + slip gear + rubber band; slower fire-rate than flywheel; single ball per cycle |
| S5 | web | https://www.vexforum.com/t/how-to-build-the-indexer-without-using-pneumatics/106441 | 2026-06-19 | "ratchet your intake to power a linear puncher to push discs into the flywheel, or double ratchet the flywheel motor to spin a wheel style indexer"; confirms motorless ratchet approach |
| S6 | web | https://www.youtube.com/watch?v=gNs56uY7U_A | 2026-06-19 | "Really simple design that uses 0 pneumatics / 2 motor flywheel @ 4200 rpm / 1 motor indexer @ 200 rpm" — confirms dedicated 1-motor roller indexer at 200 RPM (18:1 cartridge) |
| S7 | web | https://www.vexforum.com/t/intake-mechanism-question-advice/113120 | 2026-06-19 | "switch to a wheel indexer…basically just slap a flex wheel on the flywheel so that just the top of the wheel makes contact with the disc" — compact roller indexer technique |
| S8 | web | https://www.vexforum.com/t/is-it-possible-to-build-an-indexer-without-using-pneumatics-or-custom-cut-pieces-like-slip-gears/107070 | 2026-06-19 | "1m intake and a separate 1m conveyor. This allows the robot to hold up to 3 discs before it goes to shoot." — confirms motor-driven indexer staging approach |
| S9 | web | https://kb.vex.com/hc/en-us/articles/360035592932-Selecting-a-V5-Assembly | 2026-06-19 | "usually activated using a motor, a motor with a gear/sprocket system, or a pneumatic cylinder system"; conveyors use Tank Tread Kit |
| S10 | codebase | `raw/research/vex-v5-booster-kit/index.md` | 2026-06-19 | Booster Kit includes 4× Rack Gear (276-1957), 3× Motor Clutch (276-1098), 4× Intake Roller (276-1499) — parts for Types B and D |

## Excerpts

### S3 — VEX Forum: Spin Up Meta (page 25)
https://www.vexforum.com/t/sooo-spin-up-meta-is/102027?page=25
> "Without pneumatics or free motors, a ratchet seems like your best option. Lots of examples on youtube."

### S5 — VEX Forum: How to build indexer without pneumatics
https://www.vexforum.com/t/how-to-build-the-indexer-without-using-pneumatics/106441
> "You could probably ratchet your intake to power a linear puncher to push discs into the flywheel, or double ratchet the flywheel motor to spin a wheel style indexer. so the indexer is ratcheted off of the intake. the intake and roller can go forwards and backwards. and the indexer is activated when the intake reverses."

### S6 — YouTube: Very simple flywheel shooter and indexer
https://www.youtube.com/watch?v=gNs56uY7U_A
> "Really simple design that uses 0 pneumatics / 2 motor flywheel @ 4200 rpm (Blue cartridge with 7:1 ratio) / 1 motor indexer @ 200 rpm"

### S7 — VEX Forum: Intake mechanism question/advice
https://www.vexforum.com/t/intake-mechanism-question-advice/113120
> "One thing you could do, is switch to a wheel indexer it's not hard to build and it works really well for rapid fire. It is much more compact, you basically just slap a flex wheel on the flywheel so that just the top of the wheel makes contact with the disc"

### S4 — Purdue SIGBots Wiki: Linear Puncher
https://wiki.purduesigbots.com/hardware/shooting-mechanisms/linear-puncher
> "The puncher is drawn as the rack and pinion set moves the rack away from the ball, and then when the shaved section of the pinion gear reaches the rack, the rack is released and shoots forward. The shooting is powered by rubber bands (not shown, but connected from the standoff on the back of the rack c-channel to the front of the assembly)."
