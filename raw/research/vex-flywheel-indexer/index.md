---
topic: "flywheel indexer mechanism — load a ball/disc and hold it, then shoot on command — for both 1-motor and 2-motor VEX V5 flywheel setups"
slug: vex-flywheel-indexer
researched: 2026-06-19
sources: [./sources.md]
---

# Research: VEX V5 Flywheel Indexer Mechanisms

> The indexer is the sub-mechanism that holds a game piece in the staging area and pushes it into the spinning flywheel wheel on command. For a **1-motor flywheel** (arm motor repurposed), the freed claw motor (18:1 cartridge already in kit) makes a **dedicated roller indexer** trivially achievable with zero new purchases. For a **2-motor flywheel** (both arm + claw motors repurposed), no free motor remains — the best no-extra-motor option is a **ratchet indexer** driven off a momentary flywheel motor reverse, or adding a 5th V5 Smart Motor (276-4840) to dedicate to the indexer.

---

## Research Questions

1. What indexer mechanism types exist for VEX V5 flywheels?
2. Which work without pneumatics or extra motor purchases?
3. How does motor budget interact with 1-motor vs 2-motor flywheel configurations?
4. What parts from the existing Starter Kit / already-purchased flywheel BOM cover each approach?
5. How is "hold then shoot on command" implemented in code?

---

## Current State (Codebase)

From `raw/research/vex-flywheel-structure-parts/index.md` and `wiki/knowledge/entities/tools/vex-v5.md`:

- **Clawbot motor budget**: 4 motors — Port 1 (right drive), Port 10 (left drive), Port 8 (arm), Port 3 (claw)
- **1-motor flywheel** repurposes Port 8 (arm motor) → Port 3 (claw motor) is **free**
- **2-motor flywheel** repurposes Port 8 (arm) + Port 3 (claw) → **no motor free**; drive motors (ports 1, 10) are not available
- The Starter Kit includes: rubber bands (#32 and #64), standard gears (12T, 84T), C-channels (from disassembled arm), #8-32 standoffs, shafts — but **no pneumatics**, **no rack gear**, **no motor clutch**
- The Booster Kit (276-2232, separately purchased) includes: 4× Rack Gear (276-1957), 3× Motor Clutch (276-1098), 4× Intake Roller (276-1499)

---

## Key Findings

### 1. Mechanism Type Taxonomy [S1, S2, S3]

Five distinct indexer approaches exist for VEX V5 flywheels, differing in motor cost, build complexity, and hold-then-fire reliability:

| Type | Extra motors needed | Pneumatics? | Starter Kit parts only? | Fire-rate |
|---|---|---|---|---|
| **A — Dedicated roller (motor)** | 1 | No | Yes (uses claw motor) | ~1/sec |
| **B — Ratchet (motorless)** | 0 | No | Yes + rubber bands | ~0.5/sec |
| **C — Pneumatic cylinder** | 0 | **Yes** | **No** | ~2/sec |
| **D — Rack-and-pinion puncher** | 1 | No | Needs Booster Kit rack gear | ~1/sec |
| **E — Gravity/passive chute** | 0 | No | Yes | Continuous (no hold) |

---

### 2. Type A — Dedicated Roller Indexer (Recommended for 1-Motor Flywheel) [S1, S2]

A **single wheel or rubber roller** driven by a dedicated motor sits just behind the flywheel gap. The game piece rests against the stopped (or reversed) roller and waits. When commanded to fire, the motor spins the roller forward, pushing the piece into the flywheel contact zone.

- **Motor**: Use the freed claw motor (Port 3) at its existing **18:1 (200 RPM) cartridge** — no cartridge swap needed. 200 RPM is ample to push a disc/ball into the flywheel in ~0.3 seconds.
- **Wheel**: Any rubber-surfaced wheel works — a standard traction wheel or a spare flex wheel (already purchased for the flywheel mechanism) works. Even a section of rubber band wrapped around a spool gives enough grip.
- **Hold mode**: Set roller motor velocity to 0 (stopped) or -10% (slight back-pressure to hold piece in place).
- **Fire mode**: Set roller motor to +100% for ~0.3–0.5 seconds, then stop.
- **Parts needed from Starter Kit**: motor (Port 3), 2× C-channel segments (from arm), #8-32 screws. **Zero new purchases** beyond what's already in the flywheel BOM.
- **Code pattern**:
  ```python
  indexer_motor = Motor(Ports.PORT3, GearSetting.RATIO_18_1, False)
  
  # hold
  indexer_motor.spin(FORWARD, 0, PERCENT)
  
  # fire
  indexer_motor.spin(FORWARD, 100, PERCENT)
  wait(400, MSEC)
  indexer_motor.stop(HOLD)
  ```

> **This is the zero-extra-purchase option for 1-motor flywheel.** The freed claw motor + a C-channel bracket + any rubber wheel = a working indexer.

---

### 3. Type B — Ratchet Indexer (Recommended for 2-Motor Flywheel, No Extra Motor) [S1, S3]

A **ratchet and pawl** mechanism connects to one of the flywheel motors via a secondary output shaft. Normally the ratchet freewheels — the flywheel motor spins forward and the ratchet does nothing. When the motor briefly **reverses**, the pawl engages and drives a pusher arm forward, which shoves the game piece into the flywheel. The flywheel then immediately returns to forward spin.

- **Motor**: No dedicated motor — the ratchet is parasitic on one flywheel motor's reverse direction.
- **Timing**: Reverse the flywheel motor for ~100–200ms. RPM drops slightly; game piece enters as the flywheel is recovering. Flywheel weight (276-8794) is especially valuable here to maintain RPM through the fire event.
- **Parts needed**: A ratchet and pawl (the Booster Kit includes a **Motor Clutch 276-1098** which is a ratchet-style mechanism, or fabricate from gears + bent metal). Rubber band for return spring on the pusher arm. C-channel from arm assembly for the pusher rail.
- **Complexity**: Higher than Type A — requires precise ratchet alignment and careful code timing.
- **Code pattern**:
  ```python
  flywheel_motor = Motor(Ports.PORT8, GearSetting.RATIO_6_1, False)
  
  # hold — flywheel at speed, indexer passive
  flywheel_motor.spin(FORWARD, 600, RPM)
  
  # fire — brief reverse triggers ratchet
  flywheel_motor.spin(REVERSE, 100, RPM)
  wait(150, MSEC)
  flywheel_motor.spin(FORWARD, 600, RPM)
  ```

> **Community consensus** [S3]: "Without pneumatics or free motors, a ratchet seems like your best option. Lots of examples on YouTube."

---

### 4. Type C — Pneumatic Cylinder (Best Performance, Not Available Without Extra Purchase) [S2]

A pneumatic cylinder (1" or 2" stroke) pushes the game piece directly into the flywheel gap when triggered. This is the **fastest and most reliable** indexer used in competition — virtually zero fire latency, no motor load, repeatable every ~0.5 seconds.

- **Why not viable for capstone**: The Classroom Starter Kit (276-7010) contains **no pneumatics**. A pneumatics kit runs ~$150–200 additional. Pneumatics require a compressor or pre-charged reservoir, a solenoid valve, tubing, and cylinders.
- **VEX pneumatics SKU**: Air pressure kit ~$189 (276-2175 or equivalent); solenoid valve $30; cylinders $20–40 each.
- **Not recommended** unless the capstone budget specifically includes pneumatics expansion.

---

### 5. Type D — Rack-and-Pinion Linear Puncher [S4]

A linear rack gear (276-1957) is pulled back by a motor and held under rubber-band tension. A **slip gear** (a pinion with some teeth filed/cut off) drives the rack back, then "slips" past the missing teeth, releasing the rack, which springs forward and strikes the game piece into the flywheel.

- **How it holds**: Rubber bands hold the rack forward (toward ball). Motor holds it back. Cut the teeth to trigger the release.
- **Parts**: Rack Gear (276-1957, **in Booster Kit** or buy separately at ~$7 each), pinion gear (12T or 18T from kit), rubber bands (#64 for power), C-channel rails and standoffs for slide, 1 motor (18:1 or 36:1 for torque).
- **Starter Kit only?**: Rack gear (276-1957) is **not in the Classroom Starter Kit** — it's in the Booster Kit (276-2232) or sold individually (~$7–10/pack of 4).
- **Fire rate**: One shot per motor cycle; need to wait for rack to reload. ~1 shot per second at best.
- **Best for**: Ball objects (spherical); works less well for flat discs which can tip off the rack.

---

### 6. Type E — Passive Gravity Chute (No Hold, Not Useful for "Wait-Then-Shoot") [S2]

A sloped channel feeds game pieces into the flywheel continuously by gravity or by a conveyor. There is **no active hold** — pieces flow as fast as they arrive.

- **Not appropriate** for "load and wait" use case — cannot hold the piece in staging for a timed shot.
- **Use case**: Continuous rapid-fire intake → flywheel pipeline (competition use).

---

### 7. Motor Budget Summary

| Config | Flywheel motors | Indexer motor | Remaining motors | Recommended indexer |
|---|---|---|---|---|
| 1-motor flywheel | Port 8 | Port 3 (free, 18:1) | 0 | **Type A — roller** (zero new parts) |
| 2-motor flywheel | Ports 8 + 3 | None free | 0 | **Type B — ratchet** (uses flywheel motor reverse) |
| 2-motor flywheel + 5th motor | Ports 8 + 3 | Port 11 (new 276-4840) | 0 | **Type A — roller** (cleanest; ~$53 motor) |

---

## Constraints

1. **No pneumatics** — Starter Kit does not include pneumatics; adding them is a separate ~$200 purchase. Type C is off the table without this.
2. **Motor cap = 4 by default** — The Classroom Starter Kit ships with exactly 4 motors. 2-motor flywheel exhausts the motor budget and forces a ratchet indexer unless a 5th motor is purchased.
3. **No rack gear in Starter Kit** — Type D (linear puncher) requires the rack gear (276-1957) from the Booster Kit or individual purchase.
4. **Existing rubber bands are #32** — Starter Kit ships with #32 rubber bands (fine for light return springs but not ideal for heavy puncher tension). The Booster Kit includes #64 bands, which are better for a puncher.
5. **Self-model telemetry requirement** — the indexer should produce a detectable signal in the Task Telemetry Contract. Type A (roller) naturally provides `position(DEGREES)` and `current(AMP)` telemetry from the indexer motor. Type B (ratchet) shows as a brief velocity dip on the flywheel motor telemetry — less clean but still observable.

---

## Solution Comparison

| Criteria | A — Roller (motor) | B — Ratchet (motorless) | D — Rack puncher |
|---|---|---|---|
| **Extra parts needed** | None (uses free claw motor + existing parts) | Motor Clutch/ratchet (Booster Kit) | Rack gear (Booster Kit or ~$7) |
| **Extra motor needed** | Yes (1, but it's already free in 1-motor-flywheel config) | No | Yes (1) |
| **Works with 2-motor flywheel** | Only with 5th motor purchase | ✓ (motorless) | Only with 5th motor |
| **Build complexity** | Low | High | Medium |
| **Hold reliability** | Excellent (motor holds piece) | Good (rubber band holds piece on pawl) | Good (rubber band holds rack) |
| **Telemetry signal** | Clean (indexer motor position + current) | Indirect (flywheel velocity dip) | Clean (indexer motor position) |
| **Fire latency** | ~300–500ms | ~150–200ms | ~200–400ms |
| **Fire rate** | ~1/sec | ~0.5/sec | ~0.75/sec |
| **Starter Kit only?** | ✓ (1-motor flywheel) | With Booster Kit or hand-made ratchet | Needs rack gear |

---

## Recommendation

### For 1-motor flywheel → **Type A roller indexer** (immediate, zero new parts)

Use the freed claw motor (Port 3, 18:1 cartridge). Mount any rubber-surfaced wheel on a short C-channel bracket angled to press against the game piece staging position. Hold = motor stopped. Fire = motor at 100% for 400ms then stop.

**Implementation outline:**
1. Mount a short (4-hole) C-channel segment at the rear of the flywheel frame opening, angled toward the game piece entry.
2. Attach a 2" flex wheel (already purchased for flywheel) on a standard 1/8" shaft through the C-channel, driven by the claw motor (Port 3) via the existing 12T gear coupling.
3. In VEXcode Python:
   - Idle: `indexer_motor.stop(HOLD)` (piece rests against stopped wheel)
   - Fire: `indexer_motor.spin(FORWARD, 100, PERCENT)` → `wait(400, MSEC)` → `indexer_motor.stop(HOLD)`
4. Add indexer motor `current(AMP)` and `position(DEGREES)` to the `launch_disc` Task Telemetry Contract as `indexer_current_A` and `indexer_advance_deg`.

### For 2-motor flywheel → **Type B ratchet** or **add a 5th motor**

- **No budget for 5th motor**: Build a ratchet from the Motor Clutch (276-1098) in the Booster Kit, or fabricate a simple pawl from a bent C-channel piece + rubber band return. Wire it off one flywheel motor's reverse shaft output.
- **Budget allows 5th motor**: Buy one V5 Smart Motor (276-4840, ~$52.99) and use it as a Type A roller indexer. This is the cleanest solution but adds cost.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Roller doesn't have enough grip to push game piece against spinning flywheel backpressure | Use 60A (firm) flex wheel; increase roller motor speed; add #64 rubber band to hold piece against roller |
| Game piece jams between roller and flywheel gap | Tune gap width to game piece OD; ensure piece enters at correct angle; add a guide rail (C-channel lip) above the entry |
| Ratchet indexer fires on startup before flywheel reaches speed | Gate fire command behind `if flywheel_motor.velocity(RPM) > 550` |
| Indexer pulse too short — piece partially fired | Extend pulse to 500ms; monitor indexer position to detect full advance |

---

## Next Steps

- **1-motor flywheel path**: No further purchases needed for indexer. Mount claw motor + small bracket to flywheel frame, wire Port 3 in VEXcode.
  `/task-add "Wire roller indexer: mount claw motor bracket on flywheel frame, add Port 3 to VEXcode, implement fire() function with 400ms pulse + telemetry logging"`
- **2-motor flywheel path (no extra motor)**: Source a Motor Clutch (276-1098) — in Booster Kit. Design ratchet mount on flywheel sideplate.
  `/task-add "Build ratchet indexer for 2-motor flywheel: mount Motor Clutch 276-1098 on arm C-channel, tune reverse pulse timing, log flywheel velocity dip as fire telemetry"`
- **Decision needed**: `/decision-create "Indexer type: Type A roller (simpler, free motor) vs Type B ratchet (no extra motor, harder to build)"`
- **To ingest**: Run `/wiki-ingest raw/research/vex-flywheel-indexer/index.md`
