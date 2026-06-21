---
topic: VEX V5 Brain stdout serial connectivity issue — why pros terminal drops and how to fix it; RPi impact
slug: v5-serial-connectivity
researched: 2026-06-21
sources: [./sources.md]
---

# Research: VEX V5 Brain Serial Connectivity — Diagnosis & Fix

> **Executive summary**: `pros terminal` is almost certainly failing because the Mac is connected to the **V5 controller** (micro-USB on the joystick), not directly to the **V5 Brain** (USB-C on the back of the Brain). `pros terminal` over a controller connection is a known-broken path in pros-cli 3.5.6 (GitHub issues #383, #305). The fix is to plug into the Brain directly. The same issue would affect the RPi if connected to the controller — it must also plug into the Brain.

---

## Research Questions

1. Why does `pros terminal` immediately drop with "Connection broken" despite the program running?
2. Is stdout actually routed to the USB user port in PROS kernel 4.2.2?
3. How does `pros terminal` read data (raw bytes or packet protocol)?
4. Is the root cause the connection type (controller vs. direct Brain)?
5. Would a Raspberry Pi face the same issue?

---

## Current State (Codebase)

- `robot/v5-brain/v5-test/src/main.cpp`: bare-bones test with `std::puts("ping")` + `std::fflush(stdout)` + `pros::c::serctl(SERCTL_DISABLE_COBS, nullptr)` in `initialize()`
- Two macOS serial ports visible: `/dev/cu.usbmodem1201` (system, upload) and `/dev/cu.usbmodem1203` (user, terminal)
- pros-cli 3.5.6 installed in `.venv/`; `pyserial` is in `uv.lock` (available without install)

---

## Key Findings

### 1. `pros terminal` is NOT reading raw serial [S1, S2]

`pros terminal` uses `V5UserDevice` which COBS-decodes packets. It:
- Opens the user serial port via `pyserial`
- Reads until a null-byte delimiter (`\0`) — the COBS frame boundary
- COBS-decodes the frame
- Asserts the decoded message is ≥ 4 bytes (4-byte stream ID + data)
- Only displays frames with stream ID `sout` or `serr`

`SERCTL_DISABLE_COBS` on the Brain side breaks `pros terminal` because it strips the COBS framing. Raw bytes are meaningless to the terminal reader.

### 2. stdout IS enabled by default in PROS 4.x kernel [S3]

From `src/system/dev/ser_driver.c` in the PROS kernel source:
```c
void ser_driver_initialize(void) {
    ser_driver_runtime_config |= E_COBS_ENABLED;  // COBS on by default
    set_initialize(&enabled_streams_set);
    set_add(&enabled_streams_set, STDOUT_STREAM_ID);  // stdout enabled by default
    ...
}
```
`std::printf` / `std::puts` writes to stdout, which is in the enabled set and will be COBS-encoded and forwarded to the user USB port automatically. No `SERCTL_ACTIVATE` call is needed.

`stderr` is additionally *guaranteed delivery* — it cannot be deactivated even by user code.

### 3. The write guard with `&=` is a bug but not the cause [S3]

```c
if (ser_driver_runtime_config &= E_COBS_ENABLED) {
```
This uses `&=` (bitwise AND-ASSIGN) instead of `&` (read-only test). This corrupts the config if other flags are set, but with a single flag `E_COBS_ENABLED=1` it behaves correctly in practice.

### 4. `pros terminal` over a controller connection is a known broken path [S4, S5]

GitHub issues #383 and #305 both document that `pros terminal` produces no output and the connection immediately drops when the computer is plugged into the **V5 controller** (radio tether mode) rather than directly into the Brain. The root cause per vexide deep-dive [S6]:

> "This method of communication only has one serial port (this port is often named a controller port). This port acts the same way as the system port in a direct brain connection. For this reason, stdio output has to be received with a UserFifoPacket. The response to this packet contains the incoming stdout buffer."

`pros-cli 3.5.6` does NOT implement `UserFifoPacket` — it only reads raw COBS from the user serial port. Over a controller connection there is no user port, so `serial.read()` immediately raises `SerialException` → `PortConnectionException` → "Connection broken".

### 5. Port-selection logic on macOS [S2]

pros-cli identifies the user port on macOS by checking which `/dev/cu.usbmodem*` device ends in `'3'`. With a direct Brain connection this correctly finds `1203`. However, if connected via the controller, the single controller port may enumerate as `*1` or `*3` depending on the OS, and the logic can misidentify it.

### 6. SD card is irrelevant [S7]

The PROS filesystem docs mention SD cards only for `fopen()`/`fwrite()` file I/O. The stdout serial stream is forwarded over the USB user port entirely in-kernel — no SD card is needed or involved.

---

## Constraints

- pros-cli 3.5.6 does not support `UserFifoPacket` (controller terminal mode)
- The Brain must be directly connected via its USB-C port for the user serial port to work
- `pyserial` is already available via `uv.lock` — no new install needed
- The RPi use-case will NOT use `pros terminal`; it will read the serial port via Python

---

## Solution Comparison

| Approach | Works now | Works on RPi | Notes |
|----------|-----------|--------------|-------|
| Connect USB to Brain directly (USB-C port on back) | ✓ | ✓ | Correct fix; `pros terminal` and pyserial both work |
| Connect USB to controller, use `UserFifoPacket` | ✗ | ✗ | Not implemented in pros-cli 3.5.6 |
| Write to `stderr` instead of `stdout` | ✓ (with direct) | ✓ | `stderr` is guaranteed-delivery, same wire |

---

## Recommendation

**Connect the USB cable to the V5 Brain's USB-C port, not the controller.**

With that change:
1. Remove `serctl(SERCTL_DISABLE_COBS, nullptr)` — stdout is COBS-encoded by default and `pros terminal` decodes it
2. Use `std::printf` / `std::puts` + `std::fflush(stdout)` as normal
3. `pros terminal` will show output cleanly

For the RPi serial bridge:
- Connect RPi to Brain via USB (Brain's USB-C → RPi USB-A)
- On the RPi two devices appear: `/dev/ttyACM0` (system) and `/dev/ttyACM1` (user)
- Read from `/dev/ttyACM1` with pyserial: `serial.Serial('/dev/ttyACM1', 115200)`
- THEN call `serctl(SERCTL_DISABLE_COBS, nullptr)` in the Brain program so the RPi reads raw newline-delimited JSON without COBS decoding
- `pros terminal` will NOT work when COBS is disabled; use pyserial or `cat /dev/ttyACM1` on RPi instead

**Quick test right now**: plug into Brain directly, run `pros terminal` — it should start displaying JSON heartbeats.

---

## Next Steps

- Replug USB cable from controller to Brain USB-C → run `pros terminal`
- Restore the full heartbeat program (with LCD + printf) — remove `serctl` call for `pros terminal` testing
- When building the Pi bridge, re-add `serctl(SERCTL_DISABLE_COBS)` and use raw pyserial reads on the Pi
- `/task-add` — Pi-side serial reader: open `/dev/ttyACM1`, read JSONL, pipe to LLM telemetry pipeline
