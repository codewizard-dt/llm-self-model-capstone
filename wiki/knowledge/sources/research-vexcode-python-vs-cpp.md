---
id: research-vexcode-python-vs-cpp
title: Research: VEXcode V5 Python vs C++ API — Thorough Comparison
updated: 2026-06-20
sources:
  - ../../raw/research/vexcode-python-vs-cpp/index.md
tags: [source, vex, vexcode, python, cpp, api, comparison, micropython]
---

# Research: VEXcode V5 Python vs C++ API — Thorough Comparison

A method-level comparison of the VEXcode V5 Python and C++ APIs, including a complete linked local reference to both doc trees and a runtime/concurrency analysis. Complements derives_from::[[research-vexcode-v5]] by going deeper on the language-pair specifics.

## Core Finding: Functional Parity, Runtime Gap

**Python and C++ are two bindings over one underlying VEX V5 SDK.** Every device — motors, sensors, brain, drivetrain, VEXlink, competition template — is accessible in both languages. The Motor/Motor Group page proves this concretely: the action/mutator/getter method sets are identical in function, only differing in naming convention (`snake_case` Python vs `camelCase` C++) and minor per-page documentation drift.

**Runtime is where they diverge materially.** Python on the Brain is **MicroPython 1.13** (Python 3.4 base), interpreted, with modules `uasyncio, ujson, math, sys, gc, etc.` but **no pip, no CPython C-extensions**. C++ is compiled to native ARM Cortex-A9. General embedded benchmarks put MicroPython ~10–300× slower for compute-heavy/tight loops; the VEX forum confirms PID control is predominantly C++ because Python is too slow and under-documented for it. Both share the **cooperative VEXcode thread scheduler** (not preemptive).

## Complete API Doc Tree (Local Reference)

Home: <https://api.vex.com/v5/home/>

**Python sections** (`https://api.vex.com/v5/home/python/`): Drivetrain, Motion (Motor/MotorGroup/MC55/Motor393/Victor883/Servo), Vision, Screen, Controller, Sensing, Inertial, 3-Wire Devices, Pneumatics, Brain, SD Card, VEXlink, Console, Logic (Threads), 6-Axis Arm, Magnet, Competition, MicroPython Libraries

**C++ sections** (`https://api.vex.com/v5/home/cpp/`): Drivetrain, Motors and Motor Controllers, Controller, Brain, Competition, Smart Port Devices (Inertial/Rotation/Distance/Optical/GPS/AI Vision/Vision), 3-Wire Devices, Console, Logic (Threads), VEXlink, CTE Workcell (6-Axis Arm/Object Sensor/Pneumatics/Signal Tower)

**Key mapping difference:** C++ groups sensors under "Smart Port Devices" and industrial devices under "CTE Workcell"; Python lists each as a top-level page. Same hardware, different filing. There is no Python-only or C++-only *device* — only a Python-only *section* for MicroPython library reference.

## Critical Codebase Contradiction

> **Contradiction:** The prior `vexcode-v5` research (and its wiki summary at [[research-vexcode-v5]]) recommended "VEXcode V5 Python on the V5 Brain for all robot-side code." The codebase at `robot/v5-brain/pros_bridge/src/main.cpp` uses **PROS C++** (`pros/apix.h`, `pros::millis`, `serctl`, `initialize()`/`opcontrol()` PROS lifecycle). This contradicts the Python recommendation. This report argues the PROS C++ choice is correct for real-time/PID and should be recorded as a formal decision rather than left as implicit drift. See [[pros]] and [[vex-coprocessor-pattern]].

## Method-Level Telemetry Fields (confirmed both languages)

Motor getters available in **both** Python and C++: `position`, `velocity`, `current`, `power`, `torque`, `efficiency`, `temperature`. These are the Task Telemetry Contract observed fields.

relates_to::[[vexcode]]  
relates_to::[[pros]]  
relates_to::[[vex-coprocessor-pattern]]  
relates_to::[[task-telemetry-contract]]  
derived_from::[[research-vexcode-v5]]
