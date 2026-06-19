---
id: vex-launch-disc-parts
title: "Research: VEX V5 Minimum Parts for a Launch-Disc Configuration"
updated: 2026-06-19
sources:
  - ../../raw/research/vex-launch-disc-parts/index.md
tags: [vex-v5, hardware, flywheel, disc-launcher, parts, morphology]
---

# Research: VEX V5 Minimum Parts for a Launch-Disc Configuration

A flywheel-based disc launcher on VEX V5 is achievable with **as few as 3 individual part purchases** when repurposing the existing arm motor: a 6:1 cartridge swap (276-5842), at least one flex wheel (e.g., 217-6449 for 3" 60A), and VersaHex adapters to mount it on the V5 shaft (217-7947). All part numbers confirmed on vexrobotics.com as of 2026-06-19.

## Mechanism

**Flywheel** is the standard VEX V5 disc-launching design: one or two wheels spin continuously at high RPM and fling a disc on contact. A single flywheel with a backplate (friction surface guiding the disc) is the minimal viable launcher. Double-flywheel (two contra-rotating wheels) gives higher velocity and removes the backplate, at the cost of an additional motor. The VEX hero bot "Disco" (Spin Up 2022-23 season) is the canonical VRC example, built from Competition Starter Kit parts.

## Required Parts by Category

### Motor Speed

**6:1 (600 RPM) gear cartridge is required.** The Classroom Starter Kit ships 18:1 (200 RPM) only — insufficient for flywheel operation. Two purchase paths:

- **276-5842** — V5 Motor 6:1 Cartridge (600 RPM) only — swap into an existing arm motor
- **276-4840** — V5 Smart Motor & Gear Cartridges — full motor unit; includes all 3 cartridges; needed if adding a dedicated motor without repurposing one

### Flywheel Contact Wheel — Flex Wheels

**Flex Wheels** are silicone-rubber compressible cylinders sold individually. 60A durometer is recommended for flywheel contact (firmness = efficient energy transfer); 30A is better for intake rollers (softness = compliance).

Confirmed SKUs available on vexrobotics.com:

| SKU | Size | Durometer | Use |
|-----|------|-----------|-----|
| 217-6353 | 2" OD | 30A | Intake rollers |
| 217-6354 | 2" OD | 40A | General / intake |
| 217-6447 | 3" OD | 30A | Intake rollers |
| 217-6448 | 3" OD | 40A | Mid-range |
| **217-6449** | **3" OD** | **60A** | **Flywheel (recommended)** |
| 217-6450 | 4" OD | 30A | Intake/drive |
| 217-6451 | 4" OD | 40A | — |

A single flex wheel suffices for a single-flywheel design.

### Shaft Adapters

Flex wheels are VEXpro parts designed for 1/2" hex (small sizes) or 1-1/8" round bore (large sizes). VEX V5 shafts are 1/4" square (HS). Adapters bridge the gap:

**For 1.625" and 2" flex wheels** (1/2" hex bore):
- **217-7947** — 1/2" VersaHex Adapters v2 (1/4" Square Bore, 1/4" Long) 8-pack — 2 adapters per wheel

**For 3" and 4" flex wheels** (1-1/8" round bore):
- **217-8079** — 1/2" Hex Bore Plastic VersaHub v2 — 1 or 2 per wheel, bridges 1-1/8" bore to 1/2" hex
- **217-7947** — VersaHex Adapters (as above) — still needed for shaft-to-hub

The 2" wheel route (217-6354 + 217-7947) is simpler: no VersaHub required, wheel mounts directly at motor output shaft. The 3" route (217-6449 + 217-8079 + 217-7947) gives a larger contact patch and better disc control.

### Strongly Recommended (Not Strictly Required)

- **276-8402** — High Strength Shaft Ball Bearings (11-pack) — bushing-based launchers draw more than double the current of bearing-based ones; critical for consistent RPM and motor health
- **276-8794** — V5 Flywheel Weight 2-pack — increases moment of inertia; reduces RPM drop between shots; improves shot-to-shot consistency

## Constraint: Motor Availability

The Clawbot (Gen 1 reference morphology) occupies all 4 Starter Kit motors. A dedicated flywheel motor requires either:
- **Repurpose the arm motor** (swap cartridge) — loses grab/arm capability; disc-launcher becomes an exclusive morphology swap
- **Purchase additional motor** (276-4840) — preserves other functions; uses one more Smart Port

For the capstone self-model loop, the exclusive swap is the cleaner model: "launch_disc" replaces "grab+throw" as an alternative end-effector configuration.

## Implementation Sketch

1. Remove arm and claw assemblies.
2. Swap arm motor 18:1 cartridge for 6:1 (276-5842) — ~30 seconds with a tool.
3. Attach VersaHex adapters (217-7947, 2×) to motor's 1/4" HS shaft output.
4. Press 2" or 3" flex wheel onto adapters.
5. Add ball bearing (276-8402) at far end of shaft for support.
6. Fabricate backplate from existing Starter Kit steel plates at correct compression (~1–2 mm narrower than disc diameter).
7. Build angled indexer ramp from existing L-channel to feed discs into flywheel.
8. In VEXcode: set motor to velocity mode, target 580–600 RPM, hold until at speed, trigger indexer.

relates_to::[[vex-v5]]
relates_to::[[typed-assembly-grammar]]
relates_to::[[vex-v5-motor-cartridges]]
derived_from::[[vex-launch-disc-parts]]
relates_to::[[task-telemetry-contract]]
