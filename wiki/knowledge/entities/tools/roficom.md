---
id: roficom
title: RoFI / RoFICoM
aliases: [RoFICoM, RoFI platform]
updated: 2026-06-15
sources:
  - ../../../raw/Feasibility of a Software-Factory Approach to Learning Robots That Assemble Additional Robots from M.pdf
tags: [tool, hardware, connector, modular-robotics, open-hardware]
---

# RoFI / RoFICoM

An open modular-robotics platform (rofi.fi.muni.cz) whose **RoFICoM connector** is singled out as the most strategically aligned hardware for autonomous robot-building. Genderless, 90° symmetric, blind-docking, with **integrated power and data**, automatic orientation detection, and a reconfiguration-focused morphology. Modules expose 3 DoF, IMU, dock-centered ToF sensing, and ESP32 control; the platform is self-buildable from open hardware sources with a listed BOM.

## Why It Matters Here

RoFICoM is the exemplar of [[connector-first-hardware]]: it establishes firm mechanical, power, and data connection **without prior synchronization** and is explicitly designed for desktop 3D printing. Because the connector contributes its own alignment and engagement tolerance, the assembly planner can be simpler and the cell faster — directly shrinking the [[reality-gap]] failure budget. Its **module descriptors / configuration model** let a robot exchange shape+capability metadata and distinguish topology from physical configuration, supporting robot self-identification.

exemplifies::[[connector-first-hardware]]  
relates_to::[[feasibility-modular-blocks-robot-assembly]]
