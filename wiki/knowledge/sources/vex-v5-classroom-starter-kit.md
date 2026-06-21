---
id: vex-v5-classroom-starter-kit
title: VEX V5 Classroom Starter Kit (Product Research)
aliases: [276-7010, V5 Classroom Starter Kit]
updated: 2026-06-21
sources:
  - ../../../raw/research/vex-v5-classroom-starter-kit/index.md
  - ../../../raw/research/vex-v5-classroom-starter-kit/sources.md
  - ../../../raw/research/vex-v5-classroom-starter-kit/index-2.md
  - ../../../raw/research/vex-v5-classroom-starter-kit/sources-2.md
tags: [source, research, vex, hardware, robotics, education]
---

# VEX V5 Classroom Starter Kit (Product Research)

A full product-page scrape of the **VEX V5 Classroom Starter Kit** (SKU **276-7010**, **$849.49**, 10.6 lbs / 4.8 kg), the most affordable entry point into the `relates_to::[[vex-v5]]` platform. Targeted at **grades 9–12, 2–3 students per kit**, the kit contains everything needed to build the **V5 Clawbot** — a wheeled robot with a motorised claw arm. It bundles one complete **V5 System Bundle** (276-7000, the electronics core) plus the structural steel, motion parts, and hardware the bundle alone omits. Part 276-7010 **supersedes the older 276-6500**.

The **electronics** are the headline: (1) V5 Robot Brain, (1) Controller, (1) Radio, (1) Li-Ion 1100mAh Battery + cable + charger, **(4) V5 Smart Motors**, and **(2) Bumper Switch v2** sensors that demonstrate the sensor-to-behaviour relationship. The remainder is a complete mechanical build kit: Smart Cables (300/600/900mm), 4" omni and traction wheels, shafts, high-strength gears (12T pinion, 84T spur), the V5 Claw Assembly, steel U-/C-channels and angles, and a full complement of nuts, screws, bearings, spacers, and tools (T15 star drive keys, zip ties, battery clips).

The kit anchors a four-tier **classroom product family**: Starter Kit → Super Kit (adds motion kits) → **Starter Bundle** (276-7070, 6× Starter Kits, 12–18 students) → **Super Bundle** (276-7080, 6× Super Kits, full classroom). Programming is via `relates_to::[[vexcode]]` (Blocks, Python, and C++), and the kit pairs with the free, standards-aligned `relates_to::[[stem-labs]]` curriculum. Optional checkout add-ons: **VEX PD+** professional-development licence (210-8353, $999/yr) and **VEXcare** extended warranty (1-yr $89.49 / 2-yr $145.99). VEX Robotics is a subsidiary of `relates_to::[[innovation-first]]`.

> **Note on access:** The vexrobotics.com product page blocks direct HTTP fetches (HTTP 403); the data was captured via a scripted browser session. Prices/availability are as of 2026-06-16.

## Key Resource Links

- **Build instructions** (V5 Clawbot): https://link.vex.com/docs/v5-clawbot-buildinstructions
- **CAD model** (276-6009): https://www.vexrobotics.com/cadmodels/upload/download/upload_id/0212d660-fca3-43ad-addb-bc9dc58b28e4
- **STEM Labs curriculum**: https://education.vex.com/
- **Get Started portal**: https://getstarted.vex.com/
- **VEXcode download**: https://www.vexrobotics.com/vexcode
- **Knowledge Base**: https://kb.vex.com/hc/en-us
- **PD+ / Certifications**: https://pd.vex.com/ · https://certifications.vex.com/educator

See the [raw research report](../../../raw/research/vex-v5-classroom-starter-kit/index.md) for the complete kit bill-of-materials and the full ~70-link catalogue.

## Per-Part Specs, Dimensions, Weights & CAD (2026-06-21)

A complete part-isolation reference was added in `index-2.md` (derived_from::[[vex-v5-classroom-starter-kit]] index-2). For **every kit line item** it gives SKU, dimensions, weight, and electrical/mechanical specs, with **30 STEP CAD files (~319 MB)** downloaded to `raw/research/vex-v5-classroom-starter-kit/cad/`.

**Weight/dimension methodology** — three precision tiers, all labeled in the table:
- **Published** — read from VEX product-page Weight/Specs tabs via authenticated browser (site 403s plain fetches). Pack weights divided by count: e.g. hex nut 100-pk 0.26 lb → **1.18 g each**.
- **Calc** — geometry + calibration. Square steel shaft calibrated against published 12″ 4-pack (276-1149 = 0.21 lb) → **0.00435 lb/in**. Steel structure cut-lengths from published per-hole rate (1x2x1x35 = 0.361 lb, 0.01031 lb/hole).
- **Est** — no VEX data; engineering approximation (screws, pins, cables, zip ties).

**Key published weights:**

| Part | SKU | Weight |
|------|-----|--------|
| V5 Robot Brain | 276-4810 | **285 g** (101.6×139.7×33.0 mm) |
| V5 Controller | 276-4820 | **350 g** |
| V5 Robot Battery | 276-4811 | **350 g** (46.45×160.45×30.33 mm) |
| V5 Robot Radio | 276-4831 | **25 g** |
| V5 Smart Motor (11 W) | 276-4840 | **160 g** motor; **50 g** cartridge |
| Battery Charger | 276-4812 | **100 g** |
| Bumper Switch v2 (each) | 276-4858 | **≈ 7.5 g** |
| 4″ Omni Wheel | 276-2185 | **105 g** |
| 4″ Traction Wheel | 276-1497 | **90 g** |
| 84T HS Spur Gear | 276-3438 | **35 g** |
| 12T HS Metal Pinion | 276-2251 | **0.9 g** |
| Flat Bearing | 276-1209 | **2.27 g** |
| Rubber Shaft Collar | 228-3510 | **≈ 0.45 g** |
| #8-32 Hex Nut | 275-1028 | **1.18 g** |
| V5 Battery Clip (each) | 276-6020 | **≈ 5.7 g** |

**CAD files saved** — `kebab-name_SKU.step` naming, all STEP format. Electronics: brain, controller, radio, battery, motor, bumper, battery clip. Motion/gears: both 4″ wheels, 2″+3″+12″ shafts, 12T pinion, 84T gear, HS shaft inserts, claw kit. Hardware: hex nut, all three nut retainers, flat bearing, rubber collar, four screw sizes. Structure proxies: alu u-channel (276-7285), steel c-channel (276-2906), steel angle (275-1142). Assembly: full Clawbot (276-6009).

**Structural notes:** VEX hole pitch = **0.500″ (12.7 mm); hole size = 0.182″ square**. The kit's exact steel cut-lengths have no standalone SKU; their geometry is represented by the nearest published steel part (same cross-section, longer stock). The 2×2×2×20 steel U-channel weight is estimated from the aluminum 276-7285 (0.15 lb) × empirical steel/alu ratio 2.3.

relates_to::[[vex-v5]]  
relates_to::[[vex-v5-cad-designs]]
