---
id: 3d-printing-file-formats
title: 3D Printing File Formats
updated: 2026-06-18
sources:
  - ../../raw/research/3d-printer-file-formats/index.md
tags: [3d-printing, file-formats, cad, manufacturing]
---

# 3D Printing File Formats

Two fundamentally different file types exist in 3D printing and must not be confused: **model files** that describe geometry, and **machine instruction files** (G-code) that the printer executes. A model file alone is never sufficient — it must pass through a slicer to become printable.

relates_to::[[slicer-workflow]]  
relates_to::[[vex-v5-cad-designs]]  
used_by::[[typed-assembly-grammar]]

---

## Model Files (pre-slicing)

These describe the 3D shape and are what you create, download, or export from CAD.

| Format | Geometry | Color/Texture | Slicer Support | Best Use |
|--------|----------|---------------|----------------|---------|
| **STL** | Triangular mesh | None | Universal | Functional parts, maximum compatibility |
| **OBJ** | Polygon mesh | Yes (via .mtl + images) | Good | Artistic/scanned models |
| **3MF** | Mesh + metadata | Yes (built-in) | Modern slicers | Multi-material, reproducible setups |
| **AMF** | Mesh + material | Yes | Limited | Legacy only |
| **STEP** | B-Rep solid | Material data | Engineering slicers | Precision engineering parts |
| **IGES** | Surface model | Limited | Wide but aging | Legacy CAD exchange |

**STL is the universal default.** Every slicer and every CAD tool supports it. Use it when compatibility is the priority.

**3MF is the modern standard.** Developed 2015 by the 3MF Consortium (Microsoft, Autodesk, 3D Systems, Stratasys, HP). It packages color, multi-material data, and embedded slicer settings into one file; it eliminates scale ambiguity and reduces mesh errors. Prefer it for any print that needs to be reproducible or shared with settings intact.

**STEP is the engineering-grade choice.** It retains the full B-Rep solid model from CAD, preserving curves, assemblies, and tolerances. Converting STEP → STL/3MF produces cleaner meshes than converting from IGES. Formlabs PreForm 3.43+ (Dec 2024) and some other modern slicers now import STEP directly — useful for precision parts where an intermediate mesh conversion would introduce error.

**IGES is legacy.** The oldest neutral CAD exchange format (ANSI standard, 1980–1996); more error-prone on complex geometry than STEP. Accept it from legacy suppliers; prefer STEP for new workflows.

---

## Machine Instruction Files (post-slicing)

These are what the printer's controller actually reads. They are produced by slicer software — never from CAD directly.

**G-code** (`.gcode`, `.gco`, `.gc`) is the CNC-derived instruction language for FDM/FFF printers. G-commands control motion; M-commands control machine functions (heaters, fans). A single print can contain tens of thousands of lines.

**Proprietary formats** are used by specialist printers: `.form` (Formlabs SLA/SLS), `.ufp` (Ultimaker — G-code + thumbnail packaged), `.gx` (FlashForge), `.xyz` (DaVinci Color), Stratasys GrabCAD job files.

---

## Design Rule for this Capstone

VEX V5 custom and 3D-printed parts should be designed to the **0.500" hole spacing / 0.125" square shaft / #8-32 screw** spec. Export from Onshape as STEP for engineering fidelity, then convert to STL/3MF for slicing. Avoid snap geometry — holes-only mounts with VEX hardware are durable in FDM.

See relates_to::[[slicer-workflow]] for the full pipeline from model file to print.
