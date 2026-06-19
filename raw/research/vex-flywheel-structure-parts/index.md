---
topic: "a minimal list of structural parts from VEX structure catalog to support a flywheel setup, along with any required hardware to attach them"
slug: vex-flywheel-structure-parts
researched: 2026-06-19
sources: [./sources.md]
---

# Research: Minimal Structural Parts for a VEX V5 Flywheel Setup

> **Four structural purchase lines cover everything not already in the Classroom Starter Kit** for a single-flywheel disc launcher: HS Shaft Bearings (276-3521), HS Clamping Shaft Collars (276-6102), a 2" HS Shaft (276-3440), and one pack of 1×2×1 C-channels (276-2288 or 276-2906) if the Clawbot's arm structure is being reused in place. All #8-32 screws, standoffs, keps nuts, and nylock nuts are already in the Starter Kit. This research is a structural companion to `raw/research/vex-launch-disc-parts/index.md`, which covers the flywheel mechanism parts (flex wheel, cartridge, VersaHex adapters, ball bearings).

---

## Research Questions

1. What structural frame parts does a VEX V5 single-flywheel launcher require?
2. Which of those parts are already in the Classroom Starter Kit (276-7010)?
3. What must be purchased individually from the VEX structure catalog?
4. What are the correct SKUs, pack sizes, and quantities for each purchase?
5. What fastener hardware is needed to attach the structural parts together?

---

## Current State (Codebase)

From `raw/research/vex-launch-disc-parts/index.md` and `wiki/knowledge/entities/tools/vex-v5.md`:

- The capstone robot is a V5 Clawbot built from the Classroom Starter Kit (276-7010).
- **All structural metal included in the kit is consumed by the Clawbot build** — 15-hole and 25-hole steel C-channels, 20-hole U-channels, angles; all used for drivetrain, arm tower, and claw.
- The kit includes standard 1/8" shaft bearing flats, standard shaft collars (for 1/8" square shafts), a variety of standoffs (1/2", 1", 2", 3"), and #8-32 screws/nuts.
- The V5 Smart Motor outputs a **1/4" High Strength (HS) shaft** — this is NOT the same as the 1/8" shafts the kit's bearing flats and shaft collars are sized for.
- A flywheel requires high-speed shaft support that standard bearing flats cannot provide on a 1/4" HS shaft.

---

## Key Findings

### 1. The Flywheel Frame Anatomy [S1, S2]

A single-flywheel disc launcher (simplest pattern: one wheel + backplate) is built from five structural sub-systems:

| Sub-system | Role | Key constraint |
|---|---|---|
| **Two side plates (C-channels)** | Frame walls that hold everything; motor mounts to one | Must be long enough to span motor + flywheel + shaft collar (~6–10") |
| **Cross-members (standoffs)** | Space the two side plates apart at exactly the HS shaft length | Standoff length must match HS shaft length (2" shaft → 2" standoffs) |
| **HS Shaft Bearings** | Support the 1/4" HS shaft through the inner face of each side plate | Standard bearing flats do NOT fit 1/4" HS shaft |
| **HS Shaft Collars** | Retain shaft and wheel axially; prevent sliding | Standard shaft collars (1/8") do NOT fit HS shaft |
| **Backplate** | Flat surface the disc presses against as it passes the spinning wheel | Can be any existing steel or aluminum plate; no separate purchase needed |

The motor itself mounts directly to a C-channel using 4× standard #8-32 screws (already in kit) through the motor's four mounting holes — no special motor bracket is needed.

### 2. C-Channels — Side Plates [S3, S4]

VEX 1×2×1 C-channel is the standard building block. The Clawbot uses every C-channel included in the Starter Kit; the flywheel frame needs at minimum **two pieces ~7–10 holes long** (3.5–5").

Individual C-channel options on vexrobotics.com:

| SKU | Description | Qty per pack | Notes |
|-----|-------------|-------------|-------|
| **276-2906** | 1×2×1×35 Steel C-Channel | 2 | Can be hacksaw-cut; ~$13–18 |
| **276-2288** | 1×2×1×25 Aluminum C-Channel | 6 | Lighter; same hole spacing; ~$22–25 |
| **276-2289** | 1×2×1×35 Aluminum C-Channel | 6 | Longer for bigger frames; ~$28–35 |

**Minimum purchase: 1 pack of 276-2906 (steel, 2-pack)** — gives 2 C-channels, the exact minimum needed for one flywheel frame. If the Clawbot arm and claw are being disassembled for the morphology swap, the Clawbot's existing C-channels can be repurposed and no purchase is needed.

### 3. HS Shaft Bearings — Critical New Part [S2, S5]

The 1/4" HS shaft that exits the V5 Smart Motor is too large for the standard bearing flat holes. VEX makes a specific bearing for it:

| SKU | Description | Qty per pack | Notes |
|-----|-------------|-------------|-------|
| **276-3521** | High Strength Shaft Bearing | 10 | The only VEX part that supports the 1/4" HS shaft on structure |

**Quantity needed: 2** (one per side plate). The bearing mounts to the inner face of each C-channel; the HS shaft sits between the two bearings. The 276-3521 mounts using the same 3-hole pattern as a standard bearing flat (#8-32 screws or bearing attachment rivets through the outer two holes, shaft through the center hole).

> **NOT in the Starter Kit.** The Starter Kit includes Bearing Flats (for 1/8" shaft) but not HS Shaft Bearings. This is the single most critical purchase gap.

### 4. HS Shaft Collars — Retention [S2, S6]

Standard shaft collars (276-2010, 16-pack) fit 1/8" shafts; they cannot clamp a 1/4" HS shaft. VEX makes clamping collars for the HS shaft:

| SKU | Description | Qty per pack | Notes |
|-----|-------------|-------------|-------|
| **276-6102** | High Strength Clamping Shaft Collar | 4-pack or 10-pack | Clamps without scratching shaft |
| **276-7580** | Low Profile HS Clamping Shaft Collar | varies | Shorter; fits in tighter spaces |

**Quantity needed: 2** (one outside each bearing, to keep the shaft sandwiched between the two C-channels). Each collar clamps with a standard #8-32 screw + Nylock nut (already in kit).

> **NOT in the Starter Kit.**

### 5. HS Shaft — Flywheel Axle [S2, S7]

The V5 Smart Motor's output shaft is integral to the motor — it cannot be extended or swapped in place. To support the flywheel shaft between two C-channel side plates with bearings, a separate **HS shaft** is used as the flywheel axle (with the motor's own output coupling to a gear or the flex wheel adapter directly).

For the 2" flex wheel configuration (Approach A from vex-launch-disc-parts research):

| SKU | Description | Qty per pack | Notes |
|-----|-------------|-------------|-------|
| **276-3440** | High Strength Shaft 2" Long | 4 | Sits between 2" standoffs without cutting [S2] |
| **276-3524** | High Strength Shaft 12" Long | 4 | Can be cut to any length needed |

**Key design trick [S2]:** VEX 2", 3", and 4" HS shafts are designed ~1mm shorter than their corresponding #8-32 standoffs. If you use 2" standoffs to hold the two C-channels apart, a 2" HS shaft sits exactly between the HS Shaft Bearings without requiring any cutting or drilling of the C-channel holes.

**Quantity needed: 1** (2" shaft for the flywheel wheel axle). The Starter Kit may include a small number of HS shafts (from the arm gear reduction) but availability varies; purchasing a 4-pack ensures availability.

> **May not be in Starter Kit** in the right length or quantity. Verify before purchasing.

### 6. Standoffs — C-Channel Spacing [S1, S8]

#8-32 standoffs hold the two side-plate C-channels at the correct distance apart. For a 2" HS shaft + 2" HS Shaft Bearings:

- Use **2" (#8-32) standoffs** at the top and bottom of the C-channel opening.
- Minimum 2 standoffs; 4 recommended for rigidity.
- Additional standoffs connect the flywheel frame to the existing Clawbot drivetrain structure.

**Standoffs ARE in the Starter Kit** (various lengths including 2"). If the Clawbot build consumed most of them, the VEX standoff packs are sold individually (no confirmed SKU from this research — they are stocked individually on vexrobotics.com/standoffs-8-32.html).

### 7. Motor Mounting — No Extra Parts Needed [S1]

The V5 Smart Motor (both 11W and 5.5W variants) mounts directly to any VEX structural metal (C-channel, plate, U-channel, or angle) using **4× #8-32 screws** (any length from 1/2" to 3/4"). The motor has 4 factory-threaded inserts on its face; #8-32 screws pass through matching holes in the C-channel wall. No motor bracket or special adapter is required.

All needed screws are in the Starter Kit.

### 8. Backplate — No Extra Purchase Needed [S1]

A single-flywheel uses a flat rigid surface on the opposite side of the flywheel gap from the spinning wheel. The disc rolls along this surface as the flywheel accelerates it. Any VEX steel plate from the existing kit (or the arm structure plates) can serve this role. No additional purchase is needed.

### 9. What the Starter Kit Already Provides for Hardware [S8]

| Hardware | Included in Starter Kit? | Sufficient for flywheel? |
|---|---|---|
| #8-32 star drive screws (1/4", 1/2", 3/4") | ✓ | ✓ (motor mount + bearing mount) |
| Standoffs (2") | ✓ | ✓ (if enough remain after Clawbot build) |
| Keps nuts (#8-32) | ✓ | ✓ |
| Nylock nuts (#8-32) | ✓ | ✓ (shaft collar screws) |
| Standard Bearing Flats (1/8" shaft) | ✓ | ✗ (wrong bore for HS shaft) |
| HS Shaft Bearings (1/4" shaft, 276-3521) | **✗** | Required — must purchase |
| Standard Shaft Collars (1/8", 276-2010) | ✓ | ✗ (wrong bore for HS shaft) |
| HS Clamping Shaft Collars (1/4", 276-6102) | **✗** | Required — must purchase |
| 1×2×1 C-channels | ✓ (used in Clawbot) | ✗ if keeping Clawbot; ✓ if disassembling arm |

---

## Constraints

1. **All Starter Kit C-channels consumed by Clawbot** — the flywheel frame requires two C-channels for side plates; these must either be repurposed from the disassembled arm/claw or purchased.
2. **Standard bearings/collars are wrong size for HS shaft** — the V5 Smart Motor HS shaft is 1/4"; the kit's bearings and collars are for 1/8" shafts. Both must be purchased separately.
3. **Drilling HS shaft through C-channel** — the 1/4" HS shaft is larger than the standard 0.182" square holes in VEX C-channel. **For the standoff sandwich method (2" standoff + 2" HS shaft), no drilling is needed** — the shaft sits on the outer face of each HS Shaft Bearing and never passes through the structural metal. If a longer shaft through the structure is desired, a 5/16" (8mm) hole must be drilled [S2].
4. **Shaft collar screws must not over-tighten** — HS clamping collar uses a #8-32 screw; over-tightening can dig into the HS shaft. Use Nylock nut and snug rather than torque.
5. **Backplate gap tuning** — the compression distance between the flywheel wheel and the backplate must be set to ~1–2mm narrower than the disc diameter. This requires loosening the C-channel-to-frame connection and sliding the flywheel side slightly.

---

## Solution Comparison

| Approach | C-Channel Source | New Structural Purchases | Notes |
|---|---|---|---|
| **A — Reuse arm structure** | Disassemble Clawbot arm/claw; reuse those C-channels | 276-3521, 276-6102, 276-3440 (3 SKUs) | Fewest purchases; eliminates arm/grab as expected |
| **B — Purchase new C-channels** | Buy 276-2906 (steel) or 276-2288 (aluminum) | 276-2906 + 276-3521 + 276-6102 + 276-3440 (4 SKUs) | Keeps Clawbot intact for comparison; arm still accessible |

**Approach A is recommended** for the capstone exclusive-swap morphology model (launch_disc replaces arm/claw). Approach B is recommended if both morphologies need to be physically assembled simultaneously for comparison.

---

## Recommendation

### Minimum Structural BOM (Approach A — reuse arm structure)

| # | Part | SKU | Qty to Buy | Already in Kit? | Purpose |
|---|------|-----|-----------|----------------|---------|
| 1 | HS Shaft Bearing (10-pack) | **276-3521** | 1 pack (use 2) | **No** | Support 1/4" HS shaft through C-channel walls |
| 2 | HS Clamping Shaft Collar (4-pack or 10-pack) | **276-6102** | 1 pack (use 2) | **No** | Retain shaft axially; fix flex wheel position |
| 3 | HS Shaft 2" (4-pack) | **276-3440** | 1 pack (use 1) | No (or insufficient) | Flywheel axle between side plates |
| — | 2" #8-32 Standoffs | N/A | 0 (use 4 from kit) | **Yes** | Space C-channels to match shaft length |
| — | #8-32 screws (1/2" and 3/4") | N/A | 0 | **Yes** | Motor mount (4×) + bearing mount (4×) |
| — | Keps nuts / Nylock nuts | N/A | 0 | **Yes** | Fasten standoffs; collar screw locking |
| — | C-channels (2× 1×2×1) | N/A | 0 (reuse from arm) | **Yes (via reuse)** | Side plates of flywheel frame |
| — | Steel/aluminum plate (backplate) | N/A | 0 (reuse from kit) | **Yes** | Disc guidance surface |

**3 purchase lines total; uses 2 pack + 2 bearings + 1 shaft from each pack.**

### Minimum Structural BOM (Approach B — keep Clawbot intact)

Add to the above:

| # | Part | SKU | Qty to Buy | Purpose |
|---|------|-----|-----------|---------|
| 4 | 1×2×1×35 Steel C-Channel (2-pack) | **276-2906** | 1 pack (use 2) | Side plates of flywheel frame |

**4 purchase lines total.**

### Assembly Sequence (Structural Only)

1. Lay two C-channels flat, open face inward, parallel and ~2" apart (top and bottom edges aligned).
2. Mount one HS Shaft Bearing (276-3521) to the **inner face** of each C-channel at the same hole position, using 2× #8-32 screws + Keps nuts per bearing.
3. Insert four 2" standoffs between the two C-channels at the four corners of the bearing area; tighten to lock the 2" spacing.
4. Slide the 2" HS shaft (276-3440) through both bearings from the outside. It will rest on the bearing surfaces.
5. Mount the flex wheel onto the shaft using VersaHex adapters (from vex-launch-disc-parts research).
6. Clamp one HS shaft collar (276-6102) on each side of the flywheel frame, outside the bearings, to prevent axial shift.
7. Mount the V5 Smart Motor to one end of the outer C-channel face using 4× #8-32 screws (3/4" length). The motor HS output shaft couples to the flex wheel through the VersaHex adapter system.
8. Mount a flat steel plate as a backplate, positioned at ~1–2mm compression distance from the flywheel wheel OD.
9. Attach the entire flywheel sub-assembly to the Clawbot's main drivetrain frame using standoffs and #8-32 screws at the appropriate mounting holes.

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| HS shaft bearing holes misaligned between C-channels | Use a long shaft as an alignment pin during assembly before tightening standoffs |
| Shaft collar overtightened — digs into HS shaft | Use Nylock nut and hand-tighten plus 1/4 turn; inspect shaft for burr before reuse |
| Standoff spacing wrong — shaft doesn't sit in bearings | Measure standoff length against shaft length before final assembly; 2" shaft is 1mm shorter than 2" standoff (correct) |
| C-channel flex under high-speed vibration | Add a third C-channel or a gusset at the top connecting both side plates for rigidity |

---

## Next Steps

- **To purchase (structural only)**: Add 276-3521 + 276-6102 + 276-3440 (+ 276-2906 if keeping Clawbot arm) to cart at vexrobotics.com.
- **For complete flywheel BOM**: Combine with mechanism parts from `raw/research/vex-launch-disc-parts/index.md` (276-5842 cartridge + 217-6354/6449 flex wheel + 217-7947 VersaHex adapters).
- **For wiki**: Run `/wiki-ingest raw/research/vex-flywheel-structure-parts/index.md` to synthesize into the knowledge base and update `wiki/knowledge/entities/tools/vex-v5.md`.
- **To task**: `/task-add "Build flywheel structural frame: purchase 276-3521 + 276-6102 + 276-3440, reuse arm C-channels, assemble side plates with 2-inch standoffs"`
