---
id: feasibility-modular-blocks-robot-assembly
title: "Feasibility: Learning Robots That Assemble Robots from Modular Blocks"
updated: 2026-06-15
sources:
  - ../../raw/Feasibility of a Software-Factory Approach to Learning Robots That Assemble Additional Robots from M.pdf
tags: [feasibility, robotics, modular, connectors, software-factory]
---

# Feasibility: Learning Robots That Assemble Robots from Modular Blocks

A 16-page ChatGPT feasibility report broadening the question beyond LEGO to *any* modular building block. **Verdict: feasible in a bounded sense today — a robot learns to assemble additional robots from pre-manufactured modules in a structured workcell — but not full self-replication from raw materials.** evaluates::[[physical-robot-software-factory]]

## The Decisive Insight: Connector Choice

The report's strategic standout: **the hardware connector is decisive.** LEGO/VEX rely on friction fits, varied geometries, and separate wiring — workable for *learning the problem* but not optimized for robot-friendly assembly. **Cubelets** are easier (magnetic faces already carry power+data). **RoFI/RoFICoM-like open connectors are the most strategically aligned with the goal** — genderless, blind-mate, self-aligning, power+data integrated, with machine-readable module descriptors. Conclusion: *educational kits are good for learning the problem; purpose-built modular robotics is better for solving it.* uses::[[roficom]] relates_to::[[connector-first-hardware]]

## Scope Boundary

"Autonomously build additional robots" spans a wide range. The literature supports the **low/medium interpretations** (modular docking, collective construction, kit-based assembly) but **not** near-term open-world full-stack self-replication. The strongest near-term target is a **constrained assembly family**: assemble one or a few morphologically-related robots from a curated module library, auto-identify the resulting configuration, retrieve/generate the control stack, test, and hand off the finished robot. relates_to::[[typed-assembly-grammar]]

## Evidence Base

Academically well-supported: modular self-reconfigurable robotics (decades of surveys), **TERMES** (decentralized multi-robot 3D construction from passive blocks), and robotic brick assembly — a 2023 framework learned LEGO assembly/disassembly from human demonstration on a FANUC arm; **Eye-in-Finger** (2025/26) achieved sub-mm manipulation, raising calibration tolerance from 0.4 mm to 2.0 mm; **BrickCraft / Prompt-to-Product** decomposed long-horizon interlocking-brick assembly into reusable skills. "Bounded autonomous robot assembly from blocks is no longer speculative."

## Reference Hardware & Learning Stack

A first cell needs a single table-mounted manipulator (overhead RGB-D + wrist camera + fixture-based part presentation); low-cost open arms (**SO-ARM100**) linked to **LeRobot**, or desktop cobots (**UFACTORY Lite 6**, **DOBOT MG400** at ±0.05 mm). Eliminating loose wires is the single biggest mechanical improvement. Learning is **hybrid**: classical planning owns build order/collision/precondition; **imitation learning** for pick-orient-align-seat-verify; **RL** only for contact-rich insertion/recovery. Datasets that matter: BridgeData V2 (60k+ trajectories), DROID (76k), Open X-Embodiment (22 robots, 527 skills). relates_to::[[reality-gap]]

## Software Factory, Legal, Cost

Same mandate: treat robot design, assembly plans, learned skills, sim scenes, and safety constraints as **first-class versioned build artifacts** (DoD DevSecOps + Google MLOps framing). A built robot should **self-identify** — boot, publish its module list/topology/firmware versions, receive its config package, run acceptance tests, then join the fleet. Legal: LEGO Fair Play (no logo/trademark misuse), OSHWA open-hardware definition, **EU AI Act** (major rules from Aug 2, 2026; full roll-out Aug 2, 2027). Illustrative cost: proof-of-concept ~$2k–$8k, functional prototype ~$15k–$45k, pilot ~$75k–$250k — **module design is a bigger cost lever than arm selection.**

> **Bottom line:** combine a software-factory operating model with a connector-first hardware strategy → viable. Combine the software factory with classroom kits alone → likely an impressive demo, not a dependable robot-building system.

derived_from::[[agent-evolution-factory]]  
relates_to::[[human-in-the-loop-replication]]  
relates_to::[[feasibility-lego-self-assembling-robots]]  
relates_to::[[feasibility-human-built-generational-factory]]
