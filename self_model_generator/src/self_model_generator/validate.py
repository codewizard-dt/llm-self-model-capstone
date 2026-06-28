from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from self_model_generator.loop_closure import (
    export_task_envelope,
    generate_self_model_candidate,
    run_critic_panel,
)
from self_model_generator.gap_analyzer import build_gap_summary_from_jsonl, write_gap_summary
from self_model_generator.loop_runner import run_full_loop
from self_model_generator.packet_builder import (
    BLOCKED_F10_GAP,
    BLOCKED_HARDWARE_PROOF,
    FIXTURE_BACKED_GAP,
    build_packet_from_files,
    load_parts_catalog,
    load_self_model,
    read_contract_lines_jsonl,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SELF_MODEL = REPO_ROOT / "contracts" / "fixtures" / "self_model_gen0.json"
DEFAULT_PARTS = REPO_ROOT / "contracts" / "parts_catalog.json"
DEFAULT_CONTRACT_JSONL = REPO_ROOT / "contracts" / "fixtures" / "session_example.jsonl"
DEFAULT_ROS_BUNDLE = (
    REPO_ROOT / "robot" / "ros2-runtime" / "fixtures" / "align_to_tag_success_bundle.json"
)


def validate_fixture_packets() -> tuple[str, str, str]:
    contract_packet = build_packet_from_files(
        self_model_path=DEFAULT_SELF_MODEL,
        parts_catalog_path=DEFAULT_PARTS,
        contract_jsonl_path=DEFAULT_CONTRACT_JSONL,
        human_constraints=("offline self-model loop only",),
    )
    if BLOCKED_F10_GAP not in contract_packet:
        raise AssertionError("contract fixture packet must label missing F10 gap summary")
    if BLOCKED_HARDWARE_PROOF not in contract_packet:
        raise AssertionError("contract fixture packet must label missing hardware proof")

    ros_packet = build_packet_from_files(
        self_model_path=DEFAULT_SELF_MODEL,
        parts_catalog_path=DEFAULT_PARTS,
        ros_bundle_path=DEFAULT_ROS_BUNDLE,
        human_constraints=("leverage ROS proof-export routine",),
    )
    if "vexy_ros.evidence_export.contract_jsonl_from_bundle" not in ros_packet:
        raise AssertionError("ROS packet must cite the proof-export routine")
    if "proof/rosbags/align_to_tag_fixture" not in ros_packet:
        raise AssertionError("ROS packet must preserve the proof raw_session_path")
    if BLOCKED_HARDWARE_PROOF in ros_packet:
        raise AssertionError("ROS packet should not mark hardware proof as missing")
    if BLOCKED_F10_GAP not in ros_packet:
        raise AssertionError("ROS packet must still label missing F10 gap summary")

    gap_summary = build_gap_summary_from_jsonl(DEFAULT_CONTRACT_JSONL)
    with TemporaryDirectory() as tmpdir:
        gap_path = Path(tmpdir) / "gap_summary.json"
        write_gap_summary(gap_summary, gap_path)
        gap_packet = build_packet_from_files(
            self_model_path=DEFAULT_SELF_MODEL,
            parts_catalog_path=DEFAULT_PARTS,
            contract_jsonl_path=DEFAULT_CONTRACT_JSONL,
            gap_summary_path=gap_path,
            human_constraints=("fixture-backed F10 gap analysis",),
        )

    if FIXTURE_BACKED_GAP not in gap_packet:
        raise AssertionError("gap packet must label the F10 residual summary")
    if '"force_error_N"' not in gap_packet:
        raise AssertionError("gap packet must preserve residual keys")
    if BLOCKED_F10_GAP in gap_packet:
        raise AssertionError("gap packet should not mark F10 as missing")
    return contract_packet, ros_packet, gap_packet


def validate_loop_closure_fixture() -> None:
    current_model = load_self_model(DEFAULT_SELF_MODEL)
    parts_catalog = load_parts_catalog(DEFAULT_PARTS)
    contract_lines = read_contract_lines_jsonl(DEFAULT_CONTRACT_JSONL)
    gap_summary = build_gap_summary_from_jsonl(DEFAULT_CONTRACT_JSONL)

    candidate, handoff = generate_self_model_candidate(current_model, gap_summary)
    if candidate.generation != current_model.generation + 1:
        raise AssertionError("generator must emit the next SelfModel generation")
    if handoff["candidate_generation"] != candidate.generation:
        raise AssertionError("generator handoff must name the candidate generation")

    critic_report = run_critic_panel(
        candidate,
        parts_catalog=parts_catalog,
        contract_lines=contract_lines,
        gap_summary=gap_summary,
    )
    if critic_report["approved"] is not True:
        raise AssertionError("fixture candidate should pass the deterministic critic panel")

    envelope = export_task_envelope(
        candidate,
        critic_report=critic_report,
        seed_contract=contract_lines[0],
    )
    if envelope.contract.generation != candidate.generation:
        raise AssertionError("exported task envelope must carry the candidate generation")


def validate_full_loop_fixture() -> None:
    with TemporaryDirectory() as tmpdir:
        manifest = run_full_loop(
            self_model_path=DEFAULT_SELF_MODEL,
            parts_catalog_path=DEFAULT_PARTS,
            contract_jsonl_path=DEFAULT_CONTRACT_JSONL,
            out_dir=Path(tmpdir),
            provenance="fixture",
        )
        task_path = Path(manifest["artifacts"]["task_envelope"])
        if not task_path.exists():
            raise AssertionError("full loop must write a task envelope artifact")
        if manifest["success"] is not True:
            raise AssertionError("full loop manifest must report success")
        if manifest["critic_approved"] is not True:
            raise AssertionError("full loop manifest must record critic approval")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate self-model packet-builder fixtures.")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    contract_packet, ros_packet, gap_packet = validate_fixture_packets()
    validate_loop_closure_fixture()
    validate_full_loop_fixture()
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            contract_packet + "\n\n---\n\n" + ros_packet + "\n\n---\n\n" + gap_packet + "\n",
        )
    print("OK - self-model packet-builder fixtures valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
