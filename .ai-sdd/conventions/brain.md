# ai-sdd Conventions — `brain` vertical

> **Evidence-grounded (not pure seed).** This vertical now has working repo code + dedicated
> research, so discovery was run evidence-first. **Root:** `robot/v5-brain/` (the team's deployable
> Brain surface, DEC-0001 — the spec's logical `brain` vertical maps here; see
> [`MASTER_REQUIREMENTS.md`](../../MASTER_REQUIREMENTS.md) Authority/roots reconciliation). Rows cite
> **REQ** (MASTER_REQUIREMENTS), **REPO** (code in tree), or **WIKI** (ingested research). Owner: **TBD** (per O1; slices inherit the vertical lead once assigned, ADR-0027).

> **Brain language: PROS C++ (ADR-05).** MicroPython is 10–300× slower for tight loops and
> VEXcode-Python *receiving* serial from the Pi is community-unconfirmed (blocking `readline` stalls
> the cooperative-scheduler watchdog), whereas **PROS C++ bidirectional JSON is community-confirmed**
> (SERCTL_DISABLE_COBS + getchar/printf; FreeRTOS preemptive two-task pattern; VAIC reference). The
> team already has verified Brain→Pi telemetry in PROS C++. *(WIKI: [[research-vexcode-python-vs-cpp]],
> [[v5-brain-python-vs-pros]], [[v5-user-programs]], [[pros-cli-brain-bridge]], [[vex-coprocessor-pattern]].)*

**Vertical.** `brain` — the VEX V5 Brain firmware: a **PROS C++** thin executor that (1) emits the
Task Telemetry Contract over USB and (2) receives + executes clamped control commands. Root:
`robot/v5-brain/`.

## Discovery Record

| Change type | Evidence | Convention | Status |
|---|---|---|---|
| Language | WIKI (python-vs-cpp, brain-python-vs-pros); REPO `robot/v5-brain/v5-test/src/main.cpp`, `pros_bridge/` | **PROS C++** (FreeRTOS). Thin executor; no outer PID (V5 Smart Motors run hardware PID). | confirmed |
| Build / install | REPO `robot/v5-brain/v5-test/{Makefile,common.mk,project.pros}`, `TOOLCHAIN.md`; WIKI [[pros-dependency-compatibility]] | **PROS CLI** + ARM `arm-none-eabi-gcc`. Build **monolith** (`USE_PACKAGE:=0`) — mandatory on this Brain (hot/cold packaging silently broken). `pros mu --slot 1` to upload. | confirmed |
| Concurrency | WIKI (brain-python-vs-pros, pros-cli-brain-bridge); REPO BRAIN_INTERFACE §3.4 | **Two FreeRTOS tasks**: a receive task (`getchar` → parse → clamp → act → ack) and a high-priority **watchdog** task (stop motors on stale packet). A single combined loop deadlocks. | confirmed |
| Telemetry (out) | REPO `v5-test/src/main.cpp`, `robot/ros2-runtime/docs/BRAIN_INTERFACE.md` (VERIFIED) | Emit **newline-delimited JSON** on the USER port with **COBS disabled** (`serctl(SERCTL_DISABLE_COBS)`), `printf`+`fflush`. ~100 Hz during an action; silent between. | confirmed |
| Command (in) | REPO `pros_bridge/` sketch, BRAIN_INTERFACE §3 (designed, not yet on HW) | Receive clamped commands per the control grammar (`contracts`), ack each, enforce TTL + watchdog stop. | partial (HW-unproven) |
| Validate | REQ ADR-06; REPO field names | Emitted lines must satisfy the frozen `task-telemetry` contract. **Open:** the test program uses abbreviated fields/units (`pos/vel/cur(mA)/trq`) vs the contract's `position_deg/velocity_RPM/current_A/torque_Nm` — reconcile at integration. | open gap |
| Lint / format | REQ ADR-16 (ruff = Python) | `ruff` applies to Python dev scripts only. **C++ formatting (clang-format) is not established** — open gap. | open gap |
| Module / feature | REPO `v5-test/` (telemetry), `pros_bridge/` (command bridge) | One PROS project (promote `pros_bridge` → monolith for the bidirectional bridge; `v5-test` is the verified telemetry reference). | confirmed |
| Model / entity | REQ Components (Boundary rule) | **No schema defined here**; line/command shapes owned by `contracts`. | confirmed |
| Migration | REQ ADR-11 | **Not applicable.** | N/A |
| Test | REPO `v5-test` (arm-raise episodes); m1 | A run must emit valid contract telemetry; commands must be clamped + watchdog-safe. | confirmed |
| Endpoint | REQ OUT of scope | **Not applicable.** | N/A |
| Config / secrets | REQ ADR-03/08 | **None.** | confirmed |
| Dependency / new package | REPO `project.pros`, `pyproject.toml`/`uv.lock`; WIKI [[pros-dependency-compatibility]] | PROS deps via `project.pros` (pin kernel-4.x, monolith). Python dev tooling via `uv`. No `ArduinoJson`-free hand-rolled parse is acceptable but a small JSON lib is preferred. | confirmed |
| Naming / layering | REQ Components (Boundary rule) | PROS project under `robot/v5-brain/`; contract shapes imported-conceptually from `contracts`, never redefined. | confirmed |
| CI / release | — | **Open gap.** | open gap |

## Boundary rules (non-negotiable)

- **No schema defined here.** Telemetry and command/ack shapes are owned by `contracts` (Task
  Telemetry Contract + control grammar). *(REQ Components — Boundary rule.)*
- **Thin executor only.** The Brain relays setpoints to the motors' internal PID and emits telemetry;
  trajectory/goal reasoning lives off-Brain (`pilot`/`operator`). *(WIKI [[vex-coprocessor-pattern]].)*
- **Safety:** clamp every setpoint; stop on watchdog timeout and per-command `ttl_ms` expiry; reject
  malformed/unknown commands. *(REPO BRAIN_INTERFACE §3.5.)*
- **Single user port — telemetry vs ack multiplexing is unresolved** (BRAIN_INTERFACE §3.3): a
  continuous telemetry push and request/response acks share one port. Tagged single-stream demux is
  the recommended path; this must be decided before commands work on hardware. **Open.**
