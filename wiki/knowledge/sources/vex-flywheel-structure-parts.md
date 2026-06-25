---
id: vex-flywheel-structure-parts
title: Research — VEX V5 Minimal Structural Parts for a Flywheel Setup
updated: 2026-06-25
sources:
  - ../../raw/research/vex-flywheel-structure-parts/index.md
  - ../../raw/research/vex-order-2026-06-25/index.md
tags: [vex-v5, flywheel, structure, hardware, morphology, bom]
---

# Research: VEX V5 Minimal Structural Parts for a Flywheel Setup

Structural companion to relates_to::[[vex-launch-disc-parts]], which covers the flywheel mechanism parts (flex wheels, cartridge, VersaHex adapters). This source documents the **frame and fastener parts** — the C-channels, shaft bearings, shaft collars, and hardware needed to physically mount a flywheel on the Clawbot — and clarifies what is already in the Classroom Starter Kit vs. what must be purchased.

## Frame Anatomy

A single-flywheel disc launcher requires five structural sub-systems:

1. **Two C-channel side plates** — the frame walls. The V5 Clawbot arm/claw assembly uses 1×2×1 C-channels and U-channel angles; **when the arm is disassembled for the `launch_disc` morphology swap, those pieces are directly repurposable as flywheel side plates** — no purchase needed.
2. **Standoffs (#8-32)** — space the two side plates apart to match the shaft length. Already in the Starter Kit in appropriate lengths.
3. **HS Shaft Bearings (276-3521)** — the **single most critical gap** vs. the Starter Kit. Standard Bearing Flats have a 1/8" bore and **cannot support the V5 Smart Motor's 1/4" HS shaft**. The dedicated HS Shaft Bearing is not included in the Starter Kit.
4. **HS Clamping Shaft Collars (276-6102)** — similarly, standard shaft collars (276-2010) are sized for 1/8" shafts and cannot clamp the HS shaft. Must be purchased.
5. **Backplate** — any flat steel/aluminum plate from the existing kit; no additional purchase.

**The V5 Smart Motor mounts directly to a C-channel** using 4× standard #8-32 screws (already in kit). No special motor bracket or adapter is needed.

> **Inventory update, 2026-06-25:** derived_from::[[vex-order-2026-06-25]] records that the current known build inventory has **no spare U-channels and no spare C-channels**. The C-channel side-plate approach below remains valid when arm C-channels are available, but the immediate build plan must use a plate-and-spacer sandwich based on the ordered 5x15 steel plates, available spacers, and measured non-VEX perforated steel where appropriate.

## The Standoff Sandwich Trick

A key design technique avoids drilling holes in C-channel: **VEX 2", 3", and 4" HS shafts are designed ~1mm shorter than their corresponding #8-32 standoffs**. By using same-length standoffs to hold the two C-channels apart, the HS shaft rests on the HS Shaft Bearings (which mount to the inner face of each C-channel) without the shaft needing to pass through the structural metal at all. No drilling required.

## Purchase BOM — Arm Repurposed (Recommended)

With the Clawbot arm disassembled and C-channels reused, only **3 purchase lines** are needed for the structural frame:

| # | SKU | Part | Qty needed | Why |
|---|-----|------|-----------|-----|
| 1 | **276-3521** | HS Shaft Bearing (10-pack) | 1 pack, use 2 | Supports 1/4" HS shaft — NOT in Starter Kit |
| 2 | **276-6102** | HS Clamping Shaft Collar | 1 pack, use 2 | Retains shaft axially — NOT in Starter Kit |
| 3 | **276-3440** | HS Shaft 2" Long (4-pack) | 1 pack, use 1 | Flywheel axle between side plates |

If new C-channels are needed (arm kept intact): add **276-2906** (1×2×1×35 Steel, 2-pack) or **276-2288** (1×2×1×25 Aluminum, 6-pack) as a 4th purchase.

All other hardware — standoffs, #8-32 screws, keps nuts, nylock nuts — is already in the Starter Kit.

derived_from::[[vex-launch-disc-parts]]  
relates_to::[[vex-v5]]  
relates_to::[[vex-flywheel-disc-launcher]]  
relates_to::[[typed-assembly-grammar]]
