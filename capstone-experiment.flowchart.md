# Capstone Experiment — 30,000 ft Overview

> Auto-generated from `wiki/knowledge/concepts/llm-authored-self-model.md` (+ `task-telemetry-contract.md`, `typed-assembly-grammar.md`, `physical-robot-software-factory.md`) by `/mermaid-flowchart`.

```mermaid
flowchart TD
    %% External actors (outside all subgraphs)
    Researcher((Researcher))
    Builder((Human Builder))

    %% ── Design Space ──────────────────────────────────────────────────────────
    subgraph DS ["Design Space"]
        Grammar[/Typed Assembly Grammar<br/>~15–30 valid VEX V5 configs/]
        LLMGen(LLM Generator)
        SelfModel["Self-Model<br/>structural · capability · predictive · gap"]
    end

    %% ── Validation ────────────────────────────────────────────────────────────
    subgraph Val ["Validation"]
        Critics{{Multi-LLM Critic Panel}}
        SimValidate(Simulation / Digital Twin)
    end

    %% ── Hardware Loop ─────────────────────────────────────────────────────────
    subgraph HW ["Hardware Loop"]
        BOM[Build Instructions & BOM]
        Robot[VEX V5 Robot]
        TaskExec([Task Execution<br/>grab · pull · throw])
        Telemetry[(Telemetry Log<br/>torque · current · velocity)]
        GapAnalysis(Gap Analysis<br/>observed vs predicted)
    end

    %% ── Edges — main generation flow ─────────────────────────────────────────
    Researcher -->|task spec| LLMGen
    Grammar -->|bounded vocab| LLMGen
    LLMGen -->|authors| SelfModel
    SelfModel -->|submit| Critics

    %% ── Edges — adversarial feedback (dotted = iterative revision) ───────────
    Critics -.->|reject: revise| LLMGen
    Critics -->|approved| SimValidate
    SimValidate -.->|sim failure: revise| LLMGen

    %% ── Edges — hardware build & execute ────────────────────────────────────
    SimValidate -->|validated| BOM
    BOM -->|instructions| Builder
    Builder -->|assembles| Robot
    Robot -->|attempts task| TaskExec
    TaskExec -->|sensor data| Telemetry
    Telemetry -->|observed values| GapAnalysis

    %% ── Edge — loop closure (the learning signal) ────────────────────────────
    GapAnalysis ==>|gap model: next gen| LLMGen

    %% ── Styling ──────────────────────────────────────────────────────────────
    classDef actor fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef llm fill:#f0fdf4,stroke:#16a34a,color:#111;
    classDef hw fill:#fef3c7,stroke:#b45309,color:#111;
    classDef infra fill:#ede9fe,stroke:#6d28d9,color:#111;

    class Researcher,Builder actor;
    class LLMGen,Critics,SelfModel,GapAnalysis llm;
    class Robot,TaskExec,Telemetry hw;
    class Grammar,SimValidate,BOM infra;
```

## Notes

- **Solid arrows** (`-->`) = forward generation flow. **Dotted arrows** (`-.->`) = revision loops (Critics reject or sim fails → LLM revises). **Thick arrow** (`==>`) = the primary learning signal closing the generational loop.
- The `Grammar` node represents the bounded VEX V5 design space (~15–30 valid configurations across 6 parameters); it constrains every self-model the LLM can author.
- `Multi-LLM Critic Panel` is adversarial by design — each critic is prompted to find a specific failure mode (CoM too high, torque budget violated, sensor occlusion, etc.) before any physical build is committed.
- Digital Twin / Simulation validation is listed as a mandatory pipeline stage but the specific sim toolchain (Gazebo vs. Isaac Sim vs. PyBullet) has not yet been decided — flagged as `% TODO: verify sim stack`.
- The `Gap Analysis` node maps directly to the Task Telemetry Contract (`predicted`, `observed`, `gap` JSON blocks) for grab, pull, and throw primitives; the `gap` block is the exact residual fed back to the LLM Generator each generation.
