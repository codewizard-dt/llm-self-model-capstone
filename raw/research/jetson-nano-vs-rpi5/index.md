---
topic: "compare the jetson nano and NVIDIA JetPack to rpi 5 and our suggested architecture"
slug: jetson-nano-vs-rpi5
researched: 2026-06-17
sources: [./sources.md]
---

# Research: Jetson Nano / JetPack vs Raspberry Pi 5 for the Capstone Architecture

> The Raspberry Pi 5 is the correct coprocessor for this capstone. For the capstone's actual workloads — 8-10 FPS YOLO11n, AprilTag localization, USB-serial telemetry bridge, and Claude API calls — the Pi 5 outperforms the original Jetson Nano on every CPU-bound task, runs the identical serial protocol, costs far less, and eliminates the JetPack ecosystem's setup friction. The original Jetson Nano developer kit is now EOL; its worthy successor (Jetson Orin Nano Super, $249) is overkill and would slow down capstone development velocity without delivering needed capability.

---

## Research Questions

1. What are the hardware and performance differences between the Jetson Nano and Pi 5 for the capstone's specific workloads (YOLO, AprilTags, serial bridge, LLM API)?
2. What is JetPack, what does it add, and what friction does it introduce vs Raspberry Pi OS?
3. What is the current availability and pricing landscape for Jetson Nano vs Pi 5?
4. What are the mobile power implications for on-robot deployment?
5. How compatible is the VAIC reference architecture (Jetson Nano) code with Pi 5?

---

## Current State (Codebase)

The capstone's suggested architecture (from `raw/research/vision-vex-architecture/index.md` and `wiki/knowledge/entities/tools/raspberry-pi-5.md`) is:

```
VEX V5 Brain (deterministic motor control)
    ↕ USB serial, 115200 baud, /dev/ttyACM0, newline-delimited JSON
Raspberry Pi 5 (4GB, ~$110)
    ├── vision_loop.py     → YOLO11n NCNN + AprilTag → detection JSON
    ├── serial_bridge.py   → V5 telemetry → JSONL → motor commands
    └── llm_loop.py        → JSONL → Claude API → revised self-model
    ↕ CSI ribbon
Pi Camera Module 3 ($25, 12MP, PDAF)
    Power: standard USB-C 5V/3A power bank (12-15 hrs runtime)
```

The **VAIC reference architecture** (`wiki/knowledge/entities/tools/vaic-reference-architecture.md`) is the official VEX AI Competition stack. It uses a Jetson Nano as the coprocessor with an Intel RealSense depth camera and CUDA-accelerated YOLO inference. The capstone's architecture is an explicit substitution of Pi 5 for the Jetson Nano — the serial protocol (`V5Comm.py`, `/dev/ttyACM0`, 115200 baud) is coprocessor-agnostic and identical on both platforms [S6].

---

## Key Findings

### 1. Hardware Comparison

| Spec | Jetson Nano (B01) | Jetson Orin Nano Super | Raspberry Pi 5 (4GB) |
|------|-------------------|----------------------|----------------------|
| CPU | 4× Cortex-A57 @ 1.47 GHz | 6× Cortex-A78AE @ 1.7 GHz | 4× Cortex-A76 @ 2.4 GHz |
| GPU | 128-core Maxwell (CUDA 10.2) | 1024-core Ampere, 32 Tensor cores | None (VideoCore VII, no CUDA) |
| AI TOPS | ~0.5 TOPS | 67 TOPS (MAXN mode) | 0 native (13 TOPS w/ Hailo-8L HAT) |
| RAM | 4 GB LPDDR4 | 8 GB LPDDR5 | 4 GB LPDDR4X |
| CPU speed (pure tasks) | baseline | ~2× Nano | **~3× Nano** [S3] |

The Pi 5's Cortex-A76 is fundamentally newer than the Jetson Nano's A57 — roughly **3× faster on CPU-bound workloads** including Python scripts, JSON processing, serial bridge, and LLM API calls [S3].

### 2. YOLO Inference Performance

| Platform | Model | FPS | Notes |
|---|---|---|---|
| Jetson Nano (GPU/TensorRT) | YOLOv4-tiny | 15-25 FPS | CUDA GPU path [S3] |
| Jetson Nano (GPU/TensorRT) | YOLOv5 | 30+ FPS | TensorRT optimised [S2] |
| Pi 5 (CPU, NCNN INT8) | YOLO11n | 8-10 FPS @ 640×480 | Our stack [S7] |
| Pi 5 (CPU, NCNN INT8) | YOLO11n | 25+ FPS @ 240×240 | Downsampled [S7] |
| Pi 5 + Hailo-8L HAT ($70) | YOLOv8s | 41 FPS @ 640×640 | Optional NPU [S8] |

**Capstone verdict**: The capstone's slow-manipulation tasks (Clawbot arm movements, object placement) operate at ~0.5–2 Hz. **8 FPS is 4–16× faster than the task rate** — the Pi 5 CPU path is already overkill. The Jetson Nano's 30+ FPS GPU advantage does not translate to a capstone benefit. [S7]

### 3. JetPack SDK: What It Is and What It Costs

JetPack is NVIDIA's mandatory OS/SDK bundle for all Jetson platforms [S4]:

- **Contents**: Linux kernel (L4T / Ubuntu base), CUDA, cuDNN, TensorRT, DeepStream, Isaac SDK, VPI
- **Setup path**: Requires NVIDIA SDK Manager running on an **x86 Ubuntu PC** to flash the Jetson Nano. (Orin Nano Super can be flashed from an SD card image, eliminating this requirement.)
- **OS base**: JetPack 4.6 (latest for Jetson Nano) is **Ubuntu 18.04** with Python 3.6 — Python 3.6 reached end-of-life December 2021. Modern packages (YOLOv8, Ultralytics, pyserial 3.5+) require either 3rd-party custom wheel builds or an unofficial OS image [S5].
- **Python compatibility trap**: Community reports confirm that NVIDIA's bundled Python/PyTorch packages do not work with modern YOLO out-of-the-box. A 3rd-party patched image (Qengineering) is required [S5].
- **JetPack 6.x (for Orin)**: Much improved — Ubuntu 22.04, Python 3.10+, modern libraries. But the Orin Nano Super costs $249 and has its own setup complexity (firmware update required before flashing) [S4].

By contrast, Pi OS Bookworm (Debian 12) or Ubuntu 22.04 on Pi 5:
- Flashes from a standard SD card with Raspberry Pi Imager (~5 minutes)
- Python 3.11 with full `pip` — any package installs natively
- `apt install python3-opencv` works without modification
- `pip install ultralytics pyserial apriltag` — done

**Setup overhead estimate**: Jetson Nano JetPack setup takes 2–4 hours including SDK Manager installation, host PC requirements, library patching, and Python version management. Pi 5 OS setup takes 10–20 minutes. This matters for a 10-week capstone.

### 4. Availability and Pricing (June 2026)

| Platform | Status | Price (June 2026) | Camera | Notes |
|---|---|---|---|---|
| Jetson Nano B01 Dev Kit | **EOL** — discontinued | Used/grey market ~$80–150 | Not included | Module available until Jan 2027 [S1] |
| Jetson Orin Nano Super | Current, in demand, backorder reported | $249 dev kit | Not included | Dev kit only [S9] |
| Intel RealSense D435 | Current | ~$180–200 | Depth camera | Used in VAIC reference |
| Raspberry Pi 5 (4GB) | In stock | $110 [S7] | Not included | 3× price hike since 2025 |
| Pi Camera Module 3 | In stock | $25 | CSI ribbon | Recommended pairing |
| **Pi 5 4GB + Camera** | **Complete** | **$135** | Included | Full capstone camera system |
| **Jetson Orin Nano Super + Camera** | Complete | **~$430–450** | Intel RealSense | 3.2× more expensive |

### 5. Mobile Power for On-Robot Deployment

This is a critical difference that the wiki has already identified but not quantified versus Jetson:

| Platform | Power Draw | Power Connector | Power Bank Compatibility |
|---|---|---|---|
| Jetson Nano (MAXN/10W) | 10W | 5V/4A **barrel jack** (J48 jumper required) | Needs barrel-jack power bank or DC-DC converter |
| Jetson Nano (USB mode) | 5W | micro-USB | Standard 5V/2A bank but limited to 5W mode |
| Jetson Orin Nano Super (15W) | 7–25W | **DC jack 7–20V** | Requires dedicated DC supply — USB-C power banks do NOT work [S10] |
| **Pi 5 (capstone workload)** | **3–5W** | USB-C 5V/3A | **Standard 10,000 mAh USB-C power bank — 12–15 hrs** [S7] |

The Jetson Orin Nano Super **cannot be powered from a standard USB-C power bank** — it requires a DC supply at 7–20V. On a VEX Clawbot chassis, this means adding a DC voltage regulator from the V5 battery (which is explicitly warned against for the Pi 5 in our architecture, and even more problematic for Jetson). The Pi 5's USB-C power bank approach is the simplest possible mobile power solution.

### 6. Thermal Behaviour on a Robot Chassis

- **Jetson Nano (original)**: Ships with a passive heatsink only. Under sustained GPU load (YOLO inference) in an enclosed robot chassis, it reaches 50°C+ and begins thermal throttling within 20–30 minutes — producing **inconsistent inference latency**, which would corrupt the Task Telemetry Contract timing [S11, S12].
- **Jetson Orin Nano Super**: Ships with an active cooling fan. Better, but fan adds weight, noise, and a moving part; sustained >15W still risks throttling in enclosures [S13].
- **Pi 5 (3–5W workload)**: A metal case or passive heatsink is sufficient. No throttling reported at 3–5W. No moving parts needed.

### 7. Protocol Compatibility (No Code Rewrite Needed)

From `wiki/knowledge/entities/tools/vaic-reference-architecture.md` and confirmed by community repos: the Jetson Nano's `V5Comm.py` uses `/dev/ttyACM0` at 115200 baud with pyserial — **character-for-character identical to the Pi 5 implementation** [S6]. The serial bridge script (`serial_bridge.py`) requires zero changes when switching from Jetson to Pi 5.

---

## Constraints

- The capstone needs to be buildable and demonstrable within weeks, not months — developer setup time is a real constraint.
- Mobile power must come from a standard USB power bank (V5 battery is motor-rated, not safe for coprocessor).
- Pi Camera Module 3 is already specified in the architecture and budgeted ($25, CSI ribbon, included adapter cable).
- The YOLO inference rate requirement is 8 FPS minimum (sufficient for 0.5–2 Hz manipulation tasks) — not 30+ FPS.
- The capstone's novel contribution is the **LLM self-model loop**, not GPU inference — compute should be spent on developer velocity, not GPU setup.

---

## Solution Comparison

| Criteria | Jetson Nano B01 (original VAIC) | Jetson Orin Nano Super | **Raspberry Pi 5 4GB (recommended)** |
|---|---|---|---|
| **YOLO FPS (capstone)** | 30+ (GPU/TensorRT) — overkill | 67 TOPS — extreme overkill | **8-10 FPS CPU** — sufficient |
| **CPU task speed** | Baseline (A57) | ~2× Nano | **~3× Nano (A76)** |
| **Serial bridge** | ✅ identical protocol | ✅ identical protocol | ✅ identical protocol |
| **OS setup time** | 2-4 hrs (SDK Manager, Ubuntu host needed) | 1-2 hrs (SD card but firmware update first) | **10-20 min (Raspberry Pi Imager)** |
| **Python ecosystem** | ❌ Python 3.6, custom wheels | ✅ Python 3.10+ | **✅ Python 3.11, full pip** |
| **Mobile power** | ❌ barrel jack 5V/4A (jumper required) | ❌ DC jack 7-20V (no USB-C bank) | **✅ USB-C 5V/3A power bank** |
| **Thermal (enclosed)** | ⚠️ throttles under GPU load | ⚠️ needs active fan | **✅ passive heatsink sufficient** |
| **Total system cost** | ~$80-150 used + camera | **$430-450** | **$135** |
| **Availability** | EOL (module until Jan 2027) | In stock, high demand/backorders | **In stock** |
| **Camera** | Intel RealSense (~$180) | Intel RealSense (~$180) | **Pi Camera Module 3 ($25)** |
| **Developer complexity** | High | Medium-High | **Low** |
| **Capstone fit** | Poor (EOL, setup cost, power issues) | Poor (cost, power, overkill) | **Excellent** |

---

## Recommendation

**Use the Raspberry Pi 5.** The capstone's suggested architecture is correct. The Pi 5 is not a compromise compared to the Jetson Nano — it is the better choice for these specific workloads.

**Why the VAIC architecture uses Jetson Nano and we don't have to**: The VAIC competition requires real-time autonomous operation with CUDA-accelerated YOLO running at 30+ FPS on 1080p video from a depth camera, with sub-100ms vision-to-motor latency. Our capstone task rate is 0.5–2 Hz. The Pi 5's 8 FPS CPU inference is already faster than our task rate by an order of magnitude.

**When Jetson would become the right call** (future project, not this capstone):
- Local LLM inference on-device (no Claude API) — Orin Nano Super can run LLaVA-7B, Pi 5 cannot
- >30 FPS high-resolution object detection required
- CUDA-dependent libraries (e.g., NVIDIA Isaac ROS, cuSpatial) are mandatory
- Production deployment where thermal reliability across >1 hour matters more than setup speed

### Implementation Outline

No changes required to the current architecture. The research confirms the existing design:

1. `Pi 5 4GB ($110) + Pi Camera Module 3 ($25)` — total hardware $135
2. Flash Pi OS Bookworm (Raspberry Pi Imager, ~10 min)
3. `pip install pyserial apriltag ultralytics` — no CUDA, no TensorRT, no SDK Manager
4. `serial_bridge.py` — identical to the VAIC `V5Comm.py` approach
5. `vision_loop.py` — YOLO11n NCNN (8-10 FPS), `apriltag.detect()` (CPU)
6. `llm_loop.py` — Claude API (network-bound; Pi 5 3× faster than Nano at Python processing)

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| 8 FPS is too slow for a future task | Add Hailo-8L AI HAT+ ($70) → 41 FPS at 640×640 |
| Pi 5 price continues rising | 2GB variant ($65 + $25 camera = $90) is sufficient for pure streaming + inference |
| Local LLM needed (no cloud) | Upgrade path: Jetson Orin Nano Super or Hailo-8L provides NPU path |

---

## Next Steps

- No hardware change needed — Pi 5 is confirmed correct
- Consider: `/wiki-ingest raw/research/jetson-nano-vs-rpi5/index.md` to add this to the knowledge base
- Optional follow-on: `/task-add "Document YOLO11n NCNN benchmarks on Pi 5 with actual timing measurements"` once hardware is available
