# V5 Brain + PROS — Bring-Up Notes (the detailed story)

This is the **detailed reference** for how we got PROS programs and the PROS CLI working
on this specific V5 Brain, including every non-obvious gotcha we hit and how we proved
the fix. For the terse step-by-step setup, see [TOOLCHAIN.md](TOOLCHAIN.md). For the
Pi↔Brain serial interface (telemetry + commands), see
[../pi-runtime/docs/BRAIN_INTERFACE.md](../pi-runtime/docs/BRAIN_INTERFACE.md).

> **TL;DR of the hard-won lessons**
> 1. Build **monolith** (`USE_PACKAGE:=0`) — the PROS hot/cold split is silently broken on this Brain.
> 2. The PROS CLI 3.5.6 crashes on Python 3.13 until you drop a `version` file in site-packages.
> 3. Use `pros::screen::*` (LVGL 9), **not** `pros::lcd::*` (LLEMU) — the legacy LCD does not render here.
> 4. USB has **two** serial ports: system (upload/control) and user (your stdout). Telemetry comes out the **user** port only.
> 5. For a raw reader (the Pi), disable COBS on the Brain — but that breaks `pros terminal`.

---

## 0. Verified working state (2026-06-21)

- **Hardware:** V5 Brain, System ID `E05EA500`, VEXos **1.1.5.0** (`V1.1.5 (b18)`).
- **Toolchain:** PROS CLI **3.5.6**, PROS kernel **4.2.2**, liblvgl **9.2.0**, ARM GNU toolchain `arm-none-eabi-g++` 15.2.rel1 (Homebrew, at `/opt/homebrew/bin`).
- **Host:** macOS; Python managed by **uv** in `robot/v5-brain/.venv`.
- **Proven:** build → upload → run → `pros::screen` renders → serial telemetry streams out the user port → read on both the Mac (`pyserial`) and the Pi (`cat`). The arm-raise telemetry program (`v5-test/src/main.cpp`) streamed ~100 Hz JSON for 5 motion episodes end-to-end to the Pi.

---

## 1. Repository layout (`robot/v5-brain/`)

```
robot/v5-brain/
├── TOOLCHAIN.md        # terse setup runbook
├── BRINGUP.md          # this file — detailed notes + gotchas
├── pyproject.toml      # host tooling; pins pros-cli (managed by uv)
├── uv.lock             # locked deps (includes pyserial, transitively available)
├── .venv/              # uv-created venv holding the pros CLI (gitignored)
├── v5-test/            # the working PROS project (monolith). Current main.cpp = arm-raise telemetry test
│   ├── Makefile        # USE_PACKAGE:=0  <-- the critical setting
│   ├── src/main.cpp    # program source
│   ├── include/        # depot-managed headers (gitignored; restore with `pros conductor apply`)
│   ├── firmware/       # depot-managed libs/linker scripts (gitignored)
│   └── project.pros    # PROS project manifest (kernel@4.2.2, liblvgl)
└── pros_bridge/        # buildable guarded Pi↔Brain bridge with ack, telemetry, watchdog, routine slots.
```

`firmware/` and `include/` are gitignored because they are large depot artifacts. After a
fresh clone, restore them inside the project dir with `pros conductor apply`.

---

## 2. Getting the PROS CLI working

### 2.1 Install with uv (never pip)
This project manages all Python with **uv**. `pros-cli` is pinned in `pyproject.toml` +
`uv.lock`:
```bash
cd robot/v5-brain
uv venv          # creates .venv
uv sync          # installs pros-cli (3.5.6) and deps
source .venv/bin/activate   # the pros commands below assume the venv is active
```

### 2.2 Gotcha: PROS CLI 3.5.6 crashes on Python 3.13
`pros --version` (and most commands) raise `RuntimeError: Could not determine version`.
Cause: the CLI calls a deprecated `pkg_resources` entry-point API that was removed in
3.13. **Fix** — drop the version string where the code looks for it:
```bash
echo "3.5.6" > .venv/lib/python3.*/site-packages/version
pros --version   # -> pros, version 3.5.6
```
This is a one-time patch after each fresh venv. (A cleaner long-term fix is pinning the
venv to Python ≤3.12, but the `version` file works and is what we use.)

### 2.3 Gotcha: ARM cross-compiler must be on PATH
PROS builds for the Brain's ARM Cortex-A9 with `arm-none-eabi-g++`. Install via
`brew install --cask gcc-arm-embedded` (runs a `sudo` `.pkg` installer — do it in an
interactive terminal). It lands on PATH at `/opt/homebrew/bin/arm-none-eabi-g++`. Verify
with `arm-none-eabi-g++ --version` before building.

### 2.4 CLI commands that actually exist
`pros v5 lsusb` does **not** exist in 3.5.6. The useful subcommands:
```bash
pros v5 status         # firmware version, System ID, connection (uses the system port)
pros v5 ls-files       # files in user slots (does NOT show the cold/library file)
pros v5 run <slot>     # start a program
pros v5 stop           # stop the running program
pros v5 rm-all         # remove user programs (does NOT remove the cold/library package)
pros v5 capture <out.png>   # screenshot the Brain display — invaluable when headless
```
`pros v5 capture` is the single most useful debugging tool when you can't see the Brain
in person — it pulls the actual framebuffer over USB.

---

## 3. The big one: hot/cold packaging is silently broken → build monolith

This cost the most time, so it gets the most detail.

### 3.1 Symptom
A freshly built+uploaded program **appeared to run** — the Brain showed the program name
and a running timer — but:
- the screen body stayed blank/black (no `pros::lcd` *or* `pros::screen` output), and
- **zero bytes** came out of either USB serial port (`pros terminal` showed nothing; raw
  `pyserial` reads returned 0 bytes).

The program didn't crash (timer kept counting), it just did *nothing observable*.

### 3.2 How we proved the code itself was fine
- `arm-none-eabi-objdump -d bin/hot.package.elf` showed `opcontrol()` compiled correctly —
  it looped and called `printf`/`screen`/`delay`. So the source and compile were good.
- The calls went through **veneers**: little trampolines in the hot package that branch to
  fixed addresses inside the separately-uploaded **cold package** (kernel + libs).

### 3.3 Root cause
PROS defaults to **hot/cold linking** (`USE_PACKAGE:=1`): the cold package (PROS kernel +
liblvgl + libc/libm) is uploaded once; only your small "hot" code is re-uploaded each
build. On this Brain, `pros upload` kept printing **"Library is already onboard V5"** — a
*false positive*. The onboard cold package did not match the veneer addresses the hot
package was linked against, so every library call jumped to the wrong address and silently
no-op'd. Notes:
- `pros v5 rm-all` does **not** remove the cold/library package.
- There is **no force-library flag** in `pros upload`.
- `pros v5 ls-files` doesn't even list the library file (different vendor-id category).

### 3.4 Fix — monolith build (verified)
Link everything into one binary, eliminating veneers and the separate cold package:
```makefile
# v5-test/Makefile
USE_PACKAGE:=0
```
```bash
pros make clean && pros make    # produces bin/monolith.bin (~425 KB)
pros upload --after run         # now uploads slot_1.bin = monolith.bin (no "library onboard" line)
```
The instant we switched to monolith, **both** the screen and serial came alive. This is
now the standing rule for this Brain — see the wiki concept
`pros-dependency-compatibility` (applies to **any** added library, e.g. LemLib too).

Trade-off: every upload re-sends the full ~425 KB instead of a small hot package.
Negligible for our use; reliability wins.

---

## 4. Serial architecture (what goes where)

### 4.1 Two USB serial ports
A direct USB connection to the Brain enumerates **two** CDC-ACM interfaces:

| Role | macOS | Linux/Pi (`by-id`) | Purpose |
|------|-------|--------------------|---------|
| **system** | `/dev/cu.usbmodem*1` | `…-if00` → `/dev/ttyACM0` | upload, `pros v5 …`, control |
| **user** | `/dev/cu.usbmodem*3` | `…-if02` → `/dev/ttyACM1` | your program's `stdout`/`stderr` |

Telemetry (`printf`) comes out the **user** port only. (Verified on this Brain: `if02` =
user = `ttyACM1` on the Pi.)

### 4.2 stdout/stderr path on the Brain
`std::printf(...)` → newlib → PROS VFS → `ser_driver` → an in-kernel stream buffer →
flushed by the PROS system daemon → `vexSerialWriteBuffer(1, …)` → USB user port. Always
`std::fflush(stdout)` after a line so it leaves promptly. `stderr` is *guaranteed
delivery* and cannot be disabled.

### 4.3 COBS framing — the key fork in the road
By default PROS **COBS-encodes** everything on the user port and wraps each write with a
4-byte stream id (`sout` for stdout, `serr` for stderr). `pros terminal` decodes this.

- **Want to use `pros terminal`?** Leave COBS on. Output arrives as `sout`/`serr` frames.
- **Want a raw reader (the Pi via `pyserial`/`cat`)?** Disable COBS on the Brain:
  ```cpp
  #include "pros/apix.h"
  pros::c::serctl(SERCTL_DISABLE_COBS, nullptr);   // in initialize()
  ```
  Then the user port carries plain newline-delimited text. **This breaks `pros terminal`**
  (it expects COBS) — verify with a raw read instead. Our telemetry program does exactly
  this because the Pi consumer reads raw JSON.

  Note: the PROS **boot banner** is printed by the system daemon *before* `initialize()`
  runs, so it is still COBS-framed and looks like garbage (`sout … _+=+_ …`) on a raw
  reader. It appears once at program start; downstream parsers should skip non-JSON lines.

### 4.4 Screen output: use `pros::screen`, not `pros::lcd`
The legacy LLEMU API (`pros::lcd::*`) did **not** render on this Brain (PROS 4 ships LVGL
9.2.0; LLEMU is a PROS-3-era shim). The modern, working API:
```cpp
#include "pros/screen.hpp"
pros::screen::set_pen(pros::c::COLOR_WHITE);
pros::screen::print(pros::E_TEXT_LARGE, 1, "hello");   // line-based
```
Colors are in the `pros::c::` namespace (`pros::c::COLOR_WHITE`, etc.). `pros v5 capture`
is the way to confirm what's actually on screen.

---

## 5. The workflow that works (copy-paste)

```bash
cd robot/v5-brain/v5-test
source ../.venv/bin/activate

# build (monolith)
pros make clean && pros make

# upload WITHOUT auto-running (safer when a motor will move)
pros upload --after none

# run / stop on demand (system port)
pros v5 run 1
pros v5 stop

# see the screen even when headless
pros v5 capture /tmp/screen.png

# verify serial on the Mac (COBS disabled -> raw JSON on the user port, device ends in '3')
python - <<'PY'
import serial, time
from serial.tools import list_ports
dev=[p.device for p in list_ports.comports() if 'VEX' in (p.description or '') and p.device.endswith('3')][0]
s=serial.Serial(dev,115200,timeout=0.5); t=time.time()
while time.time()-t<8:
    l=s.readline()
    if l: print(l.decode('utf-8','replace'),end='')
PY
```

(`pyserial` is available via `uv.lock`; run inside the venv.)

---

## 6. Writing a program — patterns proven on this Brain

- **Always** `#include "main.h"`; add `"pros/screen.hpp"`, `"pros/motors.hpp"`,
  `"pros/apix.h"` as needed.
- Emit telemetry with `std::printf(json "\n"); std::fflush(stdout);`.
- Disable COBS in `initialize()` if the Pi will read it raw.
- Motor API (C++): `pros::Motor m(port);` (uses the installed cartridge; negative port or
  flipped target sign to reverse). Telemetry getters that work:
  `get_position()`, `get_actual_velocity()`, `get_current_draw()` (mA), `get_torque()`
  (N·m), `get_temperature()` (°C), `get_voltage()` (mV). Motion: `move_absolute(deg, rpm)`,
  `move_velocity(rpm)`, `move(±127)`, `brake()`, `set_brake_mode(pros::E_MOTOR_BRAKE_HOLD)`,
  `tare_position()`.
- Sample at a fixed cadence with `pros::c::task_delay_until(&now, period_ms)` for
  jitter-free rates (we run 100 Hz / 10 ms).
- **Baud budget:** the user port is 115200 8N1 ≈ 11,520 B/s. Keep lines compact; put
  slow-changing fields (temp, voltage, target) in episode markers, not every sample.
- Bound any motion with a **timeout** and, against real hardware, a **stall guard**
  (abort + `brake()` when current stays high) so a wrong direction/end-stop can't damage
  the geartrain. See `v5-test/src/main.cpp` for a worked example (arm-raise, 5 cycles,
  ~100 Hz telemetry only during the motion).

---

## 7. Gotcha quick-reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| `pros --version` → "Could not determine version" | CLI 3.5.6 on Python 3.13 | `echo "3.5.6" > .venv/lib/python3.*/site-packages/version` |
| `arm-none-eabi-g++: not found` | ARM toolchain missing | `brew install --cask gcc-arm-embedded` |
| Program "runs" but screen blank + 0 serial bytes | hot/cold mismatch ("Library is already onboard" false positive) | `USE_PACKAGE:=0` (monolith), `pros make clean` |
| `pros::lcd::*` shows nothing | LLEMU not supported under LVGL 9 | use `pros::screen::*` |
| `pros terminal` shows nothing | COBS disabled in program | read raw (`pyserial`/`cat`) instead, or re-enable COBS |
| Raw reader shows garbled `sout…` header | PROS boot banner (COBS, pre-`initialize`) | skip non-JSON lines; it's once per run |
| `pros v5 lsusb` → no such command | not in 3.5.6 | use `pros v5 status` |
| 0 bytes on `…*1` / `ttyACM0` | that's the **system** port | read the **user** port (`…*3` / `ttyACM1` / `…-if02`) |

---

## 8. The guarded command bridge

`pros_bridge/` is the active buildable **Pi→Brain command** path: receive
newline JSON over `getchar()`, ack by sequence, stream separate telemetry
records, watchdog-stop on timeout, and run fixed Brain routine slots. It stays
monolith (`USE_PACKAGE:=0`) for this Brain. The current routine slots are:

| Slot | Routine |
|------|---------|
| 2 | 720 spin |
| 3 | arm up/down full cycle |
| 4 | one foot forward/back |

These are routine IDs inside the running bridge program, not separate VEXos
program upload slots. The interface and Pi-side fallback notes are documented in
[../pi-runtime/docs/BRAIN_INTERFACE.md](../pi-runtime/docs/BRAIN_INTERFACE.md).

---

## See also
- [TOOLCHAIN.md](TOOLCHAIN.md) — terse setup steps
- [../pi-runtime/docs/BRAIN_INTERFACE.md](../pi-runtime/docs/BRAIN_INTERFACE.md) — Pi↔Brain interface (telemetry + commands)
- wiki: `knowledge/concepts/pros-dependency-compatibility.md`, `knowledge/entities/tools/pros.md`
- research: `raw/research/v5-serial-connectivity/index-2.md` (the monolith diagnosis)
