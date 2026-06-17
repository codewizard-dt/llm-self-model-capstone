---
topic: LEGO SPIKE Prime kit — its functionality and whether it is appropriate for this project
slug: lego-spike-prime
researched: 2026-06-16
---

# Primary Sources — LEGO SPIKE Prime Kit

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `wiki/knowledge/entities/tools/lego-spike-prime.md` | 2026-06-16 | Existing entity page: hub specs summary, Python path, Build HAT reference, lifecycle risk flag |
| S2 | codebase | `wiki/knowledge/sources/feasibility-human-built-generational-factory.md` | 2026-06-16 | Generation manifest JSON schema, three-stage roadmap (SPIKE → VEX V5 → ROBOTIS), typed parts grammar requirements, grounding requirement for self-model |
| S3 | web | https://github.com/gpdaniels/spike-prime | 2026-06-16 | Internal hardware specs: STM32F413 ARM Cortex M4 @ 100MHz, ROM 1MB, RAM 320KB; sensor specs: distance sensor 2m/1mm res, force sensor 10N/0.65N accuracy, color sensor 8 colors; motor accuracy ±3° |
| S4 | web | https://education.lego.com/en-us/teacher-resources/lego-education-spike-prime/support-technical-info/lego-education-spike-prime-support-technical-info-product-info/ | 2026-06-16 | Official hub specs: 6 I/O ports, 5×5 light matrix, Bluetooth, speaker, 6-axis gyro, rechargeable battery; kit overview |
| S5 | web | https://www.toysperiod.com/lego-set-reference/lego-education/lego-45678-spike-prime-set/ | 2026-06-16 | Kit contents list: hub, Distance Sensor, Force Sensor, Color Sensor, Large Motor, 2× Medium Motors, 500+ LEGO Technic elements |
| S6 | web | https://github.com/gpdaniels/spike-prime | 2026-06-16 | USB serial MicroPython REPL path; python3 upload script for hub; protocol details |
| S7 | web | https://www.raspberrypi.com/news/raspberry-pi-build-hat-lego-education/ | 2026-06-16 | Build HAT: 4-port LPF2 controller for Raspberry Pi; Python library mirrors gpiozero API; supports all SPIKE Portfolio sensors/motors; text serial protocol at 115200 baud over /dev/serial0 |
| S8 | web | https://pybricks.com/ | 2026-06-16 | PyBricks: open-source alternative firmware for SPIKE Prime hub; clean Python API (pybricks.hubs.PrimeHub, pybricks.pupdevices.*); VS Code compatible; offline storage; Bluetooth REPL; actively maintained |
| S9 | web | https://education.lego.com/en-us/spike-update-2026/ | 2026-06-16 | Official retirement page: end-of-sales June 30, 2026; SPIKE App no new features after June 30; FLL no longer eligible from 2026-2027 season |
| S10 | web | https://education.lego.com/en-us/products/lego-education-spike-prime-set/45678/ | 2026-06-16 | Official product page: "This product is retiring on June 30, 2026." |
| S11 | web | https://blocksmag.com/lego-education-retires-spike-portfolio/ | 2026-06-16 | Confirms LEGO.com stock already depleted: "with the entire range listed as out of stock on LEGO.com, it seems direct sales have already ceased" |
| S12 | web | https://www.studica.ca/en/computer-science-ai-kit-68 | 2026-06-16 | LEGO CS & AI successor kit specs: 1 double motor, 1 single motor, 1 color sensor, 1 controller, 2 connection cards, 379 bricks — confirms it is not a robotics research platform |
| S13 | web | https://primelessons.org/en/RobotDesigns.html | 2026-06-16 | Community modular robot designs from single 45678 kit; confirms typed modular attachment system is used in practice for FLL |
| S14 | web | https://www.brickeconomy.com/set/45678-1/lego-education-spike-prime-set | 2026-06-16 | Secondary market: new/sealed 45678 valued at ~$566; 6.21% annual appreciation since release |
| S15 | web | https://www.amazon.com/LEGO-Education-Spike-Prime-Set/dp/B07QN7ZJF9 | 2026-06-16 | Amazon listing (user-shared): confirms third-party availability despite LEGO.com stock-out |
| S16 | web | https://bigl.es/microcontroller-monday-lego-spike-prime/ | 2026-06-16 | Confirms STM32F413xx Cortex M4 @ ~100MHz, Flash ~1-1.5MB, SRAM 320KB |

---

## Excerpts

### S3 — gpdaniels/spike-prime GitHub README
https://github.com/gpdaniels/spike-prime
> STM32F413 (Architecture: ARM Cortex M4, ROM: 1M, RAM: 320k, Clock: 100MHz).
> Medium motor with integrated absolute orientation sensor, accuracy +- 3 degrees.
> Measures depth to 2m (fast to 30cm) with 1mm resolution. Has 4 white LED outputs.
> Measures touch, tap, and force up to 10N (About 1Kg) at an accuracy of 0.65N.

### S7 — Raspberry Pi Build HAT announcement
https://www.raspberrypi.com/news/raspberry-pi-build-hat-lego-education/
> The Build HAT library already supports all the LEGO Technic devices included in the SPIKE Portfolio, along with those from the LEGO® MINDSTORMS® Robot Inventor kit and other devices that use an LPF2 connector.
> Communication with the Build HAT uses a text protocol over /dev/serial0 (115200 baud, 8N1).

### S9 — LEGO Education SPIKE Portfolio Retirement page
https://education.lego.com/en-us/spike-update-2026/
> All related products will also be available for purchase until June 30, 2026.
> For the duration of the software support period, we will fix bugs and support the newest versions of supported operating systems. We will not add any new features after June 30 2026.
> After that, changes to the FIRST LEGO League experience mean that the SPIKE solutions, as well as other legacy LEGO Education solutions, will no longer be eligible for participation.

### S11 — Blocks Magazine
https://blocksmag.com/lego-education-retires-spike-portfolio/
> LEGO Education has announced the retirement of the SPIKE portfolio... Direct sales are officially ending on June 30, 2026, but with the entire range listed as out of stock on LEGO.com, it seems direct sales have already ceased.

### S12 — Studica LEGO CS & AI Kit 6-8 specs
https://www.studica.ca/en/computer-science-ai-kit-68
> 1 double motor 1 single motor 1 color sensor 1 controller 2 connection cards 1 USB charging cable
> 379 LEGO® bricks, providing limitless hands-on possibilities

### S16 — Microcontroller Monday: LEGO SPIKE Prime
https://bigl.es/microcontroller-monday-lego-spike-prime/
> The Hub is identified as a LEGO Technic Large Hub with STM32F413xx which is a Cortex M4 unit running at around 100MHz. Flash memory is approximately 1024Kb to 1536Kb, and there is 320Kb of SRAM.
