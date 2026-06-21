---
topic: VEX V5 Brain stdout serial connectivity issue — ACTUAL root cause (correction to index.md)
slug: v5-serial-connectivity
researched: 2026-06-21
sources: [./sources.md, ./sources-2.md]
---

# Research Correction: V5 Serial Connectivity — Real Root Cause

> Builds on [index.md](index.md). That report's headline hypothesis (controller-vs-
> direct connection, pros-cli #383/#305) was **WRONG for this case** — the Brain was
> always connected directly via USB. The real cause was **PROS hot/cold packaging**.
> This file records only the corrected diagnosis; everything in `index.md` about the
> serial architecture, COBS framing, and port layout remains accurate.

## What actually happened

The Brain was directly connected the whole time (two ports enumerated:
`/dev/cu.usbmodem1201` system, `/dev/cu.usbmodem1203` user — both reporting
`VEX Robotics V5 Brain - E05EA500`). Uploads to the system port succeeded, proving
bidirectional USB comms worked. Yet:

- The program *appeared* to run (Brain showed program name + a counting timer).
- **Zero raw bytes** on both USB ports (confirmed with pyserial reading raw, not just
  `pros terminal`).
- The Brain screen body was **black** — neither LLEMU (`pros::lcd::*`, LVGL-based) nor
  the simplified `pros::screen::*` (vexDisplay-based) API rendered anything.
- The compiled `opcontrol()` was **correct** — verified by `arm-none-eabi-objdump`;
  it looped calling `set_eraser`/`erase`/`screen_print`/`printf`/`fflush`/`delay`.

Two *independent* output subsystems (two display APIs + serial) all silently
no-op'd while correct code ran. That pointed at the layer they share: the calls from
the **hot package** into the **cold package**.

## Root cause: broken hot/cold linkage (false "Library is already onboard")

PROS default `USE_PACKAGE:=1` splits the build into a **cold package** (kernel + libs,
uploaded once) and a **hot package** (user code). Hot-package calls reach library
functions through *veneers* that branch to fixed addresses in the onboard cold
package. `pros upload` kept reporting **"Library is already onboard V5"** — a false
positive: the onboard cold package did not match the hot package's veneer addresses,
so every library call jumped to the wrong address and no-op'd. `pros v5 rm-all` does
not remove the library, and pros-cli 3.5.6 has no force-library flag.

## Fix (verified working)

Set `USE_PACKAGE:=0` in the project `Makefile` to build a **monolith** (everything
linked into one binary — no veneers, no separate cold package):

```bash
pros make clean && pros make     # bin/monolith.bin (~425 KB)
pros upload --after run
```

Immediately after the switch, the user port produced COBS-framed packets and the
screen rendered:

```
b'\x11sout{"tick": 8}\n\x00'      # std::printf -> stdout -> sout packet
b'\rsoutping 17\n\x00\tserrerr \x00\x07serr17\x00\x06serr\n\x00'  # earlier test: sout + serr
```

## Implications for the RPi bridge

The connection-type analysis in `index.md` was a red herring; the RPi will work over a
direct USB connection just as the Mac now does — **provided the Brain program is built
as a monolith**. The hot/cold trap is host-independent, so the same `USE_PACKAGE:=0`
requirement applies regardless of whether the Mac or the Pi performs the upload. For a
raw Pi-side reader, add `pros::c::serctl(SERCTL_DISABLE_COBS, NULL)` to drop COBS
framing (breaks `pros terminal`, fine for pyserial / `cat /dev/ttyACM1`).
