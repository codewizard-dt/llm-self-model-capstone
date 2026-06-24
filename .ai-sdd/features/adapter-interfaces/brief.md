# adapter-interfaces — Brief

| Field | Value |
|---|---|
| Feature ID | F4 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 · **reactivex** |
| Deps | F1 telemetry-contract **frozen** — `ContractLine` and `VisionBlock` (the Observable element types) are already defined in `contracts/src/contracts/contract_line.py` and exported from `contracts/__init__.py`. F4 imports them; it does not redefine them. |
| Gates | `m1` contracts-frozen |
| Unblocks | F14 synthetic-oracle · F15 replay-source · F17 live-hw-sources · F5 vision-pipeline · F6 serial-bridge-merge · F21 online-control-harness |
| Owner | TBD |

> Sources: [MASTER_REQUIREMENTS.md](../../../MASTER_REQUIREMENTS.md) (Components → "Adapter interfaces `(contracts)` — owns `TelemetrySource` and `VisionSource` protocol definitions that decouple the loop from hardware"; ADR-01; Integration Boundaries & Swap Paths; ADR-05/15/16). The whole project pipeline is reactive by nature — motors push hot 20ms ticks, camera pushes hot frames, the bridge zips and buffers them, gap residuals feed the LLM, and the online control loop reads live state to emit commands. `reactivex` is the right abstraction for the domain, not an over-engineering choice. The hot/cold split (D5) is the one correctness constraint that must be explicit in the brief so F17 implementers get it right.

---

## Goal

Define `TelemetrySource` and `VisionSource` as `@runtime_checkable` Python `Protocol` types whose single method — `observe()` — returns a `reactivex.Observable` stream of typed records. These are the swap-in boundaries that decouple every consumer of telemetry and vision data from any concrete source. With these two interfaces frozen, `operator`, `coprocessor`, and `pilot` compose reactive pipelines against the abstract protocol; swapping between `Synthetic`, `Replay`, `Serial`, or `Camera` implementations is a single config-flag change with zero pipeline change. Exhaustion is `on_completed`, errors are `on_error` — both are first-class signals in the stream, not exceptions the caller must separately handle. This mechanically enforces ADR-01 and gives every downstream vertical (`serial_bridge.py`, the gap analyzer, the online control loop) a uniform, composable stream primitive.

---

## In scope

- **`contracts/src/contracts/adapters.py`** — two `@runtime_checkable` `typing.Protocol` classes:
  - `TelemetrySource` — one method: `observe(self) -> Observable[ContractLine]`. A cold Observable for `Replay`/`Synthetic`; a hot Observable (via `Subject`) for `Serial`.
  - `VisionSource` — one method: `observe(self) -> Observable[VisionBlock]`. Same cold/hot split.
  - Both element types imported from `contracts.contract_line`; `Observable` imported from `reactivex`.
- **`contracts/src/contracts/__init__.py` extended additively** — add `TelemetrySource`, `VisionSource` to imports and `__all__`. All existing exports unchanged.
- **`reactivex` added to `contracts/pyproject.toml`** via `uv add reactivex`.
- **`contracts/tests/test_adapters.py`** — conformance tests (pure in-memory, no I/O):
  - A class implementing `observe(self) -> Observable[ContractLine]` passes `isinstance(obj, TelemetrySource)`.
  - A class missing `observe` fails the check.
  - A class implementing `observe(self) -> Observable[VisionBlock]` passes `isinstance(obj, VisionSource)`.
  - A class missing `observe` fails the check.
  - The protocols are non-overlapping: only-`TelemetrySource` class does not satisfy `VisionSource`.
  - Smoke test: a minimal cold `TelemetrySource` emitting one fixture `ContractLine` then completing delivers the record via `on_next` and fires `on_completed` — proves the Observable contract end-to-end.
  - F1 and F2 test suites still pass (regression guard).

## Out of scope

- All concrete implementations: `SyntheticTelemetrySource` (F14), `ReplayTelemetrySource` / `ReplayVisionSource` (F15), `SerialTelemetrySource` / `CameraVisionSource` (F17). F4 defines the contract; those features satisfy it.
- `ContractLine` and `VisionBlock` definitions — owned by F1, already landed. Redefining either here violates the "no schema outside `contracts`" boundary rule.
- Control grammar / `control-command` adapter interfaces (F19).
- Self-model schema (F2), parts catalog grammar (F3).
- `Subject` implementations, schedulers, or any Rx operator usage — those belong in concrete adapter implementations and pipeline consumers.
- JSON Schema output — protocols have no serializable artifact; `make schema` is not extended.
- `make validate` extension — no data fixtures.
- Any change to `contract_line.py`, `self_model.py`, `vocabulary.py`, `motor_telemetry.py`, `schema.py`, `validate.py`, or any committed schema/fixture file.

---

## Acceptance

Each item is independently runnable from `contracts/` (or repo root, which delegates):

1. `make sync` exits 0 (`reactivex` resolves and installs).
2. `make lint` exits 0 (`ruff check` + `ruff format --check`).
3. `make test` exits 0, covering:
   - `isinstance` conformance checks for `TelemetrySource` and `VisionSource` (pass and fail cases).
   - The protocols are non-overlapping.
   - Smoke test: minimal cold `TelemetrySource` emits one `ContractLine` + `on_completed`; `on_next` receives the record and `on_completed` fires.
   - F1 and F2 test suites still pass.
4. `from contracts import TelemetrySource, VisionSource` resolves cleanly in `uv run python` after `make sync`.
5. Root `make sync` / `make test` / `make lint` delegate correctly and exit 0; F1/F2/F3 suites unaffected.

---

## Constraints

- Python 3.12 (`requires-python = ">=3.12,<3.13"`) · uv · ruff — no pip/poetry/black/flake8 (ADR-05, ADR-15, ADR-16). Build entry is `make sync` (the routed build gate per F1 D7).
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- `reactivex` is the **only** new dep added by F4. Pin it in `contracts/pyproject.toml` via `uv add reactivex`.
- Protocols use **`typing.Protocol` + `@runtime_checkable`** from the stdlib. `Observable` is imported from `reactivex` for the return type annotation only.
- `ContractLine` and `VisionBlock` are imported from `contracts.contract_line`; never redefined here.
- **Hot/cold correctness (non-negotiable — see D5):** cold sources (`Replay`, `Synthetic`) must not start emitting until subscribed; hot sources (`Serial`, `Camera`) must bridge to a `Subject` so frames are not dropped between subscription and production. This is a documented constraint for F14/F15/F17, not an F4 implementation concern.
- **Additive only:** `adapters.py` is new; `__init__.py` gains two exports; no existing file is modified beyond that.
- No `Subject`, no schedulers, no operators in `adapters.py` — pure Protocol + return-type annotation.

---

## Decisions

| # | Decision | Resolution | Status |
|---|---|---|---|
| D1 | Interface model: discrete vs Observable stream | **`reactivex.Observable` stream.** The whole project pipeline is reactive: motors push hot 20ms ticks, camera pushes hot frames, the bridge zips and buffers, gap residuals feed the LLM, the online control loop is a real-time reactive loop. `zip`, `buffer`, `flat_map`, `take_until` are first-class pipeline primitives, not one-offs to hand-implement. Exhaustion is `on_completed`; errors are `on_error`. Discrete `read()` / `state()` are rejected. | `closed` |
| D2 | Protocol mechanism | **`typing.Protocol` + `@runtime_checkable`.** No ABC, no registration. | `closed` |
| D3 | Lifecycle / resource management | **Not part of the protocol.** Concrete implementations manage open/close/teardown. The protocol exposes exactly one method. Callers subscribe to the Observable; unsubscription (via `Disposable`) handles teardown at the Rx layer. | `closed` |
| D4 | `VisionBlock` nullability in the stream | **`Observable[VisionBlock]`, never `Observable[VisionBlock \| None]`.** When detection fails, the implementation emits a sentinel `VisionBlock(object_detected=False, ...)`. Callers check `item.object_detected`. `VisionBlock`'s optional inner fields absorb the no-detection state. | `closed` |
| D5 | Hot vs cold Observable | **Cold for `Replay`/`Synthetic`; hot (via `Subject`) for `Serial`/`Camera`.** Cold sources start emitting only on subscribe — correct for deterministic replay and synthetic generation. Hot sources (serial port, camera ISR) push frames independently of subscribers; a `Subject` bridges the push source into the Observable world so frames are not dropped. F14/F15 must implement cold; F17 must implement hot. This is a correctness constraint, not a preference. | `closed` |

---

## Milestones

F4 lands in a single slice.

| id | Validates | Mode | Owner |
|---|---|---|---|
| `s1` protocols-and-exports | `adapters.py` defines both protocols; `reactivex` dep resolves; `__init__.py` re-exports; `make lint` + `make test` green including smoke test; `from contracts import TelemetrySource, VisionSource` resolves; F1/F2/F3 suites passing | automated (`make lint`, `make test`) | TBD |
| (gate) `m1` contracts-frozen | All contracts (F1–F4, F19) load and round-trip cleanly | manual — human gate | TBD |

---

## Coordination items

- **C1 — F14, F15 (cold Observables).** `SyntheticTelemetrySource` and `ReplayTelemetrySource`/`ReplayVisionSource` must return cold Observables — emitting only on subscribe, completing with `on_completed` when the synthetic run or JSONL file ends. Exhaustion via `on_completed` is the answer to the former O-A; no exception-based signaling needed.
- **C2 — F17 (hot Observables via Subject).** `SerialTelemetrySource` and `CameraVisionSource` must bridge their push sources into the Observable world using a `Subject` (or equivalent). Frames must not be dropped between source start and subscription. Scheduler choice (thread pool vs `asyncio`) is an F17 decision.
- **C3 — F6 serial-bridge-merge.** The merge step becomes a reactive pipeline: `rx.zip(telemetry.observe(), vision.observe()).pipe(ops.map(...)).subscribe(...)`. The zip strategy (by round index vs timestamp) is an F6 decision.
- **C4 — F21 online-control-harness.** The real-time control loop is a natural Rx pipeline: `zip` → `map(build_state)` → `flat_map(llm.decide)` → `take_until(human_interrupt)`. F21 planning should treat the Observable from `TelemetrySource`/`VisionSource` as its primary input.
