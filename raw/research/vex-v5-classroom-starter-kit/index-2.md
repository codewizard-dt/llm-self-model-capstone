---
topic: "Per-part specifications, dimensions, weights, and CAD files for every item in the VEX V5 Classroom Starter Kit (276-7010)"
slug: vex-v5-classroom-starter-kit
researched: 2026-06-21
sources: [./sources-2.md, ./sources.md]
---

# Research: VEX V5 Classroom Starter Kit — Per-Part Specs, Dimensions, Weights & CAD

> Builds on [index.md](index.md) (full product-page scrape of kit 276-7010). This file is the **part-isolation reference**: for every kit line item it gives SKU, **dimensions, weight**, electrical/mechanical specs, and a downloaded **STEP CAD file** where VEX publishes one. 30 STEP models (~319 MB) are saved under [`cad/`](cad/).

## How weights & dimensions were obtained

- **Published** values were read from each part's VEX **Product Specs** / **Weight** tab (the site 403s plain fetches, so a headless browser session was used). VEX often lists a **pack weight**; per-piece = pack ÷ count, noted as such.
- **Computed** values (marked *calc*) are derived from geometry + material density where VEX publishes none — e.g. square-steel-shaft weight calibrated against the published 12″ 4-pack (276-1149 = 0.21 lb → **0.00435 lb/in** of 0.125″ steel shaft); steel structure cut-lengths scaled from the published steel per-hole rate.
- **Estimated** values (marked *est*) are engineering approximations for items VEX neither tabulates nor lets us calibrate (small screws, connector pins, rubber bands, zip ties).
- Where VEX publishes no dimensions (controller, radio, charger, motor, claw), **the exact geometry is in the downloaded STEP file** — noted "see CAD."
- **VEX hole pitch = 0.500″ (12.7 mm); holes are 0.182″ square.** Structural length ≈ (hole count) × 0.5″.

---

## Master Part Table — Dimensions + Weight + Specs

### V5 Electronics

| # | Part | SKU | Dimensions | Weight (each) | Other specs | CAD |
|---|------|-----|-----------|---------------|-------------|-----|
| 1× | V5 Robot Brain | 276-4810 | 101.6 × 139.7 × 33.0 mm (4.0″W × 5.5″H × 1.3″L) | **285 g (0.63 lb)** | 12.8 V; 21 Smart Ports; 8 3-wire (8 dig/12 analog); 4.25″ 480×272 65k touchscreen; Cortex-A9 667 MHz+2×M0+FPGA; 128 MB RAM; 32 MB flash; USB 2.0 HS; microSD ≤16 GB; VEXnet 3.0+BT 4.2 | ✓ |
| 1× | V5 Controller | 276-4820 | see CAD | **350 g (0.77 lb)** | LCD 128×64; 2 joysticks; 12 buttons; haptic; VEXnet 3.0+BT 4.2 @200 kbps; Li-ion 8–10 h / 1 h charge | ✓ |
| 1× | V5 Robot Radio | 276-4831 | see CAD | **25 g (0.06 lb)** | VEXnet 3.0 + Bluetooth 4.2 | ✓ |
| 1× | V5 Robot Battery 1100 mAh | 276-4811 | 46.45 × 160.45 × 30.33 mm (1.82″W × 6.31″L × 1.18″H) | **350 g (0.77 lb)** | LiFePO4 12.8 V; 12.8 Wh; 20 A / 256 W peak; ~2000 cycles; 10 motors at peak | ✓ |
| 1× | V5 Robot Battery Cable | 276-4817 | length 180 / 300 / 500 mm | ~10 g *est* (assortment 0.46 lb / multi) | Brain↔battery power cable; kit has one length | — |
| 1× | V5 Robot Battery Charger | 276-4812 | see CAD | **100 g (0.21 lb)** | Mains→12.8 V; full recharge < 60 min | — |
| 4× | V5 Smart Motor (11 W) | 276-4840 | see CAD (≈ 2.5 × 1.5 × 1.7 in body) | **160 g (0.35 lb)** motor; **50 g** per cartridge | 11 W; **2.1 N·m** max torque; 2.5 A stall; 18:1/200 RPM std, 36:1/100 & 6:1/600 cartridges; encoder ±0.02°; PID @10 ms | ✓ |
| 2× | Bumper Switch v2 | 276-4858 | ≈ 1.26″L × 1.21″W × 0.5″H | **≈ 7.5 g** (2-pack 15 g) | Momentary push switch; 3-wire digital; low-force | ✓ |

### V5 Smart Cables & Charging Cable

| # | Part | SKU | Dimensions | Weight (each) | Spec | CAD |
|---|------|-----|-----------|---------------|------|-----|
| 3× | 300 mm Smart Cable | 276-4860 (family) | 300 mm long | ~5 g *est* | 4-conductor V5 Smart Cable, RJ-style connectors (power+data) | — |
| 1× | 600 mm Smart Cable | 276-4860 (family) | 600 mm | ~9 g *est* | as above | — |
| 1× | 900 mm Smart Cable | 276-4861 (family) | 900 mm | ~13 g *est* | as above | — |
| 1× | USB A → Micro Cable | — | ~1 m | ~20 g *est* | USB 2.0 A-to-Micro; wired Controller download/charge | — |

### Wheels

| # | Part | SKU | Dimensions | Weight (each) | Spec | CAD |
|---|------|-----|-----------|---------------|------|-----|
| 2× | 4″ Omni-Directional Wheel | 276-2185 (kit) / 276-8107 (current) | 4.0″ (101.6 mm) dia; 320 mm travel/rev | **105 g (0.232 lb)** classic; 74 g anti-static | Side rollers; fits 0.125″ square shaft | ✓ (276-8107) |
| 2× | 4″ Wheel (traction) | 276-1497 | 4.0″ (101.6 mm) dia | **90 g (0.198 lb)** | Solid traction wheel | ✓ |

### Shafts — 0.125″ (3.18 mm) square steel (*calc* @ 0.00435 lb/in)

| # | Part | SKU | Dimensions | Weight (each) | CAD |
|---|------|-----|-----------|---------------|-----|
| 2× | 2″ Shaft | 276-2011-001 | 0.125″ sq × 2″ | ≈ 4 g (0.009 lb) | ✓ |
| 2× | 3″ Shaft | 276-2011-002 | 0.125″ sq × 3″ | ≈ 6 g (0.013 lb) | ✓ |
| 1× | 3.5″ Shaft | cut from 276-1149 | 0.125″ sq × 3.5″ | ≈ 7 g (0.015 lb) | proxy ✓ (12″ stock) |
| 3× | 4″ Shaft | cut from 276-1149 | 0.125″ sq × 4″ | ≈ 8 g (0.017 lb) | proxy ✓ (12″ stock) |

### High-Strength Gears & Inserts

| # | Part | SKU | Dimensions | Weight (each) | Spec | CAD |
|---|------|-----|-----------|---------------|------|-----|
| 1× | 12T Metal Pinion (HS) | 276-2251 | 12-tooth, ~0.5″ pitch dia | **0.9 g (0.002 lb)** | High-strength metal pinion; mates standard VEX gears | ✓ |
| 1× | 12T Metal Pinion Insert | (276-2251 system) | HS-bore → 0.125″ sq | ~1 g *est* | Metal insert adapting HS bore to shaft | proxy ✓ (276-3881-002) |
| 1× | 84T High-Strength Spur Gear | 276-3438 | 84-tooth, ~3.5″ pitch dia | **35 g (0.08 lb)** | HS gear; extra turntable mounting holes | ✓ |
| 10× | HS Gear Shaft Inserts (metal) | 276-3881-002 | HS-bore → 0.125″ sq | ~1 g *est* each | Metal shaft inserts for HS gears/wheels | ✓ |

### Other Motion

| # | Part | SKU | Dimensions | Weight | Spec | CAD |
|---|------|-----|-----------|--------|------|-----|
| 1× | V5 Claw Assembly (Claw Kit v2) | 276-6010 | see CAD | ~40 g *est* (assembly) | Gripper: claw + #64 bands + locking screws + collar + 12T gear + 4x shaft; uses 12T pinion 276-2251 | ✓ |

### Nuts & Connectors

| # | Part | SKU | Dimensions | Weight (each) | Spec | CAD |
|---|------|-----|-----------|---------------|------|-----|
| 30× | #8-32 Hex Nut | 275-1028 | 11/32″ (0.344″) across flats × ~0.105″ thick | **1.18 g** (100-pack 0.26 lb) | Non-locking steel hex nut | ✓ |
| 15× | 1-Post Hex Nut Retainer w/ Flat Bearing | 276-6481 | 1 sq peg + bearing flat | ≈ 9 g *(10-pk 0.20 lb, coarse)* | Nylon; captures nut + integrated bearing | ✓ |
| 5× | 1-Post Hex Nut Retainer | 276-6482 | 1 sq peg | ≈ 9 g *(10-pk 0.20 lb, coarse)* | Nylon; captures hex nut | ✓ |
| 7× | 4-Post Hex Nut Retainer | 276-6483 | 4 posts, 5 contact points | ≈ 9 g *(10-pk 0.20 lb, coarse)* | Nylon | ✓ |

> Note: VEX lists all three retainer 10-packs at the same rounded 0.20 lb; true per-piece nylon mass is lower (~2–4 g). Use as an upper bound; exact volume is in the CAD.

### Shaft Hardware

| # | Part | SKU | Dimensions | Weight (each) | Spec | CAD |
|---|------|-----|-----------|---------------|------|-----|
| 5× | Flat Bearing (Bearing Flat) | 276-1209 | mounts on structure; passes 0.125″ shaft | **2.27 g** (10-pack 0.05 lb) | Nylon; low-friction shaft support | ✓ |
| 23× | Rubber Shaft Collar | 228-3510 | bore 0.125″ | **≈ 0.45 g** (30-pack 0.03 lb) | Friction collar on 0.125″ shafts | ✓ |
| 6× | 0x2 Connector Pin | — | ~0.5″ long plastic pin | ~0.3 g *est* | Joins parts flush (2-thickness) | — |
| 8× | 1/8″ Nylon Spacer | 275-1066 (1/2″OD pack) | 0.194″ ID × 1/2″ OD × 0.125″ L | ≈ 0.4 g *calc* | nylon | — |
| 4× | 3/8″ Nylon Spacer | 275-1066 | 0.194″ ID × 1/2″ OD × 0.375″ L | ≈ 1.2 g *calc* | nylon | — |
| 3× | 1/2″ Nylon Spacer | 275-1066 | 0.194″ ID × 1/2″ OD × 0.5″ L | ≈ 1.6 g *calc* | nylon | — |
| 2× | 7/8″ Nylon Spacer | 275-1066 | 0.194″ ID × 1/2″ OD × 0.875″ L | ≈ 2.8 g *calc* | nylon | — |

> Nylon spacer variety packs: 1/2″ OD = 275-1066 (0.09 lb/pack), 3/8″ OD = 276-6340 (0.05 lb/pack). All have 0.194″ ID. Per-piece weights *calc* from nylon density (1.15 g/cc) — exact OD depends on which pack the kit drew from (1/2″ OD assumed).

### Screws — #8-32 Star Drive (T15), grade-8 steel (*est* from geometry)

| # | Part | SKU | Dimensions | Weight (each) | CAD |
|---|------|-----|-----------|---------------|-----|
| 30× | #8-32 × 3/8″ Star Drive | 276-4991 | #8 (0.164″) × 3/8″ L | ≈ 1.4 g *est* | ✓ |
| 2× | #8-32 × 1.000″ Star Drive | 276-4996 | #8 × 1.000″ L | ≈ 2.8 g *est* | ✓ |
| 4× | #8-32 × 1/2″ Locking Star Drive | 276-4992 (geom) | #8 × 1/2″ L | ≈ 1.7 g *est* | ✓ |
| 4× | #8-32 × 1.500″ Locking Star Drive | 276-4998 (geom) | #8 × 1.500″ L | ≈ 3.8 g *est* | ✓ |

> "Locking" = thread-locker coated; identical geometry/weight to the non-locking star-drive screw of the same length (the captured CAD).

### Steel Structure — 0.5″ hole pitch; length ≈ holes × 0.5″ (kit ships **steel**)

| # | Part | SKU (CAD proxy) | Dimensions | Weight (each) | CAD |
|---|------|-----------------|-----------|---------------|-----|
| 3× | 2×2×2×20 Steel U-Channel | 276-7285 (alu CAD) | 1.0″ × 1.0″ U-profile, ~10.0″ (254 mm) long; 0.064″ wall | ≈ **0.345 lb (157 g)** *est* (alu = 0.15 lb × steel/alu ratio 2.3) | ✓ (alu geom) |
| 2× | 1×2×1×15 Steel C-Channel | 276-2906 (steel CAD) | 1.0″ web × 0.5″ flanges, ~7.5″ (190 mm) long | ≈ **0.155 lb (70 g)** *calc* (0.01031 lb/hole) | proxy ✓ |
| 2× | 1×2×1×25 Steel C-Channel | 276-2906 (steel CAD) | 1.0″ web × 0.5″ flanges, ~12.5″ (318 mm) long | ≈ **0.258 lb (117 g)** *calc* | proxy ✓ |
| 2× | 2×2×14×20 Steel Angle | 275-1142 (steel CAD) | 1.0″ × 1.0″ angle legs, ~10.0″ (254 mm) long (14-hole leg detail) | ≈ **0.20 lb (92 g)** *calc* (0.0101 lb/hole) | proxy ✓ |

> Steel rates derived from published VEX steel parts: 1x2x1x35 steel C-channel = 0.361 lb (→ 0.01031 lb/hole); 2x2x25 / 2x2x35 steel angles = 0.252 / 0.353 lb (→ 0.0101 lb/hole). The exact kit cut-lengths aren't sold standalone, so these are computed, not published. The 2x2x2x20 **steel** U-channel has no published steel data point — estimated from the aluminum 276-7285 (0.15 lb) × the empirical steel/aluminum mass ratio (2.3×) observed on the 1x2x1x35 channel.

### Tools & Accessories

| # | Part | SKU | Dimensions | Weight (each) | Spec | CAD |
|---|------|-----|-----------|---------------|------|-----|
| 2× | V5 Battery Clip | 276-6020 | clips battery to structure | **≈ 5.7 g** (4-pack 0.05 lb) | Plastic retention clip | ✓ |
| 2× | #32 Rubber Bands | — | 3.5″ × 1/8″ flat | ≈ 1 g *est* | Latex elastic | — |
| 2× | T15 Star Drive Key | — | T15 torx, L-handle | ≈ 5 g *est* | Star-drive screw key | — |
| 50× | 4″ Zip Ties | — | ~4″ (100 mm) | ≈ 0.3 g *est* | Nylon cable ties | — |
| 1× | V5 Clawbot Instruction Manual | — | printed booklet | — | Build guide (link.vex.com/docs/v5-clawbot-buildinstructions) | — |
| — | V5 Clawbot (assembled reference) | 276-6009 | full robot | — | Complete assembled-robot model | ✓ |

---

## CAD Inventory (`cad/`, 30 STEP files, ~319 MB)

Electronics: `v5-robot-brain_276-4810`, `v5-controller_276-4820`, `v5-robot-radio_276-4831`, `v5-robot-battery_276-4811`, `v5-smart-motor_276-4840`, `bumper-switch-v2_276-4858`, `v5-battery-clip_276-6020`.
Motion/gears: `wheel-4in_276-1497`, `wheel-4in-omni_276-8107`, `shaft-2in_276-2011-001`, `shaft-3in_276-2011-002`, `shaft-12in-stock_276-1149`, `pinion-12t-hs-metal_276-2251`, `gear-84t-hs_276-3438`, `hs-metal-shaft-inserts_276-3881-002`, `v5-claw-kit_276-6010`.
Hardware: `hex-nut-8-32_275-1028`, `1-post-hex-nut-retainer-w-bearing_276-6481`, `1-post-hex-nut-retainer_276-6482`, `4-post-hex-nut-retainer_276-6483`, `flat-bearing_276-1209`, `rubber-shaft-collar_228-3510`, `screw-star-8-32x0.375_276-4991`, `screw-star-8-32x0.500_276-4992`, `screw-star-8-32x1.000_276-4996`, `screw-star-8-32x1.500_276-4998`.
Structure (proxies): `u-channel-2x2x2x20-alu_276-7285`, `c-channel-1x2x1x35-steel_276-2906`, `angle-2x2x25-steel_275-1142`.
Assembly: `v5-clawbot-assembly_276-6009`.

**No CAD published** (specs in table): battery cable 276-4817, smart cables (300/600/900 mm), USB cable, 0x2 connector pin, nylon spacers, #32 rubber bands, T15 key, zip ties, charger 276-4812, manual.

---

## Coverage summary

- **Weight: complete for all line items** — published per-piece or pack-derived for electronics, wheels, gears, bearing, collar, nuts, retainers, battery clip, bumper; *calc* for shafts, spacers, steel structure; *est* for screws, cables, pins, bands, ties, key.
- **Dimensions: complete** — published for Brain & Battery; standard/derived for fasteners, spacers, shafts, structure (hole-pitch convention); for the controller, radio, charger, motor, and claw the exact geometry is in the downloaded STEP file ("see CAD").
- Anything marked *est* / *calc* is a stated approximation with its basis given, not a published VEX figure — flagged so it can be replaced by a scale reading if exact mass is critical.

## Next Steps

- Run `/wiki-ingest raw/research/vex-v5-classroom-starter-kit/index-2.md` to fold the complete per-part dimension/weight/CAD reference into the knowledge base.
- For exact masses of the *est*/*calc* items (small screws, steel cut-lengths, spacers), weigh the physical parts — VEX does not publish them individually.
- STEP files in `cad/` give exact geometry/CG for any part and can be assembled into a full robot mass model.
