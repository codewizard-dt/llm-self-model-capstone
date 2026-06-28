# Full Working Telemetry Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one deterministic command that turns contract-valid robot telemetry into a gap summary, generator packet, revised `SelfModel`, critic report, approved `TaskEnvelope`, and manifest.

**Architecture:** Reuse the existing `gap_analyzer`, `packet_builder`, and `loop_closure` modules instead of inventing new schemas. The new runner is an orchestration layer with hard success gates: live evidence must have run identity and hardware source paths, critics must approve before export, and every generated artifact must validate through `contracts`.

**Tech Stack:** Python 3.12, Pydantic contracts, existing `uv` test/lint workflow, `make` targets.

---

## Success Contract

A full loop run is successful only when all of these are true:

1. The input ContractLine JSONL exists, parses, and contains at least one line.
2. The gap summary is freshly built from that input in the same run, not copied from an older file.
3. For `--provenance live`, every ContractLine carries a single `run_id`.
4. For `--provenance live`, every ContractLine carries `source.raw_session_path`; otherwise the telemetry is memory, not hardware proof.
5. The generated `SelfModel` has `generation = current.generation + 1` and `parent_generation = current.generation`.
6. The critic panel includes exactly `physics`, `torque`, and `com_geometry`.
7. The critic panel approves before a task is exported.
8. The exported `TaskEnvelope` validates against `contracts.TaskEnvelope`.
9. The output directory contains `gap_summary.json`, `self_model_packet.md`, `candidate_self_model.json`, `generator_handoff.json`, `critic_report.json`, `task_envelope.json`, and `manifest.json`.
10. `manifest.json` records the input paths, output paths, run/session/generation metadata, critic approval, and next task path.

## File Structure

- Create `self_model_generator/src/self_model_generator/loop_runner.py`: one orchestration function plus CLI.
- Create `self_model_generator/tests/test_loop_runner.py`: fixture-backed happy path and live-proof failure tests.
- Modify `self_model_generator/src/self_model_generator/__init__.py`: lazy-export `run_full_loop`.
- Modify `self_model_generator/src/self_model_generator/validate.py`: validate the runner on committed fixtures.
- Modify `self_model_generator/Makefile`: add `loop` target.
- Modify root `Makefile`: add `full-loop` target delegating into `self_model_generator`.
- Modify `self_model_generator/docs/README.md`: document the command, success contract, and live run prerequisites.

### Task 1: Full-Loop Runner Tests

**Files:**
- Create: `self_model_generator/tests/test_loop_runner.py`

- [ ] **Step 1: Write failing tests**

Add tests that call `run_full_loop(...)` and assert artifact creation, manifest metadata, candidate generation, critic approval, and validated task envelope. Add a live-provenance test where a ContractLine lacks `source.raw_session_path`; it must raise `ValueError("raw_session_path")`.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd self_model_generator
PYTHONPATH=src:../contracts/src:../robot/ros2-runtime/src uv run pytest tests/test_loop_runner.py -v
```

Expected: FAIL because `self_model_generator.loop_runner` does not exist.

### Task 2: Runner Implementation

**Files:**
- Create: `self_model_generator/src/self_model_generator/loop_runner.py`
- Modify: `self_model_generator/src/self_model_generator/__init__.py`

- [ ] **Step 1: Implement `run_full_loop(...)`**

The function must:

1. Load `SelfModel`, `PartsCatalog`, and ContractLine JSONL.
2. Build a fresh gap summary with `build_gap_summary_from_jsonl`.
3. Enforce full-loop requirements, especially live `run_id` and `source.raw_session_path`.
4. Write `gap_summary.json`.
5. Build and write `self_model_packet.md`.
6. Generate and write `candidate_self_model.json`.
7. Write `generator_handoff.json`.
8. Run critics and write `critic_report.json`.
9. Export and write `task_envelope.json` only when approved.
10. Write `manifest.json`.

- [ ] **Step 2: Add CLI**

Expose:

```bash
python -m self_model_generator.loop_runner \
  --self-model ../contracts/fixtures/self_model_gen0.json \
  --parts-catalog ../contracts/parts_catalog.json \
  --contract-jsonl ../contracts/fixtures/session_example.jsonl \
  --out-dir /tmp/vexy-loop \
  --provenance fixture
```

- [ ] **Step 3: Export the function**

Add `run_full_loop` to `self_model_generator.__all__` via the existing lazy export pattern.

- [ ] **Step 4: Run tests**

Run:

```bash
cd self_model_generator
PYTHONPATH=src:../contracts/src:../robot/ros2-runtime/src uv run pytest tests/test_loop_runner.py -v
```

Expected: PASS.

### Task 3: Validation and Make Targets

**Files:**
- Modify: `self_model_generator/src/self_model_generator/validate.py`
- Modify: `self_model_generator/Makefile`
- Modify: `Makefile`

- [ ] **Step 1: Add validation fixture**

`validate.py` must call `run_full_loop(...)` into a temporary directory using the committed fixture ContractLine JSONL and assert the returned manifest points to a real task file.

- [ ] **Step 2: Add make targets**

Add `self_model_generator/Makefile` target:

```make
loop:
	@test -n "$(CONTRACT_JSONL)" || (echo "usage: make loop CONTRACT_JSONL=path/to/contract.jsonl OUT_DIR=path/to/out [PROVENANCE=live] [RUN_ID=run-id]" >&2; exit 2)
	$(UV) python -m self_model_generator.loop_runner ...
```

Add root `Makefile` target:

```make
full-loop:
	$(MAKE) -C self_model_generator loop ...
```

- [ ] **Step 3: Run validation**

Run:

```bash
make -C self_model_generator validate
```

Expected: PASS.

### Task 4: Documentation

**Files:**
- Modify: `self_model_generator/docs/README.md`

- [ ] **Step 1: Document the exact commands**

Add the fixture proof command and the live command:

```bash
make sync-telemetry
make full-loop CONTRACT_JSONL=telemetry/<run>/operator_results.jsonl OUT_DIR=artifacts/full-loop/<run> PROVENANCE=live RUN_ID=<run>
make send-task FILE=artifacts/full-loop/<run>/task_envelope.json
```

- [ ] **Step 2: Document success prerequisites**

List the ten success requirements above in plain English.

### Task 5: Final Verification

**Files:**
- All modified files

- [ ] **Step 1: Run focused tests**

```bash
cd self_model_generator
PYTHONPATH=src:../contracts/src:../robot/ros2-runtime/src uv run pytest tests/test_loop_runner.py tests/test_loop_closure.py tests/test_gap_analyzer.py -q
```

- [ ] **Step 2: Run self-model validation/lint**

```bash
make -C self_model_generator validate
make -C self_model_generator lint
```

- [ ] **Step 3: Run fixture full-loop command**

```bash
make full-loop CONTRACT_JSONL=contracts/fixtures/session_example.jsonl OUT_DIR=/tmp/vexy-full-loop-fixture PROVENANCE=fixture
```

Expected: output directory contains all required artifacts and command exits 0.

- [ ] **Step 4: Commit and push**

```bash
git add Makefile self_model_generator
git commit -m "Add full telemetry loop runner"
git push -u origin codex/full-working-telemetry-loop
```

---

## Known Baseline Issue

Root `make validate`, `make test`, and `make lint` currently fail when they delegate to `robot/ros2-runtime` because that subproject's `uv` environment defaults to Python `>=3.11`, while `contracts` requires `>=3.12,<3.13`. This plan does not edit robot runtime packaging; verify the self-model loop with explicit Python 3.12-compatible commands.
