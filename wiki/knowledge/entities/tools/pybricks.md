---
id: pybricks
title: Pybricks
aliases: [PyBricks, Pybricks firmware]
updated: 2026-06-16
sources:
  - ../../../raw/research/lego-spike-prime/index.md
tags: [tool, firmware, python, lego, micropython, spike-prime]
---

# Pybricks

Open-source **MicroPython-based alternative firmware** for LEGO smart hubs (BOOST, City, Technic, MINDSTORMS, SPIKE). For this project it is the **recommended integration path** for [[lego-spike-prime]]: flashing Pybricks onto the SPIKE Prime hub replaces LEGO's firmware with a cleaner, more complete Python API (`pybricks.hubs.PrimeHub`, `pybricks.pupdevices.Motor/ColorSensor/UltrasonicSensor/ForceSensor`, `pybricks.parameters`), plus offline on-hub program storage and a Bluetooth REPL. Actively maintained and VS Code-compatible.

Its decisive advantage over the native SPIKE App Python path: Pybricks **does not depend on LEGO's retiring toolchain**, so it survives the SPIKE App end-of-support on June 30 2026. The firmware flash is reversible. In the capstone stack, Pybricks runs on the hub while the workstation runs the LLM self-model pipeline, communicating over USB/Bluetooth serial.

used_by::[[physical-robot-software-factory]]
controls::[[lego-spike-prime]]
relates_to::[[raspberry-pi-build-hat]]
relates_to::[[research-lego-spike-prime]]
