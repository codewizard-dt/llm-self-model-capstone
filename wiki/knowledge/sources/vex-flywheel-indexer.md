---
id: vex-flywheel-indexer
title: Research — VEX V5 Flywheel Indexer Mechanisms
updated: 2026-06-19
sources:
  - ../../raw/research/vex-flywheel-indexer/index.md
tags: [vex-v5, flywheel, indexer, mechanism, morphology, motor-budget]
---

# Research: VEX V5 Flywheel Indexer Mechanisms

The **indexer** is the sub-mechanism that holds a game piece in a staging position and pushes it into the spinning flywheel on command. The critical constraint is motor budget: the Clawbot has 4 motors total, and whether the flywheel uses 1 or 2 of them determines what indexer options are available.

**For a 1-motor flywheel** (arm motor repurposed), the freed claw motor (Port 3, 18:1 cartridge) becomes the indexer motor. A rubber-surfaced roller wheel — including the flex wheel already purchased for the flywheel mechanism — mounted on a short C-channel bracket pushes the piece into the flywheel gap when spun at 100%. Hold mode is simply stopping the motor. **Zero additional purchases required beyond the flywheel BOM.**

**For a 2-motor flywheel** (both arm + claw motors repurposed), no free motor remains. The best no-extra-motor option is a **ratchet indexer**: a Motor Clutch (276-1098, available in the Booster Kit) mounted on one flywheel motor's secondary shaft engages only when that motor briefly reverses (~150ms), pushing the game piece in, then the flywheel immediately returns to forward spin. Alternatively, adding a 5th V5 Smart Motor (276-4840, ~$53) allows the clean roller approach for a 2-motor flywheel. **Pneumatics are not available** in the Classroom Starter Kit; adding them costs ~$200 and is not recommended for the capstone.

| Type | Motor cost | Parts source | Best for |
|------|-----------|-------------|---------|
| **A — Roller** | 1 (claw motor, free in 1-flywheel config) | Kit only | 1-motor flywheel |
| **B — Ratchet** | 0 | Motor Clutch 276-1098 (Booster Kit) | 2-motor flywheel |
| **C — Pneumatic** | 0 | Pneumatics kit (~$200 add-on) | Competition; not for capstone |
| **D — Rack puncher** | 1 | Rack gear 276-1957 (Booster Kit) + motor | Either; more complex |

derived_from::[[vex-flywheel-structure-parts]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[vex-v5]]  
relates_to::[[task-telemetry-contract]]  
relates_to::[[typed-assembly-grammar]]
