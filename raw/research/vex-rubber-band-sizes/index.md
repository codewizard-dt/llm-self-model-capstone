---
topic: "VEX rubber bands #32 and #64 — what the numbers mean and different uses"
slug: vex-rubber-band-sizes
researched: 2026-06-18
sources: [./sources.md]
---

# Research: VEX Rubber Band Sizes #32 and #64

> The numbers are standardized industry size codes from the Alliance Rubber Company system, where the number encodes the band's flat dimensions: #32 = 3" × 1/8" (narrower, lighter tension) and #64 = 3.5" × 1/4" (wider, stronger). In VEX robotics, #32 suits precision mechanisms (latches, triggers, return springs), while #64 is the workhorse for lift assistance, catapults, and intake rollers. Both are sold in three material variants — synthetic, silicone, and EPDM — chosen by use case rather than size.

## Research Questions

1. What does the number designation (#32, #64) actually mean in rubber band sizing?
2. What are the exact dimensions of each?
3. What are the different use cases for #32 vs #64 in VEX robotics?
4. Are there material-type differences (synthetic, silicone, EPDM) that interact with size choice?
5. What does VEX competition rules say about legal rubber band sizes?

## Current State (Codebase)

Not applicable — this is product/hardware research, not codebase analysis.

## Key Findings

### The Numbering System [S1, S2, S3]

Rubber band size numbers come from a standardized system developed by Alliance Rubber Company (est. 1923) and used industry-wide. The number encodes **both flat length and cut width** in a grouped scheme:

- Numbers 8–19: all 1/16" wide, increasing in length (7/8" to 3.5")
- Numbers 30–35: all 1/8" wide, increasing in length
- Numbers 60s: all 1/4" wide, increasing in length
- Numbers 80s: all 1/2" wide

So the "3" in #32 places it in the 1/8"-wide family, and "2" orders it within that family by length.

### Exact Dimensions [S2, S3]

| Size | Flat Length | Cut Width | Metric |
|------|------------|-----------|--------|
| **#32** | 3 inches | 1/8 inch | 76mm × 3.2mm |
| **#64** | 3.5 inches | 1/4 inch | 89mm × 6.4mm |

The #64 is thus slightly longer **and** twice as wide, making it substantially stronger and capable of storing more elastic energy.

### VEX Competition Legality [S4]

VEX V5 Robotics Competition (VRC) rules explicitly allow:
- **#32** — 3" × 1/8" when not stretched under load
- **#64** — 3.5" × 1/4"
- **#117B** — approximately 7" in diameter

Teams may use off-brand rubber bands purchased in bulk (e.g., from Amazon or office supply stores) as long as dimensions match these standards.

### VEX Product Variants [S5]

VEX sells both #32 and #64 in three materials, each optimized for a different use:

| Material | Best for | Why |
|----------|----------|-----|
| **Synthetic (standard latex)** | Latches, triggers, return mechanisms, catapults | High elongation, stores energy well |
| **EPDM (synthetic rubber)** | High elongation uses, outdoor/chemical resistance | Similar to latex but synthetic; better durability |
| **Silicone** | Intake rollers, grip surfaces | Higher coefficient of friction against plastic → grips game pieces better |

### Robotics Use Cases by Size [S5, S6, S7]

**#32 (3" × 1/8") — precision and light force:**
- Latches and trigger mechanisms (lighter actuation force)
- Return springs for lightweight arms or flaps
- Fine-tuning tension where precision matters — described as "the goldilocks size for linear tensioning" [S6]
- Stacking multiple bands to dial in exact force increments
- Lighter counterbalancing on small pivoting assemblies

**#64 (3.5" × 1/4") — power and grip:**
- **Lift/arm counterbalancing** — reduces motor load by up to ~30%, enabling 1-motor lifts that compete with 2-motor designs
- **Catapult and slingshot energy storage** — wider cross-section stores more elastic potential energy per band
- **Intake rollers** — looped around sprockets as a rolling surface; silicone #64 has especially high friction for gripping game pieces
- Heavy return mechanisms (heavier arms, claws)
- Scissor lift assistance (documented in competition research [S7])
- Most popular size for general VEX use — community tends to default to #64 when buying in bulk

**Both sizes** share this core category of uses:
- "Free energy" passive assistance — stored elastic energy that does mechanical work without motor power
- Rubber band–powered passive mechanisms (self-resetting triggers, latch releases)

## Constraints

- VRC game rules enumerate exactly which sizes are legal — teams cannot use non-standard band sizes even if they'd work better
- Silicone and EPDM are latex-free, relevant for allergy concerns in classroom settings
- VEX's official packs come in small quantities (often 10-packs); budget-conscious teams buy standard sizes (#32, #64) in bulk from office suppliers

## Recommendation

For a VEX V5 robot build:
- **Start with #64** as the default. It is the community's go-to size, available cheaply in bulk, and handles the highest-impact use case (lift assist, catapult, intake rollers).
- **Add #32** for lighter, precision mechanisms: triggers, latches, small return springs.
- **Choose silicone** for any intake roller application where you need grip on game pieces.
- **Choose synthetic/EPDM** for energy storage (catapults, lift counterweights).

## Next Steps

- Run `/wiki-ingest raw/research/vex-rubber-band-sizes/index.md` to add this to the knowledge base
- Consider a concept page: `wiki/knowledge/concepts/rubber-band-mechanisms.md`
- If building a specific mechanism, consider `/task-add` for the relevant subsystem
