---
id: game-object-selection
title: Game Object Selection
aliases: [Ball Selection Criteria, Object Selection Framework, Game Piece Selection]
updated: 2026-06-22
sources:
  - ../../raw/research/game-object-selection/index.md
tags: [concept, vex-v5, morphology, hardware, game-object]
---

# Game Object Selection

The choice of game object is a **cross-cutting constraint** that must satisfy every handling morphology simultaneously. Because the capstone robot can use a claw, a passive scoop, or a flywheel launcher (one at a time), the game object must fit within the intersection of all three mechanism windows — otherwise a morphology swap makes the object unusable and breaks the self-model loop's continuity.

relates_to::[[typed-assembly-grammar]]  
relates_to::[[clawbot-scoop-replacement]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[task-telemetry-contract]]

---

## The Three-Window Intersection

| Morphology | Window |
|-----------|--------|
| Claw sweet spot | 55–75 mm diameter |
| Passive scoop max | ≤ 65 mm diameter |
| Flywheel optimal | 55–75 mm diameter |
| **Intersection** | **55–65 mm** |

Any object in this range — approximately 2–2.5 inches in diameter — is compatible with all three morphologies and can persist across morphology swaps without changing the game piece.

---

## Recommended Object: Racquetball

**Standard racquetball** (US spec: 2¼" / 57.15 mm diameter, ~1.4 oz / ~40 g, hollow rubber, hardness 55–60 Shore durometer) is the recommended game object. It sits at the center of the three-window intersection and excels on every evaluation axis:

- **Graspability**: 57 mm places the claw 30–40 mm from fully closed at first contact — maximum mechanical advantage zone; rubber surface generates friction against claw plates without requiring high torque
- **Scoopability**: fits cleanly inside a standard serving-spoon bowl (~70–80 mm wide); light enough (~40 g) for the arm to lift at modest torque
- **Flywheel launch**: hollow rubber compresses ~10% against the 60A flex wheel — ideal energy transfer; smooth surface = consistent shot-to-shot velocity (±5%); ~40 g = 5–8 m range at 22 m/s rim speed
- **Safety**: hollow construction collapses on impact; harmless at robot-scale velocities (0.45–22 m/s)
- **Durability**: designed for thousands of high-speed wall impacts; outlasts the capstone
- **Cost/availability**: $1–3 each, any sporting-goods store

---

## Flywheel Compression Rule

Compression target: **~10% of object diameter** (derived from VEX Nothing But Net teams who used 0.35–0.5" compression on 4" foam balls). For a 57 mm racquetball, backplate gap = 57 − (57 × 0.10) ≈ **51 mm** from wheel rim. Objects that do not compress at all (solid rubber, metal) slip over the wheel without launching.

---

## Grammar Extension: `game_object` Node

The racquetball's physical parameters become GEN-0 defaults in the [[typed-assembly-grammar]] `game_object` node:

```json
{
  "game_object": {
    "type": "racquetball",
    "diameter_mm": 57,
    "weight_g": 40,
    "material": "hollow_rubber",
    "compressibility": "medium",
    "color": "blue_or_green",
    "cost_usd": 2.0
  }
}
```

This node participates in the [[task-telemetry-contract]]: the object's physical properties directly constrain the predicted grip force, scoop torque, and flywheel launch range in the `predicted` block of each task primitive.

---

## Runner-Up: Small Foam Ball (55–70 mm)

A colored foam ball of 55–70 mm (Nerf-type, any hobby store) is the runner-up. It is marginally better for flywheel launching (easier compression tuning, maximally safe) but slightly worse for claw grip (foam deforms under claw pressure → inconsistent position reading) and worse for flywheel shot-to-shot consistency (compression variance). Prefer if the flywheel is the exclusive launch mechanism and the claw is never used.

---

## Special-Case Objects

- **Wiffle ball (73 mm)**: holes catch claw fingers → most consistent grip position; safe launch; but aerodynamic holes create unpredictable flight. Best for scoop + bin-drop tasks where flight accuracy doesn't matter.
- **VEX 4" foam ball (100 mm)**: proven flywheel game object (VEX Nothing But Net 2015–16); too large for the serving-spoon scoop. Viable if scoop morphology is never used.
- **Avoid**: tennis ball (felt jams flywheel), lacrosse ball (too heavy + safety risk), ping pong ball (claw force crushes it).
