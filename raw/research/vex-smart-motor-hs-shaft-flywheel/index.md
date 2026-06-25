---
topic: "How VEX V5 Smart Motors normally drive High Strength shafts and compression-wheel flywheels, and what this means for the foam golf ball build"
slug: vex-smart-motor-hs-shaft-flywheel
researched: 2026-06-25
sources: [./sources.md]
---

# Research: VEX Smart Motor, High Strength Shaft, and Flywheel Fit

> The V5 Smart Motor is not the blocker: official VEX docs state that its shaft socket accepts both standard 1/8 in shafts and 1/4 in High Strength shafts. The blocker is the steel plate: 1/4 in HS shafts do not pass through normal VEX structural holes unless a 5/16 in or 8 mm clearance hole is drilled, or the shaft is kept between HS bearings mounted to the inside faces of the plates. Because the current projectile is now a foam golf ball, the fastest working prototype should use the compression wheel kit's 1/8 in shaft adapter path first; reserve the HS shaft path for a stronger fallback if the 1/8 in shaft flexes or slips.

## Research Questions

- Does a V5 Smart Motor accept a 1/4 in High Strength shaft directly?
- Why does the HS shaft not fit through the VEX steel plate holes?
- What adapters are included in the 276-8882 compression wheel kit?
- How are HS shafts normally supported in VEX structure?
- What is the fastest correct build path for the foam golf ball flywheel?

## Current State

The local wiki already records that the current order includes the 276-8882 60A compression wheel kit, 276-3440 2 in HS shafts, 276-3521 HS Shaft Bearings, and 276-6102 HS clamping collars [S1]. It also records the earlier HS-shaft flywheel frame plan: mount HS Shaft Bearings to side plates, set plate spacing with standoffs, and let the 2 in HS shaft sit between the bearings without passing through structural metal [S2].

Recent design work changed the projectile from a 57 mm racquetball to a foam golf ball, approximately 42.7 mm / 1.68 in. That smaller, softer ball reduces shaft load and allows a narrower launcher throat than the racquetball layout [S3].

## Key Findings

- The V5 Smart Motor shaft socket accepts both high-strength 1/4 in shafts and standard 1/8 in shafts [S4][S5].
- High Strength shafts are 1/4 in square bar. They are only compatible with VEX motion products designed for the larger shaft and will not pass through normal VEX structural metal holes unless a 5/16 in or 8 mm clearance hole is drilled [S5].
- VEX's HS Shaft Bearing guidance explicitly allows a no-drill sandwich: choose an HS shaft length that fits between two bearings attached to two pieces of structural metal. In that layout, the shaft does not pass through the metal; it is supported by the bearing plastic [S5].
- VEX's HS hardware product page says the 2 in, 3 in, and 4 in HS shafts are slightly shorter than corresponding #8-32 standoffs, allowing the shaft to sit on bearings between structural pieces without cutting [S6].
- The 276-8882 kit is a 2 in, 60A compression wheel kit. The VEX page says the 1.625 in and 2 in compression wheel kits include 1/2 in VersaHex adapters with 1/4 in square bore and 1/2 in hex to 1/8 in square hub adapters [S7].
- VEX's mechanical launching guidance says ball bearings reduce launcher friction and outperform bushings at high speed. The purchased 276-3521 HS Shaft Bearings are nylon bushings, not the later 276-8402 HS ball bearings, so they are acceptable for a fast prototype but not ideal for a final high-speed launcher [S8].
- Brave Search surfaced the same official VEX sources and also VEX's Smart Motor product page, which says the 6:1 cartridge is best used for intake rollers, flywheels, and other fast mechanisms [S9].

## Constraints

- No additional VEX orders are planned.
- The available HS shafts are only 2 in long.
- The VEX plate holes are not large enough for a 1/4 in HS shaft.
- The user may not have a drill or metal saw available immediately.
- The current projectile is a foam golf ball, not a racquetball.

## Solution Comparison

| Criteria | 1/8 in Shaft Prototype | HS Shaft No-Drill Sandwich | HS Shaft Through Drilled/Notched Plate |
|---|---|---|---|
| Approach | Use standard 1/8 in shaft through normal plate holes and the compression kit's 1/8 in adapter | Use 2 in HS shaft between HS bearings inside two plates/standoffs | Drill/notch 5/16 in or 8 mm clearance in motor-side plate and run HS shaft through |
| Pros | Fastest; no new cutting/drilling; uses normal VEX holes | Uses purchased HS parts; no plate drilling if spacing matches | Strongest direct-drive path with better shaft stiffness |
| Cons | Less stiff than HS shaft; may wobble at high load | Tight packaging; 2 in shaft limits side spacing; bushings add friction | Requires drilling/notching steel plate accurately |
| Complexity | Low | Medium | High |
| Best use | Foam golf ball proof-of-function | Compact final-ish prototype if 2 in spacing works | Final HS version if tools are available |

## Recommendation

Build the foam golf ball launcher first with the standard 1/8 in shaft path:

1. Mount the V5 Smart Motor outside one VEX side plate.
2. Insert a standard 1/8 in VEX shaft through the normal plate hole into the motor socket.
3. Mount the 2 in, 60A compression wheel using the kit's 1/2 in hex to 1/8 in square adapters.
4. Use standard 1/8 in collars/spacers to control side play.
5. Set the wheel-rim-to-backplate gap to 37 mm, adjustable from 34-39 mm, for the foam golf ball.

Switch to the HS shaft path only if the 1/8 in setup visibly bends, wobbles, or slips. In the HS fallback, do not expect the shaft to pass through unmodified plate holes. Either keep the HS shaft between HS bearings using the standoff sandwich trick, or drill/notch a 5/16 in / 8 mm clearance hole where the HS shaft must pass through steel.

## Next Steps

- Update the wiki to mark the foam-golf-ball 1/8 in shaft prototype as the immediate build path.
- Keep the existing HS shaft cassette plan as a fallback and explicitly document the plate-hole clearance issue.
- If the prototype works, collect telemetry on RPM drop and current spike to decide whether HS shaft or ball bearings are worth pursuing after the demo.
