---
topic: Deep dive into Prof. Justin Hart's robot self-modeling papers, citations, and LLM-in-robotics work as a direct predecessor to the capstone's primary concept
slug: justin-hart-self-modeling
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Justin Hart — Robot Self-Modeling Papers, Citations & LLM Work

> Hart's body of work is the **single closest academic predecessor** to the capstone's primary concept, but with a critical architectural difference: Hart's robots build self-models *from sensory data bottom-up* (the robot watches its own arm move); the capstone proposes an LLM *authors* the self-model *top-down from a typed parts catalog*, then reality corrects it. That gap is the novelty claim. Hart's 2024 Dobby paper shows exactly the LLM-as-agent architecture the capstone needs — but applied to conversation, not self-modeling. **The pitch to Hart writes itself**: "we extend your self-modeling lineage with LLM authoring and apply your Dobby architecture to the self-model revision loop."

---

## Research Questions

1. What exactly is Hart's robot self-model method — how is it constructed and how does it update from experience?
2. How do the 2011 ecological self, 2012 mirror perspective-taking, and 2017 journal paper relate to each other?
3. What is Hart's 2024 GPT-4/Dobby architecture, and how does it map onto the capstone's design?
4. Who has cited Hart's self-modeling work, and what is the current field consensus?
5. What precisely is the gap between Hart's work and the capstone's novelty claim?

---

## Current State (Codebase / Wiki Context)

- `wiki/knowledge/concepts/llm-authored-self-model.md` — primary capstone concept; Hart's 2017 paper added to lineage during the prior ingest
- `wiki/knowledge/entities/people/justin-hart.md` — entity page created; outreach contact at hart@cs.utexas.edu
- Prior research (`raw/research/ut-vexu-team/index.md`) identified Hart as the highest-priority outreach contact

---

## Key Findings

### 1. Hart's Self-Modeling Lineage — Complete Arc [S1][S2][S3]

Hart spent his entire PhD (Yale, completed 2014) on robot self-modeling. The arc:

| Year | Paper | Venue | Key Contribution |
|------|-------|-------|-----------------|
| 2010 | "Robotic Self-Models Inspired by Human Development" | AAAI Workshop | Theoretical framing from developmental psychology |
| 2011 | "Robotic Models of Self" | MIT Press book chapter (Metareasoning) | Taxonomy of robot self-model types |
| 2011 | "A Robotic Model of the Ecological Self" | IEEE-RAS HUMANOIDS | Robot as ecologically situated agent; Gibson's affordance theory applied |
| 2012 | "Mirror Perspective-Taking with a Humanoid Robot" | AAAI | Self-as-seen-from-outside; perspective simulation |
| 2014 | "Robot Self-Modeling" | PhD thesis, Yale | Full system on Nico (infant humanoid): visual self-observation → geometric self-model |
| 2014 | "Robotic Self-Modeling" | Book chapter (The Computer After Me, Imperial College Press) | Accessible summary |
| 2015 | "Self-Awareness and Social Competencies" | AMD Newsletter | Connection to social HRI |
| 2017 | "Robot Self-Modeling" | International Journal of Humanoid Robotics | Peer-reviewed journal publication of thesis work |

### 2. The 2014/2017 Self-Modeling Method — What It Actually Does [S2]

**Robot**: Nico — an infant-scale upper-torso humanoid with arms, cameras, and proprioceptive sensors. Built at Yale's Social Robotics Lab (Scassellati lab).

**Method**: The robot builds a **geometric (kinematic) self-model** through **visual self-observation**:
1. Robot moves its own limbs through a motion sequence
2. Cameras observe where the limb ends up (proprioception + vision fusion)
3. System infers the geometric model (joint angles, link lengths, kinematic chain) that explains the observed positions
4. Result: a calibrated inverse kinematics model — the robot learns the shape of its own body

**Key properties**:
- **Numerical/geometric**, not language-grounded
- **Data-driven** from motor babbling + visual feedback (bottom-up)
- **Self-correcting** when body changes (e.g., an arm is removed or altered)
- Updates from **sensory residuals** — analogous to the capstone's task telemetry gap

**What it does NOT do**:
- Does not author a self-model from a parts catalog
- Does not use language or symbolic representations
- Does not have a multi-agent critic panel
- Does not connect the self-model to task performance residuals in a structured way

### 3. The Ecological Self (2011) — The Philosophical Foundation [S3]

Hart's 2011 paper frames the self as a **relational entity**: the robot doesn't just model its body geometry — it models itself *in relation to the environment*. Grounded in James Gibson's **ecological psychology** (affordances), the robot understands what it **can do** in a given environment, not just what it **is** geometrically.

This is directly analogous to the capstone's **capability self-model layer** — not just "I have a claw motor" but "I can grab objects ≤42N stall force in a 0.3m reach envelope." The ecological self is a capability model, not just a structural one.

### 4. Dobby (2024) — Hart's LLM Architecture [S4]

**Paper**: "Dobby: A Conversational Service Robot Driven by GPT-4" (RO-MAN 2024, with Stark, Chun, Stone, et al.)

**Architecture** (directly applicable to the capstone):

```
User utterance
  → Audio transcription
  → GPT-4 (gpt-4-0613 with function calling)
       System: history buffer (all prior messages + state updates)
       Functions: ExecutePlan(), CancelPlan(), navigation actions (10 landmarks)
  → GPT-4 output: free-form text action plan
  → Semantic embedding (cosine similarity) → predefined Action Classes
       (each Action Class: textual title + pre/post-conditions + executable function)
  → Greedy plan validator (checks preconditions/postconditions, reorders if needed)
  → Sequential action execution (non-blocking → conversation continues during execution)
  → State updates written back to history buffer
```

**Hardware**: Segway RMP (mobility) + LIDAR + pre-built lab map. No face.

**Results** (22 participants, within-subjects):
- Interaction time: **14.3 min** (Dobby) vs **5.8 min** (scripted)
- Destinations visited: **5.27** vs **3.00**
- Personality rating: **5.88/7** vs **2.09/7**
- Enjoyment: **6.59/7** vs **4.00/7**
- All 22 preferred Dobby

**Limitations noted**: response latency, audio transcription errors, occasional hallucination.

### 5. Mapping Dobby → Capstone Architecture [S4]

The Dobby architecture maps cleanly onto the capstone's LLM self-model loop with one addition:

| Dobby Component | Capstone Analog |
|----------------|-----------------|
| GPT-4 agent | LLM Generator (authors/revises self-model) |
| History buffer | Self-model document (structural + capability + predictive layers) |
| Action Classes with pre/post-conditions | Typed assembly grammar primitives with physical specs |
| Semantic embedding matcher | Self-model revision validator (does this update make physical sense?) |
| Environmental state updates | Task telemetry contract residuals (gap JSON) |
| Plan validator | Multi-LLM Critic panel (attacks model before build) |
| Non-blocking execution | Physical build (human executes) while LLM continues to analyze |

The gap: Dobby has no self-model — the LLM reasons about the world but not about the robot's own body/capabilities. Adding the **self-model document** as the persistent shared artifact that the LLM both reads and revises is the capstone's contribution.

### 6. Citation Context — Where Hart's Work Sits in 2024-2026 [S5][S6][S7]

The robot self-modeling field has moved in two directions since 2017:

**Numerical/learned self-models** (Lipson lineage continuation):
- Kwiatkowski & Lipson (2019, Science Robotics) — deep learning self-model from random motion
- arXiv 2111.06389 — "Full-Body Visual Self-Modeling of Robot Morphologies" (visual neural field approach)
- arXiv 2503.05398 (2025) — "Learning High-Fidelity Robot Self-Model with Articulated 3D Gaussian Splatting"
- arXiv 2209.02010 — "On the Origins of Self-Modeling" — quantifies when self-modeling adds value (R²=0.90 with robot complexity)

**LLM+Robotics** (separate track, no self-modeling):
- Dobby (Hart 2024) — LLM agent for conversation + navigation, no self-model
- RoboMorph (arXiv 2407.08626, 2024) — LLM generates robot *designs* (morphology), not self-models
- SAS-Prompt (ICRA 2025) — LLM optimizes *controllers*, no morphology self-model

**The gap that persists**: No paper combines (a) LLM authoring + (b) structured language-readable self-model + (c) multi-agent critique + (d) reality correction via telemetry residuals. This is still the capstone's unclaimed territory.

### 7. Brian Scassellati — Hart's PhD Advisor [S1]

**Prof. Brian Scassellati** (Yale, Social Robotics Lab) co-authored all of Hart's self-modeling work. He is one of the most cited researchers in social robotics and robot self-awareness. Hart's self-modeling work is squarely in the Scassellati lab's tradition of developmental robotics — robots that learn about themselves and others the way infants do.

---

## Constraints

- Hart's self-model is geometric/kinematic (learns body shape from motion), not semantic/language (authored from a parts catalog) — the methods are architecturally different
- The Dobby architecture uses GPT-4 function calling → predefined action classes; the capstone needs the self-model *document* as the persistent state, not just a history buffer
- Hart's work is on service robots in structured environments (labs, homes), not modular robot factories — the domain is different but the concept transfers

---

## Recommendation

**Outreach pitch to Prof. Hart** (hart@cs.utexas.edu):

> "Prof. Hart — I'm a student at Gauntlet AI building a capstone that extends your robot self-modeling lineage into the LLM era. Your 2014/2017 work grounds self-models in sensory observation; we're exploring whether an LLM can *author* a language-readable self-model top-down from a typed parts catalog (VEX V5), and whether a multi-LLM critic panel can replace expensive failed physical trials. Your Dobby architecture is our design reference for the LLM-to-robot interface. Would you have 20 minutes to tell us what we're missing? Our showcase demo is June 29."

**Why Hart will respond**: the capstone is a genuine extension of his work, not a vague "AI robot" pitch. Citing the specific 2017 paper and the Dobby paper shows you've read his work. The "what are we missing?" framing is academically respectful and non-threatening.

**Implementation note**: The Dobby architecture (GPT-4 + function calling + action classes + history buffer) is the correct starting pattern for the LLM-robot interface. Extend it by:
1. Making the history buffer → a structured self-model document (the persistent artifact)
2. Adding the critic LLM that challenges the self-model before each build
3. Replacing Dobby's navigation action classes with VEX V5 motor telemetry contracts

---

## Next Steps

- Email Prof. Hart using the pitch above — this week (before the Jun 29 showcase)
- Read the Dobby paper (arXiv:2310.06303) in full for architectural details — the semantic-embedding action-matching pattern is directly reusable
- Consider citing Hart 2017 + Dobby 2024 explicitly in the capstone proposal (due Jun 17) — demonstrates field awareness
- `/task-add Draft capstone outreach email to Prof. Justin Hart (hart@cs.utexas.edu) citing 2017 self-modeling paper and Dobby`
- `/wiki-ingest raw/research/justin-hart-self-modeling/index.md` to update the knowledge base
