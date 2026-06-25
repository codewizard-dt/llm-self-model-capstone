"""m1 gate — advisory LLM review of the irreducibly-human checks (Bucket 3).

The deterministic m1 invariants are enforced by `make test` (see
`tests/test_m1_handshake.py`). What a script *cannot* assert is judgment:

* Does the Gen-0 -> Gen-1 `reasoning` diff actually *explain* why each number
  moved, in prose a non-author can follow? (the self-model thesis)
* Is the grab cycle a *physically sensible* grab, not just a parseable one?

This script assembles those artifacts into a rubric prompt and asks the local
`claude` CLI (the project's Claude Code subscription runtime — ADR-08, no API
key) for a PASS/FLAG verdict. It is **advisory**: it always exits 0, and if the
`claude` CLI is missing or the call fails it prints SKIPPED and returns. The
human reviewer remains the gate of record; this is a second opinion, not a
substitute for the freeze sign-off.

Run via `make m1-judge` (or as part of `make m1`).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = CONTRACTS_ROOT / "fixtures"
CLAUDE_TIMEOUT_S = 120

RUBRIC = """\
You are a contract-freeze reviewer for milestone `m1` of a robotics self-model
project. The mechanical checks (schema round-trips, ranges, ack-pairing, cycle
shape) have ALREADY PASSED in an automated suite. Judge ONLY the two qualitative
questions below, then return a single JSON object and nothing else.

Q1 (self-model readability): Read the Gen-0 -> Gen-1 self-model diff. Does the
`reasoning` field explain, in prose a non-author could follow, WHY each changed
number moved — and is that change consistent with the gap shrinking? A bare
restatement of the new value with no rationale is a FLAG.

Q2 (grab-cycle sensibility): Read the grab-cycle command transcript. Is it a
physically sensible grab on a claw robot (approach, lower, close, lift, stop) —
not just a parseable sequence?

Return exactly:
{"verdict": "pass" | "flag", "q1_reasoning": "<one sentence>", "q2_grab": "<one sentence>", "notes": "<anything a human should double-check, or empty>"}

--- ARTIFACT 1: Gen-0 -> Gen-1 self-model diff ---
%(self_model_diff)s

--- ARTIFACT 2: grab-cycle transcript ---
%(grab_cycle)s
"""


def _self_model_diff() -> str:
    gen0 = json.loads((FIXTURES / "self_model_gen0.json").read_text())
    gen1 = json.loads((FIXTURES / "self_model_gen1.json").read_text())
    keep = ("generation", "gap_model", "reasoning")
    return json.dumps(
        {
            "gen0": {k: gen0.get(k) for k in keep},
            "gen1": {k: gen1.get(k) for k in keep},
        },
        indent=2,
    )


def _grab_cycle() -> str:
    return (FIXTURES / "control_command_grab_cycle.jsonl").read_text().strip()


def _build_prompt() -> str:
    return RUBRIC % {
        "self_model_diff": _self_model_diff(),
        "grab_cycle": _grab_cycle(),
    }


def _skip(reason: str) -> int:
    print(f"  m1-judge: SKIPPED — {reason}")
    print("  (advisory only; the human freeze sign-off remains the gate of record)")
    return 0


def _extract_json(text: str) -> dict | None:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def main() -> int:
    claude = shutil.which("claude")
    if claude is None:
        return _skip("`claude` CLI not on PATH")

    print("  m1-judge: asking the local Claude Code runtime for an advisory verdict…")
    try:
        result = subprocess.run(
            [claude, "-p", _build_prompt()],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return _skip(f"claude did not respond within {CLAUDE_TIMEOUT_S}s")
    except OSError as exc:
        return _skip(f"could not invoke claude: {exc}")

    if result.returncode != 0:
        return _skip(f"claude exited {result.returncode}: {result.stderr.strip()[:200]}")

    verdict = _extract_json(result.stdout)
    if verdict is None:
        print("  m1-judge: could not parse a verdict; raw response below:")
        print("  " + result.stdout.strip().replace("\n", "\n  "))
        return 0

    mark = "PASS" if verdict.get("verdict") == "pass" else "FLAG"
    print(f"  m1-judge (advisory): {mark}")
    for key in ("q1_reasoning", "q2_grab", "notes"):
        if verdict.get(key):
            print(f"    - {key}: {verdict[key]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
