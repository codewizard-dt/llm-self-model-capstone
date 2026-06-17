---
id: research-graph-infrastructure
title: Research Graph Infrastructure
aliases: [DAG-Based Research, Research DAG, Autonomous Research Infrastructure]
updated: 2026-06-16
sources:
  - ../../raw/research/flywheel-paradigma/index.md
tags: [concept, infrastructure, dag, research, autonomous, scientific-method, audit-trail]
---

# Research Graph Infrastructure

The idea that **scientific investigation is most productive when represented as a Directed Acyclic Graph (DAG)** of evidence-backed hypotheses rather than as a linear sequence of papers or notebooks. Each node in the graph holds one claim or experiment, knows its ancestry (what prior result it extends or contradicts), and carries concrete evidence as attached artifacts. Branches represent divergent hypotheses; merges record resolved disagreements. The DAG structure makes the lineage of evidence and decisions inspectable by agents, humans, and automated evaluators alike.

## Why This Matters for Agentic Research

When AI agents generate results faster than humans can audit them, the organising substrate becomes the bottleneck. A flat file system or a linear notebook does not expose enough structure for an agent to know: what has been tried, what held, and what it implies. A DAG makes these facts first-class — an agent can traverse the graph to find open questions, avoid duplicate work, and extend only lines of inquiry with supporting evidence. relates_to::[[flywheel]]

## The Scientific Method Encoded

The recommended node template for research claims maps directly to the scientific method:

1. **Hypothesis** — what claim is being tested?
2. **Evidence for** — observations that support the claim (attached as artifacts)
3. **Evidence against** — counterexamples, failed runs, uncertainty
4. **Current read** — what you believe now, and how strongly
5. **Next step** — next experiment, branch, review, or decision

Tags encode state: `open`, `supported`, `rejected`, `needs-replication`, `needs-evidence`, `blocked`.

## Fit with the Self-Model Loop

The capstone's [[llm-authored-self-model]] revision cycle is a natural instantiation of research graph infrastructure:

- **Hypothesis node**: current LLM self-model (structured self-description)
- **Artifact**: [[task-telemetry-contract]] JSON from each robot run (predicted vs. observed vs. gap)
- **Branch**: competing morphology hypotheses, each with its own telemetry evidence
- **Merge/tag**: surviving configuration after multi-LLM critic convergence

The generational progression (Gen 0 → Gen N) is the DAG's ancestral lineage; each generation's design rationale and telemetry residuals are preserved and inspectable. substrate_for::[[llm-authored-self-model]] substrate_for::[[physical-robot-software-factory]]

## Exemplar Implementation

uses::[[flywheel]] is the primary exemplar: beta platform (Paradigma Inc., March 2026) exposing this model via MCP to Claude Code agents.
