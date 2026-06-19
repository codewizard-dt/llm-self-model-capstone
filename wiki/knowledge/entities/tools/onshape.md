---
id: onshape
title: Onshape
aliases: [Onshape CAD, Onshape Education, PTC Onshape]
updated: 2026-06-18
sources:
  - ../../../raw/research/vex-v5-cad-designs/index.md
tags: [tool, cad, cloud, vex]
---

# Onshape

A professional-grade cloud-native CAD platform (acquired by PTC) used for VEX V5 robot design. **Free for educators** via an Onshape Education account. No install required — full parametric 3D CAD and assembly in the browser, with real-time collaboration.

## VEX V5 Parts Library

The Onshape Education team maintains an official **VEX V5 Parts Library** accessible from the Onshape App Store ("VEX Library"). Key facts:

- **100+ V5 parts and assemblies** with correct appearances, materials, weights, and VEX part numbers
- Parts have been placed into assemblies **500,000+ times**
- Access: free Onshape Education account → App Store → "VEX Library" → insert parts into any document
- Recent additions (as of 2026): 5.5W motors, anti-static traction wheels, Over Under game field, configurable bearing inserts, rubber bumper

This library is the fastest path to an editable, engineering-accurate VEX V5 robot assembly. Teams follow the `instructions.online` 3D build for any official build and recreate it with Onshape parts to obtain a live, editable CAD file — including the Hero Bots for which VEX does not publish downloadable assembly CAD.

## Export for 3D Printing

Onshape exports parts as **STEP** (`.stp`) — the preferred engineering-grade format for 3D printing workflows. Exporting as STEP rather than STL preserves full B-Rep geometry; the downstream slicer (or a conversion tool) then produces a cleaner mesh than an STL export would. Modern slicers such as Formlabs PreForm 3.43+ accept STEP directly. For FDM printing, export STEP → convert to STL or 3MF in the slicer. VEX-compatible 3D-printed parts must follow the 0.500" hole-spacing / 0.125" square shaft / #8-32 screw spec.

See relates_to::[[3d-printing-file-formats]] and relates_to::[[slicer-workflow]] for full file-format and pipeline details.

## Community Use

The VEX competition community maintains public Onshape docs for Push Back and other game fields, competition robot design reveals, and VEXU part libraries. Most teams do not share their actual robot files publicly; the official Onshape VEX V5 Parts Library is the authoritative geometry source.

relates_to::[[vex-v5]]  
relates_to::[[typed-assembly-grammar]]  
relates_to::[[3d-printing-file-formats]]  
used_for::[[vex-v5-cad-designs]]
