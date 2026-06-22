# ai-sdd Conventions — `coprocessor` vertical

> **Evidence-grounded.** **Root:** `robot/pi-runtime/` (the team's deployable Pi surface, DEC-0001 —
> the spec's logical `coprocessor` vertical maps here). Rows cite **REQ**
> ([`MASTER_REQUIREMENTS.md`](../../MASTER_REQUIREMENTS.md)), **REPO** (code in tree), or **WIKI**
> (ingested research). Owner: **Jake** (Grace: vision-pipeline).

**Vertical.** `coprocessor` — Raspberry Pi 5 runtime: the serial transport to the Brain, the vision
pipeline (YOLO11n + AprilTag), the telemetry+vision merge into `session_*.jsonl`, and baseline
capture. It is also the **host for the online-control harness** (see the [`pilot`](pilot.md) vertical,
which runs here). Root: `robot/pi-runtime/`.

## Discovery Record

| Change type | Evidence | Convention | Status |
|---|---|---|---|
| Build / install | REQ Tech stacks; ADR-15; REPO `robot/pi-runtime/` (`PYTHONPATH=src`, system python) | Target convention: **`uv`** (`uv sync`/`add`/`run`). The existing scaffold runs on system `python3` + `PYTHONPATH` — migrate to a `uv` project. | confirmed (migration pending) |
| Test | REQ Verification & Reviewer Runbook; m3; REPO `scripts/smoke_test.sh` | `make test`; m3 validates a valid `vision` block + merged JSONL. | confirmed |
| Lint / format | REQ ADR-16 | `ruff` only; `make lint` = `ruff check` + `ruff format --check`. | confirmed |
| Validate | REQ ADR-06 | `make validate` — pydantic fixtures vs frozen schemas (imported from `contracts`). | confirmed |
| Language | REQ ADR-05; Tech stacks | **Python 3.11** (Pi 5). | confirmed |
| Serial transport | REPO `robot/pi-runtime/docs/BRAIN_INTERFACE.md` (VERIFIED), `src/vexy_system2/bridge.py`; WIKI [[vex-coprocessor-pattern]] | Read the **USER port** (`/dev/serial/by-id/...-if02` = `/dev/ttyACM1`), 115200 8N1, newline JSON, COBS-off, filter the one-time boot banner (`grep -a '^{'`). `pyserial`. | confirmed |
| Telemetry merge | REQ Components (serial-bridge-merge) + data-flow; REPO `protocol.py`, `bridge.py` | `serial_bridge.py` merges telemetry + vision **into `session_*.jsonl`** (Task Telemetry Contract lines). The Brain pushes telemetry continuously; the merge consumes a **read-stream** (not request/response). | confirmed |
| Vision | REQ Components (YOLO11n + AprilTag → `bbox_iou`); ADR-13; REPO `camera_broker.py` (picamera2/cv2 capture) | Vision pipeline = **YOLO11n (NCNN) + AprilTag** → `VisionBlock`. The existing `camera_broker` (single-camera-owner via `picamera2`) is the capture base; detection is to be built. | confirmed (detection pending) |
| Command path / control | REPO `protocol.py` (command/ack grammar), `bridge.py --mode serial`; BRAIN_INTERFACE §3 | The existing teleop command/ack grammar is the **seed of the control grammar** (now owned by `contracts`; see [`pilot`](pilot.md)). The Pi sends clamped commands + reads acks. **Multiplex tension** (telemetry stream vs acks on one port) is unresolved — BRAIN_INTERFACE §3.3. | partial (seed; HW-unproven) |
| Module / feature | REQ Components; REPO `vexy_system2/` | `vision_loop.py`, `serial_bridge.py`, live `Serial`/`Camera` sources, baseline capture. Existing `vexy_system2` (bridge/protocol/state/camera_broker) is reusable transport/camera/deploy plumbing. | confirmed |
| Model / entity | REQ Components (Boundary rule) | **No schema defined here.** Import frozen schemas from `contracts`; emit the `vision` block. | confirmed |
| Migration | REQ ADR-11 | **Not applicable** (append-only JSONL). | N/A |
| Endpoint | REQ ADR-04 / OUT of scope | **Not applicable** as an MVP deliverable. (A local dashboard exists in the scaffold; not an API contract.) | N/A |
| Config / secrets | REQ ADR-03/08; REPO `~/.config/vexy-system2/local` | **No secrets.** Device config (serial port/baud) is non-secret, kept off git on the Pi. | confirmed |
| Dependency / new package | REQ ADR-15/09/13; REPO lazy imports | `uv add`. Deps: `pyserial`, `picamera2`, `ultralytics` (YOLO11n+NCNN), an AprilTag lib (`pupil-apriltags`/`robotpy-apriltag`). | confirmed |
| CI / release | — | **Open gap.** | open gap |

## Boundary rules (non-negotiable)

- Live sources implement the `contracts` `TelemetrySource`/`VisionSource` interfaces; `serial_bridge.py`
  merge logic is identical on real hardware vs recorded/synthetic data. *(REQ ADR-01/02.)*
- **No schema defined here** — import from `contracts`. *(REQ Components — Boundary rule.)*
- Transport USB serial @115,200 (RS-485 = Stage-2 high-throughput swap path; relevant to resolving
  the telemetry/ack multiplex). *(REQ ADR-10; WIKI [[vex-coprocessor-pattern]].)*
- Localization via AprilTags. *(REQ ADR-13.)*

## Reusable scaffold (kept, on `main`)

`robot/pi-runtime/` ships working transport + camera + deploy plumbing: `vexy_system2/`
(bridge/protocol/state/camera_broker), `scripts/find_v5_serial.sh`, systemd units, and the verified
`docs/BRAIN_INTERFACE.md`. Build the loop's sources/merge/vision on top of this rather than from
scratch.
