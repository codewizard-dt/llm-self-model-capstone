---
topic: what's meant by a "policy" when it comes to training robots and how it applies specifically to this capstone
slug: robot-policy
researched: 2026-06-18
sources: [./sources.md]
---

# Research: What Is a "Policy" in Robot Training — and How Does It Apply to This Capstone?

> A **policy** is the robot's decision function: given what it currently observes, it outputs what action to take next. Policies can be hand-coded rules (classical control), learned from trial-and-error (reinforcement learning), or learned from human demonstrations (imitation learning). The VEX capstone does **not** train a neural policy — it iterates a *self-model*, which is a structured description of the robot's body and capabilities. The V5 Brain runs a classical deterministic policy (VEXcode Python); the LLM's job is to revise the self-model across generations, not to act in real time. The ENPIRE/SO101 experiment track (separate from VEX) is where ACT neural policies are trained.

---

## Research Questions

1. What is a policy, formally and intuitively?
2. What are the main paradigms for producing robot policies (classical, RL, imitation learning)?
3. What does "training a policy" mean in practice?
4. Where do LLMs fit in the policy landscape?
5. Where does this capstone sit — is it training a policy at all, and if so, what kind?

---

## Current State (Codebase / Wiki)

From `wiki/knowledge/concepts/imitation-learning-act.md` and `wiki/knowledge/concepts/llm-authored-self-model.md`:

- The wiki already has a solid ACT/imitation-learning concept page that defines "robot policies from human demonstrations" — but only in the context of the ENPIRE/hyperfamila track (SO101 arm, LeRobot, HackRome 2026).
- The VEX V5 capstone track is described in terms of a **self-model loop**: LLM authors a JSON self-description → critics attack it → human builds → V5 runs task → telemetry feeds gap residuals → LLM revises self-model.
- The `ARCHITECTURE.md` uses the word "policy" nowhere. The V5 brain runs `brain_main.py` on a 20 ms tick driving four Smart Motors — classical deterministic control.

The wiki **does not** have a concept page explaining the policy spectrum or where the capstone's approach sits on it. This is the gap the research fills.

---

## Key Findings

### 1. Policy = observation → action mapping [S1, S2]

Formally, a policy π is a function from the current state (or observation) to an action:
- Deterministic: `π(s) = a` — same state always produces the same action
- Stochastic: `π(a | s)` — outputs a probability distribution over actions

In plain terms: the policy is the robot's **rulebook for what to do right now**, given what it currently sees/senses.

### 2. Three major paradigms [S1, S3, S4]

| Paradigm | How the policy is produced | Robot example |
|---|---|---|
| **Classical control** | Hand-coded by engineer | PID motor controller, `spin_for()` in VEXcode |
| **Reinforcement learning (RL)** | Learned by trial-and-error with a reward signal | Robot learning to walk by trying millions of random movements and keeping what works |
| **Imitation learning (IL)** | Learned from human demonstrations (behavior cloning) | Teleop a robot arm 100× → train ACT → robot replicates the task |

The V5 Smart Motor has a **hardware PID** inside its cartridge — a classical policy running at the actuator level [S6]. VEXcode's `spin_for()` is the outer classical policy the Brain runs per task.

### 3. "Training a policy" means optimizing the function [S3, S5]

In RL, the policy is usually a neural network. Training means adjusting the network's weights so the cumulative reward increases. You need:
- A reward signal (what counts as success)
- Many rollouts (real or simulated)
- A learning algorithm (PPO, SAC, etc.)

In imitation learning (ACT, behavior cloning), training is supervised: the network learns to output the same action the human demonstrated for a given observation. No reward function needed, but you need ~100 demonstration episodes [S5].

### 4. LLMs in the policy landscape [S7, S8]

LLMs entered robotics in two roles:
- **High-level planners**: decompose a language instruction ("pick up the red cup") into a sequence of motor primitives, which a lower-level classical or learned policy executes.
- **Vision-Language-Action (VLA) models**: the cutting edge (NVIDIA GR00T N1, Figure Helix, Google Gemini Robotics 2025). LLM/VLM handles perception + reasoning; a sensorimotor head executes at control frequency. Still outputs an action sequence — still a policy.

The capstone does not implement either of these.

### 5. The capstone's relationship to "policy" [S6, inference — no direct primary source]

The capstone operates at a **different abstraction level** than policy training:

| Layer | What runs | Policy type |
|---|---|---|
| Actuator (V5 Smart Motor cartridge) | Hardware PID | Classical, fixed |
| Brain tick (20 ms VEXcode Python) | `spin_for()`, `set_max_torque()`, task state machine | Classical, deterministic |
| LLM generational loop (operator + Claude Code) | Reads gap residuals → revises self-model JSON | Not a policy at all — this is **model revision** |

The LLM is not acting as a policy in the capstone. It is acting as a **model builder** — authoring and revising a structured representation of the robot's physical capabilities. This is philosophically closer to *model-based control* (maintaining a world/self model to plan with) than to policy learning.

The closest analogy: in model-based RL, a world model is learned, and then a policy is derived from it. The capstone iterates the model but leaves the execution policy fixed (classical VEXcode control). The novel claim is that iterating the *self-model* (not the policy weights) across physical generations produces compounding improvement.

---

## Constraints

- The VEX V5 Brain runs MicroPython with no pip, no WiFi, no GPU. Real-time neural policy inference on-brain is infeasible at capstone scale.
- The operator uses Claude Code subscription — no API billing per call, no scripted HTTP. LLM inference is interactive and asynchronous (not on the robot's control loop).
- Demo deadline: June 29. Scope is 2–3 generational iterations, not a full policy training pipeline.
- The ACT/imitation learning policy approach is scoped to the **separate** ENPIRE/SO101 experiment track (not the VEX capstone).

---

## Recommendation

**Use "policy" precisely, not loosely**, in presentations and documentation:

1. The V5 brain runs a **classical control policy** (VEXcode Python task programs). Name it that way. It is not trained — it is written.
2. The LLM loop is **not policy training** — it is **iterative self-model authoring + gap-residual-driven model revision**. Calling it "policy training" would mislead reviewers; the accurate term is closer to *model-based design iteration*.
3. If asked "why don't you train a neural policy?" — the answer is clean: neural policy training requires reward functions, many rollouts, and compute the V5/Pi5 stack cannot support at capstone scale. The capstone's contribution is that language-grounded self-modeling + real telemetry feedback can substitute for policy training at the *morphology/design* level.
4. The word "policy" does legitimately appear in the ENPIRE/hyperfamila track: ACT trains a behavioral cloning policy from teleop demonstrations. That's correct usage.

---

## Next Steps

- Run `/wiki-ingest raw/research/robot-policy/index.md` to create a `wiki/knowledge/concepts/robot-policy.md` concept page that anchors the policy spectrum and the capstone's position on it.
- Consider `/task-add` to update `ARCHITECTURE.md` with a one-paragraph "What this is not" section clarifying the capstone is model-iteration, not policy training — useful for the June 29 showcase Q&A.
- The `wiki/knowledge/concepts/imitation-learning-act.md` page could add a cross-link to the new policy concept page to clarify which track uses ACT.
