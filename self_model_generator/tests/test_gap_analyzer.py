from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from contracts import ContractLine
from self_model_generator.gap_analyzer import (
    analyze_contract_lines,
    build_gap_summary_from_jsonl,
)

ROOT = Path(__file__).resolve().parents[2]
DELIVER_BALL = ROOT / "robot" / "ros2-runtime" / "fixtures" / "contract_deliver_ball.json"


def _deliver_ball_line(
    *,
    round_id: int,
    method: str,
    success: bool,
    reason: str,
    command: str | None = None,
    has_object: bool | None = None,
    gap: dict[str, float] | None = None,
    vision: dict[str, Any] | None = None,
    source_path: str | None = "proof/live/run_42",
) -> ContractLine:
    payload = json.loads(DELIVER_BALL.read_text())
    payload["session_id"] = "run_42"
    payload["round"] = round_id
    payload["gap"] = gap or payload["gap"]
    payload["outcome"] = {
        "method": method,
        "success": success,
        "reason": reason,
        "command": command,
        "has_object": has_object,
    }
    if vision is not None:
        payload["vision"] = vision
    payload["source"] = {
        "raw_session_path": source_path,
        "brain_start_ms": 100,
        "brain_end_ms": 200,
        "pi_received_ms": 210,
        "telemetry_sample_count": 3,
    }
    return ContractLine.model_validate(payload)


def _diagnosis(summary: dict[str, Any], code: str) -> dict[str, Any]:
    matches = [item for item in summary["diagnoses"] if item["code"] == code]
    assert matches, summary["diagnoses"]
    return matches[0]


def test_pickup_advanced_before_grab_is_diagnosed_from_contract_evidence() -> None:
    lines = [
        _deliver_ball_line(
            round_id=1,
            method="pickup_ball",
            success=False,
            reason="opening_claw",
            command="release",
            has_object=False,
        ),
        _deliver_ball_line(
            round_id=2,
            method="lift",
            success=True,
            reason="operator_lift",
            command="lift",
            has_object=False,
        ),
    ]

    summary = analyze_contract_lines(lines)

    diagnosis = _diagnosis(summary, "PICKUP_ADVANCED_BEFORE_GRAB")
    assert diagnosis["severity"] == "error"
    assert diagnosis["evidence"]["methods"] == ["pickup_ball", "lift"]
    assert diagnosis["evidence"]["pickup_reason"] == "opening_claw"
    assert "task_step_timeout_s" in diagnosis["recommended_runtime_knobs"]
    assert "pickup_grab_settle_s" in diagnosis["recommended_runtime_knobs"]
    assert summary["generator_handoff"]["blocked"] is False
    assert "runtime_config" in summary["generator_handoff"]["candidate_update_scope"]


def test_missing_object_confirmation_recommends_known_pickup_knobs() -> None:
    line = _deliver_ball_line(
        round_id=7,
        method="pickup_ball",
        success=False,
        reason="grab_not_confirmed",
        command="grab",
        has_object=False,
        vision={
            "object_detected": True,
            "object_bbox": [300, 210, 68, 62],
            "apriltag_pose": {"x": 0.38, "y": 0.01, "heading": 0.03},
            "bbox_iou": None,
        },
    )

    summary = analyze_contract_lines([line])

    diagnosis = _diagnosis(summary, "OBJECT_NOT_CONFIRMED")
    assert diagnosis["severity"] == "error"
    assert diagnosis["evidence"]["method"] == "pickup_ball"
    assert diagnosis["evidence"]["reason"] == "grab_not_confirmed"
    assert diagnosis["evidence"]["has_object"] is False
    assert "end_effector_object_max_closed_deg" in diagnosis["recommended_runtime_knobs"]
    assert "pickup_max_attempts" in diagnosis["recommended_runtime_knobs"]

    visible_diagnosis = _diagnosis(summary, "BALL_STILL_VISIBLE_AFTER_GRAB")
    assert "ball_capture_forward_m" in visible_diagnosis["recommended_runtime_knobs"]
    assert "ball_capture_lateral_m" in visible_diagnosis["recommended_runtime_knobs"]


def test_residuals_and_source_context_are_preserved_for_generator_packet() -> None:
    lines = [
        _deliver_ball_line(
            round_id=1,
            method="pickup_ball",
            success=False,
            reason="moving_to_ball",
            command="drive",
            has_object=False,
            gap={"force_error_N": -2.0, "duration_error_s": 0.2},
        ),
        _deliver_ball_line(
            round_id=2,
            method="pickup_ball",
            success=True,
            reason="ball_grabbed",
            command="grab",
            has_object=True,
            gap={"force_error_N": 1.0, "duration_error_s": 0.4},
        ),
    ]

    summary = analyze_contract_lines(lines)

    assert summary["kind"] == "gap_summary"
    assert summary["source"]["contract_line_count"] == 2
    assert summary["source"]["session_ids"] == ["run_42"]
    assert summary["source"]["raw_session_paths"] == ["proof/live/run_42"]
    assert summary["residuals"]["force_error_N"] == {
        "count": 2,
        "latest": 1.0,
        "mean": -0.5,
        "mean_abs": 1.5,
        "max_abs": 2.0,
    }
    assert summary["residuals"]["duration_error_s"]["latest"] == 0.4
    assert "gap_model" in summary["generator_handoff"]["candidate_update_scope"]


def test_jsonl_gap_summary_builder_validates_contract_lines(tmp_path: Path) -> None:
    lines = [
        _deliver_ball_line(
            round_id=1,
            method="pickup_ball",
            success=False,
            reason="grab_failed",
            has_object=False,
        ),
    ]
    path = tmp_path / "contract.jsonl"
    path.write_text("\n".join(line.model_dump_json() for line in lines) + "\n")

    summary = build_gap_summary_from_jsonl(path)

    assert _diagnosis(summary, "OBJECT_NOT_CONFIRMED")["evidence"]["reason"] == "grab_failed"
