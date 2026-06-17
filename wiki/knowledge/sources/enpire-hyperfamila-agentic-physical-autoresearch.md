---
id: enpire-hyperfamila-agentic-physical-autoresearch
title: "Research: ENPIRE + Hyperfamila — Agentic Physical Autoresearch"
updated: 2026-06-16
sources:
  - ../../raw/research/enpire/index.md
tags: [robotics, agentic-ai, physical-autoresearch, imitation-learning, capstone-track]
---

# Research: ENPIRE + Hyperfamila — Agentic Physical Autoresearch

relates_to::[[Agentic Physical Autoresearch]]
relates_to::[[Imitation Learning — ACT]]
relates_to::[[Research Graph Infrastructure]]
uses::[[Flywheel]]
uses::[[LeRobot]]
uses::[[SO101 Arm]]

**ENPIRE** (NVIDIA/CMU/Berkeley) identifies the missing abstraction in autonomous robotics research: a **repeatable physical feedback loop** — reset the scene, execute a policy, verify the outcome, refine the next iteration. Once that loop exists, a coding agent can treat robot learning as a software optimization problem. Frontier coding agents running on ENPIRE achieved **99% success rates** on challenging dexterous manipulation tasks (PushT, pin insertion, zip-tie tying, GPU insertion) with no human intervention.

**Hyperfamila** (HackRome 2026, 8 hours) proves the same loop is feasible at hobbyist scale. An SO101 leader/follower arm with a custom syringe end-effector, 400 teleop episodes collected via LeRobot, four ACT policies (~5M params, 100 episodes each) trained on cloud H100s, and OpenAI Codex given full autonomous control via robot tool calls. Paradigma Flywheel managed experimental knowledge. The project won four prizes including best Codex use and a $1k grant. **Full stack is open-source** (code: https://github.com/giacomoran/hyperfamila-hackrome-2026; dataset: https://huggingface.co/datasets/giacomoran/hyperfamila_provette).

**Why this matters for the capstone**: this research anchors a new, wholly independent experiment track — agentic physical autoresearch for scientific discovery (wet lab / AI for Science framing). **It has zero relation to the VEX V5 telemetry project.** The hyperfamila build demonstrates that the hardware, policy training, and agent stack are accessible to a solo developer in hours. A serious version with more careful experiment design, richer task structure, and a knowledge-management loop would be a compelling capstone.

## ENPIRE Architecture

Four-module harness that structures the physical feedback loop for coding agents:

| Module | Role |
|--------|------|
| **EN** (Environment) | Automatic scene reset, safety boundaries, outcome verification, structured logging the agent calls via API |
| **PI** (Policy Improvement) | Agent generates/revises policy code from rewards, video, traces, failure cases; supports heuristic learning, BC, offline/online RL |
| **R** (Rollout) | Runs budgeted robot trials; records state, action, video, result for audit |
| **E** (Evolution) | Compares hypothesis branches; reuses successful recipes; prunes hardware-failed paths |

Fleet scaling tracked via **MRU** (Mean Robot Utilization — fraction of time robot actively runs; decreases as fleet grows) and **MTU** (Mean Token Utilization — LLM throughput; scales ~linearly).

## Hyperfamila Stack

- **Arms**: SO101 leader/follower (teleop collection → autonomous execution)
- **End effector**: custom linear-actuator syringe (suction 8s full range, empty 4s)
- **Cameras**: wrist-mounted + overhead (2 total)
- **Dataset**: 400 episodes / 90,620 frames / 2.15 GB via LeRobot v3.0; AV1 at 30fps
- **Policies**: ACT, ~5M params, batch 64, 10K steps, 100 epochs; one policy per flask target (red/green/blue/output)
- **Agent**: OpenAI Codex with tool calls (`goto_waypoint`, `classify_top_camera`, `eval_flask`, etc.)
- **Knowledge**: Paradigma Flywheel

## Key Design Principles

1. **Reset automation is the hard part** — the loop breaks without reliable reset; liquid handling has natural reset (pipette back)
2. **Vision-based verification** — overhead camera + classifier is sufficient for a success oracle
3. **Minimal tool surface** — `run_policy(name)`, `classify_state()`, `log_result()`, `reset()` is enough to start
4. **One policy per atomic action** — agent composes; policies need not generalize
