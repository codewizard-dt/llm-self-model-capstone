"""Offline self-model generator (LLM/Critic) orchestration helpers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_FIXTURE_LOADER_EXPORTS = {
    "DEFAULT_RUN_ID",
    "fixture_evidence_path",
    "load_contract_jsonl",
    "load_fixture_contract_lines",
}
_GAP_ANALYZER_EXPORTS = {
    "analyze_contract_lines",
    "build_gap_summary_from_jsonl",
    "write_gap_summary",
}
_PACKET_BUILDER_EXPORTS = {
    "BLOCKED_F10_GAP",
    "BLOCKED_HARDWARE_PROOF",
    "BLOCKED_NO_CONTRACT_EVIDENCE",
    "FIXTURE_BACKED_GAP",
    "LIVE_BACKED_GAP",
    "REPLAY_BACKED_GAP",
    "build_packet_from_files",
    "build_self_model_packet",
    "contract_lines_from_ros_bundle",
    "read_contract_lines_jsonl",
    "validate_gap_summary_matches_contract_lines",
}

__all__ = sorted(_FIXTURE_LOADER_EXPORTS | _GAP_ANALYZER_EXPORTS | _PACKET_BUILDER_EXPORTS)


def __getattr__(name: str) -> Any:
    if name in _FIXTURE_LOADER_EXPORTS:
        return getattr(import_module("self_model_generator.fixture_loader"), name)
    if name in _GAP_ANALYZER_EXPORTS:
        return getattr(import_module("self_model_generator.gap_analyzer"), name)
    if name in _PACKET_BUILDER_EXPORTS:
        return getattr(import_module("self_model_generator.packet_builder"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
