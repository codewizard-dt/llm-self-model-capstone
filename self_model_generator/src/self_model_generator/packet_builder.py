from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from contracts import ContractLine, PartsCatalog, SelfModel, validate_config
from vexy_ros.evidence_export import contract_jsonl_from_bundle

BLOCKED_F10_GAP = "[BLOCKED: awaiting F10 gap analyzer residual summary]"
BLOCKED_NO_CONTRACT_EVIDENCE = "[BLOCKED: no ContractLine evidence for this task]"
BLOCKED_HARDWARE_PROOF = "[BLOCKED: hardware proof not recorded as contract-valid JSONL]"
FIXTURE_BACKED_GAP = "[FIXTURE-BACKED: F10 residual summary]"


def load_self_model(path: Path) -> SelfModel:
    return SelfModel.model_validate_json(path.read_text())


def load_parts_catalog(path: Path) -> PartsCatalog:
    return PartsCatalog.model_validate_json(path.read_text())


def read_contract_lines_jsonl(path: Path) -> list[ContractLine]:
    lines: list[ContractLine] = []
    for raw in path.read_text().splitlines():
        if raw.strip():
            lines.append(ContractLine.model_validate_json(raw))
    return lines


def contract_lines_from_ros_bundle(path: Path) -> list[ContractLine]:
    bundle = json.loads(path.read_text())
    jsonl = contract_jsonl_from_bundle(bundle)
    return [ContractLine.model_validate_json(jsonl)]


def read_gap_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def build_packet_from_files(
    *,
    self_model_path: Path,
    parts_catalog_path: Path,
    contract_jsonl_path: Path | None = None,
    ros_bundle_path: Path | None = None,
    gap_summary_path: Path | None = None,
    human_constraints: Sequence[str] = (),
) -> str:
    contract_lines: list[ContractLine] = []
    source_refs: dict[str, str] = {
        "self_model": str(self_model_path),
        "parts_catalog": str(parts_catalog_path),
    }

    if contract_jsonl_path is not None:
        contract_lines.extend(read_contract_lines_jsonl(contract_jsonl_path))
        source_refs["contract_jsonl"] = str(contract_jsonl_path)

    if ros_bundle_path is not None:
        contract_lines.extend(contract_lines_from_ros_bundle(ros_bundle_path))
        source_refs["ros_proof_bundle"] = str(ros_bundle_path)
        source_refs["ros_export_routine"] = "vexy_ros.evidence_export.contract_jsonl_from_bundle"

    gap_summary = None
    if gap_summary_path is not None:
        gap_summary = read_gap_summary(gap_summary_path)
        source_refs["gap_summary"] = str(gap_summary_path)

    return build_self_model_packet(
        self_model=load_self_model(self_model_path),
        parts_catalog=load_parts_catalog(parts_catalog_path),
        contract_lines=contract_lines,
        source_refs=source_refs,
        human_constraints=human_constraints,
        gap_summary=gap_summary,
    )


def build_self_model_packet(
    *,
    self_model: SelfModel,
    parts_catalog: PartsCatalog,
    contract_lines: Sequence[ContractLine],
    source_refs: Mapping[str, str],
    human_constraints: Sequence[str] = (),
    gap_summary: Mapping[str, Any] | None = None,
) -> str:
    verdict = validate_config(self_model.config)
    sections = [
        "# Self-Model Generator Packet",
        "",
        "## Track 1 - M1 + ROS Proof Intake",
        "",
        "- M1 contract surface: `contracts.ContractLine`, `contracts.SelfModel`, "
        "`contracts.PartsCatalog`, and F19 control grammar.",
        "- ROS proof routine: "
        f"`{source_refs.get('ros_export_routine', 'not provided for this packet')}`.",
        f"- Hardware proof status: {_hardware_proof_status(contract_lines)}",
        "",
        "## Track 2 - Self-Model Generator Packet",
        "",
        "This packet is the visible evidence boundary for the offline F8/F9 LLM loop.",
        "It must not include hidden oracle parameters or define self_model_generator-local schemas.",
        "",
        "### Source References",
        "",
        _source_refs_block(source_refs),
        "",
        "### Current SelfModel",
        "",
        _self_model_block(self_model),
        "",
        "### Parts Catalog Verdict",
        "",
        _catalog_block(parts_catalog, verdict),
        "",
        "### Contract Evidence",
        "",
        _contract_evidence_block(contract_lines),
        "",
        "### Gap Summary",
        "",
        _gap_summary_block(gap_summary),
        "",
        "### Human Constraints",
        "",
        _human_constraints_block(human_constraints),
        "",
        "### Generator Guardrails",
        "",
        "- Use only contract-valid observed telemetry, vision observations, approved "
        "self-models, parts catalog constraints, and fixture-backed gap summaries.",
        "- Do not read hidden synthetic oracle parameters.",
        "- Preserve residual-key traceability; do not rename gap keys in prose.",
        "- Return one candidate `contracts.SelfModel` plus a short handoff note.",
        "",
    ]
    return "\n".join(sections)


def _source_refs_block(source_refs: Mapping[str, str]) -> str:
    if not source_refs:
        return "- none"
    return "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(source_refs.items()))


def _self_model_block(self_model: SelfModel) -> str:
    config = self_model.config
    return "\n".join(
        [
            f"- generation: `{self_model.generation}`",
            f"- parent_generation: `{self_model.parent_generation}`",
            f"- motor_allocation: `{config.motor_allocation.value}`",
            f"- end_effector: `{config.end_effector.value}`",
            f"- cartridge: `{config.cartridge.value}`",
            f"- reasoning keys: `{', '.join(sorted(self_model.reasoning))}`",
        ]
    )


def _catalog_block(parts_catalog: PartsCatalog, verdict: Any) -> str:
    violations = [
        f"  - `{item.code}`: {item.message}" for item in getattr(verdict, "violations", [])
    ]
    violation_block = "\n".join(violations) if violations else "  - none"
    return "\n".join(
        [
            f"- catalog schema_version: `{parts_catalog.schema_version}`",
            f"- finite motor allocations: `{', '.join(item.value for item in parts_catalog.motor_allocation)}`",
            f"- finite end effectors: `{', '.join(item.value for item in parts_catalog.end_effector)}`",
            f"- finite cartridges: `{', '.join(item.value for item in parts_catalog.cartridge)}`",
            f"- current config buildable: `{str(verdict.buildable).lower()}`",
            "- violations:",
            violation_block,
        ]
    )


def _contract_evidence_block(contract_lines: Sequence[ContractLine]) -> str:
    if not contract_lines:
        return f"- {BLOCKED_NO_CONTRACT_EVIDENCE}"

    rows: list[str] = []
    for line in contract_lines:
        devices = sorted({sample.device for sample in line.motor_samples})
        gap_keys = sorted(line.gap)
        source = line.source.raw_session_path if line.source is not None else None
        rows.extend(
            [
                f"- session `{line.session_id}` round `{line.round}` task `{line.task}`",
                f"  - motor devices: `{', '.join(devices)}`",
                f"  - gap keys: `{', '.join(gap_keys)}`",
                f"  - raw session path: `{source or 'none'}`",
            ]
        )
    return "\n".join(rows)


def _gap_summary_block(gap_summary: Mapping[str, Any] | None) -> str:
    if gap_summary is None:
        return f"- {BLOCKED_F10_GAP}"
    return "\n".join(
        [
            f"- {FIXTURE_BACKED_GAP}",
            "```json",
            json.dumps(gap_summary, indent=2, sort_keys=True),
            "```",
        ]
    )


def _human_constraints_block(human_constraints: Sequence[str]) -> str:
    if not human_constraints:
        return "- none provided"
    return "\n".join(f"- {item}" for item in human_constraints)


def _hardware_proof_status(contract_lines: Sequence[ContractLine]) -> str:
    if not contract_lines:
        return BLOCKED_NO_CONTRACT_EVIDENCE
    paths = [
        line.source.raw_session_path
        for line in contract_lines
        if line.source is not None and line.source.raw_session_path
    ]
    if not paths:
        return BLOCKED_HARDWARE_PROOF
    joined = ", ".join(f"`{path}`" for path in sorted(set(paths)))
    return f"contract-valid JSONL references hardware/proof source(s): {joined}"
