---
topic: "possible addition of https://www.vexrobotics.com/276-2232.html booster kit to this project in addition to the starter kit"
slug: vex-v5-booster-kit
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Adding the VEX Booster Kit (276-2232) to the Project

> The Booster Kit (276-2232, **$214.49**) is a ~600-piece bundle of **purely passive structural and motion parts** — steel channels/plates/angles/gussets, standoffs, shafts, bearings, ~600 fasteners, plus a few *new* functional part types: a **Gear Kit assortment, 19T rack gears, intake rollers, and motor clutches**. It contains **no brain, no motors, no sensors, no battery**. For this project — an LLM-authored self-model driving a *typed assembly grammar / morphology search* — the parts catalog **is** the search space, so the Booster Kit is a high-leverage, low-cost addition: it roughly triples the structural inventory and adds new typed primitives (linear motion via rack-and-pinion, intakes, slip clutches, long lever arms). **Recommendation: add it — but pair it with 2–4 additional V5 Smart Motors**, because actuation (still capped at the starter kit's 4 motors) — not structure — is the binding constraint on how complex a robot any generation can actually drive.

## Research Questions

1. What exactly is in the Booster Kit (276-2232), and what does it add beyond the V5 Classroom Starter Kit (276-7010)?
2. Is it compatible with the V5 platform this project standardized on for Stage 2?
3. How does it map onto the project's core mechanism — the typed assembly grammar and LLM-authored self-model (parts catalog = morphology search space)?
4. Which new *capability primitives* does it unlock for the grab/pull/throw task-telemetry contracts?
5. Is it the best marginal purchase, or are additional motors / specialty kits a better use of the same budget?

---

## Current State (Codebase)

This project is the **LLM-Authored Robot Self-Model / Physical-Robot Software Factory** capstone. Relevant existing knowledge:

- `wiki/knowledge/concepts/typed-assembly-grammar.md` + `llm-authored-self-model.md` — the system searches over **typed modules**, not free-form CAD; the **parts catalog defines the search space**, and gear ratios are capability parameters. [S3]
- `raw/research/vex-v5-classroom-starter-kit/index.md` — the Starter Kit (276-7010, $849.49) builds **one Clawbot** with **4 V5 Smart Motors** and a fixed steel-structure inventory. It already lists the **Booster Kit (276-2232) at $214.49** as a compatible related/upgrade product. [S1]
- `raw/research/vex-v5-customization-grab-pull-throw/index.md` — grab/pull are achievable on the base kit; throw release velocity = `ω × arm_length`; **"Linear Motion Kit (rack+slide)"** and gear-cartridge swaps are called out as the specialty add-ons that unlock precise linear pull and varied ratios; the kit is **capped at 4 motors** (more cost ~$52.99 each); Brain has **21 Smart Ports**, so actuation — not ports — is the limit. [S2]

So the project already treats the parts catalog as the lever, and already flagged exactly the kinds of parts (rack gears, more gears, longer shafts) that the Booster Kit happens to contain.

---

## Key Findings

### What the Booster Kit is [S4][S6]

- Marketed as VEX's **"Top Recommended Add-On Kit"** — "pieces specifically recommended by VEX builders to maximize versatility… Use the parts in the Booster Kit to build bigger and better robots."
- **Over 600 pieces**, all **structural + motion** components. **No electronics whatsoever** (no Brain, controller, radio, battery, motors, or sensors).
- Product page states it **"Works with VEX V5, VEX U, VEX AI."** [S4] The parts-list PDF is "VEX EDR" branded (©2018) — VEX's metal **structure subsystem is shared across EDR and V5**; only the control electronics differ, so the parts are cross-compatible with the V5 robots this project uses. *(see Constraints for the caveat)*

### Full itemized contents [S5]

**Steel structure**
| Part | SKU | Qty |
|---|---|---|
| 1×2×1×15 Steel C-Channel | 276-2232-028 | 2 |
| 1×2×1×25 Steel C-Channel | 276-2288 | 2 |
| 1×5×1×25 Steel C-Channel | 275-1138 | 2 |
| 5×5 Steel Plate | 276-2232-026 | 2 |
| 5×15 Steel Plate | 275-2023 | 2 |
| 5×25 Steel Plate | 275-1140 | 2 |
| 2×1×25 Steel Rail | 275-1145 | 4 |
| 1×1×25 Steel Bar | 275-1141 | 8 |
| 2×2×25 Steel Angle | 275-1142 | 2 |
| 1×1×25 Steel Slotted Angle | 276-2232-025 | 2 |
| 1×1×30 Steel Slotted Segmented Angle (R/L) | 276-2232-024 / -023 | 2 + 2 |
| Gusset Pack | 276-1110 | 2 |

**Motion / power-transmission (the functionally new types)**
| Part | SKU | Qty | Why it matters here |
|---|---|---|---|
| **Gear Kit (assortment)** | 276-2169 | 1 | Many gear sizes → expands the gear-ratio parameter space the grammar searches |
| **19T Rack Gear** | 276-1957 | 4 | Rack-and-pinion = **precise linear motion** (linear pull, slides, extenders) |
| **Intake Roller** | 276-1499 | 4 | Enables **intake/conveyor** grab mechanisms |
| **Motor Clutch** | 276-1098 | 3 | Slip/torque-limit element → overload protection + catapult-style release |
| 12.00" Shaft | 276-1149 | 4 | **Long lever arms** → higher throw release velocity & reach |
| 4.00" / 11mm / 2"&3" shafts | 276-2232-021 / 276-2177-021 / 276-2011 | 2 / 10 / 1 | More axles for multi-stage mechanisms |
| Flat Bearing / Pillow Block Bearing & Lock Bar | 276-1209 / 276-2016 | 26 / 1 | Support long shafts & big structures |
| Shaft Collars / Teflon & Steel Washers / Plastic Spacers | 276-2010 / 275-1025,275-1024 / 276-2018,276-2019 | 16 / 40 / 40 | Bulk shaft hardware for many builds |

**Fasteners (bulk — enough to build several robots)**
- Screws (#6-32 and #8-32, 1/4"–3/4"): 275-0659/1169/1002/1003/1004/1006 — **~160 total**
- #8-32 Keps Nut ×130, #8-32 Nylock Nut ×28
- Standoffs 0.5"/1"/2"/3" — 26 total; Bearing Attachment Rivet ×50

### Project fit: it expands the morphology search space [S2][S3]

The Self-Model factory's central lever is the **size and diversity of the typed parts catalog** — that *is* the space the LLM searches over. The Starter Kit gives exactly one robot's fixed inventory. The Booster Kit:

1. **Roughly triples generic structure** (channels, plates, rails, bars, gussets) + supplies ~600 fasteners → the factory can build **larger robots, taller towers, or several distinct morphologies in parallel** without running out of metal.
2. **Adds new typed primitives** the current catalog lacks — rack gears (linear-motion type), a gear assortment (more ratios), intake rollers (intake type), motor clutches (release/overload type), 12" shafts (long-arm type). Each is a **new node type the grammar can compose**, directly enriching grab/pull/throw envelopes the prior research defined.

### Capability primitives unlocked

| New part | New task-contract capability |
|---|---|
| 19T Rack Gear + Gear Kit | **Precise linear PULL / extension** (rack-and-pinion) — prior research flagged this as an add-on; now in-kit |
| Gear Kit assortment | More **gear ratios** → tunable arm torque/speed → richer THROW & lift parameter sweeps |
| 12" shafts | **Longer arm_length** → higher throw release velocity (`v = ω × arm_length`) |
| Intake Roller | **GRAB via intake/roller** mechanism (alternative to the single-sided claw) |
| Motor Clutch | **Slip-release** for energetic catapult THROW + overload protection of the 4 motors |

---

## Constraints

1. **No actuation added.** The Booster Kit is 100% passive. The robot is still **capped at the Starter Kit's 4 V5 Smart Motors**; structure is no longer the bottleneck, **motors are**. Additional V5 Smart Motors are ~$52.99 each. [S2][S4]
2. **EDR-branded parts list (©2018).** Parts are V5-structure-compatible (page says "Works with VEX V5"), but the **Motor Clutch (276-1098) and Intake Roller (276-1499) are legacy 3-wire/EDR-motor-era components** — the clutch mounts to the older 393-style motor interface, not the V5 Smart Motor shaft directly. Verify mounting before relying on those two specific parts with V5 motors. *(inference from EDR lineage — confirm on receipt)*
3. **Pieces are mostly fasteners/structure**, not "robots." "600 pieces" is dominated by ~290 screws+nuts; the headline count overstates capability gain. The real value is the *new part types* + bulk metal, not the raw count.
4. Price/availability ($214.49, In Stock) are as of **2026-06-16** and may change. [S1]
5. vexrobotics.com blocks direct HTTP fetch (403); product data here came from search snippets + the CDN parts-list PDF + the prior in-repo scrape. [S4][S5]

---

## Solution Comparison

| Criteria | A. Add Booster Kit | B. Add 2–4 Smart Motors | C. Add Linear/Advanced Mechanics specialty kit | D. Starter Kit only |
|---|---|---|---|---|
| **What it adds** | ~600 passive structure+motion parts, new part *types* | Actuation budget (5–8 motors) | Narrow: rack/slide or slip-gear | Nothing |
| **Cost** | $214.49 | ~$106–212 | ~$50–100 | $0 |
| **Pros** | Biggest expansion of the *morphology search space*; new typed primitives; build several/larger robots | Lifts the true bottleneck (4-motor cap); enables multi-actuator generations | Cheapest path to one specific primitive (linear pull) | No spend |
| **Cons** | Adds **no actuation**; 2 legacy parts need V5-mount check | Adds no structure/new geometry; still one robot's metal | Doesn't broaden general search space | Search space frozen at one Clawbot |
| **Complexity** | Low (drop-in catalog entries) | Low | Low | — |
| **Codebase fit** | **Excellent** — catalog = search space | Good — but pairs best *with* A | Partial | Baseline |

---

## Recommendation

**Add the Booster Kit (276-2232) — and pair it with 2–4 additional V5 Smart Motors.** Rationale:

- The Booster Kit is the single best **structural** purchase for a morphology-search factory: at $214.49 it triples generic build material and, more importantly, introduces **new typed primitives** (rack-and-pinion linear motion, a gear-ratio assortment, intake rollers, long lever-arm shafts, slip clutches) that each become composable nodes in the typed assembly grammar. This directly grows the LLM self-model's search space — the project's core lever.
- But structure alone is half the story. With actuation frozen at **4 motors**, every generation must reuse the same four actuators, which caps achievable robot complexity regardless of how much metal is available. Buying **2–4 more Smart Motors (~$106–212)** lifts that real bottleneck and lets the factory explore genuinely more capable morphologies.

**Implementation outline:**
1. Add all Booster Kit SKUs to the **typed parts catalog** (`vex_v5_catalog.json` per the grab/pull/throw next-steps) with physical specs (length, hole count, gear teeth, shaft diameter) so the grammar can compose them.
2. Define new typed primitives: `linear_actuator` (rack+pinion+motor), `intake` (roller pair), `long_arm` (12" shaft), `slip_release` (motor clutch).
3. Extend the grab/pull/throw telemetry contracts to cover the linear-pull and intake-grab variants.

**Risks & mitigations:**
- *Legacy-part mounting (clutch/intake roller with V5 motors)* → verify on receipt; treat as optional catalog entries, not core. (Constraint 2)
- *Overstated value from "600 pieces"* → model the catalog by part *type*, not count, so the search space reflects real morphological options.

**When a different option wins:** If the showcase only needs one fixed demo robot (no morphology diversity), skip the Booster Kit and buy a single specialty kit (Option C) or nothing (D). If budget is tight and the goal is *more capable* single robots rather than *more varied* ones, prioritize motors (B) first.

## Next Steps

- Run `/wiki-ingest raw/research/vex-v5-booster-kit/index.md` to synthesize this into the knowledge base.
- `/decision-create` — "Procure VEX Booster Kit (276-2232) + N additional V5 Smart Motors to expand the morphology search space" (trade-off: structure vs. actuation budget).
- `/task-add "Add Booster Kit SKUs as typed nodes to vex_v5_catalog.json with physical specs and new primitive types (linear_actuator, intake, long_arm, slip_release)"`.
- On receipt, verify Motor Clutch (276-1098) and Intake Roller (276-1499) mounting against V5 Smart Motors before relying on them.
