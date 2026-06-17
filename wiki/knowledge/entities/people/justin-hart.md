---
id: justin-hart
title: Justin Hart
aliases: [Justin W. Hart, Prof. Hart]
updated: 2026-06-16
sources:
  - ../../../raw/research/ut-vexu-team/index.md
tags: [person, ut-austin, robotics, self-modeling, llm, outreach]
---

# Justin Hart

**Assistant Professor of Practice**, Department of Computer Science, University of Texas at Austin.  
**Email**: hart@cs.utexas.edu | **Phone**: (512) 998-1757  
**Lab**: Living with Robots Laboratory (LWR Lab)

## Why This Person Matters for the Capstone

Hart is the **highest-priority outreach contact** in all of UT Austin for this project. His published expertise is a near-exact match for the capstone's primary concept:

- **"Robot Self-Modeling"** (2017, with Brian Scassellati) — the direct academic predecessor to the [[llm-authored-self-model]] idea. Published at IEEE-RAS.
- **"A Robotic Model of the Ecological Self"** (2011, IEEE-RAS International Conference on Humanoid Robots, Bled, Slovenia)
- **LLMs and foundation models in robotics** — current active research thread; applies language models to service robot autonomy
- **Semantic mapping, autonomous human-robot interaction, service robots** — research domain

He co-directs the **"Living and Working with Robots" project** under UT Good Systems, and collaborates on the **RoboCup@Home team** (service robots in home environments — the closest analog to the capstone scenario).

## Self-Modeling Method (2014/2017) — What It Actually Does

**Robot**: Nico — infant-scale upper-torso humanoid at Yale's Social Robotics Lab (advisor: relates_to::[[brian-scassellati]]).

**Method**: visual self-observation → geometric kinematic model. The robot moves its limbs through a motion sequence; cameras observe where the limb ends up; the system infers the joint angles, link lengths, and kinematic chain that best explains the observations. Result: a calibrated inverse kinematics model — the robot learns the shape of its own body. **Numerical/geometric**, not language-grounded; bottom-up from motor babbling + vision.

**Ecological Self (2011)**: Hart's earlier paper frames the self as a *relational* entity via Gibson's affordance theory — the robot models what it *can do* in a given environment, not just what it *is* geometrically. This is the direct predecessor to the capstone's capability self-model layer ("I can grab objects ≤42N stall force in a 0.3m reach envelope").

**Critical gap vs capstone**: Hart's self-model is built by the robot from sensory data. The capstone proposes an LLM *authors* the self-model top-down from a typed parts catalog, then reality corrects it. Different architecture; the gap is the novelty claim.

## Dobby (2024) — LLM Architecture Reference

Paper: "Dobby: A Conversational Service Robot Driven by GPT-4" (RO-MAN 2024, with Stark, Chun, Stone, et al.). arXiv:2310.06303.

Architecture: GPT-4 (gpt-4-0613 with function calling) → cosine-similarity embedding matches free-form LLM output to predefined **Action Classes** (each: title + pre/post-conditions + executable function) → greedy plan validator → non-blocking execution. A **history buffer** accumulates all messages and state updates sent with every API call. Hardware: Segway RMP + LIDAR.

Results (22 participants): 14.3 min interaction vs 5.8 min scripted; all 22 preferred Dobby.

**Capstone mapping**: history buffer → structured self-model document; Action Classes → typed assembly grammar primitives; state updates → task telemetry contract residuals; plan validator → multi-LLM critic panel.

## Recommended Pitch

> "We're building a capstone system where an LLM authors and iteratively revises a structured self-model of a VEX V5 robot — your 2017 *Robot Self-Modeling* paper is a direct predecessor. Would you have 30 minutes to discuss our approach, or could a grad student observe our June 29 demo?"

A UT professor with exact expertise lending credibility to the concept is worth more than any hardware shortcut.

relates_to::[[llm-authored-self-model]]  
affiliated_with::[[ut-ieee-ras]]
