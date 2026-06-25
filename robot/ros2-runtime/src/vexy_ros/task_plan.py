from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Any, Mapping

from .vision_map import Pose2D, SceneMap, normalize_angle, scene_map_from_json

DEFAULT_HOME_TAG_ID = 2


@dataclass(frozen=True)
class TaskPlanRequest:
    target: str
    action: str = "inspect"
    target_distance_m: float = 0.75
    dispatch: bool = False
    survey_duration_s: float | None = None
    survey_omega_rad_s: float | None = None

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "target": self.target,
            "action": self.action,
            "target_distance_m": self.target_distance_m,
            "dispatch": self.dispatch,
        }
        if self.survey_duration_s is not None:
            payload["survey_duration_s"] = self.survey_duration_s
        if self.survey_omega_rad_s is not None:
            payload["survey_omega_rad_s"] = self.survey_omega_rad_s
        return payload


def parse_task_plan_request(raw: str | Mapping[str, Any]) -> TaskPlanRequest:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    return TaskPlanRequest(
        target=str(payload["target"]),
        action=str(payload.get("action", "inspect")),
        target_distance_m=float(payload.get("target_distance_m", 0.75)),
        dispatch=bool(payload.get("dispatch", False)),
        survey_duration_s=(
            float(payload["survey_duration_s"])
            if payload.get("survey_duration_s") is not None
            else None
        ),
        survey_omega_rad_s=(
            float(payload["survey_omega_rad_s"])
            if payload.get("survey_omega_rad_s") is not None
            else None
        ),
    )


def build_task_plan(
    scene: SceneMap,
    request: TaskPlanRequest,
    *,
    now_s: float | None = None,
) -> dict[str, Any]:
    stamp_s = time.monotonic() if now_s is None else now_s
    kind, name = _split_target(request.target)
    if kind == "tag":
        return _tag_plan(scene, tag_id=int(name), request=request, stamp_s=stamp_s)
    if kind == "object":
        return _object_plan(scene, object_name=name, request=request, stamp_s=stamp_s)
    if kind == "survey":
        if name != "all":
            raise ValueError("survey target must be survey:all")
        return _survey_plan(scene, request=request, stamp_s=stamp_s)
    if kind == "home":
        return _return_home_plan(
            scene,
            home_tag_id=_home_tag_id_from_target(name),
            request=request,
            stamp_s=stamp_s,
        )
    raise ValueError("target must start with tag:, object:, survey:, or home:")


def task_plan_from_scene_json(
    scene_json: str | Mapping[str, Any],
    request: TaskPlanRequest,
    *,
    now_s: float | None = None,
) -> dict[str, Any]:
    return build_task_plan(scene_map_from_json(scene_json), request, now_s=now_s)


def _tag_plan(
    scene: SceneMap,
    *,
    tag_id: int,
    request: TaskPlanRequest,
    stamp_s: float,
) -> dict[str, Any]:
    pose = scene.tags.get(tag_id)
    if pose is None:
        return _blocked_plan(
            request=request,
            stamp_s=stamp_s,
            reason="tag_not_in_scene",
            target={"type": "tag", "tag_id": tag_id},
        )
    return {
        "type": "task_plan",
        "stamp_s": stamp_s,
        "status": "ready",
        "executable_now": True,
        "request": request.to_json(),
        "target": {"type": "tag", "tag_id": tag_id, "pose": pose.to_json()},
        "action": request.action,
        "steps": [
            {
                "type": "align_to_tag",
                "goal": {
                    "tag_id": tag_id,
                    "target_distance_m": request.target_distance_m,
                    "timeout_s": 8.0,
                },
                "dispatchable": True,
            }
        ],
    }


def _object_plan(
    scene: SceneMap,
    *,
    object_name: str,
    request: TaskPlanRequest,
    stamp_s: float,
) -> dict[str, Any]:
    matches = [obj for obj in scene.objects if obj.name == object_name]
    if not matches:
        return _blocked_plan(
            request=request,
            stamp_s=stamp_s,
            reason="object_not_in_scene",
            target={"type": "object", "name": object_name},
        )
    target = max(matches, key=lambda obj: obj.confidence or 0.0)
    robot_pose = scene.map_from_robot
    distance_m = _distance(robot_pose, target.map_from_object)
    bearing_rad = _bearing(robot_pose, target.map_from_object)
    nearest_tag = _nearest_tag(scene, target.map_from_object)
    return {
        "type": "task_plan",
        "stamp_s": stamp_s,
        "status": "mapped",
        "executable_now": False,
        "blocked_reason": "object_go_to_pose_controller_not_proven",
        "request": request.to_json(),
        "target": {
            "type": "object",
            "name": object_name,
            "pose": target.map_from_object.to_json(),
            "source": target.source,
            "confidence": target.confidence,
            "range_from_robot_m": distance_m,
            "bearing_from_robot_rad": bearing_rad,
            "nearest_tag_id": nearest_tag,
        },
        "action": request.action,
        "steps": [
            {
                "type": "face_map_target",
                "target_pose": target.map_from_object.to_json(),
                "dispatchable": False,
                "required_proofs": ["fresh_scene_map", "bounded_turn_controller"],
            },
            {
                "type": "go_to_map_pose",
                "standoff_m": request.target_distance_m,
                "dispatchable": False,
                "blocked_reason": "needs bounded go-to-pose skill",
                "required_proofs": [
                    "fresh_scene_map",
                    "healthy_bridge_status",
                    "fresh_vex_ack",
                    "fresh_vex_telemetry",
                    "operator_supervised",
                    "bounded_go_to_pose_mcap",
                ],
            },
        ],
    }


def _return_home_plan(
    scene: SceneMap,
    *,
    home_tag_id: int,
    request: TaskPlanRequest,
    stamp_s: float,
) -> dict[str, Any]:
    pose = scene.tags.get(home_tag_id)
    target = {
        "type": "home",
        "home_tag_id": home_tag_id,
        "strategy": "align_to_home_tag",
    }
    if pose is None:
        return _blocked_plan(
            request=request,
            stamp_s=stamp_s,
            reason="home_tag_not_in_scene",
            target=target,
        )
    return {
        "type": "task_plan",
        "stamp_s": stamp_s,
        "status": "ready",
        "executable_now": True,
        "request": request.to_json(),
        "target": {
            **target,
            "pose": pose.to_json(),
            "observed_tag_ids": sorted(scene.observed_tag_ids),
        },
        "action": request.action,
        "steps": [
            {
                "type": "capture_home_anchor_snapshot",
                "topics": [
                    "/camera/camera_info",
                    "/apriltag/detections",
                    "/vision/scene_map",
                    "/vex/ack",
                    "/vex/telemetry",
                    "/vex/bridge_status",
                ],
                "dispatchable": False,
            },
            {
                "type": "align_to_tag",
                "purpose": "return_home",
                "goal": {
                    "tag_id": home_tag_id,
                    "target_distance_m": request.target_distance_m,
                    "timeout_s": 10.0,
                },
                "dispatchable": True,
                "required_proofs": [
                    "fresh_scene_map",
                    "home_tag_visible",
                    "healthy_bridge_status",
                    "fresh_vex_ack",
                    "fresh_vex_telemetry",
                    "bounded_align_to_tag",
                ],
            },
            {
                "type": "confirm_home_stop",
                "expected_outputs": [
                    "terminal_align_to_tag_result",
                    "final_stop_command",
                    "fresh_vex_ack",
                    "fresh_vex_telemetry",
                ],
                "dispatchable": False,
            },
        ],
    }


def _survey_plan(
    scene: SceneMap,
    *,
    request: TaskPlanRequest,
    stamp_s: float,
) -> dict[str, Any]:
    observed_tag_ids = sorted(scene.observed_tag_ids)
    unobserved_anchor_tag_ids = [
        tag_id for tag_id in scene.anchor_tag_ids if tag_id not in observed_tag_ids
    ]
    object_summaries = [
        {
            "name": obj.name,
            "pose": obj.map_from_object.to_json(),
            "source": obj.source,
            "confidence": obj.confidence,
            "nearest_tag_id": _nearest_tag(scene, obj.map_from_object),
            "range_from_robot_m": _distance(scene.map_from_robot, obj.map_from_object),
            "bearing_from_robot_rad": _bearing(
                scene.map_from_robot, obj.map_from_object
            ),
        }
        for obj in sorted(scene.objects, key=lambda item: item.name)
    ]
    duration_s = (
        14.5
        if request.survey_duration_s is None
        else max(0.2, min(20.0, request.survey_duration_s))
    )
    omega_rad_s = (
        0.45
        if request.survey_omega_rad_s is None
        else max(-0.5, min(0.5, request.survey_omega_rad_s))
    )
    if abs(omega_rad_s) < 0.02:
        omega_rad_s = -0.02 if omega_rad_s < 0.0 else 0.02
    return {
        "type": "task_plan",
        "stamp_s": stamp_s,
        "status": "ready",
        "executable_now": True,
        "request": request.to_json(),
        "target": {
            "type": "survey",
            "scope": "all",
            "anchor_tag_ids": sorted(scene.anchor_tag_ids),
            "observed_tag_ids": observed_tag_ids,
            "unobserved_anchor_tag_ids": unobserved_anchor_tag_ids,
            "object_count": len(object_summaries),
            "objects": object_summaries,
        },
        "action": request.action,
        "steps": [
            {
                "type": "capture_scene_snapshot",
                "topics": [
                    "/camera/camera_info",
                    "/apriltag/detections",
                    "/vision/object_detections",
                    "/vision/object_indications",
                    "/vision/scene_map",
                ],
                "dispatchable": False,
            },
            {
                "type": "survey_scan",
                "angle_rad": 2.0 * math.pi,
                "duration_s": duration_s,
                "omega_rad_s": omega_rad_s,
                "max_omega_rad_s": 0.5,
                "ttl_ms": 180,
                "dispatchable": True,
                "goal": {
                    "duration_s": duration_s,
                    "omega_rad_s": omega_rad_s,
                    "max_step_ms": 180,
                    "ack_stale_s": 0.8,
                    "telemetry_stale_s": 1.0,
                },
                "required_proofs": [
                    "healthy_bridge_status",
                    "fresh_vex_ack",
                    "fresh_vex_telemetry",
                    "scan_only_mcap",
                ],
                "proven_by": "full-survey-20260624-223313",
            },
            {
                "type": "merge_survey_observations",
                "expected_outputs": [
                    "observed_tag_ids",
                    "updated_robot_pose",
                    "objects",
                    "task_plan",
                ],
                "dispatchable": False,
            },
        ],
    }


def _blocked_plan(
    *,
    request: TaskPlanRequest,
    stamp_s: float,
    reason: str,
    target: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "task_plan",
        "stamp_s": stamp_s,
        "status": "blocked",
        "executable_now": False,
        "blocked_reason": reason,
        "request": request.to_json(),
        "target": target,
        "action": request.action,
        "steps": [],
    }


def _nearest_tag(scene: SceneMap, pose: Pose2D) -> int | None:
    if not scene.tags:
        return None
    return min(scene.tags, key=lambda tag_id: _distance(scene.tags[tag_id], pose))


def _distance(a: Pose2D, b: Pose2D) -> float:
    return math.hypot(b.x_m - a.x_m, b.y_m - a.y_m)


def _bearing(a: Pose2D, b: Pose2D) -> float:
    return normalize_angle(math.atan2(b.y_m - a.y_m, b.x_m - a.x_m) - a.yaw_rad)


def _split_target(target: str) -> tuple[str, str]:
    if ":" not in target:
        raise ValueError(
            "target must be formatted as tag:<id>, object:<name>, survey:<scope>, "
            "or home:tag"
        )
    kind, name = target.split(":", 1)
    return kind, name


def _home_tag_id_from_target(name: str) -> int:
    if name in {"tag", "default", "home"}:
        return DEFAULT_HOME_TAG_ID
    return int(name)
