---
id: agentic-physical-autoresearch
title: Agentic Physical Autoresearch
updated: 2026-06-16
sources:
  - ../../raw/research/enpire/index.md
tags: [robotics, agentic-ai, autonomous-science, physical-feedback-loop]
---

# Agentic Physical Autoresearch

derived_from::[[ENPIRE + Hyperfamila Research]]
relates_to::[[Research Graph Infrastructure]]
relates_to::[[Imitation Learning — ACT]]
uses::[[Flywheel]]
uses::[[LeRobot]]

The idea that a coding agent — given a **repeatable physical feedback loop** — can autonomously conduct real-world robot experiments: proposing hypotheses, executing policies on hardware, verifying outcomes, and iterating without human intervention.

## The Missing Abstraction

ENPIRE (NVIDIA/CMU/Berkeley, 2026) articulates the gap precisely: coding agents can already automate algorithm search in digital environments, but physical robotics research requires something more — a controllable, repeatable loop over the real world. The four ingredients are:

1. **Automatic scene reset** — return hardware to a defined starting state without human touch
2. **Policy execution** — run a candidate policy for a budgeted number of trials
3. **Outcome verification** — compute a success/failure signal without human judgment (camera + classifier is sufficient)
4. **Code refinement** — agent revises policy code based on results, videos, and failure traces

Once these four are in place, the agent treats robot learning as software optimization.

## Scale: Research Lab vs. Hobbyist

| Dimension | ENPIRE (NVIDIA/CMU/Berkeley) | Hyperfamila (HackRome 2026) |
|-----------|------------------------------|------------------------------|
| Hardware | Industrial arms, robot fleet | SO101 consumer arms (~$400) |
| End effector | Standard grippers | Custom syringe (built in hours) |
| Policy method | Heuristic learning, BC, RL | ACT (100 eps, 5M params) |
| Agent | Codex / Claude Code / Kimi | OpenAI Codex |
| Knowledge | Custom metrics (MRU/MTU) | Paradigma Flywheel |
| Build time | Research project | 8 hours at a hackathon |
| Open source | Planned | Yes (GitHub + HuggingFace) |

## "AI for Science" Framing

The most compelling application is **wet lab automation**: an agent autonomously tests hypotheses about liquid handling, mixing, or sample preparation. The syringe end-effector maps directly to pipetting; the overhead camera provides a natural verification oracle; and liquids reset trivially (pipette back). This framing connects agentic physical autoresearch to real scientific discovery rather than just robotics benchmarking.

## Key Design Rules

1. **Reset automation first** — design the task so reset is automatic; this is the rate-limiting step
2. **One policy per atomic action** — train small, specialized policies; the agent composes them
3. **Minimal tool surface** — `run_policy(name)`, `classify_state()`, `log_result()`, `reset()` is a complete starting API
4. **Vision-based oracle** — overhead camera + classifier is sufficient; no need for force sensors or expensive hardware
5. **Log everything from day one** — the Evolution module's value comes from comparing branches; structured logs enable this

## Relationship to This Capstone

This concept anchors the **ENPIRE-inspired experiment track** — a wholly independent direction from the VEX V5 telemetry project. The two tracks share no hardware, code, or design artifacts. See project memory `project-enpire-track.md` for the full separation note.
