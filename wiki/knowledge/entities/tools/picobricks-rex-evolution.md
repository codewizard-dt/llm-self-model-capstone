---
id: picobricks-rex-evolution
title: PicoBricks REX Evolution 8in1
aliases: [REX Evolution, REX 8in1, PicoBricks REX]
updated: 2026-06-16
sources:
  - ../../../raw/research/picobricks-rex-vs-vex-v5/index.md
tags: [tool, hardware, robotics, esp32, rejected-platform]
---

# PicoBricks REX Evolution 8in1

A Turkish-made consumer/educational hobby robot kit from **Robotistan** (sold via Picobricks), priced at **$164.99** and positioned as "8 robot designs in one box at a friendly price" for children and adult hobbyists learning Python. The REX Main Board is built on an **ESP32E** (dual-core, 240 MHz, WiFi 802.11 b/g/n + BLE) with **4× DC-motor ports and 4× servo ports**, an **MPU6050** IMU, **HC-SR04** ultrasonic and IR sensor connectors, a buzzer, and on-board battery charging. It is programmed via RexIDE (web), Thonny (MicroPython), Arduino IDE (C++), or MicroBlocks. Its plastic body parts build **8 fixed configurations** — RoverBot, SonicBot, SumoBot, TrackerBot, BalanceBot, WiBot, OmniBot, ArmBot — with 3 interchangeable wheel options and no published parts-SKU system.

**Evaluated as a Stage-2 alternative to [[VEX V5]] and rejected.** Its DC motors are open-loop (no encoders, no current sensing) and its servos are standard RC servos with no feedback bus, so it exposes **no motor telemetry**. That disqualifies it as the project substrate, because the [[Task Telemetry Contract]]'s `observed` block requires per-actuator torque/current/velocity/position that the REX physically cannot provide. evaluated_against::[[VEX V5]], rejected_for::[[Task Telemetry Contract]]. Full comparison: see [[picobricks-rex-vs-vex-v5]].
