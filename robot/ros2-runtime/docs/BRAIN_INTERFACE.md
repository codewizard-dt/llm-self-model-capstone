# Pi <-> V5 Brain Interface

The active Raspberry Pi runtime is `robot/ros2-runtime/`. It talks to the V5
Brain over the V5 user serial interface using protocol-v1 newline-delimited
JSON. The ROS bridge (`vexy_ros.vex_bridge_node`) demultiplexes Brain
acknowledgements, telemetry, and bridge faults onto ROS topics.

## Physical Layer

A direct USB connection from the Brain to the Pi enumerates two CDC-ACM serial
interfaces:

- `if00` / system port: PROS upload/control; not used for robot telemetry.
- `if02` / user port: running program stdout/stderr; used for telemetry and
  command/ack traffic.

Prefer `/dev/serial/by-id/*-if02` over bare `/dev/ttyACM*`, because the bare
numbers can reorder. The V5 CDC-ACM port effectively ignores baud, but the ROS
bridge opens it at `115200 8N1`. The Pi user must be in `dialout`.

## Telemetry

The guarded PROS firmware disables COBS with
`pros::c::serctl(SERCTL_DISABLE_COBS, nullptr)` and emits raw JSON records on
the user port. The PROS boot banner can still appear before COBS is disabled, so
raw readers must ignore non-JSON lines.

The active ROS bridge publishes:

- `/vex/ack` for command acknowledgements.
- `/vex/telemetry` for Brain telemetry.
- `/vex/bridge_status` for bridge health and faults.

## Commands

Pi-to-Brain commands are protocol-v1 newline-delimited JSON. See
[PROTOCOL.md](PROTOCOL.md) and
[`bridge_protocol.py`](../src/vexy_ros/bridge_protocol.py) for the authoritative
Pi-side validator. The Brain-side implementation lives in
`robot/v5-brain/pros_bridge/src/main.cpp`.
