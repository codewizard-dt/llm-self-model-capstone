---
id: flywheel-arm-retrofit
title: Research: Flywheel Arm Retrofit
aliases: [Fixed Arm Flywheel Retrofit, Flywheel Arm Retrofit]
updated: 2026-06-25
sources:
  - ../../raw/research/flywheel-arm-retrofit/index.md
tags: [vex-v5, flywheel, arm, retrofit, hardware]
---

# Research: Flywheel Arm Retrofit

This research answers whether a flywheel plate-and-spacer frame can be assembled onto the existing VEX V5 arm layout after the arm is fixed and its motor is taken out of service. **The answer is yes, but only if the former arm is mechanically locked and braced first; an unplugged motor is not a structural lock.** The former arm should be treated as a fixed tower, not as an actuator.

The recommended assembly is a bolt-on cassette: adapter plates attach to the stationary arm's existing VEX hole pattern; a pair of flywheel side plates are separated with #8-32 standoffs; bearings support both sides of the flywheel shaft; collars and spacers control side play; and diagonal bracing carries launch vibration back to the chassis or tower. The report includes a side-layout diagram and an exploded spacer-frame diagram for how the adapter, plates, standoffs, bearings, shaft, motor, and wheel relate.

The source sharpens the existing flywheel plan by separating **electrical decommissioning** from **mechanical immobilization**. Unplugging or removing the arm motor is reasonable from the V5 control-system side, but the old motor must be removed from code/config and any stiffness it provided must be replaced with structural bracing.

derived_from::[[vex-flywheel-structure-parts]]  
relates_to::[[fixed-arm-flywheel-retrofit]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[scoop-and-flywheel-build-diagrams]]  
relates_to::[[vex-v5]]
