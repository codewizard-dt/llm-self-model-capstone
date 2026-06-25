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


DEFAULT_TARGETS = ("object:yellow_ball", "survey:all")


def default_proof_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"/home/vexy/proof/scene-observation-{stamp}")


def default_action_for_target(target: str) -> str:
    if target == "survey:all":
        return "survey_all"
    return "inspect"


def task_request_payload(target: str) -> str:
    return json.dumps(
        {
            "target": target,
            "action": default_action_for_target(target),
            "dispatch": False,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def summarize_observation_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    scene = bundle.get("scene_map") or {}
    detections_payload = bundle.get("object_detections") or {}
    detections = detections_payload.get("detections", [])
    indications = bundle.get("object_indications") or []
    objects = scene.get("objects", [])
    task_plans = bundle.get("task_plans") or {}
    return {
        "motion_commanded": False,
        "requested_targets": list(bundle.get("requested_targets", [])),
        "observed_tag_ids": list(scene.get("observed_tag_ids", [])),
        "scene_object_names": sorted(str(item.get("name")) for item in objects),
        "object_detection_count": len(detections),
        "object_indication_count": len(indications),
        "scene_object_count": len(objects),
        "task_plan_statuses": {
            str(target): {
                "status": plan.get("status"),
                "executable_now": bool(plan.get("executable_now", False)),
                "blocked_reason": plan.get("blocked_reason"),
                "step_count": len(plan.get("steps", [])),
            }
            for target, plan in sorted(task_plans.items())
        },
    }


class ObservationProofNode(Node):
    def __init__(self, targets: list[str]) -> None:
        super().__init__("scene_observation_proof")
        self.targets = targets
        self.latest: dict[str, Any] = {}
        self.task_plans: dict[str, dict[str, Any]] = {}
        self._request_pub = self.create_publisher(String, "/task_plan/request", 10)
        self.create_subscription(
            String,
            "/vision/object_detections",
            lambda msg: self._capture_json("object_detections", msg),
            10,
        )
        self.create_subscription(
            String,
            "/vision/object_indications",
            lambda msg: self._capture_json("object_indications", msg),
            10,
        )
        self.create_subscription(
            String,
            "/vision/scene_map",
            lambda msg: self._capture_json("scene_map", msg),
            10,
        )
        self.create_subscription(String, "/task_plan/current", self._on_task_plan, 10)
        self.create_subscription(
            String,
            "/vex/bridge_status",
            lambda msg: self._capture_json("bridge_status", msg),
            10,
        )
        self.create_subscription(
            String, "/vex/ack", lambda msg: self._capture_json("ack", msg), 10
        )
        self.create_subscription(
            String,
            "/vex/telemetry",
            lambda msg: self._capture_json("telemetry", msg),
            10,
        )

    def _capture_json(self, key: str, msg: String) -> None:
        try:
            self.latest[key] = json.loads(msg.data)
        except json.JSONDecodeError:
            return

    def _on_task_plan(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        target = str(payload.get("request", {}).get("target", "unknown"))
        self.task_plans[target] = payload

    def publish_requests(self) -> None:
        for target in self.targets:
            self._request_pub.publish(String(data=task_request_payload(target)))

    def bundle(self) -> dict[str, Any]:
        payload = dict(self.latest)
        payload["requested_targets"] = list(self.targets)
        payload["task_plans"] = dict(self.task_plans)
        payload["captured_at_s"] = time.monotonic()
        payload["summary"] = summarize_observation_bundle(payload)
        return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture no-motion scene-map/object/survey task-plan proof."
    )
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--timeout-s", type=float, default=20.0)
    parser.add_argument("--settle-s", type=float, default=2.0)
    parser.add_argument("--request-period-s", type=float, default=0.5)
    return parser


def main(argv: list[str] | None = None) -> int:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run observation proof capture")
    args = build_parser().parse_args(argv)
    proof_dir = args.proof_dir or default_proof_dir()
    proof_dir.mkdir(parents=True, exist_ok=True)
    targets = list(args.target or DEFAULT_TARGETS)

    rclpy.init()
    node = ObservationProofNode(targets)
    try:
        settle_until = time.monotonic() + max(0.0, args.settle_s)
        while time.monotonic() < settle_until:
            rclpy.spin_once(node, timeout_sec=0.1)

        deadline = time.monotonic() + max(0.0, args.timeout_s)
        next_request_s = 0.0
        while time.monotonic() < deadline:
            now_s = time.monotonic()
            if now_s >= next_request_s:
                node.publish_requests()
                next_request_s = now_s + max(0.1, args.request_period_s)
            rclpy.spin_once(node, timeout_sec=0.1)
            if "scene_map" in node.latest and all(
                target in node.task_plans for target in targets
            ):
                break

        bundle = node.bundle()
        output_path = proof_dir / "scene_observation_proof.json"
        output_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
        print(
            json.dumps(
                {
                    "proof_dir": str(proof_dir),
                    "captured": sorted(bundle),
                    "summary": bundle["summary"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if all(target in node.task_plans for target in targets) else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
