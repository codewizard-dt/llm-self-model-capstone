# Slice: trace-readback-history

| Field | Value |
|---|---|
| Feature | run-logger |
| Stack | pilot |
| Depends on | `trace-append-writer` |

## What this slice delivers

Validated trace consumption utilities: a ROS-free JSONL reader/parser for replay-mode inputs and a
bounded recent-history formatter for LLM prompt context. This slice makes traces useful after they are
written without exposing raw unbounded logs downstream.

## Files to create / change

```
pilot/
  src/pilot/run_logger.py       CHANGE - validated JSONL readback and recent-history utilities
  tests/test_run_logger.py      CHANGE - readback, malformed-line, history bounds coverage
```

## Requirements

- Read JSONL trace files back into typed, contract-validated trace records.
- Report malformed JSON, non-object JSON, and schema-invalid records with useful line-number context.
- Preserve record order during readback.
- Provide a bounded recent-history selector or formatter over typed trace records.
- Include useful recent decisions, commands, results, assertions, failures, and stop records where
  available.
- Keep recent-history output compact, deterministic, and suitable for `pilot.decision` prompt input.
- Do not pass raw JSONL tails, binary data, provider secrets, environment variables, or unbounded logs
  to the LLM.
- Keep all utilities ROS-free and replay-friendly.

## Acceptance

- Tests prove readback returns typed, contract-valid records from files written by the logger.
- Tests prove malformed JSONL reports line numbers and does not silently skip bad records.
- Tests prove schema-invalid JSONL reports line numbers and validation context.
- Tests prove recent-history selection is bounded by count/size policy and deterministic across
  repeated calls.
- Tests prove recent-history text or payloads summarize relevant outcomes without embedding raw
  unbounded trace lines.
- Tests prove readback and history utilities import without ROS.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Running replay mode, selecting next skills, executing commands, computing assertions, changing
  prompt adapter behavior beyond providing history input, or hardware proof runs.
