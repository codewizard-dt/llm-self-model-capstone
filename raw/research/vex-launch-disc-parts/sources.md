---
topic: "the minimum required parts (not kits, individual parts) needed from VEX website to add a 'launch disc' type configuration option"
slug: vex-launch-disc-parts
researched: 2026-06-19
---

# Primary Sources — VEX Launch-Disc Parts

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://kb.vex.com/hc/en-us/articles/360035592932-Selecting-a-V5-Assembly | 2026-06-19 | Confirmed flywheel is the standard VEX V5 disc-launching mechanism; described single vs double flywheel and single flywheel + friction-plate patterns |
| S2 | web | https://wiki.purduesigbots.com/hardware/shooting-mechanisms/flywheel | 2026-06-19 | Detailed flywheel design patterns; confirmed 60A durometer for flywheel contact wheel; single flywheel is most common in VRC |
| S3 | web | https://kb.vex.com/hc/en-us/articles/8415934248340-An-Introduction-to-Disco-the-V5RC-Spin-Up-Hero-Bot | 2026-06-19 | Confirmed Disco (Spin Up hero bot) is built from Competition Starter Kit and uses disc-launching; demonstrates this is achievable with standard parts |
| S4 | web | https://www.vexrobotics.com/v5/downloads/build-instructions | 2026-06-19 | Confirmed Disco build instructions require Competition Starter Kit; provided context for disc-launching in VRC Spin Up season |
| S5 | web | https://www.vexrobotics.com/276-4840.html | 2026-06-19 | Confirmed 6:1 (600 RPM) cartridge is "best used for intake rollers, flywheels, or other fast moving mechanisms"; confirmed 6:1 and 36:1 cartridges available for individual purchase; SKU 276-4840 for full motor |
| S6 | web | https://www.vexrobotics.com/v5/products/motion/vrc-flex-wheels.html (EU mirror) | 2026-06-19 | Confirmed flex wheel SKUs: 217-6353 (2" 30A), 217-6354 (2" 40A), 217-6447 (3" 30A), 217-6450 (4" 30A), 217-6451 (4" 40A); confirmed VersaHex adapters 217-8004 (48-pack plastic) and VersaHub 217-8079; confirmed "VersaHex Adapters must be used with 1.625\" and 2\" OD Flex Wheels" and "3\" and 4\" OD Flex Wheels must use VersaHubs and VersaHex Adapters" |
| S7 | web | https://wiki.purduesigbots.com/hardware/misc.-vex-parts-1/motion/flex-wheels | 2026-06-19 | Confirmed 60A durometer recommended for flywheels and drivetrain traction (high firmness = better energy transfer); 30A recommended for intakes; confirmed 217-6449 for 3" 60A; confirmed 36T HS Gear as alternative to VersaHub for 3"/4" wheel mounting |
| S8 | web | https://kb.vex.com/hc/en-us/articles/10487034781076-Flex-Wheels-for-V5 | 2026-06-19 | Confirmed assembly requirements: 2" wheels need 2× VersaHex adapters per wheel; 3"/4" wheels need VersaHub (217-8079) + VersaHex adapters; listed alternatives (276-3891 clamping shaft collar, 276-2551 12T HS Gear) as interference-fit substitutes for VersaHex on small wheels; confirmed 5-step assembly process |
| S9 | web | https://www.idesignsol.com/vexrobotics (search results) | 2026-06-19 | Confirmed SKUs for VersaHex Adapters: 217-7946 (1/4" Square Bore, 1/8" Long, 8-pack), 217-7947 (1/4" Square Bore, 1/4" Long, 8-pack); confirmed flex wheel SKU 217-6449 (3" OD 60A) price $2.49; confirmed 217-6352 (1.625" 60A) |
| S10 | web | https://kb.vex.com/hc/en-us/articles/10004528811412-Understanding-V5-Mechanical-Launching-Systems | 2026-06-19 | Confirmed ball bearing vs. bushing comparison: "bushing-based launcher drawing more than double the current of the bearing-based launcher"; confirmed SKU 276-8402 for HS Shaft Ball Bearings (11-pack); described flywheel weight impact on RPM recovery time |
| S11 | web | https://www.vexrobotics.com/276-8794.html | 2026-06-19 | Confirmed SKU and description for V5 Flywheel Weight 2-pack (276-8794): "prevent your launcher wheels from losing speed after firing"; confirmed VEX V5, VEX U, VEX AI legal |
| S12 | web | https://www.vexrobotics.com/compression-wheels.html | 2026-06-19 | Confirmed Compression Wheel 4-Pack Kits exist (1.625" and 2" OD, 30A/40A/60A) with mounting hardware included; SKUs not confirmed at time of research |
| S13 | web | https://nooby.tech/en/shop/1138-vex-v5-smart-motor-6-1-cartridge-600-rpm.html | 2026-06-19 | Confirmed V5 Motor 6:1 Cartridge (600 RPM) SKU = **276-5842**; sold separately from motor; cartridges for 36:1 and 6:1 available separately |
| S14 | codebase | `raw/research/vex-v5-customization-grab-pull-throw/index.md` | 2026-06-19 | Provided existing robot state: 4 motors in use (all 18:1), 17 free Smart Ports, steel structure; confirmed no 6:1 cartridges in Starter Kit; identified throw-as-catapult as current throw implementation |

## Excerpts

### S5 — V5 Smart Motor & Gear Cartridges (vexrobotics.com/276-4840.html)
> "Ships with a standard [200 RPM, 18:1] gear cartridge. 36:1 (100 RPM) and 6:1 (600 RPM) cartridges are also available for individual purchase."
> "6:1 (600 RPM) - Low torque, high speed. Best used for intake rollers, flywheels, or other fast moving mechanisms"

### S6 — Flex Wheels Page (vexrobotics.com EU mirror)
> "217-6353: 2\" OD Straight Flex Wheel · 217-6447: 3\" OD Straight Flex Wheel · 217-6450: 4\" OD Straight Flex Wheel · 40A Durometer Wheels · 217-6351: 1.625\" OD Straight Flex Wheel · 217-6354: 2\" OD Straight Flex Wheel"
> "Note 1: VersaHex Adapters must be used with 1.625\" and 2\" OD Flex Wheels to be compatible with VEX V5 Shafts. 3\" and 4\" OD Flex Wheels must use VersaHubs and VersaHex Adapters."
> "Plastic 1/2\" VersaHex Adapters v2 (1/4\" Square Bore, 1/8\" Long) (48-pack) SKU#: 217-8004 · 1/2\" Hex Bore Plastic VersaHub v2 · SKU#: 217-8079"

### S7 — Purdue SIGBots Wiki — Flex Wheels
> "For flywheels and drivetrain traction wheels, 60A Flex Wheels are typically ideal. However, for intakes, 30A Flex Wheels might be more ideal."

### S10 — VEX KB: Understanding V5 Mechanical Launching Systems
> "The difference in current draw was significant, with the bushing-based launcher drawing more than double the current of the bearing-based launcher."
> "With the introduction of the High Strength Shaft Ball Bearing, VEX users now have access to two different ways of supporting rotational systems in their robots."
> "Recovery Time—the time it takes the launcher to get back to the target RPM (600)—was reduced significantly in the test with 2 flywheels."

### S13 — nooby.tech (VEX authorised reseller listing for 276-5842)
> "VEX V5 Smart Motor 6:1 Cartridge (600 RPM) 276-5842"
> "Cartridges for 36:1 (100 RPM) & 6:1 (600 RPM) are available separately"
