from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


MOTOR_FIELDS = (
    "position_deg",
    "velocity_rpm",
    "current_amp",
    "power_w",
    "torque_nm",
    "efficiency_pct",
    "temperature_c",
)
MOTOR_METHODS = {
    "position_deg": "position",
    "velocity_rpm": "velocity",
    "current_amp": "current",
    "power_w": "power",
    "torque_nm": "torque",
    "efficiency_pct": "efficiency",
    "temperature_c": "temperature",
}


def contract_payload_from_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    scene = bundle.get("scene_map", {})
    align_result = bundle.get("align_result", {})
    goal = bundle.get("goal", {})
    brain = bundle.get("brain", {})

    motor_samples = _motor_samples(bundle)
    if not motor_samples:
        raise ValueError("proof bundle must include at least one motor sample")

    gap = dict(bundle.get("gap") or _gap_from_align_result(align_result))
    if not gap:
        raise ValueError("proof bundle must include numeric gap values")

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "session_id": str(bundle["session_id"]),
        "generation": int(bundle.get("generation", 0)),
        "round": int(bundle.get("round", 1)),
        "task": str(bundle.get("task", "align_to_tag")),
        "motor_samples": motor_samples,
        "predicted": dict(bundle.get("predicted") or _predicted_from_goal(goal)),
        "gap": gap,
        "outcome": dict(
            bundle.get("outcome") or _outcome_from_align_result(align_result)
        ),
        "vision": dict(bundle.get("vision") or _vision_from_scene(scene)),
        "source": {
            "raw_session_path": bundle.get("raw_session_path"),
            "brain_start_ms": brain.get("start_ms"),
            "brain_end_ms": brain.get("end_ms"),
            "pi_received_ms": bundle.get("pi_received_ms"),
            "telemetry_sample_count": int(
                brain.get("telemetry_sample_count", len(brain.get("telemetry", [])))
            ),
        },
    }
    return _strip_none(payload)


def contract_jsonl_from_bundle(
    bundle: Mapping[str, Any], *, validate: bool = True
) -> str:
    payload = contract_payload_from_bundle(bundle)
    line = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    if validate:
        validate_contract_line(line)
    return line + "\n"


def validate_contract_line(line: str) -> None:
    try:
        from contracts import ContractLine  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "contracts package is required for validation; run from the repo with "
            "PYTHONPATH=contracts/src:robot/ros2-runtime/src or use --no-validate"
        ) from exc
    ContractLine.model_validate_json(line)


def _motor_samples(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    if "motor_samples" in bundle:
        return [dict(sample) for sample in bundle["motor_samples"]]

    samples: list[dict[str, Any]] = []
    for record in bundle.get("brain", {}).get("telemetry", []):
        for sample in record.get("motor_samples", []):
            samples.append(_normalize_motor_sample(sample))
    return samples


def _normalize_motor_sample(sample: Mapping[str, Any]) -> dict[str, Any]:
    device = str(sample["device"])
    values = sample.get("values", sample)
    return {
        "device": device,
        "subsystem": sample.get("subsystem", "drivetrain"),
        "api_binding": "vexcode_python",
        "sample_ms": int(sample.get("sample_ms", 0)),
        "values": {field: float(values[field]) for field in MOTOR_FIELDS},
        "source_api": _source_api(device),
    }


def _source_api(device: str) -> dict[str, str]:
    return {
        field: f"{device}.{method}(DEGREES)"
        if field == "position_deg"
        else f"{device}.{method}(RPM)"
        if field == "velocity_rpm"
        else f"{device}.{method}(AMP)"
        if field == "current_amp"
        else f"{device}.{method}(WATT)"
        if field == "power_w"
        else f"{device}.{method}(NM)"
        if field == "torque_nm"
        else f"{device}.{method}(PERCENT)"
        if field == "efficiency_pct"
        else f"{device}.{method}(CELSIUS)"
        for field, method in MOTOR_METHODS.items()
    }


def _predicted_from_goal(goal: Mapping[str, Any]) -> dict[str, float | bool | str]:
    return {
        "target_tag_id": int(goal.get("tag_id", 0)),
        "target_distance_m": float(goal.get("target_distance_m", 0.45)),
        "success": True,
    }


def _gap_from_align_result(result: Mapping[str, Any]) -> dict[str, float]:
    gap: dict[str, float] = {}
    for source, target in (
        ("final_yaw_error_rad", "yaw_error_rad"),
        ("final_lateral_error_m", "lateral_error_m"),
        ("final_distance_error_m", "distance_error_m"),
    ):
        value = result.get(source)
        if value is not None:
            gap[target] = float(value)
    return gap


def _outcome_from_align_result(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "success": bool(result.get("success", False)),
        "reason": str(result.get("reason", "unknown")),
        "final_yaw_error_rad": result.get("final_yaw_error_rad"),
        "final_lateral_error_m": result.get("final_lateral_error_m"),
        "final_distance_error_m": result.get("final_distance_error_m"),
    }


def _vision_from_scene(scene: Mapping[str, Any]) -> dict[str, Any]:
    robot_pose = scene.get("robot_pose") or scene.get("camera_pose")
    tags = scene.get("tags", {})
    objects = scene.get("objects", [])
    if not robot_pose:
        return {"object_detected": bool(tags or objects)}
    return {
        "object_detected": bool(tags or objects),
        "apriltag_pose": {
            "x": float(robot_pose.get("x_m", robot_pose.get("x", 0.0))),
            "y": float(robot_pose.get("y_m", robot_pose.get("y", 0.0))),
            "heading": float(robot_pose.get("yaw_rad", robot_pose.get("heading", 0.0))),
        },
    }


def _strip_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_none(item) for key, item in value.items() if item is not None
        }
    if isinstance(value, list):
        return [_strip_none(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export one ROS proof bundle JSON file to contract-valid JSONL."
    )
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args(argv)

    bundle = json.loads(args.bundle.read_text())
    try:
        line = contract_jsonl_from_bundle(bundle, validate=not args.no_validate)
    except Exception as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        return 1

    if args.out is None:
        print(line, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
