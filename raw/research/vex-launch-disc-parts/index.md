---
topic: "the minimum required parts (not kits, individual parts) needed from VEX website to add a 'launch disc' type configuration option"
slug: vex-launch-disc-parts
researched: 2026-06-19
sources: [./sources.md]
---

# Research: Minimum VEX Parts to Add a Launch-Disc Configuration

> A flywheel-based disc launcher on VEX V5 requires as few as **3 individual part purchases** when repurposing an existing motor: a 6:1 gear cartridge swap (276-5842), at least one flex wheel (217-6449 or similar), and VersaHex adapters to mount it (217-7947). If a dedicated motor is added instead of repurposing one, the cartridge becomes part of the motor purchase (276-4840). Ball bearings (276-8402) are not strictly required but cut current draw by more than half and are strongly recommended. All part numbers are confirmed on vexrobotics.com.

---

## Research Questions

1. What mechanism type is standard for VEX disc launchers?
2. What individual parts (not kits) does VEX sell for this mechanism?
3. What are the exact SKUs for each required part on vexrobotics.com?
4. Which parts are truly required vs. strongly recommended vs. optional?
5. What does adding this configuration cost relative to the existing Starter Kit setup?

---

## Current State (Codebase)

From prior research [`raw/research/vex-v5-customization-grab-pull-throw/index.md`]:

- The capstone robot is a V5 Clawbot built from the Classroom Starter Kit (276-7010).
- It uses 4 V5 Smart Motors (all with 18:1 / 200 RPM cartridges): 2 drive, 1 arm (7:1 gear reduction), 1 claw.
- All 4 Brain Smart Ports 1/3/6/8/10 area are in use; 17 ports remain free.
- "THROW" at present is a slow catapult (arm motor + rubber bands); "LAUNCH DISC" would be a flywheel-based fast launcher.
- The Starter Kit includes standard 1/8" shafts, Bearing Flats, and steel structural parts but **no 6:1 cartridges, no flex wheels, and no VersaHex adapters**.

The "launch disc" configuration is envisioned as an alternative morphology — either replacing the arm/claw with a flywheel (reconfiguration) or adding a dedicated motor.

---

## Key Findings

### 1. Mechanism Type [S1, S2]

VEX V5 disc launchers use a **flywheel** design: one or two high-speed wheels spin continuously and fling a disc outward on contact. The standard approach for VEX V5 is a single flywheel with a back-plate (friction surface) or a double flywheel (two wheels contra-rotating). Single flywheel is simpler and the most common beginner build.

The VEX hero bot "Disco" (Spin Up 2022-23) demonstrates this pattern using Competition Starter Kit parts only, but competition builds extend it with dedicated flywheel parts [S3, S4].

### 2. Required Motor Speed [S5]

Flywheel launchers require the **6:1 (600 RPM) gear cartridge** — the fastest available for V5 Smart Motors. The 18:1 cartridge (included in the Classroom Starter Kit) is insufficient; it tops out at 200 RPM which cannot store enough kinetic energy for a meaningful throw. The 6:1 cartridge is available for individual purchase as SKU **276-5842** (~$12–20), or it comes bundled with a new motor (276-4840, which ships with all three cartridge types).

### 3. Flywheel Wheel [S6, S7]

**Flex Wheels** are the standard VEX V5 flywheel contact surface. They are silicone-rubber, compressible, high-grip cylinders sold individually on vexrobotics.com. Key options:

| SKU | Size | Durometer | Notes |
|-----|------|-----------|-------|
| 217-6353 | 2" OD | 30A (soft) | Better for intake rollers |
| 217-6354 | 2" OD | 40A (medium) | All-round |
| 217-6447 | 3" OD | 30A (soft) | Intake |
| 217-6448 | 3" OD | 40A (medium) | Mid-range |
| **217-6449** | **3" OD** | **60A (firm)** | **Recommended for flywheel** |
| 217-6450 | 4" OD | 30A (soft) | Intake/drivetrain |
| 217-6451 | 4" OD | 40A (medium) | — |

**60A durometer is recommended for flywheel discs** because the firmer rubber transfers energy to the disc more efficiently; soft wheels deform and waste energy. 3" is the most common flywheel size for VRC Spin Up-style launchers.

A **single** 3" 60A flex wheel is enough for the flywheel contact surface (single-flywheel + backplate design). A second wheel is used in double-flywheel setups.

### 4. Flex Wheel Mounting Hardware [S6, S8]

Flex wheels are originally VEXpro parts designed for a 1/2" hex bore (1.625"/2") or a 1-1/8" round bore (3"/4"). V5 shafts are 1/4" square (High Strength) or 1/8" square (standard). Adapters are required:

**For 2" flex wheels (1/2" hex bore):**
- 2× VersaHex Adapters per wheel (go from 1/4" square shaft → 1/2" hex bore)
- SKU: **217-7947** — 1/2" VersaHex Adapters v2 (1/4" Square Bore, 1/4" Long) 8-pack [S9]
- Or SKU: **217-7946** — same adapter, 1/8" Long version 8-pack

**For 3" and 4" flex wheels (1-1/8" round bore):** [S8]
- Need VersaHub v2 to bridge 1-1/8" round bore → 1/2" hex
- SKU: **217-8079** — 1/2" Hex Bore Plastic VersaHub v2
- Plus VersaHex adapters (217-7947) to further adapt 1/2" hex → 1/4" square shaft

The 3" route requires both 217-8079 and 217-7947. The 2" route requires only 217-7947.

### 5. Ball Bearings (Strongly Recommended) [S10, S11]

Standard Bearing Flats (already in Starter Kit) work but create substantial friction at flywheel speeds. Ball bearings reduce this dramatically:

- Test data: bearing-based launcher draws **less than half the current** of a bushing-based equivalent under identical conditions [S10].
- Lower current → more consistent RPM → more consistent launch distance.
- SKU: **276-8402** — High Strength Shaft Ball Bearings (11-pack)
- These bearings are for the 1/4" High Strength Shaft that the V5 Smart Motor outputs.

### 6. Flywheel Weights (Optional) [S11]

- SKU: **276-8794** — V5 Flywheel Weight (2-pack)
- Bolts onto flex wheel to increase moment of inertia, which slows spin-up but reduces RPM drop when launching a disc.
- Reduces recovery time between shots when using 2 weights vs. 0 in VEX's own test [S11].
- Optional for demonstration use; useful for high-volume shooting.

### 7. Alternative: Compression Wheel 4-Packs [S12]

VEX now sells Compression Wheel 4-Pack Kits (1.625" and 2" OD, 30A/40A/60A) at `vexrobotics.com/compression-wheels.html`. Each 4-pack includes VersaHex adapters in the box. This simplifies procurement — one line item instead of wheel + adapters separately — but pack size (4 wheels) is more than needed for a single flywheel. SKUs were not confirmed at time of research.

---

## Constraints

1. **All 4 motors occupied** — the Clawbot uses all 4 Starter Kit motors. A dedicated flywheel motor requires purchasing an additional V5 Smart Motor (276-4840, ~$52.99). Alternatively, repurpose the arm motor (loses arm/grab functionality — this becomes an exclusive configuration swap).
2. **No 6:1 cartridge in Starter Kit** — the kit only includes 18:1. A cartridge swap or new motor purchase is required regardless of which approach is taken.
3. **No flex wheels or VersaHex adapters in Starter Kit** — these are external-only parts and must be purchased.
4. **3"/4" flex wheels need hole drilling** — the 1/4" HS shaft does not pass through Starter Kit C-channels without a custom 5/16" / 8mm drilled hole, per the KB documentation. The 2" flex wheel route avoids this (the wheel mounts directly at the motor output shaft).
5. **Backplate material** — a single-flywheel design needs a backplate surface for the disc to ride along. This can be a steel or aluminum plate from the existing kit; no additional purchase needed.

---

## Solution Comparison

| Approach | Required Purchases | Pros | Cons |
|---|---|---|---|
| **A – Repurpose arm motor + 2" flex wheel** | 276-5842 + 217-6354 + 217-7947 | Fewest new parts (~3 SKUs), cheapest | Loses arm/claw; 2" wheel has smaller contact patch |
| **B – Repurpose arm motor + 3" flex wheel** | 276-5842 + 217-6449 + 217-8079 + 217-7947 | Better disc contact area | Requires VersaHub + possible hole drilling in structure |
| **C – Add dedicated motor + 2" flex wheel** | 276-4840 + 217-6354 + 217-7947 | Preserves grab/pull; motor includes all cartridges | Costs more (~$53 motor); uses one more Smart Port |
| **D – Add dedicated motor + 3" flex wheel** | 276-4840 + 217-6449 + 217-8079 + 217-7947 | Best overall launch performance | Most parts; hole drilling required |

For the capstone self-model project, **Option A or B** is recommended: the "launch disc" configuration replaces the arm/claw morphology (exclusive swap), which maps cleanly onto the self-model's morphology enumeration.

---

## Recommendation

**Minimum viable launch-disc configuration (Approach A):**

| # | Part | SKU | Qty | Purpose |
|---|------|-----|-----|---------|
| 1 | V5 Motor 6:1 Cartridge (600 RPM) | **276-5842** | 1 | Swap into existing arm motor |
| 2 | Straight Flex Wheel 2" OD 40A | **217-6354** | 1 | Flywheel contact wheel |
| 3 | VersaHex Adapters v2 1/4" Square, 8-pack | **217-7947** | 1 | Mount wheel on motor HS shaft |

**Strongly recommended additions:**

| # | Part | SKU | Qty | Purpose |
|---|------|-----|-----|---------|
| 4 | HS Shaft Ball Bearings (11-pack) | **276-8402** | 1 | Halves friction vs. bearing flats |
| 5 | V5 Flywheel Weight (2-pack) | **276-8794** | 1 | Maintains RPM between shots |

**To upgrade to 3" wheel (better disc contact, Step B):** additionally purchase:
- **217-6449** (3" OD 60A Flex Wheel) in place of 217-6354
- **217-8079** (Plastic VersaHub v2) — 2 units to mount 3" wheel on both sides

### Implementation outline

1. Remove arm and claw assemblies from existing Clawbot arm motor.
2. Swap 18:1 cartridge for 6:1 (276-5842) in that motor — takes ~30 seconds with a tool.
3. Attach VersaHex adapters (217-7947, 2 per wheel) to the motor's 1/4" HS shaft output.
4. Press flex wheel onto adapters.
5. Mount ball bearing (276-8402) at the far end of the shaft for support.
6. Fabricate a backplate from existing Starter Kit steel plates and secure at the correct compression distance (typically 1–2 mm narrower than the disc diameter).
7. Add an indexer slot (angled ramp from existing L-channel) to feed discs into the flywheel.
8. In VEXcode: set arm motor to velocity mode, target 580–600 RPM, hold until at speed, then trigger indexer.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Flywheel loses RPM between shots | Add 276-8794 flywheel weights; or add second motor in double-flywheel config |
| 18:1 cartridge used by mistake | Label the motor; note cartridge color: 6:1 = blue cap |
| Shaft binding in structural metal | Use 5/16" (8mm) drill to open C-channel holes; or route shaft outside structure |
| Disc not launching consistently | Tune backplate compression distance; 60A flex wheel gives more consistent energy transfer than 40A |

---

## Next Steps

- **To purchase**: Add the 3 minimum SKUs (276-5842 + 217-6354 + 217-7947) to cart at vexrobotics.com. Optional: add 276-8402 + 276-8794.
- **To create a task**: `/task-add "Build launch-disc morphology: swap 6:1 cartridge, mount 2\" flex wheel, wire indexer, add throw-disc telemetry contract"`
- **To ingest into wiki**: Run `/wiki-ingest raw/research/vex-launch-disc-parts/index.md`
- **For self-model**: Add "launch_disc" to the morphology enumeration in the self-model schema alongside grab/pull/throw; quantify via flywheel RPM at launch and observed disc travel distance.
