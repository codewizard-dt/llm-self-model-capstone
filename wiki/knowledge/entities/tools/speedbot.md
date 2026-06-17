---
id: speedbot
title: VEX V5 Speedbot
aliases: [Speedbot, TrainingBot, VEX TrainingBot, V5 TrainingBot]
updated: 2026-06-16
sources:
  - ../../../raw/research/vex-v5-starter-kit-configurations/index.md
tags: [tool, hardware, vex-v5, robot-build, drivetrain, gen-0]
---

# VEX V5 Speedbot (TrainingBot)

The **simplest official configuration** of the [[vex-v5]] Classroom Starter Kit — a 2-motor tank drivetrain with no manipulator. VEX's STEM Labs PDF explicitly states: **"The VEX V5 Clawbot is an extension of the VEX Speedbot."** This makes the Speedbot the base morphology from which the Clawbot is derived by adding the arm uprights, 84T:12T gear train, and plastic claw assembly. The VEX build downloads page also documents an equivalent build as the "TrainingBot" ("standard drivetrain that can move forward/reverse and turn — requires Classroom Starter or Classroom Super Kit").

For the capstone LLM self-model loop, the Speedbot is **Gen 0** — the simplest valid grammar sentence from the [[typed-assembly-grammar]], establishing a baseline telemetry profile before any manipulator is added. It uses ports 1 and 6 (or equivalent) for drive motors, leaving ports 3 and 8 free. The [[task-telemetry-contract]] for Gen 0 covers drive-only tasks (pull, navigate). Gen 1 extends it to the full Clawbot (grab, throw). Rebuilding between generations is a ~30-minute human task.

extends_to::[[vex-v5-clawbot-build-instructions]]
used_by::[[physical-robot-software-factory]]
grounds::[[typed-assembly-grammar]]
relates_to::[[task-telemetry-contract]]
