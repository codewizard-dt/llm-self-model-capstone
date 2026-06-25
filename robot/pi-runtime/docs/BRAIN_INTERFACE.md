# Pi ↔ V5 Brain Interface

How the Raspberry Pi (`vexy`, System 2) talks to the V5 Brain (System 1) over USB:
the physical layer, **receiving telemetry** (verified working), and **sending commands**
(now handled by the ROS 2 `vex_bridge_node` live path).

Related docs:
- [PROTOCOL.md](PROTOCOL.md) — the command/ack wire format (Pi→Brain).
- [ARCHITECTURE.md](ARCHITECTURE.md) — the System 1 / System 2 split.
- [TOMORROW_BRINGUP.md](TOMORROW_BRINGUP.md) — original first-contact checklist.
- [../../v5-brain/BRINGUP.md](../../v5-brain/BRINGUP.md) — the Brain/PROS side in detail.

> **Status (2026-06-25):** The active live path is ROS 2 Jazzy:
> `vex_bridge_node` demuxes `/vex/ack`, `/vex/telemetry`, and `/vex/bridge_status`
> from the guarded PROS `pros_bridge` firmware. The legacy `robot/pi-runtime`
> protocol remains as a fallback reference only.

---

## 1. Physical layer

A direct Micro-USB → USB-A connection from the Brain to the Pi enumerates **two**
CDC-ACM serial interfaces. Confirmed on this Brain (System ID `E05EA500`):

```
$ ls -l /dev/serial/by-id/
…V5_Brain_-_E05EA500-if00 -> ../../ttyACM0    # SYSTEM port: upload / pros control
…V5_Brain_-_E05EA500-if02 -> ../../ttyACM1    # USER port:   program stdout/stderr  <-- telemetry
```

- **Read telemetry from the USER port** = `…-if02` = `/dev/ttyACM1`. `ttyACM0`/`if00` is
  the system port and carries no program output.
- Prefer the stable `by-id` symlink over `ttyACM*` (the bare numbers can reorder).
- Line settings: **115200 8N1**. (The V5 CDC-ACM effectively ignores baud, so `cat` works
  without `stty`, but `pyserial` should still open at 115200.)
- Throughput ceiling ≈ **11,520 B/s**. Keep telemetry lines compact.
- Permissions: the Pi user needs `dialout` (`sudo usermod -aG dialout vexy`, re-login) or
  use `sudo` to read the device.

---

## 2. Receiving telemetry (Brain → Pi) — VERIFIED

### 2.1 Format
The Brain program disables COBS (`pros::c::serctl(SERCTL_DISABLE_COBS, nullptr)`) and emits
**plain newline-delimited JSON** on the user port via `printf` + `fflush`. The current
arm-raise test (`v5-brain/v5-test/src/main.cpp`) emits, per raise episode:

```json
{"event":"raise_start","ep":1,"t":5,"tgt_deg":300,"vel_rpm":50,"temp_c":40,"volt_mv":209}
{"t":185,"pos":77.0,"vel":57,"cur":1167,"trq":0.48}      // ~48 of these, ~100 Hz, during motion only
{"event":"raise_end","ep":1,"t":485,"pos_deg":295.0,"reached":true,"fault":null,"dur_ms":480,"peak_cur_ma":1167,"samples":49}
{"event":"run_done","cycles":5,"t":9627}
```

Per-sample fields: `t` (ms since program start), `pos` (deg), `vel` (RPM), `cur` (mA),
`trq` (N·m). Slow-changing fields (temperature, voltage, target) live in the
`*_start`/`*_end` markers to save bandwidth. Telemetry streams **only during the action**;
the Brain is silent between episodes.

### 2.2 The one caveat: boot banner
The PROS system daemon prints a startup banner **before** the program disables COBS, so the
first ~18 lines on a raw reader are COBS-framed garbage (`sout … Powered by PROS … `). It
appears **once per program start**. Always filter to JSON lines.

### 2.3 Reading it (no repo or packages required)
```bash
# simplest: see everything (banner once, then JSON)
cat /dev/ttyACM1

# clean + logged: keep only JSON objects, tee to a session file
cat /dev/serial/by-id/usb-VEX_Robotics__Inc_VEX_Robotics_V5_Brain_-_E05EA500-if02 \
  | grep -a --line-buffered '^{' \
  | tee session_$(date +%Y%m%d_%H%M%S).jsonl
```
**`grep -a` is required** — without it grep sees the banner's escape bytes, declares the
stream "binary", and prints `binary file matches` instead of your data (this bit us).

`pyserial` equivalent (matches what `bridge.py` uses):
```python
import serial
s = serial.Serial('/dev/ttyACM1', 115200, timeout=2)
while True:
    line = s.readline()
    if line:
        print(line.decode('utf-8', 'replace'), end='')
```

Trigger a run from the **Brain touchscreen** (select slot 1 → Run) — no Pi-side launcher
needed.

### 2.4 Toward the LLM pipeline
Persist as **JSONL**, one file per session (`session_<ts>.jsonl`), append-only. That feeds
the Task Telemetry Contract / Claude loop (Mode A real-time or Mode B batch). See the wiki
`vex-v5-telemetry-pipeline` source page.

---

## 3. Sending commands (Pi → Brain)

The command path uses tagged JSON records on the V5 user serial port.

### 3.1 Wire format (see [PROTOCOL.md](PROTOCOL.md))
Pi→Brain commands are newline-delimited JSON with `v`/`seq`/`type`/`sent_ms`/`ttl_ms`:
```json
{"v":1,"seq":2,"type":"cmd","cmd":"drive","sent_ms":...,"ttl_ms":200,"vx":0.1,"vy":0.0,"omega":0.0}
{"v":1,"seq":3,"type":"cmd","cmd":"routine","sent_ms":...,"ttl_ms":500,"slot":2}
{"v":1,"seq":4,"type":"heartbeat","sent_ms":...,"ttl_ms":200}
```
Brain→Pi ack:
```json
{"v":1,"ack":2,"type":"ack","state":"ok","recv_ms":...,"battery_mv":12300,"drive_ports_ok":true,"arm_port_ok":true,"routine_active":false,"fault":null}
```
`src/vexy_system2/protocol.py` builds/validates/clamps the legacy fallback shape.
The active ROS validator in `robot/ros2-runtime/src/vexy_ros/bridge_protocol.py`
accepts `stop`, `drive`, `turn`, `set_goal`, and the fixed `routine` slots `2`,
`3`, and `4`.

### 3.2 Pi side: `bridge.py --mode serial`
`SerialV5Brain.handle()` does `serial.write(encode(packet)); flush(); line = readline()`
— i.e. **write a command, then block for one ack line** (0.4 s timeout). Configure:
```bash
# ~/.config/vexy-system2/local
VEXY_BRIDGE_MODE=serial
VEXY_SERIAL_PORT=/dev/serial/by-id/usb-VEX_Robotics__Inc_VEX_Robotics_V5_Brain_-_E05EA500-if02
VEXY_SERIAL_BAUD=115200
```
then `scripts/serial_ping_test.sh`. **Note:** the repo is **not currently on the Pi** — to
use `bridge.py`/scripts you'd clone it there (or scp the `src/` tree). For telemetry-only,
the repo is not needed (see §2.3).

### 3.3 Tagged multiplexing
The ROS bridge resolved the original telemetry/ack tension with tagged
multiplexing: the Brain emits `type:"ack"`, `type:"telemetry"`, and
`type:"bridge_status"` records, and the Pi demuxes by `type` instead of assuming
"next line = ack".

### 3.4 Brain side: required program structure (`pros_bridge`)
`v5-brain/pros_bridge/src/main.cpp` is now a buildable monolith PROS project.
The structure is multiple FreeRTOS tasks so a blocked read cannot starve safety:
- **receive task:** `getchar()` loop → assemble line → parse → clamp → act → ack.
- **watchdog task:** if `millis() - last_packet_ms > WATCHDOG_MS` → stop all motors.
- **telemetry task:** emits `type:"telemetry"` records independently from acks.
- **routine task:** runs fixed Brain routine slots 2-4 without blocking receive/heartbeat reads.

### 3.5 Safety model (from PROTOCOL.md, enforce on the Brain)
- Reject malformed JSON and unknown commands (ack `state:"rejected"`).
- Clamp every velocity/setpoint.
- Stop on watchdog (no valid packet within the interval) and on per-command `ttl_ms`
  expiry.
- Pi treats a missing ack as a fault and sends `stop` on reconnect.

---

## 4. Bring-up checklist for commands (when we get there)

1. Source the ROS workspace and confirm `/vex/ack` plus `/vex/telemetry`.
2. Confirm `drive_ports_ok:true`, `arm_port_ok:true` when testing slots that need them.
3. Record MCAP before dispatching a Brain routine.
4. Dispatch `routine:2`, `routine:3`, or `routine:4` through `/task_plan/request`
   or publish `cmd:"routine"` directly to `/vex/cmd`.
5. Send `cmd:"stop"` to cancel any active routine.

## 5. Open questions
- Whether future arm/claw actions should remain fixed Brain routines or graduate
  to separate `arm`/`claw` command verbs in the live firmware.
- Where ack/telemetry timestamps are reconciled (`t` is ms-since-boot on the Brain; the Pi
  stamps wall-clock `recv_ms`) for gap/latency analysis.
- Whether the legacy `bridge.py` should be retired now that ROS owns the live duplex client.
