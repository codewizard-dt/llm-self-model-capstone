# ai-sdd Conventions — `pilot` vertical  *(online-control loop — first-class expansion)*

> **New vertical (added 2026-06-21).** This is the **online control loop**: an LLM running on the
> Raspberry Pi that reads live telemetry + vision and issues control-grammar commands to perform an
> **open-ended task in real time**, looping until the task completes, is interrupted, or hits a limit.
> It is distinct from `self_model_generator` (the offline, generational self-model loop). Grounded in the
> maintainer's stage-c brief + REPO `robot/ros2-runtime/docs/BRAIN_INTERFACE.md` (Mode A real-time) +
> WIKI [[vex-coprocessor-pattern]] (LLM inference on the coprocessor). **The name `pilot` is a
> proposal — confirm or rename.**

**Vertical.** `pilot` — the real-time autonomy harness. Root: `pilot/` (greenfield; deployed onto the
Pi host alongside `robot/ros2-runtime`). Owner: **TBD** (per O1; slices inherit the vertical lead once assigned, ADR-0027).

## The loop

```
read live telemetry (Brain→Pi) + vision (camera) → LLM interprets state vs task
   → choose ONE control-grammar command → send (Pi→Brain) → ack → repeat
   until: task complete | operator interrupt | iteration/time/safety limit
```

The LLM's decisions are informed by the **offline analysis** the `self_model_generator` loop produces (the
self-model / gap model) — i.e. the offline loop tightens the model; the online loop uses it to act.

## Discovery Record

| Change type | Evidence | Convention | Status |
|---|---|---|---|
| Purpose | Maintainer brief (stage c); REPO BRAIN_INTERFACE §2.4 (Mode A real-time) | Online LLM control loop over live telemetry + vision. | confirmed |
| Language | REQ ADR-05 (Pi = Python); PILOT_MASTER_REQUIREMENTS Tech stacks | **Python 3.12** on the Pi. | confirmed |
| LLM runtime | REQ ADR-08 (Claude Code interactive, dev machine) · ADR-03 (no API keys) | **⚠️ Open / contradicts ADR-03 & ADR-08.** Real-time on-device control needs an LLM callable from a loop on the Pi (Claude API / Agent SDK, or Claude Code headless) — which implies network + an API key, contradicting ADR-03 ("no keys") and ADR-08 ("interactive dev-machine"). Decide the runtime + key/network posture. | open gap |
| Control interface | `contracts` control grammar (`control-command`) | Issue only **fixed-grammar** clamped commands via the `TelemetrySource`/command path; never raw motor writes. | confirmed |
| Build / test / lint / validate | REQ Tech stacks; ADR-15/16/06 | `uv`; `make test/lint/validate`. | confirmed |
| Loop safety | REPO BRAIN_INTERFACE §3.5; maintainer brief | Hard **iteration + wall-clock limits**; human **interrupt**; every command carries `ttl_ms`; Brain watchdog stops on silence. The harness must be safe to kill at any step. | confirmed |
| State / logging | REQ ADR-11; REPO `session_*.jsonl` | Append-only per-run log (decisions + commands + observed results) for audit + later offline analysis. | confirmed |
| Model / entity | REQ Components (Boundary rule) | **No schema defined here**; the command + telemetry shapes are owned by `contracts`. | confirmed |
| Migration / Endpoint | REQ ADR-11 / ADR-04 | **Not applicable.** | N/A |
| Config / secrets | ADR-03 (revisit) | If an API key is required (see LLM runtime), it must be an **environment-backed secret**, never committed. Surface the requirement in docs. | open gap |
| CI / release | — | **Open gap.** | open gap |

## Boundary rules

- **Fixed control grammar only.** The LLM emits commands strictly from the `contracts` control
  grammar; the Brain clamps and may reject. No open-ended motor access. *(contracts/PROTOCOL.md.)*
- **No schema defined here** — import from `contracts`.
- **Bounded + interruptible.** Always run under iteration/time limits with a human kill switch; never
  an unbounded autonomous loop. *(Maintainer brief; BRAIN_INTERFACE §3.5.)*
- **Reuse, don't redefine, the command path.** Build on the `coprocessor` ROS serial/command plumbing
  (`robot/ros2-runtime`), not a parallel transport.

## Open decisions (flagged — resolve before building)

1. **LLM runtime + key/network** on the Pi (contradicts ADR-03/ADR-08).
2. **Telemetry-vs-ack multiplex** on the single USB port (BRAIN_INTERFACE §3.3) — shared with `brain`.
3. **Control grammar vocabulary** — the arm/manipulation commands beyond drive/turn/stop (open in
   `contracts` control-command, draft).
4. **Vertical name/owner** — `pilot` is a proposal.
