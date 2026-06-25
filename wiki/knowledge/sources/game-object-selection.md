---
id: game-object-selection
title: "Research: Game Object Selection — Graspability, Scoopability, Launchability"
aliases: [Game Object Research, Ball Selection, Object Selection Research]
updated: 2026-06-25
sources:
  - ../../raw/research/game-object-selection/index.md
  - ../../raw/research/game-object-selection/sources.md
  - ../../raw/research/home-depot-inventory-2026-06-25/index.md
tags: [source, vex-v5, hardware, morphology, game-object, clawbot, flywheel]
---

# Research: Game Object Selection — Graspability, Scoopability, Launchability

A 2026-06-22 research report identifying the optimal real-world object for the capstone robot's three handling morphologies: claw grab, passive-scoop pickup, and flywheel launch. **The recommended object is a standard racquetball** (57 mm diameter, ~40 g, hollow rubber, official US spec: 2¼" / 1.4 oz, hardness 55–60 Shore durometer). It is the only common off-the-shelf ball that simultaneously fits the claw's mechanical-advantage sweet spot, fits inside the serving-spoon scoop bowl, compresses correctly against the 3" flex-wheel flywheel, and is safe and durable at robot-scale launch velocities.

derives_from::[[clawbot-scoop-replacement]]  
derives_from::[[vex-v5-customization-grab-pull-throw]]  
derives_from::[[vex-launch-disc-parts]]  
relates_to::[[typed-assembly-grammar]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[task-telemetry-contract]]

---

## Mechanism Constraints

Each of the three morphologies imposes a hard size window on the game object:

| Morphology | Object size constraint | Notes |
|-----------|----------------------|-------|
| **Claw** (port 3, 12T gear) | 50–125 mm; sweet spot **55–75 mm** | Claw fully open ~100–125 mm; closes to stall; objects ≤ 50 mm lose mechanical advantage |
| **Passive scoop** (serving spoon) | **≤ 65 mm** (marginal to 70 mm) | Bowl ~70–80 mm wide; object must slide under and roll onto bowl |
| **Flywheel** (3" flex wheel, 60A) | **55–75 mm** optimal | Compression target ~10% of object diameter; smooth surface required |
| **Slow catapult** (base kit, no flywheel swap) | **≤ 50 g** | Arm at 200 RPM + rubber bands → ~0.45 m/s; 0.25–0.5 m range |

The intersection of all three windows is **55–65 mm** — and the 57 mm racquetball sits at the center.

---

## Candidate Comparison

| Object | Diameter | Weight | Graspability | Scoopability | Flywheel | Safety | Durability |
|--------|----------|--------|-------------|-------------|---------|--------|------------|
| **Racquetball** | 57 mm | ~40 g | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★ | ★★★★★ |
| Small foam ball (55–70 mm) | 55–70 mm | 20–35 g | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★ |
| Wiffle ball | 73 mm | ~20 g | ★★★★★ | ★★★★ | ★★★ | ★★★★★ | ★★★★ |
| Tennis ball | 67 mm | ~57 g | ★★★★★ | ★★★★ | ★★★ | ★★★★★ | ★★★ |
| VEX 4" foam ball | 100 mm | ~60 g | ★★★★ | ★★ | ★★★★★ | ★★★★★ | ★★★★ |
| Ping pong ball | 40 mm | 2.7 g | ★★ | ★★★★ | ★★★ | ★★★★★ | ★★ |
| Lacrosse ball | 64 mm | ~145 g | ★★★★ | ★★★ | ★★★ | ★★★ | ★★★★★ |

Key disqualifiers: tennis ball felt grabs the flywheel unevenly → inconsistent shots; VEX 4" ball (100 mm) does not fit the scoop; lacrosse ball (145 g) is too heavy for the slow catapult and a safety concern at speed; ping pong ball is crushed by claw force.

---

## Flywheel Compression Physics (corrected)

VEX Nothing But Net teams used **0.35–0.5" (9–13 mm) compression** on 4" foam balls — approximately 9–12% of object diameter. The general rule is **target ~10% of object diameter** as backplate gap reduction. For a 57 mm racquetball: gap between wheel rim and backplate = 57 − (57 × 0.10) ≈ 51 mm. Balls that do not compress at all (solid rubber, lacrosse) slip over the wheel and produce zero exit velocity.

---

## Implementation Notes

1. **Procurement**: 3–6 racquetballs, any brand (~$5–10 total); most are already brightly colored (blue, green, purple) — ideal for vision-sensor detection
2. **Claw**: set `max_torque` to ~50% stall to grip without deforming; log `claw_motor.position()` as ball-width proxy
3. **Scoop**: angle bowl 10–15° upward; approach slowly (< 50% drive) so ball rolls onto bowl rather than being pushed off
4. **Flywheel**: backplate gap ≈ 51 mm from wheel rim; target 560–600 RPM; adjust ±1 mm if ball skips (gap too wide) or motor stalls (gap too narrow)

## 2026-06-25 Foam Ball Update

derived_from::[[home-depot-inventory-2026-06-25]] adds very soft foam balls that compress almost flat. These are useful for low-risk scoop pickup and flywheel feed-path tests, but they are **not a strong launch-data candidate** unless testing shows elastic rebound. A flywheel needs the object to compress and then recover; a ball that collapses nearly to zero thickness will likely absorb energy, produce low/inconsistent exit velocity, and hide useful compression-gap telemetry.

relates_to::[[game-object-selection]]
