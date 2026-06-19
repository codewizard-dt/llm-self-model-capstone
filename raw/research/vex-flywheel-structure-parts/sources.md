---
topic: "a minimal list of structural parts from VEX structure catalog to support a flywheel setup, along with any required hardware to attach them"
slug: vex-flywheel-structure-parts
researched: 2026-06-19
---

# Primary Sources — Minimal Structural Parts for a VEX V5 Flywheel Setup

> **User clarification (2026-06-19):** Arm pieces from the Clawbot arm/claw assembly WILL be repurposed for the flywheel frame. This confirms Approach A is the correct path — zero C-channel purchase needed. The BOM reduces to 3 purchase lines: 276-3521 + 276-6102 + 276-3440.

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://kb.vex.com/hc/en-us/articles/360035591372-Using-V5-Shafts | 2026-06-19 | HS shaft bearing mounting pattern; "only part available to support HS shaft is HS Shaft Bearing"; standoff sandwich technique (no drilling needed for 2"/3"/4" HS shafts) |
| S2 | web | https://www.vexrobotics.com/hs-hardware.html | 2026-06-19 | HS shaft lengths + SKUs; key fact: "VEX V5 2", 3", and 4" High Strength Shafts are slightly shorter than their corresponding #8-32 standoffs, allowing them to sit on bearings between structural pieces without requiring cutting"; SKU 276-3521, 276-3440, 276-3524 confirmed |
| S3 | web | https://nooby.tech/en/shop/1292-1x2x1x35-aluminum-c-channel-6-pack.html | 2026-06-19 | Complete VEX V5 structural components SKU list: C-channels (276-2288, 276-2289, 276-2906), angles, U-channels |
| S4 | web | https://www.vexrobotics.com/276-6240.html | 2026-06-19 | V5 Clawbot Structure (Aluminum) lists exact C-channels in Clawbot: 3×U-channel, 2×angle, 2×1x2x1x15, 2×1x2x1x25; confirms arm/claw assembly uses these pieces (repurposable) |
| S5 | web | https://tienda.vexrobotics.com.mx/store/categorias/high-strength-shaft-bearing-27/ | 2026-06-19 | Confirmed SKU 276-3521 for High Strength Shaft Bearing; confirmed it is the HS-shaft-specific version of the bearing flat |
| S6 | web | https://www.vexrobotics.com/hs-shaft-collars.html | 2026-06-19 | HS Clamping Shaft Collar SKU 276-6102 and 276-7580 (low profile); clamping style, uses #8-32 screw + Nylock nut |
| S7 | web | https://www.idesignsol.com/High-Strength-Shaft-2-inch-Long-4-Pack-276-3440 | 2026-06-19 | Confirmed SKU 276-3440 for High Strength Shaft 2" Long (4-Pack) |
| S8 | codebase | `raw/research/vex-launch-disc-parts/index.md` | 2026-06-19 | Prior research: Starter Kit hardware inventory (screws, standoffs, nuts confirmed in kit); constraint that 1/4" HS shaft requires 5/16" drill if passing through C-channel (avoided by standoff-sandwich method) |

## Excerpts

### S1 — Using V5 Shafts (VEX Library)
https://kb.vex.com/hc/en-us/articles/360035591372-Using-V5-Shafts
> "The only part available to support the High Strength Shaft is the High Strength Shaft Bearing. These are plastic parts similar to the Bearing Flats with the exception that the center hole is sized for the ¼" shaft to pass through. High Strength Shaft Bearing can be used by selecting a High Strength Shaft which is the exact length to be sandwiched between two bearings attached between two pieces of structural metal."

### S2 — High Strength Shafts & Hardware (VEX Robotics)
https://www.vexrobotics.com/hs-hardware.html
> "VEX V5 2", 3", and 4" High Strength Shafts are slightly shorter than their corresponding #8-32 standoffs, allowing them to sit on bearings between structural pieces without requiring cutting."

### S4 — V5 Clawbot Structure (Aluminum)
https://www.vexrobotics.com/276-6240.html
> "Spare aluminum structure used to construct the V5 Clawbot. (3) 2x2x2x20 U-Channels (276-6240-001) (2) 2x2x14x20 Angles (276-6240-002) (2) 1x2x1x15 C-Channels (276-6240-003) (2) 1x2x1x25 C-Channels (276-2288-001)"
*(Confirms the arm/claw assembly contains C-channels and angles directly repurposable as flywheel side plates.)*

### S6 — High Strength Shaft Collars (VEX Robotics)
https://www.vexrobotics.com/hs-shaft-collars.html
> "High Strength Shaft Collars are designed to fit onto High Strength Shafts. This clamping-style collar uses standard hex and star drive screws and nuts to maintain a tight lock without scratching or damaging the shaft. Designed specifically for VEX 0.25" High Strength Shafts."
