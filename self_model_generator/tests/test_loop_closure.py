from __future__ import annotations

import json
from pathlib import Path

import pytest
from contracts import ContractLine, PartsCatalog, SelfModel, TaskEnvelope
from self_model_generator.loop_closure import (
    export_task_envelope,
    generate_self_model_candidate,
    run_critic_panel,
)

ROOT = Path(__file__).resolve().parents[2]
SELF_MODEL = ROOT / "contracts" / "fixtures" / "self_model_gen0.json"
PARTS = ROOT / "contracts" / "parts_catalog.json"
SESSION = ROOT / "contracts" / "fixtures" / "session_example.jsonl"


def _current_model() -> SelfModel:
    return SelfModel.model_validate_json(SELF_MODEL.read_text())


def _parts_catalog() -> PartsCatalog:
    return PartsCatalog.model_validate_json(PARTS.read_text())


def _contract_lines() -> list[ContractLine]:
    return [
        ContractLine.model_validate_json(raw)
        for raw in SESSION.read_text().splitlines()
        if raw.strip()
    ]


def _gap_summary() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "kind": "gap_summary",
        "source": {
            "contract_line_count": 1,
            "generations": [0],
            "provenance": "fixture",
            "raw_session_paths": [],
            "round_range": [1, 1],
            "run_ids": [],
            "session_ids": ["session_20260624_141200"],
            "tasks": ["grab"],
        },
        "residuals": {
            "force_error_N": {
                "count": 1,
                "latest": -3.4,
                "mean": -3.4,
                "mean_abs": 3.4,
                "max_abs": 3.4,
            },
            "duration_error_s": {
                "count": 1,
                "latest": 0.2,
                "mean": 0.2,
                "mean_abs": 0.2,
                "max_abs": 0.2,
            },
        },
        "diagnoses": [
            {
                "code": "OBJECT_NOT_CONFIRMED",
                "severity": "error",
                "summary": "grab failed to confirm object",
                "evidence": {"method": "grab", "has_object": False},
                "recommended_runtime_knobs": ["pickup_grab_settle_s"],
            }
        ],
    }


def test_generator_emits_revised_self_model_from_gap_summary() -> None:
    candidate, handoff = generate_self_model_candidate(_current_model(), _gap_summary())

    assert candidate.generation == 1
    assert candidate.parent_generation == 0
    assert candidate.predictive["grab"]["grip_force_N"] == pytest.approx(11.3)
    assert candidate.gap_model["grab"]["force_error_N"] == pytest.approx(0.0)
    assert "predictive.grab.grip_force_N" in candidate.reasoning
    assert handoff["candidate_generation"] == 1
    assert handoff["evidence"]["gap_summary_kind"] == "gap_summary"


def test_critic_panel_reviews_candidate_with_three_lanes() -> None:
    candidate, _ = generate_self_model_candidate(_current_model(), _gap_summary())

    report = run_critic_panel(
        candidate,
        parts_catalog=_parts_catalog(),
        contract_lines=_contract_lines(),
        gap_summary=_gap_summary(),
    )

    assert report["approved"] is True
    assert {review["critic"] for review in report["reviews"]} == {
        "physics",
        "torque",
        "com_geometry",
    }
    assert all(review["verdict"] == "pass" for review in report["reviews"])


def test_critic_panel_flags_unbuildable_candidate() -> None:
    payload = _current_model().model_dump(mode="json")
    payload["generation"] = 1
    payload["parent_generation"] = 0
    payload["config"]["motor_allocation"] = "2drive+1flywheel"
    candidate = SelfModel.model_validate(payload)

    report = run_critic_panel(
        candidate,
        parts_catalog=_parts_catalog(),
        contract_lines=_contract_lines(),
        gap_summary=_gap_summary(),
    )

    assert report["approved"] is False
    geometry = next(item for item in report["reviews"] if item["critic"] == "com_geometry")
    assert geometry["verdict"] == "flag"
    assert "CLAW_MOTOR_BUDGET" in json.dumps(geometry)


def test_exporter_turns_approved_model_into_robot_task_envelope() -> None:
    candidate, _ = generate_self_model_candidate(_current_model(), _gap_summary())
    report = run_critic_panel(
        candidate,
        parts_catalog=_parts_catalog(),
        contract_lines=_contract_lines(),
        gap_summary=_gap_summary(),
    )

    envelope = export_task_envelope(
        candidate,
        critic_report=report,
        seed_contract=_contract_lines()[0],
        tag_id=0,
    )

    assert isinstance(envelope, TaskEnvelope)
    assert envelope.contract.generation == candidate.generation
    assert envelope.contract.parent_generation == candidate.parent_generation
    assert envelope.outline.method_plan()[0][0] == "locate_nearest_apriltag"
    assert [step[0] for step in envelope.outline.method_plan()] == [
        "locate_nearest_apriltag",
        "pickup_ball",
        "lift",
        "move_to_tag",
        "release",
    ]


def test_exporter_rejects_flagged_critic_report() -> None:
    candidate, _ = generate_self_model_candidate(_current_model(), _gap_summary())
    report = {"approved": False, "reviews": [{"critic": "physics", "verdict": "flag"}]}

    with pytest.raises(ValueError, match="critic approval"):
        export_task_envelope(
            candidate,
            critic_report=report,
            seed_contract=_contract_lines()[0],
            tag_id=0,
        )
