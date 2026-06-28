from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

REQUIRED_JSONL_FILES = (
    "operator_status.jsonl",
    "vex_telemetry.jsonl",
    "vision_object_detections.jsonl",
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def verify_visual_pickup_proof(
    result: Mapping[str, Any],
    *,
    result_path: Path | None = None,
    visual_confirmed: bool = False,
    min_images: int = 1,
    require_mcap: bool = True,
) -> dict[str, Any]:
    capture_dir = _capture_dir(result, result_path)
    checks = [
        _check("probe_succeeded", result.get("status") == "succeeded"),
    ]
    attempt = _successful_attempt(result)
    checks.append(_check("attempt_succeeded", attempt is not None))
    checks.append(
        _check(
            "has_object_true",
            _status_has_object(attempt.get("latest_status") if attempt else None),
        )
    )
    lift = attempt.get("lift_result") if attempt else None
    checks.append(
        _check(
            "lift_succeeded",
            isinstance(lift, Mapping) and lift.get("status") == "succeeded",
            _lift_reason(lift),
        )
    )
    checks.append(_arm_delta_check(lift))
    checks.extend(_capture_checks(result, capture_dir, min_images, require_mcap))
    checks.append(
        _check(
            "visual_confirmed",
            visual_confirmed,
            "manual review must confirm ball held in claw and lifted",
        )
    )
    failed = [check for check in checks if check["status"] != "passed"]
    return {
        "type": "visual_pickup_proof_verdict",
        "status": "failed" if failed else "succeeded",
        "reason": failed[0]["name"] if failed else "grab_and_lift_proven",
        "capture_dir": str(capture_dir) if capture_dir is not None else None,
        "review_image": _review_image(result, capture_dir),
        "checks": checks,
    }


def _successful_attempt(result: Mapping[str, Any]) -> Mapping[str, Any] | None:
    attempts = result.get("attempts")
    if not isinstance(attempts, list):
        return None
    for attempt in attempts:
        if isinstance(attempt, Mapping) and attempt.get("status") == "succeeded":
            return attempt
    return None


def _status_has_object(status: Any) -> bool:
    return isinstance(status, Mapping) and status.get("has_object") is True


def _lift_reason(lift: Any) -> str | None:
    if isinstance(lift, Mapping):
        reason = lift.get("reason")
        if reason is not None:
            return str(reason)
    return None


def _arm_delta_check(lift: Any) -> dict[str, Any]:
    if not isinstance(lift, Mapping):
        return _check("arm_delta_confirmed", False, "missing_lift_result")
    before = _float_or_none(lift.get("before_arm_position_deg"))
    after = _float_or_none(lift.get("after_arm_position_deg"))
    min_delta = _float_or_none(lift.get("min_arm_delta_deg")) or 0.0
    if before is None:
        return _check("arm_delta_confirmed", False, "missing_before_arm_position")
    if after is None:
        return _check("arm_delta_confirmed", False, "missing_after_arm_position")
    delta = after - before
    return _check(
        "arm_delta_confirmed",
        delta >= min_delta,
        f"delta={delta:.3f}, min={min_delta:.3f}",
    )


def _capture_checks(
    result: Mapping[str, Any],
    capture_dir: Path | None,
    min_images: int,
    require_mcap: bool,
) -> list[dict[str, Any]]:
    capture = result.get("capture")
    jsonl_counts = _jsonl_counts(capture, capture_dir)
    image_count = _image_count(capture, capture_dir)
    checks = [
        _check("capture_dir_present", capture_dir is not None),
        _check(
            "image_evidence_present", image_count >= min_images, f"images={image_count}"
        ),
    ]
    for name in REQUIRED_JSONL_FILES:
        checks.append(
            _check(
                f"{name}_present",
                jsonl_counts.get(name, 0) > 0,
                f"lines={jsonl_counts.get(name, 0)}",
            )
        )
    if require_mcap:
        checks.append(
            _check(
                "mcap_metadata_present", _mcap_metadata_present(capture, capture_dir)
            )
        )
    return checks


def _capture_dir(result: Mapping[str, Any], result_path: Path | None) -> Path | None:
    capture = result.get("capture")
    if isinstance(capture, Mapping) and isinstance(capture.get("out_dir"), str):
        return Path(capture["out_dir"]).expanduser()
    return result_path.parent if result_path is not None else None


def _jsonl_counts(capture: Any, capture_dir: Path | None) -> dict[str, int]:
    if isinstance(capture, Mapping) and isinstance(capture.get("jsonl_files"), Mapping):
        return {
            str(name): int(count)
            for name, count in capture["jsonl_files"].items()
            if _intable(count)
        }
    if capture_dir is None:
        return {}
    return {path.name: _line_count(path) for path in capture_dir.glob("*.jsonl")}


def _image_count(capture: Any, capture_dir: Path | None) -> int:
    if isinstance(capture, Mapping) and _intable(capture.get("image_count")):
        return int(capture["image_count"])
    if capture_dir is None:
        return 0
    images_dir = capture_dir / "images"
    return sum(
        1
        for path in images_dir.glob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".ppm", ".png"}
    )


def _mcap_metadata_present(capture: Any, capture_dir: Path | None) -> bool:
    if isinstance(capture, Mapping) and isinstance(capture.get("bag_files"), list):
        if "metadata.yaml" in {str(name) for name in capture["bag_files"]}:
            return True
    return bool(capture_dir and (capture_dir / "bag" / "metadata.yaml").exists())


def _review_image(result: Mapping[str, Any], capture_dir: Path | None) -> str | None:
    capture = result.get("capture")
    if isinstance(capture, Mapping) and isinstance(capture.get("last_image"), str):
        return capture["last_image"]
    if capture_dir is None:
        return None
    images_dir = capture_dir / "images"
    images = sorted(
        path
        for path in images_dir.glob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".ppm", ".png"}
    )
    return str(images[-1]) if images else None


def _line_count(path: Path) -> int:
    count = 0
    with path.open("rb") as fh:
        for _ in fh:
            count += 1
    return count


def _check(name: str, passed: bool, detail: str | None = None) -> dict[str, Any]:
    payload = {"name": name, "status": "passed" if passed else "failed"}
    if detail is not None:
        payload["detail"] = detail
    return payload


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _intable(value: Any) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a visual pickup grab+lift proof bundle."
    )
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument(
        "--visual-confirmed",
        action="store_true",
        help="Set only after visually confirming the saved frame shows held ball plus lift.",
    )
    parser.add_argument("--min-images", type=int, default=1)
    parser.add_argument("--no-require-mcap", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    result_path = args.result.expanduser()
    verdict = verify_visual_pickup_proof(
        load_json(result_path),
        result_path=result_path,
        visual_confirmed=args.visual_confirmed,
        min_images=args.min_images,
        require_mcap=not args.no_require_mcap,
    )
    output = json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.expanduser().write_text(output)
    print(output, end="")
    return 0 if verdict["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
