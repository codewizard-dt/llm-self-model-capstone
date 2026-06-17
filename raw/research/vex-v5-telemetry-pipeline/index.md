---
topic: how telemetry would be output, saved, and transferred from the VEX V5 to an external system for heavier modeling/LLM tasks
slug: vex-v5-telemetry-pipeline
researched: 2026-06-16
sources: [./sources.md]
---

# Research: VEX V5 Telemetry Pipeline — Output, Storage, and Transfer

> The canonical path is three stages: (1) the V5 Brain emits line-delimited JSON over its USB serial user port at 115200 baud (~11,500 B/s, ample for Task Telemetry Contracts); (2) the Raspberry Pi 5 receives, merges with vision data, and writes to a rotating JSONL archive on its filesystem; (3) the Pi uploads each completed contract to the Claude API in real time for immediate self-model revision, and archives session JSONL files for later bulk submission to the Anthropic Message Batches API at 50% cost. A SD card on the Brain is the cold-backup for untethered runs.

---

## Research Questions

1. How does the V5 Brain emit telemetry to an external process?
2. What file format and storage strategy should the Raspberry Pi use for incoming telemetry?
3. How are completed Task Telemetry Contracts transferred to an LLM for heavier inference?
4. What are the throughput and reliability limits of the USB serial link?
5. What is the SD card fallback path for offline/untethered runs?

---

## Current State (Codebase)

No robot-side code exists yet. Existing wiki knowledge confirms:

- **Architecture**: `raw/research/vexcode-v5/index.md` — recommends V5 Brain running VEXcode Python as a lightweight stub emitting JSON via `sys.stdout` (USB serial user port); external host runs the LLM pipeline.
- **Task Telemetry Contract schema**: `wiki/knowledge/concepts/task-telemetry-contract.md` — `{task, predicted, observed, gap}` JSON per primitive (grab/pull/throw). Visual extension documented from `raw/research/vision-vex-architecture/index.md`.
- **Toolchain**: Stage 1 = VEXcode V5 Python; Stage 2 = PROS + LemLib (FreeRTOS + RS-485 Smart Port at up to 921,600 baud).
- **Constraint**: V5 Brain has no Wi-Fi; all network access must go through the Raspberry Pi coprocessor.

---

## Key Findings

### 1. Emitting Telemetry from the V5 Brain

**Primary path — USB serial user port** [S1][S2]:

The V5 Brain exposes two USB serial ports when connected: a *system port* (upload/control) and a *user port* (stdio). In VEXcode V5 Python, all `print()` and `sys.stdout.write()` output goes to the user port. The Pi reads from `/dev/ttyACM0`.

```python
# V5 Brain side (VEXcode V5 Python)
import sys, json
from vex import *

motor = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)

def emit_telemetry(task_name, data):
    sys.stdout.write(json.dumps({"task": task_name, **data}) + '\n')
    sys.stdout.flush()

# After a grab action:
emit_telemetry("grab", {
    "claw_position_delta_deg": motor.position(DEGREES),
    "claw_current_A": motor.current(),
    "claw_torque_Nm": motor.torque(),
    "ts": brain.timer.time(MSEC)
})
```

**Throughput**: 115200 baud (8N1) = 11,520 bytes/sec effective [S3]. A typical Task Telemetry Contract JSON is 300–600 bytes → a single contract transmits in ~30–55 ms. Not a bottleneck; the link can comfortably sustain 15–30 contracts/second.

**USB device naming on Pi** [S1]:

```
/dev/ttyACM0  ← user port (telemetry/commands)
/dev/ttyACM1  ← system port (upload)
```

Udev rule for stable naming [S1]:
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="2888", MODE="0666", SYMLINK+="vex_brain"
```

**Alternative path — PROS RS-485 Smart Port** [S4]:

Stage 2 only. `pros::Serial` opens any of the 21 Smart Ports as RS-485 at up to 921,600 baud (8× USB serial). A Pi connected via RS-485 transceiver gets a second, higher-speed, isolated data channel — the USB port stays free for monitoring/upload. Useful if USB bandwidth becomes a constraint with high-frequency multi-motor streaming.

**SD card fallback (untethered runs)** [S5][S6]:

When the Pi is not connected (battery-powered autonomous run), the V5 Brain can write directly to a FAT32 SD card (≤32GB):

```python
# V5 Brain — SD card logging
from vex import *
brain = Brain()

if brain.sdcard.is_inserted():
    with open("/sdcard/session_001.jsonl", "a") as f:
        f.write(json.dumps(contract) + '\n')
```

After the run, eject the SD card, insert into a reader, and transfer to the Pi or laptop manually.

---

### 2. Saving Telemetry on the Raspberry Pi

**Format recommendation — JSONL (newline-delimited JSON)** [S7][S8]:

JSONL (one JSON object per line, no outer array) is the standard for edge telemetry:
- Append-only, O(1) writes, no schema migration
- Directly consumable by the Anthropic Batch API (`POST /v1/messages/batches` accepts JSON arrays of requests; JSONL is the output format)
- Grep-able, human-readable, loadable in Pandas with `pd.read_json(file, lines=True)`
- Rotation per session keeps file sizes manageable

**Pi-side writer pattern**:

```python
# Pi: serial_bridge.py
import serial, json, pathlib
from datetime import datetime

SESSION_DIR = pathlib.Path("/home/pi/telemetry")
SESSION_DIR.mkdir(exist_ok=True)

session_file = SESSION_DIR / f"session_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
port = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)

with session_file.open('a') as log:
    for line in port:
        try:
            contract = json.loads(line.strip())
            log.write(json.dumps(contract) + '\n')
            log.flush()          # flush after each contract
            process_contract(contract)
        except json.JSONDecodeError:
            pass                 # skip malformed lines
```

**Storage sizing**: Each session (≤10 task primitives) produces <10 KB of JSONL. A Raspberry Pi 5 with a 32GB microSD card can hold ~3 million sessions before running out of space — retention is not a practical concern for the capstone.

**Why not SQLite?** [S8][S9]: SQLite is slower for inserts than raw file writes on Pi's SD card. Useful if you need indexed queries across sessions; unnecessary for the capstone's sequential task flow.

---

### 3. Transferring Telemetry to an External LLM

Two complementary transfer modes:

#### Mode A — Real-time (demo/interactive, Stage 1)

After each completed contract, the Pi calls the Claude API synchronously:

```python
# Pi: llm_loop.py
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

def revise_self_model(contract: dict, current_model: dict) -> dict:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        system="You are the self-model revision agent for a VEX V5 robot...",
        messages=[{
            "role": "user",
            "content": f"Task contract:\n{json.dumps(contract, indent=2)}\n\n"
                       f"Current self-model:\n{json.dumps(current_model, indent=2)}\n\n"
                       "Identify the root cause of each gap residual and produce a revised self-model."
        }]
    )
    return json.loads(response.content[0].text)
```

**Latency**: Claude API round-trip is 1–4 seconds — acceptable for the capstone's slow manipulation tasks. The Pi's Wi-Fi handles the HTTPS connection to `api.anthropic.com`.

**Structured outputs** [S10]: Use `output_config={"format": {"type": "json_schema", "schema": SELF_MODEL_SCHEMA}}` (Sonnet 4.5 / Opus 4.8) to get schema-guaranteed JSON back from the revision agent — no parsing gymnastics.

#### Mode B — Batch (training/post-hoc, Stage 2)

After accumulating N sessions of JSONL, submit all contracts to the Anthropic Message Batches API for 50% cost savings [S11]:

```python
# Batch submission after N sessions
import anthropic, json

client = anthropic.Anthropic()

# Build batch requests from JSONL archive
requests = []
for session_file in sorted(Path("/home/pi/telemetry").glob("*.jsonl")):
    for line in session_file.read_text().splitlines():
        contract = json.loads(line)
        requests.append({
            "custom_id": f"{session_file.stem}_{contract['task']}",
            "params": {
                "model": "claude-opus-4-8",
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": build_revision_prompt(contract)}]
            }
        })

batch = client.messages.batches.create(requests=requests)
# Poll until complete (SLA: best-effort <1 hour, guaranteed 24h)
# Results streamed as JSONL from GET /v1/messages/batches/{id}/results
```

**Pricing**: Batch API costs 50% of standard rates (Claude Opus 4.8: $7.50/M input vs $15/M) — critical for running hundreds of revision cycles across many sessions.

#### Mode C — File archive sync (laptop/server)

For bulk data handoff (training dataset accumulation):

```bash
# On Pi — rsync session JSONL files to laptop over Wi-Fi
rsync -avz /home/pi/telemetry/ david@laptop.local:/datasets/vex-v5-capstone/
```

Or upload to DigitalOcean Spaces (S3-compatible) using `boto3` after each session for cloud-durable archival.

---

### 4. End-to-End Pipeline Diagram

```
┌─────────────────────────────────────────────────────────┐
│  VEX V5 Brain (VEXcode Python, MicroPython)             │
│  motor.torque/current/position → json.dumps → stdout   │
│  SD card: backup write if Pi disconnected               │
└───────────────┬─────────────────────────────────────────┘
                │  USB serial 115200 baud (~11.5 KB/s)
                │  /dev/ttyACM0 on Pi
┌───────────────▼─────────────────────────────────────────┐
│  Raspberry Pi 5 (Python 3, pyserial)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ serial_bridge.py                                  │   │
│  │  readline() → json.loads() → session.jsonl write │   │
│  │  merge with vision_loop.py visual fields         │   │
│  └────────────────────┬─────────────────────────────┘   │
│                        │ completed contract dict         │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │ llm_loop.py                                      │   │
│  │  Mode A: claude.messages.create() → revision    │   │
│  │  Mode B: batch JSONL queue → batches.create()   │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────┬─────────────────────────────────────────┘
                │  HTTPS / Wi-Fi
┌───────────────▼─────────────────────────────────────────┐
│  External LLM System                                     │
│  Claude API (Anthropic): real-time or batch             │
│  Laptop: rsync JSONL archive for modeling               │
│  DigitalOcean Spaces: S3 durable storage (optional)     │
└─────────────────────────────────────────────────────────┘
```

---

## Constraints

1. **V5 Brain has no Wi-Fi** — all external network access must route through the Pi. Never call the LLM from V5 Brain code.
2. **VEX USB user port baud rate is fixed at 115200** — the Brain does not expose a baud-rate configuration to MicroPython user code. PROS Smart Port RS-485 is the escape hatch if higher throughput is needed.
3. **USB serial is single-channel shared** — you cannot upload code and stream telemetry simultaneously. During active demo, leave the USB in telemetry mode; upload code beforehand.
4. **VEX SD card requires FAT32, ≤32GB** — larger cards use exFAT by default, which the V5 Brain rejects. Format to FAT32 before use.
5. **Anthropic Batch API SLA is 24 hours** — do not use Mode B for anything that needs a result within minutes. Mode A (real-time) is the only path for live demo feedback loops.
6. **Pi requires separate power** — the Pi 5 draws up to 15W; cannot run off the V5 battery. Use a USB-C PD power bank.

---

## Solution Comparison

| Criteria | Mode A: Real-time Claude API | Mode B: Batch API | Mode C: File sync + manual |
|---|---|---|---|
| **Latency** | 1–4 seconds | Hours (best-effort) | Manual (minutes to hours) |
| **Cost** | Full price | 50% discount | Free (storage only) |
| **Use case** | Live demo feedback loop | Training data analysis | Archive / dataset curation |
| **Internet required** | Yes (Pi Wi-Fi) | Yes (after sessions) | No (rsync local only) |
| **Scale** | 1 contract at a time | Up to 100K requests/batch | Unlimited (filesystem) |
| **Implementation** | `anthropic.messages.create()` | `anthropic.messages.batches.create()` | `rsync` / `boto3` |
| **Stage** | Stage 1 (Jun 29 demo) | Stage 2 (post-demo) | Both |

---

## Recommendation

**For Stage 1 (Jun 29 demo)**: implement Mode A exclusively.

1. Flash V5 Brain with Python stub that emits one JSON line per completed task primitive via `sys.stdout`.
2. On Pi, run `serial_bridge.py` (pyserial readline → JSONL append to `session_<ts>.jsonl`).
3. After each contract write, call `client.messages.create()` with the contract JSON in the prompt (Mode A).
4. Parse the revised self-model from the response; write next motor command back to V5 via `port.write()`.
5. Store SD card backup on V5 as a silent fallback (check `brain.sdcard.is_inserted()` on startup).

**For Stage 2 (post-demo)**: add Mode B.

1. After N sessions, collect all session JSONL files.
2. Build batch request array (one request per contract per session).
3. Submit to Anthropic Batches API; poll for results; extract revised self-models.
4. Use results to evaluate self-model convergence across generations.

**Implementation outline (Stage 1)**:

```
Task: Implement V5 Brain serial telemetry stub
  → emit_telemetry(task, fields) → sys.stdout.write(json + '\n')
  → call after every motor action in grab/pull/throw sequences

Task: Implement Pi serial_bridge.py
  → open /dev/ttyACM0 at 115200 → readline loop → JSONL write + llm_loop call

Task: Implement Pi llm_loop.py
  → build_prompt(contract, model) → claude.messages.create() → parse revision
  → write revised model to shared state file
```

**Risks and mitigations**:
- *Serial line drops during demo*: wrap `readline()` in try/except; log malformed lines and continue. The JSONL file captures everything received before the drop.
- *API latency spikes*: add a 10-second timeout to `messages.create()`; if it exceeds the timeout, cache the contract and retry after the next task primitive.
- *SD card not inserted*: check `brain.sdcard.is_inserted()` at startup; print a warning to screen if absent (do not crash).
- *Pi Wi-Fi unavailable*: the loop degrades gracefully — telemetry still writes to JSONL locally. Submit batch post-hoc once connectivity is restored.

---

## Next Steps

- `/task-add Implement VEX V5 Brain Python telemetry stub (sys.stdout JSON emit)`
- `/task-add Implement Raspberry Pi serial_bridge.py (pyserial → JSONL writer)`
- `/task-add Implement Raspberry Pi llm_loop.py (Mode A real-time Claude API call)`
- `/task-add Add SD card fallback to V5 Brain telemetry stub`
- **Ingest**: `/wiki-ingest raw/research/vex-v5-telemetry-pipeline/index.md`
