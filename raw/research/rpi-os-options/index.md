---
topic: "Changing the OS setup on the RPi: Bookworm vs Ubuntu 24.04/ROS 2 Jazzy vs Trixie/Hailo"
slug: rpi-os-options
researched: 2026-06-23
sources: [./sources.md]
---

# Research: RPi OS Options for the Capstone

> **Executive summary:** The current Bookworm + PiCam2 + custom Python stack is the only option that is
> *working today* and has zero new hardware dependencies — and the Jun 29 showcase is 6 days out.
> Switching OS this week carries meaningful bringup risk with minimal upside for the capstone demo.
> The best post-showcase upgrade is **Trixie + Hailo AI HAT+** (3× FPS boost, $70, Pi-native stack);
> the best long-term architecture is **Ubuntu 24.04 + ROS 2 Jazzy + OAK-D** (stereo depth, cleanest
> robotics platform, but requires new hardware and building libcamera-family tools from source).

---

## Research Questions

1. What does ROS 2 Jazzy actually give the capstone vs. the current custom Python/C++ pipeline?
2. Does `picamera2` work on Ubuntu 24.04, or is it Raspberry Pi OS–only?
3. What is the real setup complexity of each option on Pi 5 today (2025–2026)?
4. What does an OAK-D add over PiCam2, and what does it cost/require?
5. What is the Trixie + Hailo path — is Hailo now fully supported on Trixie?

---

## Current State (Codebase)

The Pi 5 coprocessor currently runs **Raspberry Pi OS Bookworm (64-bit)**, with:
- `picamera2` pre-installed; Camera Module 3 (CSI ribbon) in use [S6]
- Custom Python pipeline: YOLO11n (~8–10 FPS), AprilTag detection, USB serial JSON to V5 Brain [S6, S7]
- `pyserial` at `/dev/ttyACM0`, 115,200 baud — matches VAIC reference architecture [S7]
- No ROS, no Hailo hardware

All existing code assumes Raspberry Pi OS (libcamera/picamera2 ecosystem).

---

## Key Findings

### F1 — picamera2 is officially Raspberry Pi OS–only [S1]
`picamera2` docs state: *"Picamera2 is only supported on Raspberry Pi OS Bullseye (or later) images."*
Community workarounds for Ubuntu 24.04 require **building libcamera from source** inside a ROS2
workspace — a multi-hour process with reported failures [S2, S3]. This is the single biggest obstacle
for Options 2 and 3: PiCam2 + Ubuntu = significant manual friction.

### F2 — ROS 2 Jazzy + Ubuntu 24.04 works but is not trivial on Pi [S4, S8]
Official binary packages (`ros-jazzy-ros-base`) install cleanly with the right repository config
(`noble-updates` required, not just base `noble` [S8]). Real-world reports show additional steps to
avoid missing dependency errors. A real-time Jazzy image for Pi 5 exists (ros-realtime project) [S9].

### F3 — ROS 2 adds negligible value for this capstone's architecture [S5, S10]
The capstone serial bridge is custom JSON over pyserial. `rosserial_vex_v5` has **no Jazzy package**
(index.ros.org shows "No version for distro jazzy") [S5]. ROS benefits (Nav2, SLAM, TF, multi-robot
coordination) are not needed. The camera pipeline is a single-node Python script. ROS overhead is
real cost with near-zero benefit here.

### F4 — OAK-D eliminates the Ubuntu/libcamera camera headache [S11, S12]
The OAK-D connects via USB and uses the DepthAI SDK — no libcamera/picamera2 dependency.
This makes Ubuntu + ROS 2 + OAK-D the *cleanest* combination: ROS gets a proper driver
(`depthai-ros`), depth data is native, and no custom camera stack is needed.
Trade-offs: OAK-D hardware cost ($79–$249 depending on model), and `depthai-ros` on Jazzy
currently requires building `depthai-core` from source (not yet a binary apt package for Jazzy) [S13].
OAK-D inference latency is 80–100 ms combined, acceptable for manipulation but not high-speed loops [S12].

### F5 — Trixie + Hailo is now fully supported (as of fall 2025) [S14, S15, S16]
Hailo AI HAT+ support was **missing at Trixie launch** (July 2025) but was re-added by the RPi team
in a subsequent update [S14]. Install is `sudo apt install dkms hailo-all` [S15].
AI HAT+ 13 TOPS: **$70**. 26 TOPS: **$110**. AI HAT+ 2 (Hailo-10H, 40 TOPS + 8 GB RAM): **$130** [S16].
picamera2 examples include `hailo/detect.py` for YOLOv8/v11 — fully integrated into the Pi camera stack.
Caution: Trixie ships Python 3.13, which causes compat issues with some packages (Open WebUI requires
Docker; other pip packages may need pins) [S17]. Camera had early Trixie bugs (resolved ~Oct 2025) [S18].

### F6 — Bookworm remains the most stable, best-documented Pi 5 platform [S19, S20]
Multiple sources confirm Bookworm 64-bit as the "recommended default" for Pi 4/5 since Oct 2023.
The VAIC reference architecture (canonical VEX+RPi) was built for Bookworm [S7].
Hailo AI HAT+ also works on Bookworm (the original launch target) — so a Hailo upgrade does NOT
require moving to Trixie.

---

## Constraints

Any solution must account for:
1. **Jun 29 showcase is 6 days away** — zero tolerance for OS bringup failures
2. **Existing Python code** (YOLO, AprilTag, pyserial bridge) is written for picamera2/libcamera
3. **No new hardware in hand** (no OAK-D, no AI HAT+)
4. **VEX V5 serial protocol** is custom JSON — not ROS topics, not micro-ROS
5. **Pi 5 PCIe slot** is available if AI HAT+ is acquired (no M.2 NVMe in use)

---

## Solution Comparison

| Criteria | **Option 1: Bookworm + PiCam2 + Python** | **Option 2: Ubuntu 24.04 + Jazzy + PiCam2** | **Option 3: Ubuntu 24.04 + Jazzy + OAK-D** | **Option 4: Trixie + Hailo + PiCam2** |
|---|---|---|---|---|
| **Setup pain (now)** | None (already running) | High — libcamera from source, Jazzy install steps, python 3.13 compat | Medium — Ubuntu + Jazzy straightforward; OAK-D USB plug-in | Medium — reflash to Trixie, `apt install hailo-all`; requires AI HAT+ hardware |
| **New hardware needed** | No | No | Yes — OAK-D ($79–$249) | Yes — AI HAT+ ($70–$130) |
| **picamera2 / PiCam3 support** | Native, pre-installed | **Not officially supported** (build libcamera from source) | N/A (OAK-D replaces camera) | Native (tight Hailo integration) |
| **FPS (vision)** | ~8–10 FPS (YOLO11n) | ~8–10 FPS (same, if camera works) | ~15–30 FPS (OAK-D onboard VPU offloads Pi) | **~30+ FPS** (Hailo NPU handles YOLO) |
| **VEX V5 serial** | pyserial (working) | pyserial (works on Ubuntu, no rosserial_vex_v5 for Jazzy) | pyserial node in ROS2 (custom, no package) | pyserial (unchanged) |
| **Depth perception** | No | No | **Yes** — stereo depth, 3D object localization | No |
| **ROS 2 ecosystem** | No | Yes — full Jazzy (little benefit here) | Yes — depthai-ros, visualization | No |
| **Showcase risk** | **None** | **High** (camera compat unknown) | **High** (new hw + ROS setup) | **High** (reflash + new hw) |
| **Long-term quality** | Medium (custom, no standards) | High (ROS ecosystem, camera friction) | **Very High** (stereo depth + ROS) | Medium/High (fast inference, no ROS) |
| **Best for** | Jun 29 demo (current) | ROS-first robotics platform | Cleanest production architecture | Pi AI HAT–first design |

---

## Recommendation

### For the Jun 29 showcase: **Stay on Option 1 (Bookworm)**

Do not reflash or change OS this week. The existing stack is working. Any other option introduces
bringup risk that cannot be recovered from in 6 days. The capstone judges are evaluating the
self-model loop, telemetry contracts, and LLM integration — not which camera stack is running.

### Post-showcase upgrade path

**If camera FPS is the bottleneck → Option 4 (Bookworm OR Trixie + Hailo AI HAT+)**
- Keep the existing codebase almost entirely unchanged
- Add AI HAT+ 13 TOPS ($70): `sudo apt install hailo-all` on Bookworm (or Trixie)
- picamera2 `hailo/detect.py` example provides immediate YOLOv8 at 30+ FPS
- Recommended: stay on Bookworm to avoid Python 3.13 compat issues in Trixie

**If architecture matters → Option 3 (Ubuntu 24.04 + ROS 2 Jazzy + OAK-D)**
- Budget 1–2 full days for bringup: Ubuntu flash, Jazzy install, depthai-ros build from source
- OAK-D adds stereo depth → real 3D object localization → richer Task Telemetry Contract gap residuals
- The custom Python serial bridge becomes a thin ROS2 node (no `rosserial_vex_v5` available)
- Recommended model: OAK-D-S2 ($149) or OAK-D-Lite ($79 used)

**Option 2 (Ubuntu + Jazzy + PiCam2) is the weakest choice**: high setup pain, camera compat
is unsupported, and ROS adds no value for this serial-JSON architecture. Avoid.

### Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| AI HAT+ out of stock / slow shipping | Order from official Pi reseller (Adafruit, PiShop, Vilros); in-stock today at ~$70–$110 |
| Trixie Python 3.13 breaks pip packages | Stay on Bookworm for Hailo (Bookworm is the original AI HAT+ launch target) |
| depthai-ros Jazzy build fails | Use Jazzy + OAK-D with plain DepthAI SDK (Python), skip ROS until stable |
| OAK-D stereo depth calibration drift | Run factory calibration on first boot; 30 cm–10 m range is well within workspace |

---

## Next Steps

- **To proceed with Hailo post-showcase**: `/task-add "Install Raspberry Pi AI HAT+ and Hailo on Bookworm — upgrade YOLO pipeline to 30+ FPS"`
- **To proceed with OAK-D architecture**: `/task-add "Migrate Pi coprocessor to Ubuntu 24.04 + ROS 2 Jazzy + OAK-D for stereo depth perception"`
- **No action needed before Jun 29** — Bookworm stack is ready
