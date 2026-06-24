"""m1 gate — mechanical invariants the human reviewer used to eyeball.

These assertions encode the parts of the m1 manual-review checklist that are
deterministic, so the human gate shrinks to the irreducible judgment calls
(prose readability + freeze sign-off, covered advisorily by `scripts/m1_review.py`).

Three buckets of checks live here:

* **Ack-pairing (B)** — every command/heartbeat line in a happy-path cycle
  fixture is answered by exactly one `ack` line, in order, whose `ack` equals the
  preceding `seq` and whose `state == "ok"`. Round-trip tests only prove each
  line *parses*; this proves the transcript is a coherent command/ack handshake.
* **Cycle shape (C)** — the grab cycle actually grabs (claw `close` bracketed by
  arm moves, ending in `stop`); the flywheel cycle spins up then coasts to 0
  before stopping.
* **Telemetry gap sanity (A', substituted)** — the as-shipped `ContractLine` has
  no `observed` block (the F10 gap-analyzer derives `gap` from `motor_samples`),
  so `gap == predicted - observed` is *not* recomputable at the contract layer.
  Instead we assert the weaker, genuinely-checkable invariant: every session
  line carries a non-empty `predicted` and `gap`, and every `gap` value is
  finite (no NaN/inf leaking into a frozen fixture).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

# contracts/tests/test_m1_handshake.py -> parents[1] is the contracts root.
CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = CONTRACTS_ROOT / "fixtures"

GRAB_FIXTURE = FIXTURES_DIR / "control_command_grab_cycle.jsonl"
FLYWHEEL_FIXTURE = FIXTURES_DIR / "control_command_flywheel_cycle.jsonl"
SESSION_FIXTURE = FIXTURES_DIR / "session_example.jsonl"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- B: ack-pairing handshake ------------------------------------------------


@pytest.mark.parametrize("fixture", [GRAB_FIXTURE, FLYWHEEL_FIXTURE])
def test_cycle_is_a_coherent_command_ack_handshake(fixture: Path) -> None:
    """Each cmd/heartbeat line is immediately answered by its own ok ack."""
    lines = _read_jsonl(fixture)
    assert lines, f"{fixture.name} is empty"
    assert len(lines) % 2 == 0, f"{fixture.name}: every command needs an ack line"

    for i in range(0, len(lines), 2):
        sent, ack = lines[i], lines[i + 1]
        assert sent["type"] in {"cmd", "heartbeat"}, (
            f"{fixture.name} line {i}: expected a cmd/heartbeat, got {sent['type']!r}"
        )
        assert ack["type"] == "ack", (
            f"{fixture.name} line {i + 1}: expected an ack, got {ack['type']!r}"
        )
        assert ack["ack"] == sent["seq"], (
            f"{fixture.name}: ack {ack['ack']} does not answer seq {sent['seq']}"
        )
        assert ack["state"] == "ok", (
            f"{fixture.name}: seq {sent['seq']} was not acked ok (state={ack['state']!r})"
        )


def test_cycle_seqs_are_strictly_monotonic() -> None:
    """Command seqs ascend without gaps so a reader can detect a dropped line."""
    for fixture in (GRAB_FIXTURE, FLYWHEEL_FIXTURE):
        seqs = [ln["seq"] for ln in _read_jsonl(fixture) if "seq" in ln]
        assert seqs == sorted(seqs), f"{fixture.name}: seqs not ascending: {seqs}"
        assert len(seqs) == len(set(seqs)), f"{fixture.name}: duplicate seq"


# --- C: cycle shape ----------------------------------------------------------


def _commands(path: Path) -> list[dict]:
    return [ln for ln in _read_jsonl(path) if ln.get("type") == "cmd"]


def test_grab_cycle_actually_grabs() -> None:
    """drive -> arm(lower) -> claw(close) -> arm(lift) -> stop."""
    cmds = _commands(GRAB_FIXTURE)
    verbs = [c["cmd"] for c in cmds]

    assert verbs[-1] == "stop", f"grab cycle must end in stop, got {verbs[-1]!r}"

    claw_idxs = [i for i, c in enumerate(cmds) if c["cmd"] == "claw"]
    assert claw_idxs, "grab cycle never actuates the claw"
    closes = [i for i in claw_idxs if cmds[i]["state"] == "close"]
    assert closes, "grab cycle never closes the claw"
    close_at = closes[0]

    arm_idxs = [i for i, c in enumerate(cmds) if c["cmd"] == "arm"]
    assert any(i < close_at for i in arm_idxs), "no arm move before the claw close"
    assert any(i > close_at for i in arm_idxs), "no arm lift after the claw close"


def test_flywheel_cycle_spins_up_then_coasts() -> None:
    """flywheel(rpm>0) -> flywheel(rpm==0 coast) -> stop, with a drive approach."""
    cmds = _commands(FLYWHEEL_FIXTURE)
    verbs = [c["cmd"] for c in cmds]

    assert "drive" in verbs, "flywheel cycle has no drive approach"
    assert verbs[-1] == "stop", f"flywheel cycle must end in stop, got {verbs[-1]!r}"

    fly = [c for c in cmds if c["cmd"] == "flywheel"]
    assert any(c["rpm"] > 0 for c in fly), "flywheel never spins up"
    assert fly[-1]["rpm"] == 0.0, "flywheel never coasts back to 0 before stop"


# --- A' (substituted): telemetry gap structural sanity -----------------------


def test_session_lines_carry_finite_predicted_and_gap() -> None:
    """Every frozen telemetry line has a non-empty predicted + finite gap.

    NOT a gap-arithmetic check: the contract has no `observed` block, so
    `gap == predicted - observed` is the F10 gap-analyzer's job, not the
    contract's. This guards the frozen fixtures against empty/NaN gap blocks.
    """
    lines = _read_jsonl(SESSION_FIXTURE)
    assert lines, "session_example.jsonl is empty"

    for i, ln in enumerate(lines):
        assert ln.get("predicted"), f"session line {i}: empty predicted block"
        gap = ln.get("gap")
        assert gap, f"session line {i}: empty gap block"
        for key, value in gap.items():
            assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                f"session line {i}: gap[{key!r}] is not numeric: {value!r}"
            )
            assert math.isfinite(value), f"session line {i}: gap[{key!r}] is not finite"
