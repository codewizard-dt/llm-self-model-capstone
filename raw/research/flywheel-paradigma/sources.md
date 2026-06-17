---
topic: "Flywheel (flywheel.paradigma.inc) — what it is and potential applications in the capstone project"
slug: flywheel-paradigma
researched: 2026-06-16
---

# Primary Sources — Flywheel (Paradigma)

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://flywheel.paradigma.inc/ | 2026-06-16 | Tagline "The infrastructure for autonomous research"; MCP + CLI install options; beta status |
| S2 | web | https://paradigma.inc/ | 2026-06-16 | Company positioning: "We are building the infrastructure for autonomous research" |
| S3 | web | https://paradigma.inc/blog/the-new-age-of-research/ | 2026-06-16 | Francesco Pappone's founding thesis: structure is load-bearing when intelligence scales; full DAG explanation; March 2026 publication date |
| S4 | web | https://www.threads.com/@sakeeb.rahman/post/DWmQo1wEQeP/ | 2026-06-16 | Independent analysis: "MCP integration means Claude Code agents can traverse the graph, branch experiments, and commit results programmatically. The research loop closes without a human touching a notebook." Also: managed GPU compute, campaigns, full subgraph export/import |
| S5 | web | https://docs.flywheel.paradigma.inc/concepts/nodes-artifacts-executions | 2026-06-16 | Definitive description of three record types — Nodes (durable work state), Artifacts (concrete evidence: JSON, plots, logs, checkpoints), Executions (run-oriented compute) |
| S6 | web | https://docs.flywheel.paradigma.inc/how-to-use-flywheel/encoding-the-scientific-method | 2026-06-16 | Four-question hypothesis template; artifact categories (tables, plots, logs, diffs, checkpoints); competing hypotheses as branches; tags (open/supported/rejected/needs-replication/blocked); summary vs. content distinction |
| S7 | web | https://x.com/EmanueleRodola/status/2032182841379795388 | 2026-06-16 | "Flywheel is built to work with any agent orchestration framework you may be using via Flywheel's MCP" — open beta announcement |
| S8 | web | https://docs.flywheel.paradigma.inc/concepts/hooks | 2026-06-16 | Full hooks reference: trigger events (artifact.finalized, node.published), scope (self/subtree/graph), workflow steps (http_request@v1, http_poll@v1, json_extract@v1, load_artifact@v1, upsert_artifact@v1, add_node_tags@v1), secrets, run lifecycle |
| S9 | web | https://docs.flywheel.paradigma.inc/concepts/campaigns | 2026-06-16 | Campaigns: challenge-style graphs with organiser root, participant attempt nodes, submission artifact metadata, visibility policy, lifecycle states (accepted/forwarding/forwarded/scored/rejected/failed) |
| S10 | web | https://docs.flywheel.paradigma.inc/concepts/graph-model | 2026-06-16 | Graph model: nodes as durable work units, edges as ancestry, branching for alternatives, merging for resolved outcomes; CLI commands nodes:list, nodes:get, nodes:children, nodes:parents |
| S11 | web | https://docs.flywheel.paradigma.inc/mcp/tools | 2026-06-16 | MCP tool families: graph/node creation, node inspection, artifact publish/retrieval, hook management, managed compute, import/export; flywheel_get_contract tool for live contract lookup |
| S12 | codebase | `wiki/index.md` | 2026-06-16 | Capstone project context: LLM-Authored Robot Self-Model as primary idea; Task Telemetry Contract (predicted+observed+gap JSON); VEX V5 hardware; ~15-30 valid configs; Gen 0 Speedbot, Gen 1 Clawbot |

---

## Excerpts

### S3 — The New Age of Research (Paradigma Blog, Francesco Pappone, March 2026)
https://paradigma.inc/blog/the-new-age-of-research/

> "In Flywheel, the unit of knowledge is a Directed Acyclic Graph, instead of a paper. Every experiment is a node. Every node knows its parents: what hypothesis motivated it, what prior result it extends or contradicts. Replication is a first-class operation, structurally identical to any other branch of the graph. Agents can traverse this graph, extend it, prune dead ends. Humans can enter at any point to redirect, contribute, or inspect."

> "If intelligence becomes scalable, the systems that organize its output become load-bearing."

### S4 — Threads analysis by Sakeeb Rahman (external, independent)
https://www.threads.com/@sakeeb.rahman/post/DWmQo1wEQeP/

> "MCP integration means Claude Code agents can traverse the graph, branch experiments, and commit results programmatically. The research loop closes without a human touching a notebook."

> "The platform ships with managed GPU compute tied to graph nodes, artifact storage for evidence, campaigns for structured research challenges with live leaderboards, and full subgraph export/import."

### S5 — Nodes, Artifacts, And Executions (Flywheel Docs)
https://docs.flywheel.paradigma.inc/concepts/nodes-artifacts-executions

> "Use artifacts for evidence. An artifact is the durable output of work: a report, plot, table, dataset excerpt, model checkpoint, patch, transcript, or JSON record. Keeping evidence in artifacts makes it inspectable by people, agents, hooks, and exports without requiring readers to scrape it from prose."

> "A typical empirical branch starts as a node, launches an execution or acquires compute, uploads artifacts from the run, then commits a summary that explains what the artifacts mean."

### S6 — Encoding the Scientific Method (Flywheel Docs)
https://docs.flywheel.paradigma.inc/how-to-use-flywheel/encoding-the-scientific-method

> "Use each claim-bearing node to answer four questions: What hypothesis, claim, or question is this node about? What evidence currently supports it? What evidence currently argues against it? What should happen next?"

> "Use tags for research state such as open, supported, rejected, needs-replication, or blocked."

> "When there are multiple plausible explanations, branch them explicitly. Start from a shared observation or question, then create child nodes for each candidate explanation."

### S8 — Hooks And Automations (Flywheel Docs)
https://docs.flywheel.paradigma.inc/concepts/hooks

> "Flywheel Hooks are durable rules configured on nodes. A hook watches for a supported event, checks whether the event is in scope, evaluates the workflow filter, and creates an observable asynchronous run when the event matches."

> "Use hooks when a graph needs repeatable automation around artifacts: notify an external service, enrich a node after a submission, write a derived artifact, or tag a participant attempt for later review."

> Supported trigger events: `artifact.finalized` (after artifact finalize writes succeed) and `node.published` (when an eligible submission node becomes public).
