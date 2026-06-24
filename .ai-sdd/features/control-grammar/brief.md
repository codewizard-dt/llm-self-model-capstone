# control-grammar

| Field | Value |
|---|---|
| Feature ID | F19 |
| Vertical | `contracts` · root `contracts/` |
| Stack | Python 3.12 · uv · ruff · pydantic v2 |
| Gates | `m1` contracts-frozen |
| Deps | F1 telemetry-contract, F2 self-model-schema, F3 parts-catalog-grammar, F4 adapter-interfaces — **all merged** |
| Unblocks | F20 brain-command-bridge → F21 online-control-harness (`pilot`) |
| Owner | TBD |

> Sources: [MASTER_REQUIREMENTS.md](../../../MASTER_REQUIREMENTS.md) (Components → "Control grammar `(contracts)` — owns `control-command`"; Sub-features F19/F20/F21; ADR-10/19; Frozen Contracts; Milestones m1). Catalog narrowing: F3 frozen Parts Catalog Grammar (effector-encoded `MotorAllocation`, 4 buildable configs). Wire draft + safety: [robot/v5-brain/PROTOCOL.md](../../../robot/v5-brain/PROTOCOL.md), [robot/v5-brain/BRAIN_INTERFACE.md](../../../robot/v5-brain/BRAIN_INTERFACE.md), [robot/v5-brain/pros_bridge/](../../../robot/v5-brain/pros_bridge/) (guarded handler: `stop`/`drive`/`heartbeat`, watchdog, TTL clamps). Research: [raw/research/ros2-jazzy-supervisory-control-plan/](../../../raw/research/ros2-jazzy-supervisory-control-plan/index.md) ("treat `control-command` as the canonical command/ack/fault schema before custom ROS messages proliferate"; agent loop slow / robot loop fast / V5 loop hard-real-time; the Brain stays the safety authority), [raw/research/robot-policy/](../../../raw/research/robot-policy/index.md) (the V5 Brain runs a deterministic classical policy; the LLM revises a self-model, it does not train a neural policy). Full decision record (D1–D13) lives in [requirements.md](requirements.md).

---

## Goal

Freeze the **control grammar** — the fixed, typed command/ack vocabulary the online control loop uses to drive the robot — as the runtime source of truth in the `contracts` package, so milestone `m1` (contracts-frozen) can close and `F20`/`F21` can be built against a stable wire. The grammar ships as pydantic v2 models that validate (a) a closed **command line** carrying a discriminated union of six motion/manipulator verbs (`stop`, `drive`, `turn`, `arm`, `claw`, `flywheel`) behind a strict envelope, (b) a Pi-liveness **heartbeat** line, and (c) the Brain's **ack** line with a closed `FaultCode` vocabulary and `ok`/`rejected`/`stale` states. The verb set spans the three buildable motor topologies in F3's narrowed catalog (claw / scoop / flywheel) so a Generator-revised build is drivable without a contract amendment. A single closed `type ∈ {cmd, heartbeat, ack}` discriminator lets the Brain demultiplex commands, heartbeats, and acks off the *same* USB user port that already carries telemetry `ContractLine`s, and the change is strictly **additive** to F1–F4 (no regression to the frozen telemetry/self-model/catalog/adapter contracts).

---

## In scope

- **`contracts/src/contracts/control_command.py`** — the wire models:
  - `ControlEnvelope` (base, `extra="forbid"`): `v: Literal[1]`, `seq` (`ge=0, lt=2³²`), `sent_ms`, `ttl_ms` (`ge=1, le=TTL_MS_MAX`).
  - Six command bodies, each tagged `type="cmd"` + a `cmd` discriminator: `StopCommand` (`reason ∈ {operator_estop, operator, watchdog_self, fault}`), `DriveCommand` (`vx`/`omega` range-checked, `vy` wire-locked to 0), `TurnCommand` (`omega`), `ArmCommand` (`deg` in arm range, optional `vel_rpm`), `ClawCommand` (`state ∈ {open, close}`, optional `grip_force_N` reusing F1's unit), `FlywheelCommand` (`rpm ≥ 0`).
  - `ControlCommand` (inner `cmd`-keyed union) · `HeartbeatLine` (`type="heartbeat"`, envelope-only) · `ControlLine` (outer `type`-keyed wire union the Pi emits and the Brain parses).
  - `AckLine` (`type="ack"`): `ack`, `state ∈ {ok, rejected, stale}`, `recv_ms`, `fault: FaultCode | None` with the `fault`↔`state` invariant enforced, plus optional guarded-Brain health fields (`battery_*`, `watchdog_age_ms`, `estop`, `motion_enabled`, `drive_ports_ok`, `motor_ports`).
  - `FaultCode` (`StrEnum`, 8 closed values) and the exported clamp constants (`MAX_LINEAR`, `MAX_OMEGA`, `MAX_FLYWHEEL_RPM`, `MAX_ARM_RPM`, `MAX_CLAW_GRIP_FORCE_N`, `ARM_DEG_MIN/MAX`, `TTL_MS_MAX`, `BRAIN_MAX_LINEAR`, `BRAIN_TTL_MS_MAX`).
- **`__init__.py`** — re-export the new models, `FaultCode`, and clamp constants additively; existing exports unchanged.
- **`schema` entrypoint** — two new registry entries emitting `contracts/schemas/control_command.json` (the `ControlLine` union) and `contracts/schemas/ack_line.json`; existing schema files stay byte-identical (drift-gated).
- **`validate` entrypoint** — a third dispatch over `fixtures/control_command_*.jsonl`, routing each line by `type` through `ControlLine`/`AckLine`; existing F1/F2/F3 dispatches untouched.
- **Fixtures** — `control_command_grab_cycle.jsonl` (claw build: heartbeat→drive→arm→claw→arm→stop, each with its ack), `control_command_flywheel_cycle.jsonl` (flywheel build), `control_command_rejections.jsonl` (one rejected ack per `FaultCode`).
- **Tests** — `contracts/tests/test_control_command.py` covering the round-trips, union/range/envelope rejections, ack invariants, exhaustive fault coverage, clamp-constant identity, and the cross-contract demux guard (a `ContractLine` must fail to validate as `ControlLine`).

## Out of scope

- **F20** Brain-side PROS C++ parser/clamp/watchdog/ack emitter — F19 freezes the wire; F20 satisfies it.
- **F21** `pilot` online-control harness (the `reactivex` pipeline that emits `ControlLine`s and consumes `AckLine`s).
- **Cross-build verb applicability** — rejecting a verb that is wire-legal but mechanically inapplicable to the *currently assembled* build (e.g. `flywheel` to a claw robot) is F20's runtime check via `FaultCode.not_assembled`, not a static-contract concern.
- **Transport selection** (USB serial 115,200 is the MVP per ADR-10; RS-485 is a Stage-2 "same JSON" swap), **binary protocol-v2** (CRC/framing), a command-flow **adapter protocol** (`ControlSink`), **per-motor/PID** commands, **ROS message/action** definitions (F19 is the canonical schema ROS would bind over), and **auth/signing** (single-machine USB, no threat model).

---

## Acceptance

Each item is independently runnable from `contracts/` (or repo root, which delegates):

1. `make sync` exits 0.
2. `make lint` exits 0 (`ruff check` + `ruff format --check`).
3. `make schema` writes `control_command.json` + `ack_line.json` (committed, non-empty; `type`/`cmd`/`state`/`fault` surface as JSON-Schema `enum`s); `make schema-check` exits 0 and `contract_line.json`/`self_model.json`/`score_contract.json` are **byte-identical** to their pre-F19 versions.
4. `make validate` exits 0 — round-trips all three control fixtures by `type` dispatch and still validates the F1/F2/F3 fixtures.
5. `make test` exits 0, covering: round-trip of all fixtures; union failures (missing/out-of-vocab `cmd`, missing body fields); range rejections (`vx>MAX_LINEAR`, `vy≠0`, `omega<-MAX_OMEGA`, `deg` out of range, `rpm<0`/`>MAX`, `ttl_ms` out of `[1,TTL_MS_MAX]`); envelope rejections (`v≠1`, foreign `type`, extra field under `extra="forbid"`); ack invariants (`fault`↔`state`, `stale` accepted); exhaustive `FaultCode` coverage in the rejections fixture; clamp constants importable and bit-for-bit correct; cross-contract demux (a `ContractLine` fails as `ControlLine`); F1–F4 suites still green.
6. `from contracts import ControlLine, AckLine, FaultCode, MAX_LINEAR, MAX_OMEGA, MAX_FLYWHEEL_RPM, TTL_MS_MAX` resolves in `uv run python` after `make sync`.
7. Root `make sync`/`validate`/`test`/`lint`/`schema` (delegating into `contracts/`) all exit 0; F1–F4 suites pass.
8. **Manual `m1` reviewer check:** a hand-authored grab cycle round-trips through `ControlLine` + `AckLine` exactly as the existing `pros_bridge` handler emits today, plus the `arm`/`claw`/`flywheel` verbs the three buildable configs need — i.e. F19 frozen unblocks F20 across the whole catalog without re-litigating the wire.

---

## Constraints

- Python 3.12 (`>=3.12,<3.13`) · uv · ruff · pydantic v2 — no pip/poetry/black/flake8 (ADR-05/15/16). Build entry is **`make sync`**.
- `root: contracts/` · `ignore_folders: .venv, __pycache__, dist, .pytest_cache, captures`.
- pydantic v2 only: `ConfigDict`, `Field`, discriminated unions (`Field(discriminator=...)` inner / callable `Discriminator`+`Tag` outer), JSON Schema via `model_json_schema()` (ADR-06). Reuse F1's `StrictModel` base.
- **Closed vocabulary** — every discriminator is a `Literal`/`StrEnum`: `type ∈ {cmd, heartbeat, ack}`, `cmd ∈ {stop, drive, turn, arm, claw, flywheel}`, `state ∈ {ok, rejected, stale}`, `reason ∈ {operator_estop, operator, watchdog_self, fault}`, `FaultCode ∈ {malformed_json, unknown_command, ttl_expired, watchdog, estop_latched, out_of_range, oversized_packet, not_assembled}`. No free-string `cmd` or `fault`. Adding a verb is a frozen-contract change.
- **`v: Literal[1]` is locked** (the protocol version; no `schema_version` on the wire — bumping `v` needs frozen-contract approval). Control grammar versions independently of F1's `ContractLine`.
- **Bounded + interruptible (ADR-19):** every line carries `ttl_ms`; `stop` is always legal. **Reject, don't clamp:** F19 rejects out-of-range values (`ValidationError`); physical clamping is F20's safety contract at the Brain.
- **Single-stream safe:** the `type` `Literal` set must not collide with anything `ContractLine` puts on the same user port (enforced by the demux test); `AckLine` is self-identifying so the Pi reader demuxes on `type` alone.
- **No telemetry leakage on the ack** — acks carry `state`/`fault`/health only; streaming motor samples stay on telemetry/`ContractLine`.
- **Additive only** — every existing model, schema file, fixture, and Makefile target is untouched; `schema` gains two entries, `validate` gains one dispatch. No hardware, no network, no schema defined outside `contracts`, no PROS C++.

---

## Milestones

| id | Validates | Mode | Owner |
|---|---|---|---|
| `s1` models + schemas | `control_command.py` defines the envelope, the closed 6-verb `ControlCommand` union, `HeartbeatLine`, `ControlLine`, `AckLine`, `FaultCode`, and clamp constants; all field/range/ack validators fire; `__init__` re-exports; `make schema` emits the two schema files; `make lint` + `make test` green; F1–F4 suites pass | automated (`make lint`, `make test`, `make schema`) | TBD |
| `s2` fixtures + gates | the three control fixtures round-trip via the extended `validate` dispatch; exhaustive `FaultCode` coverage + cross-contract demux tests fire; `make schema-check` byte-identical for F1–F3 schemas; root `make validate`/`test`/`lint`/`schema` green | automated (`make validate`, `make schema-check`) | TBD |
| (gate) `m1` contracts-frozen | all contracts (F1–F4 + F19) load and round-trip cleanly; manual grab-cycle reviewer check (Acceptance §8) | manual — human gate | TBD |

---

## Open questions

- **O1 — arm angle range.** `ArmCommand.deg` ships with a conservative `[0, 360]`; the operational sub-range differs between the claw and scoop builds and isn't measured in-repo. Proposal: F20 narrows per assembled build once hard stops are measured. Needs an owner call (could defer the bound entirely to F20).
- **O2 — `MAX_FLYWHEEL_RPM`.** Shipped permissive at `3600` (let the Brain clamp + motor PID enforce reality); the cartridge-rated ceiling is ~600 RPM at the output shaft but launch-mechanism gearing is unmeasured. Confirm with the flywheel-build owner.
- **O3 — clamp constants for F20.** Whether F19 emits a generated C++ header so the Brain pins to the same numbers, or F20 inlines them under a `make` diff-guard. Deferred to the F20 owner.
- **O4 — MASTER "draft" wording.** MASTER tags `control-command` as *draft*; after `m1` it should read "frozen" alongside F1–F4 (small MASTER amendment landed with/after the F19 merge).
- **O5 — `pilot` runtime/secret posture (ADR-19).** On-device online inference may need an API key + network, contradicting "no keys." This affects F21, **not** F19 — the wire is identical whether `pilot` runs on Claude Code or an API. Flagged for transparency; F19 freezes independently.
