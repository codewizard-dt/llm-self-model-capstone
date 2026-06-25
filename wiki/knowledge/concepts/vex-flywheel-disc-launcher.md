---
id: vex-flywheel-disc-launcher
title: VEX Flywheel Disc Launcher
aliases: [Disc Launcher, Flywheel Launcher, Launch Disc Configuration]
updated: 2026-06-25
sources:
  - ../../raw/research/vex-launch-disc-parts/index.md
  - ../../raw/research/vex-order-2026-06-25/index.md
tags: [vex-v5, flywheel, disc-launcher, mechanism, morphology, task-primitive]
---

# VEX Flywheel Disc Launcher

A flywheel disc launcher is a **high-speed rotary-wheel mechanism** that launches disc-shaped objects by contacting them with a spinning wheel. It is an alternative end-effector configuration for the VEX V5 Clawbot — an exclusive swap that replaces the arm+claw assembly and expands the [[typed-assembly-grammar]] with a `launch_disc` primitive.

## Mechanism

A spinning flex wheel (or pair of wheels) stores kinetic energy at high RPM. When a disc is fed into the wheel's contact zone, energy transfers to the disc's edge, launching it. Two designs:

| Design | Wheels | Motor(s) | Notes |
|--------|--------|----------|-------|
| **Single flywheel** | 1 spinning wheel + backplate | 1 | Simpler; backplate is angled steel from existing kit |
| **Double flywheel** | 2 contra-rotating wheels | 1–2 | No backplate needed; higher and more consistent exit velocity |

Single flywheel is the standard for entry-level VRC builds and is the minimum viable approach for the capstone self-model loop.

## Required Speed: 6:1 Cartridge

The **6:1 (600 RPM, blue cap) gear cartridge is the critical prerequisite.** The Classroom Starter Kit ships only 18:1 (200 RPM) cartridges — the arm at 18:1 produces only ~28.6 RPM at the flywheel wheel through a 7:1 external train, yielding ~0.45 m/s rim speed. The 6:1 cartridge through the same external ratio yields 4,200 RPM → ~22 m/s rim speed. This difference is the distinction between a slow catapult and a true flywheel launcher.

See relates_to::[[vex-v5-motor-cartridges]] for full cartridge comparison.

## Minimum Individual Parts (from vexrobotics.com)

| # | SKU | Part | Role | Required? |
|---|-----|------|------|-----------|
| 1 | **276-5842** | V5 Motor 6:1 Cartridge (600 RPM) | Motor speed upgrade | **Yes** (if reusing arm motor) |
| 1 | **276-4840** | V5 Smart Motor & Gear Cartridges | Dedicated flywheel motor | Alt. to 276-5842 if adding motor |
| 2 | **217-6449** | Straight Flex Wheel 3" OD 60A (each) | Flywheel contact surface | **Yes** (1 minimum) |
| 3 | **217-7947** | VersaHex Adapters v2 1/4" Sq., 8-pack | Mounts 2" flex wheels on V5 shaft | **Yes** (2 per wheel) |
| — | **217-8079** | Plastic VersaHub v2 (1/2" hex bore) | Required for 3" or 4" wheels | Yes if using 3"+ wheel |
| 4 | **276-8402** | HS Shaft Ball Bearings (11-pack) | Halves friction vs bearing flats | Strongly recommended |
| 5 | **276-8794** | V5 Flywheel Weight 2-pack | RPM stability between shots | Optional |

**Note:** 2" flex wheels (217-6354) avoid the VersaHub requirement, simplifying the assembly — the wheel mounts directly at the motor output shaft via two VersaHex adapters only.

## Task Telemetry for `launch_disc`

The flywheel launcher produces telemetry that maps cleanly onto the [[task-telemetry-contract]]:

| Signal | Python call | Self-model mapping |
|--------|-------------|-------------------|
| Flywheel speed at shot | `flywheel_motor.velocity(RPM)` | Actual launch RPM → predicted exit velocity |
| Current draw | `flywheel_motor.current(AMP)` | Load; drops post-shot = disc ejected |
| Velocity drop at shot | `velocity_before − velocity_after` | Fraction of stored energy transferred |
| RPM recovery time | time to return to target RPM | Rebound time ↔ flywheel weight effect |
| Observed disc range | AI Vision Sensor / Distance Sensor | Actual vs. predicted range |

Sample `launch_disc` contract:
```json
{
  "task": "launch_disc",
  "predicted": {
    "flywheel_rpm": 600,
    "exit_velocity_ms": 22.0,
    "disc_range_m": 2.0
  },
  "observed": {
    "flywheel_rpm_at_launch": 582,
    "velocity_drop_rpm": 34,
    "current_spike_A": 1.8,
    "recovery_time_ms": 420,
    "disc_range_m": 1.65
  },
  "gap": {
    "rpm_error": -18,
    "range_error_m": -0.35,
    "energy_loss_ratio": 0.057
  }
}
```

The self-model can read this gap and reason: "I predicted 2.0 m range but observed 1.65 m — the flywheel lost 34 RPM at launch; either compression is too high, backplate friction is excessive, or a flywheel weight would reduce the RPM drop."

## Configuration Space Position

`launch_disc` is an **exclusive alternative morphology** — it replaces the `arm+claw` end-effector. The [[typed-assembly-grammar]]'s end-effector node becomes:

```json
{
  "end_effector": ["claw_grasper", "bare_arm", "none", "flywheel_launcher"]
}
```

`flywheel_launcher` requires `cartridge: 600rpm` to be physically viable. With the Starter Kit's 4 motors all occupied, choosing `flywheel_launcher` frees the arm motor for the flywheel while the claw motor becomes unused (or serves as an indexer actuator).

## Ball Bearing Effect

Standard Bearing Flats at flywheel speeds create substantial friction. VEX's own test data shows a bushing-based launcher draws more than double the current of a bearing-based one under identical conditions. Ball bearings (276-8402) are therefore critical for consistent RPM and motor longevity — treating them as optional risks unreliable launch distances in the self-model test loop.

## Structural Frame (from [[vex-flywheel-structure-parts]])

The structural frame for a single flywheel consists of two C-channel side plates, standoffs for spacing, HS Shaft Bearings, and HS Shaft Collars. **When the Clawbot arm is disassembled for the morphology swap, its C-channels are directly reused** — no structural purchase needed. The critical gap vs. the Starter Kit is the shaft support hardware:

| SKU | Part | Role | In Starter Kit? |
|-----|------|------|----------------|
| **276-3521** | HS Shaft Bearing (10-pk) | Supports 1/4" HS shaft — standard Bearing Flats are 1/8" bore only | **No** |
| **276-6102** | HS Clamping Shaft Collar | Retains shaft axially — standard collars are 1/8" bore only | **No** |
| **276-3440** | HS Shaft 2" (4-pk) | Flywheel axle between side plates | No / insufficient |

**Standoff sandwich trick:** 2"/3"/4" HS shafts are ~1mm shorter than same-size #8-32 standoffs. Using standoffs to space the two C-channels lets the shaft rest on HS Shaft Bearings without drilling any new holes in the structural metal.

The motor mounts directly to C-channel with 4× standard #8-32 screws already in the kit. The backplate is any existing steel plate from the kit. Standoffs, screws, keps and nylock nuts are all in the Starter Kit.

### Inventory-Constrained Frame — 2026-06-25

derived_from::[[vex-order-2026-06-25]] changes the immediate build assumption: there are **no spare U-channels or C-channels**. For the next build pass, use a **plate-and-spacer sandwich frame**:

- Use the ordered 5x15 steel plates (SKU 275-2023) as the precision side plates.
- Use existing spacers/standoffs to set the plate separation.
- Mount ordered HS Shaft Bearings (276-3521) to matching plate holes and run the 2" HS shaft (276-3440) through them.
- Retain the shaft with ordered HS clamping collars (276-6102).
- Use non-VEX perforated steel only for a backplate, chute wall, brace, or scoop adapter spine unless its hole spacing is measured and confirmed.

The same principle applies to the scoop: without spare C-channel, a non-VEX perforated plate can serve as the clamp adapter spine for a spoon or dustpan, but it should not be treated as precision VEX structure until measured.

## Indexer (from [[vex-flywheel-indexer]])

The indexer holds the game piece in staging and pushes it into the flywheel on command. Type depends on motor budget:

- **1-motor flywheel** → freed claw motor (Port 3, 18:1) as roller indexer — zero new parts
- **2-motor flywheel** → ratchet via Motor Clutch 276-1098 (Booster Kit) or 5th motor purchase

See relates_to::[[vex-flywheel-indexer]] for full mechanism comparison and code patterns.

## Ball Compatibility (from [[game-object-selection]])

Although this page uses "disc" in its name and the VEX curriculum framing, **the flywheel mechanism works equally well with spherical balls** in the 55–75 mm diameter range. The critical variable is compression, not shape.

**Compression rule**: target ~10% of object diameter as the gap reduction at the backplate. VEX Nothing But Net teams confirmed 0.35–0.5" (9–13 mm) compression on 4" foam balls at competition. For the capstone:

| Object | Diameter | Backplate gap from wheel rim | Notes |
|--------|----------|----------------------------|-------|
| Racquetball | 57 mm | ~51 mm | Recommended; consistent hollow rubber |
| Small foam ball | 55–70 mm | ~50–63 mm | Easier to tune; more variable shot |
| VEX 4" foam ball | 100 mm | ~90 mm | Proven VRC object; too large for scoop |
| Tennis ball | 67 mm | — | Not recommended — felt grabs wheel unevenly |

Objects with zero compressibility (solid rubber, lacrosse balls) slip over the wheel without launching. Objects too soft (sponge) compress completely and absorb all energy.

For the capstone self-model loop, the **racquetball (57 mm)** is preferred because it fits within all three morphology windows (claw, scoop, flywheel) and can persist across morphology swaps. See [[game-object-selection]] for the full three-window analysis.

exemplified_by::[[vex-launch-disc-parts]]
relates_to::[[vex-flywheel-structure-parts]]
relates_to::[[vex-flywheel-indexer]]
relates_to::[[vex-v5]]
relates_to::[[typed-assembly-grammar]]
relates_to::[[vex-v5-motor-cartridges]]
relates_to::[[task-telemetry-contract]]
relates_to::[[llm-authored-self-model]]
relates_to::[[game-object-selection]]
