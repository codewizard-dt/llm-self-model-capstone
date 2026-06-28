from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from contracts import ContractLine, SelfModel, TaskEnvelope
from self_model_generator.loop_runner import run_full_loop

ROOT = Path(__file__).resolve().parents[2]
SELF_MODEL = ROOT / "contracts" / "fixtures" / "self_model_gen0.json"
PARTS = ROOT / "contracts" / "parts_catalog.json"
SESSION = ROOT / "contracts" / "fixtures" / "session_example.jsonl"
DELIVER_BALL = ROOT / "robot" / "ros2-runtime" / "fixtures" / "contract_deliver_ball.json"


def test_run_full_loop_writes_approved_artifacts(tmp_path: Path) -> None:
    manifest = run_full_loop(
        self_model_path=SELF_MODEL,
        parts_catalog_path=PARTS,
        contract_jsonl_path=SESSION,
        out_dir=tmp_path,
        provenance="fixture",
    )

    expected_artifacts = {
        "gap_summary": tmp_path / "gap_summary.json",
        "self_model_packet": tmp_path / "self_model_packet.md",
        "candidate_self_model": tmp_path / "candidate_self_model.json",
        "generator_handoff": tmp_path / "generator_handoff.json",
        "critic_report": tmp_path / "critic_report.json",
        "task_envelope": tmp_path / "task_envelope.json",
        "manifest": tmp_path / "manifest.json",
    }
    assert manifest["artifacts"] == {key: str(path) for key, path in expected_artifacts.items()}
    for path in expected_artifacts.values():
        assert path.exists(), path

    saved_manifest = json.loads(expected_artifacts["manifest"].read_text())
    assert saved_manifest == manifest
    assert saved_manifest["success"] is True
    assert saved_manifest["critic_approved"] is True
    assert saved_manifest["inputs"]["contract_jsonl"] == str(SESSION)
    assert saved_manifest["source"]["provenance"] == "fixture"
    assert saved_manifest["source"]["contract_line_count"] == 4
    assert saved_manifest["generation"] == {"parent": 0, "candidate": 1}

    candidate = SelfModel.model_validate_json(
        expected_artifacts["candidate_self_model"].read_text()
    )
    assert candidate.generation == 1
    assert candidate.parent_generation == 0
    assert candidate.reasoning

    critic_report = json.loads(expected_artifacts["critic_report"].read_text())
    assert {review["critic"] for review in critic_report["reviews"]} == {
        "physics",
        "torque",
        "com_geometry",
    }
    assert all(review["verdict"] == "pass" for review in critic_report["reviews"])

    envelope = TaskEnvelope.model_validate_json(expected_artifacts["task_envelope"].read_text())
    assert envelope.contract.generation == candidate.generation
    assert [step[0] for step in envelope.outline.method_plan()] == [
        "locate_nearest_apriltag",
        "pickup_ball",
        "lift",
        "move_to_tag",
        "release",
    ]
    packet = expected_artifacts["self_model_packet"].read_text()
    assert "[FIXTURE-BACKED: F10 residual summary]" in packet
    assert "force_error_N" in packet


def test_live_loop_requires_hardware_source_path(tmp_path: Path) -> None:
    contract_jsonl = tmp_path / "operator_results.jsonl"
    line = _live_pickup_line(raw_session_path=None)
    contract_jsonl.write_text(line.model_dump_json() + "\n")

    with pytest.raises(ValueError, match="raw_session_path"):
        run_full_loop(
            self_model_path=SELF_MODEL,
            parts_catalog_path=PARTS,
            contract_jsonl_path=contract_jsonl,
            out_dir=tmp_path / "out",
            expected_run_id="live-run-1",
            expected_session_id="live-session-1",
            provenance="live",
        )


def test_live_loop_accepts_run_scoped_hardware_source(tmp_path: Path) -> None:
    contract_jsonl = tmp_path / "operator_results.jsonl"
    line = _live_pickup_line(raw_session_path="telemetry/live-run-1/operator_results.jsonl")
    contract_jsonl.write_text(line.model_dump_json() + "\n")

    manifest = run_full_loop(
        self_model_path=SELF_MODEL,
        parts_catalog_path=PARTS,
        contract_jsonl_path=contract_jsonl,
        out_dir=tmp_path / "out",
        expected_run_id="live-run-1",
        expected_session_id="live-session-1",
        provenance="live",
    )

    assert manifest["success"] is True
    assert manifest["source"]["run_ids"] == ["live-run-1"]
    assert manifest["source"]["raw_session_paths"] == [
        "telemetry/live-run-1/operator_results.jsonl"
    ]
    assert Path(manifest["artifacts"]["task_envelope"]).exists()


def _live_pickup_line(*, raw_session_path: str | None) -> ContractLine:
    payload: dict[str, Any] = json.loads(DELIVER_BALL.read_text())
    payload["session_id"] = "live-session-1"
    payload["run_id"] = "live-run-1"
    payload["round"] = 1
    payload["task"] = "pickup_ball"
    payload["gap"] = {"force_error_N": -2.0, "duration_error_s": 0.2}
    payload["outcome"] = {
        "method": "pickup_ball",
        "success": False,
        "reason": "grab_not_confirmed",
        "command": "grab",
        "has_object": False,
    }
    payload["source"] = {
        "raw_session_path": raw_session_path,
        "brain_start_ms": 100,
        "brain_end_ms": 200,
        "pi_received_ms": 210,
        "telemetry_sample_count": 3,
    }
    return ContractLine.model_validate(payload)
