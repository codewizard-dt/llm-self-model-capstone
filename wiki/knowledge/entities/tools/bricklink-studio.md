---
id: bricklink-studio
title: BrickLink Studio
aliases: [Studio, BrickLink Studio]
updated: 2026-06-15
sources:
  - ../../../raw/Feasibility of a Software Factory for LEGO-Based Self-Assembling Learning Robots.pdf
  - ../../../raw/Feasibility of a Human-Built Generational Robot Software Factory.pdf
tags: [tool, software, lego, bom, instructions]
---

# BrickLink Studio

LEGO's official CAD/instruction tool, identified as the most practical LEGO-oriented **instruction + bill-of-materials** layer for a physical-robot software factory. Supports virtual parts, automatic divide-into-steps instructions, submodels, and parts pricing/availability linked to the BrickLink catalog; exports `.io`, `.ldr/.mpd`, `.csv`, `.xml`.

## Role in the Factory

It directly supplies the **Instruction layer** of the [[physical-robot-software-factory]] — turning a design into ordered, human-followable build steps with a priced, available BOM. It also surfaces a data-normalization challenge to solve early: LEGO uses **Design IDs** and **Element IDs** while BrickLink/Studio use **Item Numbers**, so the factory needs all three aligned in one internal schema.

used_by::[[physical-robot-software-factory]]  
relates_to::[[typed-assembly-grammar]]  
relates_to::[[feasibility-lego-self-assembling-robots]]
