# Architecture

A **Physical-Robot Software Factory** driven by LLM-authored self-models. Given a finite typed parts vocabulary (VEX V5 Classroom Starter Kit), an LLM iteratively authors and revises a structured, language-readable self-description of a physical robot — what it *is*, what it *can do*, and what it *predicts* will happen on a task. Real-world motor telemetry closes the loop: gap residuals (predicted vs. observed) correct the self-model each generation.

**Novelty claim**: No published work combines language-authored self-models + multi-LLM adversarial critique + reality correction via per-actuator telemetry in a single generational loop. Lipson proved numerical self-models work; RoboMorph used LLMs for design in simulation only; Hart & Scassellati built symbolic self-models pre-LLM. The unoccupied position is this system.

> **Requirements authority.** [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md) is the decision-closed source for scope, ownership, milestones, and verification. This document is the design narrative; where the two disagree, the requirements doc wins.

**Build strategy (software-first).** The MVP closes the loop in software: every telemetry and vision source sits behind a `TelemetrySource` / `VisionSource` adapter, so the same loop runs on recorded or synthetic data and expands to the full physical loop by swapping the adapter implementation — no contract change. Early milestones run on a parametric **synthetic oracle** — a hidden-ground-truth forward model whose true parameters are withheld from the Generator, so a tightening gap reflects the model actually converging on reality, not steering. The oracle is grounded by one real baseline capture once hardware is up. Code is organized into four verticals — `contracts`, `operator`, `coprocessor`, `brain` — with Python deps managed by `uv` and lint/format by `ruff`.

```
┌─────────────────────────────────────────────────────┐
│  OPERATOR (Claude Code — subscription)              │
│  ├─ Generator: reads JSONL → revises self-model     │
│  └─ Critic panel: parallel agents attack design     │
└──────────────────┬──────────────────────────────────┘
                   │ reads session_*.jsonl from Pi filesystem
                   │ writes revised self-model + build instructions
                   ▼
┌─────────────────────────────────────────────────────┐
│  Raspberry Pi 5  (coprocessor)                      │
│  ├─ vision_loop.py   — Camera + YOLO + AprilTags    │
│  └─ serial_bridge.py — V5 JSON → merged JSONL       │
└──────────────────────┬──────────────────────────────┘
                       │ USB serial  115,200 baud
                       ▼
┌─────────────────────────────────────────────────────┐
│  VEX V5 Brain                                       │
│  └─ 4× Smart Motors  — torque/current/vel/pos API   │
└─────────────────────────────────────────────────────┘
```

---

## Hardware Platform

### VEX V5 Brain

The deterministic motor-control layer. Runs `brain_main.py` (VEXcode Python) on a 20 ms tick, drives all four Smart Motors, and emits task telemetry as newline-delimited JSON to the USB user port.

- **Kit**: Classroom Starter Kit 276-7010 ($849)
- **Motors**: 4× V5 Smart Motor 11W — stall torque 2.1 Nm, continuous 0.735 Nm
- **Telemetry API** (per-motor, 20 ms loop): `torque()`, `current()`, `velocity()`, `position()`, `power()`
- **Sensors**: 2× Bumper Switch v2
- **Output**: newline-delimited JSON → USB serial, 115,200 baud

**Interface out**: JSON task-contract lines on `/dev/ttyACM0`. Format defined in [Telemetry Pipeline](#telemetry-pipeline).

### Raspberry Pi 5 Coprocessor

The data-collection layer. Runs two cooperating Python scripts: `vision_loop.py` (camera + ML) and `serial_bridge.py` (V5 ingest + JSONL storage). Pi 5 was chosen over Jetson Nano for 3× CPU advantage and USB-C power bank compatibility.

- **Camera**: Pi Camera Module 3, 12 MP, CSI 22-pin — 8–10 FPS YOLO, 30+ FPS blob/color
- **Vision**: YOLO11n NCNN INT8 for object detection; AprilTag (tag36h11) for robot pose `{x, y, heading}`
- **Power**: 10,000 mAh USB-C PD bank — ~3–5 W draw, 12–15 hr runtime
- **Weight**: ~280–350 g (board + case + camera + bank)

**Interface in**: JSON lines from `/dev/ttyACM0`. **Interface out**: `session_*.jsonl` on Pi filesystem — read directly by the operator's Claude Code session at analysis time.

---

## Robot Configuration

The typed assembly grammar — the bounded vocabulary the LLM searches over. Defining and maintaining this is its own owned work chunk: it is `parts_catalog.json`, and every other component reads from it.

**All options below are achievable with the Starter Kit (276-7010) alone:**

```json
{
  "motor_allocation": ["2drive+2free", "2drive+1arm+1claw", "4drive", "3drive+1manip"],
  "arm_position":     ["front", "rear", "side", "absent"],
  "end_effector":     ["claw_grasper", "bare_arm", "none"],
  "wheel_config":     ["front_omni+rear_standard"],
  "arm_gear_ratio":   ["7:1", "1:1"],
  "cartridge":        ["200rpm"]
}
```

Valid configurations: **~10–15** (96 raw slots; many mechanically invalid).

Generational ladder:

| Gen | Morphology | Key change |
|-----|-----------|------------|
| 0 | Speedbot | 2-motor drive only — baseline telemetry |
| 1 | Clawbot | Add arm + claw — grab/pull/throw tasks |
| 2–5 | Mutations | Arm position, gear ratio variants |

### Optional Hardware Expansions

Add-ons that extend the vocabulary without replacing the base kit. Each row is a deliberate purchasing decision — buy when the design loop reaches it, not upfront.

| Add-on | Cost | Vocabulary entry unlocked |
|--------|------|--------------------------|
| 36:1 cartridge (100 RPM) | ~$20 | `"cartridge": "100rpm"` — higher arm torque, heavier lifts |
| 6:1 cartridge (600 RPM) | ~$20 | `"cartridge": "600rpm"` — faster intake/flywheel mechanisms |
| 2× additional omni wheels | ~$15 | `"wheel_config": "all_omni"` |
| HS aluminum shafts | ~$10 | Longer arm reach, multi-stage linkages |
| 3D-printed end-effector | $3–5 | `"end_effector": "scoop_cup"` or other custom type — produces telemetry the claw cannot |

3D-printed parts are the highest-leverage expansion: a scoop-cup end-effector is a genuine new vocabulary entry, can be iterated cheaply per generation, and produces continuous-contact telemetry vs. the claw's discrete jaw-close signal.

---

## Telemetry Pipeline

The data contract between the V5 Brain and the operator's Claude Code session. Owning this means owning the JSON schema — everything else in the system reads or writes to it.

**Data flow:**
```
V5 Brain → emit contract JSON → USB serial → Pi serial_bridge.py
  → merge with vision state → append to session_*.jsonl
  → operator opens Claude Code session → reads JSONL → revises self-model
```

**Task Telemetry Contract** — three blocks per task execution:

| Block | Content |
|-------|---------|
| `predicted` | Self-model's forward-simulated expectation before execution |
| `observed` | Actual motor API readings during execution |
| `gap` | Signed residuals — the only signal Claude needs to revise the model |

Storage: JSONL — append-only, `flush()` per contract, fast on Pi SD card. The operator's Claude Code session reads the file directly at analysis time; no API polling or streaming required.

**Interface contract**: `session_YYYYMMDD_HHMMSS.jsonl` on Pi filesystem. V5 Brain writes to it (via Pi bridge); Claude Code reads it. Both sides must agree on the JSON field names.

---

## LLM Integration

All LLM work runs through Claude Code (subscription) — no API keys, no billing per call, no scripted HTTP. The operator opens a Claude Code session, points it at the JSONL on the Pi, and drives the generational loop interactively.

### Self-Model & Generator

One owned piece: the self-model JSON schema plus the Claude Code workflow (prompts, slash commands, context-loading) that produces and revises it. Schema and workflow are designed together — the schema dictates what Claude must emit.

The self-model has four layers in a single versioned JSON document:

| Layer | Content |
|-------|---------|
| **Structural** | Typed graph of parts and connections drawn from `parts_catalog.json` |
| **Capability** | Physical parameters derived from specs: reach, torque, max pull force, CoM |
| **Predictive** | Forward-simulated outcome for the goal task |
| **Gap model** | Signed residuals from real execution — drives next-generation revision |

The `reasoning` field is first-class: Claude explains *why* it made each structural choice and what gap evidence drove each parameter change. This is the human-readable audit trail across generations.

At analysis time the operator loads the latest `session_*.jsonl` into the Claude Code session and asks Claude to revise the self-model. Claude reads the file directly — no intermediary script required.

### Critic LLM Panel

A separate owned piece — different workflow, different prompts, different output format. Runs *before* the human build step, so design errors are caught before a physical assembly is wasted.

- Parallel Claude Code subagents, each assigned a single attack dimension: physics validity, torque budget, CoM stability, reach geometry
- Each critic returns `pass` / `flag` + rationale; operator reviews and incorporates before finalizing the BOM
- Stateless relative to execution — reads only the proposed self-model, not telemetry; testable against synthetic self-models without a physical robot

---

## Generational Loop

The orchestration that ties all other chunks together. Not independently ownable — it's the integration spec.

| Stage | Owner | Inputs | Outputs |
|-------|-------|--------|---------|
| 1. Design | Operator + Claude Code | `parts_catalog.json` + prior gap residuals | Self-model JSON vN |
| 2. Critique | Operator + Claude Code agents | Self-model vN | Pass / revise flags |
| 3. Build | Human | BOM + ordered build steps | Physical robot Gen N |
| 4. Execute | V5 + Pi (autonomous) | Robot + task description | `session_*.jsonl` |
| 5. Analyze | Operator + Claude Code | `session_*.jsonl` gap blocks | Revised self-model vN+1 |

**Minimum Viable Demo (June 29):** The loop closes in software first (synthetic oracle, then grounded by a real baseline capture); the live Gen-2 segment runs on hardware with a recorded fallback ready.
1. Gen 0 Clawbot — LLM authors self-model from specs; run grab, pull, and throw tasks; collect telemetry (synthetic oracle, then real capture)
2. Show gap JSON — LLM explains residuals in plain language, revises self-model
3. Repeat grab/pull/throw — self-model correction converges across rounds; the oracle's hidden parameter is recovered within tolerance
4. Gen 1 / Gen 2 novel configuration — LLM proposes a new morphology from the grammar; human builds; runs same task suite
5. Compare generations — gap residuals tighten; design hypothesis confirmed or refuted by data

---

## Aesthetic Vocabulary

A non-functional grammar extension giving the Generator LLM structured choices for **visual self-expression**. Separate from the functional grammar — aesthetic parameters don't affect motor commands or telemetry contracts. One owned piece.

The key insight: aesthetic choices can encode hypotheses and make them visible. "Wide side panels = testing mass distribution." "Forward antennae = prioritizing forward sensing." Generations become visually distinct without reading telemetry.

```json
{
  "body_panel":      { "material": ["corrugated_plastic", "craft_foam", "cardboard", "acrylic", "3d_print", "none"] },
  "surface_markings":{ "tape_pattern": ["none", "stripes", "chevron", "solid_block"] },
  "appendages":      { "type": ["none", "antennae", "swept_fins", "dorsal_ridge", "whiskers"] },
  "accent_lighting": { "type": ["none", "neopixel_strip", "neopixel_ring"],
                       "pattern": ["solid", "breathing", "chase", "generation_pulse"] }
}
```

All materials attach via existing VEX 0.5" square holes — velcro, zip ties, or screws. No drilling, no modification to metal. Budget: $0–25 per generation. NeoPixel on Pi 5 requires SPI method (GPIO 10) — standard PWM/DMA libraries are incompatible with Pi 5 hardware.

---

## Key Decisions

| Decision | Chosen | Why |
|----------|--------|-----|
| Coprocessor | Pi 5 over Jetson Nano | 3× faster CPU; USB-C power bank compatible; Jetson Nano EOL |
| Serial | USB 115,200 baud (Stage 1) | No extra hardware; proven; upgradeable to RS-485 Smart Port (Stage 2) without protocol change |
| Storage | JSONL over SQLite | Faster Pi SD writes; native Anthropic Batch API input format |
| Assembly | Human-in-the-loop | Full autonomy is low-feasibility at capstone scale; human is a formal manufacturing station, not ad-hoc |
| Localization | AprilTags over odometry | Wheel slip + snap-fit tolerances make pure odometry unreliable at this scale |
| Design space | Starter Kit only (~10–15 configs) | Small enough to exhaust in 3–5 gens; large enough to show real mutations |
| Build strategy | Software-first behind `TelemetrySource`/`VisionSource` adapters | Demoable loop in 4 days; full physical loop is a drop-in adapter swap, no contract change |
| Synthetic telemetry | Parametric hidden-ground-truth oracle | Honest gap — the LLM recovers parameters it never sees; not hand-authored, not a physics sim |
| Tooling | `uv` (deps) + `ruff` (lint/format); Python all verticals | One fast, lockfile-reproducible toolchain; replaces pip/poetry/black/isort/flake8 |

> Full decision log (ADR-01 … ADR-18) with rationale and rejected options: [MASTER_REQUIREMENTS.md → Closed Decisions](MASTER_REQUIREMENTS.md).
