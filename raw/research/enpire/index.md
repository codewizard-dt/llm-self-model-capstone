---
topic: ENPIRE — Agentic Robot Policy Self-Improvement; hyperfamila as hobbyist reference; inspiration for independent experiment track
slug: enpire
researched: 2026-06-16
sources: [./sources.md]
---

# Research: ENPIRE + Hyperfamila — Agentic Physical Autoresearch

> ENPIRE (NVIDIA/CMU/Berkeley) closes the physical robot-learning loop autonomously: coding agents reset scenes, execute policies, verify outcomes, and iterate — on real hardware, no human in the loop. The hyperfamila project (HackRome 2026) is the hobbyist-scale proof of concept: an SO101 arm with a syringe end-effector, four ACT policies trained on 100 episodes each, and OpenAI Codex given full autonomous control over the arm for lab experimentation. This research documents both as **inspiration for a wholly independent experiment track** with zero relation to the VEX V5 telemetry project.

---

## Research Questions

1. What is ENPIRE's architecture and what problem does it solve?
2. How does the physical feedback loop work end-to-end?
3. What did the hyperfamila hackathon prove is feasible at small scale in 8 hours?
4. What hardware, policy training method, and agent stack did hyperfamila use?
5. What would a serious, extended experiment in this spirit look like?

---

## Current State (Codebase)

No existing codebase relevance — this is a greenfield experimental concept. Nothing in the capstone repository relates to robotics policy learning or agentic physical autoresearch.

---

## Key Findings

### The Core Problem ENPIRE Solves [S1]

Coding agents can already generate code to automate algorithm search, but their successes have been confined to digital environments. The missing abstraction for autonomous robotics research is a **repeatable physical feedback loop**: reset the scene → execute a policy → verify the outcome → refine the next iteration.

ENPIRE provides this loop as a structured harness framework.

### ENPIRE Architecture: Four Modules [S1, S2]

| Module | Name | Role |
|--------|------|------|
| **EN** | Environment | Automatic scene reset, safety boundaries, outcome verification, structured logging the agent can call via API |
| **PI** | Policy Improvement | Agent generates/revises policy code from rewards, video, traces, failure cases; supports heuristic learning, BC, offline/online RL |
| **R** | Rollout | Runs budgeted robot trials; records state, action, video, result for audit |
| **E** | Evolution | Compares hypothesis branches across agents; reuses successful recipes; prunes paths that fail on hardware |

### ENPIRE Results [S1, S2]

Frontier coding agents achieved **99% success rates** on real-world dexterous manipulation:
- **PushT** — push object from random start into T-shaped target
- **Pin Insertion** — organize pins into a pin box
- **Zip-tie tying** — align strap with head using cutter
- **GPU Insertion** — insert GPU from arbitrary table position

### AutoEnvBench — Agent Comparison [S1, S2]

Benchmark tracks *agent-driven research progress over wall-clock time* (not just final success). Evaluated:

| Agent | Backbone | Domain |
|-------|----------|--------|
| Codex | GPT-5.5 | Push-T (heuristic learning) |
| Claude Code | Opus 4.7 | Pin Insertion (gradient-based) |
| Kimi Code | Kimi K2.6 | Both tasks |

Fleet scaling: 1, 4, and 8 agent teams tested. Larger teams reach success faster; efficiency tracked via:
- **MRU (Mean Robot Utilization)** — fraction of time robot is actively running (decreases as fleet grows; agents spend more time reasoning)
- **MTU (Mean Token Utilization)** — LLM token throughput; scales ~linearly with fleet size

Technical integration: SAM3 (perception) + cuRobo (planning) + YAM arm (control).

Open-source release is planned [S2].

---

### Hyperfamila — The Hobbyist Reference Implementation [S3, S4, S5, S6]

HackRome 2026 hackathon. **8 hours of work. 4 prizes.**

#### Framing
"We're entering the era of AI for Science. In 2026, we trust our agents to do almost anything in software, but to unlock real-world experimentation in fields like bio and med, we need to close the loop with the physical world."

#### Hardware [S4, S5]
- **Robot**: SO101 arms in **leader/follower setup** (teleop for data collection, follower for autonomous execution)
  - Follower: `hackrome_follower_0` via `/dev/tty.usbmodem5A460829821`
  - Leader: `hackrome_leader_0` via `/dev/tty.usbmodem5A460824651`
- **Cameras**: wrist-mounted (index 0) + overhead (index 1)
- **End effector**: custom linear actuator syringe with vacuum-based gripper
  - Suction: full range in 8 seconds
  - Emptying: full range in 4 seconds
- **Compute**: Remote H100 / L40S instances via SSH for training

#### Dataset [S5, S6]
- Framework: **LeRobot** (codebase v3.0)
- Single mixed dataset `hyperfamila_provette`: **400 episodes, ~90,620 frames** (~2.15 GB)
- Format: Parquet + AV1 video at 30 fps
- 6-DOF joint states + actions (shoulder pan/lift, elbow flex, wrist flex/roll, gripper)
- Episodes labeled by target container after recording, then split into 4 policy training sets:

| Episodes | Target |
|----------|--------|
| 0–49, 200–249 | Red flask |
| 50–99, 350–399 | Green flask |
| 100–149, 300–349 | Blue flask |
| 150–199, 250–299 | Output flask |

#### Policy Training [S3, S5]
- **Method**: ACT (Action Chunking with Transformers)
- **Model size**: ~5M parameters
- **Training**: batch size 64, 10K steps, 100 epochs per policy
- **Sample count**: 100 episodes per policy — sufficient for reliable manipulation
- Four specialized policies, one per flask:
  - `hyperfamila_redflask_bs64_10K_100ep`
  - `hyperfamila_blueflask_bs64_10K_100ep`
  - `hyperfamila_greenflask_bs64_10K_100ep`
  - `hyperfamila_outputflask_bs64_10K_100ep`
- Each policy learns to position the syringe within its designated container from arbitrary start positions

#### Agent Stack [S3, S5]
- **Agent**: OpenAI Codex given full autonomous control of the robot arm
- **Knowledge platform**: Paradigma Inc. Flywheel for managing experimental knowledge
- **Agent tools** (inferred from repo structure):
  - `goto_waypoint.py` — move arm to named waypoint
  - `capture_waypoint.py` — record current position as waypoint
  - `classify_top_camera.py` — vision classification from overhead camera
  - `log_policy_input.py` — log state for policy
  - `processor_act_patched.py` / `processor_act_smooth.py` — ACT inference wrappers
  - `eval_flask.py` — flask-level evaluation
- **Flow**: Codex agent creates hypotheses → calls robot tools → ARM executes policy → result verified → Flywheel stores findings

#### Awards [S3]
- OpenAI: **Best use of Codex**
- Paradigma Inc.: **Best use of Flywheel**
- UnitdVentures: **$1k grant**
- Apeira: **Best demo**

#### Repo / Data
- Code: https://github.com/giacomoran/hyperfamila-hackrome-2026
- Dataset: https://huggingface.co/datasets/giacomoran/hyperfamila_provette

---

## Constraints

Any experiment inspired by this work must account for:

1. **Reset automation is the hard part** — both ENPIRE and hyperfamila rely on tasks where reset is either automatic or trivially fast (liquid can be pipetted back; object positions can be randomized by the agent)
2. **Hardware cost** — SO101 arm kits are consumer-accessible; the syringe end effector was custom-built in hours
3. **Training compute** — 100-episode ACT policies train on H100 in minutes; this is accessible via cloud instances; 5M-param models are fast
4. **Verification oracle** — the agent needs a computable success signal; vision-based (overhead camera + classification) worked for hyperfamila
5. **Agent tool interface** — the robot must expose named tool calls (goto_waypoint, run_policy, classify) that the coding agent can invoke; this is the key software layer
6. **Safety** — unattended physical operation requires position limits, speed limits, and a kill switch

---

## Recommendation

**The hyperfamila project proves the full loop is feasible in 8 hours with accessible hardware and a small team.** The key decisions for a serious version:

### Hardware
- **SO101 leader/follower** is the validated choice — used by hyperfamila, open-source, ~$200–400/arm
- **Syringe end effector** for liquid handling is the natural fit for "AI for Science" framing (biology/chemistry)
- **Two cameras** (wrist + overhead) provide complementary views without requiring depth sensors

### Policy Training
- **ACT** (Action Chunking with Transformers) is proven at 100 episodes / 5M params — start here
- **LeRobot** is the de facto framework (HuggingFace, codebase v3.0)
- Train one policy per atomic action (reach flask A, reach flask B, etc.); the agent composes them

### Agent Layer
- **Claude Code** or **Codex** as the orchestrating agent with robot tool calls
- Minimal tool surface: `run_policy(name)`, `classify_state()`, `log_result()`, `reset()` is enough to start
- **Flywheel** (Paradigma) or any structured knowledge store for tracking hypotheses and results

### Experiment Domain
- **Wet lab automation** is the most compelling application — agent autonomously tests hypotheses about liquid handling, mixing, or sample preparation
- Alternatively: **materials science** (small-scale synthesis trials), **plant biology** (watering/dosing experiments), or **chemistry titration**

### Scale-up Path
1. One arm, one task, one agent (validate the loop)
2. Multiple tasks, agent composes policies
3. Multiple arms / fleet scaling (ENPIRE-style MRU/MTU tracking)

**This is a radical departure from the VEX V5 telemetry track** — different hardware, different domain, different methodology, different goals. No shared infrastructure.

---

## Next Steps

- `/task-add` — Design the ENPIRE-inspired experiment: hardware procurement (SO101), task definition, reset mechanism, success criterion, agent tool API
- `/decision-create` — Experiment domain choice (wet lab vs. other physical science domain)
- Study the hyperfamila repo in detail: `agent/goto_waypoint.py`, `agent/classify_top_camera.py`, `eval_flask.py` — these are the reference implementations for the agent tool layer
- Consider reaching out to @ludocomito / @giacomoran — they open-sourced everything and may collaborate
