# Vexy Runtime Architecture

## Roles

System 2 runs on the Raspberry Pi.

- Owns camera capture and frame summarization.
- Runs Codex or another planner.
- Converts goals into short-lived high-level robot intents.
- Logs what it thought it saw and what it sent.

System 1 runs on the V5 Brain.

- Owns motors and timing.
- Validates commands from the Pi.
- Applies speed/current/acceleration limits.
- Executes closed-loop drive behavior.
- Stops safely when commands expire.

The Pi should never be the only safety layer. Every command has a TTL and every moving command must be safe to ignore, reject, or expire.

## Evidence Boundary

This legacy runtime is a fallback/reference path, not the canonical downstream
self-modeling evidence source. MVP self-modeling features consume
`contracts.ContractLine` JSONL from `telemetry-fixtures/<run-id>/contract.jsonl`.
Later real hardware runs are captured in the ROS 2 runtime as replayable MCAP
and exported to the same JSONL shape.

## Runtime Components

- `camera_broker`: the only process that opens the Pi camera.
- `bridge`: local TCP command server that forwards to a fake or real V5 Brain.
- `planner_demo`: tiny Codex/planner stand-in that sends heartbeats and safe commands.
- `dashboard`: local web surface for latest frame, state, and stop command.

## Data Flow

```text
camera_broker -> /tmp/vexy-system2/latest.jpg
camera_broker -> /tmp/vexy-system2/camera.json
planner       -> bridge TCP 127.0.0.1:8765
bridge        -> /tmp/vexy-system2/bridge.json
dashboard     -> bridge TCP 127.0.0.1:8765
bridge        -> V5 USB serial fallback (ROS 2 owns the active live path)
```

## Why One Camera Owner

The Pi camera pipeline is exclusive. Today `/home/vexy/Desktop/camera_feed.py` was holding `/dev/media0` and `/dev/media1`, causing `rpicam-still` to fail with `Pipeline handler in use by another process`.

The robot runtime should replace ad hoc camera readers with one owner and publish frames/observations to other processes.
