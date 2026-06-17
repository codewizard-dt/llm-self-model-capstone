---
topic: "Is there any real advantage to addressing the Pi 5 'low voltage' warning, and is the 52Pi PD Expansion Board the only way to fix it?"
slug: rpi5-low-voltage-warning
researched: 2026-06-17
sources: [./sources.md]
---

# Research: Raspberry Pi 5 Low Voltage Warning — Real Consequences & All Fixes

> The Pi 5 "low voltage / supply not 5A" warning triggered by a standard 5V/3A power bank has **zero functional impact on the capstone workload** (CSI camera + USB serial only). It is produced by a failed PD negotiation, not an actual voltage sag, and its only real effect — capping USB ports to 600 mA total — is irrelevant when the heaviest USB consumer on the robot is the V5 serial cable at ~50 mA. There are at least four ways to eliminate it; the 52Pi board is not the only option. For the capstone, the cheapest fix is a free one-liner in `config.txt`.

---

## Research Questions

1. What does the Pi 5 "low voltage" warning actually trigger — CPU throttling, USB current cap, or something else?
2. At the capstone workload (YOLO + serial bridge + WiFi + NeoPixels, ~5–8 W), does the warning represent a real problem?
3. Is the 52Pi PD Expansion Board the only hardware path to a clean 5 V/5 A supply from a power bank?
4. Are there software-only fixes that eliminate the warning's consequences without extra hardware?
5. Can an off-the-shelf 45 W PD power bank (like the INIU CZW8VCK787) natively negotiate the 5 V/5 A profile?

---

## Current State (Codebase / Wiki)

The existing wiki page `wiki/knowledge/sources/rpi-complete-kits-mobile-power.md` and `wiki/knowledge/entities/tools/raspberry-pi-5.md` describe the warning as "cosmetic only, does not affect stability at these power levels." This research validates that claim but adds significantly more nuance: the warning is cosmetic **for the capstone's specific peripheral set**, and there are free software fixes that remove it entirely.

---

## Key Findings

### F1 — There Are Two Distinct Warnings, Not One [S1, S2]

The Pi 5 can show two very different power alerts:

| Warning | Trigger | Consequence |
|---------|---------|-------------|
| **"Supply not capable of 5 A"** | PD negotiation returns no 5 V/5 A PDO | USB port aggregate capped at **600 mA** |
| **Under-voltage / CPU throttle** | Rail voltage drops below ~4.63 V at the Pi | CPU/GPU clock capped; possible crash |

A quality 5 V/3 A power bank (e.g., INIU CZW8VCK787) at 5–8 W total draw will **not** cause the second warning — the voltage stays well above 4.63 V. Only the first warning (PD negotiation miss) fires.

### F2 — The USB 600 mA Cap Is Not a Problem for the Capstone [S1, S3]

The 600 mA cap is the **total** current budget for all four USB-A ports combined. The capstone's USB peripherals are:

- Camera Module 3: **CSI ribbon, not USB** → 0 mA from USB budget
- V5 serial cable: **~50 mA**

Total USB draw: **~50 mA** — 12× below the 600 mA cap. The warning has zero functional impact on this peripheral set.

The cap would matter for: USB SSDs/drives, USB webcams, USB keyboards at boot, USB hubs. None of those apply here.

### F3 — 5 V/5 A Is a Non-Standard PD Profile; No Commodity Bank Offers It [S4, S5]

Standard USB PD 3.0 fixed-voltage PDOs go: 5 V/3 A → 9 V/3 A → 15 V/3 A → 20 V/5 A. The 5 V/5 A profile the Pi 5 requests is **out of spec for USB PD**. The official Raspberry Pi 27 W PSU implements it as a proprietary extension. Virtually no commodity power bank (including 45 W INIU units) offers a 5 V/5 A PDO — they top out at 5 V/3 A for the 5 V rail. This is structural, not a deficiency of any particular bank.

### F4 — Free Software Fixes Exist [S2, S6, S7]

Two config options address the warning without any hardware addition:

**Option 1 — Unlock USB current only (warning may persist at boot screen):**
```
# /boot/firmware/config.txt
usb_max_current_enable=1
```
Raises aggregate USB current limit from 600 mA to 1.6 A. The on-screen "not capable of 5 A" overlay may still flash at boot, but the USB restriction is gone. For the capstone (50 mA USB draw) this is entirely moot.

**Option 2 — Full suppression (no warning, full USB current):**
```bash
sudo rpi-eeprom-config --edit
# Add line: PSU_MAX_CURRENT=5000
```
Tells the PMIC firmware the supply is 5 A capable; suppresses warning completely and unlocks USB to 1.6 A. Note: this is a deliberate firmware assertion that the supply can provide 5 A. At the capstone's 5–8 W draw this is safe — the Pi never comes close to demanding 5 A. Do **not** use with a marginal supply or heavy USB peripherals.

### F5 — The 52Pi Board and Its Alternatives [S8, S9, S10]

When hardware fix is preferred (e.g., heavy USB peripherals, desire to eliminate warning unconditionally):

| Option | Cost | Weight | How It Works |
|--------|------|--------|-------------|
| **52Pi PD Expansion Board** | ~$20 | ~20 g | Negotiates 9–15 V from bank via PD, steps down to 5.1 V/8 A; clean supply |
| **PD trigger + buck converter** (DIY) | ~$8–15 | ~15 g | PD trigger selects 9 V/12 V from bank; separate buck → 5.1 V/5 A |
| **Pichondria 5V 5A converter board** | ~$25 | ~15 g | Same concept as 52Pi, different form factor |
| **Specialty UPS with PD trigger** | ~$30–50 | ~80–120 g | Spotpear/Waveshare units with integrated LiPo; adds UPS capability |

The 52Pi is the most community-tested and compact option specifically for Pi 5 on a robot. The DIY PD-trigger+buck path is documented on Reddit and works but requires more assembly.

---

## Constraints

- The capstone runs headless with no USB display adapter, no USB SSD, and no USB webcam (Camera Module 3 uses CSI). This is precisely the peripheral set where the 600 mA cap is irrelevant.
- The INIU CZW8VCK787 is a quality 45 W PD bank — voltage will not sag to 4.63 V at 5–8 W draw.
- Adding `PSU_MAX_CURRENT=5000` to EEPROM is safe at capstone loads but would be unsafe with a genuinely marginal 2 A supply or sustained 20 W+ draw.

---

## Recommendation

**For the capstone as currently configured: do nothing.** The warning is genuinely cosmetic. The INIU bank + Camera Module 3 (CSI) + V5 serial cable is exactly the configuration where 600 mA USB cap causes no harm.

**If the warning is distracting during demos or SSH sessions**, the free one-liner is sufficient:
```
# /boot/firmware/config.txt — add this line
usb_max_current_enable=1
```

**If USB peripherals are added later** (USB webcam, USB SSD boot), upgrade to `usb_max_current_enable=1` at minimum, or add the 52Pi board for a fully clean supply without any firmware assertions.

**Do not buy the 52Pi board for the capstone as-is.** It solves a problem this workload doesn't have, adds $20 and 20 g, and introduces one more component that can fail.

---

## Next Steps

- No action required for power configuration as the capstone stands.
- If/when adding a USB webcam or USB SSD: add `usb_max_current_enable=1` to `config.txt` first (free); add 52Pi board only if voltage instability is observed.
- Run `/wiki-ingest raw/research/rpi5-low-voltage-warning/index.md` to add this to the knowledge base.
