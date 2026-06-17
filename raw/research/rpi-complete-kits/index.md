---
topic: "how does raspberry pi interface... find a full kit that is complete with power source, sd card etc. Consider rasp pi 5 and rasp pi 4, include cost for all kits"
slug: rpi-complete-kits
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Raspberry Pi Complete Kits — Pi 4 vs Pi 5 with Camera Module 3

> As of June 2026, Pi 4 and Pi 5 complete kits are **nearly identically priced** due to the same LPDDR4 shortage that inflated Pi 5 board costs. A complete Pi 5 4GB kit runs $170–$205 depending on the seller, while a Pi 4 4GB complete kit costs $150–$165. Given that Pi 5 delivers 2–3× the CPU performance and adds PCIe/NVMe support, **Pi 5 is the better choice at current pricing for any new purchase**. Both boards are fully compatible with Camera Module 3 — Pi 4 uses the camera's included 15-pin cable directly; Pi 5 needs the 22-pin adapter cable (now bundled with Camera Module 3 since December 2025).

## Research Questions

1. What physical interfaces does the Raspberry Pi expose and how do they connect to the VEX V5 robot?
2. Which complete kits (Pi 5 and Pi 4) include everything needed out-of-box: board, power supply, SD card, case?
3. What do those complete kits cost from major US resellers in 2026?
4. Is Camera Module 3 compatible with both Pi 4 and Pi 5, and what cable is needed?
5. Is Pi 4 still a cost-effective choice compared to Pi 5 given recent price hikes?

## Current State (Codebase)

The wiki already documents the two-computer architecture (Pi 5 + VEX V5 Brain) via `vision-vex-architecture` and `rpi5-camera-module-3-cost` research. This report adds the kit/procurement dimension and Pi 4 compatibility not covered in those sources.

## Key Findings

### Raspberry Pi Interfaces [S1, S2, S3]

Both Pi 4 and Pi 5 share the same 40-pin GPIO header and USB port layout, making them functionally identical for the capstone's VEX V5 serial link.

| Interface | Pi 4 | Pi 5 | Capstone Use |
|-----------|------|------|-------------|
| 40-pin GPIO | ✓ SPI/I2C/UART/PWM | ✓ same (via RP1 chip) | Extensible; not used in base design |
| USB-A (×4: 2× USB3 + 2× USB2) | ✓ | ✓ | **USB-A → microUSB → V5 Brain user port** (serial JSON) |
| USB-C | Power only (3A) | Power only (5A) | Power supply connection |
| Gigabit Ethernet | ✓ | ✓ | SSH/remote dev; not needed on-robot |
| Wi-Fi | 802.11ac | 802.11ac | Optional network access |
| Bluetooth | 5.0/BLE | 5.0/BLE | Not used |
| Camera (CSI) | 1× 15-pin 1mm standard | **2× 22-pin 0.5mm mini** | Camera Module 3 connection |
| Display (DSI) | 1× 15-pin | 2× 22-pin (shared with CSI) | Not used |
| PCIe | ✗ | ✓ PCIe 2.0 ×1 | Optional NVMe SSD via M.2 HAT |
| RTC | ✗ | ✓ (CR2032 socket) | Offline timestamping |
| Audio jack | ✓ | ✗ (removed on Pi 5) | Not needed |

**VEX V5 serial link** works identically on both boards: one USB-A port → microUSB cable → V5 Brain user port, 115200 baud, newline-delimited JSON via `pyserial`. The Camera Module 3 connects via the CSI port on both boards (cable differs — see below).

### Camera Module 3 Compatibility: Pi 4 vs Pi 5 [S4, S5]

| | Pi 4 | Pi 5 |
|-|------|------|
| CSI connector | 15-pin, 1mm pitch | 22-pin, 0.5mm pitch |
| Camera Module 3 cable needed | Standard 15-pin (included in box) | 22-pin adapter (included in box since Dec 4, 2025) |
| Extra purchase required? | **No** — works with cable in box | **No** (new Camera Module 3 now ships with both cables) |
| Number of camera ports | 1 | **2** (can run two cameras simultaneously) |

**Pi 4 is directly compatible with Camera Module 3** using the 15-pin standard cable it ships with — no adapter. Pi 5 requires the 22-pin adapter but this is now included. Pi 5's advantage: two camera ports allow simultaneous forward + overhead cameras if needed. [S4]

### Complete Kit Options & Prices (June 2026)

#### Raspberry Pi 5 Kits [S6, S7, S8]

| Kit | RAM | SD Card | Key Extras | Price |
|-----|-----|---------|------------|-------|
| **Official Desktop Kit** (CanaKit/Vilros) | 4GB | 32GB | Official case+fan, microHDMI cable | **$170** |
| **Official Desktop Kit** | 8GB | 32GB | Official case+fan, microHDMI cable | **$235** |
| **CanaKit Turbine Black Starter Kit PRO** | 4GB | 128GB | CanaKit case+fan, heatsink, microHDMI ×2, card reader | **$204.95** |
| **CanaKit Turbine Black Starter Kit PRO** | 8GB | 128GB | CanaKit case+fan, heatsink, microHDMI ×2, card reader | **$269.95** |
| **CanaKit Turbine Black Starter Kit PRO** | 16GB | 128GB | CanaKit case+fan, heatsink, microHDMI ×2, card reader | **$399.95** |
| **CanaKit Aluminum Starter Kit PRO** | 4GB | 128GB | Aluminum case+fan, heatsink, microHDMI ×2, card reader | **$214.95** |
| **CanaKit Aluminum Starter Kit PRO** | 8GB | 128GB | Aluminum case+fan, heatsink, microHDMI ×2, card reader | **$279.95** |
| **Vilros Complete Starter Kit** | 4GB | 128GB | Aluminum passive+active case, PSU, microHDMI ×2, bag | ~$175–190* |
| **Vilros Starter Kit MAX** | 8GB | 128GB | Turbo-cooled aluminum case, PSU, 27W supply | ~$220–240* |

*Vilros prices vary; check Amazon/vilros.com for current listing.

All Pi 5 kits include the **27W USB-C power supply** (or equivalent 5A supply). The Official Desktop Kit uses the official Raspberry Pi 27W PSU; CanaKit uses their own 5A UL-listed PSU.

**What's in a complete Pi 5 kit (Official Desktop):**
1. Raspberry Pi 5 board (4GB or 8GB)
2. 27W USB-C power supply
3. 32GB microSD pre-loaded with Raspberry Pi OS (64-bit)
4. Official red/white case with integrated fan
5. microHDMI to HDMI cable
6. (CanaKit PRO adds 128GB SD, heatsink, card reader, 2× microHDMI cables)

**Not included in any Pi 5 kit:** keyboard, mouse, monitor, Camera Module 3, camera cable. All of these are sold separately.

#### Raspberry Pi 4 Kits [S9, S10, S11]

| Kit | RAM | SD Card | Key Extras | Price |
|-----|-----|---------|------------|-------|
| **CanaKit Basic Kit** | 4GB | none | PSU, heatsinks only | $69.95* |
| **CanaKit Basic Kit** | 8GB | none | PSU, heatsinks only | $89.95* |
| **Official Desktop Kit** (CanaKit/Vilros) | 4GB | 32GB | Official case, PSU, microHDMI | **$165** |
| **Official Desktop Kit** | 8GB | 32GB | Official case, PSU, microHDMI | **$230** |
| **Vilros Complete Starter Kit** | 4GB | 64GB | Fan case, PSU, microHDMI, heatsinks | ~$140–160* |
| **Vilros Complete Starter Kit** | 8GB | 64GB | Fan case, PSU, microHDMI, heatsinks | ~$200–225* |
| **CanaKit 4GB Starter PRO** | 4GB | 32GB | Fan case, PSU, heatsinks, card reader | ~$100–120* |

*Some CanaKit Pi 4 basic kits showing "Pre-Orders Sold Out" on canakit.com as of June 2026 — stock is tightening as Pi 4 approaches end of mainstream production. Pi 4 is guaranteed in production until at least 2034 but resellers are clearing inventory.

Pi 4 PSU is **3.5A USB-C** (not the Pi 5's 5A PSU — not interchangeable with Pi 5).

### Pi 4 vs Pi 5: Which Kit Makes Sense in 2026? [S12, S13]

| | Pi 4 4GB kit | Pi 5 4GB kit |
|-|-------------|-------------|
| Complete kit price | $150–165 | $170–205 |
| CPU speed | 1.5 GHz Cortex-A72 | 2.4 GHz Cortex-A76 |
| Relative CPU perf | 1× | **2–3×** |
| Camera ports | 1 | **2** |
| PCIe/NVMe | ✗ | ✓ |
| RTC | ✗ | ✓ |
| Camera Module 3 compatibility | Direct (15-pin) | Adapter included |
| Price premium for Pi 5 | — | +$5–40 |

**Verdict (June 2026):** The price gap between Pi 4 and Pi 5 complete kits has narrowed to $5–40. At that delta, Pi 5 is the obvious choice — 2–3× faster, two camera ports, PCIe for optional NVMe, and a built-in RTC. The only reason to choose Pi 4 now is if you already own one or find used/surplus stock significantly cheaper. [S12]

## Constraints

- Pi 5 board alone (4GB) now costs $110 — kits at $170–205 represent $60–95 in accessories, which is reasonable
- Pi 4 8GB kits ($200–230) now cost nearly as much as Pi 5 8GB kits ($235+), making Pi 4 8GB especially poor value
- Camera Module 3 now ships with both cables (Pi 4 and Pi 5) — no extra cable cost for either platform
- Both boards need a keyboard/mouse/monitor or SSH setup for initial configuration
- Power supplies are **not interchangeable**: Pi 4 uses 3.5A, Pi 5 uses 5A USB-C

## Recommendation

**Buy: Official Raspberry Pi 5 Desktop Kit (4GB) at $170**

This is the most cost-effective complete kit for the capstone:
- Includes the Pi 5 board (4GB), 32GB microSD (Pi OS pre-loaded), official case with fan, PSU, and microHDMI cable
- Available from CanaKit, Vilros, or direct from PiShop.us
- Add Camera Module 3 ($25) separately — it comes with both the Pi 4 and Pi 5 cables
- **Total for a working camera coprocessor: $170 (kit) + $25 (camera) = $195**

If 128GB SD card and a beefier case matter more than $35:
→ **CanaKit Turbine Black PRO (4GB, 128GB SD): $204.95**

If budget is tight and you already have SD cards and HDMI cables:
→ **Pi 5 4GB board alone ($110) + official 45W PSU ($15) + SD card (~$10) = $135**, then add Camera Module 3 ($25) = **$160 total**

**Do not buy a Pi 4 new** at current prices — the kit premium for Pi 5 is too small given the performance advantage.

## Next Steps

- `/task-add` to procure the Pi 5 4GB Official Desktop Kit + Camera Module 3 and set up the development environment
- Camera Module 3 Wide variant ($35) is preferred for the capstone (120° FOV captures more workspace)
- No additional cable purchase needed — Camera Module 3 now ships with the Pi 5 22-pin adapter cable included
