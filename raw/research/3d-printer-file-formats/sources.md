---
topic: what kind of files do 3D printers need to print out designs?
slug: 3d-printer-file-formats
researched: 2026-06-18
---

# Primary Sources — 3D Printer File Formats

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://www.wevolver.com/article/3d-printer-file-formats-stl-obj-3mf | 2026-06-18 | Comprehensive overview of STL/OBJ/AMF/3MF; STL uses triangular mesh; 3MF uses XML package with textures/color/metadata |
| S2 | web | https://qidi3d.com/blogs/news/3d-printing-file-formats | 2026-06-18 | Three-stage workflow (modeling → slicing → machine execution); G-code is final output; 3MF workflow details |
| S3 | web | https://www.3dmag.com/3d-wikipedia/g-code-3d-printing-commands-slicer-output/ | 2026-06-18 | G-code structure: G-commands for motion, M-commands for machine functions; FDM standard |
| S4 | web | https://scienceinsights.org/what-is-a-slicer-for-3d-printing-and-how-does-it-work/ | 2026-06-18 | Slicer is mandatory bridge; model files contain no printer instructions; slicers generate G-code |
| S5 | web | https://www.einstar.com/blogs/einstar-academy/3d-print-file-type | 2026-06-18 | OBJ best for textured/artistic models with companion .mtl files; 3MF best for multi-material |
| S6 | web | https://www.3dnatives.com/en/best-file-format-for-3d-printing-the-complete-guide-190520254/ | 2026-06-18 | 3MF developed 2015 by consortium (Microsoft, Autodesk, 3D Systems, Stratasys, HP); STL default for simple/compatible; comparison of formats |
| S7 | web | https://hlhrapid.com/blog/3d-file-formats-to-use-for-manufacturing/ | 2026-06-18 | STEP vs IGES: STEP better for curved designs and high accuracy; IGES generally larger; STL/OBJ sufficient for most 3D printing |
| S8 | web | https://www.contenta-software.com/3dcadconverter/blog/step-vs-iges-which-format.php | 2026-06-18 | STEP preferred modern standard; converting STEP→STL/3MF produces cleaner mesh than from IGES; IGES first published 1980 |
| S9 | web | https://www.goengineer.com/blog/guide-using-formlabs-preform-software-for-sla-3d-printing | 2026-06-18 | Formlabs PreForm 3.43 (Dec 2024) added native CAD/interchange format import including STEP; uses .form proprietary output |
| S10 | web | https://3dprinting.stackexchange.com/questions/15175/slicers-and-printers-compatibility | 2026-06-18 | DaVinci Color printers use .XYZ format (not standard G-code); belt printers need non-standard slicer; most FDM printers use standard G-code |
| S11 | web | https://libguides.ouhsc.edu/c.php?g=537976&p=3999020 | 2026-06-18 | Ultimaker .ufp format: Cura packages G-code + image + printer metadata into one file |

---

## Excerpts

### S1 — Wevolver: 3D Printer File Formats
https://www.wevolver.com/article/3d-printer-file-formats-stl-obj-3mf
> "The evolution of 3D printer file formats is a testament to the ongoing innovation in the field of additive manufacturing. From the simplicity and universality of STL to the advanced capabilities of 3MF, each format brings unique benefits and challenges to the table."
> "STL files are limited to encoding the surface geometry using triangular facets and cannot represent material gradients. Newer formats like AMF and 3MF can encode material properties at different points within the object."

### S2 — Qidi3D: STL vs OBJ vs 3MF
https://qidi3d.com/blogs/news/3d-printing-file-formats
> "In a typical workflow, model files such as STL, OBJ, 3MF, STEP, and AMF are used before slicing, while the printer itself ultimately runs G-code."
> "A 3D printing workflow usually has three stages: modeling, slicing, and machine execution. You first create or export a model, then import it into a slicer, and finally generate G-code for the printer."

### S3 — 3D Mag: G-code commands
https://www.3dmag.com/3d-wikipedia/g-code-3d-printing-commands-slicer-output/
> "The structure of G-code includes several core elements: G-commands control motion (such as straight lines or arcs), M-commands manage machine functions (like heating or fan operations), and other commands handle coordinates, feed rates, and extrusion. In a typical additive manufacturing workflow, slicer software translates a 3D model into thousands of individual commands."

### S4 — ScienceInsights: What is a Slicer
https://scienceinsights.org/what-is-a-slicer-for-3d-printing-and-how-does-it-work/
> "A slicer is software that converts a 3D digital model into the step-by-step instructions a 3D printer needs to build an object, layer by layer. Without it, your printer has no idea what to do with a design file."
> "Your 3D model is just geometry: a shell of triangles describing a shape. It contains no information about how hot the nozzle should be, how fast the printer should move, or how solid the inside of the object needs to be."

### S6 — 3Dnatives: Best File Format Guide
https://www.3dnatives.com/en/best-file-format-for-3d-printing-the-complete-guide-190520254/
> "The 3MF format, developed in 2015 by a consortium of leading companies, aims to become the new standard for 3D printing."
> "STL remains the default choice for simple models and maximum compatibility, while 3MF is emerging as the future standard for more complex projects."

### S8 — Contenta Software: STEP vs IGES
https://www.contenta-software.com/3dcadconverter/blog/step-vs-iges-which-format.php
> "3D printing and additive manufacturing — converting STEP to STL or 3MF produces cleaner, more predictable mesh results than converting from IGES."
> "IGES (Initial Graphics Exchange Specification) was first published in 1980 by the U.S. National Bureau of Standards (now NIST)."

### S9 — GoEngineer: Formlabs PreForm
https://www.goengineer.com/blog/guide-using-formlabs-preform-software-for-sla-3d-printing
> "With the PreForm 3.43 update in early December 2024, PreForm now supports not just mesh files, but also a wide variety of native CAD and interchange format files!"

### S10 — 3D Printing Stack Exchange: Slicer compatibility
https://3dprinting.stackexchange.com/questions/15175/slicers-and-printers-compatibility
> "However, some machines are not compatible with normal slicers, because they either don't run G-code but a proprietary file format... An example of the former type is for example the DaVinci Color printers that use .XYZ files, which contain not only movement commands for the printhead and extruder, but also color print commands for the ink-head."

### S11 — OUHSC Library Guide: Ultimaker UFP
https://libguides.ouhsc.edu/c.php?g=537976&p=3999020
> "Ultimaker Cura is a FREE, fast, easy-to-use slicer software that converts a digital 3D object into a .ufp toolpath format understood by the Ultimaker family of 3D printers. The .ufp differs .gcode in that the Cura software packages a .gcode file with an image file and some extra information for the printer."
