---
topic: how to split the work load for this project into more modular, approachable tasks for 4 team members
slug: team-workload-split
researched: 2026-06-17
---

# Primary Sources — Team Workload Split

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `wiki/knowledge/concepts/llm-authored-self-model.md` | 2026-06-17 | Full system loop: Generator → Critic → Sim → Physical → Telemetry → Gap → repeat; identifies the 4 functional layers |
| S2 | codebase | `wiki/knowledge/concepts/task-telemetry-contract.md` | 2026-06-17 | JSON schema for grab/pull/throw contracts (predicted/observed/gap blocks); confirms it is the integration seam between hardware and AI layers |
| S3 | codebase | `wiki/knowledge/sources/vex-v5-telemetry-pipeline.md` | 2026-06-17 | 3-stage pipeline spec (Brain USB serial → Pi JSONL → Claude API); Mode A/B details; SD card fallback; PROS Stage 2 upgrade |
| S4 | codebase | `wiki/knowledge/sources/vision-vex-architecture.md` | 2026-06-17 | Pi vision stack (OpenCV + YOLO11n + AprilTag); visual contract extension fields; confirms vision is a Week 2 additive layer |
| S5 | codebase | `capstone-experiment.flowchart.md` | 2026-06-17 | End-to-end flowchart confirming 4 subgraph clusters (Design Space, Validation, Hardware Loop, external actors); validates workstream boundaries |
| S6 | codebase | `wiki/knowledge/sources/gauntlet-capstone-brief.md` | 2026-06-17 | Timeline: Deliverable 01 due June 17 11:59PM; Deliverable 02 (showcase) June 29; team size 3–4 challengers |
| S7 | web | https://www.roboticstomorrow.com/story/2026/02/how-a-paas-platform-can-bridge-classical-robotics-and-ai-to-build-the-next-generation-of-industrial-systems/26131/ | 2026-06-17 | "Robotics engineers handle parts of the data flow, while AI engineers participate in decisions about sensing and control... the boundary between software problems and hardware problems becomes less clear" — supports cross-layer involvement in critical decisions |
| S8 | web | https://www.starkinsider.com/2026/05/multi-agent-ai-coding-team-product-launch.html | 2026-06-17 | "When I have three pieces of work that don't depend on each other, I split them. Claude Code stays on the engine. Codex writes the tests in parallel." — validates parallel track approach |

## Excerpts

### S7 — RoboticsTomorrow: PaaS for Robotics + AI Teams
https://www.roboticstomorrow.com/story/2026/02/how-a-paas-platform-can-bridge-classical-robotics-and-ai-to-build-the-next-generation-of-industrial-systems/26131/
> "In practice in such a PaaS working model, robotics engineers handle parts of the data flow, while AI engineers participate in decisions about sensing and control. Robotics engineers become involved in data quality, signal interpretation, and system observability. AI engineers, in turn, participate in hardware decisions that affect sensing, timing, and controllability."

### S8 — StarkInsider: Multi-Agent AI Build Pattern
https://www.starkinsider.com/2026/05/multi-agent-ai-coding-team-product-launch.html
> "Parallel tracks. When I have three pieces of work that don't depend on each other (say: write the engine code, write a customer demo, write the unit tests), I split them. Claude Code stays on the engine. Codex writes the tests in parallel."
