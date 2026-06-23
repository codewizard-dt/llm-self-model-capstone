---
topic: "How to feasibly replace the VEX V5 Clawbot claw with a passive scoop made from a non-kit household item, using the existing two-screw bracket mount with 1\" inner gap"
slug: clawbot-scoop-replacement
researched: 2026-06-22
sources: [./sources.md]
---

# Research: Clawbot Claw → Household Scoop Replacement

> The claw + claw-motor assembly on the VEX V5 Clawbot can be removed entirely with just two #8-32 screws, leaving a pair of parallel C-channel bracket faces 1 inch apart with 0.5"-spaced mounting holes. The easiest replacement is a **kitchen serving spoon** (plastic preferred over stainless): drill two 11/64" (4.5 mm) clearance holes through the flat handle 0.5" apart, slide it into the bracket gap, and reuse the original screws + hex nuts. Total build time: ~5 minutes. Zero new parts needed.

---

## Research Questions

1. What are the exact mounting dimensions at the arm tip, and what do they constrain?
2. Which household/kitchen items are already scoop-shaped and fit within the 1" gap?
3. How do you attach a non-VEX item to #8-32 bracket holes without new hardware?
4. What are the practical trade-offs between the candidate items?
5. How does this morphology change affect the capstone self-model and Task Telemetry Contract?

---

## Current State (Codebase)

The Clawbot build instructions (`raw/276-6009-750-Rev6.pdf`, wiki page `wiki/knowledge/sources/vex-v5-clawbot-build-instructions.md`) establish:

- Standard fastener throughout: **#8-32 star-drive screws + hex nuts** [S1]
- VEX hole grid: **0.500" (12.70 mm)** center-to-center [S1]
- Claw uses 1× V5 Smart Motor 11W (port 3 or 8) + a 12T gear + two #32 rubber bands [S1]
- The arm tip bracket exposes two parallel C-channel faces; the claw + motor bolts between them

The reference image `raw/42e6b947-2207-47e8-95f3-dae3ddbffafb.jpg.jpeg` confirms: two screws on the right-hand bracket face (circled in magenta) are the only fasteners holding the entire claw + motor assembly. The stated inner bracket gap is **1" (25.4 mm)**.

CAD research (`wiki/knowledge/sources/vex-v5-cad-designs.md`) confirms:
- VEX #8-32 mounting hole diameter: ~4.2 mm [S2]
- All VEX structural holes on 0.500" grid [S2]

---

## Key Findings

**F1 — Bracket geometry is well-suited to accepting thin-handle items [S1, S2]**
The 1" gap (25.4 mm) comfortably accepts any item whose mounting-point cross-section is ≤ 22 mm wide. The two screw holes are 0.5" apart vertically. An item drilled with matching holes can be clamped rigidly between the bracket faces using the original screws and hex nuts.

**F2 — Kitchen serving spoon handles fit the gap with room to spare [S3, S4]**
Stainless steel serving spoon handles are 1.0–1.5 mm thick and 10–15 mm wide. Plastic serving spoons are 3–5 mm thick, 10–15 mm wide. Both fit the 1" gap with 10+ mm clearance. The flat mid-handle region (between bowl transition and grip flare) is the correct drilling zone [S3].

**F3 — 11/64" (4.5 mm) is the correct clearance drill size for #8-32 [S1]**
#8-32 screw body diameter is 4.17 mm; 4.5 mm / 11/64" gives ~0.33 mm clearance — standard practice. For stainless steel use an HSS bit with cutting oil; for plastic any twist bit works [S5].

**F4 — Protein powder / coffee scoops are an excellent zero-drilling alternative if the handle is wide enough [S4]**
Plastic powder scoops have a wide bowl (ideal scoop shape) and handles typically 8–12 mm wide. Their handles are soft enough to compress slightly when clamped, potentially allowing a no-drill friction mount. If the handle is narrower than the bracket hole the screw head will bridge the gap.

**F5 — No-drill alternative: zip ties or hose clamps [S5]**
If preservation of the item is desired (no holes), heavy-duty cable ties (4.8 mm+ width) or a #4 hose clamp can bind the handle to the outside face of each bracket. Less rigid than a bolted mount but requires no tools.

**F6 — The claw motor is freed and should be noted in the self-model [S1]**
Removing the claw assembly frees one V5 Smart Motor 11W. The brain program's port assignment should be updated: the claw command (`spin_for` on the claw port) becomes a no-op or is removed.

---

## Constraints

- **1" bracket gap** — mounting cross-section of replacement must be ≤ ~22 mm wide
- **0.500" hole spacing** — drilled holes must match, or the item must be narrow enough for the screw head to clamp it (< 4.2 mm hole diameter in the item, i.e. no holes at all)
- **#8-32 screws only** — no tapping required if clearance holes are used; just screw + nut
- **Arm motor still lifts/lowers** — the scoop will follow the arm arc; the Task Telemetry Contract "reach" and "lift_height" parameters are unchanged
- **No new VEX hardware required** — hex nuts and screws already in the kit

---

## Solution Comparison

| Criteria | Plastic Serving Spoon | Stainless Serving Spoon | Plastic Powder Scoop | Zip-tie clamp (any item) |
|----------|-----------------------|------------------------|----------------------|--------------------------|
| **Approach** | Drill 2 holes, bolt into gap | Drill 2 holes (HSS bit), bolt in | Drill or clamp | Bind handle to bracket face |
| **Pros** | Easiest to drill, perfect shape, rigid | Most rigid, survives drops | Wide bowl, very easy | No drilling, preserves item |
| **Cons** | Less rigid than metal | Requires HSS bit + oil | Shorter reach | Loosens over time |
| **Complexity** | Low | Low-Medium | Low | Low |
| **New hardware** | None | None | None | Zip ties (~$1 at any store) |
| **Rigidity** | ★★★★ | ★★★★★ | ★★★ | ★★ |
| **Overall** | ★★★★★ | ★★★★ | ★★★★ | ★★★ |

---

## Recommendation

**Use a plastic kitchen serving spoon — drill method.**

1. Source any large plastic serving spoon from the kitchen (10–13" long, flat handle).
2. Hold handle flat against the bracket face; mark through the two holes (0.5" spacing).
3. Drill with any ≥ 4.5 mm bit (plastic: no center punch needed, no oil needed).
4. Slide handle into the 1" bracket gap, align holes, insert original #8-32 screws, add hex nuts inside, tighten.
5. Orient bowl facing forward/slightly up before final tightening.

**If a plastic spoon is unavailable:** use a protein powder scoop or coffee scoop — same steps, even easier to drill.

**If no drill available:** zip-tie method. Two cable ties per bracket face, pulled very tight. Check tightness before each use.

### Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Spoon rotates in bracket during scooping force | Add a third zip tie or use thread-locking compound on hex nut |
| Handle too narrow for screw holes to align | Use a washer on each side, or pack with folded electrical tape |
| Metal spoon bit wanders when drilling | Center-punch first; use low speed + cutting oil |
| Scoop too shallow for target objects | Switch to a ladle (deeper bowl) with the same mounting method |

### Implementation outline

1. Remove claw+motor assembly (2 screws, ~30 seconds)
2. Mark spoon handle against bracket holes
3. Drill two 11/64" holes (~2 minutes including setup)
4. Mount and tighten (~1 minute)
5. Test arm range-of-motion
6. Run a scooping trial with target object

Total time: **~5 minutes** (excluding trial run)

### Morphology change for the self-model

```json
{
  "end_effector": {
    "type": "passive_scoop",
    "material": "plastic_or_stainless",
    "source": "kitchen_utensil",
    "grip_force": null,
    "motor_required": false
  },
  "freed_motor": {
    "port": 3,
    "previously": "claw_motor"
  },
  "task_primitive_change": {
    "grab": "scoop_under + arm_lift (no spin_for)",
    "release": "arm_lower + drive_back"
  }
}
```

---

## Next Steps

- **To proceed:** physically remove the claw and mount the spoon (steps above — no code changes needed immediately).
- **To update the robot program:** remove or comment out the claw port initialization and any `spin_for()` calls on that port; add a note in the self-model JSON that `end_effector.type = passive_scoop`.
- **To file this as a task:** `/task-add Replace Clawbot claw with household-scoop end-effector and update self-model morphology JSON`
- **To ingest into the wiki:** `/wiki-ingest raw/research/clawbot-scoop-replacement/index.md`
