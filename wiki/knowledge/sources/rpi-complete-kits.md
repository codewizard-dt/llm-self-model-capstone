---
id: rpi-complete-kits
title: "Research: Raspberry Pi Complete Kits — Pi 4 vs Pi 5 with Camera Module 3"
updated: 2026-06-16
sources:
  - ../../raw/research/rpi-complete-kits/index.md
tags: [raspberry-pi, hardware, pricing, procurement, kit, interfaces]
---

# Research: Raspberry Pi Complete Kits — Pi 4 vs Pi 5 with Camera Module 3

Procurement research (June 2026) comparing complete relates_to::[[raspberry-pi-5]] and Pi 4 kits in terms of price, interfaces, and capstone suitability. Adds the kit/procurement dimension not covered in relates_to::[[rpi5-camera-module-3-cost]], which only covers board+camera pricing.

## Interface Comparison: Pi 4 vs Pi 5

Both boards share the same 40-pin GPIO, 4× USB ports, USB-C power, and Wi-Fi — making them **functionally identical for the VEX V5 serial link**. Key differences:

| Interface | Pi 4 | Pi 5 | Capstone Use |
|-----------|------|------|-------------|
| USB-A (×4) | ✓ | ✓ | **USB-A → microUSB → V5 Brain user port** (serial JSON, 115200 baud) |
| Camera (CSI) | 1× 15-pin 1mm | **2× 22-pin 0.5mm mini** | Camera Module 3 connection |
| PCIe | ✗ | ✓ PCIe 2.0 ×1 | Optional NVMe SSD via M.2 HAT |
| RTC | ✗ | ✓ (CR2032) | Offline timestamping |
| Audio jack | ✓ | ✗ (removed) | Not needed |

**Pi 5 advantage:** two camera CSI ports enable simultaneous forward + overhead cameras. Pi 4 supports only one camera at a time.

## Camera Module 3 Compatibility

| | Pi 4 | Pi 5 |
|-|------|------|
| CSI connector | 15-pin 1mm | 22-pin 0.5mm mini |
| Cable needed | Standard 15-pin (in box) | 22-pin adapter (in box since Dec 4, 2025) |
| Extra purchase? | **No** | **No** (both cables now bundled) |

**Both platforms are directly compatible with Camera Module 3 at no extra cable cost.** Pi 5 needs the adapter cable; it has been included in all Camera Module 3 boxes since December 4, 2025.

## Complete Kit Prices (June 2026)

### Pi 5 Kits

| Kit | RAM | SD | Price |
|-----|-----|-----|-------|
| Official Desktop Kit (CanaKit/Vilros) | 4GB | 32GB | **$170** |
| Official Desktop Kit | 8GB | 32GB | **$235** |
| CanaKit Turbine Black Starter PRO | 4GB | 128GB | **$204.95** |
| CanaKit Turbine Black Starter PRO | 8GB | 128GB | **$269.95** |
| CanaKit Aluminum Starter PRO | 4GB | 128GB | **$214.95** |
| Vilros Complete Starter Kit | 4GB | 128GB | ~$175–190 |

All Pi 5 kits include the **27W USB-C power supply** (5A). Not included: keyboard, mouse, monitor, Camera Module 3.

### Pi 4 Kits

| Kit | RAM | SD | Price |
|-----|-----|-----|-------|
| Official Desktop Kit (CanaKit/Vilros) | 4GB | 32GB | **$165** |
| Official Desktop Kit | 8GB | 32GB | **$230** |
| Vilros Complete Starter Kit | 4GB | 64GB | ~$140–160 |
| CanaKit 4GB Starter PRO | 4GB | 32GB | ~$100–120 |

Pi 4 PSU is **3.5A USB-C** — not interchangeable with Pi 5's 5A supply.

## Pi 4 vs Pi 5 Decision

| | Pi 4 4GB kit | Pi 5 4GB kit |
|-|-------------|-------------|
| Complete kit price | $150–165 | $170–205 |
| CPU speed | 1.5 GHz Cortex-A72 | 2.4 GHz Cortex-A76 |
| Relative CPU perf | 1× | **2–3×** |
| Camera ports | 1 | **2** |
| PCIe/NVMe | ✗ | ✓ |
| RTC | ✗ | ✓ |
| Price premium for Pi 5 | — | +$5–40 |

**Verdict (June 2026):** The price gap has narrowed to $5–40. Pi 5 is the clear choice — 2–3× faster, dual camera ports, PCIe. Only reason to choose Pi 4 is existing hardware or significantly cheaper used/surplus stock.

## Procurement Recommendation

**Official Raspberry Pi 5 Desktop Kit (4GB) at $170** + Camera Module 3 Wide ($35) = **$205 total**. For budget-conscious build: Pi 5 board ($110) + official 45W PSU ($15) + 32GB microSD ($10) + Camera Module 3 ($25) = **$160 total**.

derived_from::[[raspberry-pi-5]]
derived_from::[[pi-camera-module-3]]
relates_to::[[rpi5-camera-module-3-cost]]
relates_to::[[vision-vex-architecture]]
