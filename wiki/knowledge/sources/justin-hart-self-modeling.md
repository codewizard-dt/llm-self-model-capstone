---
id: justin-hart-self-modeling
title: Research — Justin Hart Self-Modeling Papers & LLM Work
updated: 2026-06-16
sources:
  - ../../raw/research/justin-hart-self-modeling/index.md
tags: [source, research, self-modeling, llm, robotics, hart, academic]
---

# Research: Justin Hart — Self-Modeling Papers & LLM Work

Research conducted 2026-06-16. Deep dive into relates_to::[[justin-hart]]'s complete publication arc on robot self-modeling (2010–2017) and his current LLM-in-robotics work (Dobby, 2024), establishing how his work is the closest academic predecessor to the [[llm-authored-self-model]] concept and where the novelty gap lies.

derived_from::[[justin-hart]]

## Self-Modeling Arc (2010–2017)

Hart's entire PhD at Yale (completed 2014, advisor relates_to::[[brian-scassellati]]) focused on robot self-modeling. The progression:

**2010–2011** — Theoretical foundation: developmental psychology framing ("Robotic Self-Models Inspired by Human Development"), taxonomy of self-model types (MIT Press book chapter), and the **ecological self** (IEEE-RAS HUMANOIDS 2011, grounded in Gibson's affordance theory — the robot models what it *can do* in a given environment, not just its geometry). **The ecological self directly maps to the capstone's capability self-model layer.**

**2012–2014** — Implementation: mirror perspective-taking (AAAI 2012) and the full PhD thesis system on **Nico** (an infant-scale upper-torso humanoid at Yale's Social Robotics Lab). **Nico's method**: moves its limbs through a motion sequence; cameras observe where the limb lands; the system infers the geometric model (joint angles, link lengths, kinematic chain) that best explains the observed positions. Result: a calibrated inverse kinematics model — the robot learns the shape of its own body from sensory experience.

**2017** — Journal publication of the thesis work in *International Journal of Humanoid Robotics*.

**Critical architectural properties** of Hart's method: **numerical/geometric**, not language-grounded; **bottom-up** from motor babbling + vision; self-correcting when body changes; updates from sensory residuals (analogous to the capstone's task telemetry gap).

## Dobby (2024) — LLM-Robot Architecture Reference

Hart co-authored **"Dobby: A Conversational Service Robot Driven by GPT-4"** (RO-MAN 2024). This is the most directly applicable paper for the capstone's LLM-robot interface design.

**Architecture**: GPT-4 (gpt-4-0613 with function calling) → free-form text plan → cosine-similarity semantic embedding matches plan to predefined **Action Classes** (each has title, pre/post-conditions, executable function) → greedy plan validator → non-blocking sequential execution. A **history buffer** accumulates all messages and state updates and is sent with every API call.

**Results** (22 participants, within-subjects): 14.3 min interaction vs 5.8 min scripted; 5.27 destinations vs 3.00; enjoyment 6.59/7 vs 4.00/7. All 22 preferred Dobby. Hardware: Segway RMP + LIDAR. Limitations: response latency, audio transcription errors, hallucination.

## The Capstone Gap

**The gap that justifies the capstone's novelty claim**: Dobby has no self-model (LLM reasons about the world but not the robot's own body/capabilities); Hart's self-models have no LLM authoring or multi-agent critique. No published paper combines (a) LLM authoring + (b) language-readable self-model + (c) multi-agent critique + (d) reality correction via telemetry residuals.

**Dobby → capstone mapping**: history buffer → structured self-model document; Action Classes → typed assembly grammar primitives; environmental state updates → task telemetry contract residuals; plan validator → multi-LLM critic panel.

## Recommended Outreach Pitch

> "Prof. Hart — I'm building a capstone that extends your robot self-modeling lineage into the LLM era. Your 2014/2017 work grounds self-models in sensory observation; we're exploring whether an LLM can *author* a language-readable self-model top-down from a typed parts catalog (VEX V5), and whether a multi-LLM critic panel can replace expensive failed physical trials. Your Dobby architecture is our design reference for the LLM-to-robot interface. Would you have 20 minutes? Our showcase demo is June 29."

relates_to::[[llm-authored-self-model]]  
relates_to::[[physical-robot-software-factory]]  
relates_to::[[task-telemetry-contract]]
