---
id: clawbot-scoop-replacement
title: "Research: Clawbot Claw → Household Scoop Replacement"
aliases: [Clawbot Scoop, Passive Scoop End-Effector, Claw Swap]
updated: 2026-06-22
sources:
  - ../../raw/research/clawbot-scoop-replacement/index.md
  - ../../raw/research/clawbot-scoop-replacement/sources.md
tags: [source, vex-v5, hardware, end-effector, morphology, clawbot]
---

# Research: Clawbot Claw → Household Scoop Replacement

The **entire claw + claw-motor assembly** on the VEX V5 Clawbot detaches with just two #8-32 screws (visible on the right bracket face of the arm tip). Removing them leaves two parallel C-channel bracket faces **1" (25.4 mm) apart**, each with a hole on the standard **0.500" grid** — a clean mounting interface for any thin-handled household scoop.

relates_to::[[vex-v5-clawbot-build-instructions]]
relates_to::[[typed-assembly-grammar]]
relates_to::[[vex-v5-cad-designs]]
derives_from::[[task-telemetry-contract]]

---

## Mounting Interface

- **Inner bracket gap:** 1" (25.4 mm) — max replacement width at mount point: ~22 mm
- **Screw pattern:** two #8-32 holes, 0.500" center-to-center (vertical stack)
- **Clearance drill for #8-32:** 11/64" = 4.5 mm
- All original screws and hex nuts are reused; no new hardware needed

---

## Candidate Items (ranked)

| Item | Handle width | Drilling | Rigidity | Rating |
|------|-------------|----------|----------|--------|
| Plastic serving spoon | 10–15 mm | Easy (any bit) | ★★★★ | ★★★★★ |
| Stainless serving spoon | 10–15 mm | Medium (HSS + oil) | ★★★★★ | ★★★★ |
| Plastic powder/coffee scoop | 8–12 mm | Easy | ★★★ | ★★★★ |
| Zip-tie clamp (any item) | any | None | ★★ | ★★★ |

**Recommended:** plastic kitchen serving spoon, drilled method — ~5 minutes, zero new parts.

---

## Build Procedure (drill method)

1. Unscrew the two circled #8-32 screws; set aside claw, motor, rubber bands.
2. Hold spoon handle against bracket face; mark through the two holes.
3. Drill two holes (≥ 4.5 mm) through the flat handle mid-section.
4. Slide handle into the 1" bracket gap; align holes; re-insert original screws + hex nuts.
5. Orient bowl forward/slightly up; tighten.

No-drill fallback: heavy-duty zip ties (≥ 4.8 mm) bound around handle + bracket face. Check tightness before each session.

---

## Morphology Impact

Replacing the claw with a passive scoop is a first-class **morphology mutation** in the typed assembly grammar:

```json
{
  "end_effector": {
    "type": "passive_scoop",
    "material": "plastic_or_stainless",
    "source": "kitchen_utensil",
    "grip_force": null,
    "motor_required": false
  },
  "freed_motor": { "port": 3, "previously": "claw_motor" },
  "task_primitive_change": {
    "grab": "scoop_under + arm_lift",
    "release": "arm_lower + drive_back"
  }
}
```

**Self-model consequence:** The LLM self-model should note "I have no grip force; I can only scoop objects I can slide under." The freed Smart Motor port becomes a new variable for future generations. The `spin_for()` call on the claw port should be removed from the brain program.

The Task Telemetry Contract `grab` primitive changes: instead of `set_max_torque + spin_for(degrees)`, the grab action is an arm-lift + approach sequence with no claw actuation.
