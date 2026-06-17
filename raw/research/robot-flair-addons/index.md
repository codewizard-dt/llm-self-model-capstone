---
topic: "ad-hoc items that could be added that are not part of the VEX V5 system that would increase the self-expression of the LLMs in terms of their body shape or flair"
slug: robot-flair-addons
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Non-VEX Add-Ons for LLM Robot Self-Expression

> The VEX V5 steel structure is functionally rich but aesthetically monotonous — every generation looks like the same grey metal frame with a different arm position. A thin aesthetic vocabulary layer, drawn almost entirely from dollar-store and hardware-store materials, gives the LLM a structured grammar for **visual self-expression**: each generation can declare a color scheme, an appendage form, surface markings, and an identity marker. The key insight is that aesthetic choices can encode hypotheses ("wide side panels = testing mass distribution", "forward antennae = prioritizing forward sensing") — making flair semantically meaningful, not merely decorative. **Most options cost $0–5 and require no tools beyond scissors and tape.** 3D printing is the highest-vocabulary option but requires access; alternatives deliver most of the value without it.

---

## Research Questions

1. What non-VEX materials can attach to VEX structure without tools or cutting?
2. What cheap/free options give the most distinct visual variation between generations?
3. What attachment methods work without modifying the VEX metal?
4. Can LED-based flair be wired to the Raspberry Pi 5 without a separate microcontroller?
5. What 3D-printing options exist if access becomes available, and what's the VEX mounting spec?

---

## Current State (Codebase)

The wiki documents the VEX V5 Starter Kit's structural vocabulary at `wiki/knowledge/sources/vex-v5-starter-kit-configurations.md`. The typed assembly grammar (`wiki/knowledge/concepts/typed-assembly-grammar.md`) covers functional parameters only — motor allocation, wheel config, arm gear ratio, etc. There is **no aesthetic vocabulary** in the grammar yet. The capstone's self-model loop (`wiki/knowledge/concepts/llm-authored-self-model.md`) gives the LLM latitude to propose configuration changes, but currently only functional ones.

VEX structure uses **0.5" (12.7mm) hole spacing** on all channels/plates, #8-32 screws. [S5] The Pi 5 lives on a 56×85mm PCB with M2.5 corner holes, mounted on the robot's rear chassis. The VEX Booster Kit adds ~600 passive parts but no aesthetic vocabulary. Non-functional decorations are explicitly permitted even in VEX competition rules — "Decorations are allowed" per RECF — and this is a capstone, so there are no competition restrictions at all. [S4]

---

## Key Findings

### Attachment Methods Without Modifying VEX Metal [S4, S5, S6]

Every aesthetic add-on needs to attach to the VEX steel frame. Three methods require no drilling, cutting metal, or special tools:

| Method | How | Cost | Notes |
|--------|-----|------|-------|
| **VEX screw holes** | Thread M5 / #8-32 zip-tie heads or standoffs through existing square holes | $0 | Holes are already there; use existing VEX screws |
| **Zip tie loops** | Loop zip ties through square holes in channels; tie decorations to the zip tie | ~$3/100 | Works for foam, cardboard, wire, fabric |
| **Velcro strips (hook+loop)** | Stick adhesive-backed velcro to VEX frame; press decoration onto it | ~$5/roll | Repositionable; modular — swap panel without tools |
| **Binder clips / spring clamps** | Clip light decorations to channel flanges | ~$1 | Zero modification; removable instantly |

Velcro is the recommended primary attachment method for panels: repositionable, leaves no residue, and lets the LLM "hot-swap" an aesthetic element between generations without rebuild.

---

## Category A: Free / Scavenged (Cost $0)

### Corrugated Cardboard
Cut from shipping boxes or cereal boxes. Scores and folds easily with a butter knife. Attach with zip ties through the corrugation channels or velcro adhesive. Provides rigid-enough panels for side skins, a top deck cover, or swept-back "speed fins." Cover with aluminum foil for a metallic look. **Best free option for body panels.** [S6]

### Aluminum Foil
Wrap around foam board or cardboard backing for instant metallic sheen. Ultra-lightweight. Can be crumpled for texture, flat for a mirror surface. Attach backing piece to frame with zip ties.

### Recycled Plastic Containers
Yogurt tubs, clear plastic bottles, condiment cups → "sensor dome" over the camera or as a decorative pod. A half-sphere yogurt container with a hole cut for the Camera Module 3 lens doubles as a camera shroud and aesthetic element. Zero cost.

---

## Category B: Dollar Store / Craft Store ($1–$5 total per generation)

These are the **highest-value-per-dollar** options. A single $5 trip to Dollar Tree covers 3–4 generations of aesthetic variation.

### Craft Foam Sheets (EVA Foam) — **Top Recommendation**
$1–2 for a 6-pack of assorted colors at Dollar Tree or Walmart craft section. Cut with scissors into any shape. Attaches to VEX frame with velcro adhesive, zip ties through punched holes, or binder clips. Lightweight (~0.05 g/cm³ at 6mm), flexible, won't damage the robot if it tips over. [S8]

**Shape vocabulary for LLM**: swept-back side fins (aerodynamic personality), upright dorsal ridge (dominant stance), angled front skirt (aggressive forward lean), wide rear stabilizer wings (stability hypothesis). Each shape reads as a distinct morphological expression.

### Pipe Cleaners / Chenille Stems
$1–2 for a pack of 50 assorted colors. Twist around VEX channels by hand — no tools, no attachment hardware. Bend into antennae, whiskers, curled tendrils, or geometric cage shapes. **They move and sway during robot motion**, which is visually distinctive. A pair of forward-facing pipe-cleaner antennae reads as "sensory orientation forward." [S9]

### Colored Electrical Tape
$2–4 for a multi-color pack. Apply stripes, chevrons, or solid color blocks directly to VEX steel channels. Completely reversible — peels off cleanly. Use to: color-code left vs. right sides, mark generation number in stripe count (3 stripes = Gen 3), create visual "power lines" running the length of the arm. [S6]

### Washi Tape / Decorative Tape
$1–3 for a multi-roll pack. Same application as electrical tape but with more pattern variety (dots, stripes, geometric). Slightly less durable but much more visually distinctive. The LLM can specify pattern + placement as an aesthetic grammar choice.

### Stickers / Decals
$1–3. Generation number sticker on the top chassis plate. Team/project logo. Emoji stickers for personality. The simplest form of visual identity between generations.

### Googly Eyes
$1 for a pack of 100. Glue or tape to the claw arm tip, the front chassis plate, or the Camera Module 3 shroud. Anthropomorphizes the robot instantly and distinctly. Large eyes = curious/friendly; small eyes = focused/predatory. Cheap semantic flair. [S6]

### Pom-Poms
$1–2 for a bag of assorted colors/sizes. Velcro or zip-tie to chassis corners, arm tip, or top deck. Lightweight accent markers. LLM can specify color to match its generation palette.

### Metallic/Holographic Tape (Iridescent)
$2–4 on Amazon or craft stores. Rainbow iridescent or chrome finish. Dramatically different visual character from bare steel — applied as a strip along channel edges it makes the robot look "high-tech." Often available at dollar stores in party supply sections.

### Colored Zip Ties
$3 for a pack of assorted colors. Both functional (wire management) and aesthetic. Each generation gets a consistent zip-tie color for all wire management → visual identity that's embedded in the assembly itself.

---

## Category C: Hardware Store ($5–$15)

### Corrugated Plastic (Coroplast / Twinwall)
$8–15 for a 24"×36" sheet at Home Depot, Lowe's, or sign shops. Available in white, black, yellow, red, blue. Cuts with scissors or craft knife. Very rigid for its weight. Used officially by REV Robotics (FTC platform) for robot body panels. [S7]

Punch holes with a pen at 0.5" spacing to match VEX holes → bolt directly to frame with existing VEX screws. **Best non-printed option for rigid shaped panels.** One $10 sheet covers 5–10 generations of panels.

### Aluminum Craft Wire (18–22 gauge)
$5–8 for a 30-foot roll. Bend by hand into any shape: antennae, cage structures, arched frames, spiral elements. Lightweight, holds shape, wraps around VEX channels without attachment hardware. Can create 3D sculptural elements (a spiral halo over the robot, a wire "crown" on the arm) that add genuine morphological distinctiveness.

### Hook-and-Loop Velcro Roll
$5–8. Already mentioned as an attachment method, but worth buying a roll to enable modular swap of any aesthetic element. One roll covers all generations.

---

## Category D: Dynamic / Electronic Flair ($8–$25)

### WS2812B NeoPixel LED Strip — **Highest Visual Impact**
$8–15 for a 1m, 60 LED/m strip (Amazon, Adafruit). 5V DC — powered directly from the Pi 5's power bank, no separate power source. 16.7 million colors per LED, individually addressable. [S1, S2, S3]

**Pi 5 caveat**: The standard `rpi_ws281x` PWM library does not work on Pi 5 due to GPIO hardware changes. Two workarounds: [S10, S11]
1. **SPI method (recommended, no extra hardware)**: connect LED data wire to Pi 5 SPI0-MOSI (GPIO 10, pin 19); use `neopixel_spi` library (`pip install adafruit-circuitpython-neopixel-spi`). Requires SPI enabled in raspi-config.
2. **Arduino Nano co-controller**: Connect an Arduino Nano (~$5 clone on Amazon) via USB to the Pi 5. Pi sends `{"color": [255, 0, 128], "pattern": "breathing"}` JSON over serial; Nano drives the LED strip with standard `FastLED` or `Adafruit_NeoPixel` Arduino library. Adds 7g and $5.

Each robot generation gets a **unique color signature** specified by the LLM — "Gen 3: deep blue breathing pattern." The strip runs along the rear chassis edge or under the chassis rail for an underglow effect.

### NeoPixel Ring (8 or 12 LED)
$4–8 (Adafruit or Amazon). Mounts around the Camera Module 3 lens as a "glowing eye" ring. Same SPI or Arduino-Nano wiring. Compact, dramatic visual effect. The LLM can specify the ring color as a generation identity marker.

---

## Category E: 3D Printing (If Access Available)

3D printing is the **highest vocabulary option** — the LLM can describe an arbitrary shape and have it fabricated — but requires a printer. Access options to investigate:

| Access path | Cost | Notes |
|------------|------|-------|
| **UT Austin library / FabLab** | Free or ~$0.10/g | Public access 3D printers common at university libraries |
| **Austin Central Library** | Free | Austin Public Library has maker spaces with 3D printers |
| **Makespace Austin / local makerspace** | $5–20/month membership | Full shop access |
| **Online services (Craftcloud, Shapeways, JLCPCB)** | $3–15/part | Upload STL → shipped in 5–10 days; PLA parts at Craftcloud from ~$3 |

**VEX mounting spec for 3D printing**: holes at 0.5" (12.7mm) center spacing, square holes 4.6mm×4.6mm for VEX screws, or round holes 4.4mm diameter for zip ties. [S5] Design in TinkerCAD (free, browser-based) — no CAD experience needed.

**High-value shapes the LLM could specify**: a decorative claw "beak" cover that mounts over the plastic claw assembly; a custom chassis top plate with the generation number embossed; swept aerodynamic side fins with a generation-specific profile; a "visor" over the camera that changes angle per generation.

**If no printer is available**: laser-cut acrylic from SendCutSend ($10–20/part, 2–4 day lead time) achieves similar results for flat shapes. Corrugated plastic cut with scissors achieves 80% of the result for $0 extra cost.

---

## Aesthetic Vocabulary Extension for Typed Grammar

These add-ons map cleanly onto a new `aesthetic_vocabulary` block in the typed assembly grammar:

```json
{
  "aesthetic_vocabulary": {
    "body_panel": {
      "material": ["corrugated_plastic", "craft_foam", "cardboard", "acrylic", "3d_print", "none"],
      "position": ["left_side", "right_side", "top_deck", "front_face", "rear_skirt"],
      "color": ["generation_palette_primary", "generation_palette_accent", "raw_steel"]
    },
    "surface_markings": {
      "tape_pattern": ["none", "stripes", "chevron", "solid_block", "diagonal"],
      "tape_color": ["red", "blue", "yellow", "black", "iridescent"],
      "identity_label": ["sticker_numeral", "painted_numeral", "none"]
    },
    "appendages": {
      "type": ["none", "antennae", "swept_fins", "dorsal_ridge", "cage_frame", "whiskers"],
      "material": ["pipe_cleaner", "craft_wire", "foam", "cardboard", "3d_print"],
      "position": ["top_chassis", "arm_tip", "front_bumper", "rear_deck"]
    },
    "accent_lighting": {
      "type": ["none", "neopixel_strip", "neopixel_ring"],
      "position": ["chassis_edge", "arm_tip", "camera_ring"],
      "pattern": ["solid", "breathing", "chase", "generation_pulse"]
    }
  }
}
```

This is a **non-functional layer** — it doesn't affect motor commands, telemetry contracts, or the self-model's functional parameters. But it lets the LLM make choices that are visible, photographable, and narratively meaningful: "Gen 4 chose blue side panels and forward antennae, hypothesizing that a narrower visual profile would reduce lateral drag during the pull task."

---

## Constraints

1. **Weight budget**: The Clawbot chassis supports ~500g additional payload; the Pi 5 system already uses ~316g. Total aesthetic add-on weight must stay under ~150g to preserve robot dynamics. EVA foam, pipe cleaners, and tape are all negligible; corrugated plastic panels are ~15–30g each.
2. **Interference with sensors/motors**: Nothing should obstruct the Camera Module 3 FOV (front-facing, ~120° for the Wide variant) or interfere with claw mechanism travel.
3. **Reversibility**: For generation transitions, all add-ons should be removable without tools. Velcro, zip ties, and binder clips meet this. Hot glue does not — avoid it for primary attachment.
4. **Pi 5 NeoPixel caveat**: Standard `rpi_ws281x` does not work on Pi 5. Use SPI method (`neopixel_spi` library) or Arduino Nano co-controller.
5. **3D print access TBD**: UT Austin FabLab, Austin Public Library maker spaces, and online services are plausible; confirm before designing for printed parts.

---

## Recommendation

**Immediate, no-cost start**: cardboard fins + pipe-cleaner antennae + colored electrical tape stripes. Zero spend, fully reversible, covers 3–4 visually distinct generations.

**$10 upgrade**: one sheet of corrugated plastic ($8) + a pack of colored zip ties ($3) → rigid body panels that bolt to VEX holes, consistent wire color coding.

**$20 upgrade**: add a 1m WS2812B LED strip ($10) wired via SPI to Pi 5 → each generation has a unique glowing color identity. This is the single highest-impact dollar spent on flair.

**If 3D printing access confirmed**: design a custom top-deck plate (TinkerCAD, 30 min) with the generation number embossed and the VEX hole pattern — ordered from an online service for ~$8, shipped in 5 days.

---

## Next Steps

- `/task-add "Build aesthetic vocabulary JSON block and add to typed-assembly-grammar concept page"` — codify the `aesthetic_vocabulary` schema so the LLM can actually generate and parse it
- `/task-add "Procure: EVA foam sheets, colored zip ties, pipe cleaners, electrical tape"` — $5–8 total, covers Gen 0–5 aesthetic variation
- Confirm 3D printer access: UT Austin Fab Lab (fab.utexas.edu), Austin Public Library (Austin Digital Harbor, 710 W César Chávez St), or Craftcloud for mail-order prints
- Decide NeoPixel integration path: SPI-direct (no extra hardware) vs. Arduino Nano co-controller (easier software, $5 extra)
- `/decision-create` on whether aesthetic choices are LLM-authored (self-expression) or human-chosen (external variable) — the capstone story is stronger if the LLM owns them
