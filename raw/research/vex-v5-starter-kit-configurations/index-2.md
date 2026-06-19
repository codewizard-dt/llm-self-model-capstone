---
topic: "VEX V5 Classroom Starter Kit — configuration spec audit: remove all booster-kit-only vocabulary entries"
slug: vex-v5-starter-kit-configurations
researched: 2026-06-17
sources: [./sources-2.md]
prior: [./index.md]
---

# Research: VEX V5 Starter Kit Config Spec Audit (Starter-Kit-Only Corrections)

> Builds on [index.md](index.md); this update covers only the three fields in the configuration vocabulary that contain options NOT achievable with the Classroom Starter Kit (276-7010) alone. Three removals are required: `cartridge` loses "100rpm" and "600rpm"; `wheel_config` loses "all_standard" and "all_omni"; `end_effector` loses "roller". All other fields are unchanged from the prior report. The corrected spec is at the bottom.

## Research Questions

1. Which cartridge options are physically present in the Starter Kit (276-7010)?
2. How many omni wheels and standard wheels does the kit include — and does that support "all_standard" or "all_omni" wheel configs?
3. Is the "roller" end-effector achievable with Starter Kit parts alone, or does it require the Booster Kit (276-2232)?
4. Are `motor_allocation`, `arm_position`, and `arm_gear_ratio` fully achievable with Starter Kit parts only?

---

## Findings by Field

### `cartridge` — REMOVE "100rpm" and "600rpm"

**Prior spec:** `["100rpm", "200rpm", "600rpm"]`

Every V5 Smart Motor ships with the **18:1 (200 RPM) green-cap cartridge installed**. The 36:1 (100 RPM, red cap) and 6:1 (600 RPM, blue cap) cartridges are sold separately — they are **not included** in the Classroom Starter Kit (276-7010). [S1][S2]

The Starter Kit BOM lists "(4) V5 Smart Motors" with no accompanying separate cartridge packs. The prior configurations research itself flags this in its Constraints section: *"18:1 cartridge only (default 200 RPM) — higher-speed flywheel or higher-torque lift needs cartridge purchase."* [S3]

**Corrected field:** `["200rpm"]`

---

### `wheel_config` — REMOVE "all_standard" and "all_omni"

**Prior spec:** `["front_omni+rear_standard", "all_standard", "all_omni"]`

The Starter Kit BOM contains exactly **(2) 4" Omni Wheels** and **(2) 4" Wheels** (standard/traction) — four wheels in total, two of each type. [S3]

A four-wheeled ground robot uses all four wheels. With only two wheels of each type:

- **"all_standard"** requires 4 standard wheels → impossible (only 2 in kit)
- **"all_omni"** requires 4 omni wheels → impossible (only 2 in kit)
- **"front_omni+rear_standard"** uses exactly 2 omni (front) + 2 standard (rear) → valid ✅

A fifth option, "front_standard+rear_omni" (reversed), is also physically achievable with the same two-of-each inventory, but it was not in the prior spec. Both are valid; the reversed placement is unusual and not used in any official VEX build for this kit.

> **Note:** The raw research in index.md listed "all_standard" and "all_omni" without catching that the 2+2 wheel inventory makes them impossible. This is a correction, not a new finding.

**Corrected field:** `["front_omni+rear_standard"]`

*(If the reversed placement matters for the self-model loop, add "front_standard+rear_omni" as a second valid entry — both use the same kit parts.)*

---

### `end_effector` — REMOVE "roller"

**Prior spec:** `["claw_grasper", "bare_arm", "roller", "none"]`

The term "roller" (also written "roller_intake" in some wiki pages) maps to the **Intake Roller (276-1499)**, which is a **Booster Kit (276-2232) part**, not a Starter Kit part. [S4]

The Starter Kit does include a **84T High Strength Spur Gear**, and the raw grab/pull/throw research noted in passing that this gear *could* be mounted at the arm tip as an improvised spinning mechanism ("84T gear as spinning roller (mount at arm tip): intake/conveyor (experimental)"). However:

1. This is explicitly labeled "experimental" in that report — it is not a documented build.
2. The 84T gear is designed as an arm-lift gear train component, not an intake surface.
3. The dedicated `roller`/`intake` primitive the grammar vocabulary intends is the Booster Kit roller — a completely different part.

Removing "roller" from the Starter-Kit-only spec is the correct call. If/when the Booster Kit is added, "roller_intake" can be reinstated.

**Corrected field:** `["claw_grasper", "bare_arm", "none"]`

---

### `motor_allocation`, `arm_position`, `arm_gear_ratio` — NO CHANGES

All options in these three fields are achievable with Starter Kit parts only:

| Field | Options | Starter-kit basis |
|---|---|---|
| `motor_allocation` | "2drive+2free", "2drive+1arm+1claw", "4drive", "3drive+1manip" | 4 Smart Motors in kit; all allocations use ≤4 motors |
| `arm_position` | "front", "rear", "side", "absent" | Steel U/C-channels support all four mounting positions; "absent" = Speedbot |
| `arm_gear_ratio` | "7:1", "1:1" | 12T metal pinion + 84T spur gear both in kit; 7:1 = meshed; 1:1 = direct drive bypassing the gear train |

> **`3drive+1manip` note:** H-drive (3 drive motors = left, right, strafe + 1 manipulator motor) requires a perpendicular center wheel, which demands non-standard chassis construction. It is mechanically possible with starter kit parts but is not documented in any official VEX build. Flag as "non-standard, possible" rather than removing it.

---

## Corrected Configuration Spec (Starter Kit Only)

```json
{
  "platform": "vex_v5_classroom_starter_kit_276-7010",
  "vocabulary": {
    "motor_allocation": ["2drive+2free", "2drive+1arm+1claw", "4drive", "3drive+1manip"],
    "arm_position":     ["front", "rear", "side", "absent"],
    "end_effector":     ["claw_grasper", "bare_arm", "none"],
    "wheel_config":     ["front_omni+rear_standard"],
    "arm_gear_ratio":   ["7:1", "1:1"],
    "cartridge":        ["200rpm"]
  },
  "constraints": {
    "max_motors": 4,
    "wheels": {"omni_4in": 2, "standard_4in": 2},
    "cartridge_installed": "18:1_200rpm",
    "end_effectors_in_kit": ["V5_claw_assembly"],
    "sensors_included": ["bumper_switch_x2"],
    "steel_channels": {"C_15hole": 2, "C_25hole": 2, "U_20hole": 3, "angle_14x20": 2}
  },
  "removed_from_prior_spec": {
    "cartridge": ["100rpm", "600rpm"],
    "wheel_config": ["all_standard", "all_omni"],
    "end_effector": ["roller"]
  }
}
```

### Combinatorial impact of corrections

| Field | Prior count | Corrected count |
|---|---|---|
| `motor_allocation` | 4 | 4 |
| `arm_position` | 4 | 4 |
| `end_effector` | 4 | 3 |
| `wheel_config` | 3 | 1 |
| `arm_gear_ratio` | 2 | 2 |
| `cartridge` | 3 | 1 |
| **Raw combinatorial slots** | **4×4×4×3×2×3 = 1,152** | **4×4×3×1×2×1 = 96** |

The corrected slot count of 96 (vs. 1,152 prior) reflects the actual physical reality: `wheel_config` and `cartridge` each collapse to a single valid value, removing the false impression that all three wheel layouts and all three cartridges were switchable without additional purchases.

After validity filtering (e.g., 3drive+1manip has limited arm+claw options; arm must be absent when allocation is 4drive), the realistic meaningful-configuration count is roughly **10–15**, consistent with the capstone's planned 3–5 generation loop.

---

## Constraints

- The prior research (index.md) contained factual errors in `wheel_config` (listed impossible all-omni / all-standard configs) and `cartridge` (listed cartridges not included in the kit). This report corrects those errors.
- `end_effector: "roller"` is removed because the dedicated roller part (276-1499) is a Booster Kit component; the 84T improvised roller is too experimental to count as a formal vocabulary entry.
- No other fields in the prior spec require correction.

---

## Next Steps

- Update `wiki/knowledge/sources/vex-v5-starter-kit-configurations.md` to replace the vocabulary block with the corrected spec above.
- Run `/wiki-ingest raw/research/vex-v5-starter-kit-configurations/index-2.md` to push the correction into the knowledge base.
- If the Booster Kit (276-2232) is procured, reinstate `"roller_intake"` in `end_effector` and add `"36:1_100rpm"` / `"6:1_600rpm"` cartridge options in a third research pass.
