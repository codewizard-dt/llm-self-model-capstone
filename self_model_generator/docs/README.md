# Self-Model Generator Docs

The `self_model_generator` vertical owns the offline self-model loop:

- Generator: authors Gen 0 and revises Gen N+1 from contract evidence.
- Critic panel: stateless pre-build review of candidate self-models.
- Gap analyzer, presenter, and demo replay: turn contract evidence into readable iteration history.

All durable schemas stay in `contracts/`. Self-model-generator docs may describe
packets, prompts, and workflows, but they must import or reference `contracts`
models instead of redefining telemetry or self-model JSON shapes. Do not create
or reference a repo-root `operator/` vertical for this offline loop; `operator`
is reserved for live robot-control code under `robot/ros2-runtime/`.

- [LLM/Critic Architecture](llm_critic_architecture.md)

## Self-Improving Telemetry Loop

The first executable bridge is:

```text
run robot
-> record operator telemetry
-> export/read ContractLine JSONL
-> build F10 gap summary
-> build self-model packet
-> deterministic Generator emits a candidate SelfModel
-> deterministic 3-critic panel reviews it
-> approved candidate exports the next TaskEnvelope
-> human reviews and sends the task to the Pi
```

Telemetry by itself is only memory. The loop becomes useful when the
`ContractLine` evidence is turned into a gap summary and then into a self-model
packet that the Generator/Critic workflow can review. The implementation writes
all repo-local artifacts for that loop; it still does not redeploy robot
behavior without a human/safety gate.

From the repo root, fixture proof:

```bash
make full-loop \
  CONTRACT_JSONL=contracts/fixtures/session_example.jsonl \
  OUT_DIR=/tmp/vexy-full-loop-fixture \
  PROVENANCE=fixture
```

Live run shape after telemetry sync:

```bash
make sync-telemetry
make full-loop \
  CONTRACT_JSONL=telemetry/<run>/operator_results.jsonl \
  OUT_DIR=/tmp/vexy-full-loop-<run> \
  PROVENANCE=live \
  RUN_ID=<run_id> \
  SESSION_ID=<session_id>
make send-task FILE=/tmp/vexy-full-loop-<run>/task_envelope.json
```

The final `send-task` command is intentionally separate. A successful full-loop
run means the next task is contract-valid and critic-approved; it does not mean
the robot has been redeployed automatically.

The runner writes these artifacts into `OUT_DIR`:

- `gap_summary.json`
- `self_model_packet.md`
- `candidate_self_model.json`
- `generator_handoff.json`
- `critic_report.json`
- `task_envelope.json`
- `manifest.json`

The full-loop entrypoint is `self_model_generator.loop_runner` and the lower
level closure harness lives in `self_model_generator.loop_closure`:

- `generate_self_model_candidate(...)` emits a revised `contracts.SelfModel`.
- `run_critic_panel(...)` runs physics, torque, and CoM/geometry reviews.
- `export_task_envelope(...)` creates the next robot-facing `TaskEnvelope` only
  after critic approval.
- `run_full_loop(...)` builds the fresh gap summary, packet, candidate, critic
  report, task envelope, and manifest in one deterministic run.

## Successful Run Requirements

A live full loop is successful only when all of these are true:

1. The Pi is reachable and fresh telemetry has been synced locally.
2. The input JSONL is the `/operator/results` ContractLine-compatible file for
   the intended run.
3. Every ContractLine in live mode carries the same `run_id`.
4. Every ContractLine in live mode carries `source.raw_session_path`.
5. The gap summary is freshly built from that JSONL in the current command.
6. The source summary names one run/session and preserves raw hardware paths.
7. The generated `SelfModel` advances exactly one generation and points back to
   the previous generation.
8. The critic report contains `physics`, `torque`, and `com_geometry`.
9. The critic report is approved before `task_envelope.json` is written.
10. The exported `TaskEnvelope` validates against `contracts.TaskEnvelope`.
11. `manifest.json` records all input paths, output paths, source metadata,
    generation metadata, and critic approval.
12. A human reviews the artifacts before `make send-task`.

For live robot runs, use the JSONL written from `/operator/results` as the
`--contract-jsonl` input. The analyzer currently diagnoses:

- `PICKUP_ADVANCED_BEFORE_GRAB`
- `OBJECT_NOT_CONFIRMED`
- `BALL_STILL_VISIBLE_AFTER_GRAB`

It also preserves numeric residual keys such as `force_error_N` and
`duration_error_s`, so the Generator can revise `predictive` and `gap_model`
without renaming the evidence.

Approved changes still need the safety gate. The analyzer recommends known
runtime knobs like `pickup_grab_settle_s`, `ball_capture_forward_m`,
`ball_capture_lateral_m`, `pickup_max_attempts`, and
`end_effector_object_max_closed_deg`; it does not redeploy robot behavior by
itself.
