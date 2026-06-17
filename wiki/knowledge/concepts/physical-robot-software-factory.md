---
id: physical-robot-software-factory
title: Physical-Robot Software Factory
aliases: [Robot Software Factory, Generational Robot Factory]
updated: 2026-06-15
sources:
  - ../../raw/Feasibility of a Software Factory for LEGO-Based Self-Assembling Learning Robots.pdf
  - ../../raw/Feasibility of a Software-Factory Approach to Learning Robots That Assemble Additional Robots from M.pdf
  - ../../raw/Feasibility of a Human-Built Generational Robot Software Factory.pdf
tags: [concept, robotics, software-factory, pipeline, capstone-idea]
---

# Physical-Robot Software Factory

The unifying concept across the three feasibility reports: a **CI/CD-style pipeline that treats a physical robot's design, build instructions, learned skills, simulation scenes, and safety checks as versioned build artifacts** — automatically tested and regenerated whenever the design changes. It is the *physical-hardware sibling* of the [[agent-evolution-factory]] (which evolves software agent architectures).

## Why It's "Not Optional"

All three reports independently conclude the software-factory model is **mandatory**, not a nice-to-have — it is the only way to keep a self-improving robot system under control. Without versioned artifacts and automated regeneration, a design change silently invalidates the build instructions, sim models, and calibration, and the learning loop is poisoned.

## Canonical Layered Architecture

1. **Design** — typed part catalog, normalized BOM, submodels, assembly graph (see [[typed-assembly-grammar]])
2. **Instruction** — auto-generated build steps, pick lists, fixture recipes
3. **Simulation** — geometry/kinematics + contact-rich validation (digital twin); generic rigid-body sim is *not enough* (see [[reality-gap]])
4. **Software/firmware** — hub code, coprocessor code, calibration assets, interface contracts
5. **CI/CD** — on every design change: rebuild artifacts, run sim regression tests, verify BOM availability, publish packages
6. **Execution** — the builder cell runs the plan, emits telemetry, records failures
7. **Learning** — failures become new data for step refinement, grasp tuning, recovery-policy and *design-prior* updates

## Two-Level Learning

The generational framing distinguishes **controller learning within a generation** (RL/imitation for one robot) from **design learning across generations** (the design prior + builder-error model improve each cycle). This is the closest practical analogue to "a learning robot that designs its own successors."

## Standards & Tools It Maps Onto

URDF/SDF/Xacro (robot description), BrickLink Studio (`.io`/`.ldr`/BOM), HEBI YAML+HRDF, Gazebo / Isaac Sim (simulation), ROS 2, GitHub Actions / GitLab CI (the automation layer). uses::[[bricklink-studio]]

## Flywheel as Audit Trail Substrate (2026-06-16)

[[flywheel]] (Paradigma) provides the natural audit-trail layer for the generational factory: each robot generation (design, build instructions, telemetry) is a DAG node with artifact evidence. The Gen 0 → Gen N ancestral lineage is graph ancestry. Evaluators can inspect every design decision and its evidence without manually parsing file histories. The Flywheel graph model is the [[research-graph-infrastructure]] the factory needs to remain evaluatable across generations. infrastructure::[[flywheel]] tracked_by::[[research-graph-infrastructure]]

derived_from::[[agent-evolution-factory]]  
realized_by::[[human-in-the-loop-replication]]  
constrains::[[typed-assembly-grammar]]  
relates_to::[[connector-first-hardware]]  
derived_from::[[feasibility-human-built-generational-factory]]
