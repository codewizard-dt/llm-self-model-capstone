---
id: vex-v5-motor-cartridges
title: VEX V5 Motor Gear Cartridges
aliases: [V5 Gear Cartridges, Smart Motor Cartridges, 6:1 18:1 36:1 Cartridges, 276-4840]
updated: 2026-06-18
sources:
  - ../../raw/research/vex-v5-customization-grab-pull-throw/index.md
  - ../../raw/research/vex-v5-starter-kit-configurations/index.md
tags: [vex-v5, motor, cartridge, gear-ratio, throw, flywheel, drivetrain]
---

# VEX V5 Motor Gear Cartridges

The [[vex-v5]] Smart Motor (11W) carries a **swappable internal gear cartridge** that sets the motor's output speed-vs-torque profile. Stall torque is **2.1 Nm regardless of cartridge** — the cartridge changes the gear ratio between the motor and its output shaft, trading speed against torque. The Gear Cartridge Kit (part 276-4840) contains all three types. Only the **18:1 (200 RPM)** ships installed in the Classroom Starter Kit; the others are ~$20 add-ons.

## The Three Cartridges

| Cartridge | Ratio | Output Speed | Cap Color | In Starter Kit? | Primary Use |
|-----------|-------|-------------|-----------|-----------------|-------------|
| High-torque | 36:1 | **100 RPM** | Red | No (~$20) | Heavy arm lift, winch, max-force pull, precise positioning |
| Standard | 18:1 | **200 RPM** | Green | **Yes** | Drive base, general-purpose movement |
| High-speed | 6:1 | **600 RPM** | Blue | No (~$20) | **Flywheel / launcher / fast throw** |

A lower ratio (6:1) spins fast with less torque per unit of motor effort; a higher ratio (36:1) moves slowly with much more rotational force. The 18:1 is the balanced middle.

## For Launching / Throwing — the 6:1 (600 RPM, Blue)

This is the decisive choice for improved launching/throwing capability ([[vex-v5-customization-grab-pull-throw]]):

- **Default 18:1 (200 RPM)** through the Clawbot's 84T:12T (7:1) external gear train → only **28.6 RPM at the arm tip** → ~0.45 m/s release velocity. Works as a slow catapult for ~50 g objects over 0.25–0.5 m with rubber-band assist, but limited range.
- **6:1 (600 RPM)** through the same 7:1 external ratio → **4,200 RPM at the flywheel wheel** → **~22 m/s rim speed** → true medium-range flywheel launcher.

The wiki explicitly identifies the 6:1 cartridge as the required add-on to move from "slow catapult" to "fast flywheel" throwing.

## The Other Two

- **36:1 (100 RPM, Red — high-torque):** maximum torque at the cost of speed. Best for lifting heavy arms near the motor's load limit, driving a winch, or maximum-force drivetrain pull. At 100 RPM through a 7:1 arm train, the arm tip turns ~14 RPM — very slow, very strong.
- **18:1 (200 RPM, Green — standard):** general-purpose balance; the only cartridge in the Starter Kit. Used for the Clawbot's tank drivetrain and standard arm motion. The default Clawbot runs entirely on 200 RPM motors.

## Relation to the Typed Grammar

`cartridge` is a free parameter in the Starter Kit configuration space ([[vex-v5-starter-kit-configurations]]). On the base Starter Kit it is locked to 200 RPM (only one cartridge ships). Adding a 6:1 (for a flywheel launcher) or 36:1 (for a high-torque lift) is a **one-step grammar mutation** the LLM self-model would propose and test against telemetry — Gen N → Gen N+1.

relates_to::[[vex-v5]]
relates_to::[[typed-assembly-grammar]]
derived_from::[[vex-v5-customization-grab-pull-throw]]
relates_to::[[vex-v5-starter-kit-configurations]]
relates_to::[[task-telemetry-contract]]
