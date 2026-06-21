---
id: pros-dependency-compatibility
title: PROS Dependency & Build Compatibility (this Brain)
aliases: [PROS library compatibility, PROS monolith build, USE_PACKAGE, hot-cold packaging]
updated: 2026-06-21
sources:
  - ../../../raw/research/v5-serial-connectivity/index-2.md
  - ../../../raw/research/v5-serial-connectivity/sources-2.md
tags: [concept, vex, pros, build, dependencies, gotcha, toolchain]
---

# PROS Dependency & Build Compatibility (this Brain)

The rules for safely adding **any** library or template to a relates_to::[[pros]] project
on the capstone's physical V5 Brain (System ID `E05EA500`, VEXos **1.1.5.0**, PROS kernel
**4.2.2**). These are not LemLib-specific — they apply to every added dependency
(uses::[[lemlib]], OkapiLib, ArduinoJson, EZ-Template, any depot template, any `.a`).

## Rule 1 — Build as a monolith (`USE_PACKAGE:=0`)

PROS defaults to **hot/cold linking** (`USE_PACKAGE:=1`): the kernel + libraries
("cold package") upload once, only user code ("hot package") re-uploads each time.
**On this Brain that split is silently broken.** A hot/cold program *appears* to run
(name + timer on screen) but **nothing renders and zero serial bytes come out** — every
library call (`printf`, `pros::screen::*`, serial) no-ops. `pros upload` reports
*"Library is already onboard V5"* as a false positive: the onboard cold package does not
match the hot package's veneer addresses, so veneer branches land on wrong addresses.
`pros v5 rm-all` does not clear the library and there is no force-library flag.

Fix (verified working — serial + display both came alive immediately):

```makefile
USE_PACKAGE:=0      # Makefile — build a monolith, no veneers, no separate cold package
```
```bash
pros make clean && pros make && pros upload --after run
```

Cost: every upload re-sends the full ~425 KB binary instead of a small hot package —
negligible here. caused::[[v5-serial-connectivity]]. Full write-up in
`robot/v5-brain/TOOLCHAIN.md` §5.

## Rule 2 — Every added library must target PROS kernel 4.x

PROS libraries are version-locked to a kernel generation. This project runs kernel
**4.2.2** (LVGL 9.2.0). Before adding a dependency, pin a release that explicitly
supports kernel 4.x — a library built for kernel 3.x links against a different SDK/jump
table and will fault or no-op. Install via `pros conductor apply` (depot template) or by
dropping its `.a` + headers into `firmware/` + `include/`.

## Rule 3 — A new library links into the monolith, not a separate cold image

Because of Rule 1, do **not** rely on the depot's per-library cold-packaging. With
`USE_PACKAGE:=0` an added library's archive is linked directly into `monolith.bin`, so
there is no separate-upload step to get out of sync. After adding any dependency,
re-verify end-to-end: upload, confirm the screen draws and serial still flows
(`pros terminal` or a pyserial read of the user port).

## Checklist for adding any PROS dependency

1. Confirm the release targets **kernel 4.x**.
2. Keep `USE_PACKAGE:=0` (monolith).
3. `pros make clean && pros make && pros upload --after run`.
4. Re-verify display + serial before building further on top of it.

relates_to::[[pros]]
relates_to::[[lemlib]]
relates_to::[[vex-v5]]
relates_to::[[vex-v5-telemetry-pipeline]]
