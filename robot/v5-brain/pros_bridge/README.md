# V5 Brain Bridge

Buildable PROS project for the V5 Brain side of the Pi/ROS serial bridge.

This bridge is intentionally conservative for physical proof:

- `USE_PACKAGE:=0` monolith build, matching the proven `v5-test` workaround for this Brain.
- COBS disabled in `initialize()` so the Pi reads raw newline-delimited JSON.
- `heartbeat` and `stop` packets ack `state:"ok"`.
- `drive` and `turn` packets are accepted only when drive motors are present on ports `1` and `10`.
- `routine` packets are accepted only for fixed slots `2`, `3`, and `4`.
- `release` packets stop the drive and run the ball-release motor on port `3` for a bounded `duration_ms`; missing release hardware is rejected.
- Motion commands are clamped, TTL-limited, watchdog-stopped, and current/voltage-limited.
- `set_goal` is rejected by the Brain; higher-level goals stay in ROS.
- A separate telemetry task emits `type:"telemetry"` records every 500 ms so the ROS bridge can prove `/vex/telemetry` independently from `/vex/ack`.
- Telemetry includes `motor_samples` for `left_drive`, `right_drive`, and `arm` using the same field names required by the contract JSONL exporter.

## Brain routine slots

These are routine IDs inside the running bridge program. They are not VEXos
program upload slots; keep the bridge uploaded/running and send `cmd:"routine"`
from the Pi.

| Slot | Routine | Bounds |
|------|---------|--------|
| 2 | `spin_720` | timed 29 s spin at 0.45 rad/s, repeated short drive TTLs |
| 3 | `arm_full_cycle` | arm motor on port 8 to 300 motor-deg target, pause, return to 0 with stall/timeout guard |
| 4 | `one_foot_forward_back` | encoder-derived 0.3048 m forward and back using the current wheel constant |

Example packet:

```json
{"v":1,"seq":200002,"type":"cmd","cmd":"routine","sent_ms":1,"ttl_ms":500,"slot":2}
```

`stop`, estop, or watchdog loss cancels the active routine and brakes all
configured motors. New drive/turn/routine commands are rejected with
`fault:"busy"` while a routine is active.

Build from this directory:

```bash
source ../.venv/bin/activate
pros conductor apply kernel@4.2.2 liblvgl@9.2.0 --force-apply
pros make clean && pros make
```

The host must use the full Arm GNU embedded toolchain from the `gcc-arm-embedded`
cask. Homebrew's `arm-none-eabi-gcc` formula is built without the standard
newlib/libstdc++ headers and fails on PROS headers such as `<cerrno>`.

Upload/run only when the V5 Brain is connected to the host running PROS. Slot 4
is the canonical return-home slot; the project upload options pin this metadata,
but the command should still pass `--slot 4` explicitly for proof captures:

```bash
pros upload --slot 4 \
  --name "Slot 4 Return Home" \
  --description "Slot 4 Return Home: guarded ROS bridge for home:tag" \
  --after none
pros v5 ls-files
pros v5 run 4
```

See `../SLOT_MANIFEST.md` for the full physical fact-check checklist before
claiming slot 4 is loaded.
