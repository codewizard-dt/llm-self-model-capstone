---
topic: "Flywheel recut plan for two VEX 5x15 steel plates"
slug: flywheel-plate-recut-plan
date: 2026-06-25
source_type: user-plan-synthesis
status: ingested
---

# Flywheel Recut Plan for Two VEX 5x15 Steel Plates

## Context

The flywheel build now assumes two ordered VEX 5x15 Steel Plates, no spare U-channel or C-channel, and no further VEX orders. Additional Home Depot spacers, bolts, washers, and straps are allowed. The VEX plates are precision structure; the Home Depot straps are secondary brace, chute, and backplate material unless their hole pattern is measured.

The phrase "5x15 plate" means a 5-hole by 15-hole VEX grid on 0.500 in pitch, not a literal 5 in by 15 in sheet. By hole-count times pitch, nominal grid spans are 2.5 in x 7.5 in for 5x15, 2.5 in x 5.0 in for 5x10, and 2.5 in x 2.5 in for 5x5. The plates are thin steel and can be cut with suitable aviation snips, but the safest cuts are straight cross-cuts between hole rows. Lengthwise strip cuts are not preferred for bearing plates because the long cut edge can curl and the remaining strip is less resistant to shaft-alignment error.

## Candidate Cut Layouts

### Recommended: 5x8 + 5x7 split

Cut each 5x15 plate into:

- one 5x8 plate
- one 5x7 plate

The two 5x8 pieces become matched left/right flywheel side plates. The two 5x7 pieces become an adjustable backplate, chute wall, top bridge, lower rail, or motor brace. This is the preferred first build because it preserves a compact matched bearing cassette and still leaves useful VEX-grid material for the non-spinning ball guide structure.

### Alternate: 5x10 + 5x5 hole-grid split

Cut each 5x15 plate into:

- one 5x10 plate
- one 5x5 plate

The two 5x10 hole-grid pieces, nominally 2.5 in x 5.0 in by hole-count times pitch, become longer matched side plates with more fore-aft adjustment room. The two 5x5 hole-grid pieces, nominally 2.5 in x 2.5 in, become gussets, motor brackets, or short chute-entry plates. This is better when the motor, wheel, fixed-arm mount, or ball path location is still uncertain, but it leaves less VEX-grid material for a long backplate; the Home Depot strap should become the adjustable backplate in this layout.

### Rejected first cuts

Do not start with a 5x6 + 5x5 + 5x4 split. It creates many small brackets but no clearly strong matched side plates.

Do not start with lengthwise 2x15 and 3x15 strips for the bearing supports. They are more likely to twist, curl during cutting, or lose bearing alignment.

Leaving both plates uncut at 5x15 is valid for a bench mockup, but it is too bulky for the robot-mounted cassette and wastes precision VEX material.

## Assembly Principles

The flywheel should remain a single-wheel-plus-backplate launcher. The cassette should use matched VEX plate pieces as side plates, HS shaft bearings in identical holes, a 2 in high-strength shaft, clamping collars, spacers, and the 60A compression wheel. The Home Depot straps should be used for frame bracing, fixed-arm adapter support, chute extension, or the adjustable backplate.

For the very soft foam balls, start with minimal compression and treat them as feed-test objects only unless they rebound reliably. A racquetball or less-collapsible foam ball remains the better object for launch telemetry.

## Verification

Before cutting steel, mock the two layouts in cardboard at true VEX hole spacing. After cutting, deburr all edges. Assemble the matched side plates with bearings first and verify that the shaft spins freely before adding the motor, backplate, or ball guide.
