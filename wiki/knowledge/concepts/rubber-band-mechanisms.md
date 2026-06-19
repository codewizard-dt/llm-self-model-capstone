---
id: rubber-band-mechanisms
title: Rubber Band Mechanisms (Passive Elastic Energy)
updated: 2026-06-18
sources:
  - ../../raw/research/vex-rubber-band-sizes/index.md
tags: [vex, passive-energy, mechanisms, robotics, competition]
---

# Rubber Band Mechanisms (Passive Elastic Energy)

In VEX robotics, rubber bands are called **"free energy"** by the community — they store elastic potential energy in robot geometry and release it mechanically without consuming a motor port. A well-designed rubber band assist can reduce motor load by ~30%, enabling a 1-motor lift to out-perform a naive 2-motor design.

## The Two Legal Sizes

VRC rules allow three sizes; the two practical ones are:

| Size | Dimensions | Strength | Primary role |
|------|-----------|----------|-------------|
| **#32** | 3" × 1/8" (76 × 3.2 mm) | Light | Precision: triggers, latches, return springs |
| **#64** | 3.5" × 1/4" (89 × 6.4 mm) | Heavy | Power: lift assist, catapults, intake rollers |

The numbers follow the Alliance Rubber Company standard — tens digit encodes width family, ones digit orders by length within the family. See relates_to::[[vex-rubber-band-sizes]] for the full size code explanation.

## Three Material Types

Both #32 and #64 come in three materials with different use cases:

- **Synthetic (latex)** and **EPDM** — high elongation, best for energy storage (latches, catapults, spring returns). EPDM is synthetic and more durable.
- **Silicone** — higher coefficient of friction against plastic; not for energy storage. The correct choice for **intake rollers** where grip on a game piece matters more than elastic return force.

## Core Use Categories

### Counterbalancing / Lift Assist
Rubber bands are routed to offset gravitational load on a lift arm. The bands pre-load against the arm's weight, reducing the motor's duty to moving the arm rather than fighting gravity. Effect: ~30% motor-load reduction; a properly tuned single-motor lift can outperform a double-motor lift with no assist. Use **#64** for heavy arms; **#32** for lighter pivoting assemblies.

### Catapult / Slingshot Energy Storage
A motor rotates a cam that stretches bands; at the release point the cam drops off and the bands fling the lever arm. More band cross-section = more stored energy per unit stretch. Use **#64** (or multiples of #32) for catapult launchers. Relates to the `slip_release` typed primitive in the relates_to::[[typed-assembly-grammar]].

### Intake Rollers
Bands (typically **silicone #64**) are looped between pairs of sprockets to form a rolling surface. The higher friction coefficient of silicone against VEX plastic parts grips game pieces as the sprocket shaft spins. This is an alternative to anti-slip mat and is more compact.

### Triggers and Latches
A lightly-stretched **#32** holds a mechanism in a cocked position until released. Used in one-shot deployment mechanisms (flag launchers, passive claw locks). The narrower band gives a more predictable, lower actuation force.

### Return Springs
Any arm or flap that needs to snap back to a resting position — such as the relates_to::[[vex-v5]] Clawbot claw's passive-close return — uses a rubber band in lieu of a metal spring. The Clawbot uses a rubber band claw return as part of its Gen 0 morphology (see relates_to::[[llm-authored-self-model]]).

## Capstone Relevance

The Clawbot Gen 0 already uses a rubber-band return on the claw (`claw: rubber-band return` in the relates_to::[[typed-assembly-grammar]] vocabulary). Rubber bands also appear in the **slow throw** primitive: `arm motor 7:1 + #32 rubber bands → 0.45 m/s release`. Adding #64 bands to the arm counterbalance is a likely **Gen 1 → Gen 2 mutation** in the self-model evolution loop.

relates_to::[[vex-v5]]  
relates_to::[[vex-rubber-band-sizes]]  
relates_to::[[typed-assembly-grammar]]  
relates_to::[[task-telemetry-contract]]  
relates_to::[[llm-authored-self-model]]
