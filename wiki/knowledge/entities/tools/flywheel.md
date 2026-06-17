---
id: flywheel
title: Flywheel
aliases: [Flywheel by Paradigma, Paradigma Flywheel]
updated: 2026-06-16
sources:
  - ../../../raw/research/flywheel-paradigma/index.md
tags: [tool, research-infrastructure, dag, mcp, agent, autonomous-research, beta]
---

# Flywheel

Beta research-infrastructure platform built by relates_to::[[paradigma]], launched March 2026 (founded by [[francesco-pappone]]). **Tagline: "The infrastructure for autonomous research."** Positioned as "git for science": instead of papers, the unit of knowledge is a Directed Acyclic Graph (DAG) where every experiment is a node, every node knows its parents (hypothesis motivating it, prior result it extends or contradicts), and replication is a first-class branch operation.

## Core Primitives

- **Nodes**: durable work units — hypothesis, task, result, or decision. Can be branched, merged, tagged (`open`, `supported`, `rejected`, `needs-replication`, `blocked`), and committed with a summary.
- **Artifacts**: concrete evidence attached to nodes — JSON, plots, tables, logs, checkpoints, diffs. Separate from graph structure so evidence is agent-inspectable without scraping prose.
- **Executions**: run-oriented compute tied to a node (managed GPU, job launch, termination state).
- **Campaigns**: challenge-style graphs with an organiser root, participant attempt nodes, submission artifacts, and leaderboard-style outputs.
- **Hooks**: durable event-driven automation rules. Trigger events: `artifact.finalized`, `node.published`. Workflow steps: `flywheel/http_request@v1`, `flywheel/upsert_artifact@v1`, `flywheel/add_node_tags@v1`. Scope: `self`, `subtree`, `graph`.

## MCP Integration

Flywheel ships a first-party MCP server. **Claude Code agents can traverse the graph, branch experiments, attach artifacts, and commit results programmatically** without touching a notebook. Compatible with any agent orchestration framework via MCP. Relevant MCP tool families: graph/node creation, node inspection, artifact publish/retrieval, hook management, managed compute, import/export, campaign submission lifecycle.

## Capstone Relevance

**HIGH VALUE.** The capstone's [[llm-authored-self-model]] revision loop is structurally identical to Flywheel's "Encoding the Scientific Method" pattern. [[task-telemetry-contract]] JSONs map directly to Flywheel artifacts. The generational robot factory lineage (Gen 0 → Gen N) maps to DAG ancestry. Hooks enable autonomous closed-loop revision without a human step between telemetry and LLM revision. substrate_for::[[llm-authored-self-model]] substrate_for::[[task-telemetry-contract]] infrastructure_for::[[physical-robot-software-factory]]

## Real-World Validation

**Hyperfamila (HackRome 2026)** used Flywheel as the knowledge-management layer in an agentic physical autoresearch system — OpenAI Codex as the agent, SO101 robot arm for execution, ACT policies for manipulation. This is direct validation that Flywheel works as the hypothesis-and-result store in a physical agent loop. The project won the Paradigma "Best use of Flywheel" prize. relates_to::[[Agentic Physical Autoresearch]]

## Practical Notes

- Free pro trial available at signup as of 2026-06-16.
- All Flywheel writes occur on the host laptop; robot telemetry path: Robot → USB → Host → Flywheel.
- Connectivity requirement: host must have internet access during runs.
- Beta risk: pin to `@v1` versioned step names; monitor changelog.
