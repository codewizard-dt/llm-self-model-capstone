---
topic: "VEX V5 Classroom Starter Kit customization — can it complete grab/pull/throw, and how to quantify"
slug: vex-v5-customization-grab-pull-throw
researched: 2026-06-16
sources: [./sources.md]
---

# Research: VEX V5 Starter Kit — Customization, Grab/Pull/Throw Capability & Quantification

> The V5 Classroom Starter Kit is a **fully scalable platform**: every motor exposes live torque, current, velocity, and position telemetry over Python; the Brain has 21 Smart Ports for additional motors and sensors; and the kit can be extended with pneumatics, linear slides, flywheels, and specialist motion kits. **GRAB and PULL are achievable with the base Starter Kit alone.** THROW is achievable in a slow-catapult form with the base kit (rubber bands + arm motor already included); for fast throws (flywheel/puncher) add the 6:1 cartridge and additional parts. All three actions produce rich numeric telemetry that maps directly onto the self-model's capability layer and gap model.

---

## Research Questions

1. What hardware customization options exist within and beyond the Starter Kit?
2. What are the exact V5 Smart Motor specs that bound any physical task?
3. Can the kit physically achieve "grab", "pull", and "throw"?
4. What does each action's capability envelope look like (force, speed, range)?
5. How do we quantify each action in terms the LLM self-model can reason about and the gap model can correct?

---

## Current State (Codebase)

The wiki holds:
- `wiki/knowledge/entities/tools/vex-v5.md` — V5 platform overview, Classroom Starter Kit contents, kit family
- `wiki/knowledge/sources/vex-v5-clawbot-build-instructions.md` — confirmed 4-motor Clawbot config; arm at 7:1 gear reduction; claw at 12T; ports 1/6/10 (drive), 3 (claw), 8 (arm)
- `wiki/knowledge/concepts/typed-assembly-grammar.md` — Clawbot as grammar exemplar; gear ratios as capability parameters
- `wiki/knowledge/concepts/llm-authored-self-model.md` — the capability self-model layer derives specs from the parts catalog; the gap model measures prediction vs. telemetry

The Clawbot build (Gen 0) already has grab and pull primitives. The research here defines their capability envelopes and quantification API.

---

## Key Findings

### V5 Smart Motor 11W — The Actuation Primitive [S1][S2]

Every motor in the kit (and every additional motor you add) reports the same telemetry:

| Spec | Value |
|------|-------|
| Stall torque | **2.1 Nm** |
| Continuous operating point | ≤ 0.735 Nm (35% of stall) at full speed |
| Peak power | 12.75 W |
| Stall current limit | 2.5 A (hardware, prevents PTC trips) |
| Power accuracy | ±1% (consistent across battery levels) |
| Internal PID rate | 10 ms |

**Three swappable gear cartridges** [S3]:

| Cartridge | Output RPM | Relative torque | Use case |
|-----------|-----------|-----------------|---------|
| 6:1 | 600 RPM | Lowest | Flywheels, intakes |
| 18:1 (default) | 200 RPM | Medium | Drive, arms (standard) |
| 36:1 | 100 RPM | Highest | Heavy lifts, winches |

**Python telemetry API** (per motor, read at any time) [S4]:
```python
motor.torque(Nm)        # 0.0–2.1 Nm — active torque
motor.current(CurrentUnits.AMP)  # 0–2.5 A
motor.velocity(RPM)     # actual RPM
motor.position(DEGREES) # cumulative degrees (unbounded)
motor.power(PowerUnits.WATT)  # 0–12.75 W
motor.temperature(PERCENT)   # thermal headroom
motor.set_max_torque(50, PERCENT)  # soft torque cap
```

### Customization Tiers [S5][S6]

The kit is **explicitly described as scalable** — "you can add-on any components, additional motors, metal, aluminum and pneumatics."

| Tier | What changes | Capability unlocked |
|------|-------------|-------------------|
| **Base Starter Kit** (276-7010) | 4 motors, steel structure, 2 rubber bands, gears | Grab, slow-catapult throw, pull |
| **Gear cartridge swap** (+$12–20 each) | 6:1 or 36:1 cartridge | Faster flywheel OR higher torque arm |
| **Classroom Super Kit** (276-7011) | Adds motion kits, High Strength Sprockets & Chain, more structure | Tank treads, better lifts |
| **Specialty add-ons** | Linear Motion Kit (rack+slide), Winch and Pulley Kit, Advanced Mechanics Kit | Precise linear pull, slip-gear catapult release |
| **V5 Pneumatics Kit** (276-8750, 100 psi) | Solenoid + cylinders (2× and 4× pitch) | Fast single-shot throw, fast clamp |
| **Additional sensors** | AI Vision (AprilTags + object detection), Distance, Optical, GPS | Task verification, object detection, landing measurement |

Brain capacity: **21 Smart Ports** (motors + sensors share), 8 3-Wire ports (legacy sensors, solenoid driver). The 4-motor Clawbot uses ports 1, 3, 6, 8 — leaving 17 ports free.

---

## GRAB — Capability & Quantification [S7][S8]

**Mechanism (base kit):** The Clawbot claw uses a 12T gear driven by Motor 4 (port 3). Single-sided design: one finger moves, one is fixed. The claw closes until it contacts an object (motor stalls) or reaches the fully-closed position.

**Capability envelope:**
- Grip force = `claw_motor.torque() × gear_ratio / moment_arm`
  - At stall (2.1 Nm), with 12T gear driving a larger gear (say 1:1 on the claw): ≈ 2.1 Nm / 0.05 m moment arm = **~42 N clamping force**
  - Continuous: ~14.7 N
- Objects up to ~80–100 mm wide (claw opening angle converts to linear gap via geometry)
- Friction holding force = grip_force × µ (rubber tip on object)

**Quantification signals:**

| Signal | Python call | What it tells the self-model |
|--------|-------------|------------------------------|
| Object width proxy | `open_degrees − claw_motor.position()` | Physical size of gripped object |
| Grip firmness | `claw_motor.current()` at stall | How hard the claw is squeezing |
| Grip torque | `claw_motor.torque()` | Force applied (with moment arm → Newtons) |
| Grip binary | `claw_motor.velocity() < 5 AND claw_motor.current() > 1.5` | "Object gripped" boolean |
| Object present pre-grip | Distance Sensor or Optical Sensor | Confirm object is in claw zone before closing |

**Self-model claim example:**
> "My claw has a 50 mm jaw opening and can exert up to 14.7 N (continuous) grip force. Predicted: can grasp the 40 mm target sphere."

**Gap model:** After gripping, if `claw_motor.position()` didn't change (claw fully closed) → missed. If `current > 2.0 A` → full stall, over-squeezing. The residual = |predicted_grip_width − measured_grip_width|.

---

## PULL — Capability & Quantification [S2][S5]

**Mechanism (base kit):** Two drive motors (ports 1 & 6/10) on 4" wheels (radius = 50.8 mm), 18:1 cartridge (200 RPM). The robot drives forward dragging a tethered or resting load.

**Capability envelope:**
- Max theoretical pull force (both motors stalled): 2 × 2.1 Nm / 0.0508 m ≈ **82.7 N (18.6 lbf)**
- Continuous pull: 2 × 0.735 Nm / 0.0508 m ≈ **29 N (6.5 lbf)** 
- Winch variant (Winch & Pulley Kit add-on): force = motor.torque() / drum_radius — can exceed drive pull with smaller drum

**Quantification signals:**

| Signal | Python call | What it tells the self-model |
|--------|-------------|------------------------------|
| Pull force estimate | `(left.torque()+right.torque()) / 0.0508` | Estimated pull force in Newtons |
| Load ratio | `actual_velocity / set_velocity` | 1.0 = no load; <0.5 = heavy load |
| Energy per meter | `sum(motor.power()) × dt / distance` | J/m — efficiency of pull |
| Distance moved | `drivetrain.position()` | Meters pulled |
| Load current | `left.current() + right.current()` | Total amps under load |

**Self-model claim example:**
> "My 4" wheel differential drive can pull up to 29 N continuously. Predicted: can drag the 2 kg (19.6 N) load across the mat."

**Gap model:** If `velocity_drop_ratio < 0.3` → stalled; load exceeds capability. Self-model update: reduce predicted pullable mass.

---

## THROW — Capability & Quantification [S9][S10]

### Slow Catapult (Base Starter Kit — YES) [S9]

**Mechanism:** Arm motor (port 8, 7:1 gear reduction from 200 RPM → 28.6 RPM output shaft, or ~171°/sec) raises arm to max height then releases. Rubber bands (#32, included) add spring energy: pre-tension them against the arm; as arm swings forward their stored energy supplements the motor.

- Output shaft angular velocity: 200 RPM / 7 = 28.6 RPM = **3.0 rad/s**
- At arm length 150 mm: release velocity = 3.0 × 0.15 = **0.45 m/s** (motor only)
- With rubber band assist (2× #32): add ~10–15 N of pull over ~90° sweep → significant kinetic energy boost
- Suitable for: gentle underhand toss of lightweight objects (< 100 g) over short range (< 0.5 m)
- **Limitation**: Cannot produce a fast throw without a slip-gear release mechanism (not in Starter Kit)

### Fast Catapult / Slip-Gear (Advanced Mechanics Kit add-on)

Add the Drop-Off Cam or a slip gear — arm motor winds elastic bands to max tension, then cam releases suddenly. Release velocity can be 5–10× the motor-only value. *(inference — no primary source for exact numbers)*

### Flywheel Shooter (Gear Cartridge + Flywheel parts add-on)

Replace arm motor cartridge with 6:1 (600 RPM) and add an external gear train (e.g., 3:1) = ~1800 RPM at wheel. Flywheel Weight (sold separately) stores kinetic energy. Object passed between two contra-rotating wheels exits at high velocity.

- Typical VEX flywheel target: 35:1 total external ratio → ~21,000 RPM internal motor speed → flywheel rim speed ~10–15 m/s [S10]
- For Starter Kit geometry: single flywheel with 6:1 cartridge at 600 RPM + 84T:12T = 7:1 external = 4200 RPM at wheel
- Wheel circumference (4" = 0.3175 m) × 4200/60 = **22 m/s rim speed** → adequate for mid-range throw

**Throw quantification signals:**

| Signal | Python call / method | What it tells the self-model |
|--------|---------------------|------------------------------|
| Release angular velocity | `arm_motor.velocity()` at release time | ω (rad/s) |
| Release linear velocity (computed) | ω × arm_length | v₀ (m/s) |
| Theoretical range | `v₀² × sin(2θ) / 9.81` | Predicted distance (m) |
| Observed range | AI Vision Sensor / distance sensor | Actual distance (m) |
| Self-model error | `|theoretical − observed|` | Gap model residual (m) |
| Energy stored | `spring_constant × compression²/2` (rubber bands) | Potential energy in elastic (J) |
| Flywheel speed at release | `flywheel_motor.velocity()` | RPM → rim speed → launch velocity |

**Gap model for throw:**
> "Predicted range: 0.4 m. Observed: 0.25 m. Residual: −0.15 m. Likely cause: arm inertia losses exceed rubber band assist, or object mass higher than modeled. Update: increase rubber band count or gear down arm further."

---

## Constraints

1. **Starter Kit has 4 motors maximum** — all 4 are used on the Clawbot (2 drive, 1 arm, 1 claw). Adding more requires purchasing additional motors ($52.99 each).
2. **18:1 cartridge (200 RPM) is the only one included** — fast flywheel throw requires separate 6:1 cartridge purchase.
3. **No slip-gear in Starter Kit** — energetic catapult release needs the Advanced Mechanics and Motion Kit.
4. **No sensor beyond bumper switches in Starter Kit** — throw range measurement and object detection for grab require add-on sensors (AI Vision, Distance, Optical).
5. **Steel structure (heavier than aluminum)** — affects arm moment of inertia for throw calculations; aluminum would increase arm angular acceleration.
6. **Brain Smart Port limit: 21** — more than enough for the self-model's 4 current motors + 4–6 additional sensors.
7. **Clawbot claw** is single-sided — not ideal for grabbing irregularly shaped objects; competition-style double-sided claws require rebuilt hardware.

---

## Recommendation

**For the capstone self-model loop, define these three task primitives and their quantification contracts:**

### Grab Contract
```json
{
  "task": "grab",
  "predicted": {
    "object_width_mm": 40,
    "grip_force_N": 14.7,
    "success": true
  },
  "observed": {
    "claw_position_delta_deg": 120,
    "claw_current_A": 1.8,
    "claw_torque_Nm": 0.9,
    "gripped": true
  },
  "gap": { "force_error_N": -0.9, "width_error_mm": 5 }
}
```

### Pull Contract
```json
{
  "task": "pull",
  "predicted": { "load_mass_kg": 2.0, "distance_m": 0.5, "success": true },
  "observed": {
    "pull_force_N": 22.4,
    "velocity_ratio": 0.77,
    "distance_m": 0.5,
    "energy_J": 11.2
  },
  "gap": { "force_error_N": 6.6, "efficiency_loss": 0.23 }
}
```

### Throw Contract
```json
{
  "task": "throw",
  "predicted": { "range_m": 0.4, "object_mass_g": 50 },
  "observed": {
    "release_velocity_ms": 0.38,
    "observed_range_m": 0.25,
    "arm_velocity_at_release_RPM": 27.1
  },
  "gap": { "range_error_m": -0.15, "velocity_loss_ratio": 0.16 }
}
```

The **gap** fields in each contract are the residuals that feed the next generation's self-model revision. The LLM can read these in plain language: "I predicted a 0.4 m throw but observed 0.25 m — my arm is slower than expected due to inertia losses not in my model."

---

## Next Steps

- `/task-add "Define VEX V5 typed parts catalog JSON (vex_v5_catalog.json) with physical specs for all Clawbot parts"` — grounds the self-model
- `/task-add "Implement grab/pull/throw telemetry logging pipeline (Python VEXcode → JSON export → workstation)"` — the gap model data source
- `/decision-create` on whether to add the AI Vision Sensor + Distance Sensor for observed-range measurement in throw tasks
- Purchase: 6:1 gear cartridge (~$20) if fast throw is required for the showcase demo; otherwise rubber-band catapult is sufficient for the slow-throw demo
- Run `/wiki-ingest raw/research/vex-v5-customization-grab-pull-throw/index.md` to pull into knowledge base
