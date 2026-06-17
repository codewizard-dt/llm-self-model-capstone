# Architecture

A **Physical-Robot Software Factory** driven by LLM-authored self-models. Given a finite typed parts vocabulary (VEX V5 Classroom Starter Kit), an LLM iteratively authors and revises a structured, language-readable self-description of a physical robot — what it *is*, what it *can do*, and what it *predicts* will happen on a task. Real-world motor telemetry closes the loop: gap residuals (predicted vs. observed) correct the self-model each generation.

**Novelty claim**: No published work combines language-authored self-models + multi-LLM adversarial critique + reality correction via per-actuator telemetry in a single generational loop. Lipson (2006–2019) proved numerical self-models work; RoboMorph (2024) used LLMs for design in simulation only; Hart & Scassellati (2017) built symbolic self-models pre-LLM. The unoccupied position is this system.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  CLOUD                                                           │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐   │
│  │  Generator LLM          │  │  Critic LLM Panel           │   │
│  │  (Claude API)           │  │  (Claude API, parallel)     │   │
│  │  - authors self-model   │  │  - attacks physics/load/    │   │
│  │  - revises from gaps    │  │    reach/CoM pre-build      │   │
│  └───────────┬─────────────┘  └──────────────┬──────────────┘   │
└──────────────┼───────────────────────────────┼──────────────────┘
               │ HTTPS JSON                    │ HTTPS JSON
               │ (Mode A: 1–4s)                │
               ▼                               │
┌──────────────────────────────────────────────┼──────────────────┐
│  Raspberry Pi 5  (coprocessor)               │                  │
│                                              │                  │
│  vision_loop.py                              │                  │
│  ├─ Pi Camera Module 3 (CSI)                 │                  │
│  ├─ YOLO11n NCNN  (8–10 FPS)                │                  │
│  └─ AprilTag detect → {x, y, heading}        │                  │
│                                              │                  │
│  serial_bridge.py                            │                  │
│  ├─ read V5 JSON from /dev/ttyACM0           │                  │
│  ├─ merge with vision state                  │                  │
│  └─ append → session_YYYYMMDD_HHMMSS.jsonl   │                  │
│                                              │                  │
│  llm_loop.py ────────────────────────────────┘                  │
│  ├─ read latest contract from JSONL                              │
│  ├─ call Claude API → revised self-model                         │
│  └─ write next command → /dev/ttyACM0                           │
│                                                                  │
│  Power: 10,000 mAh USB-C PD bank  (~3–5 W load, 12–15 hr)      │
└──────────────────────────────┬───────────────────────────────────┘
                               │ USB serial  115,200 baud
                               │ microUSB ←→ V5 user port
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  VEX V5 Brain                                                    │
│  ├─ Motor control loop (20 ms tick, inner hardware PID)          │
│  ├─ 4× Smart Motors — torque/current/velocity/position API       │
│  ├─ Gyro, bumper switches, distance sensor                       │
│  └─ VEXcode Python runtime → sys.stdout JSON → user port         │
└──────────────────────────────────────────────────────────────────┘
```

**Core telemetry pipeline:**

```
VEXcode Python runtime
  → telemetry stdout JSON
  → V5 user port (USB serial, 115,200 baud)
  → Raspberry Pi
  → onboard processing (YOLO + AprilTag + serial_bridge) if Pi is available,
    otherwise off-board processing via Claude API (batch JSONL upload)
  → revised self-model JSON
```

---

## Core Concepts

### LLM-Authored Self-Model

The self-model is a versioned JSON document with four layers:

| Layer | Content |
|-------|---------|
| **Structural** | Typed graph of parts and connections — `drive_module×2 → chassis → sensor_mast → claw` |
| **Capability** | Physical parameters derived from specs: reach, torque budget, max step height, CoM, stable polygon |
| **Predictive** | Forward-simulated behavior for a goal task — "predicted: clear 18 cm step in 2.1 s" |
| **Gap model** | Signed residuals from real execution — feeds next-generation revision |

The generational loop:

```
Generator LLM  →  authors self-model from finite parts + physical specs
Critic LLM panel  →  attacks pre-build ("CoM too high", "torque budget insufficient")
Simulation  →  scores predicted behavior (URDF/SDF, Gazebo or Isaac Sim)
Human build  →  assembles from auto-generated BOM + ordered steps
Telemetry execution  →  robot attempts goal; Pi captures motor + vision residuals
Gap analysis  →  updates capability & predictive layers; corrects structural params
             →  loop to Generator LLM for Gen N+1
```

### Typed Assembly Grammar

Morphology search is bounded to a **finite design language** — not free-form CAD. The VEX V5 Classroom Starter Kit has ≈15–30 valid configurations across 6 parameters:

```json
{
  "motor_allocation": ["2drive+2free", "2drive+1arm+1claw", "4drive", "3drive+1manip"],
  "arm_position":     ["front", "rear", "side", "absent"],
  "end_effector":     ["claw_grasper", "bare_arm", "roller", "none"],
  "wheel_config":     ["front_omni+rear_standard", "all_standard", "all_omni"],
  "arm_gear_ratio":   ["7:1", "1:1"],
  "cartridge":        ["100rpm", "200rpm", "600rpm"]
}
```

Generational ladder:

| Gen | Morphology | Description |
|-----|-----------|-------------|
| 0 | Speedbot | 2-motor drivetrain only — simplest valid sentence |
| 1 | Clawbot | Full vocabulary: drive + arm + claw (41-step official build) |
| 2–5 | Mutations | Valid variants exhausting the remaining design space |

### Task Telemetry Contract

Every task primitive emits a three-block JSON document:

```json
{
  "task": "grab",
  "generation": 1,
  "predicted": {
    "object_width_mm": 40,
    "grip_force_N": 14.7,
    "success": true
  },
  "observed": {
    "claw_position_delta_deg": 120,
    "claw_current_A": 1.8,
    "claw_torque_Nm": 0.9,
    "claw_velocity_RPM": 2.3,
    "gripped_binary": 1
  },
  "gap": {
    "force_error_N": -0.9,
    "width_error_mm": 5
  }
}
```

The `gap` block is ground truth. The Generator LLM reads it and revises exactly the physical parameter that caused the discrepancy. A platform without per-actuator feedback cannot populate `observed` → cannot close the loop. This criterion eliminated PicoBricks REX (open-loop DC motors, no encoder bus).

### Physical-Robot Software Factory

A CI/CD-style pipeline treating robot design, build instructions, simulation scenes, and firmware as versioned artifacts:

1. **Design** — typed part catalog, normalized BOM, assembly graph
2. **Instruction** — auto-generated ordered build steps + cable/port map
3. **Simulation** — URDF/SDF geometry + contact-rich validation
4. **Software** — VEXcode Python (Brain), Pi scripts, calibration assets
5. **CI/CD** — on every design change: rebuild artifacts, run sim regression, verify BOM
6. **Execution** — human assembles; robot runs; telemetry recorded
7. **Learning** — per-generation controller learning + cross-generation design prior update

---

## Aesthetic Vocabulary

A non-functional extension to the typed assembly grammar that gives the Generator LLM structured choices for **visual self-expression**. The key insight: aesthetic choices can encode hypotheses and make them visible. "Wide side panels = testing mass distribution." "Forward antennae = prioritizing forward sensing." "Gen 3 color = deep blue breathing pattern." This makes generations visually distinct (identifiable in photos without reading telemetry) and gives the LLM a richer self-description to author.

### Grammar Schema

```json
{
  "aesthetic_vocabulary": {
    "body_panel": {
      "material": ["corrugated_plastic", "craft_foam", "cardboard", "acrylic", "3d_print", "none"],
      "position": ["left_side", "right_side", "top_deck", "front_face", "rear_skirt"],
      "color": ["generation_palette_primary", "generation_palette_accent", "raw_steel"]
    },
    "surface_markings": {
      "tape_pattern": ["none", "stripes", "chevron", "solid_block", "diagonal"],
      "tape_color": ["red", "blue", "yellow", "black", "iridescent"],
      "identity_label": ["sticker_numeral", "painted_numeral", "none"]
    },
    "appendages": {
      "type": ["none", "antennae", "swept_fins", "dorsal_ridge", "cage_frame", "whiskers"],
      "material": ["pipe_cleaner", "craft_wire", "foam", "cardboard", "3d_print"],
      "position": ["top_chassis", "arm_tip", "front_bumper", "rear_deck"]
    },
    "accent_lighting": {
      "type": ["none", "neopixel_strip", "neopixel_ring"],
      "position": ["chassis_edge", "arm_tip", "camera_ring"],
      "pattern": ["solid", "breathing", "chase", "generation_pulse"]
    }
  }
}
```

### Materials by Cost Tier

| Tier | Items | Cost | Notes |
|------|-------|------|-------|
| Free | Cardboard, aluminum foil, recycled plastic containers | $0 | Attach with zip ties through VEX 0.5" square holes or velcro |
| Dollar store | EVA foam sheets, pipe cleaners, colored electrical tape, washi tape, stickers, googly eyes, pom-poms | $1–5 | Dollar Tree covers 3–4 generations per trip |
| Hardware store | Corrugated plastic (Coroplast), aluminum craft wire (18–22 gauge), velcro roll | $5–15 | Coroplast punched at 0.5" spacing bolts directly to VEX frame; best non-printed rigid panel |
| Electronic | WS2812B NeoPixel strip (1m/60 LED), NeoPixel ring (8–12 LED) | $8–25 | Pi 5 requires SPI workaround — see below |
| 3D print | Custom panels, fins, crests, camera visors | $3–15/part | Access: UT Austin FabLab (free), Austin Public Library Digital Harbor (free), Makespace Austin (~$15/mo), Craftcloud online (~$3/part) |

### Attachment Methods (No Tools Required)

All methods work through existing 0.5" VEX square holes — no drilling, no modification to metal:

| Method | Best for | Notes |
|--------|---------|-------|
| **Velcro (primary)** | All soft/foam panels | Adhesive-backed, repositionable, hot-swap between generations |
| **Zip ties** | Wire, foam, fabric, cardboard | Loop through square holes |
| **Binder clips** | Temporary/test fits | Clip to channel flanges; zero modification |
| **VEX screws** | Rigid panels (Coroplast, acrylic) | Punch holes at 0.5" spacing to match VEX grid |

### Constraints

- Total aesthetic add-on weight **≤ 150g** — Pi 5 system already consumes ~316g of the Clawbot's ~500g capacity
- Nothing obstructs Camera Module 3 front FOV (~120° for Wide variant)
- Hot glue is not recommended — not reversible between generations
- NeoPixel on Pi 5 requires the SPI method or Arduino Nano co-controller (see below)

### WS2812B NeoPixel — Hardware Notes

**Pi 5 compatibility caveat**: the standard `rpi_ws281x` PWM/DMA library does not work on Raspberry Pi 5 due to hardware GPIO changes. Two workarounds:

1. **SPI method (recommended, no extra hardware)** — connect LED data wire to GPIO 10 (SPI0-MOSI, pin 19); install `adafruit-circuitpython-neopixel-spi`; enable SPI in raspi-config.
   ```python
   import neopixel_spi as neopixel
   pixels = neopixel.NeoPixel_SPI(board.SPI(), N_LEDS, pixel_order=neopixel.GRB)
   ```
2. **Arduino Nano co-controller (~$5, 7g)** — Pi sends `{"color": [R, G, B], "pattern": "breathing"}` JSON over USB serial; Nano drives the strip with `FastLED`. Easier software path; slight extra weight.

**Power**: 5V from Pi GPIO pin 2/4 (power bank rail). Each LED draws up to 60mA at full white; at typical use (partial brightness, non-white) expect ~3–5mA per LED. A 30-LED strip at moderate brightness draws ~150mA — negligible against a 10,000mAh bank.

**Mounting**: strip adhesive-back along chassis rear edge or under chassis rail for underglow; ring mounts around Camera Module 3 lens as a "glowing eye" with velcro or zip ties.

---

## Hardware Architecture

### VEX V5 Brain

**Classroom Starter Kit (276-7010)** — $849.49

| Subsystem | Parts | Motor port | Gear ratio |
|-----------|-------|------------|------------|
| Drive left | 4" standard wheel | 1 | 1:1 |
| Drive right | 4" standard wheel | 10 | 1:1 |
| Front passive | 4" omni × 2 | — | — |
| Lift arm | 84T:12T reduction | 8 | 7:1 |
| Claw | 12T + rubber-band return | 3 | 1:1 |

**Smart Motor telemetry API** (per-actuator, 20 ms loop):

```python
motor.torque(Nm)          # 0.0–2.1 Nm
motor.current(AMP)        # 0–2.5 A
motor.velocity(RPM)       # actual RPM
motor.position(DEGREES)   # cumulative degrees, ±0.02° resolution
motor.power(WATT)         # 0–12.75 W
motor.temperature(PERCENT)
```

**Grip detection pattern** (no `is_stalled()` in VEXcode API):

```python
claw.set_max_torque(30, PERCENT)
claw.spin_for(720, DEGREES, timeout=3)
# object gripped when: velocity < 5 RPM AND current > 1.5 A
grip_width_proxy_deg = claw.position(DEGREES)
```

### Raspberry Pi 5 Coprocessor

| Spec | Value |
|------|-------|
| CPU | Quad-core Cortex-A76 @ 2.4 GHz |
| RAM | 4 GB LPDDR4X (capstone target) |
| Camera | Pi Camera Module 3, 12 MP, CSI 22-pin |
| Weight | ~280–350 g (board + case + camera + power bank) |
| Power draw | 3–5 W (YOLO + AprilTags + serial bridge) |
| Runtime | 12–15 hr on 10,000 mAh USB-C PD bank |

Vision performance:

| Stack | Resolution | FPS (CPU) |
|-------|-----------|-----------|
| OpenCV color/blob | 640×480 | 30+ |
| YOLO11n NCNN INT8 | 640×480 | 8–10 |
| YOLO11n NCNN INT8 | 240×240 | 25+ |

8 FPS is sufficient for 0.5–2 Hz manipulation tasks.

### Communication Paths

**Stage 1 — USB Serial (recommended)**

```
Pi USB-A ──── microUSB ──── V5 Brain user port
Device:    /dev/ttyACM0
Baud:      115,200
Protocol:  newline-delimited JSON
Throughput: ~11,500 B/s; 300-byte contract in ~35 ms
udev rule: SUBSYSTEM=="tty", ATTRS{idVendor}=="2888", MODE="0666", SYMLINK+="vex_brain"
```

**Stage 2 — RS-485 Smart Port (high-throughput)**

```
V5 Smart Port (RS-485) ──── RS-485→TTL module ──── Pi GPIO UART
Baud: up to 921,600 (8× USB speed)
Benefit: dedicated channel; USB free for code upload during live demo
PROS API: vexGenericSerialEnable(), vexGenericSerialBaudrate()
```

**Stage 2 alt — rosserial (ROS bridge)**

```
V5 Brain (PROS 3.x + ros_lib) ←USB→ Pi (rosserial_python)
Stable at 100 Hz; makes V5 Brain a full ROS node
```

---

## Software Architecture

### V5 Brain (VEXcode Python)

```python
# brain_main.py  — runs on V5 at 20 ms tick
import sys, json
from vex import *

brain = Brain()
left_motor  = Motor(Ports.PORT1,  GearSetting.RATIO_18_1, False)
right_motor = Motor(Ports.PORT10, GearSetting.RATIO_18_1, True)
arm_motor   = Motor(Ports.PORT8,  GearSetting.RATIO_18_1, False)
claw_motor  = Motor(Ports.PORT3,  GearSetting.RATIO_18_1, False)

def emit_contract(task, predicted, observed):
    gap = {k: observed.get(k, 0) - predicted.get(k, 0) for k in predicted}
    sys.stdout.write(json.dumps({
        "task": task, "predicted": predicted,
        "observed": observed, "gap": gap
    }) + "\n")
```

### Raspberry Pi 5 (3 Cooperating Scripts)

**`vision_loop.py`**
- Pi Camera Module 3 → OpenCV frame capture
- YOLO11n (NCNN INT8) → object detections at 8–10 FPS
- AprilTag detector (tag36h11, 100 mm markers) → robot pose `{x, y, heading}`
- Emits `{detections, pose}` JSON to serial_bridge

**`serial_bridge.py`**
- Reads contract JSON from `/dev/ttyACM0`
- Merges with latest vision state
- Appends to `session_YYYYMMDD_HHMMSS.jsonl` with `flush()` per contract
- JSONL chosen over SQLite: faster insert-heavy writes on Pi SD card; directly consumable by Anthropic Batch API

**`llm_loop.py`**
- Reads latest contract from JSONL
- Calls Claude API (Mode A: sync, 1–4 s latency; Mode B: batch, 50% cost, 24 h SLA)
- Parses revised self-model from LLM response
- Writes next motor command → `/dev/ttyACM0`

### Claude API Integration

```python
# Mode A — real-time per contract (demo)
response = anthropic.messages.create(
    model="claude-opus-4-8",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": f"Current self-model:\n{json.dumps(self_model)}\n\n"
                   f"Latest contract:\n{json.dumps(contract)}\n\n"
                   "Revise the capability layer to correct the gap residuals. "
                   "Return the updated self-model as JSON."
    }]
)

# Mode B — batch post-session (training / cost optimization)
batch = anthropic.messages.batches.create(requests=[...])
```

---

## Generational Loop

| Stage | Who | Inputs | Outputs |
|-------|-----|--------|---------|
| 1. Design | Generator LLM | Typed grammar vocab + prior gaps | Self-model JSON vN.0 |
| 2. Critique | Critic LLM panel (parallel) | Self-model vN.0 | Pass / Revise feedback |
| 3. Simulation | Gazebo / Isaac Sim | Self-model (final) | Predicted behavior score; sim_trace.bag |
| 4. Build | Human | BOM + ordered build steps | Physical robot Gen N |
| 5. Execution | V5 Brain + Pi | Robot + task description | session_*.jsonl of contracts |
| 6. Analysis | Generator LLM | Task contracts (gaps) | Revised self-model vN+1.0; revision_notes.md |
| 7. Learning | System | All gaps across generations | Updated design prior; builder error model |

**Minimum Viable Demo (June 29)**:
1. Gen 0 Speedbot — LLM authors self-model from specs
2. Run traverse task → telemetry collected
3. Show gap JSON → LLM revises self-model in plain language
4. Gen 1 Clawbot assembled from revised design + BOM
5. Run grab task again → show telemetry improvement

---

## Data Structures & Schemas

### Self-Model Document

```json
{
  "generation": 1,
  "created_timestamp": "2026-06-17T14:32:00Z",
  "structural_model": {
    "base_platform": "clawbot",
    "drivetrain": {
      "motor_allocation": "2drive+1arm+1claw",
      "wheel_config": "front_omni+rear_standard",
      "wheel_diameter_mm": 101.6
    },
    "arm": { "present": true, "gear_ratio": "7:1", "reach_mm": 400 },
    "end_effector": { "type": "claw_grasper", "jaw_opening_mm": [0, 60] },
    "connections": [
      { "from": "drive_left_motor", "to": "chassis", "port": "1" },
      { "from": "arm_motor",        "to": "chassis", "port": "8" },
      { "from": "claw_motor",       "to": "arm",     "port": "3" }
    ]
  },
  "capability_model": {
    "max_torque_Nm": 2.1,
    "max_pull_force_N": 29.0,
    "max_velocity_mps": 0.6,
    "arm_reach_mm": 400,
    "grip_force_N": 14.7,
    "center_of_mass_mm": { "x": 150, "y": 100, "z": 80 },
    "friction_coefficient": 0.3
  },
  "predicted_behavior": {
    "task": "grab_40mm_object",
    "predicted_success": true,
    "predicted_grip_force_N": 14.7,
    "predicted_time_s": 1.2
  },
  "prior_gap_residuals": [
    {
      "generation": 0,
      "task": "flat_ground_traverse_2m",
      "gap": { "time_error_s": -0.2, "energy_error_J": 1.2 }
    }
  ],
  "reasoning": {
    "structural_choices": {
      "motor_allocation": "2drive+1arm+1claw chosen over 4drive because the grab task requires end-effector control; drivetrain has sufficient torque for flat-surface traversal with two motors.",
      "arm_gear_ratio": "7:1 selected over 1:1 because Gen 0 gap showed the arm motor reaching current saturation at 1:1 — higher reduction trades speed for torque margin.",
      "wheel_config": "front_omni+rear_standard retained from Gen 0; no steering-resistance gap observed, so no reason to change."
    },
    "capability_estimates": {
      "grip_force_N": "14.7 N derived from claw motor spec (2.1 Nm stall × 1:1 ratio ÷ 0.143 m moment arm); Gen 0 gap showed -0.9 N error so this estimate carries a known 6% downward bias to be corrected next generation.",
      "friction_coefficient": "0.3 is the catalog default for VEX 4-inch standard wheels on foam tile; no empirical correction yet — flag for revision once pull-task telemetry is collected."
    },
    "predicted_behavior": "grab_40mm_object chosen as the benchmark task because it exercises all four motors and produces the richest telemetry signal (grip current + arm torque + drive odometry).",
    "gap_interpretation": "Gen 0 traverse showed the robot arrived 200 ms late and used 1.2 J more energy than predicted, consistent with friction_coefficient being underestimated. Arm and claw added in Gen 1 to test the full morphology; friction estimate revision deferred until pull-task data confirms the pattern.",
    "critic_feedback_incorporated": [
      "Critic A flagged CoM shift from arm addition — arm_motor moved to Port 8 (rear chassis plate) to keep CoM within stable polygon.",
      "Critic B noted claw jaw_opening_mm [0,60] may not clear a 50 mm object with tolerance — acknowledged; jaw range left unchanged pending physical measurement."
    ]
  }
}
```

### Task Telemetry Contract (full with vision)

```json
{
  "session_id": "session_20260617_143200",
  "task": "grab",
  "generation": 1,
  "predicted": {
    "object_width_mm": 40,
    "grip_force_N": 14.7,
    "success": true
  },
  "observed": {
    "claw_position_delta_deg": 120,
    "claw_current_A": 1.8,
    "claw_torque_Nm": 0.9,
    "claw_velocity_RPM": 2.3,
    "gripped_binary": 1
  },
  "gap": {
    "force_error_N": -0.9,
    "width_error_mm": 5
  },
  "vision": {
    "object_detected": true,
    "object_bbox": [120, 80, 200, 160],
    "object_confidence": 0.92,
    "apriltag_pose": { "x": 487, "y": -12, "heading": 2 },
    "pose_gap": { "dx": -13, "dy": -12, "dtheta": 2, "bbox_iou": 0.96 }
  }
}
```

### VEX V5 Part Catalog (vocabulary for grammar)

```json
{
  "catalog_version": "1.0",
  "parts": {
    "smart_motor_11w": {
      "sku": "276-2006",
      "max_torque_Nm": 2.1,
      "max_continuous_torque_Nm": 0.735,
      "max_velocity_RPM": 600,
      "max_current_A": 2.5,
      "encoder_resolution_deg": 0.02,
      "api": ["torque", "current", "velocity", "position", "power", "temperature"]
    },
    "clawbot_arm": {
      "sku": "276-6004",
      "gear_ratio": "7:1",
      "max_reach_mm": 400,
      "arm_length_mm": 280,
      "mass_g": 312
    },
    "clawbot_claw": {
      "sku": "276-3005",
      "jaw_opening_mm": [0, 60],
      "continuous_grip_force_N": 14.7,
      "mass_g": 156
    }
  },
  "morphology_constraints": {
    "max_ports": 21,
    "must_include": ["brain", "battery", "drivetrain"],
    "forbid_closed_loops": true,
    "requires_balance_check": true
  }
}
```

---

## Reality Gap Mitigation

The dominant technical risk: designs that score well in simulation fail on real hardware due to friction, motor backlash, snap-fit tolerances, wheel slip.

| Mitigation | Detail |
|-----------|--------|
| Narrow tasks + stiff morphologies | Start with grab/pull/throw on flat surface only |
| AprilTag localization | tag36h11, 100 mm markers around workspace; Pi computes `{x, y, heading}` from camera alone, not odometry |
| Acceptance testing | Short commissioning script after each build; insertion state machines with compliance |
| Residual learning | Collect sim-vs-real gaps across generations; feed residual model back into controller and design prior |
| Visual gap feedback | `{dx, dy, dtheta, bbox_iou}` from AprilTag vs. predicted pose feeds next-generation structural revision |

---

## External Integrations

| Service | Role | Protocol |
|---------|------|---------|
| **Claude API** (`claude-opus-4-8`) | Generator LLM + Critic panel | HTTPS JSON; Mode A sync (1–4 s); Mode B batch (50% cost, 24 h SLA) |
| **Anthropic Batch API** | Bulk post-session telemetry analysis | HTTPS JSON; JSONL input directly from Pi |
| **YOLO11n (NCNN INT8)** | Object detection on Pi | Python `ultralytics`; 8–10 FPS @ 640×480 |
| **AprilTag library** | Workspace localization | Python pip; tag36h11 family; outputs 3D pose |
| **OpenCV** | Camera capture + frame ops | Python `cv2` |
| **Gazebo / Isaac Sim** | Simulation validation | URDF/SDF input; trajectory playback |
| **BrickLink Studio** | Build instruction generation | Morphology JSON → `.io` / BOM export |
| **Flywheel (Paradigma)** | Research DAG audit trail | MCP interface; generational lineage as DAG ancestry |

---

## Key Architectural Decisions

1. **Two-computer split (V5 Brain + Pi 5)** — V5 Brain handles deterministic 20 ms motor control; Pi handles asynchronous, compute-heavy vision and LLM calls. Mixing them would require realtime Linux on Pi or slow motor loops on V5.

2. **USB serial at 115,200 baud for Stage 1** — proven, no extra hardware, bidirectional, sufficient for 300-byte contracts at ~35 ms. Upgradable to RS-485 Smart Port (921,600 baud) in Stage 2 without changing the JSON protocol.

3. **Task Telemetry Contract as the data contract** — machine-readable, platform-agnostic, directly quantifies what the self-model got wrong. The `gap` block is the only signal the LLM needs; nothing else is passed.

4. **Typed assembly grammar (15–30 valid configs)** — bounded search space makes LLM generation tractable and guarantees every generated design is buildable from real parts. Unbounded CAD generation produces unassemblable outputs.

5. **JSONL telemetry storage** — append-only, `flush()` per contract, directly consumable by Anthropic Batch API. Faster than SQLite for insert-heavy Pi SD card workloads.

6. **Human-in-the-loop assembly** — full autonomous self-replication is low-feasibility. Keeping human as a formal manufacturing station (not ad-hoc assembler) preserves the learning loop while collapsing cost and risk. The system designs; the human compiles.

7. **AprilTags for localization, not pure odometry** — wheel slip and snap-fit tolerances make pure odometry unreliable. Fiducial-based workspace localization is the single biggest reality-gap mitigation available without additional sensors.

8. **Flywheel DAG for generational audit trail** — each generation is a DAG node; design rationale + telemetry evidence are preserved and inspectable without manual file history parsing. Maps 1:1 to the self-model evolution loop.
