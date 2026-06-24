# adapter-interfaces — Requirements

| Field | Value |
|---|---|
| Feature ID | F4 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · reactivex · stdlib typing only |
| Depends on | F1 telemetry-contract (frozen — `ContractLine`, `VisionBlock` in `contracts/src/contracts/contract_line.py`) |
| Unblocks | F14 synthetic-oracle · F15 replay-source · F17 live-hw-sources · F5 vision-pipeline · F6 serial-bridge-merge · F21 online-control-harness |

---

## Goal

Define `TelemetrySource` and `VisionSource` as `@runtime_checkable` Python `Protocol` types
whose single method — `observe()` — returns a `reactivex.Observable` stream of typed records.
These are the swap-in boundaries that decouple every consumer of telemetry and vision data from
any concrete source. With these two interfaces frozen, all downstream verticals compose reactive
pipelines against the abstract protocol; swapping between Synthetic, Replay, Serial, or Camera
implementations is a single config-flag change with zero pipeline change. Exhaustion is
`on_completed`, errors are `on_error` — both are first-class signals in the stream. This
mechanically enforces ADR-01.

---

## In scope

- `contracts/src/contracts/adapters.py` — two `@runtime_checkable` `typing.Protocol` classes:
  - `TelemetrySource` — one method: `observe(self) -> Observable[ContractLine]`
  - `VisionSource` — one method: `observe(self) -> Observable[VisionBlock]`
  - Both element types imported from `contracts.contract_line`; `Observable` imported from `reactivex`
- `contracts/src/contracts/__init__.py` extended additively — add `TelemetrySource`, `VisionSource` to imports and `__all__`; all existing exports unchanged
- `reactivex` added to `contracts/pyproject.toml` via `uv add reactivex`
- `contracts/tests/test_adapters.py` — conformance tests (pure in-memory, no I/O):
  - `isinstance` conformance: pass cases for both protocols, fail cases (missing `observe`)
  - Non-overlap: a class implementing only `TelemetrySource` does not satisfy `VisionSource`
  - Smoke test: minimal cold `TelemetrySource` emits one fixture `ContractLine` then `on_completed`; `on_next` receives the record and `on_completed` fires
  - F1 and F2 regression: existing test suites still pass

## Out of scope

- All concrete implementations: `SyntheticTelemetrySource` (F14), `ReplayTelemetrySource` / `ReplayVisionSource` (F15), `SerialTelemetrySource` / `CameraVisionSource` (F17)
- `ContractLine` and `VisionBlock` definitions — owned by F1, already landed; never redefined here
- Control grammar / control-command adapter interfaces (F19)
- F2 self-model schema, F3 parts catalog grammar
- `Subject` implementations, schedulers, or any Rx operator usage — belong in concrete adapter implementations and pipeline consumers, not in this protocols module
- JSON Schema output — protocols have no serializable artifact; `make schema` not extended
- `make validate` extension — no data fixtures
- Any modification to `contract_line.py`, `self_model.py`, `vocabulary.py`, `motor_telemetry.py`, `schema.py`, `validate.py`, or any committed schema/fixture file

---

## Acceptance

Each item independently runnable from `contracts/` (or repo root, which delegates):

1. `make sync` exits 0 — `reactivex` resolves and installs
2. `make lint` exits 0 — `ruff check` + `ruff format --check` clean
3. `make test` exits 0, covering:
   - `isinstance` conformance pass/fail for `TelemetrySource` and `VisionSource`
   - Non-overlap check
   - Smoke test: cold `TelemetrySource` emits one `ContractLine` + `on_completed`
   - F1 and F2 suites still passing (regression guard)
4. `from contracts import TelemetrySource, VisionSource` resolves cleanly in `uv run python` after `make sync`
5. Root `make sync` / `make test` / `make lint` delegate correctly and exit 0; F1/F2/F3 suites unaffected

---

## Constraints

- Python 3.12 (`requires-python = ">=3.12,<3.13"`) · uv · ruff — no pip/poetry/black/flake8 (ADR-05, ADR-15, ADR-16)
- Build entry is `make sync` (the routed build gate per F1 D7)
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`
- `reactivex` is the **only** new dep added by F4; pinned via `uv add reactivex`
- Protocols use **`typing.Protocol` + `@runtime_checkable`** from stdlib; `Observable` imported from `reactivex` for return-type annotation only
- `ContractLine` and `VisionBlock` imported from `contracts.contract_line`; never redefined
- **Additive only:** `adapters.py` is new; `__init__.py` gains two exports; no existing file modified beyond that
- No `Subject`, schedulers, or operators in `adapters.py` — pure Protocol + return-type annotation

---

## Decisions

| # | Decision | Resolution | Status |
|---|---|---|---|
| D1 | Interface model: discrete vs Observable stream | `reactivex.Observable` stream. The pipeline is reactive end-to-end (20ms hot ticks, hot camera frames, zip/buffer/flat_map operators). Exhaustion is `on_completed`; errors are `on_error`. | `closed` |
| D2 | Protocol mechanism | `typing.Protocol` + `@runtime_checkable`. No ABC, no registration. | `closed` |
| D3 | Lifecycle / resource management | Not part of the protocol. Concrete implementations manage open/close/teardown; callers unsubscribe via `Disposable`. | `closed` |
| D4 | `VisionBlock` nullability in the stream | `Observable[VisionBlock]`, never `Observable[VisionBlock \| None]`. No-detection emits a sentinel `VisionBlock(object_detected=False, ...)`; callers check `item.object_detected`. | `closed` |
| D5 | Hot vs cold Observable | Cold for `Replay`/`Synthetic`; hot (via `Subject`) for `Serial`/`Camera`. Correctness constraint for F14/F15 (cold) and F17 (hot). Not an F4 implementation concern — documented here so downstream features implement correctly. | `closed` |

---

## Coordination notes

- **C1 — F14, F15:** must return cold Observables (emit only on subscribe, complete with `on_completed`)
- **C2 — F17:** must bridge push sources to the Observable world via `Subject`; scheduler is an F17 decision
- **C3 — F6:** merge step becomes `rx.zip(telemetry.observe(), vision.observe()).pipe(...)`; zip strategy is an F6 decision
- **C4 — F21:** online control loop is a natural Rx pipeline consuming these Observables directly
