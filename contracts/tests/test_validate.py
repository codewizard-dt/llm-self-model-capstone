"""Tests for the `contracts.validate` entrypoint.

The F1 (`session_*.jsonl → ContractLine`) and F2 (`self_model_*.json → SelfModel`)
dispatches are exercised end-to-end by `make validate` over the committed fixtures; the
additive F3 dispatch is covered here for the `parts_catalog.json` round-trip against
`PartsCatalog`, the per-fixture buildability assertion, and the non-buildable
fixture → non-zero exit case. The additive F19 fourth dispatch is covered here for
the three committed control-command fixtures, the exhaustive `FaultCode` coverage, the
stale-vs-rejected distinction (D6/D17), and the F1-glob-narrowing invariant (D15) —
including type-routing on a deliberately-bad cmd line and cross-dispatch isolation. The
pilot fixture dispatches are covered here for committed model/adapter round-trips, trace
event coverage, and temp-root rejection paths for invalid pilot JSON/JSONL. The committed
fixtures stay clean — every mutation case is constructed in a temp fixtures dir.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from contracts import (
    TTL_MS_MAX,
    AckLine,
    ContractLine,
    ControlLine,
    FaultCode,
    PartsCatalog,
    PilotAssertion,
    PilotDecision,
    PilotObservation,
    PilotSkillCommand,
    PilotTraceRecord,
    SelfModel,
    validate_config,
)
from contracts.validate import main

# contracts/tests/test_validate.py -> parents[1] is the contracts root.
CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CONTRACTS_ROOT.parent
CATALOG_JSON = CONTRACTS_ROOT / "parts_catalog.json"
FIXTURES_DIR = CONTRACTS_ROOT / "fixtures"
SCHEMAS_DIR = CONTRACTS_ROOT / "schemas"
TELEMETRY_FIXTURE_DIR = REPO_ROOT / "telemetry-fixtures" / "grab-align-baseline"

GRAB_FIXTURE = FIXTURES_DIR / "control_command_grab_cycle.jsonl"
FLYWHEEL_FIXTURE = FIXTURES_DIR / "control_command_flywheel_cycle.jsonl"
REJECTIONS_FIXTURE = FIXTURES_DIR / "control_command_rejections.jsonl"
PILOT_OBSERVATION_FIXTURE = FIXTURES_DIR / "pilot_observation_example.json"
PILOT_SKILL_COMMAND_FIXTURE = FIXTURES_DIR / "pilot_skill_command_examples.jsonl"
PILOT_ASSERTION_FIXTURE = FIXTURES_DIR / "pilot_assertion_examples.jsonl"
PILOT_DECISION_FIXTURE = FIXTURES_DIR / "pilot_decision_examples.jsonl"
PILOT_TRACE_FIXTURE = FIXTURES_DIR / "pilot_trace_example.jsonl"
TELEMETRY_CONTRACT_FIXTURE = TELEMETRY_FIXTURE_DIR / "contract.jsonl"
TELEMETRY_MANIFEST_FIXTURE = TELEMETRY_FIXTURE_DIR / "manifest.json"

_control_line_adapter: TypeAdapter[ControlLine] = TypeAdapter(ControlLine)
_pilot_skill_command_adapter: TypeAdapter[PilotSkillCommand] = TypeAdapter(PilotSkillCommand)
_pilot_trace_record_adapter: TypeAdapter[PilotTraceRecord] = TypeAdapter(PilotTraceRecord)


def _iter_jsonl(path: Path) -> list[dict]:
    return [json.loads(raw) for raw in path.read_text().splitlines() if raw.strip()]


# --- catalog round-trip -----------------------------------------------------


def test_committed_parts_catalog_json_validates_against_model():
    catalog = PartsCatalog.model_validate_json(CATALOG_JSON.read_text())
    assert catalog.schema_version == "1.0"


# --- committed fixtures are buildable through the validate path --------------


def test_committed_self_model_fixtures_report_buildable():
    fixtures = sorted(FIXTURES_DIR.glob("self_model_*.json"))
    assert fixtures, "expected committed self_model_*.json fixtures"
    for path in fixtures:
        model = SelfModel.model_validate_json(path.read_text())
        verdict = validate_config(model.config)
        assert verdict.buildable is True, f"{path.name} should be buildable"


def test_validate_entrypoint_exits_zero_over_committed_tree():
    # The real contracts tree: F1 jsonl + F2 self-models + the F3 catalog/buildability
    # dispatch all pass against the committed fixtures.
    assert main() == 0


def test_committed_telemetry_fixture_manifest_points_to_contract_jsonl():
    manifest = json.loads(TELEMETRY_MANIFEST_FIXTURE.read_text())
    assert manifest["run_id"] == "grab-align-baseline"
    assert manifest["task"] == "grab_align"
    assert "fixture-backed" in manifest["provenance"]
    assert "not real robot hardware" in manifest["provenance"]
    assert manifest["fixture_status"] == "committed_fixture"
    assert (
        manifest["canonical_evidence_path"]
        == "telemetry-fixtures/grab-align-baseline/contract.jsonl"
    )
    assert (REPO_ROOT / manifest["canonical_evidence_path"]).is_file()


def test_committed_telemetry_fixture_lines_validate_as_contract_lines():
    lines = [raw for raw in TELEMETRY_CONTRACT_FIXTURE.read_text().splitlines() if raw.strip()]
    assert lines, "expected telemetry fixture contract.jsonl to contain evidence lines"
    for line in lines:
        ContractLine.model_validate_json(line)


# --- pilot fixtures: committed examples validate ----------------------------


def test_committed_pilot_fixture_families_validate_against_models_and_adapters():
    observation = PilotObservation.model_validate_json(PILOT_OBSERVATION_FIXTURE.read_text())
    assert observation.bridge.last_heartbeat_age_ms == 38
    assert observation.bridge.estop is False
    assert observation.last_command is not None
    assert observation.last_result is not None
    assert observation.current_assertions

    commands = [
        _pilot_skill_command_adapter.validate_json(raw)
        for raw in PILOT_SKILL_COMMAND_FIXTURE.read_text().splitlines()
        if raw.strip()
    ]
    assert [command.skill for command in commands] == [
        "survey_scene",
        "approach_target",
        "center_object_in_gripper",
        "arm_to_angle",
        "claw_close",
        "stop",
    ]

    assertions = [
        PilotAssertion.model_validate_json(raw)
        for raw in PILOT_ASSERTION_FIXTURE.read_text().splitlines()
        if raw.strip()
    ]
    assert {assertion.assertion_id for assertion in assertions} >= {
        "assert-bridge-fresh",
        "assert-cube-visible",
        "assert-gripper-empty",
    }
    assert any(
        evidence.source == "telemetry"
        for assertion in assertions
        for evidence in assertion.evidence
    )
    assert any(
        evidence.source == "vision" for assertion in assertions for evidence in assertion.evidence
    )
    assert any(
        evidence.source == "bridge" for assertion in assertions for evidence in assertion.evidence
    )

    decisions = [
        PilotDecision.model_validate_json(raw)
        for raw in PILOT_DECISION_FIXTURE.read_text().splitlines()
        if raw.strip()
    ]
    assert [decision.action for decision in decisions] == ["continue", "retry", "stop_success"]
    assert decisions[0].command is not None
    assert decisions[1].retry_of_command_id == "cmd-approach-cube-red-1-a"
    assert decisions[2].stop_reason == "task complete"


def test_committed_pilot_trace_fixture_covers_all_event_variants():
    records = [
        _pilot_trace_record_adapter.validate_json(raw)
        for raw in PILOT_TRACE_FIXTURE.read_text().splitlines()
        if raw.strip()
    ]
    assert [record.event for record in records] == [
        "observation",
        "decision",
        "command",
        "result",
        "assertion",
        "stop",
    ]
    assert {record.session_id for record in records} == {"pilot-replay-001"}
    assert [record.seq for record in records] == [1, 2, 3, 4, 5, 6]


# --- unbuildable fixture is rejected with a readable reason ------------------


def _write_self_model(path: Path, config: dict) -> None:
    base = json.loads((FIXTURES_DIR / "self_model_gen0.json").read_text())
    base["config"] = config
    path.write_text(json.dumps(base))


def test_unbuildable_fixture_makes_entrypoint_exit_nonzero(tmp_path, monkeypatch, capsys):
    # Stand up a temp contracts root: copy the committed catalog, and add an
    # unbuildable fixture (flywheel + 200rpm cartridge violates FLYWHEEL_CARTRIDGE).
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (tmp_path / "parts_catalog.json").write_text(CATALOG_JSON.read_text())
    unbuildable = json.loads((FIXTURES_DIR / "self_model_gen0.json").read_text())["config"]
    unbuildable["motor_allocation"] = "2drive+1flywheel"
    unbuildable["end_effector"] = "flywheel"
    unbuildable["cartridge"] = "200rpm"
    _write_self_model(fixtures / "self_model_bad.json", unbuildable)

    # Sanity: the constructed config really is unbuildable.
    bad_model = SelfModel.model_validate_json((fixtures / "self_model_bad.json").read_text())
    assert validate_config(bad_model.config).buildable is False

    # Redirect the entrypoint at the temp root by pointing parents[2] resolution there.
    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "self_model_bad.json" in err
    assert "not buildable" in err
    assert "600rpm" in err  # the flywheel-cartridge violation message


class _PathStub:
    """Make `Path(__file__)` resolve to a chosen path inside the entrypoint only.

    `validate.main` computes its contracts root as `Path(__file__).resolve().parents[2]`.
    We swap in a Path whose `parents[2]` is the temp root, while leaving every other
    `Path(...)` call (the glob/read_text on real sub-paths) behaving normally.
    """

    def __init__(self, fake_file: Path) -> None:
        self._fake_file = fake_file

    def __call__(self, arg):
        # The entrypoint's only `Path(__file__)` call — return the fake file path.
        return self._fake_file


# --- F19 fourth dispatch: per-fixture round-trip -----------------------------


def test_control_grab_cycle_round_trips():
    """Every line of control_command_grab_cycle.jsonl parses through the F19 dispatch.

    Command/heartbeat lines validate as `ControlLine`; ack lines validate as
    `AckLine`. Mirrors the per-line type routing inside `validate.main()`.
    """

    objs = _iter_jsonl(GRAB_FIXTURE)
    assert len(objs) == 12  # 6 command/heartbeat lines + 6 acks
    seen_cmds: list[str] = []
    for obj in objs:
        if obj.get("type") == "ack":
            AckLine.model_validate(obj)
        else:
            line = _control_line_adapter.validate_python(obj)
            cmd = obj.get("cmd") or obj["type"]
            seen_cmds.append(cmd)
            # Envelope invariants (D5/D8): v=1, ttl_ms in (0, TTL_MS_MAX]
            assert obj["v"] == 1
            assert 1 <= obj["ttl_ms"] <= TTL_MS_MAX
            assert line is not None
    assert seen_cmds == ["heartbeat", "drive", "arm", "claw", "arm", "stop"]


def test_control_flywheel_cycle_round_trips():
    """Every line of control_command_flywheel_cycle.jsonl parses through the F19 dispatch."""

    objs = _iter_jsonl(FLYWHEEL_FIXTURE)
    assert len(objs) == 10  # 5 command/heartbeat lines + 5 acks
    seen_cmds: list[str] = []
    for obj in objs:
        if obj.get("type") == "ack":
            AckLine.model_validate(obj)
        else:
            _control_line_adapter.validate_python(obj)
            seen_cmds.append(obj.get("cmd") or obj["type"])
    assert seen_cmds == ["heartbeat", "drive", "flywheel", "flywheel", "stop"]


def test_control_rejections_round_trips():
    """Every line of control_command_rejections.jsonl parses as `AckLine`."""

    objs = _iter_jsonl(REJECTIONS_FIXTURE)
    assert len(objs) == 9
    rejected = 0
    stale = 0
    for obj in objs:
        assert obj["type"] == "ack"
        ack = AckLine.model_validate(obj)
        assert ack.fault is not None  # every non-ok ack carries a fault
        if ack.state == "rejected":
            rejected += 1
        elif ack.state == "stale":
            stale += 1
        else:  # pragma: no cover — rejections fixture never carries state='ok'
            raise AssertionError(f"unexpected state {ack.state!r} in rejections fixture")
    assert rejected == 8
    assert stale == 1


# --- F19 fourth dispatch: exhaustive FaultCode coverage (D7) ----------------


def test_exhaustive_faultcode_coverage():
    """Acc-exhaustive-faultcode (D7): the set of `fault` values parsed from
    control_command_rejections.jsonl equals `{fc.value for fc in FaultCode}` —
    no missing, no extra, no duplicate."""

    objs = _iter_jsonl(REJECTIONS_FIXTURE)
    faults = [obj["fault"] for obj in objs]
    assert len(faults) == len(set(faults)), "rejections fixture must not duplicate faults"
    assert set(faults) == {fc.value for fc in FaultCode}


# --- F19 fourth dispatch: stale vs rejected distinction (D6/D17) ------------


def test_stale_vs_rejected_distinction():
    """Acc-stale-vs-rejected-distinction: the ttl_expired row uses `state: "stale"`;
    every other rejected-fault row uses `state: "rejected"`."""

    by_fault: dict[str, str] = {}
    for obj in _iter_jsonl(REJECTIONS_FIXTURE):
        by_fault[obj["fault"]] = obj["state"]
    assert by_fault["ttl_expired"] == "stale"
    for fault, state in by_fault.items():
        if fault == "ttl_expired":
            continue
        assert state == "rejected", f"{fault!r} should be rejected, got {state!r}"


# --- F19 fourth dispatch: entrypoint exit-code paths via a temp root --------


def _stand_up_temp_root(tmp_path: Path) -> Path:
    """Mirror the temp-root setup used by `test_unbuildable_fixture_*` above.

    Copies the committed catalog so the F3 dispatch stays happy; the fixtures
    dir is empty and the caller seeds whatever fixture files it needs.
    """

    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (tmp_path / "parts_catalog.json").write_text(CATALOG_JSON.read_text())
    return fixtures


def test_validate_main_rejects_bad_cmd(tmp_path, monkeypatch, capsys):
    """Acc-type-routing-rejects-bad-cmd: a control_command_*.jsonl line with
    `cmd: "drive"`, `vx: 0.9` (> MAX_LINEAR=0.35) makes `validate.main()` return 1
    and surface a `<file>:<lineno>: ...ValidationError...` line on stderr."""

    fixtures = _stand_up_temp_root(tmp_path)
    bad = (
        '{"v":1,"seq":1,"type":"cmd","cmd":"drive","sent_ms":1,"ttl_ms":200,'
        '"vx":0.9,"vy":0.0,"omega":0.0}\n'
    )
    (fixtures / "control_command_bad.jsonl").write_text(bad)

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "control_command_bad.jsonl:1:" in err
    # Pydantic's stringified ValidationError leads with "<N> validation error(s) for <model>"
    # and mentions the offending field — both invariants are load-bearing for the
    # plan's "ValidationError on stderr" surface (acc-type-routing-rejects-bad-cmd).
    assert "validation error" in err
    assert "vx" in err


def test_validate_main_rejects_bad_telemetry_fixture_line(tmp_path, monkeypatch, capsys):
    """Repo-level telemetry-fixtures/*/contract.jsonl must parse as ContractLine."""

    repo_root = tmp_path
    contracts_root = repo_root / "contracts"
    (contracts_root / "fixtures").mkdir(parents=True)
    (contracts_root / "parts_catalog.json").write_text(CATALOG_JSON.read_text())
    fixture_run = repo_root / "telemetry-fixtures" / "bad-run"
    fixture_run.mkdir(parents=True)
    (fixture_run / "contract.jsonl").write_text(
        '{"schema_version":"1.0","session_id":"bad","generation":0,'
        '"round":1,"task":"grab","predicted":{"success":true},"gap":{}}\n'
    )

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(contracts_root / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "telemetry-fixtures/bad-run/contract.jsonl:1:" in err
    assert "motor_samples" in err


def test_validate_main_rejects_unknown_cmd(tmp_path, monkeypatch, capsys):
    """Acc-cross-dispatch-isolation: a control_command_*.jsonl line with
    `cmd: "fly"` (out of vocabulary) makes `validate.main()` return 1 and the
    error is a ControlLine-side discriminator failure — NEVER a ContractLine
    error (D15 invariant — proves the F1 glob narrowing)."""

    fixtures = _stand_up_temp_root(tmp_path)
    bad = '{"v":1,"seq":1,"type":"cmd","cmd":"fly","sent_ms":1,"ttl_ms":200}\n'
    (fixtures / "control_command_grab_cycle.jsonl").write_text(bad)

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "control_command_grab_cycle.jsonl:1:" in err
    # The error mentions the inner cmd discriminator's closed vocabulary —
    # NOT a ContractLine validation error.
    assert "ContractLine" not in err


def test_validate_main_rejects_unknown_pilot_decision_action(tmp_path, monkeypatch, capsys):
    fixtures = _stand_up_temp_root(tmp_path)
    bad = {
        "v": 1,
        "decision_id": "dec-bad-action",
        "decided_ms": 1,
        "action": "teleport",
        "rationale": "invalid decision action",
        "confidence": 0.5,
    }
    (fixtures / "pilot_decision_examples.jsonl").write_text(json.dumps(bad) + "\n")

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "pilot_decision_examples.jsonl:1:" in err
    assert "action" in err


def test_validate_main_rejects_unknown_pilot_skill_name(tmp_path, monkeypatch, capsys):
    fixtures = _stand_up_temp_root(tmp_path)
    bad = {
        "v": 1,
        "command_id": "cmd-unknown-skill",
        "issued_ms": 1,
        "skill": "fly_to_moon",
        "params": {},
    }
    (fixtures / "pilot_skill_command_examples.jsonl").write_text(json.dumps(bad) + "\n")

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "pilot_skill_command_examples.jsonl:1:" in err
    assert "fly_to_moon" in err


def test_validate_main_rejects_oversized_pilot_numeric_envelope(tmp_path, monkeypatch, capsys):
    fixtures = _stand_up_temp_root(tmp_path)
    bad = {
        "v": 1,
        "command_id": "cmd-too-fast",
        "issued_ms": 1,
        "skill": "approach_target",
        "params": {
            "target_id": "cube-red-1",
            "standoff_m": 0.18,
            "max_speed_mps": 99.0,
            "timeout_ms": 8000,
        },
    }
    (fixtures / "pilot_skill_command_examples.jsonl").write_text(json.dumps(bad) + "\n")

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "pilot_skill_command_examples.jsonl:1:" in err
    assert "max_speed_mps" in err


def test_validate_main_rejects_malformed_pilot_hardware_health(tmp_path, monkeypatch, capsys):
    fixtures = _stand_up_temp_root(tmp_path)
    bad = json.loads(PILOT_OBSERVATION_FIXTURE.read_text())
    bad["bridge"]["state"] = "stale"
    bad["bridge"]["last_heartbeat_age_ms"] = -1
    (fixtures / "pilot_observation_example.json").write_text(json.dumps(bad))

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "pilot_observation_example.json:" in err
    assert "last_heartbeat_age_ms" in err


def test_validate_main_rejects_malformed_pilot_trace_record(tmp_path, monkeypatch, capsys):
    fixtures = _stand_up_temp_root(tmp_path)
    bad = {
        "v": 1,
        "session_id": "pilot-replay-bad",
        "seq": 1,
        "monotonic_ms": 1,
        "event": "noop",
    }
    (fixtures / "pilot_trace_example.jsonl").write_text(json.dumps(bad) + "\n")

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "pilot_trace_example.jsonl:1:" in err
    assert "noop" in err


def test_glob_narrowed_protects_session_dispatch(tmp_path, monkeypatch, capsys):
    """Acc-glob-narrowed (D15 invariant): a control_command_*.jsonl line that is
    invalid-as-ContractLine yet valid-as-ControlLine produces no ContractLine
    errors. The F1 dispatch must not have attempted to parse it."""

    fixtures = _stand_up_temp_root(tmp_path)
    # A valid heartbeat (ControlLine) line. It is also a perfectly invalid
    # ContractLine line — ContractLine requires `schema_version`, `task`,
    # `motor_samples`, etc., none of which are present here.
    heartbeat = '{"v":1,"seq":1,"type":"heartbeat","sent_ms":1,"ttl_ms":200}\n'
    (fixtures / "control_command_heartbeat.jsonl").write_text(heartbeat)

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    # main() exits 0: the heartbeat is valid as a ControlLine; the F1 dispatch
    # never sees `control_command_*.jsonl` (narrowed glob), so no ContractLine
    # error is reported.
    assert main() == 0
    err = capsys.readouterr().err
    assert "ContractLine" not in err


def test_session_example_still_validates(tmp_path, monkeypatch):
    """Acc-glob-narrowed companion: copy session_example.jsonl into a temp tree
    alongside a control fixture, run `main()`, and assert it exits 0 — the
    narrowed glob still matches `session_*.jsonl`."""

    fixtures = _stand_up_temp_root(tmp_path)
    (fixtures / "session_example.jsonl").write_text(
        (FIXTURES_DIR / "session_example.jsonl").read_text()
    )
    (fixtures / "control_command_grab_cycle.jsonl").write_text(GRAB_FIXTURE.read_text())

    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 0


# --- F19: schema files are slice-1 outputs and stay byte-identical ----------


def test_schema_files_present_and_non_empty():
    """`schemas/control_command.json` and `schemas/ack_line.json` are slice-1
    outputs; this slice does not touch them. Asserting they remain present and
    non-empty is the in-tree complement to `make schema-check` (which guards
    byte-identity via `git diff --exit-code schemas/`)."""

    control_schema = SCHEMAS_DIR / "control_command.json"
    ack_schema = SCHEMAS_DIR / "ack_line.json"
    assert control_schema.is_file()
    assert ack_schema.is_file()
    assert control_schema.stat().st_size > 0
    assert ack_schema.stat().st_size > 0
