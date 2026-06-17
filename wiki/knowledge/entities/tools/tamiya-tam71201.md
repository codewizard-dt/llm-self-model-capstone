---
id: tamiya-tam71201
title: Tamiya TAM71201 Microcomputer Robot (Crawler Type)
aliases: [Tamiya 71201, Tamiya Microcomputer Robot, Tamiya Crawler Robot]
updated: 2026-06-16
sources:
  - ../../../raw/research/picobricks-rex-vs-vex-v5/index-2.md
tags: [tool, hardware, robotics, microbit, rejected-platform]
---

# Tamiya TAM71201 Microcomputer Robot (Crawler Type)

A Tamiya educational crawler kit (item 71201, released July 2019) built on the company's Cam-Program Robot lineage but with the cam autonomy replaced by a **BBC micro:bit** MCU. The kit ships a twin gearbox driving **two 130-type brushed DC motors** (plastic gears, ~3V, very low torque, **no encoders**), an **HC-SR04** ultrasonic sensor for obstacle avoidance, soft-plastic crawler tracks, and a plastic structural body. It builds **one fixed configuration only** — a tracked mini-tank — and has **no arm, claw, or gripper**: it is a mobility-only platform. Programmable in MakeCode / Python / JavaScript via micro:bit; ships with a pre-installed obstacle-avoidance program. MSRP $143 (street ~$50–70).

**Evaluated as a Stage-2 alternative to [[VEX V5]] and rejected.** The 130-type DC motors expose zero actuator telemetry, the kit has no manipulation mechanism at all, and a micro:bit MCU is **Stage-1-class** (the tier characterized by [[lego-spike-prime]] in the feasibility reports) — adopting it would be a regression, not a step-up. With no encoder feedback it cannot populate the [[Task Telemetry Contract]] `observed` block. Useful only for teaching obstacle avoidance; irrelevant to this project's self-model loop.

evaluated_against::[[VEX V5]]
rejected_for::[[Task Telemetry Contract]]
relates_to::[[picobricks-rex-vs-vex-v5]]
relates_to::[[lego-spike-prime]]
