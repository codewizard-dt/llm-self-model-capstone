from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Any, Mapping

from .vision_map import Pose2D, SceneMap, scene_map_from_json


@dataclass(frozen=True)
class TaskPlanRequest:
    target: str
    action: str = "inspect"
    target_distance_m: float = 0.75
    dispatch: bool = False


def parse_task_plan_request(raw: str | Mapping[str, Any]) -> TaskPlanRequest:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    return TaskPlanRequest(
        target=str(payload["target"]),
        action=str(payload.get("action", "inspect")),
        target_distance_m=float(payload.get("target_distance_m", 0.75)),
        dispatch=bool(payload.get("dispatch", False)),
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
    raise ValueError("target must start with tag: or object:")


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
            },
            {
                "type": "go_to_map_pose",
                "standoff_m": request.target_distance_m,
                "dispatchable": False,
                "blocked_reason": "needs bounded go-to-pose skill",
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
    return math.atan2(b.y_m - a.y_m, b.x_m - a.x_m) - a.yaw_rad


def _split_target(target: str) -> tuple[str, str]:
    if ":" not in target:
        raise ValueError("target must be formatted as tag:<id> or object:<name>")
    kind, name = target.split(":", 1)
    return kind, name
