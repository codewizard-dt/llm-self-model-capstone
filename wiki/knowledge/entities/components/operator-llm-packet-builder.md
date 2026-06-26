---
id: operator-llm-packet-builder
title: Operator LLM Packet Builder
aliases: [operator_llm, operator-llm-critic, packet-builder, F8 packet builder]
updated: 2026-06-25
sources:
  - ../../sources/operator-layer-research.md
  - ../../../../operator/src/operator_llm/packet_builder.py
  - ../../../../operator/src/operator_llm/validate.py
  - ../../../../operator/docs/llm_critic_architecture.md
tags: [component, llm, f8, f9, offline, packet-builder, operator]
---

# Operator LLM Packet Builder

`operator/src/operator_llm/` is the offline Python package that assembles structured Markdown evidence packets for the F8 Generator/F9 Critic loop. It is distributed as the `operator-llm-critic` package (v0.2.0, Python ≥3.12,<3.13) under `operator/pyproject.toml`.

derived_from::[[operator-layer-research]]
feeds::[[llm-authored-self-model]]
uses::[[task-telemetry-contract]]
uses::[[vexy-ros-runtime]]
implements::[[llm-authored-self-model]]

## Package Layout

| File | Symbols | Purpose |
|------|---------|---------|
| `packet_builder.py` | `build_operator_packet`, `build_packet_from_files`, `_*_block` helpers, blocked-state constants | Assembles the Markdown evidence packet for the F8 Generator |
| `validate.py` | `validate_fixture_packets`, `main` | Validates the two canonical packet types against blocked-state invariants |
| `__init__.py` | `__all__` | Public surface (minimal) |

**Runtime dependencies**: `pydantic>=2.12`, `reactivex>=4.1.0`
**PYTHONPATH**: `src:../contracts/src:../robot/ros2-runtime/src` (from `operator/Makefile`)

## Entry Points

### `build_packet_from_files` (`packet_builder.py:42–78`)

File-level entry point. Accepts optional `contract_jsonl_path`, `ros_bundle_path`, `gap_summary_path`. When a ROS bundle is supplied it calls `vexy_ros.evidence_export.contract_jsonl_from_bundle` and stamps `source_refs["ros_export_routine"]` for traceability. Returns the assembled Markdown string.

### `build_operator_packet` (`packet_builder.py:81–140`)

Core assembly function. Produces a structured Markdown document with two tracks:

- **Track 1 — M1 + ROS Proof Intake**: contract surface, ROS proof routine, hardware proof status
- **Track 2 — Operator LLM Packet**: source refs, current SelfModel, parts catalog verdict, contract evidence, gap summary, human constraints, generator guardrails

The generator guardrails section enforces information separation — oracle parameters are never included.

## Blocked-State Constants

All constants live in `packet_builder.py`:

| Constant | Meaning |
|----------|---------|
| `BLOCKED_F10_GAP` | No `gap_summary_path` was provided — gap section is blocked pending F10 |
| `BLOCKED_NO_CONTRACT_EVIDENCE` | No contract lines exist in the input |
| `BLOCKED_HARDWARE_PROOF` | Contract lines exist but none have a `raw_session_path` |
| `FIXTURE_BACKED_GAP` | Gap summary is supplied via a fixture (not live F10 output) |

Until F10 (gap analyzer) is implemented, gap summary sections will be either `BLOCKED_F10_GAP` or `FIXTURE_BACKED_GAP`. This is the **only open blocker for the F8 Generator**.

## Integration Test

`validate_fixture_packets` (`validate.py:21–47`) runs both the "contract-JSONL path" and "ROS-bundle path" packet types through assertion checks that confirm blocked labels appear (or don't) in the right sections. It serves as a living integration test of the packet builder's invariants.

Test coverage (`operator/tests/test_packet_builder.py`, 5 functions):
- F10 + hardware-proof blockers with a contract fixture
- ROS bundle intake naming the proof-export routine and preserving `raw_session_path`
- Missing-contract blocked label
- Fixture-backed gap-summary labeling
- Catalog violations exposed without operator-local schemas

## Evidence Bridge

`vexy_ros.evidence_export.contract_jsonl_from_bundle` (`evidence_export.py:70–77`) is the bridge between ROS bag/proof data and this packet builder. It accepts a bundle dict, calls `contract_payload_from_bundle`, serializes to JSON, validates against `ContractLine`, and appends `\n`. The bundle path stamping in `source_refs["ros_export_routine"]` provides end-to-end traceability.

## Schema Constraint

This package must import all telemetry, self-model, and parts schemas from `contracts/src/contracts/`. It does not define its own schemas. Key shared types: `ContractLine`, `SelfModel`/`SelfModelConfig`, `PartsCatalog`/`validate_config`, `vocabulary`.

## F8/F9 Architecture

`operator/docs/llm_critic_architecture.md` (owner: Grace Huang, 2026-06-24) defines:
- One **Generator LLM** that reads the assembled packet and produces a revised SelfModel
- Three stateless **Critics**: physics, torque, CoM/geometry — each attacks the Generator's output
- Six implementation slices: operator-packet-builder (done) → generator-prompt → generator-gap-revision → critic-prompt-panel → critic-review-aggregation → planted-fault-critic-tests

The packet builder is the **completed prerequisite**; the remaining five slices are unimplemented pending F10.
