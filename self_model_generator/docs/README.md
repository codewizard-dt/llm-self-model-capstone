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
```

Telemetry by itself is only memory. The loop becomes useful when the
`ContractLine` evidence is turned into a gap summary and then into a self-model
packet that the Generator/Critic workflow can review. The current implementation
closes the repo-local artifact loop; it still does not redeploy robot behavior
without a human/safety gate.

From `self_model_generator/`:

```bash
PYTHONPATH=src:../contracts/src:../robot/ros2-runtime/src \
  uv run python -m self_model_generator.gap_analyzer \
  ../contracts/fixtures/session_example.jsonl \
  --out /tmp/gap_summary.json
```

Then build the packet:

```bash
PYTHONPATH=src:../contracts/src:../robot/ros2-runtime/src \
  uv run python -m self_model_generator.packet_builder \
  --self-model ../contracts/fixtures/self_model_gen0.json \
  --parts-catalog ../contracts/parts_catalog.json \
  --contract-jsonl ../contracts/fixtures/session_example.jsonl \
  --gap-summary /tmp/gap_summary.json \
  --human-constraint "critic and human review required before deploy" \
  --out /tmp/self_model_packet.md
```

The repo-local closure harness lives in `self_model_generator.loop_closure`:

- `generate_self_model_candidate(...)` emits a revised `contracts.SelfModel`.
- `run_critic_panel(...)` runs physics, torque, and CoM/geometry reviews.
- `export_task_envelope(...)` creates the next robot-facing `TaskEnvelope` only
  after critic approval.

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
