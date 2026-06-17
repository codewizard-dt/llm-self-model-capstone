---
id: rpi5-usb-pd-power
title: Raspberry Pi 5 USB PD Power — Negotiation Behavior and Mobile Power Fixes
aliases: [Pi 5 USB PD, RPi5 power bank, rpi5-usb-pd]
updated: 2026-06-17
sources:
  - ../../raw/research/rpi5-low-voltage-warning/index.md
tags: [concept, raspberry-pi, power, usb-pd, mobile, robotics]
---

# Raspberry Pi 5 USB PD Power — Negotiation Behavior and Mobile Power Fixes

A recurring challenge in relates_to::[[raspberry-pi-5]] battery-powered robotics deployments. The Pi 5 requests a 5V/5A PDO at boot via USB PD. When no 5A PDO is returned, two consequences follow — and both are commonly misunderstood.

## The Two-Alert Distinction

| Alert | Trigger | Functional Consequence |
|-------|---------|----------------------|
| "Supply not capable of 5A" | PD negotiation returns no 5V/5A PDO | USB ports aggregate-capped at **600 mA** |
| Under-voltage / CPU throttle | Rail voltage drops below **~4.63 V** at the Pi | CPU/GPU clock capped; possible crash/shutdown |

These are mechanically separate. A quality 5V/3A bank at moderate load fires only the first alert; the rail stays well above 4.63 V. Only the second alert actually degrades performance.

## Why No Commodity Bank Offers 5V/5A

Standard USB PD 3.0 fixed-voltage profiles are: 5V/3A, 9V/3A, 15V/3A, 20V/5A. **5V/5A (25W) is out of spec.** The official Raspberry Pi 27W PSU implements it as a proprietary extension. No commodity power bank — including 45W PD units — offers a 5V/5A PDO on the 5V rail. This is structural across the market, not a deficiency of any specific product.

## The USB 600 mA Cap in Context

The cap applies to the **aggregate total** of all four USB-A ports. Peripheral draw:

- CSI-connected cameras (Camera Module 3): **0 mA** (not USB)
- V5 serial cable: **~50 mA**
- USB webcam: ~100–300 mA
- USB SSD (bus-powered): ~500–900 mA
- USB keyboard + mouse: ~100–200 mA combined

The cap matters for disk-heavy or peripheral-heavy setups. For a headless coprocessor with only a serial cable on USB, the cap is irrelevant.

## Fixes: Software (Free)

**Option 1 — Unlock USB current; boot warning may still flash briefly:**
```
# /boot/firmware/config.txt
usb_max_current_enable=1
```

**Option 2 — Full suppression; warning gone, USB unlocked:**
```bash
sudo rpi-eeprom-config --edit
# Add: PSU_MAX_CURRENT=5000
```
Safe at capstone loads (never near 5A draw). Do not use if the actual supply cannot sustain the expected peak current.

## Fixes: Hardware

| Option | Cost | Weight | Notes |
|--------|------|--------|-------|
| **52Pi PD Expansion Board** | ~$20 | ~20 g | Negotiates higher PD voltage, steps down to 5.1V/8A; most community-tested for Pi robotics |
| PD trigger + buck converter (DIY) | ~$8–15 | ~15 g | PD trigger selects 9V/12V; buck → 5.1V/5A |
| Pichondria 5V 5A converter | ~$25 | ~15 g | Same concept as 52Pi |
| Specialty UPS with PD trigger | ~$30–50 | ~80–120 g | Adds UPS capability |

derived_from::[[rpi5-low-voltage-warning]]
relates_to::[[raspberry-pi-5]]
relates_to::[[rpi-complete-kits-mobile-power]]
