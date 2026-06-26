from __future__ import annotations

import json
import math
from typing import Any, Mapping


def build_agent_scene(
    *,
    scene_map: Mapping[str, Any] | None,
    object_tracks: Mapping[str, Any] | None = None,
    telemetry: Mapping[str, Any] | None = None,
    bridge_status: Mapping[str, Any] | None = None,
    task_plan: Mapping[str, Any] | None = None,
    operator_status: Mapping[str, Any] | None = None,
    now_s: float,
    include_debug_tracks: bool = False,
) -> dict[str, Any]:
    scene = dict(scene_map or {})
    localization = dict(scene.get("localization") or {})
    bridge = dict(bridge_status or {})
    tel = dict(telemetry or {})
    operator = dict(operator_status or {})
    pose = scene.get("robot_pose")
    pose_age_s = _optional_float(localization.get("pose_age_s"))
    pose_confidence = float(localization.get("pose_confidence", 0.0))
    tracks = _agent_objects(
        scene=scene,
        object_tracks=object_tracks or {},
        include_debug_tracks=include_debug_tracks,
        pose_confidence=pose_confidence,
    )

    return {
        "type": "agent_scene",
        "stamp_s": now_s,
        "robot": {
            "pose": _pose_payload(pose),
            "localization_source": str(localization.get("source", "unavailable")),
            "pose_confidence": pose_confidence,
            "pose_age_s": pose_age_s,
            "motion_enabled": _motion_enabled(tel, bridge),
            "estop": bool(tel.get("estop", bridge.get("estop", False))),
            "bridge_status": str(bridge.get("status", bridge.get("state", "unknown"))),
            "bridge_fault": bridge.get("fault"),
            "holding": operator.get("holding"),
        },
        "localization": {
            "source": str(localization.get("source", "unavailable")),
            "pose_confidence": pose_confidence,
            "pose_age_s": pose_age_s,
            "visible_anchor_count": int(localization.get("visible_anchor_count", 0)),
            "tag_residual_m": _optional_float(localization.get("tag_residual_m")),
            "tag_residual_deg": _optional_float(localization.get("tag_residual_deg")),
            "dead_reckoning_age_s": _optional_float(
                localization.get("dead_reckoning_age_s")
            ),
        },
        "visible_tags": _visible_tags(scene),
        "missing_anchor_tags": _missing_anchor_tags(scene),
        "objects": tracks,
        "affordances": _affordances(tracks, pose_confidence=pose_confidence),
        "task_plan": _task_plan_summary(task_plan),
        "health": {
            "scene_map_available": bool(scene_map),
            "object_tracks_available": bool(object_tracks),
            "telemetry_available": bool(telemetry),
            "bridge_status_available": bool(bridge_status),
        },
    }


def agent_scene_json(**kwargs: Any) -> str:
    return json.dumps(
        build_agent_scene(**kwargs),
        separators=(",", ":"),
        sort_keys=True,
    )


def _agent_objects(
    *,
    scene: Mapping[str, Any],
    object_tracks: Mapping[str, Any],
    include_debug_tracks: bool,
    pose_confidence: float,
) -> list[dict[str, Any]]:
    scene_by_id = {
        str(item.get("id")): item
        for item in scene.get("objects", [])
        if item.get("id") is not None
    }
    scene_by_class = {
        str(item.get("class", item.get("name"))): item
        for item in scene.get("objects", [])
        if item.get("class") is not None or item.get("name") is not None
    }
    raw_tracks = object_tracks.get("tracks") or scene.get("objects", [])
    objects: list[dict[str, Any]] = []
    for index, track in enumerate(raw_tracks, start=1):
        if not isinstance(track, Mapping):
            continue
        status = str(track.get("status", "confirmed"))
        if status == "candidate" and not include_debug_tracks:
            continue
        if status == "expired" and not include_debug_tracks:
            continue
        class_name = str(track.get("class", track.get("name", "object")))
        object_id = str(track.get("id", f"{class_name}_{index:02d}"))
        scene_object = (
            scene_by_id.get(object_id) or scene_by_class.get(class_name) or {}
        )
        pose = scene_object.get("map_pose") or scene_object.get("pose")
        uncertainty = _optional_float(
            track.get(
                "position_uncertainty_m",
                scene_object.get("position_uncertainty_m"),
            )
        )
        confidence = float(track.get("confidence", scene_object.get("confidence", 0.0)))
        reachable = (
            status == "confirmed"
            and pose is not None
            and confidence >= 0.35
            and pose_confidence >= 0.35
        )
        objects.append(
            {
                "id": object_id,
                "class": class_name,
                "pose": _pose_payload(pose),
                "camera_pose": track.get("camera_pose"),
                "confidence": confidence,
                "position_uncertainty_m": uncertainty,
                "seen_frames": int(track.get("seen_frames", 0)),
                "age_s": _optional_float(track.get("age_s", scene_object.get("age_s"))),
                "status": status,
                "reachable": reachable,
                "range_source": track.get(
                    "range_source", scene_object.get("range_source")
                ),
                "source": track.get("source", scene_object.get("source")),
                "blocked_reason": None
                if reachable
                else _object_blocked_reason(status, pose, pose_confidence),
            }
        )
    return objects


def _affordances(
    objects: list[dict[str, Any]], *, pose_confidence: float
) -> list[dict[str, Any]]:
    affordances: list[dict[str, Any]] = []
    for item in objects:
        if item["status"] != "confirmed":
            continue
        score = _object_score(item, pose_confidence=pose_confidence)
        affordances.append(
            {
                "skill": "inspect_object",
                "target": item["id"],
                "score": score,
                "dispatchable": False,
                "reason": "visible, mapped object; read-only inspection affordance",
            }
        )
        affordances.append(
            {
                "skill": "face_object",
                "target": item["id"],
                "score": score,
                "dispatchable": False,
                "reason": "object mapped; bounded object-facing controller not yet proven",
            }
        )
    return sorted(affordances, key=lambda item: item["score"], reverse=True)


def _object_score(item: Mapping[str, Any], *, pose_confidence: float) -> float:
    uncertainty = item.get("position_uncertainty_m")
    uncertainty_penalty = 0.0 if uncertainty is None else min(0.4, float(uncertainty))
    return max(
        0.0,
        min(
            1.0,
            0.25
            + 0.45 * float(item.get("confidence", 0.0))
            + 0.30 * pose_confidence
            - uncertainty_penalty,
        ),
    )


def _visible_tags(scene: Mapping[str, Any]) -> list[dict[str, Any]]:
    tags = scene.get("tags", {})
    if not isinstance(tags, Mapping):
        return []
    observed = {int(tag_id) for tag_id in scene.get("observed_tag_ids", [])}
    return [
        {
            "tag_id": int(tag_id),
            "pose": _pose_payload(pose),
            "visible": int(tag_id) in observed,
        }
        for tag_id, pose in sorted(tags.items(), key=lambda item: int(item[0]))
    ]


def _missing_anchor_tags(scene: Mapping[str, Any]) -> list[int]:
    anchors = {int(tag_id) for tag_id in scene.get("anchor_tag_ids", [])}
    observed = {int(tag_id) for tag_id in scene.get("observed_tag_ids", [])}
    return sorted(anchors - observed)


def _task_plan_summary(task_plan: Mapping[str, Any] | None) -> dict[str, Any]:
    if not task_plan:
        return {
            "available": False,
            "status": "unavailable",
            "executable_now": False,
            "blocked_reason": "task_plan_unavailable",
        }
    return {
        "available": True,
        "target": task_plan.get("request", {}).get("target"),
        "status": task_plan.get("status"),
        "executable_now": bool(task_plan.get("executable_now", False)),
        "blocked_reason": task_plan.get("blocked_reason"),
    }


def _motion_enabled(
    telemetry: Mapping[str, Any], bridge_status: Mapping[str, Any]
) -> bool:
    if "motion_enabled" in telemetry:
        return bool(telemetry["motion_enabled"])
    if "motion_enabled" in bridge_status:
        return bool(bridge_status["motion_enabled"])
    return False


def _pose_payload(raw: Any) -> dict[str, float] | None:
    if not isinstance(raw, Mapping):
        return None
    x_m = _optional_float(raw.get("x_m", raw.get("x")))
    y_m = _optional_float(raw.get("y_m", raw.get("y")))
    if x_m is None or y_m is None:
        return None
    yaw_rad = _optional_float(raw.get("yaw_rad", raw.get("heading", 0.0))) or 0.0
    return {
        "x_m": x_m,
        "y_m": y_m,
        "yaw_rad": yaw_rad,
        "heading_deg": float(raw.get("heading_deg", math.degrees(yaw_rad))),
    }


def _object_blocked_reason(
    status: str, pose: Any, pose_confidence: float
) -> str | None:
    if status != "confirmed":
        return f"object_status_{status}"
    if pose is None:
        return "object_pose_unavailable"
    if pose_confidence < 0.35:
        return "localization_confidence_low"
    return None


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
