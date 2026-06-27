# ai-sdd Conventions — `coprocessor` vertical

> **Root:** `robot/ros2-runtime/` (the active Raspberry Pi 5 runtime).

**Vertical.** `coprocessor` — Raspberry Pi 5 runtime: ROS 2 Jazzy camera
pipeline, V5 Brain serial bridge, MCAP capture, topic JSONL capture, and
ContractLine JSONL export. It is also the host for the online-control harness
(see the [`pilot`](pilot.md) vertical). Root: `robot/ros2-runtime/`.

## Discovery Record

| Change type | Evidence | Convention | Status |
|---|---|---|---|
| Build / install | REQ Tech stacks; REPO `robot/ros2-runtime/pyproject.toml`; ROS package metadata | Use **`uv`** for Python deps/dev tooling and ROS 2 Jazzy/ament for deployment. `uv sync` works from `robot/ros2-runtime/`. | confirmed |
| Test | REQ Verification & Reviewer Runbook; REPO tests | `uv run pytest`; focused operator/export smoke: `PYTHONPATH=src:../../contracts/src uv run pytest tests/test_operator.py tests/test_evidence_export.py -q`. | confirmed |
| Lint / format | REQ ADR-16 | `ruff` only; `ruff check` + `ruff format --check`. | confirmed |
| Validate | REQ ADR-06 | Contract validation imports frozen schemas from `contracts`; no schemas are defined here. | confirmed |
| Language | REQ ADR-05; Tech stacks | **Python 3.12** on Ubuntu 24.04 + ROS 2 Jazzy. | confirmed |
| Serial transport | REPO `docs/BRAIN_INTERFACE.md`, `src/vexy_ros/vex_bridge_node.py` | Read the **USER port** (`/dev/serial/by-id/...-if02`), 115200 8N1, newline JSON, COBS-off, filter the one-time boot banner. `pyserial`. | confirmed |
| Telemetry / ack demux | REPO `vex_bridge_node.py`, `bridge_demux.py` | Continuous reader thread demuxes `ack`, `telemetry`, and `bridge_status` before motion proof interpretation. | confirmed |
| Vision | REQ Components; REPO launch/config/docs | `camera_ros` + measured `CameraInfo` + `image_proc` rectification + `apriltag_ros` + `scene_map_node`; object detection publishes structured vision topic JSON. | confirmed |
| Capture / export | REPO `operator_run_capture.py`, `telemetry_writer_node.py`, `evidence_export.py` | Capture MCAP + per-topic JSONL; export `/operator/results` to canonical `contract.jsonl`. | confirmed |
| Command path / control | REPO `docs/PROTOCOL.md`, `bridge_protocol.py` | Commands use fixed protocol-v1 JSON and are clamped/validated before Brain delivery. | confirmed |
| Model / entity | REQ Components (Boundary rule) | **No schema defined here.** Import frozen schemas from `contracts`. | confirmed |
| Config / secrets | REQ ADR-03/08 | No secrets in repo. Device-local config, model artifacts, logs, frames, bags, captures, and proof output stay off git. | confirmed |

## Boundary rules

- Live sources implement or feed the `contracts` telemetry/vision boundaries; downstream self-modeling consumes ContractLine JSONL, not ROS topics directly.
- **No schema defined here** — import from `contracts`.
- Brain owns motors and timing; the Pi sends bounded high-level commands only.
- Raw evidence is replayable MCAP/topic JSONL; semantic handoff is contract-valid `contract.jsonl`.
