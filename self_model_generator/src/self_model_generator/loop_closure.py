from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from contracts import ContractLine, PartsCatalog, SelfModel, TaskEnvelope, validate_config


def generate_self_model_candidate(
    current_model: SelfModel, gap_summary: Mapping[str, Any]
) -> tuple[SelfModel, dict[str, Any]]:
    """Deterministic first Generator slice that emits a revised SelfModel candidate."""
    target_task = _target_task(current_model, gap_summary)
    payload = current_model.model_dump(mode="json")
    payload["generation"] = current_model.generation + 1
    payload["parent_generation"] = current_model.generation

    predictive = dict(payload.get("predictive") or {})
    task_prediction = dict(predictive.get(target_task) or {})
    gap_model = dict(payload.get("gap_model") or {})
    task_gap_model = dict(gap_model.get(target_task) or {})
    reasoning = dict(payload.get("reasoning") or {})

    residuals = gap_summary.get("residuals", {})
    changed_fields: list[str] = []
    force_error = _latest_residual(residuals, "force_error_N")
    if force_error is not None and isinstance(task_prediction.get("grip_force_N"), int | float):
        old_value = float(task_prediction["grip_force_N"])
        new_value = old_value + force_error
        task_prediction["grip_force_N"] = round(new_value, 3)
        task_gap_model["force_error_N"] = 0.0
        key = f"predictive.{target_task}.grip_force_N"
        reasoning[key] = (
            f"Adjusted grip_force_N {old_value:g} by force_error_N {force_error:g} "
            "from the F10 gap summary; the candidate prediction moves toward observed evidence."
        )
        changed_fields.append(key)

    duration_error = _latest_residual(residuals, "duration_error_s")
    if duration_error is not None and isinstance(task_prediction.get("duration_s"), int | float):
        old_value = float(task_prediction["duration_s"])
        new_value = max(0.1, old_value + duration_error)
        task_prediction["duration_s"] = round(new_value, 3)
        task_gap_model["duration_error_s"] = 0.0
        key = f"predictive.{target_task}.duration_s"
        reasoning[key] = (
            f"Adjusted duration_s {old_value:g} by duration_error_s {duration_error:g} "
            "from the F10 gap summary while preserving the residual key name."
        )
        changed_fields.append(key)

    if task_gap_model:
        gap_model[target_task] = task_gap_model
    if task_prediction:
        predictive[target_task] = task_prediction
    payload["predictive"] = predictive
    payload["gap_model"] = gap_model
    payload["reasoning"] = reasoning

    candidate = SelfModel.model_validate(payload)
    handoff = {
        "candidate_generation": candidate.generation,
        "parent_generation": candidate.parent_generation,
        "changed_fields": changed_fields,
        "evidence": {
            "gap_summary_kind": gap_summary.get("kind"),
            "source": gap_summary.get("source", {}),
        },
        "critic_review_request": ["physics", "torque", "com_geometry"],
    }
    return candidate, handoff


def run_critic_panel(
    candidate: SelfModel,
    *,
    parts_catalog: PartsCatalog,
    contract_lines: Sequence[ContractLine],
    gap_summary: Mapping[str, Any],
) -> dict[str, Any]:
    """Run the deterministic first F9 critic panel over a candidate SelfModel."""
    reviews = [
        _physics_review(candidate, gap_summary),
        _torque_review(candidate, contract_lines),
        _com_geometry_review(candidate, parts_catalog),
    ]
    return {
        "kind": "critic_panel_report",
        "approved": all(review["verdict"] == "pass" for review in reviews),
        "reviews": reviews,
    }


def export_task_envelope(
    candidate: SelfModel,
    *,
    critic_report: Mapping[str, Any],
    seed_contract: ContractLine,
    tag_id: int = 0,
    target_distance_m: float = 0.45,
    pickup_duration_ms: int = 700,
) -> TaskEnvelope:
    """Compile an approved candidate model into the next robot-facing TaskEnvelope."""
    if critic_report.get("approved") is not True:
        raise ValueError("critic approval is required before exporting a TaskEnvelope")

    payload = seed_contract.model_dump(mode="json")
    payload["session_id"] = f"{seed_contract.session_id}-gen{candidate.generation}"
    payload["generation"] = candidate.generation
    payload["parent_generation"] = candidate.parent_generation
    payload["round"] = seed_contract.round + 1
    payload["task"] = "self_model_revision_run"
    payload["predicted"] = _task_prediction(candidate)
    payload["gap"] = _task_gap(candidate)
    payload["outcome"] = None

    return TaskEnvelope.model_validate(
        {
            "contract": payload,
            "outline": [
                ["locate_nearest_apriltag", []],
                ["pickup_ball", [], {"duration_ms": pickup_duration_ms}],
                ["lift", []],
                ["move_to_tag", [tag_id], {"target_distance_m": target_distance_m}],
                ["release", []],
            ],
        }
    )


def _target_task(current_model: SelfModel, gap_summary: Mapping[str, Any]) -> str:
    for diagnosis in gap_summary.get("diagnoses", []) or []:
        if not isinstance(diagnosis, Mapping):
            continue
        evidence = diagnosis.get("evidence", {})
        if isinstance(evidence, Mapping):
            method = evidence.get("method")
            if isinstance(method, str) and method in current_model.predictive:
                return method
    if "grab" in current_model.predictive:
        return "grab"
    return next(iter(current_model.predictive))


def _latest_residual(residuals: Any, key: str) -> float | None:
    if not isinstance(residuals, Mapping):
        return None
    value = residuals.get(key)
    if not isinstance(value, Mapping):
        return None
    latest = value.get("latest")
    if isinstance(latest, int | float) and not isinstance(latest, bool):
        return float(latest)
    return None


def _physics_review(candidate: SelfModel, gap_summary: Mapping[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    capability = candidate.capability
    for field_name in ("reach_mm", "max_grip_force_N", "max_pull_force_N", "com_height_mm"):
        if float(getattr(capability, field_name)) < 0:
            findings.append(
                {
                    "field": f"capability.{field_name}",
                    "message": "capability values must be nonnegative",
                }
            )

    summary_keys = _representable_residual_keys(candidate, gap_summary)
    model_keys = {key for task in candidate.gap_model.values() for key in task}
    missing_keys = sorted(summary_keys - model_keys)
    if missing_keys:
        findings.append(
            {
                "field": "gap_model",
                "message": f"candidate dropped residual keys: {missing_keys}",
            }
        )

    return _review("physics", findings)


def _representable_residual_keys(candidate: SelfModel, gap_summary: Mapping[str, Any]) -> set[str]:
    residuals = gap_summary.get("residuals")
    if not isinstance(residuals, Mapping):
        return set()

    representable: set[str] = set()
    for task_prediction in candidate.predictive.values():
        if "grip_force_N" in task_prediction and "force_error_N" in residuals:
            representable.add("force_error_N")
        if "duration_s" in task_prediction and "duration_error_s" in residuals:
            representable.add("duration_error_s")
    return representable


def _torque_review(candidate: SelfModel, contract_lines: Sequence[ContractLine]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    max_observed_torque = 0.0
    for line in contract_lines:
        for sample in line.motor_samples:
            max_observed_torque = max(max_observed_torque, abs(sample.values.torque_nm))
    if candidate.capability.max_grip_force_N > 100.0 and max_observed_torque <= 0.0:
        findings.append(
            {
                "field": "capability.max_grip_force_N",
                "message": "high grip force claim has no supporting torque evidence",
            }
        )
    return _review("torque", findings)


def _com_geometry_review(candidate: SelfModel, parts_catalog: PartsCatalog) -> dict[str, Any]:
    verdict = validate_config(candidate.config)
    findings = [
        {"field": item.code, "message": item.message} for item in getattr(verdict, "violations", [])
    ]
    if candidate.capability.com_height_mm > 250.0:
        findings.append(
            {
                "field": "capability.com_height_mm",
                "message": "center of mass is high for a compact VEX clawbot",
            }
        )
    _ = parts_catalog
    return _review("com_geometry", findings)


def _review(critic: str, findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    findings_list = [dict(item) for item in findings]
    return {
        "critic": critic,
        "verdict": "pass" if not findings_list else "flag",
        "findings": findings_list,
    }


def _task_prediction(candidate: SelfModel) -> dict[str, float | bool | str]:
    if "pickup_ball" in candidate.predictive:
        return dict(candidate.predictive["pickup_ball"])
    if "grab" in candidate.predictive:
        return dict(candidate.predictive["grab"])
    return dict(next(iter(candidate.predictive.values())))


def _task_gap(candidate: SelfModel) -> dict[str, float]:
    if "pickup_ball" in candidate.gap_model:
        return dict(candidate.gap_model["pickup_ball"])
    if "grab" in candidate.gap_model:
        return dict(candidate.gap_model["grab"])
    return dict(next(iter(candidate.gap_model.values())))
