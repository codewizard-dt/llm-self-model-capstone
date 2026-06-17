---
id: reality-gap
title: The Reality Gap
aliases: [Sim-to-Real Gap, Simulation-to-Real Mismatch]
updated: 2026-06-15
sources:
  - ../../raw/Feasibility of a Human-Built Generational Robot Software Factory.pdf
  - ../../raw/Feasibility of a Software Factory for LEGO-Based Self-Assembling Learning Robots.pdf
  - ../../raw/research/apriltags/index.md
tags: [concept, robotics, simulation, risk, sim-to-real]
---

# The Reality Gap

The dominant *technical* risk for any physical-robot factory: **designs that score well in simulation fail on real hardware** because of friction, motor backlash, sensor noise, snap-fit tolerances, wheel slip, and occlusion. Named the "reality gap" / "simulation-to-real mismatch" across the feasibility reports, and the reason the best automated-design papers either test in reality or explicitly reason about manufacturability.

## Why It's Acute Here

Robotic assembly is a **snap-fit, tolerance-sensitive, contact-rich** domain. Generic rigid-body simulation does *not* faithfully capture it — this is precisely why BrickSim was purpose-built to model interlocking-brick mechanics. So simulation must be a **layered stack**: ordinary geometry/kinematics for planning, brick-specific mechanics for insertion/disassembly, and **hardware-in-the-loop** for final acceptance.

## Key Empirical Anchor

Carnegie Mellon's vibro-tactile work and the **"Eye-in-Finger"** embedded fingertip-vision result raised calibration-error tolerance from **0.4 mm up to 2.0 mm** — a 5× relaxation that turns a fragile demo into a repeatable cell. The lesson: instrument the contact interface (tool-tip cameras, force/tactile feedback) rather than chase global precision.

## Mitigations (from the reports)

- Start with **narrow tasks, stiff/predictable morphologies, simple terrain**
- **Fiducials/AprilTags + geometric alignment first, learned perception second**
- Aggressive **acceptance testing** + insertion state machines with compliance
- **Learn a residual model** from the sim-vs-real gap and feed it back into both the controller *and* the design prior

This residual-learning loop is what distinguishes a real [[physical-robot-software-factory]] from a one-shot "build and hope" cycle.

threatens::[[physical-robot-software-factory]]  
mitigated_by::[[connector-first-hardware]]  
relates_to::[[typed-assembly-grammar]]  
derived_from::[[feasibility-human-built-generational-factory]]
