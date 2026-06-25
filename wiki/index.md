---
title: Wiki Index
updated: 2026-06-25
---

# Wiki Index — Home Map

The page catalog and home Map of Content for this wiki. **Read this first on every query**, then drill into the linked pages. Updated on every ingest and every filed answer.

Conventions that govern every page (atomic pages, stable IDs, typed links, frontmatter namespace): see [conventions](conventions.md). Operation history: see [log](log.md).

Entry format: `- [Title](path) — one-line summary`.

The wiki is split into two domains with opposite organizing laws:
- **Knowledge** — timeless, link-navigated synthesis (sources, concepts, entities). Pages are listed individually below.
- **Work** — stateful, status-navigated lifecycle artifacts (requirements, decisions, roadmaps, tasks, uat, bugs). Items are **not** listed here — each family keeps its own `index.md` of active items; this page links to those.

---

## Knowledge

### Sources
- [ChatGPT: AI-powered Software Factory](knowledge/sources/chatgpt-ai-powered-software-factory.md) — ChatGPT brainstorm of 5 capstone ideas; recommends Agent Evolution Factory as the strongest pitch
- [Gauntlet Capstone Brief 2026](knowledge/sources/gauntlet-capstone-brief.md) — official brief: 3 directions (ML+LLM, novel agents, multi-approach), planning doc due Jun 17, showcase Jun 29
- [Masterclass: AI Product Engineering (Cohort 5)](knowledge/sources/gauntlet-g5-masterclass-ai-product-engineering.md) — 31-slide deck: execution is commoditized, judgment is the new bottleneck; Shape·Ship·Sync + BrainLift methodology
- [Capstone Proposal Structure](knowledge/sources/capstone-proposal-structure.md) — 7 required sections for Deliverable 01 (due Jun 17); scoring is on ambition not polish; sections 6–7 are the gap to close
- [Feasibility: LEGO Self-Assembling Learning Robots](knowledge/sources/feasibility-lego-self-assembling-robots.md) — LEGO software factory; feasible as staged prototype, not pure-LEGO self-replication; 4 capability tiers
- [Feasibility: Robots Assembling Robots from Modular Blocks](knowledge/sources/feasibility-modular-blocks-robot-assembly.md) — connector choice is decisive; RoFICoM/Cubelets beat LEGO/VEX for autonomous assembly
- [Feasibility: Human-Built Generational Robot Factory](knowledge/sources/feasibility-human-built-generational-factory.md) — "robot designs, human builds, system learns"; typed grammar + 3-stage roadmap (SPIKE→VEX→ROBOTIS)
- [Research: LEGO SPIKE Prime — Functionality & Project Fit](knowledge/sources/research-lego-spike-prime.md) — SPIKE Prime is the right Stage-1 substrate; buy now (retires Jun 30 2026), offload all inference, use PyBricks
- [VEX V5 Classroom Starter Kit (Product Research)](knowledge/sources/vex-v5-classroom-starter-kit.md) — full scrape of 276-7010 kit + per-part dimensions/weights/STEP CAD for all 40+ parts; 30 CAD files ~319 MB in `raw/research/vex-v5-classroom-starter-kit/cad/`
- [VEX V5 Clawbot Build Instructions (276-6009-750 Rev6)](knowledge/sources/vex-v5-clawbot-build-instructions.md) — 41-step official build guide; Gen 0 morphology; 4-motor typed config; seed for Stage-2 parts catalog
- [Research: VEX V5 Grab/Pull/Throw Capability & Quantification](knowledge/sources/vex-v5-customization-grab-pull-throw.md) — grab/pull achievable with base kit; motor API gives torque/current/velocity/position; task telemetry contracts defined
- [Research: VEX V5 Starter Kit Configuration Space](knowledge/sources/vex-v5-starter-kit-configurations.md) — 2 base topologies (Speedbot + Clawbot); ~10–15 valid configs (corrected 2026-06-17: only "200rpm" cartridge, only "front_omni+rear_standard" wheels, no roller end-effector); Speedbot=Gen 0, Clawbot=Gen 1
- [Research: VEXcode V5 — Functionality, Implementation, and Limitations](knowledge/sources/research-vexcode-v5.md) — MicroPython on Xilinx ZYNQ; USB serial user port is the LLM integration path; no pip, no WiFi on Brain; VS Code Extension replaced Pro V5
- [VEX V5 Booster Kit (Product Research)](knowledge/sources/vex-v5-booster-kit.md) — Booster Kit (276-2232, $214.49): ~600 passive parts, 4 new typed primitives (linear_actuator, intake, long_arm, slip_release); recommend pairing with additional Smart Motors
- [PicoBricks REX Evolution vs VEX V5 (Platform Comparison)](knowledge/sources/picobricks-rex-vs-vex-v5.md) — REX ($164.99, ESP32) rejected as V5 alternative: no motor encoders/telemetry → cannot populate Task Telemetry Contract observed block
- [Research: UT Austin VEX U Championship Team](knowledge/sources/ut-vexu-team.md) — GHOST team (9 members, 2 ASE PhD students); Prof. Justin Hart (CS) identified as highest-value outreach — published "Robot Self-Modeling" (2017), now applies LLMs to service robots
- [Research: Justin Hart Self-Modeling Papers & LLM Work](knowledge/sources/justin-hart-self-modeling.md) — Hart's full arc (2010–2017): Nico robot, geometric kinematic self-model via visual self-observation; Dobby (2024) as LLM-robot architecture reference; field gap confirmed
- [Research: Flywheel (Paradigma) — Potential Capstone Applications](knowledge/sources/research-flywheel-paradigma.md) — DAG-based research infrastructure with MCP/Claude Code integration; self-model loop maps 1:1 to its scientific-method pattern; Task Telemetry Contract JSONs = artifacts; hooks enable autonomous closed-loop revision
- [Research: Vision into VEX V5 Architecture (Raspberry Pi + Webcam)](knowledge/sources/vision-vex-architecture.md) — Pi 5 as vision/AI coprocessor over USB serial JSON; YOLO11n ~8–10 FPS; AprilTags for pose localization; extends Task Telemetry Contract with visual observation fields
- [Research: AprilTags — What They Are and How They Fit the Capstone](knowledge/sources/apriltags.md) — fiducial markers for workspace localization; two detection paths (Pi 5 `apriltag` library vs. VEX AI Vision Sensor); extends Task Telemetry Contract with spatial gap residuals `{dx, dy, dtheta}`
- [Research: VEX V5 Clawbot Claw Autonomy](knowledge/sources/vex-v5-clawbot-claw-autonomy.md) — no hardware sensing on the standard claw; official curriculum uses fixed-degree `spin_for()`; no `is_stalled()` API; recommended grab pattern: `set_max_torque` + long `spin_for` + timeout; grab is mechanically trivial but telemetrically rich
- [Research: VEX V5 Advanced Toolchains — VS Code Extension, PROS, LemLib, vexide](knowledge/sources/research-vex-v5-advanced-toolchains.md) — Python single-file in VS Code Extension too; PROS FreeRTOS enables concurrent tasks; pros::Serial opens Smart Ports as RS-485 channels; LemLib adds odometry; Stage 1=VEXcode Python, Stage 2=PROS+LemLib
- [Research: What Is PID Control?](knowledge/sources/pid-control.md) — 3-term feedback loop (P=current error, I=accumulated error, D=rate of change); V5 Smart Motor has its own internal Cortex M0 PID; gap residuals = evidence about unmodeled friction/inertia/load
- [Research: VEX V5 Telemetry Pipeline — Output, Storage, and Transfer](knowledge/sources/vex-v5-telemetry-pipeline.md) — V5→USB serial→Pi JSONL→Claude API; Mode A real-time (1–4s), Mode B batch (50% cost, 24h SLA); SD card fallback; PROS RS-485 Stage 2 at 921,600 baud
- [Research: Raspberry Pi 5 Cost — Especially with Camera Module 3](knowledge/sources/rpi5-camera-module-3-cost.md) — 3 hike rounds since Oct 2025; 4GB now $110 (+83%); Camera Module 3 still $25/$35; board+camera from $70 (1GB) to $135 (4GB); full headless system ~$160
- [Research: Raspberry Pi Complete Kits — Pi 4 vs Pi 5 with Camera Module 3](knowledge/sources/rpi-complete-kits.md) — kit pricing converged ($165 Pi 4 vs $170 Pi 5 4GB); Pi 5 clear winner at +$5–40 premium; Camera Module 3 now ships with both cables; all interfaces compared; recommended procurement $170 kit + $25 camera = $195
- [Addendum: Raspberry Pi 5 Weight & Mobile Power for Robot Use](knowledge/sources/rpi-complete-kits-mobile-power.md) — Pi 5 bare PCB ~47g; full system ~280–350g; actual workload ~3–5W; standard 5V/3A power bank gives 12–15 hours; mount via M2.5 standoffs on rear chassis plate
- [Research: Non-VEX Add-Ons for LLM Robot Self-Expression](knowledge/sources/robot-flair-addons.md) — 5 cost tiers from free (cardboard/foil) to $25 (NeoPixel); EVA foam top $1–5 pick; Coroplast best rigid panel; aesthetic choices encode hypotheses; Pi 5 NeoPixel requires SPI workaround
- [Research: ENPIRE + Hyperfamila — Agentic Physical Autoresearch](knowledge/sources/enpire-hyperfamila-agentic-physical-autoresearch.md) — NVIDIA ENPIRE framework + HackRome 2026 hobbyist proof-of-concept; SO101 + ACT + Codex + Flywheel; anchors independent experiment track (NOT VEX)
- [Research: VEX V5 + RPi Coprocessor Open-Source Repos, Telemetry Feedback & LLM Behavior Modeling](knowledge/sources/vex-v5-rpi-coprocessor-opensource.md) — 13 repos catalogued; RPi5+V5 combination is novel; VAIC_24_25 is the canonical reference; zero LLM+VEX V5 projects exist; USB serial at 115200 baud confirmed path
- [Research: Jetson Nano / JetPack vs Raspberry Pi 5 for the Capstone Architecture](knowledge/sources/jetson-nano-vs-rpi5.md) — Pi 5 confirmed correct vs Jetson Nano (EOL) and Orin Nano Super ($430+): 3× CPU advantage, USB-C power bank compatible, 10-min setup, $135 total system cost
- [Research: Raspberry Pi 5 Low Voltage Warning — Real Consequences & All Fixes](knowledge/sources/rpi5-low-voltage-warning.md) — warning is two distinct alerts (PD miss vs. actual voltage sag); USB 600mA cap irrelevant at capstone load; free config.txt fixes; 52Pi not required
- [Research: VEX V5 CAD Designs — Starter Kit Builds, Purchasable Expansions & 3D-Printable Parts](knowledge/sources/vex-v5-cad-designs.md) — CMFDesign TinkerCAD (conceptual, 869 remixes); GrabCAD SolidWorks (61 files, engineering-grade); Onshape 100+ part library (free); 4 Starter Kit builds; full official build map; 3D print spec: 0.500"/1/8" sq shaft; three-tier expansion strategy
- [Research: Connecting to a Raspberry Pi 5 from an M5 Mac (CanaKit, Headless)](knowledge/sources/rpi5-mac-connection.md) — CanaKit SD has SSH disabled by default; re-flash with Pi Imager (Bookworm, not Trixie) + SSH+WiFi → `ssh user@mypi.local`; Bluetooth peripherals unusable before network access; add Raspberry Pi Connect for browser-based GUI
- [Research: 3D Printer File Formats](knowledge/sources/3d-printer-file-formats.md) — two-file-type model (model files + G-code); STL universal standard; 3MF modern standard (2015 consortium); slicer is mandatory bridge; STEP preferred for engineering CAD; format-by-printer-technology table
- [Research: VEX Rubber Bands #32 and #64 — Sizes, Materials, and Robotics Uses](knowledge/sources/vex-rubber-band-sizes.md) — Alliance industry size codes decoded; #32=3"×1/8" (precision), #64=3.5"×1/4" (power/grip); 3 material variants; VRC legal sizes; passive-energy use cases
- [Research: VEX V5 Minimum Parts for a Launch-Disc Configuration](knowledge/sources/vex-launch-disc-parts.md) — 3 minimum SKUs: 276-5842 (6:1 cartridge), 217-6449 (3" 60A flex wheel), 217-7947 (VersaHex adapters); adds `launch_disc` to the morphology vocabulary as exclusive arm-motor swap
- [Research: VEX V5 Minimal Structural Parts for a Flywheel Setup](knowledge/sources/vex-flywheel-structure-parts.md) — structural companion to vex-launch-disc-parts; 3 purchase lines (276-3521 HS bearing, 276-6102 HS collar, 276-3440 2" HS shaft); arm C-channels reused; standoff sandwich trick avoids drilling
- [Research: Flywheel Arm Retrofit](knowledge/sources/flywheel-arm-retrofit.md) — fixed-arm variant: mechanically brace the old arm, bolt on adapter plates, then mount a standoff-spaced flywheel cassette with two-sided shaft support
- [Research: VEX V5 Flywheel Indexer Mechanisms](knowledge/sources/vex-flywheel-indexer.md) — holds piece in staging, fires on command; 1-motor flywheel frees claw motor → roller indexer, zero new parts; 2-motor flywheel → ratchet (Motor Clutch 276-1098) or 5th motor
- [VEX Smart Motor, High Strength Shaft, and Flywheel Fit](knowledge/sources/vex-smart-motor-hs-shaft-flywheel.md) — correction for the foam golf ball launcher: V5 motor accepts HS shaft, but HS shaft does not pass through normal plate holes; first prototype should use the compression wheel kit's 1/8" shaft adapter path
- [VEX Order and Known Build Inventory, 2026-06-25](knowledge/sources/vex-order-2026-06-25.md) — ordered flywheel/scoop parts and current known inventory constraint: no spare U- or C-channels; use plates, spacers, and measured perforated steel
- [Home Depot Supplemental Build Inventory, 2026-06-25](knowledge/sources/home-depot-inventory-2026-06-25.md) — confirmed Simpson strap plates, Everbilt nylon spacers, zip ties, Velcro straps, and very soft foam balls for the scoop/flywheel prototypes
- [Flywheel Recut Plan for Two VEX 5x15 Steel Plates](knowledge/sources/flywheel-plate-recut-plan.md) — two best cross-cut layouts for the VEX 5x15 plates: recommended 5x8+5x7 hole-grid cassette and alternate 5x10+5x5 hole-grid cassette; labels are VEX hole counts, not inches
- [Research: VEXcode V5 Python vs C++ API — Thorough Comparison](knowledge/sources/research-vexcode-python-vs-cpp.md) — Python/C++ functionally equivalent bindings; MicroPython ~10–300× slower for tight loops; codebase uses PROS C++ (contradicts prior Python-on-Brain recommendation); full linked doc-tree reference
- [Research: V5 Brain Program — Python vs PROS C++ (Both Sides)](knowledge/sources/v5-brain-python-vs-pros.md) — thin-executor architecture already settled; VEXcode Python stdin receiving unconfirmed; PROS C++ bidirectional serial community-confirmed; LemLib out of scope; 10-line empirical test resolves the question on first bringup
- [Research: V5 User Programs — Why They're Mandatory and How Simple They Can Be](knowledge/sources/v5-user-programs.md) — RPi cannot bypass user program (proprietary RS-485, inert user port); no competition infrastructure needed; minimum Brain program is ~50–100 lines; upload once, tap slot to run
- [Research: PROS CLI Workflow + The Exact Brain-Side C++ Bridge Program](knowledge/sources/pros-cli-brain-bridge.md) — 4-command CLI workflow; two-FreeRTOS-task architecture (receive + watchdog); move_velocity() API; ArduinoJson for JSON parsing; `pros terminal` conflicts with Pi's pyserial; full reference program with Clawbot port map; **updated 2026-06-25**: Pi-hosted upload confirmed (pure-Python wheel, ARM64 OK)
- [Research: PROS CLI on ARM64 Linux (Raspberry Pi 5)](knowledge/sources/pros-cli-arm64-pi.md) — pure-Python wheel installs on aarch64; pros upload decoupled from ARM toolchain; `--slot 7/8` flag; Pi (`vexy`) confirmed aarch64/Python 3.12.3; uv sync install path; RUNBOOK §8 added
- [Research: VEX V5 3-Wire Port Spec — Connector, Pinout, and Servo Compatibility](knowledge/sources/vex-3wire-port-spec.md) — 2.54 mm keyed male-pin port; GND→+5V→Signal pin order; 5 V @ 2 A shared; JR-style RC servos plug directly in; `Servo` or `pwm_out` API
- [Research: Clawbot Claw → Household Scoop Replacement](knowledge/sources/clawbot-scoop-replacement.md) — claw+motor detaches via 2 screws; 1" bracket gap; plastic serving spoon is best replacement; drill 2× 11/64" holes, reuse original screws; ~5 min, zero new hardware; frees one Smart Motor; adds `passive_scoop` morphology type
- [Research: AprilTag Larger Workspace & Map Format](knowledge/sources/apriltag-larger-workspace-map.md) — corrects 80cm arena to 150×200cm; 200mm tags for 1.5m range; checkpoint re-fix + dead-reckoning pattern; 2D JSON map format; VEXY_MAP multi-arena support
- [Research: Game Object Selection — Graspability, Scoopability, Launchability](knowledge/sources/game-object-selection.md) — racquetball (57 mm, ~40 g, hollow rubber) recommended; only object that fits claw + scoop + flywheel simultaneously; compression rule: ~10% of diameter; foam ball runner-up
- [Research: Task Contract Redesign — Single "Score" Task](knowledge/sources/task-contract-score-redesign.md) — replaces grab/pull/throw with one ScoreContract; fitness = distance_from_bin_m; motor contract layer unchanged; only 2 code files change
- [Research — RPi OS Options for the Capstone (+ Addendum)](knowledge/sources/rpi-os-options.md) — four OS/stack options compared; Ubuntu 24.04 + Jazzy camera path confirmed (RPi libcamera fork, 85–90% success); Hailo AI HAT+ ($70) = lowest-risk FPS upgrade; ROS 2 gains: yolo_ros, apriltag_ros, foxglove, ros2 bag→Claude API; stay on Bookworm for Jun 29
- [Research: Robot AprilTag Ball Delivery](knowledge/sources/robot-apriltag-ball-delivery.md) — implementation workflow for `vexy_deliver_ball`: scan, approach ball tag 1, approach bin tag 0, then bounded release command

### Concepts
- [Agent Evolution Factory](knowledge/concepts/agent-evolution-factory.md) — evolving AI-agent architectures via ML+LLM; the recommended capstone pitch
- [AI-Powered Software Factory](knowledge/concepts/ai-software-factory.md) — virtual engineering org of specialized agents; humans only approve or reject
- [The Judgment Bottleneck](knowledge/concepts/judgment-bottleneck.md) — AI commoditized execution; judgment is the new binding constraint
- [AI Product Engineer](knowledge/concepts/ai-product-engineer.md) — the defining 2026 role; owns the outcome, not the code
- [Shape · Ship · Sync](knowledge/concepts/shape-ship-sync.md) — Lenny's three-jobs operating framework for product engineers
- [BrainLift (DOK 1–4)](knowledge/concepts/brainlift.md) — Facts → Knowledge Tree → Insights → Spiky POVs; the research methodology + assignment
- [Persona vs. ICP](knowledge/concepts/persona-vs-icp.md) — who uses the product vs. who pays; conflating them ships a product nobody buys
- [Physical-Robot Software Factory](knowledge/concepts/physical-robot-software-factory.md) — CI/CD pipeline of versioned robot artifacts; the hardware sibling of the Agent Evolution Factory
- [Typed Assembly Grammar](knowledge/concepts/typed-assembly-grammar.md) — morphology search over typed modules, not free-form CAD; what makes the concept implementable
- [VEX V5 Motor Gear Cartridges](knowledge/concepts/vex-v5-motor-cartridges.md) — 6:1/18:1/36:1 swappable cartridges (276-4840); 6:1 (600 RPM) is the add-on for flywheel/launcher throws; 36:1 for high-torque lift; 18:1 default for drive
- [The Reality Gap](knowledge/concepts/reality-gap.md) — sim-to-real mismatch; the dominant technical risk for physical robot factories
- [Connector-First Hardware](knowledge/concepts/connector-first-hardware.md) — blind-mate power+data connectors (RoFICoM/Cubelets) collapse the hardest assembly steps
- [Human-in-the-Loop Replication](knowledge/concepts/human-in-the-loop-replication.md) — "robot designs, human builds, system learns" — the realistic near-term framing
- [LLM-Authored Robot Self-Model](knowledge/concepts/llm-authored-self-model.md) — THE PRIMARY IDEA: LLM authors a structured self-description from finite parts; multi-LLM critics attack it; reality corrects it; Lipson lineage but language-grounded
- [Task Telemetry Contract](knowledge/concepts/task-telemetry-contract.md) — predicted + observed + gap JSON per task primitive; the machine-readable gap model feed; grabs/pulls/throws produce numeric residuals the LLM reads to revise the self-model
- [PID Control](knowledge/concepts/pid-control.md) — u(t) = Kp·e + Ki·∫e + Kd·(de/dt); V5 motor has hardware inner PID; LemLib outer PID for trajectory; gap residuals = friction/inertia/load evidence
- [Research Graph Infrastructure](knowledge/concepts/research-graph-infrastructure.md) — DAG of evidence-backed hypothesis nodes as the substrate for autonomous research; self-model loop and generational lineage map directly onto this pattern
- [Aesthetic Vocabulary](knowledge/concepts/aesthetic-vocabulary.md) — non-functional grammar extension for LLM visual self-expression; body panels, surface markings, appendages, accent lighting; aesthetic choices encode hypotheses; free–$25 material tiers
- [Agentic Physical Autoresearch](knowledge/concepts/agentic-physical-autoresearch.md) — coding agent + repeatable physical feedback loop (reset → execute → verify → refine) on real hardware; ENPIRE at research scale, hyperfamila at hobbyist scale
- [Imitation Learning — ACT](knowledge/concepts/imitation-learning-act.md) — train robot policies from teleop demos; ACT (Action Chunking with Transformers) at 100 eps / 5M params via LeRobot; proven at hackathon scale
- [VEX Coprocessor Pattern](knowledge/concepts/vex-coprocessor-pattern.md) — V5 Brain + external Linux host over USB serial/RS-485; fixed command grammar now includes bounded `release` as the Brain-side drop primitive
- [Raspberry Pi 5 USB PD Power](knowledge/concepts/rpi5-usb-pd-power.md) — Pi 5 PD negotiation behavior: two-alert distinction (PD miss vs. voltage sag), free config.txt fixes, hardware alternatives to 52Pi board
- [3D Printing File Formats](knowledge/concepts/3d-printing-file-formats.md) — STL (universal, no color), 3MF (modern standard, color+metadata), STEP (engineering B-Rep), IGES (legacy); G-code is the machine instruction output, not a model format
- [Slicer Workflow](knowledge/concepts/slicer-workflow.md) — mandatory three-stage pipeline: model file → slicer software → G-code → printer; slicer configures layer height, infill, supports, temperatures; resin and FDM slicers are not interchangeable
- [Rubber Band Mechanisms (Passive Elastic Energy)](knowledge/concepts/rubber-band-mechanisms.md) — #32 for precision (triggers/latches/springs), #64 for power (lift assist/catapult/intake rollers); silicone for grip; ~30% motor-load reduction from counterbalancing; "free energy" in VEX community
- [Camera Module 3 — Setup, Packages, and Verification](knowledge/concepts/camera-module-3-setup.md) — cable connection, OS enablement, picamera2/YOLO/AprilTag package installs, and verification scripts for Pi 5 + Camera Module 3
- [Simulation & Prediction — What's Spec'd vs. What's Missing](knowledge/concepts/simulation-prediction-gap.md) — prediction schemas are solid (contract formulas + PID gap table); simulation step is a named placeholder with no tool, pipeline, or prompt design
- [VEX Flywheel Disc Launcher](knowledge/concepts/vex-flywheel-disc-launcher.md) — single/double flywheel mechanism; `launch_disc` morphology primitive; minimum 3 SKUs; 276-8402 ball bearings halve current draw; exclusive arm-motor swap on Clawbot
- [Fixed-Arm Flywheel Retrofit](knowledge/concepts/fixed-arm-flywheel-retrofit.md) — stationary-arm mounting pattern: brace the old arm as a tower, add adapter plates, and bolt on a removable flywheel cassette
- [VEX Flywheel Indexer](knowledge/concepts/vex-flywheel-indexer.md) — holds game piece in staging then fires on command; motor budget determines type (roller vs ratchet vs pneumatic); 1-motor flywheel enables zero-purchase roller indexer via freed claw motor
- [Scoop and Flywheel Build Diagrams](knowledge/concepts/scoop-and-flywheel-build-diagrams.md) — exploded and assembled line drawings for the inventory-aware scoop clamp adapter, flywheel plate-and-spacer frame, and 5x15 VEX plate recut cassettes
- [PROS Dependency & Build Compatibility](knowledge/concepts/pros-dependency-compatibility.md) — rules for adding ANY PROS library on this Brain: pin kernel-4.x, build as monolith (`USE_PACKAGE:=0`); hot/cold split is silently broken (program runs but display + serial no-op)
- [VEX V5 3-Wire Servo Port](knowledge/concepts/vex-v5-3wire-servo.md) — 2.54 mm keyed connector; GND·+5V·Signal pinout; 5 V @ 2 A shared; JR RC servos direct-fit; no encoder feedback (use Smart Motors for telemetered axes)
- [AprilTag Workspace Layout for Manipulation Tasks](knowledge/concepts/apriltag-workspace-layout.md) — **updated** 150×200cm arena, 200mm tags; executable delivery flow now uses staging tag 1 and bin tag 0
- [Robot Workspace Map (Multi-Arena JSON Format)](knowledge/concepts/robot-workspace-map.md) — 2D JSON map schema; active maps now live under `robot/ros2-runtime/config/maps/`; delivery defaults depend on bin/staging roles
- [Game Object Selection](knowledge/concepts/game-object-selection.md) — multi-criteria framework for choosing a game piece compatible with claw + scoop + flywheel; racquetball (57 mm) is GEN-0 default; compression rule ~10% of diameter; 55–65 mm intersection window
- [RPi Coprocessor OS Options](knowledge/concepts/rpi-coprocessor-os-options.md) — four-option decision matrix (Bookworm/Ubuntu/Trixie × PiCam2/OAK-D/Hailo); Ubuntu + Jazzy camera path confirmed via libcamera fork; VEX serial always custom pyserial; sequenced upgrade path post-Jun-29

### Entities
- People — [knowledge/entities/people/](knowledge/entities/people/)
  - [Cat Wu](knowledge/entities/people/cat-wu.md) — Head of Product, Anthropic; case study for the AI Product Engineer role
  - [Lenny Rachitsky](knowledge/entities/people/lenny-rachitsky.md) — product thought-leader; source of the Shape·Ship·Sync framework
  - [Teresa Torres](knowledge/entities/people/teresa-torres.md) — continuous-discovery coach; one interview/week practice
  - [Hod Lipson](knowledge/entities/people/hod-lipson.md) — foundational evolutionary-robotics researcher (GOLEM, self-reproducing machines)
  - [Brian Scassellati](knowledge/entities/people/brian-scassellati.md) — Hart's PhD advisor; Yale Social Robotics Lab; developmental robotics lineage behind the self-modeling concept
  - [Justin Hart](knowledge/entities/people/justin-hart.md) — UT Austin CS; published "Robot Self-Modeling" (2017); now applies LLMs to service robots; **highest-priority outreach contact** (hart@cs.utexas.edu)
  - [Karmanyaah Malhotra](knowledge/entities/people/karmanyaah-malhotra.md) — lead programmer, UT GHOST VEX U team (CS '27); GitHub: karmanyaahm
  - [Melissa Cruz](knowledge/entities/people/melissa-cruz.md) — ASE PhD, UT GHOST VEX U team; hardware-access outreach target
  - [Maxx Wilson](knowledge/entities/people/maxx-wilson.md) — ASE PhD, UT GHOST VEX U team; hardware-access outreach target
  - [Francesco Pappone](knowledge/entities/people/francesco-pappone.md) — CEO/co-founder of Paradigma; built Flywheel; published "The New Age of Research" (March 2026); X: @tensorqt
  - [Jim Fan](knowledge/entities/people/jim-fan.md) — NVIDIA Director of AI; co-lead GEAR Lab + GR00T; equal advisor on ENPIRE; prior work: Voyager, Eureka, MineDojo
  - [Giacomo Rancurel](knowledge/entities/people/giacomo-rancurel.md) — lead developer of hyperfamila (HackRome 2026); GitHub: giacomoran; X: @ludocomito; potential collaborator
- Organisations — [knowledge/entities/organisations/](knowledge/entities/organisations/)
  - [Gauntlet](knowledge/entities/organisations/gauntlet.md) — intensive AI engineering program; sets capstone evaluation criteria
  - [Anthropic](knowledge/entities/organisations/anthropic.md) — AI lab; headline case study for engineers owning product outcomes
  - [UT Austin IEEE Robotics and Automation Society](knowledge/entities/organisations/ut-ieee-ras.md) — student org; GHOST VEX U team (2025 world champions); outreach target for VEX V5 hardware access
  - [Paradigma](knowledge/entities/organisations/paradigma.md) — startup building "infrastructure for autonomous research"; product is Flywheel
  - [NVIDIA GEAR Lab](knowledge/entities/organisations/nvidia-gear-lab.md) — Generalist Embodied Agent Research; co-led by Jim Fan; produced ENPIRE, GR00T, Voyager
- Tools — [knowledge/entities/tools/](knowledge/entities/tools/)
  - [ChatGPT](knowledge/entities/tools/chatgpt.md) — used for capstone brainstorming; also a benchmark target in Option 4
  - [LEGO Education SPIKE Prime](knowledge/entities/tools/lego-spike-prime.md) — recommended Stage-1 robot-factory platform; app-mediated, offload autonomy
  - [VEX V5](knowledge/entities/tools/vex-v5.md) — recommended Stage-2 platform; deterministic mechanics, native AI Vision Sensor
  - [VEXcode](knowledge/entities/tools/vexcode.md) — VEX programming environment; scales Blocks → Python → C++; free
  - [VEX STEM Labs](knowledge/entities/tools/stem-labs.md) — free standards-aligned VEX curriculum; CMU Robotics Academy co-designed
  - [RoFI / RoFICoM](knowledge/entities/tools/roficom.md) — open genderless blind-mate connector; the connector-first exemplar
  - [BrickLink Studio](knowledge/entities/tools/bricklink-studio.md) — LEGO CAD/instruction/BOM tool; the factory's instruction layer
  - [Pybricks](knowledge/entities/tools/pybricks.md) — open-source alt firmware for SPIKE Prime; recommended Python integration path (survives SPIKE App retirement)
  - [Raspberry Pi Build HAT](knowledge/entities/tools/raspberry-pi-build-hat.md) — 4-port LPF2 HAT; alternative onboard-Pi integration path for SPIKE Prime
  - [LEGO Education Computer Science & AI Kit](knowledge/entities/tools/lego-cs-ai-kit.md) — SPIKE successor (ships Apr 2026); classroom curriculum tool, NOT a research-platform replacement
  - [VEX V5 Speedbot / TrainingBot](knowledge/entities/tools/speedbot.md) — simplest Starter Kit config (2-motor drive only); Gen 0 for the capstone self-model loop; Clawbot is its extension
  - [PicoBricks REX Evolution 8in1](knowledge/entities/tools/picobricks-rex-evolution.md) — ESP32 consumer kit; evaluated as cheaper V5 alternative and rejected (no motor telemetry)
  - [Tamiya TAM71201 Microcomputer Robot](knowledge/entities/tools/tamiya-tam71201.md) — micro:bit crawler kit; evaluated as a V5 alternative and rejected (no telemetry, mobility-only)
  - [Thames & Kosmos Robotics Workshop (THK620401)](knowledge/entities/tools/thames-kosmos-robotics-workshop.md) — micro:bit 248-piece kit; most flexible alternative but rejected (no actuator feedback)
  - [Flywheel](knowledge/entities/tools/flywheel.md) — DAG-based autonomous research infrastructure (Paradigma, beta March 2026); MCP-native; recommended substrate for the self-model evolution audit trail
  - [Raspberry Pi 5](knowledge/entities/tools/raspberry-pi-5.md) — AI/vision coprocessor for VEX V5 robot; runs OpenCV + YOLO11n + AprilTags + LLM; connects to V5 via USB serial JSON
  - [Raspberry Pi Camera Module 3](knowledge/entities/tools/pi-camera-module-3.md) — 12MP Sony IMX708, PDAF autofocus, 75°/120° FOV, 1080p50, $25; CSI ribbon to Pi 5; recommended camera upgrade over USB webcam
  - [AprilTag Library](knowledge/entities/tools/apriltag-library.md) — pip-installable Python wrapper (University of Michigan, ICRA 2011); `detector.detect(gray_frame)` → tag ID + 3D pose; workspace indoor GPS using tag36h11 printed tags
  - [PROS (Purdue Robotics OS)](knowledge/entities/tools/pros.md) — open-source FreeRTOS-based C/C++ OS for VEX V5; preemptive scheduling; pros::Serial opens Smart Ports as RS-485 coprocessor channels
  - [LemLib](knowledge/entities/tools/lemlib.md) — PROS template adding odometry (x/y/heading), PID, pure pursuit; enables pose-level telemetry for richer self-model gap residuals
  - [vexide](knowledge/entities/tools/vexide.md) — Rust async runtime for VEX V5; compile-time safety + QEMU simulation; deferred for capstone demo (Rust learning curve)
  - [WS2812B NeoPixel LED Strip](knowledge/entities/tools/ws2812b-neopixel.md) — individually addressable RGB LEDs, 5V, $8–15/1m strip; Pi 5 requires SPI method (GPIO 10) or Arduino Nano co-controller; highest visual-impact flair option
  - [LeRobot](knowledge/entities/tools/lerobot.md) — HuggingFace imitation learning framework; leader/follower teleoperation + ACT training + HF dataset publishing; used in hyperfamila
  - [SO101 Arm](knowledge/entities/tools/so101-arm.md) — consumer 6-DOF leader/follower arm; LeRobot-native; ~$200–400/arm; validated in hyperfamila with syringe end-effector
  - [VEX AI Competition (VAIC) Reference Architecture](knowledge/entities/tools/vaic-reference-architecture.md) — official VEX open-source V5+Jetson coprocessor repos (VAIC_23_24, VAIC_24_25); V5Comm.py serial class; directly portable to RPi5
  - [Onshape](knowledge/entities/tools/onshape.md) — cloud-native CAD; free education account; VEX V5 Parts Library with 100+ parts, 500k+ placements; best tool for building Hero Bot / custom robot assemblies from VEX STEP geometry
  - [NVIDIA Jetson Nano](knowledge/entities/tools/jetson-nano.md) — VAIC reference coprocessor; EOL (dev kit discontinued); replaced by Pi 5 in capstone; serial protocol identical (/dev/ttyACM0, 115200 baud)
  - [NVIDIA Jetson Orin Nano Super](knowledge/entities/tools/jetson-orin-nano-super.md) — current Jetson entry-level ($249); 67 TOPS; rejected for capstone (7-20V DC power, $430+ total, overkill for 8-FPS tasks)
  - [NVIDIA JetPack SDK](knowledge/entities/tools/nvidia-jetpack.md) — mandatory Jetson OS stack; Ubuntu 18.04 + Python 3.6 (Nano/JetPack 4.6); 2-4hr setup; library compatibility friction
  - [ROS 2 Jazzy Jalisco](knowledge/entities/tools/ros2-jazzy.md) — ROS 2 LTS for Ubuntu 24.04; Camera Module 3 works via RPi libcamera fork build; `yolo_ros`, `apriltag_ros`, `foxglove_bridge`, `ros2 bag` all apt-installable; VEX serial is always custom pyserial node
  - [Raspberry Pi AI HAT+](knowledge/entities/tools/hailo-ai-hat.md) — Hailo-8L (13 TOPS, $70) / Hailo-8 (26 TOPS, $110) / Hailo-10H (40 TOPS, $130); works on Bookworm + Trixie; `sudo apt install hailo-all`; 30+ FPS YOLO; lowest-risk post-showcase FPS upgrade
  - [Luxonis OAK-D](knowledge/entities/tools/oak-d.md) — spatial AI camera; stereo depth + 4 TOPS onboard VPU; USB interface (no libcamera); $79–$249; best long-term architecture for 3D object localization
  - [Foxglove Studio](knowledge/entities/tools/foxglove-studio.md) — web-based ROS 2 visualization; `foxglove_bridge` apt on Jazzy; debug bounding boxes + poses in browser from any machine; invaluable for headless Pi demos
- Components — [knowledge/entities/components/](knowledge/entities/components/) (this project's own modules, services, scripts)
  - [localizer.py](knowledge/entities/components/localizer.md) — planned Pi-side module: load_map, update_from_tag, update_from_odometry, get_vector_to_waypoint; bridges workspace map config and runtime pose state
  - [vexy_ros ROS 2 Runtime](knowledge/entities/components/vexy-ros-runtime.md) — current ROS 2 Jazzy Pi runtime: camera, AprilTags, scene map, task planning, bounded local skills, `vexy_deliver_ball`, V5 bridge, and proof export

---

## Work

Each family's `index.md` lists its **active items only** (completed/terminal items drop off the list; files never move — status lives in frontmatter).

- **Requirements** — REQ-NNN. [Active index](work/requirements/index.md) · [lifecycle](work/requirements/lifecycle.md)
- **Decisions** — DEC-NNNN (per-decision `#DM`). [Active index](work/decisions/index.md) · [lifecycle](work/decisions/lifecycle.md)
- **Roadmaps** — ROADMAP-NNN. [Active index](work/roadmaps/index.md) · [lifecycle](work/roadmaps/lifecycle.md)
- **Tasks** — TASK-NNN. [Active index](work/tasks/index.md) · [lifecycle](work/tasks/lifecycle.md)
- **UAT** — UAT-NNN, one per task. [Active index](work/uat/index.md) · [lifecycle](work/uat/lifecycle.md)
- **Bugs** — BUG-NNNN. [Active index](work/bugs/index.md) · [lifecycle](work/bugs/lifecycle.md)
