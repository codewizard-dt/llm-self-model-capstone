---
id: lemlib
title: LemLib
aliases: [LemLib, Lem Library]
updated: 2026-06-16
sources:
  - ../../../raw/research/vex-v5-advanced-toolchains/index.md
tags: [tool, software, vex, library, odometry, pid, competition, open-source]
---

# LemLib

An open-source relates_to::[[pros]] template for the relates_to::[[vex-v5]] that adds competition-grade autonomous navigation algorithms. The most widely adopted PROS library in VEX V5 competition robotics.

## What It Provides

- **Odometry**: tracks robot position (x, y, heading) in 2D space using any combination of internal motor encoders (IME), V5 Rotation Sensors, V5 Optical Shaft Encoders, and/or V5 Inertial Sensor (IMU). Output: continuous pose estimate `{x, y, heading}`.
- **PID control**: tunable proportional-integral-derivative controllers for precise motor and drivetrain control.
- **Pure Pursuit**: path-following algorithm that smoothly navigates waypoint lists.
- **Monte Carlo Localization**: higher-accuracy pose estimation via particle filtering.

## Capstone Relevance

LemLib transforms the relates_to::[[vex-v5]] Brain from "motor encoder counts" to "pose telemetry." Instead of raw `motor.position(DEGREES)` readings, the Brain emits `{x: 480, y: 12, heading: 2.1}` after each action. The relates_to::[[llm-authored-self-model]]'s capability self-model can then:

- **Predict**: "driving forward 500mm → expected pose `{x=500, y=0, heading=0°}`"
- **Observe**: actual pose from LemLib odometry
- **Gap**: spatial residual `{dx=20, dy=12, dh=2.1°}` feeds the next self-model revision

This is a materially richer relates_to::[[task-telemetry-contract]] than encoder-count-only telemetry.

## Setup Requirements

- Requires PROS environment
- Calibration: physical wheel diameter and chassis track width measurements (millimeter precision)
- IMU calibration on first boot
- Testing recommended on physical robot before competition/demo

## PID as the Core Mechanism

Every motion primitive in LemLib reduces to a relates_to::[[pid-control]] controller. Drive distance uses a drive PID (error = target_distance − odometry_distance); heading uses a separate heading PID (error = target_heading − IMU_heading). LemLib runs its outer PID loop at 20 ms; each loop iteration sends a motor voltage command to the V5 Smart Motors, which close their own inner hardware PID at the motor level. Tuning means finding Kp/Ki/Kd gain triples for each of those motion types. Gains are robot-specific — re-tune whenever morphology changes.

derived_from::[[research-vex-v5-advanced-toolchains]]  
uses::[[pros]]  
uses::[[pid-control]]  
relates_to::[[vex-v5]]  
relates_to::[[llm-authored-self-model]]  
relates_to::[[task-telemetry-contract]]
