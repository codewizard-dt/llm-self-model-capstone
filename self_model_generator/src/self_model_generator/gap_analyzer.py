from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from contracts import ContractLine

GAP_SUMMARY_SCHEMA_VERSION = "1.0"
PICKUP_IN_PROGRESS_REASONS = frozenset({"opening_claw", "moving_to_ball", "closing_claw"})
POST_PICKUP_METHODS = frozenset(
    {"lift", "release", "move_to_tag", "locate_nearest_apriltag", "align_to_tag"}
)


def build_gap_summary_from_jsonl(path: Path) -> dict[str, Any]:
    return analyze_contract_lines(read_contract_lines_jsonl(path))


def read_contract_lines_jsonl(path: Path) -> list[ContractLine]:
    lines: list[ContractLine] = []
    for raw in path.read_text().splitlines():
        if raw.strip():
            lines.append(ContractLine.model_validate_json(raw))
    return lines


def write_gap_summary(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def analyze_contract_lines(lines: Sequence[ContractLine]) -> dict[str, Any]:
    diagnoses = _diagnose(lines)
    residuals = _residual_summary(lines)
    return {
        "schema_version": GAP_SUMMARY_SCHEMA_VERSION,
        "kind": "gap_summary",
        "source": _source_summary(lines),
        "residuals": residuals,
        "diagnoses": diagnoses,
        "generator_handoff": _generator_handoff(lines, residuals, diagnoses),
    }


def _source_summary(lines: Sequence[ContractLine]) -> dict[str, Any]:
    session_ids = sorted({line.session_id for line in lines})
    tasks = sorted({line.task for line in lines})
    raw_session_paths = sorted(
        {
            line.source.raw_session_path
            for line in lines
            if line.source is not None and line.source.raw_session_path
        }
    )
    rounds = [line.round for line in lines]
    return {
        "contract_line_count": len(lines),
        "session_ids": session_ids,
        "tasks": tasks,
        "raw_session_paths": raw_session_paths,
        "round_range": [] if not rounds else [min(rounds), max(rounds)],
    }


def _residual_summary(lines: Sequence[ContractLine]) -> dict[str, dict[str, float | int]]:
    values_by_key: dict[str, list[float]] = {}
    for line in lines:
        for key, value in line.gap.items():
            values_by_key.setdefault(key, []).append(float(value))

    summary: dict[str, dict[str, float | int]] = {}
    for key in sorted(values_by_key):
        values = values_by_key[key]
        abs_values = [abs(value) for value in values]
        summary[key] = {
            "count": len(values),
            "latest": values[-1],
            "mean": sum(values) / len(values),
            "mean_abs": sum(abs_values) / len(abs_values),
            "max_abs": max(abs_values),
        }
    return summary


def _diagnose(lines: Sequence[ContractLine]) -> list[dict[str, Any]]:
    if not lines:
        return [
            _diagnosis(
                code="NO_CONTRACT_EVIDENCE",
                severity="blocked",
                summary="No ContractLine evidence was provided.",
                evidence={},
                runtime_knobs=[],
            )
        ]

    diagnoses: list[dict[str, Any]] = []
    _append_pickup_advanced_diagnoses(lines, diagnoses)
    _append_object_confirmation_diagnoses(lines, diagnoses)
    return _dedupe_diagnoses(diagnoses)


def _append_pickup_advanced_diagnoses(
    lines: Sequence[ContractLine], diagnoses: list[dict[str, Any]]
) -> None:
    for index, line in enumerate(lines[:-1]):
        outcome = _outcome(line)
        method = _method(line)
        reason = _reason(line)
        if method != "pickup_ball" or outcome.get("success") is not False:
            continue
        if reason not in PICKUP_IN_PROGRESS_REASONS:
            continue

        next_line = lines[index + 1]
        next_method = _method(next_line)
        if next_method not in POST_PICKUP_METHODS:
            continue

        diagnoses.append(
            _diagnosis(
                code="PICKUP_ADVANCED_BEFORE_GRAB",
                severity="error",
                summary=(
                    "The task outline moved past pickup_ball while pickup was still "
                    "in progress, so the robot could lift or travel before the object "
                    "was actually confirmed."
                ),
                evidence={
                    "session_id": line.session_id,
                    "methods": [method, next_method],
                    "pickup_reason": reason,
                    "pickup_round": line.round,
                    "next_round": next_line.round,
                    "has_object": _outcome_has_object(line),
                },
                runtime_knobs=[
                    "task_step_timeout_s",
                    "pickup_grab_settle_s",
                    "pickup_max_attempts",
                ],
            )
        )


def _append_object_confirmation_diagnoses(
    lines: Sequence[ContractLine], diagnoses: list[dict[str, Any]]
) -> None:
    for line in lines:
        method = _method(line)
        if method not in {"pickup_ball", "grab"}:
            continue

        outcome = _outcome(line)
        reason = _reason(line)
        has_object = _outcome_has_object(line)
        failed_confirmation = reason in {"grab_failed", "grab_not_confirmed"} or (
            has_object is False and outcome.get("success") is not True
        )
        if failed_confirmation:
            diagnoses.append(
                _diagnosis(
                    code="OBJECT_NOT_CONFIRMED",
                    severity="error",
                    summary=(
                        "The robot did not confirm that the end effector held an "
                        "object after a pickup or grab step."
                    ),
                    evidence={
                        "session_id": line.session_id,
                        "round": line.round,
                        "method": method,
                        "reason": reason,
                        "command": outcome.get("command"),
                        "has_object": has_object,
                        "manipulator_sample": _manipulator_sample(line),
                    },
                    runtime_knobs=[
                        "end_effector_object_max_closed_deg",
                        "end_effector_current_object_amp",
                        "end_effector_low_velocity_rpm",
                        "pickup_grab_settle_s",
                        "pickup_max_attempts",
                    ],
                )
            )

        if has_object is False and _object_still_visible(line):
            diagnoses.append(
                _diagnosis(
                    code="BALL_STILL_VISIBLE_AFTER_GRAB",
                    severity="warning",
                    summary=(
                        "Vision still reports an object after the grab failed, so the "
                        "capture zone or approach offset may be wrong."
                    ),
                    evidence={
                        "session_id": line.session_id,
                        "round": line.round,
                        "method": method,
                        "reason": reason,
                        "object_bbox": None if line.vision is None else line.vision.object_bbox,
                    },
                    runtime_knobs=[
                        "ball_capture_forward_m",
                        "ball_capture_lateral_m",
                        "ball_approach_target_forward_m",
                    ],
                )
            )


def _diagnosis(
    *,
    code: str,
    severity: str,
    summary: str,
    evidence: dict[str, Any],
    runtime_knobs: Sequence[str],
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "summary": summary,
        "evidence": evidence,
        "recommended_runtime_knobs": list(runtime_knobs),
    }


def _dedupe_diagnoses(diagnoses: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, int | None]] = set()
    deduped: list[dict[str, Any]] = []
    for diagnosis in diagnoses:
        evidence = diagnosis.get("evidence", {})
        key = (
            str(diagnosis.get("code")),
            str(evidence.get("session_id", "")),
            evidence.get("round"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(diagnosis)
    return deduped


def _generator_handoff(
    lines: Sequence[ContractLine],
    residuals: dict[str, dict[str, float | int]],
    diagnoses: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    blocked = not lines
    update_scope: set[str] = set()
    if residuals:
        update_scope.update({"gap_model", "predictive"})
    if any(item["recommended_runtime_knobs"] for item in diagnoses):
        update_scope.add("runtime_config")

    focus = [item["code"] for item in diagnoses if item["code"] != "NO_CONTRACT_EVIDENCE"]
    return {
        "blocked": blocked,
        "focus": focus,
        "candidate_update_scope": sorted(update_scope),
        "instructions": [
            "Use residual keys exactly as named in the ContractLine gap block.",
            "Treat runtime knob changes as proposals that require critic and human review.",
            "Do not use hidden oracle data or unexported hardware claims.",
        ],
    }


def _outcome(line: ContractLine) -> dict[str, Any]:
    return dict(line.outcome or {})


def _method(line: ContractLine) -> str:
    return str(_outcome(line).get("method") or line.task)


def _reason(line: ContractLine) -> str:
    return str(_outcome(line).get("reason") or "unknown")


def _outcome_has_object(line: ContractLine) -> bool | None:
    value = _outcome(line).get("has_object")
    return value if isinstance(value, bool) else None


def _object_still_visible(line: ContractLine) -> bool:
    return line.vision is not None and line.vision.object_detected is True


def _manipulator_sample(line: ContractLine) -> dict[str, float] | None:
    for sample in line.motor_samples:
        if sample.subsystem == "claw" or sample.device in {
            "claw",
            "claw_motor",
            "release",
            "release_motor",
            "manipulator",
        }:
            return sample.values.model_dump()
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an F10 gap summary from contract-valid ContractLine JSONL."
    )
    parser.add_argument("contract_jsonl", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    summary = build_gap_summary_from_jsonl(args.contract_jsonl)
    if args.out is None:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        write_gap_summary(summary, args.out)
        print(f"wrote gap summary: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
