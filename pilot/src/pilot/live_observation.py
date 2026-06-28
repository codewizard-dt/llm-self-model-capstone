"""ROS-free mapping from live JSON payloads into pilot observations."""

from __future__ import annotations

import math
from typing import Any, Literal, Mapping

from contracts import (
    BridgeHealth,
    ImageBox,
    LocalizationState,
    ManipulatorState,
    PilotObservation,
    PilotTaskPhase,
    Pose2D,
    VisibleObject,
    VisibleTag,
)

from pilot.observation import (
    ObservationCache,
    build_observation_snapshot,
    stale_bridge,
    unknown_localization,
    unknown_manipulator,
)

BridgeState = Literal["ok", "degraded", "fault", "stale"]
ClawState = Literal["open", "closed", "holding", "unknown"]


def build_live_observation(
    *,
    objective: str | None,
    observed_ms: int,
    agent_scene: Mapping[str, Any] | None = None,
    scene_map: Mapping[str, Any] | None = None,
    object_tracks: Mapping[str, Any] | None = None,
    telemetry: Mapping[str, Any] | None = None,
    bridge_status: Mapping[str, Any] | None = None,
    task_plan: Mapping[str, Any] | None = None,
    operator_status: Mapping[str, Any] | None = None,
    task_phase: PilotTaskPhase | str | None = None,
) -> PilotObservation:
    """Build a contract-valid pilot observation from live ROS JSON-style payloads."""
    cache = build_live_observation_cache(
        objective=objective,
        observed_ms=observed_ms,
        agent_scene=agent_scene,
        scene_map=scene_map,
        object_tracks=object_tracks,
        telemetry=telemetry,
        bridge_status=bridge_status,
        task_plan=task_plan,
        operator_status=operator_status,
        task_phase=task_phase,
    )
    return build_observation_snapshot(cache, observed_ms=observed_ms)


def build_live_observation_cache(
    *,
    objective: str | None,
    observed_ms: int,
    agent_scene: Mapping[str, Any] | None = None,
    scene_map: Mapping[str, Any] | None = None,
    object_tracks: Mapping[str, Any] | None = None,
    telemetry: Mapping[str, Any] | None = None,
    bridge_status: Mapping[str, Any] | None = None,
    task_plan: Mapping[str, Any] | None = None,
    operator_status: Mapping[str, Any] | None = None,
    task_phase: PilotTaskPhase | str | None = None,
) -> ObservationCache:
    """Normalize live payload fragments into an immutable observation cache."""
    agent = _mapping(agent_scene)
    scene = _mapping(scene_map)
    tracks = _mapping(object_tracks)
    tel = _mapping(telemetry)
    bridge = _mapping(bridge_status)
    plan = _mapping(task_plan)
    operator = _mapping(operator_status)

    robot = _mapping(agent.get("robot"))
    health = _mapping(agent.get("health"))
    robot_pose = _pose_from_mapping(
        _first_mapping(robot.get("pose"), agent.get("robot_pose"), scene.get("robot_pose"))
    )

    return ObservationCache.from_inputs(
        objective=objective,
        task_phase=_task_phase(task_phase, agent, plan),
        robot_pose=robot_pose,
        localization=_localization(agent, scene, robot_pose),
        visible_objects=_visible_objects(agent, scene, tracks),
        visible_tags=_visible_tags(agent, scene),
        manipulator=_manipulator(robot, tel, operator),
        bridge=_bridge_health(
            robot,
            health,
            tel,
            bridge,
            observed_ms=observed_ms,
        ),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_mapping(*values: Any) -> Mapping[str, Any]:
    for value in values:
        mapped = _mapping(value)
        if mapped:
            return mapped
    return {}


def _items(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [_mapping(item) for item in value.values() if isinstance(item, Mapping)]
    if isinstance(value, list | tuple):
        return [_mapping(item) for item in value if isinstance(item, Mapping)]
    return []


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return None


def _first_not_none(*values: int | None) -> int | None:
    for value in values:
        if value is not None:
            return value
    return None


def _confidence(value: Any) -> float:
    raw = _float(value)
    if raw is None:
        return 0.0
    return max(0.0, min(1.0, raw))


def _age_ms(payload: Mapping[str, Any], *names: str) -> int | None:
    for name in (*names, "age_ms", "pose_age_ms"):
        age = _int(payload.get(name))
        if age is not None:
            return max(0, age)
    for name in ("pose_age_s", "age_s", "dead_reckoning_age_s"):
        age_s = _float(payload.get(name))
        if age_s is not None:
            return max(0, int(round(age_s * 1000)))
    return None


def _pose_from_mapping(payload: Mapping[str, Any]) -> Pose2D | None:
    x_m = _float(payload.get("x_m", payload.get("x")))
    y_m = _float(payload.get("y_m", payload.get("y")))
    if x_m is None or y_m is None:
        return None

    heading_rad = _float(payload.get("heading_rad"))
    if heading_rad is None:
        heading_rad = _float(payload.get("yaw_rad"))
    if heading_rad is None:
        heading_rad = _float(payload.get("heading"))
    if heading_rad is None:
        heading_deg = _float(payload.get("heading_deg"))
        heading_rad = None if heading_deg is None else math.radians(heading_deg)
    if heading_rad is None:
        heading_rad = 0.0

    return Pose2D(x_m=x_m, y_m=y_m, heading_rad=heading_rad)


def _localization(
    agent: Mapping[str, Any],
    scene: Mapping[str, Any],
    robot_pose: Pose2D | None,
) -> LocalizationState:
    robot = _mapping(agent.get("robot"))
    localization = _first_mapping(agent.get("localization"), scene.get("localization"))
    pose = robot_pose if localization else None
    confidence = _confidence(
        localization.get(
            "confidence",
            localization.get("pose_confidence", robot.get("pose_confidence")),
        )
    )
    age_ms = _first_not_none(_age_ms(localization), _age_ms(robot), 0)

    if pose is None and confidence == 0.0 and age_ms == 0:
        return unknown_localization()
    return LocalizationState(pose=pose, confidence=confidence, age_ms=age_ms)


def _visible_objects(
    agent: Mapping[str, Any],
    scene: Mapping[str, Any],
    object_tracks: Mapping[str, Any],
) -> list[VisibleObject]:
    source_items = _items(agent.get("objects"))
    if not source_items:
        source_items = _items(object_tracks.get("tracks"))
    if not source_items:
        source_items = _items(scene.get("objects"))

    objects: list[VisibleObject] = []
    for index, item in enumerate(source_items, start=1):
        status = _str(item.get("status"))
        if status is not None and status.casefold() not in {"confirmed", "visible", "tracked"}:
            continue

        label = _str(item.get("label", item.get("class", item.get("name")))) or "object"
        object_id = _str(item.get("object_id", item.get("id", item.get("track_id"))))
        if object_id is None:
            object_id = f"{label}_{index:02d}"
        objects.append(
            VisibleObject(
                object_id=object_id,
                label=label,
                confidence=_confidence(item.get("confidence")),
                bbox=_image_box(item),
            )
        )
    return objects


def _image_box(item: Mapping[str, Any]) -> ImageBox | None:
    box = _mapping(
        item.get("bbox") or item.get("image_box") or item.get("box") or item.get("bbox_xywh")
    )
    if box:
        x_px = _int(box.get("x_px", box.get("x")))
        y_px = _int(box.get("y_px", box.get("y")))
        width_px = _int(box.get("width_px", box.get("width", box.get("w"))))
        height_px = _int(box.get("height_px", box.get("height", box.get("h"))))
        if (
            None not in {x_px, y_px, width_px, height_px}
            and (width_px or 0) > 0
            and (height_px or 0) > 0
        ):
            return ImageBox(
                x_px=x_px or 0,
                y_px=y_px or 0,
                width_px=width_px or 0,
                height_px=height_px or 0,
            )

    xyxy = item.get("bbox_xyxy")
    if isinstance(xyxy, list | tuple) and len(xyxy) == 4:
        x0 = _int(xyxy[0])
        y0 = _int(xyxy[1])
        x1 = _int(xyxy[2])
        y1 = _int(xyxy[3])
        if None not in {x0, y0, x1, y1} and (x1 or 0) > (x0 or 0) and (y1 or 0) > (y0 or 0):
            return ImageBox(
                x_px=x0 or 0,
                y_px=y0 or 0,
                width_px=(x1 or 0) - (x0 or 0),
                height_px=(y1 or 0) - (y0 or 0),
            )
    return None


def _visible_tags(agent: Mapping[str, Any], scene: Mapping[str, Any]) -> list[VisibleTag]:
    source_items = _items(agent.get("visible_tags"))
    if source_items:
        source_items = [item for item in source_items if _bool(item.get("visible")) is not False]
    if not source_items:
        tags = scene.get("tags")
        if isinstance(tags, Mapping):
            source_items = [
                {"tag_id": tag_id, "pose": pose}
                for tag_id, pose in tags.items()
                if isinstance(pose, Mapping)
            ]

    tags: list[VisibleTag] = []
    for item in source_items:
        tag_id = _int(item.get("tag_id", item.get("id")))
        if tag_id is None:
            continue
        tags.append(
            VisibleTag(
                tag_id=tag_id,
                family=_str(item.get("family")) or "tag36h11",
                confidence=_confidence(item.get("confidence")),
                pose=_pose_from_mapping(_mapping(item.get("pose")) or item),
            )
        )
    return tags


def _manipulator(
    robot: Mapping[str, Any],
    telemetry: Mapping[str, Any],
    operator: Mapping[str, Any],
) -> ManipulatorState:
    payloads = (operator, telemetry, robot)
    arm_deg = None
    for payload in payloads:
        arm_deg = _float(
            payload.get(
                "arm_deg",
                payload.get("arm_position_deg", payload.get("arm_angle_deg")),
            )
        )
        if arm_deg is not None:
            break
    if arm_deg is None:
        arm_deg = _arm_deg_from_samples(telemetry)

    held_object_id = _held_object_id(operator, telemetry, robot)
    claw_state = _claw_state(operator, telemetry, robot, held_object_id)
    if arm_deg is None and claw_state == "unknown" and held_object_id is None:
        return unknown_manipulator()
    return ManipulatorState(
        arm_deg=arm_deg,
        claw_state=claw_state,
        held_object_id=held_object_id,
    )


def _arm_deg_from_samples(telemetry: Mapping[str, Any]) -> float | None:
    for sample in _items(telemetry.get("motor_samples")):
        device = (_str(sample.get("device")) or "").casefold()
        subsystem = (_str(sample.get("subsystem")) or "").casefold()
        if "arm" in {device, subsystem}:
            return _float(sample.get("position_deg"))
    return None


def _held_object_id(*payloads: Mapping[str, Any]) -> str | None:
    for payload in payloads:
        held = payload.get("held_object_id", payload.get("held_object", payload.get("holding")))
        if isinstance(held, Mapping):
            held = held.get("id", held.get("object_id"))
        if isinstance(held, bool):
            continue
        held_id = _str(held)
        if held_id is not None:
            return held_id
    return None


def _claw_state(
    operator: Mapping[str, Any],
    telemetry: Mapping[str, Any],
    robot: Mapping[str, Any],
    held_object_id: str | None,
) -> ClawState:
    if held_object_id is not None:
        return "holding"
    for payload in (operator, telemetry, robot):
        raw_state = _str(payload.get("claw_state", payload.get("claw")))
        if raw_state is not None and raw_state.casefold() in {
            "open",
            "closed",
            "holding",
            "unknown",
        }:
            return raw_state.casefold()  # type: ignore[return-value]
        if _bool(payload.get("claw_open")) is True:
            return "open"
        if _bool(payload.get("claw_closed")) is True:
            return "closed"
        if _bool(payload.get("holding")) is True:
            return "holding"
    return "unknown"


def _bridge_health(
    robot: Mapping[str, Any],
    health: Mapping[str, Any],
    telemetry: Mapping[str, Any],
    bridge_status: Mapping[str, Any],
    *,
    observed_ms: int,
) -> BridgeHealth:
    if not robot and not telemetry and not bridge_status:
        return stale_bridge()
    if health.get("bridge_status_available") is False and not bridge_status:
        return stale_bridge()

    state = _bridge_state(robot, bridge_status)
    heartbeat_age_ms = _heartbeat_age_ms(robot, telemetry, bridge_status, observed_ms=observed_ms)
    estop = (
        _bool(robot.get("estop"))
        if "estop" in robot
        else _bool(telemetry.get("estop"))
        if "estop" in telemetry
        else _bool(bridge_status.get("estop"))
    )
    battery_pct = _float(
        telemetry.get(
            "battery_pct",
            telemetry.get("battery_percent", bridge_status.get("battery_pct")),
        )
    )
    fault = _str(
        robot.get(
            "bridge_fault",
            bridge_status.get("fault", bridge_status.get("reason", bridge_status.get("message"))),
        )
    )

    return BridgeHealth(
        state=state,
        last_heartbeat_age_ms=heartbeat_age_ms,
        estop=bool(estop),
        battery_pct=battery_pct,
        fault=fault,
    )


def _bridge_state(robot: Mapping[str, Any], bridge_status: Mapping[str, Any]) -> BridgeState:
    raw = _str(robot.get("bridge_status", bridge_status.get("state", bridge_status.get("status"))))
    if raw is None:
        return "stale"
    normalized = raw.casefold()
    if normalized in {"ok", "degraded", "fault", "stale"}:
        return normalized  # type: ignore[return-value]
    if normalized in {"error", "failed", "serial_disconnect", "serial_unavailable"}:
        return "fault"
    if normalized in {"unknown", "unavailable", "missing"}:
        return "stale"
    return "degraded"


def _heartbeat_age_ms(
    robot: Mapping[str, Any],
    telemetry: Mapping[str, Any],
    bridge_status: Mapping[str, Any],
    *,
    observed_ms: int,
) -> int | None:
    age_ms = _first_not_none(
        _heartbeat_age_from_payload(robot),
        _heartbeat_age_from_payload(telemetry),
        _heartbeat_age_from_payload(bridge_status),
    )
    if age_ms is not None:
        return age_ms
    source_observed_ms = _int(bridge_status.get("observed_ms"))
    if source_observed_ms is None:
        return None
    return max(0, observed_ms - source_observed_ms)


def _heartbeat_age_from_payload(payload: Mapping[str, Any]) -> int | None:
    for name in ("last_heartbeat_age_ms", "heartbeat_age_ms"):
        age_ms = _int(payload.get(name))
        if age_ms is not None:
            return max(0, age_ms)
    for name in ("last_heartbeat_age_s", "heartbeat_age_s"):
        age_s = _float(payload.get(name))
        if age_s is not None:
            return max(0, int(round(age_s * 1000)))
    return None


def _task_phase(
    explicit: PilotTaskPhase | str | None,
    agent: Mapping[str, Any],
    task_plan: Mapping[str, Any],
) -> PilotTaskPhase:
    for value in (
        explicit,
        agent.get("task_phase"),
        _mapping(agent.get("task_plan")).get("phase"),
        task_plan.get("phase"),
        task_plan.get("task_phase"),
    ):
        if value is None:
            continue
        try:
            return PilotTaskPhase(value)
        except ValueError:
            continue
    return PilotTaskPhase.IDLE


__all__ = [
    "build_live_observation",
    "build_live_observation_cache",
]
