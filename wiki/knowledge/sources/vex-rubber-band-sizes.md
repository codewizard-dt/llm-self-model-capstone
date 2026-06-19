---
id: vex-rubber-band-sizes
title: "Research: VEX Rubber Bands #32 and #64 — Sizes, Materials, and Robotics Uses"
updated: 2026-06-18
sources:
  - ../../raw/research/vex-rubber-band-sizes/index.md
tags: [vex, hardware, rubber-bands, passive-energy, competition]
---

# Research: VEX Rubber Bands #32 and #64

Ingested from derived_from::[[raw/research/vex-rubber-band-sizes/index.md]].

**The #32 and #64 designations are standardized Alliance Rubber Company industry size codes** — not arbitrary VEX-specific numbers. The code encodes flat (unstretched) dimensions: a leading digit indicates the width family, and the trailing digit orders bands within that family by length.

| Size | Flat Length | Width | Metric |
|------|------------|-------|--------|
| **#32** | 3 inches | 1/8 inch | 76 × 3.2 mm |
| **#64** | 3.5 inches | 1/4 inch | 89 × 6.4 mm |

The #64 is slightly longer **and twice as wide** as the #32, making it substantially stronger and capable of storing more elastic potential energy per band.

**VEX Competition legality** (VRC R7): only three sizes are allowed — #32 (3"×1/8"), #64 (3.5"×1/4"), and #117B (~7" diameter). Teams may buy off-brand bands in bulk (commodity sizes at any office supplier) as long as dimensions match. VEX sells official packs in small quantities (often 10-packs) at a cost premium.

**Three material variants** (both sizes available in all three):

| Material | Best use | Mechanism |
|----------|----------|-----------|
| Synthetic (latex) | Latches, triggers, catapults | High elongation, energy storage |
| EPDM | High elongation, durability | Synthetic rubber, similar to latex |
| Silicone | Intake rollers, grip surfaces | Higher friction against plastic |

**Robotics use cases by size** — see relates_to::[[rubber-band-mechanisms]]:

- **#32** — precision and light force: triggers, latches, return springs on lightweight arms, stacking multiple bands to fine-tune tension. Called "the goldilocks size for linear tensioning."
- **#64** — power and grip: lift counterbalancing (reduces motor load ~30%), catapult energy storage, intake rollers. Community default for bulk purchasing; used on scissor lifts (VEX U "In The Zone" competition paper, 2018).
- **Both** — "free energy" passive mechanisms: elastic energy stored by robot geometry that does mechanical work without a dedicated motor.

relates_to::[[vex-v5]]  
relates_to::[[rubber-band-mechanisms]]  
relates_to::[[vex-v5-clawbot-build-instructions]]
