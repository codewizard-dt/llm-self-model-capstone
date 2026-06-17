---
id: ws2812b-neopixel
title: WS2812B NeoPixel LED Strip
aliases: [NeoPixel, WS2812B, NeoPixel Ring, Addressable RGB LED]
updated: 2026-06-16
sources:
  - ../../../raw/research/robot-flair-addons/index.md
tags: [tool, hardware, led, lighting, flair, raspberry-pi]
---

# WS2812B NeoPixel LED Strip

Individually addressable RGB LED strips (and rings) running on **5V DC**, each LED independently controllable to any of 16.7 million colors. The standard tool for per-generation color identity in the capstone's relates_to::[[aesthetic-vocabulary]] layer. A 1m / 60 LED strip costs $8–15; an 8–12 LED ring costs $4–8.

## Pi 5 Compatibility Caveat

The standard `rpi_ws281x` PWM/DMA library **does not work on Raspberry Pi 5** due to hardware GPIO changes. Two workarounds:

1. **SPI method (no extra hardware, recommended)** — connect LED data wire to Pi 5 SPI0-MOSI (GPIO 10, pin 19); install `adafruit-circuitpython-neopixel-spi`; enable SPI in raspi-config. Code: `import neopixel_spi as neopixel; pixels = neopixel.NeoPixel_SPI(board.SPI(), N_LEDS, pixel_order=neopixel.GRB)`
2. **Arduino Nano co-controller (~$5, 7g)** — connect Arduino Nano via USB to Pi 5; Pi sends `{"color": [R, G, B], "pattern": "breathing"}` JSON over serial; Nano drives the strip with `FastLED` or `Adafruit_NeoPixel`. Easier software path; slight extra weight and cost.

## Power

Runs at 5V — powered directly from the Pi 5's USB-C power bank via the GPIO 5V pin (pin 2/4). Each LED draws up to 60mA at full white brightness; at the capstone's typical use (partial brightness, non-white colors) expect ~3–5mA per LED. A 30-LED strip at moderate brightness draws ~150mA — negligible against the power bank's capacity.

## Mounting

Strip: adhesive backing on the underside; run along chassis rear edge or under chassis rail for underglow. Ring: mount around Camera Module 3 lens as a "glowing eye" using velcro or zip ties.

relates_to::[[raspberry-pi-5]]
used_by::[[aesthetic-vocabulary]]
