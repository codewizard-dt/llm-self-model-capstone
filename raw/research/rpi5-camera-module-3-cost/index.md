---
topic: raspberry pi 5 cost esp with camera module 3
slug: rpi5-camera-module-3-cost
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Raspberry Pi 5 Cost — Especially with Camera Module 3

> As of June 2026, three rounds of RAM-driven price increases have significantly inflated Pi 5 costs relative to launch. The 4GB board — the practical sweet spot for camera projects — now costs **$110**, up 83% from its $60 launch price. Adding a Camera Module 3 standard variant ($25, now ships with the Pi 5 adapter cable included) brings the board+camera subtotal to **$135**. A fully functional headless system (board, camera, power supply, SD card) runs roughly **$160–$165**.

## Research Questions

1. What are the current official prices for each Raspberry Pi 5 RAM variant?
2. What does the Camera Module 3 cost and which variants exist?
3. Is a special cable required to connect the Camera Module 3 to the Pi 5, and what does it cost?
4. What are the price drivers and trajectory — are prices expected to change?
5. What does a complete Pi 5 + Camera Module 3 system realistically cost all-in?

## Current State (Codebase)

Not applicable — this is a hardware procurement question unrelated to the software codebase.

## Key Findings

### Raspberry Pi 5 Pricing — Current (as of April 2026) [S1, S2, S3]

Three rounds of price increases since launch have been driven by LPDDR4 memory shortages caused by AI infrastructure demand. Current prices at authorized US resellers (PiShop.us, April 12 2026):

| Model | Launch Price | Current Price | % Increase |
|-------|-------------|--------------|-----------|
| Pi 5 1GB | $45 (Dec 2025 new SKU) | $45 | 0% |
| Pi 5 2GB | $50 | $65 | +30% |
| Pi 5 4GB | $60 | $110 | +83% |
| Pi 5 8GB | $80 | $175 | +119% |
| Pi 5 16GB | $120 | $305 | +154% |

Hike timeline:
- **October 2025**: Compute Module products only
- **December 1, 2025**: Pi 4 and Pi 5 first hike; new 1GB Pi 5 SKU at $45
- **February 2, 2026**: Second hike (+$10/$15/$30/$60 across 2GB–16GB tiers)
- **April 1, 2026**: Third hike — 4GB to $110, 8GB to $175, 16GB to $305

The 1GB model has remained at $45 through all hikes, intentionally positioned as a sub-$50 entry point [S4]. The Pi Foundation has stated prices should drop once DRAM market conditions normalize, but no timeline is given [S3].

### Camera Module 3 Pricing [S5, S6]

Launched January 2023. Prices have **not** increased alongside Pi 5 board prices (different supply chain — Sony IMX708 sensor, not LPDDR4 memory).

| Variant | Price | Field of View | IR Filter |
|---------|-------|--------------|-----------|
| Camera Module 3 | $25 | 75° | Yes (visible light) |
| Camera Module 3 NoIR | $25 | 75° | No (night vision capable) |
| Camera Module 3 Wide | $35 | 120° | Yes (visible light) |
| Camera Module 3 Wide NoIR | $35 | 120° | No (night vision capable) |

All variants: 12MP Sony IMX708, HDR, phase-detect autofocus, 1080p50 video.

### Cable Compatibility — Pi 5 Requires Adapter [S7, S8, S9]

The Pi 5 uses a **22-pin 0.5mm pitch** ("mini") FPC connector for cameras, while Camera Module 3 ships with a **15-pin 1mm pitch** ("standard") FPC cable. An adapter cable is required.

**Good news (as of December 4, 2025)**: Camera Module 3 now ships with *both* a 150mm standard cable and a 200mm Pi 5 adapter cable included in the box [S10]. If buying a new Camera Module 3, no additional cable purchase is needed.

If sourcing a cable separately:
| Length | Official Price |
|--------|---------------|
| 200mm | $1 |
| 300mm | $2 |
| 500mm | $3 |

### Essential Accessories [S11, S12]

| Accessory | Official Price |
|-----------|---------------|
| 27W USB-C power supply (original) | $12 |
| 45W USB-C power supply (newer, recommended) | $15 |
| Official 32GB microSD (pre-loaded with Pi OS) | ~$10 |
| Official case with fan | ~$10 |
| Active cooler (standalone) | ~$5 |

The 27W/5A supply is strongly recommended — using a standard 3A charger limits USB port output to 600mA.

## Constraints

- The LPDDR4 RAM shortage is ongoing as of June 2026; further price hikes cannot be ruled out.
- For camera projects, 4GB RAM is the practical minimum if running desktop + browser; 1GB or 2GB is sufficient for headless camera capture/streaming.
- Camera Module 3 Wide NoIR (120°, no IR filter) variants are sometimes harder to find in stock.

## Solution Comparison

| Configuration | Board Cost | Camera Cost | Cable | Power | SD Card | **Total** |
|--------------|-----------|------------|-------|-------|---------|-----------|
| Minimal: 1GB + Cam3 (board+camera only) | $45 | $25 | $0 (included) | — | — | **$70** |
| Headless: 2GB + Cam3 + essentials | $65 | $25 | $0 | $12 | $10 | **$112** |
| Practical: 4GB + Cam3 Wide + essentials | $110 | $35 | $0 | $12–$15 | $10 | **$167–$170** |
| High-end: 8GB + Cam3 Wide + essentials | $175 | $35 | $0 | $15 | $10 | **$235** |

## Recommendation

**For most camera-centric projects**: the **Pi 5 4GB ($110) + Camera Module 3 standard ($25)** combination at **$135 for board+camera** is the recommended minimum. Add the 45W power supply ($15) and a microSD ($10) for a functional headless system at **~$160**.

If RAM usage is genuinely low (e.g., a dedicated camera capture node, no desktop, streaming only), the **2GB ($65)** or even **1GB ($45)** saves $45–$65 at the cost of headroom.

**Avoid 8GB+ unless you need it** — the $175 vs $110 jump for 4GB→8GB is steep and rarely justified for pure camera work.

**Implementation steps to get to a working system:**
1. Buy Pi 5 4GB ($110) and Camera Module 3 ($25) from an authorized reseller (PiShop.us, Adafruit, CanaKit)
2. Add 45W USB-C PSU ($15) and 32GB microSD with Pi OS ($10)
3. No separate camera cable needed if buying a new Camera Module 3 (cable included since Dec 2025)
4. Total spend: ~$160 for a headless camera system

**Risks:**
- Further price hikes are possible; prices could also drop if DRAM supply normalizes
- Verify reseller authorization at raspberrypi.com to avoid inflated third-party pricing
- Stock of specific camera variants (especially Wide NoIR) can be intermittent

## Next Steps

- `/task-add` if you want to procure hardware and set up the development environment
- Consider whether the 1GB Pi 5 ($45) suffices for a headless embedded camera node, which would significantly reduce costs
- Check rpilocator.com for real-time stock tracking across authorized resellers
