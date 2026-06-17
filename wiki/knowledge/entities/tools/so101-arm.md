---
id: so101-arm
title: SO101 Arm
aliases: [SO-101, SO101, SO101 leader/follower]
updated: 2026-06-16
sources:
  - ../../../../raw/research/enpire/index.md
tags: [tool, hardware, robot-arm, teleoperation, lerobot-compatible]
---

# SO101 Arm

relates_to::[[Agentic Physical Autoresearch]]
relates_to::[[Imitation Learning — ACT]]
used_by::[[LeRobot]]

A consumer-accessible 6-DOF robot arm designed for the **leader/follower teleoperation** workflow. The leader arm (worn/driven by human) is physically identical to the follower; joint positions mirror in real time, enabling natural demonstration collection without programming the motion.

## Specification

- 6 degrees of freedom: shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper
- USB serial connection to host computer
- Fully open-source hardware and firmware
- LeRobot v3.0 compatible out of the box
- Approximate price: **~$200–400/arm** (components, open-source BOM)

## Validated Use (Hyperfamila)

Hyperfamila used two SO101 arms (leader + follower) at HackRome 2026:
- Follower: `hackrome_follower_0` via `/dev/tty.usbmodem5A460829821`
- Leader: `hackrome_leader_0` via `/dev/tty.usbmodem5A460824651`
- Custom syringe end-effector with linear actuator (suction 8s full range, empty 4s)
- Training dataset: 400 episodes → 90,620 frames

## End-Effector Customization

The gripper mount is standard and easy to modify. Hyperfamila swapped the gripper for a custom **syringe with vacuum-based actuator** for liquid handling — built in hours. This establishes that wet-lab end effectors are practically feasible without precision machining.

## Relevance

The SO101 is the **recommended hardware starting point** for an ENPIRE-inspired experiment. It is the most battle-tested combination with LeRobot, has public reference implementations (hyperfamila), and hits a price point accessible to individual researchers.
