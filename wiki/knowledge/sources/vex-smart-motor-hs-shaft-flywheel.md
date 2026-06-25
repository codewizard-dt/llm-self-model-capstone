---
id: vex-smart-motor-hs-shaft-flywheel
title: VEX Smart Motor, High Strength Shaft, and Flywheel Fit
updated: 2026-06-25
sources:
  - ../../../raw/research/vex-smart-motor-hs-shaft-flywheel/index.md
tags: [source, vex-v5, flywheel, high-strength-shaft, smart-motor, compression-wheel]
---

# VEX Smart Motor, High Strength Shaft, and Flywheel Fit

This source corrects the immediate flywheel build path. The **V5 Smart Motor can accept both 1/8 in standard shafts and 1/4 in High Strength shafts**, so the motor socket is not the problem. The mechanical conflict is that **1/4 in HS shafts do not pass through normal VEX structural steel holes**. VEX's normal solutions are either to keep the shaft between HS bearings mounted to structural plates, or to drill/notch a 5/16 in / 8 mm clearance hole where the HS shaft must pass through metal.

The purchased relates_to::[[vex-v5]] compression wheel kit (276-8882) remains useful. Official VEX product data says the 2 in 60A kit includes both **1/4 in square-bore VersaHex adapters** and **1/2 in hex to 1/8 in square adapters**. That means the foam golf ball prototype should use a standard 1/8 in shaft first: it passes through unmodified plate holes, fits the motor socket, and mounts the compression wheel with the included adapter.

For the current foam golf ball, relates_to::[[vex-flywheel-disc-launcher]] should treat the 1/8 in shaft route as the immediate proof-of-function path. The HS shaft cassette remains a stronger fallback if the 1/8 in shaft visibly bends, slips, or wobbles, but it must not be drawn as passing through unmodified VEX plate holes.

derived_from::[[vex-order-2026-06-25]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[fixed-arm-flywheel-retrofit]]  
relates_to::[[scoop-and-flywheel-build-diagrams]]  
relates_to::[[vex-v5]]
