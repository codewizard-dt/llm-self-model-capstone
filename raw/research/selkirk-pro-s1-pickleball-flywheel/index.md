---
topic: "Is the Selkirk Sport Pro S1 pickleball from Academy a good ball for the VEX flywheel?"
slug: "selkirk-pro-s1-pickleball-flywheel"
researched: 2026-06-25
sources: [./sources.md]
---

# Research: Selkirk Pro S1 Pickleball For VEX Flywheel

> The Selkirk Pro S1 pickleball is a usable flywheel test ball, but it should not replace the racquetball as the default capstone game object. For a flywheel-only prototype it is worth buying/testing because it is light, durable, bright, USAP-approved, and sized near the flywheel's workable diameter range. For the full claw+scoop+flywheel robot, it is worse than a racquetball because it is too large for the current scoop window, lighter and more draggy, and its holes can make wheel contact and flight less predictable.

## Research Questions

- What are the Selkirk Pro S1's physical specs and material properties?
- Does it fit the existing capstone flywheel diameter/compression window?
- Does it remain compatible with the claw and passive scoop morphologies?
- What risks does a perforated hard-plastic pickleball introduce compared with the current racquetball recommendation?
- What should be tested before adopting it?

## Current State (Codebase)

The existing game-object research recommends a standard racquetball: 57 mm diameter, about 40 g, hollow rubber, medium compressibility, and compatible with the claw, scoop, and flywheel at the same time [S1]. The current wiki captures the key intersection: claw sweet spot 55-75 mm, passive scoop max <=65 mm, flywheel optimal 55-75 mm, yielding an all-morphology intersection of 55-65 mm [S2].

The flywheel page also says spherical balls in roughly the 55-75 mm range can work if compression is tuned, with target compression around 10% of object diameter [S3].

## Key Findings

- The Academy product is the Selkirk Sport Pro S1 Pickleball Balls 4-Pack, SKU 141792241 / item 10053_PRO-S1-BALL-4PK, priced at $9.99 when accessed [S4].
- Academy lists the Pro S1 as rotomold plastic, seamless rotomolded, 38-hole, USAP-approved, bright neon, indoor/outdoor, and backed by a 1-year no-crack warranty [S4].
- Selkirk's own product page lists 38 holes, 0.93 oz weight, 2.8 in diameter, USAP approval, seamless rotomolding, maintained shape, and a 1-year no-crack warranty [S5].
- USA Pickleball's Equipment Standards Manual says compliant balls are 2.87-2.97 in diameter, 0.78-0.935 oz, bounce 30-34 in from a 78 in drop, compression under 43 lbf, and have 26-40 circular holes [S6].
- There is a small spec tension: Selkirk/retail listings round or state the diameter as 2.8 in (71.1 mm), while USA Pickleball's standard range is 2.87-2.97 in (72.9-75.4 mm). Since the same product is marked USAP-approved, treat the practical build diameter as about 71-75 mm and measure the actual balls before setting the backplate gap [S5] [S6].
- Compared with the current racquetball default, the Pro S1 is larger (about 71-75 mm vs 57 mm), lighter (26.4 g vs about 40 g), harder/plastic instead of rubber, and perforated rather than smooth [S1] [S5].

## Constraints

- The current passive scoop target is <=65 mm, so the Pro S1 likely fails the all-morphology object requirement even if the flywheel can launch it [S2].
- The flywheel can likely accommodate the diameter if the backplate gap is reset. With the existing 10% compression rule, a 71-75 mm ball implies a wheel-rim-to-backplate gap of roughly 64-68 mm.
- Because the ball has holes, contact against a single flywheel may vary depending on where the wheel hits the shell. This is an engineering inference from the geometry; the sources confirm the 38-hole design but do not directly test VEX flywheel launch consistency.
- The ball is light and hollow, so it should be safe and easy to accelerate, but it may also lose speed quickly and curve more in flight than a denser smooth rubber ball. This is an inference from mass/shape, not directly measured in the sources.

## Solution Comparison

| Criteria | Selkirk Pro S1 Pickleball | Racquetball |
|----------|---------------------------|-------------|
| Approach | Use as flywheel-only test object | Keep as default all-morphology object |
| Diameter | About 71-75 mm; inside flywheel range but above scoop target | 57 mm; inside claw+scoop+flywheel intersection |
| Weight | 0.93 oz / 26.4 g; easy to accelerate | About 40 g; more momentum, still light enough |
| Material/contact | Rotomold plastic with 38 holes; contact may vary | Hollow smooth rubber; predictable wheel contact |
| Flywheel fit | Plausible, with wider backplate gap | Stronger fit under current plan |
| Scoop fit | Likely poor with <=65 mm scoop window | Good |
| Vision | Bright neon green, strong visibility | Usually bright blue/green, also good |
| Durability | 1-year no-crack warranty; designed for play impacts | Designed for repeated wall impacts |
| Codebase fit | Good for a flywheel-only experiment | Best for continuity across morphology swaps |

## Recommendation

Buy/test the Selkirk Pro S1 if the immediate question is "will this flywheel launch a lightweight hollow ball?" Do not make it the default capstone game object unless the scoop is redesigned wider or the demo no longer needs scoop compatibility.

Recommended test setup:

1. Measure the actual ball diameter with calipers. Do not trust the rounded 2.8 in listing if you are setting a tight backplate gap.
2. Start with wheel-rim-to-backplate gap at 90% of measured diameter. For 72 mm, start around 65 mm.
3. Spin the flywheel at a conservative speed first, then increase speed while watching for shell chatter, sideways kick, and current spikes.
4. Run 10 shots and record distance/lateral error. Compare against 10 racquetball shots from the same flywheel speed.
5. Inspect for cracks, ovalization, or whitening around contact points.

Adoption rule:

- Use the Pro S1 if it launches consistently enough for the demo and the task is flywheel-only.
- Keep racquetball as the default if the same object must work across claw, scoop, and flywheel.
- Reject the Pro S1 if the holes cause erratic exits, the ball chatters in the wheel/backplate gap, or the larger diameter breaks the feed/indexer path.

## Next Steps

- To create a validation task: `/task-add Compare racquetball vs Selkirk Pro S1 in the VEX flywheel: measure diameter, tune backplate gaps, fire 10-shot groups, and log range/lateral spread/current draw`.
- If the Selkirk ball performs well, ingest this report and update `game-object-selection` with a flywheel-only alternative.
- If the scoop must remain part of the demo, do not switch the default object without widening the scoop and re-running scoop tests.
