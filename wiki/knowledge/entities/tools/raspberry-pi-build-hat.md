---
id: raspberry-pi-build-hat
title: Raspberry Pi Build HAT
aliases: [Build HAT, Raspberry Pi Build HAT]
updated: 2026-06-16
sources:
  - ../../../raw/research/lego-spike-prime/index.md
tags: [tool, hardware, raspberry-pi, lego, spike-prime, integration]
---

# Raspberry Pi Build HAT

A ~$25 Raspberry Pi add-on board (HAT) that plugs into the Pi's 40-pin GPIO header and provides **4 LPF2 connectors** for LEGO Technic motors and sensors from the SPIKE Portfolio (and MINDSTORMS Robot Inventor / any LPF2 device). Communication uses a **text serial protocol over `/dev/serial0` at 115200 baud, 8N1**, driven by a first-party Raspberry Pi Foundation Python library (`build-hat`) modeled on `gpiozero`. A separate Build HAT PSU can power both the Pi and connected LEGO devices.

For this project it is the **alternative integration path** to [[pybricks]] for [[lego-spike-prime]]: use it when the demo benefits from a **self-contained onboard Raspberry Pi** that drives a camera module, runs the local Python pipeline, and offloads LLM inference via API. Trade-off vs. the hub's native 6 ports: the Build HAT exposes only **4** device ports. Supported by the Raspberry Pi Foundation, so it is unaffected by the SPIKE App retirement.

used_by::[[physical-robot-software-factory]]
controls::[[lego-spike-prime]]
relates_to::[[pybricks]]
relates_to::[[research-lego-spike-prime]]
