from __future__ import annotations

import json
from pathlib import Path

from contracts import SelfModel
from self_model_generator.packet_builder import (
    BLOCKED_F10_GAP,
    BLOCKED_HARDWARE_PROOF,
    BLOCKED_NO_CONTRACT_EVIDENCE,
    FIXTURE_BACKED_GAP,
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
    gap_path.write_text(
        json.dumps(
            {
                "kind": "fixture",
                "residuals": {"force_error_N": -3.4},
            }
        )
    )

    packet = build_packet_from_files(
        self_model_path=SELF_MODEL,
        parts_catalog_path=PARTS,
        contract_jsonl_path=SESSION,
        gap_summary_path=gap_path,
    )

    assert FIXTURE_BACKED_GAP in packet
    assert '"force_error_N": -3.4' in packet


def test_packet_builder_cli_writes_gap_backed_packet(tmp_path: Path) -> None:
    gap_path = tmp_path / "gap-summary.json"
    gap_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "gap_summary",
                "residuals": {"force_error_N": {"latest": -1.2}},
                "diagnoses": [],
            }
        )
    )
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
