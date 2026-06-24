# Operator Docs

The `operator` vertical owns the offline self-model loop:

- Generator: authors Gen 0 and revises Gen N+1 from contract evidence.
- Critic panel: stateless pre-build review of candidate self-models.
- Gap analyzer, presenter, and demo replay: turn contract evidence into readable iteration history.

All durable schemas stay in `contracts/`. Operator docs may describe packets,
prompts, and workflows, but they must import or reference `contracts` models
instead of redefining telemetry or self-model JSON shapes.

- [LLM/Critic Architecture](llm_critic_architecture.md)
- [June 23 Team Update](team_update_2026_06_23.html)
