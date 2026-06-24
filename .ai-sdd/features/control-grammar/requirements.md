# control-grammar — Requirements

| Field | Value |
|---|---|
| Feature ID | F19 |
| Vertical | `contracts` |
| Root | `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Gates | `m1` contracts-frozen |
| Depends on | F1 telemetry-contract (frozen) · F2 self-model-schema + F3 parts-catalog-grammar (merged; **PR #18 post-merge narrowing** is the design space F19's manipulator verbs span) · F4 adapter-interfaces (merged) |
| Unblocks | F20 brain-command-bridge (PROS C++) → F21 online-control-harness (pilot) |

---

## Goal

Freeze the **Control Grammar** as the runtime source of truth for the fixed, typed command/ack vocabulary the online control loop (`pilot` → `brain`, F21) uses to drive the robot in real time. Ship pydantic v2 models that validate (a) a closed **command envelope** carrying a discriminated union of motion/manipulator primitives spanning all 3 post-PR #18 buildable motor topologies, (b) the **ack envelope** the Brain returns, and (c) a controlled **fault** vocabulary; extend the contracts package's `schema` and `validate` entrypoints **additively** (no F1/F2/F3/F4 regression); and include fixtures for one cycle per build kind + an exhaustive rejection set. This is the artifact the `pilot` LLM emits, F20's PROS C++ bridge parses-and-clamps, F21 sequences against live telemetry + vision, and — per the ROS2 research recommendation — any future ROS bindings transport unchanged. **Closing this contract is what makes ADR-19 buildable**: F20 and F21 cannot start until F19 freezes the wire. F19 gates `m1`.

---

## In scope

- **`contracts/src/contracts/control_command.py`**, re-exported from `contracts.__init__`:
  - **`ControlEnvelope`** (pydantic v2, `StrictModel` base, `extra="forbid"`): `v: Literal[1]` (protocol version, locked), `seq: int` (`Field(ge=0, lt=2**32)` — D5), `type: Literal["cmd", "heartbeat"]` (stream discriminator — see D2 for the demux invariant), `sent_ms: int`, `ttl_ms: int` (`Field(ge=1, le=TTL_MS_MAX)` — D5).
  - **`ControlCommand`** — pydantic v2 discriminated union (`Field(discriminator="cmd")`) over the 6 closed verbs:
    - `StopCommand` — `cmd: Literal["stop"]`, `reason: Literal["operator_estop", "operator", "watchdog_self", "fault"]`.
    - `DriveCommand` — `cmd: Literal["drive"]`, `vx: float` (`Field(ge=-MAX_LINEAR, le=MAX_LINEAR)`), `vy: float = 0.0` (`Field(ge=0, le=0)` — locked; non-zero rejected per D12), `omega: float` (`Field(ge=-MAX_OMEGA, le=MAX_OMEGA)`).
    - `TurnCommand` — `cmd: Literal["turn"]`, `omega: float` (`Field(ge=-MAX_OMEGA, le=MAX_OMEGA)`).
    - `ArmCommand` — `cmd: Literal["arm"]`, `deg: float` (`Field(ge=ARM_DEG_MIN, le=ARM_DEG_MAX)`), `vel_rpm: float | None = None`.
    - `ClawCommand` — `cmd: Literal["claw"]`, `state: Literal["open", "close"]`, `grip_force_N: float | None = None`.
    - `FlywheelCommand` — `cmd: Literal["flywheel"]`, `rpm: float` (`Field(ge=0, le=MAX_FLYWHEEL_RPM)`).
  - **`HeartbeatLine`** — envelope-only, `type: Literal["heartbeat"]`.
  - **`ControlLine`** — outer wire model: discriminated union over `type` of (envelope+`ControlCommand`) for `type=="cmd"` and `HeartbeatLine` for `type=="heartbeat"`. Single thing the Pi serializes per line.
  - **`AckLine`** — `type: Literal["ack"]`, `v: Literal[1]`, `ack: int` (the `seq` it acknowledges), `state: Literal["ok", "rejected", "stale"]` (D6), `recv_ms: int`, `fault: FaultCode | None` (model-validator: `fault is None` iff `state == "ok"`), plus optional lightweight bridge-health fields proven by the guarded V5 Brain bridge (`battery_mv`, `battery_pct`, `watchdog_age_ms`, `estop`, `motion_enabled`, `drive_ports_ok`, `motor_ports`). Streaming motor samples remain on `/vex/telemetry`.
  - **`FaultCode`** (`StrEnum`): `malformed_json`, `unknown_command`, `ttl_expired`, `watchdog`, `estop_latched`, `out_of_range`, `oversized_packet`, `not_assembled` (D7).
  - **Clamp constants** (module-level): wire-envelope limits `MAX_LINEAR=0.35`, `MAX_OMEGA=0.60`, `MAX_FLYWHEEL_RPM=3600`, `ARM_DEG_MIN=0`, `ARM_DEG_MAX=360`, `TTL_MS_MAX=5000`, plus guarded Brain physical clamps `BRAIN_MAX_LINEAR=0.18` and `BRAIN_TTL_MS_MAX=500`.
- **`contracts/src/contracts/__init__.py` extended additively** — add `ControlLine`, `ControlCommand`, `ControlEnvelope`, `HeartbeatLine`, `AckLine`, `StopCommand`, `DriveCommand`, `TurnCommand`, `ArmCommand`, `ClawCommand`, `FlywheelCommand`, `FaultCode`, `MAX_LINEAR`, `MAX_OMEGA`, `MAX_FLYWHEEL_RPM`, `ARM_DEG_MIN`, `ARM_DEG_MAX`, `TTL_MS_MAX`, `BRAIN_MAX_LINEAR`, and `BRAIN_TTL_MS_MAX` to imports and `__all__`. All existing exports unchanged.
- **`schema.py` registry extended additively** — add `control_command.json` (for `ControlLine`) and `ack_line.json` (for `AckLine`). Existing `contract_line.json` / `self_model.json` / `score_contract.json` outputs **byte-identical**.
- **`validate.py` extended additively** — third dispatch: `fixtures/control_command_*.jsonl` → each line dispatches by `type` (`"cmd"`/`"heartbeat"` → `ControlLine`; `"ack"` → `AckLine`). Existing F1/F2/F3 dispatches unchanged.
- **Fixtures** in `contracts/fixtures/`:
  - `control_command_grab_cycle.jsonl` — claw build (`2drive+1arm+1claw`): `heartbeat` → `drive` → `arm` → `claw` → `arm` → `stop`, each with its ack.
  - `control_command_flywheel_cycle.jsonl` — flywheel build (`2drive+1flywheel`): `heartbeat` → `drive` → `flywheel(spin)` → `flywheel(rpm=0)` → `stop`, each with its ack.
  - `control_command_rejections.jsonl` — one rejected ack per `FaultCode` value (exhaustive coverage).
- **Unit tests** in `contracts/tests/test_control_command.py` and `contracts/tests/test_validate.py` (extended).

## Out of scope

- **F20 Brain-side parser** (PROS C++ receive + clamp + ack + watchdog).
- **F21 online control harness** (`pilot` Rx pipeline that emits `ControlLine` against F4 streams).
- **Single-port multiplex *strategy*** (tagged single-stream vs RS-485 second channel — BRAIN_INTERFACE §3.3). F19 *enables* tagged single-stream by closing the `type` discriminator (D2); the reader-thread/seq-map implementation lives in F20.
- **Transport selection** — USB serial 115,200 (ADR-10) is MVP; RS-485 is a swap.
- **Binary protocol-v2** — out of scope; future contract.
- **`ControlSink` adapter protocol** — F21 may want one; F19 freezes only the data.
- **Motor-level commands** (per-motor voltage/velocity, PID gains) — bypasses F20's safety contract and contradicts ADR-19's "bounded + interruptible."
- **ROS message/action definitions** — F19 is the canonical schema; ROS bindings are transport adapters.
- **Authentication/signing** on commands.
- **`Subject`/`reactivex` operators/schedulers** — pinned to F17/F21 by F4's C2/C4.
- **Cross-build runtime applicability enforcement** — F20's job (D13).

---

## Acceptance

Runnable from `contracts/` (or root, which delegates):

1. `make sync` exits 0.
2. `make lint` exits 0.
3. `make schema` exits 0 and writes `contracts/schemas/control_command.json` + `contracts/schemas/ack_line.json` (committed, non-empty, the `type`/`cmd`/`state`/`fault` discriminators surface as JSON-Schema `enum` arrays). `make schema-check` exits 0; `contract_line.json`, `self_model.json`, `score_contract.json` are **byte-identical** to their pre-F19 versions.
4. `make validate` exits 0 — round-trips `control_command_grab_cycle.jsonl`, `control_command_flywheel_cycle.jsonl`, and `control_command_rejections.jsonl` through `ControlLine` / `AckLine` per the `type` dispatch, and still validates the F1 `*.jsonl`, F2 `self_model_*.json`, F3 `parts_catalog.json` (+ F2 fixture buildability) paths.
5. `make test` exits 0, covering:
   - round-trip parse of all three control fixtures;
   - discriminated union: `cmd` missing → `ValidationError`; `cmd: "fly"` (out of vocabulary) → `ValidationError`; `cmd: "drive"` missing `vx`/`omega` → `ValidationError`;
   - per-command range validation: `drive.vx > MAX_LINEAR` → `ValidationError`; `drive.vy != 0` → `ValidationError` (D12); `turn.omega < -MAX_OMEGA` → `ValidationError`; `arm.deg` outside `[ARM_DEG_MIN, ARM_DEG_MAX]` → `ValidationError`; `flywheel.rpm < 0` or `> MAX_FLYWHEEL_RPM` → `ValidationError`; `ttl_ms` outside `[1, TTL_MS_MAX]` → `ValidationError`;
   - envelope shape: `v != 1` → `ValidationError`; `type: "telemetry"` → `ValidationError` (closed `Literal`); unknown extra field anywhere → `ValidationError` (`extra="forbid"`);
   - ack invariants: `state: "ok"` with non-null `fault` → `ValidationError`; `state: "rejected"` with `fault: null` → `ValidationError`; `state: "stale"` accepted; every `FaultCode` value appears at least once in `control_command_rejections.jsonl` (exhaustive-coverage assertion);
   - clamp-constant identity: `MAX_LINEAR`/`MAX_OMEGA`/`MAX_FLYWHEEL_RPM`/`ARM_DEG_MIN`/`ARM_DEG_MAX`/`TTL_MS_MAX` are importable from `contracts` and match the documented values bit-for-bit (D10/C1);
   - cross-contract demux: a `ContractLine` JSON line round-trips through `ContractLine` and **fails** to validate as `ControlLine` (proves D2's single-stream demux is wire-level safe);
   - F1, F2, F3, F4 test suites still pass.
6. `from contracts import ControlLine, ControlCommand, AckLine, FaultCode, MAX_LINEAR, MAX_OMEGA, MAX_FLYWHEEL_RPM, TTL_MS_MAX` resolves cleanly in `uv run python` after `make sync`.
7. Root `make sync`/`validate`/`test`/`lint`/`schema`/`schema-check` (+ `catalog`/`catalog-check`) all exit 0; F1/F2/F3/F4 suites still pass.
8. Manual reviewer check: a hand-authored grab cycle round-trips as it would today via `pros_bridge/src/main.cpp` (`stop`/`drive`/`heartbeat`) plus the manipulator primitives (`arm`/`claw`/`flywheel`) the 3 post-PR #18 buildable configs address — F19 frozen unblocks F20 to extend the Brain handler across the full design space without re-litigating the wire.

---

## Constraints

- Python 3.12 (`>=3.12,<3.13`) · uv · ruff · pydantic v2 — no pip/poetry/black/flake8 (ADR-05/15/16). Build entry is **`make sync`** (F1 D7).
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- pydantic v2 only: `ConfigDict`, `Field`, discriminated unions via `Field(discriminator=...)`; JSON Schema via `model_json_schema()` (ADR-06). Reuse F1's `StrictModel` base for all strict sub-models.
- `v: Literal[1]` is locked on the wire (D8). No `schema_version` field on `ControlLine`/`AckLine` — `v` plays that role; contracts version independently (mirrors F2/F3).
- **Closed vocabulary**: every discriminator is a `Literal`/`StrEnum`. `type ∈ {cmd, heartbeat, ack}`, `cmd ∈ {stop, drive, turn, arm, claw, flywheel}`, `state ∈ {ok, rejected, stale}`, `reason ∈ {operator_estop, operator, watchdog_self, fault}`, `FaultCode ∈ {malformed_json, unknown_command, ttl_expired, watchdog, estop_latched, out_of_range, oversized_packet, not_assembled}`.
- **Strict envelopes**: every command body + envelope + ack uses `extra="forbid"`.
- **Wire discriminator non-collision** (D2): `type`'s `Literal` values must not overlap with anything `ContractLine` emits on the same stream — enforced by the cross-contract demux test.
- **Additive only**: every existing model, schema file, fixture, and Makefile target is untouched; `schema.py`'s registry gains two entries, `validate.py` gains one dispatch.
- **No hardware, no network, no schema defined outside `contracts`, no PROS C++** — F20/F21 own those.
- **Out-of-range rejects at F19, clamps at F20** (D11): F19 is the contract; F20 is the safety layer.

---

## Decisions

| # | Decision | Resolution | Status |
|---|---|---|---|
| D1 | Command vocabulary (frozen at m1) | **`stop`, `drive`, `turn`, `arm`, `claw`, `flywheel`** — spans the 3 post-PR #18 buildable motor topologies (one verb per addressable manipulator motor). Earlier "claw-only, defer scoop/flywheel" plan rejected: the Generator can revise across all 3 builds today; deferring would leave 2/3 of the design space un-drivable until an immediate amendment. | `closed` |
| D2 | Stream discriminator | **Closed `type: Literal["cmd", "heartbeat", "ack"]`** — the single demultiplexer for the Pi reader thread (BRAIN_INTERFACE §3.3 Option 1). Cross-contract demux test asserts `ContractLine`'s payload cannot collide. | `closed` |
| D3 | Ack field set | **Receipt plus lightweight bridge health.** The required receipt is `state` + `fault` + `ack` + `recv_ms`; optional `battery_mv`, `battery_pct`, `watchdog_age_ms`, `estop`, `motion_enabled`, `drive_ports_ok`, and `motor_ports` match the live guarded Brain ack. Streaming motor samples stay on telemetry/ContractLine. | `closed` |
| D4 | Discriminator placement | **Two-level**: outer `type` (cmd/heartbeat/ack) at envelope, inner `cmd` (stop/drive/turn/arm/claw/flywheel) inside `cmd`-typed lines. | `closed` |
| D5 | Wire bounds | **`ttl_ms: Field(ge=1, le=TTL_MS_MAX=5000)`** (matches the ROS bridge envelope). The guarded Brain narrows motion TTL with `BRAIN_TTL_MS_MAX=500`. **`seq: Field(ge=0, lt=2**32)`** (matches a future binary framing). | `closed` |
| D6 | Ack `state` values | **`ok`/`rejected`/`stale`.** `stale` = command received post-TTL — distinct from `rejected`; lets F20 log without re-stopping. | `closed` |
| D7 | Fault codes — closed enum or free string | **Closed `StrEnum`** of 8 values. `not_assembled` is new — F20 emits it when a verb is wire-legal but mechanically inapplicable to the assembled build (e.g. `flywheel` to a claw robot). Decouples wire-legality from runtime-applicability (D13). | `closed` |
| D8 | `schema_version` vs `v` | **`v: Literal[1]`** on the wire — matches PROTOCOL.md draft + existing Brain handler. F1's `schema_version` lives on `ContractLine`. Independent versioning. | `closed` |
| D9 | Module + schema file names | **`contracts/src/contracts/control_command.py`**; schemas at `contracts/schemas/control_command.json` (the command/heartbeat union) + `contracts/schemas/ack_line.json` (the ack). Two files because they validate different lines on the same stream. | `closed` |
| D10 | Clamp constants — where they live | **Exported from `contracts.control_command`**: wire-envelope constants `MAX_LINEAR=0.35`, `MAX_OMEGA=0.60`, `MAX_FLYWHEEL_RPM=3600`, `ARM_DEG_MIN=0`, `ARM_DEG_MAX=360`, `TTL_MS_MAX=5000`, plus guarded Brain clamps `BRAIN_MAX_LINEAR=0.18`, `BRAIN_TTL_MS_MAX=500`. F19 enforces wire bounds and exposes Brain clamps so F20 can narrow safely at the hardware boundary. | `closed` |
| D11 | Out-of-range = reject or clamp at F19 | **Reject (`ValidationError`).** F19 is the contract; F20 still clamps at the Brain (its safety contract). | `closed` |
| D12 | `DriveCommand.vy` — drop, keep at 0, or accept | **Keep on the wire, locked to 0** (`Field(ge=0, le=0)`). Every buildable post-PR #18 config uses the same `front_omni+rear_standard` drivetrain; keeping the field is forward-compat for a future holonomic upgrade (drop the `le=0` instead of adding a field). | `closed` |
| D13 | Cross-build verb applicability — where enforced | **F20, not F19.** F19 freezes the verb set across all 3 motor topologies (any verb is wire-legal). F20 reads the *assembled* build's port assignments and rejects mechanically-inapplicable verbs with `FaultCode.not_assembled`. | `closed` |
| D14 | Slice decomposition | **Two slices: `models-and-schemas` → `validate-fixtures-and-gates`.** Slice 1 ships `control_command.py` (all 6 verbs + envelope + ack + FaultCode + clamp constants) + the `schema.py`/`__init__.py` additions + unit tests covering validators, the discriminated union, range bounds, and the cross-contract demux. Slice 2 ships the 3 fixtures + the additive `validate.py` dispatch + exhaustive `FaultCode` coverage assertion + root delegation + full no-regression sweep. Mirrors F3's `catalog-model-and-rules` → `validate-and-gates` decomposition exactly. | `closed` |

---

## Open questions

All F19 open questions O1–O5 from the brief are proposed for closure in D5/D7/D10 above. Specifically:

- **O1 (arm range)** → D10 closes at `ARM_DEG_MIN=0`, `ARM_DEG_MAX=360` (conservative); F20 may narrow per build.
- **O1b (`MAX_FLYWHEEL_RPM`)** → D10 closes at `3600`; F20 may narrow.
- **O2 (generated C++ header)** → deferred to F20 implementer (not F19's concern).
- **O3 (free-text `reason` on `StopCommand`)** → rejected; D7's closed `reason` enum stays.
- **O4 (`seq` bounds)** → D5 closes at `Field(ge=0, lt=2**32)`.
- **O5 (`pilot` runtime secret posture)** → out of F19 scope (informational; affects F21).

> This requirements draft awaits explicit approval before slices + `pipeline.yaml` are emitted (planning gate). The proposed D14 slice decomposition (`models-and-schemas` → `validate-fixtures-and-gates`) is the load-bearing decision for what gets cut next.
