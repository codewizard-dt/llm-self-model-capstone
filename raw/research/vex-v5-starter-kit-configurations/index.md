---
topic: "VEX V5 Classroom Starter Kit — configurability beyond the Clawbot, possible shapes and designs"
slug: vex-v5-starter-kit-configurations
researched: 2026-06-16
sources: [./sources.md]
---

# Research: VEX V5 Classroom Starter Kit — Configuration Space

> The Classroom Starter Kit (276-7010) officially produces two base topologies: the **Speedbot** (drivetrain only, ~2 motors) and the **Clawbot** (Speedbot + arm + claw, 4 motors) — the Clawbot IS the Speedbot with the arm/claw added. The structural steel is precisely sized for the Clawbot with minimal surplus, making radically different shapes difficult without cutting or adding parts. That said, VEX explicitly encourages custom designs, and the motor allocation, chassis orientation, arm position, and end-effector can all vary within the kit. For the capstone, this small, enumerable design space is an **asset**: the LLM generator can exhaustively explore it in a handful of generations.

---

## Research Questions

1. What official builds does VEX document for the Classroom Starter Kit beyond the Clawbot?
2. What structural constraints (part counts, channel lengths) bound possible shapes?
3. What is the full configurational grammar — what can the motor allocation, drivetrain, arm, and end-effector be?
4. What explicitly cannot be built with the Starter Kit alone?
5. What does this design space mean for the LLM self-model loop?

---

## Current State (Codebase)

- `wiki/knowledge/entities/tools/vex-v5.md` — Gen 0 Clawbot section, motor ports, gear ratios, capability envelope
- `wiki/knowledge/sources/vex-v5-clawbot-build-instructions.md` — complete parts list with counts; arm at 7:1, claw at 12T
- `wiki/knowledge/concepts/typed-assembly-grammar.md` — Clawbot as exemplar; grammar = vocabulary (parts catalog) + rules (port counts, load limits)
- The typed grammar research (prior wiki pages) establishes that morphology search must happen over a restricted design language — the Starter Kit's small parts set is exactly that restriction.

---

## Key Findings

### Official Builds for the Classroom Starter Kit [S1][S2][S3]

VEX documents exactly **three named configurations** for the Classroom Starter Kit:

| Build | Motors | Structure | Description |
|-------|--------|-----------|-------------|
| **Speedbot** | 2 (drive) | Chassis only | Basic tank drivetrain; base for everything else |
| **TrainingBot** | 2 (drive) | Chassis only | Equivalent to Speedbot; official download from VEX build page |
| **Clawbot** | 4 (2 drive + 1 arm + 1 claw) | Chassis + arm + claw | The full kit; Speedbot extended with arm and claw assembly |

The STEM Labs Clawbot With Controller build explicitly states: **"Can be built with: VEX V5 Classroom Starter Kit"** and **"The VEX V5 Clawbot is an extension of the VEX Speedbot."** [S3]

The Speedbot/TrainingBot and the Clawbot are not two fundamentally different robots — they are the **same kit at two stages of assembly**. The Speedbot uses ~2 motors and a chassis; the Clawbot adds the arm and claw using the same steel parts plus the remaining 2 motors.

The **Advanced TrainingBot** (arm on TrainingBot chassis) requires a **Competition Starter or Super Kit**, not the Classroom Starter Kit. [S1]

### Structural Constraints — Why More Shapes Are Difficult [S4][S5]

The Starter Kit's steel inventory (from the Clawbot build instructions):

| Part | Count | Length/Size |
|------|-------|------------|
| C-Channel 1x2x1 | 2× | 15 holes |
| C-Channel 1x2x1 | 2× | 25 holes |
| U-Channel 2x2x2 | 3× | 20 holes |
| Angle 2x2x14×20 | 2× | 14×20 holes |

The Clawbot uses **all of these** in its build: U-channels form the main chassis rails, C-channels form the arm uprights and support plates, Angles form the chassis cross-members. After fully disassembling the Clawbot, the same pieces can be reassembled but there is **no structural surplus** for a fundamentally different multi-section design.

VEX's own documentation notes: **"custom-designed robots may require the structural parts to be cut and/or bent into custom pieces."** [S4] This confirms that out-of-Clawbot shapes need modifications.

### Configurational Grammar — What CAN Vary [S2][S4][S6]

Within the available parts, these **parameters are free variables** that define the design space:

**1. Motor allocation** (4 motors total, any assignment to ports 1–21):
- 2 drive + 1 arm + 1 claw (Clawbot default)
- 2 drive + 2 free (Speedbot; free motors could power a spinning intake or winch)
- 4 drive + 0 manipulator (maximum drive power; no arm or claw)
- 3 drive + 1 manipulator (H-drive chassis with one manipulator)
- 1 drive + 3 manipulator (stationary-ish base with complex arm; unusual)

**2. Gear cartridge** (per motor, swappable if you buy extras):
- 18:1 → 200 RPM (default, included)
- 36:1 → 100 RPM (high torque arm)
- 6:1 → 600 RPM (high-speed intake/flywheel)

**3. Drivetrain configuration**:
- **Tank drive** (default): 2 motors, one per side, rear-wheel
- **4-motor tank**: all 4 motors for drive (uses all motors, no manipulator)
- **Rear-wheel only vs. front-wheel only**: motor position changes turning radius
- **H-drive**: 2 drive + 1 perpendicular wheel motor → strafing capability (requires non-standard wheel mounting)

**4. Wheel assignment** (2 standard + 2 omni):
- Front omni + rear standard (Clawbot default): omni allows easy turning
- All standard: maximum traction, no easy lateral movement
- All omni: minimum traction, holonomic-friendly
- Mixed side-to-side: asymmetric traction (unusual)

**5. Arm position**:
- Front-facing (Clawbot default)
- Rear-facing (robot backs into objects)
- Side-mounted (lateral reach)
- Absent (Speedbot)

**6. Arm gear ratio** (using the 84T:12T gear pair):
- 7:1 (default, as in Clawbot): high torque, low speed
- 1:1 (direct drive): faster, lower torque
- 1:7 (reversed — high speed, very low torque): only sensible for spinning mechanisms

**7. End-effector**:
- Plastic claw assembly (as built): grasping
- No end-effector (arm tip free): pushing/lifting flat surfaces
- 84T gear as spinning roller (mount at arm tip): intake/conveyor (experimental)
- Rubber bands as a sling: catapult (requires redesigned arm pivot)

### What the Kit CANNOT Produce [S5][S6]

Without additional parts:

| Feature | Why Not Possible |
|---------|-----------------|
| Tank treads | Not in Starter Kit; requires Tank Tread Kit |
| Pneumatic actuator | Not in Starter Kit; requires V5 Pneumatics Kit |
| 4-bar parallel linkage arm | Not enough structural channels for both chassis + 4-bar arm |
| Cascading/scissor lift | Requires Linear Motion Kit (rack + slide) |
| Flywheel shooter | Needs 6:1 cartridge + flywheel weight (both add-ons) |
| Vision-based autonomy | No camera sensor in Starter Kit (only 2 bumper switches) |
| Holonomic X-drive | Needs 4 omni wheels + 45° mounting (kit has 2 omni, 2 standard) |
| Aluminum structure | Starter Kit is steel only; aluminum is lighter |

### The Design Space as a Typed Grammar [S7]

For the capstone's self-model loop, the full Starter Kit configuration space is:

```
Design = (
  drivetrain_topology ∈ {tank_2, tank_4, h_drive},
  drive_wheel_type ∈ {omni_front, standard_front, mixed},
  arm ∈ {none, front, rear, side},
  arm_gear_ratio ∈ {7:1, 1:1},
  end_effector ∈ {claw, none, roller, sling},
  motor_cartridge ∈ {100rpm, 200rpm, 600rpm}
)
```

This gives approximately **3 × 3 × 4 × 2 × 4 × 3 = 864 combinatorial slots** but with many physically invalid combinations (e.g., 4-motor drive + arm requires 5 motors). Valid configurations are far fewer — **roughly 15–30 meaningfully distinct builds** from the Starter Kit alone.

That small space is the **ideal Gen 1–5 exploration territory** for the LLM self-model loop. The generator can propose a mutation ("swap front standard wheels to omni for better turning"), the critic can evaluate it ("but you lose traction for the pull task"), and the gap model can confirm or refute it after physical execution — all within a tractably enumerable vocabulary.

### Key Insight: Speedbot is the Base Morphology, Clawbot is Its Extension [S3]

The VEX STEM Labs hierarchy is:
1. **Speedbot** → basic drive, bumper switch sensing, coding fundamentals
2. **Clawbot** = Speedbot + arm motor + claw motor + steel arm structure

This is exactly the **morphology graph** the LLM self-model would operate on: each generation adds or removes a node (motor, structural submodule, end-effector) from the previous generation's graph. The Clawbot-to-Speedbot transition (remove arm subsystem) and Speedbot-to-Clawbot transition (add arm subsystem) are the two simplest one-step mutations in the design graph.

---

## Constraints

1. **Steel channel inventory is tight** — the Clawbot uses almost every structural piece; fundamentally different shapes require either cutting existing metal or buying more parts
2. **Only 2 sensor types in the kit** (bumper switches): any configuration requiring visual feedback, distance sensing, or color detection needs add-on sensors
3. **4 motors is the limit** without buying more — any configuration using 4-drive removes all manipulator motors
4. **The plastic claw assembly is fixed** — it can be used or omitted but cannot be structurally modified
5. **18:1 cartridge only** (default 200 RPM) — higher-speed flywheel or higher-torque lift needs cartridge purchase

---

## Recommendation

**For the capstone Gen 0–5 loop, define the design space explicitly:**

```json
{
  "platform": "vex_v5_classroom_starter_kit",
  "vocabulary": {
    "motors": ["left_drive", "right_drive", "arm_lift", "end_effector"],
    "drivetrain_topologies": ["tank_2motor", "tank_4motor", "h_drive"],
    "arm_positions": ["front", "rear", "side", "absent"],
    "end_effectors": ["claw_grasper", "bare_arm", "roller_intake", "none"],
    "wheel_configs": ["front_omni_rear_standard", "all_standard", "all_omni"],
    "gear_ratios": {"arm": [1, 7], "claw": [1]}
  },
  "constraints": {
    "max_motors": 4,
    "max_smart_ports_used": 4,
    "steel_channels_available": {"C_15hole": 2, "C_25hole": 2, "U_20hole": 3, "angle_14x20": 2},
    "requires_cutting": false,
    "sensors_included": ["bumper_switch_x2"]
  }
}
```

**Implementation steps:**
1. Build Speedbot first (2-motor drive) → Gen 0: simplest valid grammar sentence
2. Gen 1: LLM proposes adding arm → builds Clawbot → runs grab/pull/throw tests → records gap
3. Gen 2: LLM proposes mutating wheel type (standard→omni front) → same arm → records turning improvement
4. Gen 3–5: LLM proposes arm position or gear ratio changes → tests task telemetry → refines self-model

**Risks:**
- The small design space means the loop converges fast (3–5 generations) — which is fine for a capstone demo but limits "wow factor" variety
- Mitigation: add-on Super Kit parts for Gens 6+ to expand the grammar

---

## Next Steps

- `/task-add "Define vex_v5_catalog.json with typed parts vocabulary and constraint block"` — the ground-truth grammar file
- `/task-add "Build Speedbot (Gen 0) and run baseline telemetry logging"` — first physical generation
- `/decision-create` on whether to start from Speedbot (simple) or Clawbot (richer but full kit) as Gen 0
- `/wiki-ingest raw/research/vex-v5-starter-kit-configurations/index.md` to add configuration space map to knowledge base
