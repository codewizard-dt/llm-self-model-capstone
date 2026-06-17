---
topic: "ad-hoc items that could be added that are not part of the VEX V5 system that would increase the self-expression of the LLMs in terms of their body shape or flair"
slug: robot-flair-addons
researched: 2026-06-16
---

# Primary Sources — Non-VEX Robot Flair Add-Ons

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage | 2026-06-16 | Install command `pip3 install rpi_ws281x adafruit-circuitpython-neopixel`; Pi 5 requires extra work due to GPIO changes |
| S2 | web | https://github.com/jgarff/rpi_ws281x | 2026-06-16 | Library uses DMA/PWM/PCM; valid GPIO pins for WS281X: GPIO10, GPIO12, GPIO18, GPIO21; SPI on GPIO10 (MOSI) |
| S3 | web | https://www.pololu.com/product/2547 | 2026-06-16 | WS2812B strip runs at 5V; individually addressable; Adafruit NeoPixel library compatible |
| S4 | web | https://kb.roboticseducation.org/hc/en-us/articles/13230666960407 | 2026-06-16 | VEX competition rules: "Decorations are allowed"; non-functional decorations explicitly permitted; non-VEX power allowed for non-functional decoration per R8e |
| S5 | web | https://wiki.purduesigbots.com/hardware/misc.-vex-parts-1/structure/plate-metal-and-flat-bars | 2026-06-16 | Confirmed: VEX V5 uses standard 0.5" (12.7mm) hole spacing, square bores; same spec as VEX EDR |
| S6 | inference | *(no primary source — general craft knowledge)* | 2026-06-16 | Dollar Tree availability of EVA foam, googly eyes, pipe cleaners, tape; corrugated cardboard from recycling; attachment via zip ties through VEX square holes |
| S7 | web | https://docs.revrobotics.com/duo-build/structure/corrugated-plastic-sheets | 2026-06-16 | REV Robotics officially uses corrugated plastic sheets for robot body panels; "sturdy, lightweight, easy to cut with hand tools"; used as protective panels, bumper panels, enclosures |
| S8 | web | https://www.instructables.com/Introduction-to-EVA-Foam/ | 2026-06-16 | EVA foam: lightweight, heat-shapeable, beloved for robot costumes and props; density ~0.05 g/cm³; easy to cut, glue, paint |
| S9 | web | https://craftytwisty.com/cardboard-crafts/ | 2026-06-16 | Pipe cleaners as robot antennae; cardboard for robot body shapes; aluminum foil as metallic covering |
| S10 | web | https://forums.raspberrypi.com/viewtopic.php?t=375103 | 2026-06-16 | Pi 5 workaround: "connect to MOSI of SPI0 or SPI1 and use `import neopixel_spi as neopixel`" |
| S11 | web | https://core-electronics.com.au/guides/fully-addressable-rgb-raspberry-pi/ | 2026-06-16 | "Due to changes in GPIO controls, Neopixels are not currently working with the Raspberry Pi5" — SPI method required |
| S12 | web | https://kb.vex.com/hc/en-us/articles/360044560952-Creating-Your-Own-Parts-for-VEX-IQ | 2026-06-16 | VEX IQ/EDR 3D print spec: 12.70mm (0.5") hole spacing, 3.18mm (1/8") square shaft; design with holes only, mount with existing VEX hardware |
| S13 | web | https://www.stlfinder.com/3dmodels/vex-robotics-parts/ | 2026-06-16 | 690,000+ VEX 3D print models on STLFinder; CSUN, VEX U community designs; confirmed community ecosystem |
| S14 | web | https://sendcutsend.com/materials/acrylic/ | 2026-06-16 | Laser-cut acrylic: available in 10 colors, 3 thicknesses; 2–4 day lead time; cast acrylic cuts cleanly with flame-polished edges |

## Excerpts

### S4 — RECF Robot Inspection Details
https://kb.roboticseducation.org/hc/en-us/articles/13230666960407-VEX-V5-Robotics-Competition-Robot-Inspection-Details-and-Edge-Cases
> "Decorations are allowed... Aesthetic/non-functional labeling (e.g., markers, stickers, paint, etc.)... Electrical power comes from VEX batteries only. Robots may use one (1) V5 Robot Battery (276-4811) to power the V5 Robot Brain. No other sources of electrical power are permitted on the robot, **unless used as part of a non-functional decoration per R8e.**"

### S5 — Purdue SIGBots Wiki: Plate Metal
https://wiki.purduesigbots.com/hardware/misc.-vex-parts-1/structure/plate-metal-and-flat-bars
> "As barebones as it gets, Plate Metal is a 5x15 or 5x25 hole plate consisting of the standard square VEX bores every **0.5 inches (12.7mm)**."

### S7 — REV Robotics Corrugated Plastic Sheets
https://docs.revrobotics.com/duo-build/structure/corrugated-plastic-sheets
> "Corrugated plastic sheets are intended for use as a consumable flat stock to make wedges, panels, and more. This plastic is **sturdy, lightweight, and easy to cut with hand tools**. Corrugated plastic sheets are a great substitute for other types of plastic panels... One robot in this picture is using the plastic sheets as bumper panels."

### S10 — Pi 5 NeoPixel SPI Workaround
https://forums.raspberrypi.com/viewtopic.php?t=375103
> "What you need is to connect to MOSI of SPI0 or SPI1 and use this: **import neopixel_spi as neopixel**"

### S11 — NeoPixels Not Working on Pi 5
https://core-electronics.com.au/guides/fully-addressable-rgb-raspberry-pi/
> "**Due to changes in GPIO controls, Neopixels are not currently working with the Raspberry Pi5.** [Standard PWM/DMA library]"
