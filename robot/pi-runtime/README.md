# Vexy System 2

Pi-side runtime for using a Raspberry Pi Camera as the System 2 planner for a VEX V5 robot.

The V5 Brain remains System 1: it owns motors, sensors, hard timing, current limits, and fail-safe stops. The Pi/Codex side owns perception, goal reasoning, and high-level command selection.

## Current Hardware State

- Raspberry Pi hostname: `vexy`
- Pi address observed today: `10.10.3.5`
- Camera detected: Raspberry Pi Camera Module 3 Wide, `imx708_wide`
- Codex installed and logged in on the Pi
- V5 Brain: active through the ROS 2 `vex_bridge_node`; this folder is fallback/reference

## Architecture

```text
Pi Camera -> camera broker -> planner/Codex -> bridge -> V5 Brain program -> motors
                                      ^          <- telemetry/acks/watchdog <-
                                      |
                                dashboard/logs
```

The bridge can run in two modes:

- `sim`: fake V5 Brain in-process. This is for today.
- `serial`: real V5 Brain over `/dev/ttyACM*` or `/dev/serial/by-id/*`. The ROS 2 stack is the active live path; this remains a fallback.

## Run Today With Simulated Brain

From the Pi, after cloning this repo:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
PYTHONPATH=src scripts/smoke_test.sh
```

Run the bridge:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
PYTHONPATH=src python3 -m vexy_system2.bridge --mode sim
```

Run the dashboard in another terminal:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
PYTHONPATH=src python3 -m vexy_system2.dashboard --host 0.0.0.0 --port 8080
```

Then open:

```text
http://vexy.local:8080
```

Run the planner demo:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
PYTHONPATH=src python3 -m vexy_system2.planner_demo --goal "hold safe and report telemetry"
```

## Run The Camera Broker

The desktop preview script currently owns the camera:

```text
/home/vexy/Desktop/camera_feed.py
```

Stop it before starting the runtime camera broker:

```bash
cd ~/llm-self-model-capstone/robot/pi-runtime
scripts/stop_desktop_camera.sh
PYTHONPATH=src python3 -m vexy_system2.camera_broker
```

The broker writes:

- `/tmp/vexy-system2/latest.jpg`
- `/tmp/vexy-system2/camera.json`

## V5 Brain Interface (telemetry + commands)

The active live Pi↔Brain interface is now the ROS 2 stack in
`robot/ros2-runtime`. This legacy runtime remains useful as a fallback reference.
The full physical-port and protocol notes are documented in
[`docs/BRAIN_INTERFACE.md`](docs/BRAIN_INTERFACE.md). Quick facts:

- **User (telemetry) port** = `/dev/serial/by-id/…-if02` = `/dev/ttyACM1`. The `…-if00` /
  `ttyACM0` port is the system/upload port and carries no program output.
- **Receive telemetry** through `/vex/telemetry` in ROS, or with no repo/packages:
  `cat /dev/ttyACM1` (add `| grep -a --line-buffered '^{'` to drop the boot banner).
- **Send commands** through ROS `/vex/cmd`; the guarded Brain bridge accepts
  `stop`, `drive`, `turn`, and fixed `routine` slots `2`, `3`, and `4`.

## Telemetry Evidence Scope

This legacy runtime is not the canonical evidence exporter. Downstream MVP
self-modeling uses `contracts.ContractLine` JSONL from
`../../telemetry-fixtures/<run-id>/contract.jsonl` without requiring this runtime,
ROS, MCAP, or hardware. Later real-hardware evidence is captured by
`../ros2-runtime` as MCAP plus an exported contract-valid JSONL handoff.

### Original first-contact checklist

1. Connect the V5 Brain Micro-USB to the Pi.
2. Run `scripts/find_v5_serial.sh`.
3. Load the Brain-side bridge program.
4. Switch `VEXY_BRIDGE_MODE=serial` and set `VEXY_SERIAL_PORT`.
5. Run `scripts/serial_ping_test.sh`.

See `docs/TOMORROW_BRINGUP.md` and `docs/BRAIN_INTERFACE.md`.

## Device Config

Committed defaults live in `config/defaults`.

Real device overrides live only on the Pi:

```text
~/.config/vexy-system2/local
```

That local file uses the same `KEY=value` format, for example:

```bash
VEXY_BRIDGE_MODE=serial
VEXY_SERIAL_PORT=/dev/serial/by-id/YOUR_V5_USER_PORT
```
