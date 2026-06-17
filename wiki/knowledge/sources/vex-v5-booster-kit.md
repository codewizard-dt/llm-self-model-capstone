---
id: vex-v5-booster-kit
title: VEX V5 Booster Kit (Product Research)
updated: 2026-06-16
sources:
  - ../../../raw/research/vex-v5-booster-kit/index.md
tags: [source, hardware, vex, parts-catalog, morphology]
---

# VEX V5 Booster Kit (Product Research)

The **VEX Booster Kit (276-2232, $214.49)** is a ~600-piece bundle of purely passive structural and motion parts — steel channels, plates, angles, gussets, standoffs, shafts, bearings, ~290 fasteners, a Gear Kit assortment, 19T rack gears, intake rollers, and motor clutches. **No electronics whatsoever**: no brain, controller, radio, battery, motors, or sensors. VEX markets it as the "Top Recommended Add-On Kit" specifically for builders who want to maximize versatility. The product page explicitly states it **"Works with VEX V5, VEX U, VEX AI"** — the steel structure subsystem is shared across VEX's EDR and V5 platforms (the parts-list PDF carries ©2018 "VEX EDR" branding but cross-system compatibility is confirmed).

For this project's core mechanism — the **typed assembly grammar** — the Booster Kit is a high-leverage addition because **the parts catalog is the morphology search space**. The kit roughly triples the Starter Kit's generic structural inventory and, more importantly, introduces **four new typed primitives** the base kit lacks: `linear_actuator` (rack-and-pinion via 19T rack gear + Gear Kit), `intake` (intake rollers), `long_arm` (12" shafts), and `slip_release` (motor clutches). Each is a new node type the LLM generator can compose, directly expanding the grab/pull/throw capability envelope.

The binding constraint is **actuation, not structure**: the Starter Kit's cap of four V5 Smart Motors is unchanged by this kit. The recommended purchase is the Booster Kit *plus* 2–4 additional Smart Motors (~$53 each). One EDR-era caveat: the Motor Clutch (276-1098) and Intake Roller (276-1499) were designed for the legacy 3-wire motor interface; V5 Smart Motor mounting should be verified on receipt before treating those two items as reliable catalog entries.

relates_to::[[vex-v5]]  
expands::[[typed-assembly-grammar]]  
extends::[[task-telemetry-contract]]  
derived_from::[[vex-v5-customization-grab-pull-throw]]
