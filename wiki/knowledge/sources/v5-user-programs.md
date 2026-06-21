---
id: v5-user-programs
title: Research: V5 User Programs — Why They're Mandatory and How Simple They Can Be
updated: 2026-06-21
sources:
  - ../../raw/research/v5-user-programs/index.md
tags: [source, vex, vexcode, pros, brain, user-program, serial, architecture, motors]
---

# Research: V5 User Programs — Why They're Mandatory and How Simple They Can Be

Research conducted 2026-06-21. Full report: `raw/research/v5-user-programs/index.md`.

## The RPi Cannot Bypass the User Program — Three Reasons

**V5 Smart Motors use a proprietary RS-485 protocol that the RPi cannot speak.** When the V5 Brain powers on, VEXos loads motor firmware onto each connected Smart Motor over the proprietary RS-485 Smart Port bus. The motor responds only to commands from the Brain. No public library or specification allows an RPi or Arduino to speak this protocol directly — "you would have to fake the signals sent from the V5 brain to the smart motors, and trick the motors into thinking they are connected to a V5 brain."

**The Brain's two USB serial ports serve different purposes, neither of which enables motor control without a running program:**
- **System port**: used by VEXcode and PROS CLI for program upload, file management, and Brain status queries. The V5 Serial Protocol it speaks contains only program-management packets (upload, run, stop, list) — no real-time motor command packets exist in the protocol.
- **User port**: carries stdio (`print()`/`printf()` output) from a *running* user program only. "If you try to communicate with the Brain over the user port nothing will happen" without a running program.

**A user program is therefore structurally mandatory.** It is the translation layer: `RPi serial JSON → user program → VEXos motor API → RS-485 → Smart Motor`.

## Non-Competition Operation

**No competition infrastructure is needed for the capstone.** The PROS competition template documents: "If no competition control is connected, this function will run immediately following initialize()." Without a Competition Switch or Field Management System plugged into the Brain's competition port, `opcontrol()` starts immediately after `initialize()`. There is no need for an autonomous/teleop split, a competition switch, or a field controller.

In a competition context, teams write `autonomous()` (executed during the 15-second auto period) and `opcontrol()` (executed during 1:45 driver control) as separate functions triggered by the FMS. For the capstone, the entire program is just a single serial-read loop in `opcontrol()`.

## Minimum Viable Program for the Capstone

The minimum user program that satisfies the Pi-first architecture is ~50–100 lines: `initialize()` sets up serial (e.g. `SERCTL_DISABLE_COBS` in PROS C++), then `opcontrol()` runs a loop that reads newline-delimited JSON commands from serial, calls motor velocity APIs, sends JSON acks, and stops motors if no packet arrives within 250ms. The current codebase sketch (`robot/v5-brain/pros_bridge/src/main.cpp`) already has this structure — it only needs motor port wiring and `vx`/`omega` JSON parsing filled in.

**VEXos also includes a built-in "Drive program"** that maps V5 Controller joysticks to motors without any uploaded code. This does not help the Pi-first architecture — it requires the physical V5 Controller, not serial from the RPi.

**Deployment:** upload once via laptop + USB + VEXcode or PROS CLI; program persists in its slot across power cycles. At the start of each session: power on Brain → tap slot on touchscreen → program runs. The Pi then connects via USB serial and sends commands.

relates_to::[[vex-v5]]  
relates_to::[[vex-coprocessor-pattern]]  
relates_to::[[pros]]  
relates_to::[[vexcode]]  
relates_to::[[v5-brain-python-vs-pros]]  
relates_to::[[vex-v5-telemetry-pipeline]]
