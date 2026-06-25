---
id: fixed-arm-flywheel-retrofit
title: Fixed-Arm Flywheel Retrofit
aliases: [Stationary Arm Flywheel Mount, Flywheel Arm Retrofit, Arm-Mounted Flywheel Cassette]
updated: 2026-06-25
sources:
  - ../../raw/research/flywheel-arm-retrofit/index.md
  - ../../raw/research/flywheel-plate-recut-plan/index.md
tags: [vex-v5, flywheel, retrofit, mechanical-design, arm]
---

# Fixed-Arm Flywheel Retrofit

A fixed-arm flywheel retrofit converts the VEX V5 Clawbot arm from a moving actuator into a **stationary structural tower** that carries a bolt-on flywheel cassette. The key rule is that **the arm must be mechanically locked with metal structure before the flywheel is attached**. Disabling, unplugging, or removing the arm motor is not enough because it removes active holding torque and does not create a reliable load path for high-speed flywheel vibration.

The preferred pattern is a sandwich assembly: inner/outer adapter plates bolt through existing arm holes; flywheel side plates mount to the adapter layer; #8-32 standoffs set the plate spacing; bearings on both flywheel plates support the shaft; collars/spacers locate the wheel; and diagonal bracing ties the cassette or fixed arm back to the chassis/tower. This keeps the rotating assembly self-contained and makes the arm interface mostly structural.

For the `5x10 + 5x5` recut option, those labels are VEX hole-grid counts, not inch dimensions. The two `5x10` pieces are nominally 2.5 in x 5.0 in by hole-count times pitch and become the flywheel cassette side plates. The two `5x5` pieces are nominally 2.5 in x 2.5 in and become gussets or motor brackets at the fixed-arm adapter layer. The diagrams use the photographed Clawbot side profile: front lower arm pivots at the left, paired diagonal arm channels rise to the rear tower, and the cassette mounts outboard of the rear tower/arm interface.

![Fixed-arm 5x10 flywheel side layout](assets/fixed-arm-flywheel-5x10-side-layout.svg)

![Fixed-arm 5x10 flywheel exploded stack](assets/fixed-arm-flywheel-5x10-exploded-stack.svg)

Use this pattern when the arm cannot or should not be fully disassembled into C-channel side plates. If spare C-channels are available, the older C-channel frame in relates_to::[[vex-flywheel-structure-parts]] remains valid. If only plates and spacers are available, this retrofit is the safer concept: the former arm becomes the mount, while the cassette carries the motor, bearings, shaft, and flywheel.

Validation checklist before spinning the wheel: arm cannot drift by hand; diagonal brace is installed; both shaft ends are bearing-supported; collars remove side play without binding; wheel clears the arm under vibration; flywheel motor is aligned to the shaft/gear path; former arm motor is removed from commands; wires are strain-relieved; fasteners are tight.

![Fixed-arm 5x10 flywheel top section](assets/fixed-arm-flywheel-5x10-top-section.svg)

derived_from::[[flywheel-arm-retrofit]]  
derived_from::[[flywheel-plate-recut-plan]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[scoop-and-flywheel-build-diagrams]]  
relates_to::[[vex-v5-motor-cartridges]]  
relates_to::[[vex-v5]]
