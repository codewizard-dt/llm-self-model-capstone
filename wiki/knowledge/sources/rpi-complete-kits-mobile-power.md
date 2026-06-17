---
id: rpi-complete-kits-mobile-power
title: "Addendum: Raspberry Pi 5 Weight & Mobile Power for Robot Use"
updated: 2026-06-16
sources:
  - ../../raw/research/rpi-complete-kits/index-2.md
tags: [raspberry-pi, hardware, power, mobile, weight, robot-payload]
---

# Addendum: Raspberry Pi 5 Weight & Mobile Power for Robot Use

Addendum to relates_to::[[rpi-complete-kits]] covering payload weight and battery/mobile-power options for mounting the relates_to::[[raspberry-pi-5]] on a VEX V5 Clawbot chassis.

## Component Weights

| Component | Weight |
|-----------|--------|
| Pi 5 board (bare PCB) | **~46–47g** |
| Official Pi 5 case with fan | ~50–60g |
| Camera Module 3 (PCB + lens + cable) | **~6g** |
| 10,000 mAh USB-C power bank (typical) | ~180–220g |
| M2.5 standoffs + velcro | ~10g |
| **Total system on-robot** | **~280–350g** |

A VEX Clawbot's steel frame and motors support 500g+ additional load — this payload is modest.

## Actual Power Draw

**The rated 25W peak is not the capstone operating point.** The camera-coprocessor workload (YOLO11n + AprilTags + serial bridge, no USB peripherals besides the V5 cable) draws approximately **3–5W** — well within what a standard 5V/3A USB-C bank provides.

## Mobile Power Options

### Option A: Standard USB-C Power Bank at 5V/3A (Recommended)

Any 10,000–20,000 mAh USB-C PD bank that outputs 5V/3A (15W) runs the Pi 5 comfortably at the capstone workload:

- USB port current cap drops to 600 mA (vs 1.6A at full power) — fine since V5 serial cable draws ~50 mA
- Runtime at ~4W: **12–15 hours** from 10,000 mAh
- Pi 5 logs a yellow "low voltage" OS warning — **cosmetic only, does not affect stability at these power levels**
- Example banks: Anker 622 (5,000 mAh, 145g), INIU B57 (10,000 mAh, ~190g)

### Option B: 52Pi PD Expansion Board (~$20) + Any 30W+ PD Bank

The **52Pi PD Power Expansion Board** negotiates a higher PD voltage from the bank (e.g. 9V/3A) and steps down to clean **5V/8A**, fully satisfying Pi 5's 5V/5A requirement. Eliminates the voltage warning; unlocks full USB peripheral current. Adds ~20g and ~$20. Best if running USB-heavy peripherals.

### Option C: Power Tool Battery + Buck Converter (Overkill)

18V Milwaukee/DeWalt/Makita battery + DC-DC buck converter → 5V/5A. Highest runtime (~6,000–9,000 mAh equivalent); overkill for the capstone but valid for extended outdoor runs.

### Option D: Pi 4 Advantage

Pi 4 only needs **5V/3A (15W)** natively — no voltage warning, no adapter. One remaining advantage of Pi 4 over Pi 5 for robot mounting: simpler mobile power.

### Option E: Free Software Fix (Recommended First Step)

**For the capstone as configured** (CSI camera + USB serial only), the 600 mA USB cap from the PD negotiation miss is irrelevant — total USB draw is ~50 mA. If the boot overlay warning is distracting, a one-line config.txt change removes the only functional consequence:

```
# /boot/firmware/config.txt
usb_max_current_enable=1
```

For full warning suppression (no boot overlay, USB unlocked to 1.6A): add `PSU_MAX_CURRENT=5000` via `sudo rpi-eeprom-config --edit`. Safe at capstone loads; do not use with a genuinely marginal supply. See relates_to::[[rpi5-usb-pd-power]] for the full two-warning distinction and context.

## Recommended Mobile Setup for Capstone

1. Pi 5 4GB in official case + fan: ~110g
2. Camera Module 3 Wide + cable: ~6g
3. INIU or Anker 10,000 mAh USB-C PD bank (5V/3A): ~190g
4. **Total add-on weight: ~316g**, runtime ~12–15 hours

**Mount:** bolt Pi (56mm × 85mm footprint) to rear top chassis plate via M2.5 standoffs; run Camera Module 3 ribbon cable forward to front-facing bracket; velcro power bank flat on upper frame rail to keep center of gravity low.

derived_from::[[raspberry-pi-5]]
relates_to::[[rpi-complete-kits]]
relates_to::[[vex-v5]]
