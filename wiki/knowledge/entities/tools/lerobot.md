---
id: lerobot
title: LeRobot
aliases: [HuggingFace LeRobot, lerobot]
updated: 2026-06-16
sources:
  - ../../../../raw/research/enpire/index.md
tags: [tool, robotics, imitation-learning, data-collection, policy-training, huggingface]
---

# LeRobot

relates_to::[[Imitation Learning — ACT]]
relates_to::[[Agentic Physical Autoresearch]]
uses::[[SO101 Arm]]

HuggingFace's open-source framework for **robot imitation learning** — data collection via teleoperation, policy training, and deployment. De facto standard for hobbyist and research-scale manipulation as of 2026. Current stable: codebase v3.0.

## What It Provides

- **Leader/follower teleoperation** — plug leader arm into USB, drive follower arm; LeRobot records synchronized joint states + video
- **Multi-camera recording** — wrist-mounted + overhead cameras captured simultaneously; AV1 at 30fps
- **6-DOF joint state + action logging** — shoulder pan/lift, elbow flex, wrist flex/roll, gripper; stored as Parquet
- **HuggingFace dataset integration** — push dataset to HF hub with one command; enables public sharing and reproducibility
- **ACT policy training** — built-in training scripts for Action Chunking with Transformers; batch-size/steps/epochs configurable

## Validated Configuration (Hyperfamila)

- 400 episodes, 90,620 frames, 2.15 GB total
- Wrist camera: 640×480; overhead camera: 480×640
- AV1 codec, 30 fps
- Training: batch 64, 10K steps, 100 epochs → ~5M param policy
- Public dataset: `giacomoran/hyperfamila_provette`

## Hardware Compatibility

Compatible with SO101 leader/follower arms out of the box. Also supports other arms (Koch, Moss, etc.). The SO101 is the best-documented combination for LeRobot v3.0.

## Links

- GitHub: https://github.com/huggingface/lerobot
- HuggingFace Hub: https://huggingface.co/lerobot
