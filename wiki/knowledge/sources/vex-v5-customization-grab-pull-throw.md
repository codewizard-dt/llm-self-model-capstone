---
id: vex-v5-customization-grab-pull-throw
title: "Research: VEX V5 Starter Kit — Grab/Pull/Throw Capability & Quantification"
aliases: [VEX V5 Task Capability Research, Grab Pull Throw Research]
updated: 2026-06-16
sources:
  - ../../raw/research/vex-v5-customization-grab-pull-throw/index.md
  - ../../raw/research/vex-v5-customization-grab-pull-throw/sources.md
tags: [research, vex-v5, telemetry, quantification, capability, grab, pull, throw]
---

# Research: VEX V5 Starter Kit — Grab/Pull/Throw Capability & Quantification

A 2026-06-16 research report defining the capability envelope and quantification contracts for three physical task primitives on the [[vex-v5]] Classroom Starter Kit. **GRAB and PULL are achievable with the base kit alone; THROW works in slow-catapult form with the base kit and at full flywheel speed with a $20 add-on cartridge.** All three produce rich motor telemetry that maps directly onto the [[llm-authored-self-model]]'s capability layer and [[reality-gap]] gap model. grounds::[[task-telemetry-contract]] evaluates::[[vex-v5]]

## Motor Telemetry — The Measurement Primitive

Every V5 Smart Motor 11W exposes at runtime: **`torque()` (0–2.1 Nm), `current()` (0–2.5 A), `velocity()` (RPM), `position()` (degrees), `power()` (W), `temperature()`**. The PID runs at 10 ms. Stall torque is 2.1 Nm; continuous operating point is ≤ 0.735 Nm (35% of stall) at max speed. Three swappable gear cartridges: 6:1 (600 RPM, high speed), 18:1 (200 RPM, default in Starter Kit), 36:1 (100 RPM, high torque). Only the 18:1 ships in the Starter Kit; the 6:1 needed for flywheels is ~$20 extra.

## Grab

Clawbot claw (port 3, 12T gear, motor-driven) closes until stall against object. **Grip force ≈ `claw_motor.torque() / moment_arm` (up to ~42 N stall, ~14.7 N continuous).** Object detection: `velocity < 5 RPM AND current > 1.5 A` → gripped boolean. Object width proxy: open_degrees − `claw_motor.position()`. Full quantification in [[task-telemetry-contract]].

## Pull

Two drive motors on 4" wheels (r = 50.8 mm). **Max pull: 2 × 2.1 Nm / 0.0508 m ≈ 82.7 N; continuous: ~29 N.** Load ratio = `actual_velocity / set_velocity` (drops toward 0 under heavy load). Pull force estimate = `(left.torque() + right.torque()) / 0.0508`. Winch & Pulley Kit add-on enables higher mechanical advantage.

## Throw

- **Slow catapult (base kit):** arm motor at 200 RPM ÷ 7:1 = 28.6 RPM (171°/s) + #32 rubber bands (included). Release velocity ≈ 0.45 m/s at 150 mm arm; with rubber-band assist, suitable for ~50 g objects over 0.25–0.5 m.
- **Fast flywheel (6:1 cartridge + parts):** 600 RPM × 7:1 external ratio = 4200 RPM at wheel → 22 m/s rim speed → medium-range throw.
- **Throw quantification:** `arm_motor.velocity()` × arm_length = release velocity → `v²sin(2θ)/9.81` = predicted range. AI Vision Sensor or Distance Sensor measures observed landing → gap residual.

## Scalability

The kit is **explicitly "scalable — add any components, additional motors, metal, aluminum and pneumatics."** V5 Brain: 21 Smart Ports (4 used by Clawbot → 17 free). Specialty kits add: Linear Motion (rack & slide), Winch & Pulley, Advanced Mechanics (slip-gear catapult release), Tank Tread. V5 Pneumatics (276-8750, 100 psi) enables fast single-shot throws and clamp actuators.

relates_to::[[typed-assembly-grammar]]
relates_to::[[llm-authored-self-model]]
relates_to::[[reality-gap]]
derived_from::[[vex-v5-clawbot-build-instructions]]
