---
topic: "raspberry pi complete kit weight and mobile power for robot use"
slug: rpi-complete-kits
researched: 2026-06-16
sources: [./sources-2.md]
note: Addendum to index.md — covers weight and mobile power only; all kit pricing is in index.md
---

# Addendum: Raspberry Pi 5 Weight & Mobile Power for Robot Use

> Builds on [index.md](index.md); this update covers weight and battery/mobile-power options not addressed there.

## Component Weights

| Component | Weight |
|-----------|--------|
| Pi 5 board (bare PCB) | **~46–47g** |
| Pi 5 board (gross, inc. packaging) | ~62g |
| Official Pi 5 case with fan | ~50–60g (inference — no primary source) |
| Camera Module 3 (PCB + lens, no cable) | **~3g** |
| 150mm FPC cable | ~3g |
| 10,000 mAh USB-C power bank (typical) | ~180–220g |
| **Total Pi 5 + case + camera + battery** | **~280–350g** |

For the VEX V5 robot, this is a modest payload. A Clawbot's steel frame and motors easily support 500g+ additional load on the chassis. Mount the Pi on the rear deck using M2.5 standoffs through the PCB mounting holes (56mm × 85mm footprint); velcro-strap the power bank to the chassis rail.

## Making the Pi 5 Mobile: Power Options

The Pi 5 technically requires **5V / 5A (25W)** for full peripheral use, but this is the *peak* draw (USB ports at max + CPU pinned). In practice, the camera-coprocessor workload (YOLO + AprilTags + serial bridge, no USB peripherals besides V5 cable) draws approximately **3–5W** — well within 5V/3A = 15W. [S1, S2]

### Option A: Standard USB-C Power Bank at 5V/3A (Recommended for capstone) [S1, S3]

**Most practical for the capstone.** Any modern 10,000–20,000 mAh USB-C PD power bank that outputs 5V/3A (15W) will run the Pi 5 comfortably at the camera-coprocessor workload. The only side-effect of not having the full 5A: USB port output is limited to **600 mA** rather than 1.6A — fine since the V5 serial cable draws ~50 mA and no other USB peripherals are needed.

- No adapter or intermediate board required
- Weight: ~180–220g for a 10,000 mAh bank
- Runtime at ~4W draw: **12–15 hours** from 10,000 mAh
- Example: Anker 622 (5,000 mAh, 145g), INIU B57 (10,000 mAh, ~190g)

> ⚠️ The Pi 5 will log a yellow "low voltage" warning in the OS when powered from a 3A supply — this is cosmetic for the capstone use case and does not affect stability at these power levels.

### Option B: 52Pi PD Expansion Board + Any 30W+ PD Power Bank [S4]

The **52Pi PD Power Expansion Board** (~$20) sits between a standard PD power bank and the Pi 5. It negotiates a higher-voltage PD mode from the bank (e.g. 9V/3A = 27W) and steps it down to a clean **5V/8A** output — fully satisfying the Pi 5's 5V/5A requirement even at max load. Adds ~20g and ~$20 but eliminates the voltage warning entirely and unlocks full USB peripheral current.

- Best if you plan to run USB-heavy peripherals or want rock-solid stability
- Works with any 30W+ USB-C PD bank (Anker, INIU, Baseus, etc.)
- The bank can double as a laptop charger

### Option C: Power Tool Battery Pack + Buck Converter [S2]

18V Milwaukee/DeWalt/Makita battery pack + DC-DC buck converter → 5V/5A. Highest runtime (~6,000–9,000 mAh equivalent), very rugged for a robot. Overkill for the capstone but a valid approach for extended outdoor/untethered runs.

### Option D: Pi 4 Approach (Simpler Power) [S3]

Pi 4 only needs **5V/3A (15W)** — standard USB-C PD, no complications. Any 15W+ power bank works directly. This is one genuine remaining advantage of Pi 4 over Pi 5 for a robot: simpler mobile power.

## Recommended Mobile Setup for Capstone

1. **Pi 5 4GB in official case** (board + case + fan): ~110g
2. **Camera Module 3 Wide** (PCB + cable): ~6g
3. **INIU or Anker 10,000 mAh USB-C PD power bank** (5V/3A): ~190g
4. M2.5 standoffs + velcro strap: ~10g
5. **Total add-on weight to VEX robot: ~316g**

Runtime: ~12–15 hours continuous vision processing from a 10,000 mAh bank — far exceeds any competition or demo session. For a 30-minute capstone demo, even a 5,000 mAh / 145g bank is overkill.

**Mount location:** bolt Pi (56mm × 85mm) to rear top chassis plate; run the Camera Module 3 ribbon cable forward to a front-facing bracket; velcro the power bank flat on the upper frame rail to keep the center of gravity low.
