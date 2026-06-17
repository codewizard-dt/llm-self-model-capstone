---
id: rpi5-camera-module-3-cost
title: "Research: Raspberry Pi 5 Cost — Especially with Camera Module 3"
updated: 2026-06-16
sources:
  - ../../raw/research/rpi5-camera-module-3-cost/index.md
tags: [raspberry-pi, hardware, pricing, procurement, camera]
---

# Research: Raspberry Pi 5 Cost — Especially with Camera Module 3

Pricing research (June 2026) for the relates_to::[[raspberry-pi-5]] + relates_to::[[pi-camera-module-3]] hardware combination used in the capstone vision coprocessor. **Three rounds of LPDDR4-driven price hikes since October 2025 have raised Pi 5 board costs 83–154% above launch**, while Camera Module 3 prices have held steady.

## Pi 5 Current Prices (April 2026, authorized US resellers)

| Model | Launch | April 2026 | Rise |
|-------|--------|-----------|------|
| 1GB | $45 (Dec 2025 new SKU) | $45 | 0% |
| 2GB | $50 | $65 | +30% |
| 4GB | $60 | $110 | +83% |
| 8GB | $80 | $175 | +119% |
| 16GB | $120 | $305 | +154% |

**Price hike timeline:** Oct 2025 (Compute Modules) → Dec 1 2025 (Pi 4/5 first hike; 1GB SKU introduced) → Feb 2, 2026 (second hike) → Apr 1, 2026 (third hike). The 1GB model is held at $45 as a sub-$50 anchor. The Pi Foundation states prices will drop once DRAM market conditions normalize, with no stated timeline.

## Camera Module 3 Pricing (unchanged since Jan 2023)

| Variant | Price | FoV | IR filter |
|---------|-------|-----|-----------|
| Standard | $25 | 75° | Yes |
| NoIR | $25 | 75° | No |
| Wide | $35 | 120° | Yes |
| Wide NoIR | $35 | 120° | No |

The IMX708 sensor is not LPDDR4, so Camera Module 3 has been unaffected by the RAM shortage pricing pressure.

## Cable Compatibility

The Pi 5 uses a **22-pin 0.5mm ("mini") FPC** camera connector; Camera Module 3 ships with a **15-pin 1mm ("standard")** cable. An adapter cable is required. **As of December 4, 2025, Camera Module 3 now ships with both cables in the box** (150mm standard + 200mm Pi 5 adapter) — no separate purchase needed for new orders. Standalone adapter cables cost $1/$2/$3 for 200/300/500mm.

## System Cost Estimates

| Configuration | Board | Camera | PSU | SD | **Total** |
|--------------|-------|--------|-----|----|-----------|
| Minimal: 1GB + Cam3 (board+camera only) | $45 | $25 | — | — | **$70** |
| Headless: 2GB + Cam3 + essentials | $65 | $25 | $12 | $10 | **$112** |
| Practical: 4GB + Cam3 Wide + essentials | $110 | $35 | $15 | $10 | **$170** |
| High-end: 8GB + Cam3 Wide + essentials | $175 | $35 | $15 | $10 | **$235** |

**Recommendation:** For a headless camera node with adequate RAM headroom, **4GB Pi 5 ($110) + Camera Module 3 ($25) = $135** for board+camera. Add official 45W PSU ($15) and 32GB microSD ($10) for ~$160 total. The 2GB ($65) or 1GB ($45) suffices for pure headless streaming to reduce cost by $45–65.

derived_from::[[raspberry-pi-5]]
derived_from::[[pi-camera-module-3]]
