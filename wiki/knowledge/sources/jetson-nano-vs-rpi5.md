---
id: jetson-nano-vs-rpi5
title: "Research: Jetson Nano / JetPack vs Raspberry Pi 5 for the Capstone Architecture"
updated: 2026-06-17
sources:
  - ../../raw/research/jetson-nano-vs-rpi5/index.md
tags: [source, research, raspberry-pi, jetson, coprocessor, hardware, comparison]
---

# Research: Jetson Nano / JetPack vs Raspberry Pi 5 for the Capstone Architecture

A systematic comparison (2026-06-17) of the NVIDIA Jetson Nano + JetPack SDK against the Raspberry Pi 5 for the capstone's VEX V5 coprocessor role. **Conclusion: the Pi 5 is definitively the better choice** — not as a compromise, but because the Jetson Nano's GPU advantage is orthogonal to the capstone's actual bottlenecks, while the Pi 5 wins on every other axis.

The VAIC reference architecture uses a Jetson Nano, but that architecture was designed for CUDA-accelerated real-time vision at 30+ FPS with a depth camera. The capstone's slow manipulation tasks (Clawbot arm, object placement) run at **0.5–2 Hz** — the Pi 5's 8–10 FPS NCNN YOLO11n inference is already 4–16× faster than the task rate. See relates_to::[[vaic-reference-architecture]] for the VAIC context, and relates_to::[[raspberry-pi-5]] for the Pi 5 architecture details.

**JetPack friction is the decisive factor.** The original Jetson Nano runs JetPack 4.6 (Ubuntu 18.04, **Python 3.6** — EOL Dec 2021). Modern YOLO/Ultralytics packages require 3rd-party wheel builds or an unofficial OS image; flashing requires NVIDIA SDK Manager on an x86 Ubuntu host. Pi OS Bookworm (Debian 12) flashes in 10–20 minutes from SD card; `pip install ultralytics pyserial apriltag` installs cleanly with no patches. For a week-limited capstone, this setup difference is material.

**Mobile power kills the Jetson Orin Nano Super option.** The current Jetson entry-level board (Orin Nano Super, $249) requires a 7–20V DC supply — a standard USB-C 5V/3A power bank **does not work**. The Pi 5's 3–5W capstone workload runs 12–15 hours from any USB-C bank. The Jetson Nano (original) requires a 5V/4A barrel jack with a J48 jumper — workable but awkward. The Pi 5 USB-C path is simpler. See also: relates_to::[[rpi-complete-kits-mobile-power]].

The **serial protocol is identical** on both platforms — `/dev/ttyACM0`, 115200 baud, pyserial, newline-delimited JSON. `V5Comm.py` from the VAIC repos runs on Pi 5 without modification. The capstone's coprocessor substitution is a drop-in at the code level; see derives_from::[[vex-coprocessor-pattern]].

## Comparison Summary

| Criteria | Jetson Nano B01 | Jetson Orin Nano Super | **Pi 5 4GB (chosen)** |
|---|---|---|---|
| CPU speed (Python/serial) | baseline | ~2× | **~3×** |
| YOLO FPS (capstone) | 30+ GPU | 67 TOPS | 8–10 FPS CPU — sufficient |
| JetPack / OS | Ubuntu 18.04, Python 3.6 | Ubuntu 22.04, Python 3.10+ | Debian 12, Python 3.11 |
| Setup time | 2–4 hrs + x86 host | 1–2 hrs | **10–20 min** |
| Mobile power | 5V/4A barrel jack | 7–20V DC only | **USB-C 5V/3A** |
| Total system cost | ~$100+ used + camera | ~$430 | **$135** |
| Availability | Dev kit EOL | In stock / backorder | **In stock** |

uses::[[raspberry-pi-5]]
relates_to::[[vaic-reference-architecture]]
derives_from::[[vex-coprocessor-pattern]]
relates_to::[[rpi-complete-kits-mobile-power]]
