from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from contracts import ContractLine

from self_model_generator.gap_analyzer import (
    PROVENANCE_LIVE,
    PROVENANCE_VALUES,
    GapSummaryProvenance,
    build_gap_summary_from_jsonl,
    write_gap_summary,
)
from self_model_generator.loop_closure import (
    export_task_envelope,
    generate_self_model_candidate,
    run_critic_panel,
)
from self_model_generator.packet_builder import (
    build_packet_from_files,
    load_parts_catalog,
    load_self_model,
    read_contract_lines_jsonl,
)


def run_full_loop(
    *,
    self_model_path: Path,
    parts_catalog_path: Path,
    contract_jsonl_path: Path,
    out_dir: Path,
    expected_run_id: str | None = None,
    expected_session_id: str | None = None,
    provenance: GapSummaryProvenance = "fixture",
    human_constraints: Sequence[str] = (),
    tag_id: int = 0,
    target_distance_m: float = 0.45,
    pickup_duration_ms: int = 700,
) -> dict[str, Any]:
    """Run the deterministic telemetry -> model -> task loop and write artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    contract_lines = read_contract_lines_jsonl(contract_jsonl_path)
    _require_contract_evidence(contract_lines)

    gap_summary = build_gap_summary_from_jsonl(
        contract_jsonl_path,
        expected_run_id=expected_run_id,
        expected_session_id=expected_session_id,
        provenance=provenance,
    )
    _require_hardware_proof(
        contract_lines,
        gap_summary=gap_summary,
        provenance=provenance,
    )

    artifacts = _artifact_paths(out_dir)
    write_gap_summary(gap_summary, artifacts["gap_summary"])

    packet = build_packet_from_files(
        self_model_path=self_model_path,
        parts_catalog_path=parts_catalog_path,
        contract_jsonl_path=contract_jsonl_path,
        gap_summary_path=artifacts["gap_summary"],
        human_constraints=tuple(human_constraints),
    )
    artifacts["self_model_packet"].write_text(packet + "\n")

    current_model = load_self_model(self_model_path)
    parts_catalog = load_parts_catalog(parts_catalog_path)
    candidate, handoff = generate_self_model_candidate(current_model, gap_summary)
    _write_json(artifacts["candidate_self_model"], candidate.model_dump(mode="json"))
    _write_json(artifacts["generator_handoff"], handoff)

    critic_report = run_critic_panel(
        candidate,
        parts_catalog=parts_catalog,
        contract_lines=contract_lines,
        gap_summary=gap_summary,
    )
    _write_json(artifacts["critic_report"], critic_report)
    if critic_report.get("approved") is not True:
        raise ValueError("critic approval is required before exporting a TaskEnvelope")

    task_envelope = export_task_envelope(
        candidate,
        critic_report=critic_report,
        seed_contract=contract_lines[0],
        tag_id=tag_id,
        target_distance_m=target_distance_m,
        pickup_duration_ms=pickup_duration_ms,
    )
    _write_json(artifacts["task_envelope"], task_envelope.model_dump(mode="json"))

    manifest = {
        "schema_version": "1.0",
        "kind": "self_model_full_loop_manifest",
        "success": True,
        "critic_approved": True,
        "inputs": {
            "self_model": str(self_model_path),
            "parts_catalog": str(parts_catalog_path),
            "contract_jsonl": str(contract_jsonl_path),
            "expected_run_id": expected_run_id,
            "expected_session_id": expected_session_id,
        },
        "source": gap_summary["source"],
        "generation": {
            "parent": current_model.generation,
            "candidate": candidate.generation,
        },
        "artifacts": {key: str(path) for key, path in artifacts.items()},
    }
    _write_json(artifacts["manifest"], manifest)
    return manifest


def _artifact_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "gap_summary": out_dir / "gap_summary.json",
        "self_model_packet": out_dir / "self_model_packet.md",
        "candidate_self_model": out_dir / "candidate_self_model.json",
        "generator_handoff": out_dir / "generator_handoff.json",
        "critic_report": out_dir / "critic_report.json",
        "task_envelope": out_dir / "task_envelope.json",
        "manifest": out_dir / "manifest.json",
    }


def _require_contract_evidence(contract_lines: Sequence[ContractLine]) -> None:
    if not contract_lines:
        raise ValueError("full loop requires at least one ContractLine row")


def _require_hardware_proof(
    contract_lines: Sequence[ContractLine],
    *,
    gap_summary: dict[str, Any],
    provenance: GapSummaryProvenance,
) -> None:
    source = gap_summary.get("source")
    if not isinstance(source, dict):
        raise ValueError("gap summary source is required for full-loop proof")
    if int(source.get("contract_line_count") or 0) != len(contract_lines):
        raise ValueError("gap summary must be freshly built from the input ContractLine JSONL")

    if provenance != PROVENANCE_LIVE:
        return

    missing_paths = [
        line.round
        for line in contract_lines
        if line.source is None or not line.source.raw_session_path
    ]
    if missing_paths:
        raise ValueError(
            "live full loop requires source.raw_session_path on every ContractLine; "
            f"missing for round(s): {missing_paths}"
        )
    raw_session_paths = source.get("raw_session_paths")
    if not isinstance(raw_session_paths, list) or not raw_session_paths:
        raise ValueError("live full loop requires source.raw_session_path evidence")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the full deterministic self-model telemetry loop."
    )
    parser.add_argument("--self-model", type=Path, required=True)
    parser.add_argument("--parts-catalog", type=Path, required=True)
    parser.add_argument("--contract-jsonl", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--expected-run-id", default=None)
    parser.add_argument("--expected-session-id", default=None)
    parser.add_argument(
        "--provenance",
        choices=sorted(PROVENANCE_VALUES),
        default="fixture",
    )
    parser.add_argument("--human-constraint", action="append", default=[])
    parser.add_argument("--tag-id", type=int, default=0)
    parser.add_argument("--target-distance-m", type=float, default=0.45)
    parser.add_argument("--pickup-duration-ms", type=int, default=700)
    args = parser.parse_args(argv)

    manifest = run_full_loop(
        self_model_path=args.self_model,
        parts_catalog_path=args.parts_catalog,
        contract_jsonl_path=args.contract_jsonl,
        out_dir=args.out_dir,
        expected_run_id=args.expected_run_id,
        expected_session_id=args.expected_session_id,
        provenance=args.provenance,
        human_constraints=tuple(args.human_constraint),
        tag_id=args.tag_id,
        target_distance_m=args.target_distance_m,
        pickup_duration_ms=args.pickup_duration_ms,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
