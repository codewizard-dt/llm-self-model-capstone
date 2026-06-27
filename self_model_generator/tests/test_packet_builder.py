from __future__ import annotations

import json
from pathlib import Path

import pytest
from contracts import SelfModel
from self_model_generator.packet_builder import (
    BLOCKED_F10_GAP,
    BLOCKED_HARDWARE_PROOF,
    BLOCKED_NO_CONTRACT_EVIDENCE,
    FIXTURE_BACKED_GAP,
    LIVE_BACKED_GAP,
    build_packet_from_files,
    build_self_model_packet,
    main as packet_builder_main,
    load_parts_catalog,
    read_contract_lines_jsonl,
)

ROOT = Path(__file__).resolve().parents[2]
SELF_MODEL = ROOT / "contracts" / "fixtures" / "self_model_gen0.json"
PARTS = ROOT / "contracts" / "parts_catalog.json"
SESSION = ROOT / "contracts" / "fixtures" / "session_example.jsonl"
ROS_BUNDLE = ROOT / "robot" / "ros2-runtime" / "fixtures" / "align_to_tag_success_bundle.json"


def _session_gap_summary(
    *,
    provenance: str = "fixture",
    session_ids: list[str] | None = None,
    run_ids: list[str] | None = None,
    raw_session_paths: list[str] | None = None,
    contract_line_count: int = 4,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "kind": "gap_summary",
        "source": {
            "contract_line_count": contract_line_count,
            "generations": [0],
            "provenance": provenance,
            "raw_session_paths": raw_session_paths or [],
            "round_range": [1, 4],
            "run_ids": run_ids or [],
            "session_ids": session_ids or ["session_20260624_141200"],
            "tasks": ["grab", "pull", "score", "throw"],
        },
        "residuals": {"force_error_N": {"latest": -3.4}},
        "diagnoses": [],
    }


def test_packet_from_contract_fixture_marks_f10_and_hardware_blockers() -> None:
    packet = build_packet_from_files(
        self_model_path=SELF_MODEL,
        parts_catalog_path=PARTS,
        contract_jsonl_path=SESSION,
        human_constraints=("demo must stay offline",),
    )

    assert "## Track 1 - M1 + ROS Proof Intake" in packet
    assert "## Track 2 - Self-Model Generator Packet" in packet
    assert BLOCKED_F10_GAP in packet
    assert BLOCKED_HARDWARE_PROOF in packet
    assert "task `grab`" in packet
    assert "current config buildable: `true`" in packet
    assert "demo must stay offline" in packet


def test_ros_bundle_intake_uses_proof_export_routine_and_preserves_source() -> None:
    packet = build_packet_from_files(
        self_model_path=SELF_MODEL,
        parts_catalog_path=PARTS,
        ros_bundle_path=ROS_BUNDLE,
    )

    assert "vexy_ros.evidence_export.contract_jsonl_from_bundle" in packet
    assert "proof/rosbags/align_to_tag_fixture" in packet
    assert "task `align_to_tag`" in packet
    assert BLOCKED_HARDWARE_PROOF not in packet
    assert BLOCKED_F10_GAP in packet


def test_missing_contract_evidence_uses_exact_blocked_label() -> None:
    model = SelfModel.model_validate_json(SELF_MODEL.read_text())
    catalog = load_parts_catalog(PARTS)

    packet = build_self_model_packet(
        self_model=model,
        parts_catalog=catalog,
        contract_lines=[],
        source_refs={"self_model": str(SELF_MODEL), "parts_catalog": str(PARTS)},
    )

    assert BLOCKED_NO_CONTRACT_EVIDENCE in packet


def test_fixture_gap_summary_is_visibly_labeled(tmp_path: Path) -> None:
    gap_path = tmp_path / "gap-summary.fixture.json"
    gap_path.write_text(json.dumps(_session_gap_summary()))

    packet = build_packet_from_files(
        self_model_path=SELF_MODEL,
        parts_catalog_path=PARTS,
        contract_jsonl_path=SESSION,
        gap_summary_path=gap_path,
    )

    assert FIXTURE_BACKED_GAP in packet
    assert '"force_error_N": {' in packet


def test_live_gap_summary_is_labeled_from_provenance(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.live.jsonl"
    rows: list[str] = []
    for raw in SESSION.read_text().splitlines():
        payload = json.loads(raw)
        payload["run_id"] = "live-pickup-20260626-210937"
        payload["source"] = {
            "raw_session_path": "telemetry/live-pickup-20260626-210937",
            "brain_start_ms": 100,
            "brain_end_ms": 200,
            "pi_received_ms": 210,
            "telemetry_sample_count": 3,
        }
        rows.append(json.dumps(payload))
    contract_path.write_text("\n".join(rows) + "\n")

    gap_path = tmp_path / "gap-summary.live.json"
    gap_path.write_text(
        json.dumps(
            _session_gap_summary(
                provenance="live",
                run_ids=["live-pickup-20260626-210937"],
                raw_session_paths=["telemetry/live-pickup-20260626-210937"],
            )
        )
    )

    packet = build_packet_from_files(
        self_model_path=SELF_MODEL,
        parts_catalog_path=PARTS,
        contract_jsonl_path=contract_path,
        gap_summary_path=gap_path,
    )

    assert LIVE_BACKED_GAP in packet
    assert FIXTURE_BACKED_GAP not in packet


def test_packet_rejects_gap_summary_from_different_session(tmp_path: Path) -> None:
    gap_path = tmp_path / "gap-summary.wrong.json"
    gap_path.write_text(json.dumps(_session_gap_summary(session_ids=["session_other"])))

    with pytest.raises(ValueError, match="gap summary session_ids"):
        build_packet_from_files(
            self_model_path=SELF_MODEL,
            parts_catalog_path=PARTS,
            contract_jsonl_path=SESSION,
            gap_summary_path=gap_path,
        )


def test_packet_builder_cli_writes_gap_backed_packet(tmp_path: Path) -> None:
    gap_path = tmp_path / "gap-summary.json"
    gap_path.write_text(json.dumps(_session_gap_summary()))
    out_path = tmp_path / "packet.md"

    exit_code = packet_builder_main(
        [
            "--self-model",
            str(SELF_MODEL),
            "--parts-catalog",
            str(PARTS),
            "--contract-jsonl",
            str(SESSION),
            "--gap-summary",
            str(gap_path),
            "--human-constraint",
            "review runtime knobs before deploy",
            "--out",
            str(out_path),
        ]
    )

    assert exit_code == 0
    packet = out_path.read_text()
    assert FIXTURE_BACKED_GAP in packet
    assert "review runtime knobs before deploy" in packet


def test_catalog_violations_are_exposed_without_local_schema() -> None:
    payload = json.loads(SELF_MODEL.read_text())
    payload["config"]["motor_allocation"] = "2drive+1flywheel"
    model = SelfModel.model_validate(payload)
    catalog = load_parts_catalog(PARTS)

    packet = build_self_model_packet(
        self_model=model,
        parts_catalog=catalog,
        contract_lines=read_contract_lines_jsonl(SESSION),
        source_refs={"self_model": "mutated fixture", "parts_catalog": str(PARTS)},
    )

    assert "current config buildable: `false`" in packet
    assert "`CLAW_MOTOR_BUDGET`" in packet
