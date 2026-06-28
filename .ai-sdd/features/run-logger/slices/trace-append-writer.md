# Slice: trace-append-writer

| Field | Value |
|---|---|
| Feature | run-logger |
| Stack | pilot |
| Depends on | `logger-core-api` |

## What this slice delivers

The append-only JSONL writer. This slice turns contract-valid trace records into compact one-line JSON
events on disk, provides default run-file naming under an ignored runtime directory, and ensures
schema-invalid append attempts leave the trace unchanged.

## Files to create / change

```
pilot/
  src/pilot/run_logger.py       CHANGE - JSONL file writer, append helpers, default paths
  tests/test_run_logger.py      CHANGE - write/flush/path/invalid-append coverage
```

## Requirements

- Write newline-delimited UTF-8 JSON with exactly one compact JSON object per trace event.
- Preserve caller append order exactly.
- Validate the full `PilotTraceRecord` before writing each line.
- Reject invalid append attempts without writing partial or malformed lines.
- Flush writes predictably after each append by default.
- Provide caller-supplied output path support.
- Provide a default path policy suitable for runtime output such as `pilot/runs/<session_id>.jsonl`.
- Create parent runtime directories when needed for explicit/default output paths.
- Keep the core writer single-process and ROS-free.

## Acceptance

- Tests prove successful appends produce one valid JSON object per line and no extra text.
- Tests prove every written line validates as a `contracts.PilotTraceRecord`.
- Tests prove append order and sequence numbers are stable across all event variants.
- Tests prove invalid event payloads leave the file unchanged for that append.
- Tests prove default path generation uses the configured session id and an ignored runtime directory.
- Tests prove explicit caller paths work in temporary test directories.
- Tests prove flushing/closing behavior leaves readable complete lines after interruption-style close.
- `make -C pilot test`, `make -C pilot lint`, root `make test`, root `make validate`, and root
  `make lint` pass.

## Out Of Scope

- Trace readback APIs, recent-history formatting, replay loop execution, multi-process locking, ROS
  bag/MCAP export, raw image capture, provider transcript capture, or hardware integration.
