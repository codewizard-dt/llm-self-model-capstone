---
id: thames-kosmos-robotics-workshop
title: Thames & Kosmos Robotics Workshop with Micro:Bit (THK620401)
aliases: [Thames Kosmos Robotics Workshop, THK620401, TK-620401]
updated: 2026-06-16
sources:
  - ../../../raw/research/picobricks-rex-vs-vex-v5/index-2.md
tags: [tool, hardware, robotics, microbit, rejected-platform]
---

# Thames & Kosmos Robotics Workshop with Micro:Bit (THK620401)

A modular plastic snap-together STEM kit (SKU 620401, grades 3–12+) built around a **BBC micro:bit** MCU. It includes **248 snap-together plastic building pieces**, **14 predefined robots plus free-form construction**, **multiple DC motors and 1 standard RC servo**, **2× HC-SR04** ultrasonic sensors, and is programmable in MakeCode / Python / JavaScript over USB or Bluetooth. Expandable with add-on component packs (servo, color/RGB, IR). Price ~$130–280 depending on retailer.

It is **the most flexible of the three alternatives** evaluated against [[VEX V5]] — the 248-piece free-form system is the closest analog to a typed parts vocabulary among the rejected platforms, and the curriculum depth (14 builds + 20 experiments) is real. **But it was rejected as a Stage-2 platform.** Its DC motors and single standard RC servo provide **no actuator feedback** — position is commanded, not confirmed; load and torque are invisible — and the micro:bit's accelerometer is only a **crude inertial proxy** for collisions, orders of magnitude coarser than per-motor torque/current/velocity. The parts are plastic (not load-bearing for pull/throw forces), have no published SKU specs, and offer no gear-train analog to V5's kinematic primitives. The telemetry gap is fatal for the self-model loop, so it cannot populate the [[Task Telemetry Contract]] `observed` block — though it remains the best of the alternatives for pure curriculum delivery.

evaluated_against::[[VEX V5]]
rejected_for::[[Task Telemetry Contract]]
relates_to::[[picobricks-rex-vs-vex-v5]]
