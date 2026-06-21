---
topic: VEX V5 Brain stdout serial connectivity issue — ACTUAL root cause (correction)
slug: v5-serial-connectivity
researched: 2026-06-21
---

# Primary Sources — V5 Serial Connectivity (Correction)

> Companion to [index-2.md](index-2.md). These are the diagnostic observations that
> overturned the original hypothesis. Builds on [sources.md](sources.md).

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S8  | hardware | `pros v5 status` on Brain E05EA500 | 2026-06-21 | VEXos System 1.1.5-0, CPU1 SDK 1.1.5-18; uploads succeed → USB comms OK both directions |
| S9  | hardware | pyserial raw read of `/dev/cu.usbmodem1203` (user) and `1201` (system) | 2026-06-21 | Hot/cold build: 0 raw bytes on both ports. Monolith build: COBS `sout`/`serr` packets flowed |
| S10 | codebase | `arm-none-eabi-objdump -d bin/hot.package.elf` → `<opcontrol>` | 2026-06-21 | User code compiled correctly; library calls route through veneers to fixed cold-package addresses |
| S11 | hardware | `pros v5 capture` Brain screen, hot/cold vs monolith | 2026-06-21 | Hot/cold: black body, no draws. Monolith: "tick: N" rendered → display works |
| S12 | codebase | `pros upload` output + `robot/v5-brain/v5-test/Makefile::USE_PACKAGE` | 2026-06-21 | "Library is already onboard V5" false positive; `USE_PACKAGE:=0` (monolith) is the fix |

## Excerpts

### S9 — pyserial raw read, monolith build
```
=== READ /dev/cu.usbmodem1203 for 6s ===
b'\x11sout{"tick": 8}\n\x00'
b'\x11sout{"tick": 9}\n\x00'
TOTAL BYTES on /dev/cu.usbmodem1203: 112
```
Same read on the hot/cold build returned `TOTAL BYTES: 0` on both ports.

### S10 — opcontrol disassembly (hot package, proves code is correct)
```
07800168 <opcontrol>:
 ... blx <___ZN4pros6screen5eraseEv_veneer>
 ... blx <__printf_veneer>
 ... blx <__delay_veneer>
 b.n 780016e <opcontrol+0x6>      ; loops forever
```
Veneers branch into the cold package; when the onboard cold package mismatches, these
land on wrong addresses and no-op.
