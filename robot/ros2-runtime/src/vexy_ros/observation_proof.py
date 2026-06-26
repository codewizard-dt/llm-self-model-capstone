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


def summarize_observation_bundle(
    bundle: Mapping[str, Any],
    *,
    expected_ball_count: int | None = None,
    ground_truth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    scene = bundle.get("scene_map") or {}
    detections_payload = bundle.get("object_detections") or {}
    detections = detections_payload.get("detections", [])
    indications = bundle.get("object_indications") or []
    tracks_payload = bundle.get("object_tracks") or {}
    tracks = tracks_payload.get("tracks", [])
    agent_scene = bundle.get("agent_scene") or {}
    agent_objects = agent_scene.get("objects", [])
    objects = scene.get("objects", [])
    task_plans = bundle.get("task_plans") or {}
    confirmed_tracks = [track for track in tracks if track.get("status") == "confirmed"]
    stale_tracks = [track for track in tracks if track.get("status") == "stale"]
    localization_errors = object_localization_errors(agent_scene, ground_truth or {})
    observed_count = len(
        [
            item
            for item in agent_objects or confirmed_tracks or objects
            if str(item.get("class", item.get("name", ""))) == "yellow_ball"
        ]
    )
    expected_count_delta = (
        None if expected_ball_count is None else observed_count - expected_ball_count
    )
    return {
        "motion_commanded": False,
        "requested_targets": list(bundle.get("requested_targets", [])),
        "observed_tag_ids": list(scene.get("observed_tag_ids", [])),
        "scene_object_names": sorted(str(item.get("name")) for item in objects),
        "object_detection_count": len(detections),
        "object_indication_count": len(indications),
        "scene_object_count": len(objects),
        "object_track_count": len(tracks),
        "confirmed_object_track_count": len(confirmed_tracks),
        "stale_object_track_count": len(stale_tracks),
        "agent_scene_object_count": len(agent_objects),
        "expected_ball_count": expected_ball_count,
        "observed_ball_count": observed_count,
        "expected_count_delta": expected_count_delta,
        "false_negative_count": (
            None
            if expected_ball_count is None
            else max(0, expected_ball_count - observed_count)
        ),
        "false_positive_count": (
            None
            if expected_ball_count is None
            else max(0, observed_count - expected_ball_count)
        ),
        "localization_error_count": len(localization_errors),
        "per_object_localization_errors": localization_errors,
        "mean_object_localization_error_m": _mean(
            [item["error_m"] for item in localization_errors]
        ),
        "max_object_localization_error_m": (
            max(item["error_m"] for item in localization_errors)
            if localization_errors
            else None
        ),
        "pose_confidence": (agent_scene.get("robot") or {}).get("pose_confidence"),
        "tag_residual_m": (agent_scene.get("localization") or {}).get("tag_residual_m"),
        "tag_residual_deg": (agent_scene.get("localization") or {}).get(
            "tag_residual_deg"
        ),
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
        self.create_subscription(
            String,
            "/vision/object_tracks",
            lambda msg: self._capture_json("object_tracks", msg),
            10,
        )
        self.create_subscription(
            String,
            "/vision/agent_scene",
            lambda msg: self._capture_json("agent_scene", msg),
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

    def bundle(
        self,
        *,
        expected_ball_count: int | None = None,
        ground_truth: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = dict(self.latest)
        payload["requested_targets"] = list(self.targets)
        payload["task_plans"] = dict(self.task_plans)
        payload["captured_at_s"] = time.monotonic()
        if expected_ball_count is not None:
            payload["expected_ball_count"] = expected_ball_count
        if ground_truth:
            payload["ground_truth"] = dict(ground_truth)
        payload["summary"] = summarize_observation_bundle(
            payload,
            expected_ball_count=expected_ball_count,
            ground_truth=ground_truth,
        )
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
    parser.add_argument("--expected-count", type=int, default=None)
    parser.add_argument("--ground-truth", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    if rclpy is None:
        raise RuntimeError("rclpy is required to run observation proof capture")
    args = build_parser().parse_args(argv)
    proof_dir = args.proof_dir or default_proof_dir()
    proof_dir.mkdir(parents=True, exist_ok=True)
    targets = list(args.target or DEFAULT_TARGETS)
    ground_truth = (
        json.loads(args.ground_truth.read_text()) if args.ground_truth else None
    )

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
            if {"scene_map", "object_tracks", "agent_scene"} <= set(
                node.latest
            ) and all(target in node.task_plans for target in targets):
                break

        bundle = node.bundle(
            expected_ball_count=args.expected_count,
            ground_truth=ground_truth,
        )
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
        return 0 if proof_passed(bundle, targets=targets) else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()


def proof_passed(bundle: Mapping[str, Any], *, targets: list[str]) -> bool:
    required = {"scene_map", "object_tracks", "agent_scene"}
    if not required <= set(bundle):
        return False
    task_plans = bundle.get("task_plans") or {}
    if not all(target in task_plans for target in targets):
        return False
    expected = bundle.get("expected_ball_count")
    if expected is None:
        return True
    observed = (bundle.get("summary") or {}).get("observed_ball_count", 0)
    return int(observed) >= int(expected)


def object_localization_errors(
    agent_scene: Mapping[str, Any], ground_truth: Mapping[str, Any]
) -> list[dict[str, Any]]:
    truth_objects = ground_truth.get("objects", []) if ground_truth else []
    observed = [
        item
        for item in agent_scene.get("objects", [])
        if isinstance(item, Mapping) and item.get("pose")
    ]
    errors: list[dict[str, Any]] = []
    used_observed: set[int] = set()
    for truth in truth_objects:
        if not isinstance(truth, Mapping):
            continue
        truth_pose = truth.get("pose") or truth.get("map_pose")
        if not isinstance(truth_pose, Mapping):
            continue
        truth_class = str(truth.get("class", truth.get("name", "object")))
        best: tuple[float, int, Mapping[str, Any]] | None = None
        for index, item in enumerate(observed):
            if index in used_observed:
                continue
            if str(item.get("class", item.get("name", "object"))) != truth_class:
                continue
            pose = item.get("pose") or {}
            error_m = _distance_m(truth_pose, pose)
            if best is None or error_m < best[0]:
                best = (error_m, index, item)
        if best is None:
            continue
        error_m, index, item = best
        used_observed.add(index)
        errors.append(
            {
                "truth_id": truth.get("id"),
                "observed_id": item.get("id"),
                "class": truth_class,
                "error_m": error_m,
            }
        )
    return errors


def _distance_m(a: Mapping[str, Any], b: Mapping[str, Any]) -> float:
    ax = float(a.get("x_m", a.get("x", 0.0)))
    ay = float(a.get("y_m", a.get("y", 0.0)))
    bx = float(b.get("x_m", b.get("x", 0.0)))
    by = float(b.get("y_m", b.get("y", 0.0)))
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def _mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


if __name__ == "__main__":
    raise SystemExit(main())
