---
topic: "https://www.vexrobotics.com/go and VEX GO Competition Kit in particular how is VEX GO comparable to VEX V5 and would it be a potential stand in for this experiment?"
slug: vex-go-vs-vex-v5
researched: 2026-06-16
sources: [./sources.md]
---

# Research: VEX GO vs VEX V5 — Can GO Close the Telemetry Gap?

> **VEX GO cannot serve as a stand-in for VEX V5 in this experiment, but the gap is narrower than with consumer kits like REX/Tamiya/Thames & Kosmos — and the reason matters.** VEX GO motors DO have encoders (position in degrees ✓, velocity ✓, current ✓), so they can partially populate the Task Telemetry Contract. However: (1) the readings are in **relative percentage units**, not physical units (Nm, A, RPM, W), so the LLM self-model cannot reason in force/torque without an external calibration layer; (2) **no torque, power, or temperature readings** exist at all; (3) the GO Competition Kit is a **field arena kit** — tiles and walls — not a robot kit (robot not included); (4) the GO Brain has only 4 Smart Ports vs V5's 21; (5) GO's plastic snap-together structure is far lower load capacity than V5's steel; and (6) GO targets grades 3–5 (ages 7–11) with a Scratch/Python beginner API, not the physical-unit telemetry API that the self-model loop requires. **VEX IQ (2nd gen) is actually a closer practical alternative** — same VEX ecosystem, 12 Smart Ports, current in Amps, but still lacking V5's torque/power/temperature readings and physical scale. Neither GO nor IQ displaces V5 for this project.

---

## Research Questions

1. What is VEX GO (hardware, MCU, motors, sensors, structure, ports)?
2. What is the VEX GO Competition Kit specifically — and is it a robot kit?
3. Do VEX GO motors have telemetry that can populate the Task Telemetry Contract (torque/current/velocity/position in physical units)?
4. Can VEX GO close the telemetry gap that disqualified REX/Tamiya/Thames & Kosmos?
5. Is VEX GO or any VEX sub-platform a viable cost-saving stand-in for VEX V5?

---

## Current State (Codebase)

Directly relevant prior research in this session:

- `raw/research/vex-v5-customization-grab-pull-throw/index.md` — the Task Telemetry Contract requires `motor.torque(Nm)`, `motor.current(AMP)`, `motor.velocity(RPM)`, `motor.position(DEGREES)`, `motor.power(WATT)`, `motor.temperature(PERCENT)` — all in calibrated physical units
- `raw/research/picobricks-rex-vs-vex-v5/index.md` — disqualified REX/Tamiya/Thames & Kosmos because they have no motor encoders; VEX GO is a step above (encoders exist) but still has unit-calibration and completeness gaps
- `wiki/knowledge/concepts/task-telemetry-contract.md` — `observed.claw_torque_Nm`, `observed.pull_force_N`, `observed.release_velocity_ms` are specific fields requiring calibrated physical values

---

## Key Findings

### What VEX GO Actually Is [S1][S2][S3]

| Field | Value |
|---|---|
| Target grade/age | Grades 3–5 (ages 7–11) |
| Structure | Plastic snap-together (not steel, not metal) |
| Brain ports | **4 Smart Ports** (motors/sensors shared); 1 Eye Sensor port; 1 Battery port |
| Motors in kit | 3 motors |
| Sensors in kit | 1 Eye Sensor (color/object/brightness), 1 LED Bumper, 3 Electromagnets |
| Programming | VEXcode GO: Blocks + Python (NOT C++; NOT VS Code extension) |
| Price | ~$299 (Education Kit with storage, SKU 269-6705) |

**VEX GO is VEX's elementary-school platform** — the step BELOW VEX IQ, which is itself two steps below V5. The VEX product ladder, from youngest to most advanced: VEX 123 → VEX GO → VEX IQ → VEX EXP → **VEX V5**.

### What the VEX GO Competition Kit Actually Is [S4][S5]

**Critical clarification**: The VEX GO Competition Kit (SKU 269-8115) is a **FIELD KIT** — tiles, walls, and game objects for setting up a competition arena. It is explicitly stated: **"Robot not included. Teams will also need a VEX GO Education Kit or Bundle to compete."** It contains no brain, no motors, no sensors. It is not a robot building kit.

### VEX GO Motor Telemetry — Partial but Inadequate [S6][S7]

VEX GO motors DO have encoders. This is the key difference from REX/Tamiya/Thames & Kosmos. The VEX GO Blocks and Python API exposes:

| Signal | Available? | Units | V5 equivalent |
|---|---|---|---|
| `motor position` | ✓ | degrees or turns | `motor.position(DEGREES)` — ✓ same |
| `motor velocity` | ✓ | **percentage (%)** only | `motor.velocity(RPM)` — ✗ different |
| `motor current` | ✓ | **percentage (%)** only | `motor.current(AMP)` — ✗ different |
| `motor torque` | **NOT readable** | — | `motor.torque(Nm)` — ✗ missing |
| `motor power` | **NOT readable** | — | `motor.power(WATT)` — ✗ missing |
| `motor temperature` | **NOT readable** | — | `motor.temperature(PERCENT)` — ✗ missing |

**The unit problem**: V5's API returns physical units (`AMP`, `Nm`, `RPM`, `WATT`) that the LLM can reason about directly: "I predicted 14.7 N grip force; I observed 12.1 N." GO returns percentages that are internally normalized but not calibrated to physical units — without a separate calibration measurement, you cannot convert 47% current to Newtons of grip force.

**The completeness problem**: Even if you calibrated GO's current% to approximate Amps, you still have no torque reading (which the grab contract uses as the primary force signal) and no power or temperature readings (which the self-model uses to detect overload and thermal headroom).

**What GO CAN do**: Position contracts. If your task primitive is "move arm to 90°" and verify it arrived, GO can do that. But "grip with 14.7 N force and measure the residual" is not achievable without calibration and only partially achievable with it.

### Telemetry Gap: GO vs V5 vs Disqualified Kits [S6][S7][S8]

| Platform | Encoders | Position (physical) | Velocity (physical) | Current (Amps) | Torque (Nm) | Power (W) | Temp | Verdict |
|---|---|---|---|---|---|---|---|---|
| REX / Tamiya / T&K | **None** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Disqualified |
| **VEX GO** | ✓ | ✓ (degrees) | **% only** | **% only** | ✗ | ✗ | ✗ | Partial — unusable for force contracts |
| **VEX IQ (2nd gen)** | ✓ | ✓ (degrees, ±0.375°) | ✓ (RPM) | ✓ (0–1.2 A) | computed | ✗ | ✗ | Closer — but lower power, weaker physical scale |
| **VEX V5** | ✓ | ✓ (degrees, **±0.02°**) | ✓ (RPM) | ✓ (0–2.5 A) | ✓ (0–2.1 Nm) | ✓ (0–12.75 W) | ✓ | **Fully populated** |

VEX IQ (2nd gen) Smart Motors are worth noting: they have a TI MSP430 MCU, quadrature encoder (0.375°), current sensing in Amps (0–1.2 A), speed in RPM, and internal PID. They can fill the `observed.current_A` and `observed.velocity_RPM` fields. They still lack dedicated torque and power readings. And their physical scale is much smaller (designed for plastic IQ robots, not steel V5 mechanisms). [S9]

### Structural & Configuration Differences [S1][S2][S3]

| Dimension | VEX GO | VEX V5 |
|---|---|---|
| Structure | Plastic snap-together | Steel modular (SKU'd, scalable) |
| Smart Ports | **4** | **21** |
| Motors (base kit) | 3 | 4 (Starter Kit) |
| Max motors possible | 4 (brain limit) | 21 (port limit) |
| Typed grammar vocabulary | Small plastic fixed set | Extensible steel catalog + Booster Kit |
| Programming | Blocks + Python (no C++, no VS Code extension) | Blocks + Python + C++ + VS Code extension |
| VS Code extension supported | **No** | **Yes** |
| Competition ecosystem | VGRC (elementary level) | VRC (high school, worldwide, 15+ years) |

---

## Constraints

1. **Physical-unit telemetry is required** — the LLM self-model reasons in physical terms (Nm, A, RPM, W) to produce force/energy estimates the gap model can correct. Percentage units require a calibration step that introduces error and is not part of the self-model loop design.
2. **Torque reading is the grip-force signal** — the grab contract's key observable is `claw_motor.torque(Nm)`. VEX GO does not expose this at all.
3. **4 ports is prohibitive** — 3 motors + 1 sensor fill all 4 ports; there's no room for additional sensors (AI Vision, Distance) needed to observe throw range. V5 has 17 free ports after the Clawbot's 4.
4. **The VEX GO Competition Kit is not a robot** — if someone bought it thinking it was the robot platform, the clarification is important: it's a playing-field arena.
5. **All prior VEX V5 research is non-portable to GO** — the Clawbot morphology, port maps, gear ratios, and calibrated telemetry contracts are V5-specific.

---

## Recommendation

**Do not replace VEX V5 with VEX GO.** VEX GO is two full platform tiers below V5 and designed for 8-year-olds. The Competition Kit is not a robot. The motor telemetry exists but is in relative units only, the torque reading is absent entirely, and the 4-port brain is immediately exhausted by the most basic robot.

**If budget is the primary pressure**, the hierarchy of viable alternatives within the VEX ecosystem is:

1. **VEX V5** (recommended, ~$849.49 Starter Kit) — fully closes the telemetry gap
2. **VEX IQ 2nd gen** (fallback, ~$350–450 Education Kit) — IQ Smart Motors have current in Amps + velocity in RPM + position in degrees (±0.375°); closer to V5 than GO; still lacks dedicated torque readout and physical scale; and all prior research would need to be redone for the IQ platform
3. **VEX EXP** (middle ground, ~$499 Starter Kit) — uses the same 5.5W Smart Motor variant as V5's smaller motor; VS Code + Python supported; 8 Smart Ports; steel structure; a real option if price is the blocker
4. **VEX GO** — not viable for this project

**VEX EXP** deserves a separate research note: it uses the V5/EXP 5.5W Smart Motor (same Cortex M0, same PID, same telemetry API — torque, current, velocity, position, power, temperature — just lower peak power: 0.5 Nm stall vs V5's 2.1 Nm). It supports Python and C++ via VS Code. It has 8 Smart Ports and uses steel structure (not plastic). Its price is between GO and V5. It may be worth a separate `/research` if budget is a genuine constraint.

**Risks of GO:**
- Position contract only → much weaker self-model evidence
- Cannot verify grip force (no torque reading)
- 4-port limit blocks sensor additions
- All prior research must be discarded

## Next Steps

- Run `/wiki-ingest raw/research/vex-go-vs-vex-v5/index.md` to synthesize into the knowledge base.
- If budget is a hard constraint: `/research VEX EXP as a middle-ground alternative to VEX V5` — EXP uses the same motor telemetry API at lower cost and power.
- If not: continue VEX V5 roadmap; this research confirms V5 as the only option that fully closes the telemetry gap without calibration workarounds.
- `/decision-create "Stage-2 hardware platform final selection"` using the tier table (GO → IQ 2nd gen → EXP → V5) with the telemetry gap as the decision criterion.
