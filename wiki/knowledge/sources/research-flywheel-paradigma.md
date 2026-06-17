---
id: research-flywheel-paradigma
title: Research — Flywheel (Paradigma) Potential Capstone Applications
aliases: [Flywheel Research, Paradigma Research]
updated: 2026-06-16
sources:
  - ../../raw/research/flywheel-paradigma/index.md
tags: [research, flywheel, paradigma, autonomous-research, mcp, dag, artifact, hook]
---

# Research: Flywheel (Paradigma) — Potential Capstone Applications

**Flywheel** (beta, March 2026) is a research-infrastructure platform from Paradigma Inc. that organises work as a Directed Acyclic Graph (DAG) of evidence-backed nodes — described externally as "git for science." Its MCP integration means Claude Code agents already in this project's stack can create nodes, attach artifacts, and traverse the graph programmatically with no additional tooling beyond `.mcp.json` configuration. relates_to::[[flywheel]] uses::[[paradigma]]

## Core Primitives

Three durable record types underpin everything: **Nodes** hold durable work state (hypothesis, task, current conclusion); **Artifacts** are concrete evidence (JSON, plots, logs, checkpoints, diffs) kept separate from graph structure so evidence stays inspectable without scraping prose; **Executions** represent run-oriented compute tied to a node. Flywheel's "Encoding the Scientific Method" pattern recommends treating every research node as an evidence-backed hypothesis with four components: hypothesis, evidence for, evidence against, next step. Tags (`open`, `supported`, `rejected`, `needs-replication`, `blocked`) provide scannable state; child branches hold competing hypotheses.

## Fit with the Capstone Self-Model Loop

**The capstone's self-model revision loop maps 1:1 to Flywheel's scientific-method pattern.** Hypothesis = LLM-authored self-model content; experiment = robot task run; observation = [[task-telemetry-contract]] JSON (as a Flywheel artifact); revision = child node; multi-LLM critics = parallel branches from the same parent. The ~15–30 VEX V5 morphology configs are competing hypothesis branches under a shared root. The generational robot evolution (Gen 0 Speedbot → Gen 1 Clawbot → Gen N) maps directly to DAG lineage. relates_to::[[llm-authored-self-model]] grounded_by::[[task-telemetry-contract]] substrate_for::[[physical-robot-software-factory]]

## Hook Automation (Closed Loop)

Flywheel Hooks are durable rules on nodes. When a `task-telemetry-contract` artifact is finalized, a `subtree`-scoped hook POSTs to a local revision agent endpoint; the agent creates the next child node. This closes the feedback loop without a human step — the strongest capstone demo of "autonomous research infrastructure." Supported hook actions: `flywheel/http_request@v1`, `flywheel/http_poll@v1`, `flywheel/upsert_artifact@v1`, `flywheel/add_node_tags@v1`.

## Practical Constraints

Beta product — API may change in the Jun 16–29 capstone window. All Flywheel writes happen on the host laptop; robot telemetry flows Robot → USB → Host → Flywheel. Free pro trial currently available. MCP token configuration required in `.mcp.json`. Rate limit (HTTP 429) at write operations; the self-model loop (at most 1/min) is well below limits.

## Recommendation

Integrate Flywheel as the durable substrate for the self-model evolution graph. Per run: create child node → upload Task Telemetry Contract JSON artifact → commit summary (gap deltas, supported/rejected claims). Configure subtree hook for autonomous loop closure. Walk the graph live at the Jun 29 showcase.
