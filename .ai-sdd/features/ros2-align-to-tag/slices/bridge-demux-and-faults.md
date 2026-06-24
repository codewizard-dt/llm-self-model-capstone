# Slice: bridge-demux-and-faults

| Field | Value |
|---|---|
| Feature | ros2-align-to-tag |
| Stack | coprocessor |
| Depends on | - |

## What this slice delivers

Refactor the ROS VEX bridge so the serial stream is truthfully demultiplexed before any motion proof. The current `vex_bridge_node.py` writes a command and synchronously reads one line back, which fails when Brain acknowledgements and streaming telemetry share the same USER-port stream. This slice ports the proven `robot/pi-runtime` reader-thread pattern into `robot/ros2-runtime` while keeping newline JSON v1.

## Scope

- Keep wire protocol v1: newline-delimited JSON at 115200 baud.
- Add a dedicated serial reader loop/thread that continuously reads Brain lines and classifies them.
- Publish acknowledgement lines separately from telemetry lines.
- Preserve or document the compatibility behavior of existing `/vex/telemetry` consumers.
- Publish bridge fault/status state for missing ack, stale telemetry, serial disconnect, bad JSON, and unsupported protocol.
- Track pending command sequence numbers so ack timeout is reported by command/heartbeat, not inferred from a random serial read.
- Ensure stop/heartbeat commands still use TTLs and Brain watchdog behavior.
- Add fake-serial tests that do not require hardware.
- Update ROS runtime docs/runbook for the new ack, telemetry, and status topics.

## Suggested implementation shape

- `robot/ros2-runtime/src/vexy_ros/vex_bridge_node.py`
  - split serial write lock from reader loop
  - classify `{"type":"ack"}` / `{"ack":...}` as ack
  - classify telemetry/sample/event records as telemetry
  - classify malformed/unknown records as fault/status
- Publish at minimum:
  - `/vex/ack`
  - `/vex/telemetry`
  - `/vex/bridge_status`
- If the existing `/vex/telemetry` ack behavior must be kept for compatibility, preserve it behind a documented compatibility topic or parameter; do not leave ack and telemetry ambiguous by default.

## Acceptance

1. Fake serial input containing interleaved telemetry and acks routes ack records to `/vex/ack` and telemetry records to `/vex/telemetry`.
2. A command ack with the expected sequence clears the pending command before timeout.
3. Missing ack produces a fault/status record without blocking the reader loop.
4. Bad JSON from the Brain produces a fault/status record and does not crash the node.
5. Serial disconnect produces a fault/status record and prevents further command writes until reconnect/restart.
6. Heartbeat and stop packets still include bounded `ttl_ms`.
7. Unit tests cover demux, ack matching, timeout, and bad-line behavior without hardware.
8. `robot/ros2-runtime/docs/RUNBOOK.md` distinguishes serial ack proof from motion proof.

## Out of scope

- Binary protocol v2 or CRC framing.
- Brain firmware rewrite beyond what is strictly needed to consume/emit JSON v1 records.
- `AlignToTag` logic.
