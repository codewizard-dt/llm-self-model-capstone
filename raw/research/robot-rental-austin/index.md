---
topic: What about robot rentals? Is that a thing in Austin TX? Is there a place where we can rent an appropriate robot for this experiment?
slug: robot-rental-austin
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Robot Rentals in Austin TX for the Capstone Experiment

> Robot rental is **not a viable path** for this experiment in Austin. The only meaningful rental market in Austin is entertainment/party robots (LED dancers, boxing suits) — nothing that resembles a VEX V5 or LEGO SPIKE Prime research platform. The closest realistic alternatives are Asmbly Makerspace (electronics lab membership, no VEX hardware), Cedar Park Library (Dash + Hummingbird robots only), and UT Austin's Texas Robotics (strong VEX U program — potential collaboration angle). **The recommended path is to purchase the hardware directly**, which the project was already planning to do before the June 30 SPIKE Prime retirement deadline.

---

## Research Questions

1. Does a formal robot-rental market for research/educational robots exist in Austin TX?
2. Are there party/entertainment robot rental vendors — and are any suitable for this experiment?
3. Do Austin-area makerspaces have accessible VEX V5 or LEGO SPIKE Prime equipment?
4. Does UT Austin or any institution in Austin loan robotics hardware to outside researchers?
5. Are there national/online rental services that ship to Texas?

---

## Current State (Codebase / Wiki Context)

The capstone's Hardware Acquisition plan (from `wiki/knowledge/sources/research-lego-spike-prime.md` and `wiki/knowledge/sources/vex-v5-classroom-starter-kit.md`) already specifies:

- **Stage 1**: LEGO Education SPIKE Prime — buy now (retires Jun 30 2026), ~$329
- **Stage 2**: VEX V5 Starter Kit (276-7010) — ~$849
- The project needs motor telemetry (encoder position, velocity, torque/current) which eliminates most consumer robot platforms

---

## Key Findings

### 1. Austin's robot-rental market = entertainment only [S1][S2][S3]

Multiple vendors in Austin offer robot rentals — but exclusively for events and entertainment:

- **EPIC Entertainment** — 9-ft LED dancing robots, corporate/party events [S1]
- **Altus Entertainment** — "party robot rentals," trade show activations [S2]
- **Reventals** — life-size boxing (Rock'em Sock'em) suits [S3]
- **The Bash** — lists 9 "party robot" vendors in Austin, avg quote ~$667 [S4]

None of these are programmable research platforms with motor encoders or serial interfaces.

### 2. Asmbly Makerspace (Austin's largest nonprofit makerspace) has no robotics hardware [S5]

Asmbly (9701 Dessau Rd, Austin TX 78754) offers: woodshop, metal shop, laser cutting, electronics lab, 3D printing, ceramics, textiles. Membership ~$65–$99/month. They host combat-robotics **classes** (build-your-own small battle bots) but do **not** maintain a shared VEX V5 or LEGO SPIKE Prime inventory for member use. [S5]

### 3. Cedar Park Library Makerspace has limited educational robots — wrong tier [S6]

Cedar Park Public Library's "Messy Makerspace" (~20 min north of Austin) lends:
- 12× Wonder Workshop **Dash** robots (simple Bluetooth toys)
- **Hummingbird Robotics** classroom set

Neither platform has motor encoders, USB serial, or the telemetry API needed for the Task Telemetry Contract loop. Available to any patron with a Cedar Park library card during Open Lab hours. [S6]

### 4. UT Austin Texas Robotics — VEX U equipment exists; no public lending program [S7][S8]

UT Austin's Texas Robotics program has:
- Active VEX U teams (won 2025 VEX AI World Championship)
- Research labs with industrial robots (Yaskawa, exoskeletons, F1/10 cars)
- Annual high-school Robotics Academy (June 15–27, 2026 — just concluded)

**There is no formal equipment-lending or rental program for external researchers.** However, this is the most credible angle for outreach — a capstone collaboration pitch to a UT Texas Robotics grad student or team mentor could yield supervised access to VEX U hardware. [S7][S8]

### 5. Utility Rentals rents SPIKE Prime — but appears UK-only [S9]

`utility.rentals` offers SPIKE Prime Core Set, Expansion Set, individual motors and sensors for rental. The site's language ("pupils") and product descriptions are UK-centric; no Texas/US shipping confirmed. Suitable as a last resort if US shipping is available, but verification would be needed.

### 6. National online educational robot rental is not an established market in the US [S10]

There is no US equivalent of a short-term VEX V5 or LEGO SPIKE Prime rental service. The robot-rental growth trend visible in 2025–2026 is almost entirely in industrial automation and humanoid robots (primarily China), not educational platforms.

---

## Constraints

- The experiment needs **motor telemetry**: encoder position, velocity, torque/current — rules out all entertainment robots, Dash, Hummingbird, Tamiya, Thames & Kosmos (already evaluated and rejected in prior research)
- Timeline: showcase Jun 29 2026 → hardware needed **now**
- LEGO SPIKE Prime retires Jun 30 2026 — must purchase direct from LEGO Education or a distributor immediately
- VEX V5 Starter Kit is a one-time $849 purchase with lasting utility for the full capstone arc

---

## Solution Comparison

| Option | Platform | Cost | Availability | Telemetry | Verdict |
|--------|----------|------|--------------|-----------|---------|
| Party robot rental | LED dancer / boxing suit | ~$667/event | Immediate | None | ✗ Wrong type |
| Cedar Park Library | Dash / Hummingbird | Free | Same day | None | ✗ Wrong tier |
| Asmbly Makerspace | Electronics lab only | ~$80/mo membership | Same week | Build your own | Partial — useful for electronics, not robot platform |
| UT Austin outreach | VEX U V5 hardware | Free (if approved) | Unknown | Full V5 telemetry | Possible — high effort, uncertain |
| Utility Rentals (UK) | SPIKE Prime | Unknown | Ships from UK | SPIKE Hub | Maybe — UK, verify US shipping |
| **Purchase direct** | **SPIKE Prime + VEX V5** | **~$329 + $849** | **In stock now** | **Full telemetry** | ✓ **Recommended** |

---

## Recommendation

**Purchase the hardware directly.** There is no practical path to renting a research-appropriate robot in Austin, TX. The rental market here is entertainment-only. The project was already on track to buy:

1. **LEGO SPIKE Prime** (~$329, LEGO Education store or Amazon) — buy this week; it retires Jun 30 2026
2. **VEX V5 Starter Kit** (276-7010, ~$849, vexrobotics.com) — needed for Stage 2

**If cost is the binding constraint**, two alternative angles worth one email each:
- **UT Austin Texas Robotics**: email a VEX U team mentor offering to credit them in the capstone demo in exchange for 1–2 supervised sessions with their V5 hardware at their lab
- **Anderson High School ausTIN CANs** (FRC Team 2158): active VEX team in Austin — same pitch

**Do not pursue Asmbly Makerspace** for the robot platform itself; it's useful for fabrication (3D printing mounts, laser-cutting brackets) but won't solve the robot-hardware problem.

---

## Next Steps

- **Immediate**: Purchase LEGO SPIKE Prime before Jun 30 2026 retirement
- **This week**: Order VEX V5 Starter Kit (276-7010) from vexrobotics.com
- **Optional outreach**: Email UT Austin Texas Robotics (robotics.utexas.edu) or Anderson ausTIN CANs with a collaboration pitch if budget is tight
- To create a hardware procurement task: `/task-add Purchase LEGO SPIKE Prime and VEX V5 Starter Kit before Jun 30 deadline`
