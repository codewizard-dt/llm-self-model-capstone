from __future__ import annotations

import argparse
from pathlib import Path

from operator_llm.packet_builder import (
    BLOCKED_F10_GAP,
    BLOCKED_HARDWARE_PROOF,
    build_packet_from_files,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SELF_MODEL = REPO_ROOT / "contracts" / "fixtures" / "self_model_gen0.json"
DEFAULT_PARTS = REPO_ROOT / "contracts" / "parts_catalog.json"
DEFAULT_CONTRACT_JSONL = REPO_ROOT / "contracts" / "fixtures" / "session_example.jsonl"
DEFAULT_ROS_BUNDLE = (
    REPO_ROOT / "robot" / "ros2-runtime" / "fixtures" / "align_to_tag_success_bundle.json"
)


def validate_fixture_packets() -> tuple[str, str]:
    contract_packet = build_packet_from_files(
        self_model_path=DEFAULT_SELF_MODEL,
        parts_catalog_path=DEFAULT_PARTS,
        contract_jsonl_path=DEFAULT_CONTRACT_JSONL,
        human_constraints=("offline operator loop only",),
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
    return contract_packet, ros_packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate operator packet-builder fixtures.")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    contract_packet, ros_packet = validate_fixture_packets()
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            contract_packet + "\n\n---\n\n" + ros_packet + "\n",
        )
    print("OK - operator packet-builder fixtures valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
