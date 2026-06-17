---
topic: "Flywheel (flywheel.paradigma.inc) — what it is and potential applications in the capstone project"
slug: flywheel-paradigma
researched: 2026-06-16
sources: [./sources.md]
---

# Research: Flywheel (Paradigma) — Potential Capstone Applications

> Flywheel is a beta research-infrastructure platform (paradigma.inc) that organises work as a Directed Acyclic Graph of evidence-backed nodes. Its MCP integration means Claude Code agents can create nodes, attach artifacts, and traverse the graph programmatically. The capstone's self-model revision loop — LLM proposes → robot executes → telemetry observed → gap computed → LLM revises — is structurally identical to the scientific-method workflow Flywheel was designed to encode. Recommendation: integrate Flywheel as the durable substrate for the self-model evolution graph, using hooks to close the telemetry-to-revision loop autonomously.

---

## Research Questions

1. What is Flywheel and how does it represent research work?
2. How does it integrate with Claude Code / MCP agents?
3. Which Flywheel primitives map to the capstone's core artifacts (self-model, Task Telemetry Contract, morphology configs)?
4. Which Flywheel features (hooks, campaigns, artifacts) could automate the self-model feedback loop?
5. What are the practical constraints (beta limitations, cost, connectivity) for using it in the capstone?

---

## Current State (Codebase)

The project is in the research and planning phase with no implementation code yet. The wiki documents:

- **Core concept**: `knowledge/concepts/llm-authored-self-model.md` — LLM authors a structured self-description from finite VEX V5 parts; multi-LLM critics attack it; task telemetry reality-corrects it.
- **Feedback mechanism**: `knowledge/concepts/task-telemetry-contract.md` — predicted + observed + gap JSON per task primitive (grab/pull/throw), the machine-readable feed the LLM reads to revise the self-model.
- **Hardware**: VEX V5 Clawbot (Gen 1) / Speedbot (Gen 0); ~15–30 valid morphology configs from the Starter Kit + Booster Kit.
- **Architecture decision**: USB serial user port is the LLM integration path (no WiFi on VEX Brain); inference runs on a host laptop.
- **Planning deadline**: Deliverable 01 due Jun 17, 2026; capstone showcase Jun 29, 2026.

---

## Key Findings

**What Flywheel is** [S1, S2, S3]:
Flywheel (beta, launched March 2026, Paradigma Inc., CEO Francesco Pappone) is "the infrastructure for autonomous research." It replaces papers with a Directed Acyclic Graph (DAG): every experiment is a node, every node tracks its motivating hypothesis, and every branch represents a divergent path. Described externally as "git for science" [S4]. Core thesis: "when intelligence scales, organizing its output becomes load-bearing" [S3].

**Three durable record types** [S5]:
- **Nodes**: durable work state — the prompt, task, hypothesis, current conclusion, and links to neighbours. Can be branched, merged, tagged, and committed.
- **Artifacts**: concrete evidence — text, tables, JSON, images, plots, logs, checkpoints, diffs. Kept separate from graph structure so evidence is inspectable without scraping prose.
- **Executions**: run-oriented work tied to a node — managed compute, launched jobs, termination state.

**Encoding the scientific method** [S6]:
Flywheel explicitly recommends treating nodes as evidence-backed hypotheses following four questions: (1) What is the hypothesis? (2) What evidence supports it? (3) What argues against it? (4) What next? Tags (`open`, `supported`, `rejected`, `needs-replication`) provide scannable state; summaries carry the current read; child branches hold competing hypotheses.

**MCP + Claude Code integration** [S4, S7]:
"MCP integration means Claude Code agents can traverse the graph, branch experiments, and commit results programmatically. The research loop closes without a human touching a notebook." Flywheel is built to work with any agent orchestration framework via its MCP server. The same MCP toolset that runs this project's Claude Code session can write directly to Flywheel.

**Hooks / event-driven automations** [S8]:
Hooks are durable rules on nodes. Supported trigger events: `artifact.finalized` and `node.published`. Scope options: `self`, `subtree`, `graph`. Workflow steps include `flywheel/http_request@v1`, `flywheel/http_poll@v1`, `flywheel/upsert_artifact@v1`, `flywheel/add_node_tags@v1`. Hooks enable closing the research loop without human intervention.

**Campaigns** [S9]:
Challenge-style graphs — an organiser owns a root, publishes a config, and participants work in attempt nodes. Submission artifacts are finalized with `metadata.campaign_role = "submission"`. Campaigns can have visibility policies and produce leaderboard-style outputs. Useful for structured demonstrations and evaluation.

---

## Constraints

- **Beta product**: API and MCP surface may change during the Jun 16–29 capstone window. Use stable CLI and documented MCP tool names; pin to versioned workflow step names (`@v1`).
- **Connectivity**: Flywheel is a cloud service; the VEX Brain connects to the host laptop via USB/serial only. All Flywheel writes happen on the host, not on the robot. This is fine — telemetry flows: Robot → USB → Host → Flywheel.
- **Rate limits**: Write operations return HTTP 429 when exceeded. The self-model loop (one revision per task run) is far below typical limits for a single-user research project.
- **Auth requirement**: Requires sign-up at flywheel.paradigma.inc and MCP token configuration in `.mcp.json`. No existing auth set up in this project.
- **No pip/no WiFi on VEX Brain**: not a constraint — Flywheel runs entirely on the host laptop side of the integration.

---

## Application Mapping

### 1. Self-Model Evolution Graph (HIGH VALUE — direct fit)

The self-model revision loop IS the scientific method:

| Scientific method | Capstone concept | Flywheel primitive |
|---|---|---|
| Hypothesis | LLM-authored self-model (what the robot can do) | Node content (Markdown self-description) |
| Experiment | Robot executes task (grab / pull / throw) | Execution record |
| Observation | Task Telemetry Contract JSON (predicted vs. actual) | Artifact (JSON) |
| Revision | LLM updates self-model based on gap | Child node, new summary |
| Competing explanations | Multi-LLM critics attacking the self-model | Parallel branches from same parent |
| Resolution | Surviving self-model | Merge / `supported` tag |

Each telemetry run produces a revision cycle. Flywheel preserves the full lineage: why the LLM believed what it did, what the robot actually did, and how the gap drove the next revision. This is exactly the "inspectable audit trail" Flywheel is designed to produce [S6].

### 2. Configuration Space Exploration (HIGH VALUE)

The ~15–30 valid VEX V5 morphologies are competing hypotheses about which configuration best minimises the telemetry gap. Flywheel's branching model is perfect:

- Root node: "Which Starter Kit + Booster morphology best closes the telemetry gap?"
- Branch per config: "Hypothesis: 4-motor symmetric arm (Config-07) minimises grab-gap"
- Artifact per branch: telemetry JSON from that config's runs
- Tags: `open`, `supported`, `rejected`
- Merge: best-performing config becomes the Gen N baseline

### 3. Closed-Loop Automation via Hooks (MEDIUM VALUE — demonstrable)

When a Task Telemetry Contract artifact is finalized on a self-model node, a Flywheel hook can automatically POST to a webhook that triggers the LLM revision agent. The revision agent creates a child node with the updated self-model. This closes the loop without a human step, which is the strongest demo of "autonomous research infrastructure."

Workflow sketch:
```yaml
on:
  artifact.finalized: {}
if:
  any_artifact:
    field: metadata.artifact_type
    eq: task-telemetry-contract
jobs:
  main:
    steps:
      - id: trigger_revision
        uses: flywheel/http_request@v1
        with:
          url: http://localhost:PORT/revise-self-model
          method: POST
          body:
            source_node_id: "${{ event.source_node_id }}"
            artifact_ids: "${{ event.payload.artifact_ids }}"
```

### 4. Generational Audit Trail (HIGH VALUE — aligns with capstone pitch)

The "human-built generational robot factory" maps to graph lineage:
- Gen 0 node: Speedbot (2-motor), self-model v0, baseline telemetry
- Gen 1 node (child): Clawbot (4-motor), self-model v1, improved telemetry
- Gen N node: best-discovered config, self-model vN

This lineage is inspectable by Gauntlet evaluators, which strengthens the capstone demo. Each generation has its artifact evidence; nothing is lost.

### 5. Capstone Showcase Campaign (LOW-MEDIUM VALUE)

If the Jun 29 showcase involves live scoring or comparison across configurations, Flywheel's campaign system could structure it. Less critical for a solo capstone; more relevant if the project evolves into a multi-participant research platform.

---

## Solution Comparison

| Approach | Flywheel | Plain file/git log | Notion/wiki only |
|---|---|---|---|
| Agent-writable | Native MCP | Via git commit | No |
| Artifact storage | First-class | Git LFS / file system | Attachments |
| Branching hypotheses | DAG — first class | Git branches (code-centric) | Manual |
| Hook automation | Built-in | Custom infra needed | No |
| Audit trail | Inspectable graph | Git log | Page history |
| Beta risk | Medium | None | None |
| Setup cost | Low (MCP config) | None | None |

---

## Recommendation

**Integrate Flywheel as the durable substrate for the self-model evolution graph.**

The capstone's primary research claim — "an LLM can author a robot self-model that reality-corrects itself through task telemetry" — needs a credible, inspectable record of every revision cycle to be evaluatable. Flywheel provides this with zero custom infrastructure: create a node per self-model version, attach Task Telemetry Contract JSON artifacts, and let the DAG show the evolution.

### Implementation outline

1. Sign up at `flywheel.paradigma.inc` (free pro trial currently available).
2. Install Flywheel CLI: `npm install -g flywheel` (per install docs).
3. Add Flywheel MCP server to `.mcp.json` in this project (per `/mcp/setup`).
4. Create project root node: **"VEX V5 LLM Self-Model Evolution"** — set the hypothesis, describe the methodology, tag `open`.
5. Per robot run:
   - Create child node with LLM-authored self-model content as Markdown.
   - Upload Task Telemetry Contract JSON as an artifact (`metadata.artifact_type: task-telemetry-contract`).
   - Commit summary: gap deltas, which claims were supported/rejected.
6. Configure hook on root node (`subtree` scope): `artifact.finalized` → POST to local revision agent endpoint → agent creates next child node.
7. For competing morphologies: branch from shared parent, attach config-specific telemetry.
8. For capstone demo: walk the graph live — "here is Gen 0 Speedbot, here is what the LLM predicted, here is the gap, here is Gen 1 after the loop ran twice."

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Beta API changes | Use versioned CLI commands and `@v1` step names; monitor changelog |
| Hook local server not reachable from Flywheel | Use `ngrok` or equivalent to expose local revision agent endpoint during demo |
| Rate limits during rapid iteration | Self-model loop runs at most 1/min — well within typical limits |
| Auth setup complexity | Covered by Flywheel's MCP setup guide; one-time config |

### Alternative if Flywheel is unavailable

Use a plain SQLite database + git log as the artifact store. Loss: no agent-traversable DAG, no hooks, no inspectable graph for evaluators. Gain: zero dependency risk.

---

## Next Steps

- **To set up**: `/task-add "Integrate Flywheel MCP into capstone — sign up, install CLI, add to .mcp.json, create root self-model node"`
- **To decide**: Whether to use hooks for autonomous loop closure now (complexity) or add hooks after the basic self-model loop is demonstrated (simpler first). Frame as `/decision-create "Flywheel hook automation: enable now vs. after basic loop demo"`.
- **To ingest**: Run `/wiki-ingest raw/research/flywheel-paradigma/index.md` to synthesize this research into the knowledge base.
