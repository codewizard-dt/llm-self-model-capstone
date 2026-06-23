# telemetry-contract — Requirements

| Field | Value |
|---|---|
| Feature ID | F1 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Gates | `m1` contracts-frozen |
| Unblocks | F4 adapter-interfaces · F7 brain-telemetry-firmware · F10 gap-analyzer · F14 synthetic-oracle · F15 replay-source |

---

## Goal

Freeze the Task Telemetry Contract as the runtime source of truth for the `contracts/` vertical: ship pydantic v2 models that validate every `session_*.jsonl` line emitted by the coprocessor merge step, export a JSON Schema, and include one per-task JSONL fixture for grab, pull, throw, and score. Every downstream vertical imports from `contracts/` — this is the zero-dependency foundation that gates `m1`.

---

## In scope

- `contracts/` Python 3.12 package scaffolding: `pyproject.toml` (hatchling, pydantic v2 ≥2.12, pytest), `.python-version`, `ruff.toml`, src layout; `uv sync` completes cleanly
- `ContractLine` pydantic v2 model — envelope fields:
  - `schema_version: Literal["1.0"]`
  - `session_id: str`
  - `generation: int`
  - `round: int`
  - `task: str` — free string label, not an enum; no per-task schema enforcement
  - `motor_samples: list[MotorApiSample]` — strictly typed core (see below)
  - `predicted: dict[str, float | bool | str]` — self-model claims before execution; task-specific keys, no schema enforcement
  - `gap: dict[str, float]` — computed residuals after execution; task-specific keys, no schema enforcement
  - `outcome: dict[str, Any] | None = None` — task result (e.g. `ball_in_bin`, `success`); optional
  - `vision: VisionBlock | None = None` — absent on motor-only runs
  - `source: ContractSource | None = None` — capture provenance metadata; optional
- `MotorApiSample` — strictly typed, migrated from branch (`robot/pi-runtime/src/vexy_system2/contracts/motor_telemetry.py`):
  - `device: str`, `subsystem: Literal["claw","arm","drivetrain"]`, `sample_ms: int`, `api_binding: Literal["vexcode_python"]`
  - `values: MotorApiValues` — `position_deg`, `velocity_rpm`, `current_amp`, `power_w`, `torque_nm`, `efficiency_pct`, `temperature_c`
  - `source_api: dict[str, str]` — provenance: which VEXcode/PROS call produced each value; validated by model_validator
- `MotorApiValues`, `vexcode_motor_source_api()`, `motor_sample_from_vexcode()`, `motor_sample_from_pros()` — migrated from branch
- `VisionBlock`: `object_detected: bool` · `object_bbox: list[int] | None` · `apriltag_pose: AprilTagPose | None` · `bbox_iou: float | None`
- `ContractSource`: `raw_session_path: str | None` · `brain_start_ms: int | None` · `brain_end_ms: int | None` · `pi_received_ms: int | None` · `telemetry_sample_count: int` — migrated from branch
- JSON Schema export: `contracts/schemas/contract_line.json` generated via `model_json_schema()`; committed to the repo
- JSONL fixtures: `contracts/fixtures/session_example.jsonl` — 4 lines demonstrating grab, pull, throw, score tasks
- `contracts/Makefile` targets: `validate` · `test` · `lint` · `schema`
- Root `Makefile`: delegates `validate` / `test` / `lint` to `contracts/Makefile`; includes stubs for `operator`, `coprocessor`, `brain`, `pilot`

## Out of scope

- `TelemetrySource` / `VisionSource` adapter protocols (F4)
- `SyntheticTelemetrySource` oracle (F14)
- `ReplayTelemetrySource` / `ReplayVisionSource` (F15)
- Control grammar / `control-command` contract (F19)
- Self-model schema (F2), parts catalog grammar (F3)
- PROS C++ firmware that emits the contract (F7)
- Serial reading, hardware access, network calls
- Gap computation logic (F10)
- Per-task typed sub-models for `predicted` / `gap` / `outcome` (by decision D2)

---

## Acceptance

1. `cd contracts && uv sync` exits 0
2. `cd contracts && make lint` exits 0
3. `cd contracts && make schema` exits 0; `contracts/schemas/contract_line.json` is non-empty and committed
4. `cd contracts && make test` exits 0 — covers: `ContractLine` round-trip for all 4 task fixtures; `MotorApiSample` source_api validation (missing field → error, wrong call name → error); `VisionBlock` optional (present and absent); missing `session_id` → `ValidationError`; extra field on strict model → `ValidationError`
5. `cd contracts && make validate` exits 0 against all files in `contracts/fixtures/`
6. `from contracts import ContractLine, MotorApiSample, VisionBlock` works in `uv run python` after `uv sync`
7. Root `make validate` / `make test` / `make lint` delegate to `contracts/Makefile` and exit 0

---

## Constraints

- Python 3.12 · uv (`uv sync` / `uv add` / `uv run`) · ruff (`ruff check` / `ruff format`) · pydantic v2 — no pip, no poetry, no black, no flake8 (ADR-05, ADR-15, ADR-16)
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`
- `schema_version: Literal["1.0"]` is locked — bumping requires a new frozen contract approval
- pydantic v2 only: `model_config = ConfigDict(...)` style; no v1 compat shim
- `motor_samples` must have `min_length=1`; a contract line with no motor samples is invalid
- `task` is a free `str`, not an `enum` — adding a new task primitive never requires a schema change
- `predicted`, `gap`, `outcome` are flexible dicts — task-specific interpretation belongs in F10 (gap analyzer), not here
- `extra="forbid"` on `MotorApiSample` and `MotorApiValues`; `ContractLine` may use `extra="allow"` to stay forward-compatible with new top-level fields

---

## Decisions

| # | Decision | Resolution | Status |
|---|---|---|---|
| D1 | Pull/throw field sets | Superseded by D2. With flexible dict inner blocks there are no per-task field sets to define. Fixtures demonstrate grab, pull, throw, and score with concrete key names, but the schema does not enforce them. | `closed` |
| D2 | Inner block typing approach | **Typed `motor_samples` core + flexible dict edges.** `motor_samples: list[MotorApiSample]` is strictly typed (7 motor API fields per sample, source_api provenance). `predicted`, `gap`, `outcome` are flexible dicts — no per-task subtyping. Task-specific interpretation belongs in the gap analyzer (F10). Adding a new task never requires a schema change. | `closed` |
| D3 | Root Makefile ownership | **This feature creates the root `Makefile`** with contracts targets and no-op stubs for operator / coprocessor / brain / pilot. Subsequent features fill in their stubs. `make validate` at root is runnable immediately after F1 merges. | `closed` |
| D4 | Package layout | **src layout** (`contracts/src/contracts/`). Public API via `contracts/src/contracts/__init__.py` re-exporting `ContractLine`, `MotorApiSample`, `VisionBlock`. Stable import: `from contracts import ContractLine`. Build backend: hatchling (consistent with `robot/v5-brain/`). | `closed` |
| D5 | Migration vs rewrite | **Migrate, do not rewrite.** `MotorApiSample`, `MotorApiValues`, `StrictModel`, `ContractSource`, `vexcode_motor_source_api`, `motor_sample_from_vexcode`, `motor_sample_from_pros` are moved from `robot/pi-runtime/src/vexy_system2/contracts/motor_telemetry.py` into `contracts/src/contracts/motor_telemetry.py`. `ScoreContract` and `BaseTaskContract` are discarded (D2). Existing tests covering `MotorApiSample` are migrated and adapted. | `closed` |
