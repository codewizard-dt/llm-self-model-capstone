---
id: imitation-learning-act
title: Imitation Learning — ACT (Action Chunking with Transformers)
updated: 2026-06-16
sources:
  - ../../raw/research/enpire/index.md
tags: [robotics, imitation-learning, policy-training, act, lerobot]
---

# Imitation Learning — ACT (Action Chunking with Transformers)

relates_to::[[Agentic Physical Autoresearch]]
uses::[[LeRobot]]

**Imitation learning** trains robot policies from human demonstrations rather than reward functions. The operator teleoperates the robot through desired behaviors; the policy learns to replicate them from sensor observations.

**ACT (Action Chunking with Transformers)** is the dominant policy architecture for manipulation tasks as of 2026. It predicts a *chunk* of actions (a short sequence) rather than one action at a time, which smooths out temporal jitter and enables more reliable manipulation.

## Why ACT for Hobbyist Scale

The hyperfamila project (HackRome 2026) validated ACT at minimal resource cost:
- **~5M parameters** — trains in minutes on a cloud H100 / L40S
- **100 episodes per policy** — sufficient for reliable reaching and positioning
- **Batch size 64, 10K steps, 100 epochs** — a repeatable training recipe
- One policy per atomic action (reach red flask, reach blue flask, etc.); the agent composes policies rather than requiring one monolithic model

## Data Collection with LeRobot

**LeRobot** (HuggingFace, codebase v3.0) is the de facto framework for imitation learning data collection and policy training. It standardizes:
- Leader/follower arm teleoperation for data collection
- Multi-camera recording (wrist + overhead)
- 6-DOF joint state + action logging
- AV1 video at 30fps, Parquet tabular data
- Direct upload to HuggingFace datasets

The hyperfamila dataset (`giacomoran/hyperfamila_provette`) is a public reference: 400 episodes, 90,620 frames, ~2.15 GB.

## Labeling Strategy

Collect a single mixed dataset across all task variants, then split by label post-hoc:
- Record all target-reaching demonstrations in one session
- Label episodes by target after recording
- Split into per-target training sets
- Train one ACT policy per target

This avoids re-setup between recording sessions and produces a clean per-policy dataset.

## Relationship to ENPIRE

In ENPIRE's PI (Policy Improvement) module, behavior cloning is one of several supported regimes alongside heuristic learning and RL. ACT-based BC is the recommended starting point for a hobbyist-scale experiment — it requires no reward function, trains quickly, and generalizes well to manipulation tasks with sufficient demonstrations.
