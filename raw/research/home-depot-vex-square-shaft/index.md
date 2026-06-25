---
topic: "Does Home Depot carry a longer square shaft usable for the VEX flywheel, or should the build switch balls?"
slug: home-depot-vex-square-shaft
researched: 2026-06-25
sources: [./sources.md]
---

# Research: Home Depot Square Shaft vs. Changing Balls

> Home Depot does carry 1/4 in square steel bar stock in longer lengths, so a longer shaft is locally obtainable. It should be treated as a raw shaft blank, not a guaranteed drop-in VEX High Strength Shaft. For the flywheel plan, the best path is to buy a 1/4 in square steel bar only if it fit-tests through the VEX High Strength bearings, collars, and wheel/adapter stack; otherwise, change the projectile or build a single-sided prototype instead of forcing a two-plate racquetball launcher around the existing 2 in shafts.

## Research Questions

- What shaft geometry does the current VEX flywheel plan need?
- Does Home Depot carry a same-day square steel shaft candidate?
- Is the Home Depot stock a drop-in replacement for a VEX High Strength Shaft?
- Should the build change balls instead of buying a longer shaft?

## Current State

- The current flywheel plan is based on a racquetball-scale projectile between side plates, with prior working geometry around a 65 mm blue-plate inside spacing and a 51 mm wheel-rim-to-backplate throat for a 57 mm ball [S1].
- The known ordered VEX parts include 2 in High Strength Shafts, High Strength Shaft Bearings, High Strength collars, smart motors, plates, and compression wheels [S2].
- VEX High Strength shaft geometry is 0.25 in / 6.35 mm square, while standard VEX shafting is 0.125 in square [S3][S5].
- VEX High Strength shafts cannot pass through normal VEX structural square holes without drilling a larger 5/16 in or 8 mm hole [S5].

## Key Findings

- Home Depot currently lists Everbilt 1/4 in x 3 ft plain steel solid square bar, Model 0503 / Internet 332734018, and describes it as cold-rolled low-carbon steel that should be cut with a metal saw [S6].
- Home Depot also lists Everbilt 1/4 in x 1 ft zinc-plated steel solid square bar, Model 1656 / Internet 332735183, and describes it as key stock with a zinc-plated corrosion-resistant finish [S7].
- VEX official documentation states that High Strength Shafts are 1/4 in square bar and are used with High Strength-compatible motion parts [S4][S5].
- VEX also explicitly sells longer official High Strength shaft lengths, including 3 in, 4 in, and 24 in, but the user constraint is no more VEX orders, so this only confirms what geometry the Home Depot blank is trying to imitate [S4].
- The Home Depot part is therefore dimensionally promising, but not verified as VEX-compatible. The risk is tolerance and finish: commodity square bar may be slightly oversized, plated, sharp-cornered, burred after cutting, or not straight enough for a high-RPM flywheel. This is an inference from the difference between raw bar stock and VEX drivetrain hardware, not a stated claim from either vendor.

## Constraints

- No additional VEX parts should be ordered.
- The current on-hand VEX shafts are 2 in High Strength shafts.
- A racquetball is approximately a 57 mm projectile class, so a two-side-plate launcher wants a wider structure than the 2 in shaft can comfortably span if the wheel is supported on both sides.
- The flywheel shaft must drive square-bore compatible components; a round rod or threaded rod is not a substitute for the driven shaft.
- A high-speed flywheel is more sensitive to wobble than a slow pivot or spacer.

## Solution Comparison

| Criteria | Use Existing 2 in VEX Shaft + Smaller/Soft Ball | Buy Home Depot 1/4 in Square Bar | One-Sided/Cantilever VEX Prototype |
|---|---|---|---|
| Approach | Keep official VEX shafting and reduce projectile/launcher width | Cut a longer 1/4 in square steel blank locally | Put motor and wheel on one plate, use the opposite plate only as guide/backplate |
| Pros | Safest shaft compatibility; no raw metal shaft uncertainty | Preserves racquetball-sized two-plate layout; cheap and same-day | No longer shaft needed; fastest geometry proof |
| Cons | Changes projectile behavior; compressible foam may not launch reliably | Fit and straightness are not guaranteed; must deburr and test | More shaft/motor load; not ideal for final high-RPM durability |
| Complexity | Low | Medium | Medium |
| Fit to current plan | Lower if racquetball is required | Best if it passes fit tests | Good for testing, weaker as final build |
| Main failure mode | Ball is too soft/light or too small for useful launch | Shaft binds, wobbles, or does not fit adapters | Wheel deflects or motor face takes too much load |

## Recommendation

Buy one Home Depot 1/4 in square steel bar as the same-day fallback, preferably the 1 ft zinc-plated key-stock style or the 3 ft plain steel square bar if longer stock is easier to cut cleanly. Bring one VEX High Strength bearing, collar, and any wheel/adapter part to the store if practical. The purchase is worth it because the cost is low and it could preserve the racquetball geometry.

Do not commit the final flywheel design to the Home Depot shaft until it passes these checks:

1. It slides through the High Strength Shaft Bearing without force.
2. A High Strength collar clamps it without rocking.
3. The wheel/adapter stack slides on without scraping or cracking plastic.
4. After cutting, both ends are filed/chamfered and all burrs are removed.
5. The shaft spins unloaded at low RPM without visible wobble before adding a ball.

If any of those checks fail, use the existing 2 in VEX shaft and either switch to a smaller projectile or build a one-sided/cantilever proof-of-geometry launcher. The highly compressible foam balls are a poor first validation projectile for flywheel spacing because they can collapse too much and hide whether the launcher geometry is actually right. A racquetball is the better geometry reference; a softer ball can be tested after the launcher is mechanically stable.

## Next Steps

- At Home Depot, look for "1/4 in. x 1 ft. Zinc Plated Steel Solid Square Bar" or "1/4 in. x 3 ft. Plain Steel Solid Square Bar."
- Avoid threaded rod and round rod for the driven flywheel shaft.
- Buy or use a file/hacksaw/cutoff tool to cut and deburr the square bar cleanly.
- Use the `wiki-ingest` skill on this research file if the decision should become part of the robot hardware knowledge base.
