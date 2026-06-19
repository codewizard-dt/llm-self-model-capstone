---
id: vex-flywheel-indexer
title: VEX Flywheel Indexer
aliases: [Indexer, Ball Indexer, Disc Indexer, Flywheel Loader]
updated: 2026-06-19
sources:
  - ../../raw/research/vex-flywheel-indexer/index.md
tags: [vex-v5, flywheel, indexer, mechanism, motor-budget]
---

# VEX Flywheel Indexer

An **indexer** is the sub-mechanism that holds a game piece (ball or disc) in a staging position and feeds it into a spinning flywheel wheel on command. It decouples loading from firing — the piece sits ready while the flywheel reaches target RPM, then a brief actuation pushes it in for a consistent shot.

## Motor Budget Controls Indexer Type

The Clawbot has 4 motors. The flywheel consumes 1 or 2 of the repurposed arm/claw motors, leaving different resources for the indexer:

| Flywheel config | Free motor for indexer? | Recommended indexer |
|---|---|---|
| **1-motor flywheel** (arm motor only) | ✅ Claw motor (Port 3, 18:1) | **Type A — roller** |
| **2-motor flywheel** (arm + claw) | ❌ None | **Type B — ratchet** (or buy 5th motor) |

## Type A — Roller Indexer (Simplest, Zero New Parts)

A rubber-surfaced wheel on a short C-channel bracket presses against the staged game piece. The freed **claw motor (Port 3, 18:1 cartridge)** drives it.

- **Hold**: `indexer_motor.stop(HOLD)` — wheel grips piece in place
- **Fire**: `indexer_motor.spin(FORWARD, 100, PERCENT)` → wait 400ms → stop
- **Parts**: claw motor + any flex wheel (already purchased) + 4-hole C-channel bracket from arm — **zero additional purchases**
- **Telemetry**: indexer motor `position(DEGREES)` and `current(AMP)` go directly into the `launch_disc` Task Telemetry Contract

```python
# hold
indexer_motor.stop(HOLD)

# fire (call after flywheel_motor.velocity(RPM) > 550)
indexer_motor.spin(FORWARD, 100, PERCENT)
wait(400, MSEC)
indexer_motor.stop(HOLD)
```

## Type B — Ratchet Indexer (No Extra Motor, for 2-Motor Flywheel)

A **Motor Clutch (276-1098)** or hand-fabricated ratchet-and-pawl is mounted on one flywheel motor's secondary shaft. The ratchet freewheels during forward spin. A brief motor **reverse (~150ms)** engages the pawl, driving a pusher arm that shoves the game piece in. The motor immediately returns to forward spin.

- **Hold**: game piece rests against a rubber-band-held stop; ratchet passively freewheels
- **Fire**: `flywheel_motor.spin(REVERSE, 100, RPM)` → wait 150ms → `flywheel_motor.spin(FORWARD, 600, RPM)`
- **Parts**: Motor Clutch 276-1098 (in Booster Kit 276-2232) + rubber bands (#64 for return spring) + C-channel pusher arm
- **Caveat**: flywheel RPM dips at fire — flywheel weight (276-8794) is especially important here to maintain RPM through the event
- **Telemetry**: fire event appears as a brief velocity dip in the flywheel motor telemetry (`velocity(RPM)` drop then recovery)

## What Doesn't Work Without Extra Purchases

| Approach | Why not | Cost to unlock |
|---|---|---|
| Pneumatic cylinder | No pneumatics in Starter Kit | ~$200 add-on kit |
| Rack-and-pinion puncher (Type D) | Rack gear 276-1957 not in Starter Kit | ~$7 (individual) or Booster Kit (276-2232) |
| 5th motor for 2-motor flywheel | Kit ships with 4 motors | $52.99 (276-4840) |

## Indexer Signal in the Task Telemetry Contract

The indexer's actuation produces a detectable signal that extends the `launch_disc` Task Telemetry Contract:

```json
{
  "task": "launch_disc",
  "observed": {
    "flywheel_rpm_at_launch": 582,
    "indexer_current_A": 1.4,
    "indexer_advance_deg": 310,
    "velocity_drop_rpm": 34,
    "recovery_time_ms": 420
  }
}
```

`indexer_advance_deg` (how far the roller turned before the piece left) serves as a proxy for "did the piece actually enter the flywheel gap fully."

exemplified_by::[[vex-flywheel-indexer-research]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[vex-v5]]  
relates_to::[[task-telemetry-contract]]  
relates_to::[[typed-assembly-grammar]]  
relates_to::[[rubber-band-mechanisms]]
