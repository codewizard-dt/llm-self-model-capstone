# Pi ↔ V5 Brain Interface

How the Raspberry Pi (`vexy`, System 2) talks to the V5 Brain (System 1) over USB:
the physical layer, **receiving telemetry** (verified working), and **sending commands**
(designed but not yet attempted on hardware).

Related docs:
- [PROTOCOL.md](PROTOCOL.md) — the command/ack wire format (Pi→Brain).
- [ARCHITECTURE.md](ARCHITECTURE.md) — the System 1 / System 2 split.
- [TOMORROW_BRINGUP.md](TOMORROW_BRINGUP.md) — original first-contact checklist.
- [../../v5-brain/BRINGUP.md](../../v5-brain/BRINGUP.md) — the Brain/PROS side in detail.

> **Status (2026-06-21):** Telemetry **Brain→Pi** is verified end-to-end (~100 Hz JSON,
> read live over SSH). Commands **Pi→Brain** are **not yet tried** — the protocol and the
> `bridge.py serial` path exist, but no Brain-side program has consumed a command yet, and
> there is an unresolved design tension between continuous telemetry and request/response
> acks on the single user port (see §3.3).

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

## 3. Sending commands (Pi → Brain) — NOT YET ATTEMPTED

The command path is designed but unproven on hardware. Here's what exists and what's open.

### 3.1 Wire format (see [PROTOCOL.md](PROTOCOL.md))
Pi→Brain commands are newline-delimited JSON with `v`/`seq`/`type`/`sent_ms`/`ttl_ms`:
```json
{"v":1,"seq":2,"type":"cmd","cmd":"drive","sent_ms":...,"ttl_ms":200,"vx":0.1,"vy":0.0,"omega":0.0}
{"v":1,"seq":4,"type":"heartbeat","sent_ms":...,"ttl_ms":200}
```
Brain→Pi ack:
```json
{"v":1,"ack":2,"type":"ack","state":"ok","recv_ms":...,"battery_mv":12300,"heading_deg":12.3,"fault":null}
```
`src/vexy_system2/protocol.py` already builds/validates/clamps these
(`MAX_LINEAR=0.35`, `MAX_OMEGA=0.6`, `ttl_ms` clamped to ≤1000). For our capstone the
first real command will more likely be an **arm action** (e.g. `{"cmd":"arm","deg":300}`) —
the `drive`/`turn` vocabulary is drivetrain-oriented and will need extending for the arm.

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

### 3.3 ⚠️ The core unresolved tension: telemetry stream vs. request/response acks
The two directions both use the **same single user port**, and they assume conflicting I/O
models:
- **Telemetry** (today) = the Brain *continuously pushes* JSON lines at ~100 Hz.
- **Commands** (`bridge.py`) = the Pi writes one packet and `readline()`s **the next line**
  as the ack.

If both run at once, `bridge.py`'s `readline()` will grab whatever telemetry line happens
to be next, not the ack. This must be reconciled before commands will work. Options:
1. **Tagged multiplexing (recommended):** keep one stream; the Brain tags every line
   (`"type":"telemetry"` vs `"type":"ack"`), and the Pi reader demuxes by `type` instead of
   "next line = ack". Requires replacing `bridge.py`'s naive write-then-readline with a
   reader thread + a `seq→ack` map.
2. **Quiet-during-command:** Brain only streams telemetry during actions and goes silent
   otherwise (the test already does this) so acks for idle-time commands aren't interleaved
   — fragile once an action *is* running.
3. **Second channel:** move high-rate telemetry to a **Smart Port RS-485** link (PROS
   `pros::Serial`, up to 921,600 baud) and keep USB for command/ack. Cleanest separation,
   most hardware work (RS-485↔TTL adapter to the Pi UART). See wiki
   `vex-coprocessor-pattern`.

### 3.4 Brain side: required program structure (the `pros_bridge` sketch)
`v5-brain/pros_bridge/src/main.cpp` is a starter sketch (not yet a buildable project). The
proven-correct structure for bidirectional comms is **two FreeRTOS tasks** so a blocked
read can't starve safety:
- **receive task:** `getchar()` loop → assemble line → parse → clamp → act → ack.
- **watchdog task:** if `millis() - last_packet_ms > WATCHDOG_MS` → stop all motors.
A single combined loop **deadlocks** (blocked on `getchar()` while needing to send). The
watchdog must be its own task so it ticks even when the receiver is blocked. When promoting
the sketch: `pros conductor new-project pros_bridge v5`, set `USE_PACKAGE:=0` (monolith —
mandatory on this Brain), add `serctl(SERCTL_DISABLE_COBS)`, and decide the §3.3 multiplex
strategy first.

### 3.5 Safety model (from PROTOCOL.md, enforce on the Brain)
- Reject malformed JSON and unknown commands (ack `state:"rejected"`).
- Clamp every velocity/setpoint.
- Stop on watchdog (no valid packet within the interval) and on per-command `ttl_ms`
  expiry.
- Pi treats a missing ack as a fault and sends `stop` on reconnect.

---

## 4. Bring-up checklist for commands (when we get there)

1. Decide the telemetry/ack multiplex strategy (§3.3) — do this **first**.
2. Promote `pros_bridge` to a real monolith PROS project; implement the two-task pattern +
   `serctl(SERCTL_DISABLE_COBS)`.
3. Extend `protocol.py` (and PROTOCOL.md) with the **arm** command vocabulary.
4. Put the repo (or just `src/`) on the Pi; set `VEXY_*` in `~/.config/vexy-system2/local`.
5. Loopback first: `scripts/serial_ping_test.sh` → expect an ack per command, watchdog stop
   on silence.
6. Only then connect motors and test a real commanded arm-raise, with the stall-guard +
   timeout from the telemetry program carried over.

## 5. Open questions
- Final command vocabulary for the **arm** (and later drivetrain) — fields, units, TTLs.
- Multiplex design (§3.3) — tagged single-stream vs. RS-485 second channel.
- Where ack/telemetry timestamps are reconciled (`t` is ms-since-boot on the Brain; the Pi
  stamps wall-clock `recv_ms`) for gap/latency analysis.
- Whether `bridge.py` becomes a reader-thread + seq-map design, or is replaced by a purpose
  -built duplex client.
