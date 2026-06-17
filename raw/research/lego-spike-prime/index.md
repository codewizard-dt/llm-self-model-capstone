---
topic: LEGO SPIKE Prime kit — its functionality and whether it is appropriate for this project
slug: lego-spike-prime
researched: 2026-06-16
sources: [./sources.md]
---

# Research: LEGO SPIKE Prime Kit — Functionality & Project Fit

> SPIKE Prime is appropriate as the Stage-1 physical substrate for the LLM-authored robot self-model capstone — but it must be purchased immediately (LEGO.com is already out of stock; Amazon still has stock per the user's link). The finite parts catalog, absolute-encoder motors, and tri-sensor suite map directly onto the typed assembly grammar and gap-model requirements. All LLM inference and planning must offload to external compute (Raspberry Pi Build HAT or workstation via USB serial). The platform officially retires June 30, 2026 — one day after the capstone showcase — which is acceptable for a demo but demands keeping the typed-grammar JSON representation platform-agnostic from day one so Stage 2 (VEX V5) is a representation swap, not a rewrite.

---

## Research Questions

1. What hardware does the SPIKE Prime kit (45678) contain, and what are the technical specifications?
2. What programming interfaces are available for external-compute integration?
3. What is the retirement/lifecycle status, and does it affect the capstone timeline?
4. Is the parts vocabulary finite and typed enough to ground the LLM self-model?
5. What are the gaps (sensors, compute, structural) that require external supplements?

---

## Current State (Codebase)

The wiki already holds a `lego-spike-prime` entity page (`wiki/knowledge/entities/tools/lego-spike-prime.md`) with a summary: hub specs, Python path, Raspberry Pi Build HAT reference, and the June 30 lifecycle flag. The `feasibility-human-built-generational-factory` source page documents the three-stage roadmap (SPIKE → VEX V5 → ROBOTIS) and the concrete generation manifest JSON / YAML build package formats. No code exists yet — the project is at the planning stage (capstone proposal due June 17, showcase June 29). [S1][S2]

---

## Key Findings

### Hardware Profile [S3][S4][S5]

| Component | Specification |
|-----------|---------------|
| Hub processor | STM32F413 ARM Cortex M4 @ ~100 MHz |
| Hub RAM | 320 KB SRAM |
| Hub Flash | ~1–1.5 MB |
| Hub ports | 6 LPF2 I/O (bidirectional, auto-detect) |
| Built-in IMU | 6-axis gyro (accelerometer + gyroscope) |
| Built-in display | 5×5 programmable LED matrix |
| Built-in comms | Bluetooth + USB (micro-USB) |
| Hub battery | Rechargeable Li-ion, 2100 mAh |
| Large Angular Motor | Absolute encoder, ±3° accuracy, integrated |
| Medium Angular Motor (×2) | Absolute encoder, ±3° accuracy, integrated |
| Distance Sensor | Ultrasonic, 0–2 m range, 1 mm resolution, 4 white LEDs |
| Force Sensor | 0–10 N, ±0.65 N accuracy, detects touch, tap, press |
| Color Sensor | 8 colors, reflectivity, ambient light, 3 white LEDs |
| LEGO Technic elements | ~528 pieces (503–557 depending on source) |
| MSRP (original) | $429.95 |
| Current secondary market (new, sealed) | ~$566 (appreciating 6.2%/yr since release) |

**No native camera.** Visual perception requires an external USB webcam or Raspberry Pi camera module. [S3]

### Programming Interfaces [S6][S7][S8]

Three viable paths for external-compute integration:

**1. Raspberry Pi Build HAT** — A $25 HAT that plugs into the Pi's 40-pin GPIO header. Controls up to **4** LPF2 motors/sensors (vs. hub's 6) over a text serial protocol at 115200 baud (`/dev/serial0`). Raspberry Pi Foundation ships a first-party Python library (`build-hat`) that controls motors and reads sensors from full Python on the Pi. The Pi can simultaneously drive a camera, run LLM inference (offloaded to a workstation via API), and command the robot. This is the recommended integration path. [S7]

**2. USB serial / MicroPython REPL** — Connect hub to a computer via USB cable. The hub exposes a MicroPython REPL over serial, enabling script upload and sensor logging without the SPIKE app. External tools (VS Code extension + `python3` upload script) enable edit–flash–run cycles. [S6]

**3. PyBricks (alternative firmware)** — Open-source MicroPython-based firmware that replaces the LEGO firmware on the hub. Provides a cleaner, more complete Python API (`pybricks.hubs.PrimeHub`, `pybricks.pupdevices.Motor`, etc.), offline program storage on the hub, Bluetooth REPL, and better motor primitives. Actively maintained; supports VS Code. The trade-off is flashing non-LEGO firmware (reversible). [S8]

For the capstone, the recommended stack is: **PyBricks on hub** (for clean motor/sensor API) + **workstation** (running LLM agents, the self-model pipeline, telemetry logging) connected via Bluetooth or USB serial. The Build HAT is an alternative if Raspberry Pi is the onboard compute node.

### Retirement Status [S9][S10][S11]

- **Official end-of-sales date: June 30, 2026** — one day after the capstone showcase (June 29, 2026).
- LEGO Education's own product page already reads: "This product is retiring on June 30, 2026." [S10]
- LEGO.com direct stock: **already out of stock** as of mid-June 2026 (confirmed by Blocks Magazine). [S11]
- **Third-party availability**: Amazon still carries it (user-shared link: B07QN7ZJF9); eBay lists sealed units. Secondary market price ~$566 new.
- SPIKE App: bugs fixed through support period; no new features after June 30, 2026.
- Successor platform: **LEGO Education Computer Science & AI** kit (shipping April 2026, $339.95 for 4 students). This is a classroom CS/AI curriculum kit (1 double motor, 1 single motor, 1 color sensor, 2 connection cards) — **not a robotics research platform** and not a viable successor for this capstone. [S12]
- FLL competition: SPIKE no longer eligible from 2026–2027 season onward.

### Typed Grammar Fit [S1][S2][S13]

The feasibility report's generation manifest uses a typed JSON schema (`morphology`, `electronics.hub_ports`, `constraints.max_ports`, etc.) that maps directly onto SPIKE Prime's finite parts vocabulary:

- **Actuation nodes**: `large_angular_motor`, `medium_angular_motor` — 2 types, 3 total in base kit
- **Sensing nodes**: `distance_sensor`, `force_sensor`, `color_sensor` — 3 types, 1 each
- **Hub constraint**: `max_ports: 6` hard limit (or `max_ports: 4` if using Build HAT)
- **Structural elements**: typed LEGO Technic beam/axle/bracket vocabulary (finite by kit BOM)

The finite vocabulary is **exactly the grounding requirement** for the self-model: "A self-model is only worth anything if it's grounded — grounding comes from the finite parts catalog with real physical specs." [S2] SPIKE Prime delivers a small, enumerable parts space that makes the LLM's typed graph traversal tractable at capstone scale.

### Gaps Requiring External Supplements [S3][S7]

| Gap | Mitigation |
|-----|-----------|
| No camera | USB webcam or Pi camera module on external compute |
| Only 3 motors (base kit) | Expansion set 45681 adds 1 more large motor + Maker Plate; or use structural/gearing tricks |
| 320 KB RAM: zero on-hub inference | All LLM calls, planning, and self-model revision run on workstation; hub is pure actuator/sensor |
| 4-port limit on Build HAT | Use hub's 6 native ports + PyBricks if more than 4 devices needed |
| No BrickLink Studio ↔ hub physical bridge | BrickLink Studio generates BOMs and step files; commissioning uses those as input to the build package; human builder is the bridge |
| Platform retiring post-showcase | Architecture must be platform-agnostic; typed grammar JSON must not encode SPIKE-specific part IDs |

---

## Constraints

1. **Buy immediately** — LEGO.com is out of stock; the Amazon link (B07QN7ZJF9) is the fastest path; eBay also has sealed units at ~$566.
2. **External compute is mandatory** — 320 KB RAM makes zero on-hub LLM inference possible; the hub is a pure peripheral.
3. **Design representation must be platform-agnostic from day 1** — Stage 2 (VEX V5) migration must be a JSON vocabulary swap, not an architectural rewrite.
4. **No camera in base kit** — the "killer demo" (robot attempting stairs, telemetry updating self-model) requires an external USB or Pi camera for visual confirmation and failure capture.
5. **Showcase is June 29; retirement is June 30** — the demo must be fully operational on existing hardware before the retirement date; no last-minute LEGO parts orders will be possible.

---

## Solution Comparison

Three external-compute integration architectures:

| Criteria | A: PyBricks + USB to Workstation | B: Build HAT + Raspberry Pi | C: Native SPIKE App + Workstation |
|----------|----------------------------------|---------------------------|----------------------------------|
| **Approach** | Flash PyBricks; connect via USB serial/BT to MacBook running LLM pipeline | Raspberry Pi with Build HAT as onboard compute; workstation does LLM calls via API | Use SPIKE App Python; connect to workstation via Bluetooth for telemetry |
| **Pros** | Cleanest Python API; most motor control; offline hub programs; VS Code native | Pi is self-contained; camera integration on-board; portable demo | No firmware flash needed; easiest to start |
| **Cons** | Laptop must be tethered or nearby | 4-port limit on Build HAT; Pi adds cost/setup | SPIKE App MicroPython is limited; no offline storage; app ecosystem retiring |
| **Complexity** | Medium (one-time firmware flash) | Medium (Pi setup + Build HAT wiring) | Low initially, high later |
| **Codebase fit** | High — workstation runs Python LLM pipeline | High — Pi runs Python LLM pipeline locally, offloads inference | Medium — SPIKE App Python is constrained |
| **Post-retirement** | Supported by PyBricks community (not LEGO) | Supported by Raspberry Pi Foundation | SPIKE App unsupported after Jun 30 |
| **Recommendation** | **Preferred for capstone** | Good if demo needs to be portable | Not recommended |

---

## Recommendation

**SPIKE Prime is the right Stage-1 substrate. Proceed with Option A (PyBricks + workstation).**

### Why it fits
- The kit's finite parts vocabulary is the typed assembly grammar — small enough for an LLM to enumerate, large enough for meaningful structural variation.
- Absolute-encoder motors (±3°) deliver the per-joint telemetry the gap model needs to close the self-model feedback loop.
- The tri-sensor suite (distance, force, color) provides sufficient task-performance observability for the stair-climbing / obstacle demo.
- PyBricks gives a clean Python API, making the hub-to-pipeline interface a two-line serial read.

### Implementation outline

1. **Acquire hardware now** — Order from Amazon (B07QN7ZJF9); also order expansion set 45681 for the extra large motor and Maker Plate. Budget ~$600–700 total.
2. **Flash PyBricks** — one-time; enables Bluetooth REPL + offline programs + clean `pybricks.pupdevices` API.
3. **Define typed parts catalog** — Write `spike_prime_catalog.json`: enumerate every part type with its physical specs (motor torque, gear ratio, sensor range, mass, mounting geometry). This is the grounding document.
4. **Stand up the generation manifest schema** — Implement the JSON generation manifest from the feasibility report with SPIKE Prime vocabulary substituted for the generic spec.
5. **Build the external pipeline** — Python on workstation: Generator LLM → self-model JSON → Critic LLM panel → (if critics pass) → build package YAML → human assembles → PyBricks runs commissioning program → telemetry log → Gap model update.
6. **Camera integration** — USB webcam on workstation captures video of robot task attempt; frame extraction feeds a vision check (did the robot clear the obstacle?) into the telemetry record.
7. **Gen 1 demo target** — Simple flat-surface locomotion with self-model: "I am a two-wheeled differential drive. Predicted: 0.5 m/s." → run → telemetry → gap → Gen 2 self-model revision.

### Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| SPIKE Prime units sold out before order | Order immediately from Amazon (B07QN7ZJF9); check eBay as backup |
| SPIKE App retiring kills toolchain | Use PyBricks — not dependent on SPIKE App; community-maintained |
| Only 3 motors limits morphology richness | Expansion set 45681 adds 1 large motor; gearing multiplies effective DOFs |
| Hub RAM prevents on-board planning | Architecture already requires offload; this is not a design risk |
| Platform-specific typed grammar | Define `platform` field in generation manifest from day 1; Stage 2 = swap vocabulary JSON |
| No camera for visual feedback | USB webcam + OpenCV on workstation; not a SPIKE Prime limitation, just a supplement |

---

## Next Steps

- **Immediate**: Order SPIKE Prime 45678 from Amazon (B07QN7ZJF9) + expansion set 45681. LEGO.com is out of stock.
- `/task-add "Acquire SPIKE Prime hardware and flash PyBricks firmware"` — first unblocking task
- `/task-add "Define spike_prime_catalog.json typed parts vocabulary"` — grounds the self-model
- `/task-add "Implement generation manifest JSON schema for SPIKE Prime"` — the data contract
- If the project direction is confirmed: `/decision-create` on the choice of PyBricks vs Build HAT vs native SPIKE App as the integration path.
- Run `/wiki-ingest raw/research/lego-spike-prime/index.md` to synthesize this research into the knowledge base and update the `lego-spike-prime` entity page.
