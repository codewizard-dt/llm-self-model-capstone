"""Offline self-model generator (LLM/Critic) orchestration helpers."""

from self_model_generator.fixture_loader import (
    DEFAULT_RUN_ID,
    fixture_evidence_path,
    load_contract_jsonl,
    load_fixture_contract_lines,
)
from self_model_generator.packet_builder import (
    BLOCKED_F10_GAP,
    BLOCKED_HARDWARE_PROOF,
    BLOCKED_NO_CONTRACT_EVIDENCE,
    build_packet_from_files,
    build_self_model_packet,
    contract_lines_from_ros_bundle,
    read_contract_lines_jsonl,
)

__all__ = [
    "BLOCKED_F10_GAP",
    "BLOCKED_HARDWARE_PROOF",
    "BLOCKED_NO_CONTRACT_EVIDENCE",
    "DEFAULT_RUN_ID",
    "build_packet_from_files",
    "build_self_model_packet",
    "contract_lines_from_ros_bundle",
    "fixture_evidence_path",
    "load_contract_jsonl",
    "load_fixture_contract_lines",
    "read_contract_lines_jsonl",
]
