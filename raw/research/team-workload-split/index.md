---
topic: how to split the work load for this project into more modular, approachable tasks for 4 team members
slug: team-workload-split
researched: 2026-06-17
sources: [./sources.md]
---

# Research: Team Workload Split — 4 Members, 12-Day Sprint

> **Executive summary**: The capstone system has four naturally parallel workstreams — (A) Hardware/Robot, (B) Pi Infrastructure/Pipeline, (C) AI Core/Self-Model, (D) Simulation/Demo/Integration — each independently startable on Day 1. Critical path runs A→B→C; Person D unblocks the showcase track. Assign one member per workstream with explicit mock-data contracts so each person can develop and test before upstream work is ready.

---

## Research Questions

1. What are the independently startable workstreams in this project?
2. Which workstreams have hard sequential dependencies, and which can proceed in parallel?
3. What is the critical path, and how should its risk be mitigated?
4. How should work be partitioned across exactly 4 members over 12 calendar days?
5. What are the minimum shippable milestones vs. the full-vision milestones per track?

---

## Current State (Codebase)

The project has no code yet — it is a wiki/research-stage capstone with a planning document due June 17. The system design is fully specified across:

- `wiki/knowledge/concepts/llm-authored-self-model.md` — the full generation loop
- `wiki/knowledge/concepts/task-telemetry-contract.md` — JSON schemas for grab/pull/throw
- `wiki/knowledge/sources/vex-v5-telemetry-pipeline.md` — 3-stage transport spec (Brain → Pi → Claude)
- `wiki/knowledge/sources/vision-vex-architecture.md` — Pi vision stack architecture
- `wiki/knowledge/sources/research-vex-v5-advanced-toolchains.md` — VEXcode Python vs PROS
- `capstone-experiment.flowchart.md` — end-to-end system flowchart

The system is well-enough specified that all four workstreams can begin implementation simultaneously on Day 1 with mocked interfaces.

---

## Key Findings

**[S1] The system has four natural layer boundaries**, each mapping to distinct expertise and toolchains:

| Layer | Toolchain | Can start Day 1? |
|-------|-----------|-----------------|
| Hardware / Robot (V5 Brain) | VEXcode Python, MicroPython, VEX motors | Yes — robot assembly + motor code |
| Pi Infrastructure / Pipeline | Python, pyserial, JSONL, Anthropic SDK | Yes — mock telemetry JSON from file |
| AI Core / Self-Model | Claude API, JSON Schema, prompt engineering | Yes — no hardware needed; mock contracts |
| Simulation / Demo | PyBullet, URDF, Mermaid/Markdown, Deliverable 01 | Yes — sim is hardware-independent |

**[S2] The Task Telemetry Contract JSON is the integration seam.** [S4] Its schema is fully specified in `task-telemetry-contract.md`. Any workstream can mock this JSON independently — Person B can build the pipeline before Person A's robot is running; Person C can write and test the self-model revision loop before Person B's pipeline exists. The contract schema is the shared API contract.

**[S3] The critical path is A→B→C** (robot emits telemetry → Pi pipeline receives it → LLM revises self-model), but each stage has a testable mock stub:
- Person B: reads pre-saved `.jsonl` files instead of live serial
- Person C: calls revision loop against hand-crafted contract JSON

**[S4] Simulation (Person D) is almost entirely independent.** PyBullet setup, URDF generation from the typed grammar, and the Deliverable 01 planning document can all proceed without any hardware or working pipeline. Person D converges with others only in Week 2 for the validation step.

**[S5] Vision is a Week 2 upgrade.** USB webcam + OpenCV + YOLO11n + AprilTag can be treated as an optional enhancement layer. The visual contract extension fields (`predicted.object_bbox`, `observed.pose`, `gap.dx/dy/dtheta`) are additive to the base contract schema, so Person B can add them without changing Person A's or Person C's work. [S3]

---

## Constraints

- **2-week wall clock** (June 17–29, 12 days): ambitious cut must be working by Day 10 for rehearsal time
- **Physical hardware singleton**: there is one VEX V5 robot; only Person A can do hardware-dependent work; everyone else must use mocks until Person A delivers a working telemetry emitter
- **VEXcode Python is sandboxed**: no pip on the Brain, no WiFi, no subprocess — all LLM logic lives on the Pi, not the robot
- **Showcase is 10 minutes live**: the "holy shit" moment requires at least 3 visible self-model generations with readable prose evolution; must be demoable reliably, not just once

---

## Solution Comparison

### Option A: Horizontal Layers (recommended)
Each member owns one layer end-to-end: Hardware, Pipeline, AI Core, Sim/Demo.

| Criteria | Horizontal Layers | Vertical Features | Mixed (no owner) |
|----------|------------------|------------------|-----------------|
| Day 1 start | All 4 start immediately | Partial (features cross layers) | Slow — requires coordination |
| Merge risk | Low — clear seam = Task Contract JSON | High — everyone touches same files | Very high |
| Blame/debug | Clear owner per layer | Unclear | Unclear |
| Hardware singleton | Well-managed (Person A owns it) | Multiple people blocked | Multiple people blocked |
| Knowledge concentration | Low (each layer = one person) | Medium | High |
| Demo readiness | Person D owns demo track entirely | Demo owned by everyone = nobody | Chaotic |

### Option B: Vertical Features
Each member owns one end-to-end feature: "grab loop", "vision", "critic system", "sim".
Downside: all four members touch the Pi, the API integration, and the robot code — merge conflicts and serial port contention.

### Option C: No explicit split
Everyone works on whatever is needed. Downside: the hardware singleton (one robot) creates a bottleneck; the AI core work drowns in hardware setup time.

---

## Recommendation

### Assign one member per layer:

---

### **Person A — Hardware Lead** (Robot + VEXcode)

**Owns**: Everything that runs on the VEX V5 Brain.

**Week 1 deliverables:**
- Physical assembly of the Clawbot (or Speedbot Gen 0 → Clawbot Gen 1)
- VEXcode Python: `grab()`, `pull()`, `throw()` task primitives
- Task Telemetry Contract JSON emission: `sys.stdout.write(json.dumps(contract) + '\n')` after each primitive
- USB serial link validated (Brain → Pi at 115200 baud)
- SD card fallback (`brain.sdcard.is_inserted()`)

**Week 2 deliverables:**
- Multi-generation physical runs (Gen 0 → Gen 1 → Gen 2 based on self-model revisions)
- Support for visual contract fields if Pi vision is ready
- Stage 2 PROS migration (optional — only if time permits)

**Minimum shippable**: Robot performs grab/pull/throw and emits 3 telemetry JSONs per run over USB serial.

---

### **Person B — Infrastructure Lead** (Raspberry Pi + Pipeline + API)

**Owns**: Everything that runs on the Pi — data ingest, storage, and LLM transport.

**Week 1 deliverables:**
- Pi 5 OS + Python environment setup
- pyserial receiver on `/dev/ttyACM0` → append to `session_YYYYMMDD_HHMMSS.jsonl`
- Mock test: read pre-saved `.jsonl` and confirm JSONL format and flush
- `anthropic.messages.create()` Mode A integration — given a contract JSON, call Claude and return revised self-model
- Error handling: serial drop → try/except; API timeout → 10s timeout + retry

**Week 2 deliverables:**
- Vision pipeline: USB webcam → OpenCV → YOLO11n → AprilTag → visual observation fields merged into contract JSON
- Mode B batch API (`anthropic.messages.batches.create()`) as optional post-run cost reducer
- `rsync` or DigitalOcean Spaces sync for archive (optional)

**Minimum shippable**: Pi receives serial stream from Brain, writes JSONL, and calls Claude with each contract, receiving a revised self-model JSON back.

---

### **Person C — AI Core Lead** (Self-Model + Critic + Gap Analysis)

**Owns**: All LLM prompt engineering, structured output schemas, and the revision loop logic.

**Week 1 deliverables:**
- Typed Assembly Grammar catalog JSON: all VEX V5 Starter Kit parts with physical specs (torque, reach, mass, gear ratios)
- Self-model JSON Schema (structural + capability + predictive layers)
- LLM Generator system prompt: given parts catalog + task spec + prior gap contracts → author self-model
- Multi-LLM Critic Panel: 3–4 critic prompts, each targeting a specific failure mode (CoM, torque budget, sensor occlusion, step geometry)
- Tested against mock Task Telemetry Contract JSONs (no hardware needed)

**Week 2 deliverables:**
- Gap analysis logic: mapping each gap residual field to the specific self-model parameter to revise (per the PID gap interpretation table in `task-telemetry-contract.md`)
- Generation history / lineage: save each generation's self-model with its gap inputs
- Readable prose evolution output: the narrative that changes visibly across Gen 1→2→3 for the demo

**Minimum shippable**: Given a hand-crafted telemetry contract JSON, the system produces a Gen 1 self-model, Critic panel attacks produce 1–2 revisions, and a Gap-informed Gen 2 self-model differs from Gen 1 in at least one parameter.

---

### **Person D — Simulation + Demo + Integration Lead**

**Owns**: Digital twin, end-to-end integration testing, Deliverable 01, and the live showcase.

**Week 1 deliverables:**
- **Deliverable 01** (Project Planning Document) — written and submitted by June 17 EOD
- PyBullet environment setup: 2D workspace, rigid body physics
- URDF generation: given a typed assembly grammar config (e.g., `drive_module×2 + chassis_rail + claw_module`), output a valid URDF
- Sim validation of at least Gen 0 (Speedbot) and Gen 1 (Clawbot) configs

**Week 2 deliverables:**
- Integration: end-to-end smoke test of full pipeline (mock data → pipeline → self-model → critic → revised model → sim validation)
- Demo script: scripted 10-minute showcase walkthrough with talking points per step
- Visualization: self-model prose evolution printout / slide per generation
- Rehearsal on June 27–28; final run on June 29

**Minimum shippable**: Deliverable 01 submitted; PyBullet sim runs for Gen 0 config; demo script written and rehearsed.

---

## Week-by-Week Plan

### Week 1 (June 17–22): Build in Parallel

| Day | Person A | Person B | Person C | Person D |
|-----|----------|----------|----------|----------|
| 17 | Assemble robot | Pi OS + pyserial setup | Grammar catalog JSON | **Submit Deliverable 01** |
| 18 | VEXcode grab() | JSONL logger + mock test | Self-model JSON Schema | PyBullet install + basic sim |
| 19 | VEXcode pull() + throw() | Claude API Mode A test | LLM Generator prompt | URDF for Gen 0 (Speedbot) |
| 20 | USB serial validated | Pipeline end-to-end (mock) | Critic panel prompts (×4) | URDF for Gen 1 (Clawbot) |
| 21 | Telemetry contracts emitting | Live serial from robot | Gap analysis logic | Sim validation both configs |
| 22 | **Milestone A**: robot emits 3 contract JSONs over USB | **Milestone B**: pipeline receives + calls Claude | **Milestone C**: Gen 1 self-model + 1 Critic revision | **Milestone D**: 2 configs simulated + demo outline |

### Week 2 (June 23–29): Close the Loop

| Day | Focus |
|-----|-------|
| 23–24 | Integration: real serial → pipeline → Claude → self-model update (first live end-to-end run) |
| 25 | Multi-generation runs: Gen 0→1→2 with gap-informed revisions, capture prose evolution |
| 26 | Vision layer (B adds YOLO/AprilTag), Sim validates Gen 2 design (D), Gap analysis tuning (C) |
| 27 | Demo rehearsal — full 10-minute run with real data |
| 28 | Buffer: fix any blocking issues, polish self-model prose output |
| 29 | **Showcase: Deliverable 02** |

---

## Critical Path and Risks

| Risk | Owner | Mitigation |
|------|-------|-----------|
| Robot assembly takes >2 days | A | Use mock JSONL for B+C development; unblock pipeline day 1 |
| VEXcode serial timing issues | A | Test USB serial before writing task code; use SD fallback |
| Claude API rate limit during demo | B | Cache last revision result; use Mode B batch for rehearsal |
| Critic panel too permissive / never revises | C | Tune prompts week 1; target specific numeric thresholds |
| Sim validation toolchain (PyBullet URDF) blocked | D | Fall back to static visualization if PyBullet stalls |
| Hardware singleton (one robot) | A | Coordinate with D for sim — never block showcase on hardware |

---

## Next Steps

- `/task-add` four tasks: one per workstream (A, B, C, D)
- `/roadmap-create` a 12-day roadmap with Week 1 milestone checkpoints per member
- Submit Deliverable 01 today (June 17, due 11:59PM) — Person D should own this immediately
- Share the Task Telemetry Contract JSON schemas with all four members as the shared API contract on Day 1
