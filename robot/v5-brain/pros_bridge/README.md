# V5 Brain Bridge

Buildable PROS project for the V5 Brain side of the Pi/ROS serial bridge.

This bridge is intentionally conservative for the first physical ack/telemetry proof:

- `USE_PACKAGE:=0` monolith build, matching the proven `v5-test` workaround for this Brain.
- COBS disabled in `initialize()` so the Pi reads raw newline-delimited JSON.
- `heartbeat` and `stop` packets ack `state:"ok"`.
- `drive`, `turn`, and `set_goal` packets ack `state:"rejected"` with `fault:"motion_disabled"` until motor ports and safety limits are mapped.
- A separate telemetry task emits `type:"telemetry"` records every 500 ms so the ROS bridge can prove `/vex/telemetry` independently from `/vex/ack`.

Build from this directory:

```bash
source ../.venv/bin/activate
pros conductor apply kernel@4.2.2 liblvgl@9.2.0 --force-apply
pros make clean && pros make
```

The host must use the full Arm GNU embedded toolchain from the `gcc-arm-embedded`
cask. Homebrew's `arm-none-eabi-gcc` formula is built without the standard
newlib/libstdc++ headers and fails on PROS headers such as `<cerrno>`.

Upload/run only when the V5 Brain is connected to the host running PROS:

```bash
pros upload --after run
```
