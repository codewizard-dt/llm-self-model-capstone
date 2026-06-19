---
id: 3d-printer-file-formats
title: Research — 3D Printer File Formats
updated: 2026-06-18
sources:
  - ../../raw/research/3d-printer-file-formats/index.md
  - ../../raw/research/3d-printer-file-formats/sources.md
tags: [3d-printing, file-formats, cad, manufacturing]
---

# Research: 3D Printer File Formats

3D printing requires two distinct file types that must never be confused: **model files** (STL, OBJ, 3MF, STEP) that describe the 3D shape, and **machine instruction files** (G-code or proprietary equivalents) that the printer's controller actually executes. The slicer application is the mandatory bridge between them — a printer cannot directly read a model file.

relates_to::[[3d-printing-file-formats]]  
relates_to::[[slicer-workflow]]  
relates_to::[[vex-v5-cad-designs]]

---

## Model File Formats

**STL (.stl)** is the universal standard — every slicer and CAD tool supports it. It encodes surface geometry as a mesh of triangular facets in ASCII or binary; it carries no color, texture, or material data. Scale is ambiguous (metric vs. imperial), so importers must verify units. Best for functional/structural parts where maximum compatibility matters.

**3MF (.3mf)** is the modern replacement, developed in 2015 by the 3MF Consortium (Microsoft, Autodesk, 3D Systems, Stratasys, HP). It is an XML-based package that stores geometry, full-color textures, multi-material data, embedded slicer settings, and authorship metadata in a single file. It has better compression than STL, eliminates scale ambiguity, and reduces non-manifold mesh errors. Modern printers (Bambu, Prusa, Ultimaker) fully support 3MF; legacy printers (pre-2018) may not.

**OBJ (.obj)** supports UV-mapped textures and color via companion `.mtl` and image files. It uses polygons (not strictly triangles) for better curved-surface approximation. Common for artistic models and 3D scans. Caveat: moving the OBJ without its companion files loses all textures.

**AMF (.amf)** is an XML additive-manufacturing format that supports material gradients; it was largely superseded by 3MF before achieving wide adoption.

**STEP (.stp/.step)** is the full B-Rep (boundary representation) solid-model format used in professional engineering CAD. It retains parametric, assembly, and curved-surface data; converting STEP → STL/3MF produces cleaner mesh results than converting from IGES. Some modern slicers (Formlabs PreForm 3.43+, Dec 2024) can now import STEP directly.

**IGES (.iges/.igs)** is the oldest neutral CAD exchange format (ANSI, first published 1980, last updated 1996). It is being actively superseded by STEP; more prone to translation errors on complex geometry.

---

## Machine Instruction Formats

**G-code** (`.gcode`, `.gco`, `.gc`) is the CNC-derived machine language executed by virtually all FDM/FFF printers. G-commands control motion (G1 = linear move, G28 = home); M-commands control machine functions (M104 = extruder temperature, M106 = fan on). A single print can contain tens of thousands of commands.

**Proprietary toolpath formats** are used by specialist printers: `.form` (Formlabs PreForm for SLA/SLS), `.ufp` (Ultimaker — G-code + thumbnail + metadata), `.gx` (FlashForge), `.xyz` (DaVinci Color — adds ink-head commands), and Stratasys GrabCAD job files.

---

## Format Selection by Printer Technology

| Technology | Typical Model Input | Machine Output |
|------------|---------------------|----------------|
| FDM (consumer/hobbyist) | STL, 3MF, OBJ | G-code (.gcode) |
| SLA/DLP/MSLA (resin) | STL, OBJ, 3MF | G-code variant or proprietary (.form, .ctb) |
| SLS (powder) | STL, 3MF | Proprietary job file |
| DMLS/SLM (metal) | STL, STEP | Proprietary machine file |
| PolyJet (Stratasys) | STL, OBJ, STEP | Proprietary .job |
