---
id: slicer-workflow
title: Slicer Workflow (3D Printing)
updated: 2026-06-18
sources:
  - ../../raw/research/3d-printer-file-formats/index.md
tags: [3d-printing, manufacturing, workflow, g-code]
---

# Slicer Workflow (3D Printing)

The slicer is the mandatory bridge between a 3D model file and a printable machine instruction file. **A printer cannot directly execute a model file** — the model contains geometry only, with no information about temperatures, speeds, layer thickness, infill, or support structures.

relates_to::[[3d-printing-file-formats]]  
relates_to::[[vex-v5-cad-designs]]

---

## The Three-Stage Pipeline

```
[CAD / download] → model file (STL / OBJ / 3MF / STEP)
                              ↓
                    [Slicer software]
                      • layer height
                      • infill pattern
                      • supports
                      • temperatures / speeds
                              ↓
              toolpath / G-code (.gcode, .ufp, .form …)
                              ↓
                    [Printer executes]
```

Stage 1 produces the model file (from CAD or downloaded). Stage 2 — the slicer — is where all print parameters are configured and the geometry is converted to machine instructions. Stage 3 is physical execution.

---

## Slicer Software by Printer Type

| Slicer | Printer Family | Notes |
|--------|---------------|-------|
| **Cura** (Ultimaker) | FDM — very wide printer support | Free, open-source; outputs G-code or .ufp |
| **PrusaSlicer** | FDM — Prusa + many others | Free, open-source; highest surface accuracy in medical study |
| **Bambu Studio** | FDM — Bambu Lab | Free; optimized for Bambu multi-material |
| **Simplify3D** | FDM — most printers | Commercial; fine-grained control |
| **Chitubox / Lychee** | Resin (SLA/DLP/MSLA) | Cannot be swapped with FDM slicers |
| **Formlabs PreForm** | Formlabs SLA/SLS | Free, proprietary; outputs .form; imports STEP since v3.43 |

**Critical constraint:** Resin (SLA/DLP/MSLA) and FDM slicers are not interchangeable. Chitubox/Lychee produce resin toolpaths; Cura/PrusaSlicer produce FDM G-code. Each must match the printer hardware.

---

## What Slicers Configure

- **Layer height** — controls surface smoothness vs. print time (0.1mm = smooth, 0.3mm = fast)
- **Infill** — internal fill density and pattern (strength vs. material use)
- **Supports** — scaffolding for overhangs; automatically generated
- **Temperature profiles** — nozzle and bed temperatures per material (PLA, PETG, ABS, etc.)
- **Speed** — feed rate and acceleration
- **Retraction** — filament pullback to prevent stringing

---

## File Transfer to Printer

After slicing, the G-code file is transferred via:
- SD card / USB thumb drive (most common for consumer FDM)
- Direct USB cable
- WiFi / LAN (Bambu, Ultimaker, OctoPrint setups)
- Cloud (Bambu Cloud, Formlabs Dashboard)

The printer's onboard controller reads the G-code file line by line and executes it — the host computer is not required during the print.
