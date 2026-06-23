---
id: hailo-ai-hat
title: Raspberry Pi AI HAT+
aliases: [Hailo AI HAT, AI HAT+, Hailo-8L, Hailo-8, AI HAT+ 2, Hailo-10H]
updated: 2026-06-23
sources:
  - ../../../raw/research/rpi-os-options/index.md
  - ../../../raw/research/rpi-os-options/index-2.md
tags: [tool, hardware, ai-accelerator, raspberry-pi, hailo]
---

# Raspberry Pi AI HAT+

An add-on board for Raspberry Pi 5 featuring a Hailo neural network accelerator connected over PCIe Gen 3. Delivers 13–40 TOPS of INT8 inference, enabling YOLOv8/v11 at **30+ FPS** — approximately 3× the throughput of the Pi 5 CPU alone (~8–10 FPS).

relates_to::[[raspberry-pi-5]]
relates_to::[[pi-camera-module-3]]
relates_to::[[rpi-coprocessor-os-options]]
derived_from::[[rpi-os-options]]

## Variants and Pricing

| Model | Accelerator | Performance | Price |
|-------|------------|-------------|-------|
| AI HAT+ (13T) | Hailo-8L | 13 TOPS | $70 |
| AI HAT+ (26T) | Hailo-8 | 26 TOPS | $110 |
| AI HAT+ 2 | Hailo-10H + 8 GB RAM | 40 TOPS (INT4) | $130 |

The AI HAT+ 2 adds 8 GB of dedicated on-board RAM and supports LLMs / VLMs. For pure YOLO detection tasks, the $70 13 TOPS variant is sufficient.

## OS Compatibility

**Fully supported on both Bookworm and Trixie** (as of fall 2025). Hailo support was missing when Trixie shipped (July 2025) but was re-added in a subsequent RPi software update.

Install on Bookworm or Trixie:
```bash
sudo apt update && sudo apt install dkms hailo-all
```

For AI HAT+ 2:
```bash
sudo apt install hailo-h10-all
```

**Recommended: stay on Bookworm** — Trixie ships Python 3.13 which causes compat issues (Open WebUI requires Docker; some pip packages need pins). Hailo works equally well on Bookworm.

## Integration with Camera Stack

Fully integrated into the Raspberry Pi camera software stack (libcamera, rpicam-apps, Picamera2). Example YOLO inference:
```bash
rpicam-hello -t 0 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json \
  --lores-width 640 --lores-height 640
```

Python via `picamera2`:
```python
# from picamera2/examples/hailo/detect.py
python3 detect.py -m /usr/share/hailo-models/yolov11m_h10.hef -l coco.txt
```

## Capstone Relevance

**Lowest-risk post-showcase upgrade path** for the capstone:
- No reflash needed (works on current Bookworm SD)
- Near-zero code change (picamera2 hailo/detect.py is drop-in)
- 3× FPS improvement: 30+ FPS vs ~8–10 FPS current
- Pi 5 PCIe slot is available (no M.2 NVMe currently in use)
- In-stock at Adafruit, PiShop, Vilros at $70 (13 TOPS variant)

Requires firmware update (post-January 2025 EEPROM) for AI HAT+ 2; standard AI HAT+ works with any current Bookworm installation.
