from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ModuleNotFoundError:  # pragma: no cover - allows pure helper tests off ROS.
    rclpy = None  # type: ignore[assignment]

    class Node:  # type: ignore[no-redef]
        pass

    class String:  # type: ignore[no-redef]
        def __init__(self, *, data: str = "") -> None:
            self.data = data


from .vision_map import DEFAULT_CAMERA_IN_ROBOT


def default_out_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"/home/vexy/proof/localization-{stamp}")


def summarize_localization_samples(
    samples: list[Mapping[str, Any]],
    *,
    camera_info_url: str,
    camera_in_robot_json: str,
    map_name: str,
    accepted_position_error_m: float,
    accepted_heading_error_deg: float,
) -> dict[str, Any]:
    localizations = [dict(sample.get("localization") or {}) for sample in samples]
    observed_tag_ids = sorted(
        {
            int(tag_id)
            for sample in samples
            for tag_id in sample.get("observed_tag_ids", [])
        }
    )
    position_errors = [
        float(item["tag_residual_m"])
        for item in localizations
        if item.get("tag_residual_m") is not None
    ]
    heading_errors = [
        float(item["tag_residual_deg"])
        for item in localizations
        if item.get("tag_residual_deg") is not None
    ]
    mean_position_error_m = _mean(position_errors)
    max_position_error_m = max(position_errors) if position_errors else None
    mean_heading_error_deg = _mean(heading_errors)
    max_heading_error_deg = max(heading_errors) if heading_errors else None
    accepted = (
        bool(position_errors)
        and bool(heading_errors)
        and mean_position_error_m is not None
        and mean_heading_error_deg is not None
        and mean_position_error_m <= accepted_position_error_m
        and mean_heading_error_deg <= accepted_heading_error_deg
    )
    return {
        "type": "localization_benchmark",
        "map": map_name,
        "sample_count": len(samples),
        "camera_info_url": camera_info_url,
        "camera_in_robot": json.loads(camera_in_robot_json),
        "observed_tag_ids": observed_tag_ids,
        "mean_position_error_m": mean_position_error_m,
        "max_position_error_m": max_position_error_m,
        "mean_heading_error_deg": mean_heading_error_deg,
        "max_heading_error_deg": max_heading_error_deg,
        "accepted_position_error_m": accepted_position_error_m,
        "accepted_heading_error_deg": accepted_heading_error_deg,
        "accepted_for_demo": accepted,
    }


class LocalizationBenchmarkNode(Node):
    def __init__(self, *, scene_topic: str) -> None:
        super().__init__("vexy_localization_benchmark")
        self.samples: list[dict[str, Any]] = []
        self.create_subscription(String, scene_topic, self._on_scene, 10)

    def _on_scene(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if isinstance(payload, dict) and payload.get("localization"):
            self.samples.append(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark AprilTag localization residuals from /vision/scene_map."
    )
    parser.add_argument("--map", dest="map_name", default="gen0-grab-toss-v1")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--timeout-s", type=float, default=20.0)
    parser.add_argument("--scene-topic", default="/vision/scene_map")
    parser.add_argument("--camera-info-url", default="")
    parser.add_argument("--camera-in-robot-json", default=DEFAULT_CAMERA_IN_ROBOT)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--accepted-position-error-m", type=float, default=0.10)
    parser.add_argument("--accepted-heading-error-deg", type=float, default=8.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run localization benchmark capture")
    args = build_parser().parse_args(argv)
    out_dir = args.out or default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = LocalizationBenchmarkNode(scene_topic=args.scene_topic)
    try:
        deadline = time.monotonic() + max(0.0, args.timeout_s)
        while time.monotonic() < deadline and len(node.samples) < max(1, args.samples):
            rclpy.spin_once(node, timeout_sec=0.1)
        summary = summarize_localization_samples(
            node.samples[: max(1, args.samples)],
            camera_info_url=args.camera_info_url,
            camera_in_robot_json=args.camera_in_robot_json,
            map_name=args.map_name,
            accepted_position_error_m=args.accepted_position_error_m,
            accepted_heading_error_deg=args.accepted_heading_error_deg,
        )
        output_path = out_dir / "localization_benchmark.json"
        output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary["accepted_for_demo"] else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


if __name__ == "__main__":
    raise SystemExit(main())
