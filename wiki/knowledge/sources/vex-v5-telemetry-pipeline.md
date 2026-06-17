---
id: vex-v5-telemetry-pipeline
title: Research: VEX V5 Telemetry Pipeline — Output, Storage, and Transfer
updated: 2026-06-16
sources:
  - ../../raw/research/vex-v5-telemetry-pipeline/index.md
tags: [source, research, vex-v5, telemetry, serial, raspberry-pi, llm, pipeline, capstone]
---

# Research: VEX V5 Telemetry Pipeline — Output, Storage, and Transfer

Full report: `raw/research/vex-v5-telemetry-pipeline/index.md`. Primary sources register: `raw/research/vex-v5-telemetry-pipeline/sources.md`.

## What It Is

A complete specification of the three-stage chain that carries Task Telemetry Contract JSON from the VEX V5 Brain to the Claude API for self-model revision: (1) output from the Brain, (2) storage on the relates_to::[[raspberry-pi-5]], and (3) transfer to the external LLM.

## Stage 1 — Output from the V5 Brain

**Primary channel: USB serial user port.** In VEXcode V5 Python, `sys.stdout.write(json.dumps(contract) + '\n')` emits line-delimited JSON on `/dev/ttyACM0` at 115200 baud (8N1 = 11,520 B/s effective). A Task Telemetry Contract (300–600 bytes) transmits in 35–55 ms — the link is **not a bottleneck** for the capstone's slow manipulation tasks (one contract per task primitive).

**SD card fallback.** When the Pi is disconnected (untethered battery-powered run), the Brain writes directly to a FAT32 SD card (≤32GB) via `brain.sdcard.is_inserted()` + standard Python file I/O. After the run, eject and transfer manually to the Pi or laptop. Requires `brain.sdcard.is_inserted()` check on startup.

**PROS Stage 2 alternative.** relates_to::[[pros]] `pros::Serial` opens any Smart Port as RS-485 at up to 921,600 baud (8× USB speed). Decouples the AI data channel from the USB debug/upload port — USB stays free for monitoring while the pipeline runs over Smart Port.

## Stage 2 — Storage on the Raspberry Pi

**Format: JSONL (newline-delimited JSON).** One file per session (`session_YYYYMMDD_HHMMSS.jsonl`), append-only. JSONL is faster for insert-heavy workloads than SQLite on Pi's SD card, is grep-able, human-readable, and directly consumable by the Anthropic Batch API. Each session for the capstone (≤10 task primitives) produces <10 KB; a 32GB Pi microSD holds ~3 million sessions.

```python
session_file = Path(f"/home/pi/telemetry/session_{datetime.now():%Y%m%d_%H%M%S}.jsonl")
with session_file.open('a') as log:
    log.write(json.dumps(contract) + '\n')
    log.flush()
```

## Stage 3 — Transfer to External LLM

**Mode A — Real-time (demo, Stage 1).** After each contract write, call `anthropic.messages.create()` from the Pi. Round-trip: 1–4 seconds — acceptable for slow manipulation tasks. Use `output_config={"format":{"type":"json_schema","schema":...}}` (Sonnet 4.5 / Opus 4.8) for schema-guaranteed revised self-model JSON.

**Mode B — Batch (post-demo training, Stage 2).** Accumulate session JSONL files, then submit to `anthropic.messages.batches.create()` for **50% cost discount** (Opus 4.8: $7.50/M input vs $15/M). Async, up to 100,000 requests/batch, results as JSONL, SLA best-effort <1 hour, guaranteed 24 hours.

**Mode C — Archive sync.** `rsync -avz /home/pi/telemetry/ user@laptop.local:/datasets/` over Pi Wi-Fi. DigitalOcean Spaces (`boto3`) for cloud-durable storage.

## Reliability

- Serial drop mid-task: `readline()` in try/except; malformed lines logged and skipped; JSONL captures all data received before the drop
- API timeout: 10-second timeout on `messages.create()`; cache and retry after next primitive
- Pi Wi-Fi unavailable: telemetry still writes to JSONL locally; submit batch post-hoc once online

derived_from::[[research-vexcode-v5]]
extends::[[task-telemetry-contract]]
uses::[[raspberry-pi-5]]
uses::[[pros]]
relates_to::[[vex-v5]]
relates_to::[[llm-authored-self-model]]
relates_to::[[physical-robot-software-factory]]
