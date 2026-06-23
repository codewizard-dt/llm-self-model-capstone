# Program — `self-model-loop`  *(APPROVED 2026-06-22)*

> **Source brief:** [`MASTER_REQUIREMENTS.md`](../../../MASTER_REQUIREMENTS.md) (decision-closed authoritative source).
> This file is the **program requirements** the engine plans from; it condenses the brief into the
> program tier (whole sub-features + milestone gates). Where this disagrees with the brief, the brief wins.
> **Status: APPROVED** — all 8 Decisions below are closed; `pipeline.yaml` emitted + validated (27 nodes, 47 edges).

## Goal

Close the generational self-model loop **in software** across the offline verticals
(`contracts`, `operator`, `coprocessor`, `brain`): `brain` emits the telemetry contract, `coprocessor`
merges telemetry + vision into `session_*.jsonl` through swap-in adapters, `operator` runs the Generator
+ Critic panel + gap analysis to revise the self-model, and `contracts` holds the frozen schemas every
vertical imports. Demonstrate **monotonically tightening gap residuals across ≥2 generations
(Gen 0 → Gen 2)** for the grab primitive (Gen 0/1 recorded, Gen 2 live), and expand to the full physical
loop by **replacing an adapter implementation only** — no contract change. A second, **required** loop
(`pilot`, ADR-19) puts an on-Pi LLM in real-time control behind the same frozen control grammar
(deadline risk accepted — see D3).

## Sub-features  *(each → its own `ai-sdd-plan` into `.ai-sdd/features/<slug>/`)*

`F#` = stable brief id. **Owner** is the node owner carried on the master graph; `TBD` nodes inherit
their vertical lead at runtime (ADR-0027). Erick is fixed by ADR-18.

| # | id | feature slug | vertical | one-line goal | owner |
|---|----|--------------|----------|---------------|-------|
| 1 | F1 | `telemetry-contract` | contracts | freeze predicted/observed/gap/vision JSON line | **Erick** |
| 2 | F2 | `self-model-schema` | contracts | freeze versioned 4-layer + reasoning self-model | **Erick** |
| 3 | F3 | `parts-catalog-grammar` | contracts | freeze `parts_catalog.json` vocabulary + valid-config rules | TBD |
| 4 | F4 | `adapter-interfaces` | contracts | `TelemetrySource`/`VisionSource` protocols | TBD |
| 5 | F19 | `control-grammar` | contracts | freeze `control-command` vocabulary + command/ack (draft) | TBD |
| 6 | F14 | `synthetic-oracle` | contracts | hidden-ground-truth `SyntheticTelemetrySource` | **Erick** |
| 7 | F15 | `replay-source` | contracts | `Replay` telemetry/vision readers over recorded sessions | TBD |
| 8 | F10 | `gap-analyzer` | operator | compute signed residuals from contract lines | TBD |
| 9 | F9 | `critic-panel` | operator | 3 stateless pre-build critics, pass/flag + rationale | TBD |
| 10 | F8 | `generator` | operator | author Gen 0; revise Gen N+1 from gap residuals | TBD |
| 11 | F11 | `markdown-presenter` | operator | gap tables + self-model diff + reasoning | TBD |
| 12 | F12 | `demo-replay` | operator | `make demo` deterministic Gen 0 → Gen 2 | TBD |
| 13 | F5 | `vision-pipeline` | coprocessor | YOLO11n + AprilTag → vision block | TBD |
| 14 | F6 | `serial-bridge-merge` | coprocessor | merge telemetry + vision → `session_*.jsonl` | TBD |
| 15 | F7 | `brain-telemetry-firmware` | brain | PROS C++ emits the contract on a 20 ms tick | TBD |
| 16 | F17 | `live-hw-sources` | coprocessor | `SerialTelemetrySource` + `CameraVisionSource` | TBD |
| 17 | F16 | `hw-baseline-capture` | coprocessor+brain | capture one real baseline; deliver JSONL to Erick | TBD |
| 18 | F18 | `oracle-baseline-request` | contracts | spec capture format; recalibrate the oracle | **Erick** |
| 19 | F20 | `brain-command-bridge` | brain | bidirectional PROS C++ (receive cmd + ack + watchdog) | TBD |
| 20 | F21 | `online-control-harness` | pilot | on-Pi LLM real-time control loop | TBD |

> **F13 `aesthetic-vocabulary` deleted** — robot aesthetics are out of scope entirely (Decision D2).

## Milestones  *(all MANUAL human gates — critical merge checkpoints)*

| id | validates | gate | owner |
|----|-----------|------|-------|
| `m1` contracts-frozen | every contract loads + round-trips (telemetry, self-model, parts-catalog, draft control-command) | gates ALL downstream work | **Erick** |
| `m1b` oracle-ready | parametric `SyntheticTelemetrySource` emits contract-valid synthetic telemetry, hidden params separated from the Generator | gates `demo-replay` / m2 | **Erick** |
| `m2` loop-closes-synthetic | `make demo` runs the offline loop over synthetic JSONL; gap residuals tighten Gen 0 → Gen 2 | gates hardware integration (m4) | TBD |
| `m3` vision-integrated | vision pipeline emits a valid `vision` block (`bbox_iou` + AprilTag pose) into merged JSONL | gates m4 | TBD |
| `m4` hw-capture + grounding | real V5 + Pi baseline captured, oracle recalibrated, a recorded session replaces a synthetic fixture (replay green) | gates m5 | TBD (capture) → **Erick** (calibrate) |
| `m5` demo-signoff | Gen 0/1 recorded + Gen 2 live rehearsed end-to-end with a recorded fallback ready | gates m6 | **Erick** |
| `m6` online-control *(required — ADR-19; deadline risk accepted)* | `pilot` harness drives an open-ended task in real time, bounded + interruptible | terminal | TBD |

## Sequencing  *(master dependencies — transcribed from the brief's Sequencing graph)*

- **→ m1:** F1, F2, F3, F4, F19 → **m1**
- **m1 →:** F14, F15, F5, F7, F9, F10, F17
- **Offline loop:** F1→F10→F8; F2→F8; F3→F8; F2→F11; F10→F11; (F8, F9, F11, F14, F15)→F12; F14→**m1b**→F12; **F12→m2**
- **Vision/merge:** F5→F6; F17→F6; (F5, F6)→**m3**
- **Hardware grounding:** (F7, F6, F17)→F16→F18; F14→F18; F18→**m4**; (m2, m3)→**m4**
- **Demo:** (F12, m4)→**m5**
- **Online (required):** F19→F20; F7→F20; F20→F21; (F5, F6)→F21; (m5, F21)→**m6**

## Constraints  *(shared non-negotiables — full text in the brief's Constraints section)*

- **Frozen contracts** (frozen at m1; canonical copies in `contracts/`): Task Telemetry Contract,
  Self-Model Schema, Parts Catalog Grammar, plus the draft Control-Command grammar.
- **Toolchain:** Python 3.11/3.12 · `uv` (no pip/poetry) · `ruff` (no black/isort/flake8) on the Python
  verticals; **PROS C++** on `brain` (arm-none-eabi; `uv`-managed `pros-cli` dev-only).
- **Adapter boundary:** the MVP depends only on `TelemetrySource`/`VisionSource` interfaces in
  `contracts`, never a concrete provider; live hardware is an implementation swap, not a redesign.
- **Oracle information separation (non-negotiable):** the oracle's true parameters are hidden from the
  Generator; gap-tightening must come from the self-model converging on hidden truth, not steering.
- **No schema defined outside `contracts`.**
- 19 closed ADRs (ADR-01…ADR-19) carry over from the brief unchanged.

## Decisions  *(propose → close WITH the human; only approved items become `closed`)*

| id | decision | resolution | status |
|----|----------|------------|--------|
| D1 | Milestone kind | **All 7 milestones are MANUAL human gates** (critical merge checkpoints). Each milestone node uses `milestone-gate` (workerKind `human`) + `validation-result.structure`. | ✅ confirmed |
| D2 | F13 aesthetic-vocabulary | **Deleted entirely** — robot aesthetics out of scope; removed from the brief and this plan. | ✅ confirmed |
| D3 | Online-control chain | **Required** — F19→F20→F21 + m6 are in the master graph gated behind m5; **deadline risk explicitly accepted** (ADR-19). | ✅ confirmed |
| D4 | Program slug | `self-model-loop`. | ✅ confirmed |
| O1 | Owner assignment | Keep **Erick** on `contracts` (closed via ADR-18); all other owners **TBD**, slices inherit the vertical lead (ADR-0027). | ✅ confirmed |
| O2 | "Gap tightened" definition | Generator's estimate of the oracle's hidden parameter recovered within **≤10%** across ≥2 generations; finalize the band at m1b once the oracle is calibrated. | ✅ confirmed |
| O3 | Grounded re-run | **Required** — the demo presents **grounded** results: m4 (real baseline capture F16 + oracle recalibration F18) must complete before m5. Ungrounded-synthetic is no longer an acceptable demo state. | ✅ confirmed |
| O4 | Critical-path split | When owners are assigned, **keep F5 (vision) and F7 (brain firmware) on different people** so the two critical-path items run in parallel. | ✅ confirmed |

> **Deadline note (D3 + O3).** Both confirmations push hardware onto the critical path for the
> **2026-06-29** demo: O3 makes m4 (real V5 + Pi capture, F16) a hard prerequisite of demo-signoff, and
> D3 adds the online-control tail (F20/F21/m6) after m5. The recorded-JSONL fallback (R1) still covers a
> live failure *during* the demo, but it no longer substitutes for the grounded capture itself.

## Honest edges (carried from the skill)

- Program requirements are markdown (no structured gate yet).
- The master graph is hand-emitted in Step 3 after approval; the engine validates + executes it.
- Milestone worker/check are copied into this program dir by convention.
- A failed milestone self-reworks (re-validate); it does not yet route rework into the specific upstream
  feature that fell short (ADR-0028, future work).
