from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping

DEFAULT_CAMERA_IN_ROBOT = '{"x_m":-0.3302,"y_m":0.1143,"yaw_rad":0.0}'


def normalize_angle(rad: float) -> float:
    return math.atan2(math.sin(rad), math.cos(rad))


@dataclass(frozen=True)
class Pose2D:
    """Planar pose in meters using +x forward and +y left in the named frame."""

    x_m: float
    y_m: float
    yaw_rad: float = 0.0

    def compose(self, other: Pose2D) -> Pose2D:
        cos_yaw = math.cos(self.yaw_rad)
        sin_yaw = math.sin(self.yaw_rad)
        return Pose2D(
            x_m=self.x_m + cos_yaw * other.x_m - sin_yaw * other.y_m,
            y_m=self.y_m + sin_yaw * other.x_m + cos_yaw * other.y_m,
            yaw_rad=normalize_angle(self.yaw_rad + other.yaw_rad),
        )

    def inverse(self) -> Pose2D:
        cos_yaw = math.cos(self.yaw_rad)
        sin_yaw = math.sin(self.yaw_rad)
        return Pose2D(
            x_m=-(cos_yaw * self.x_m + sin_yaw * self.y_m),
            y_m=sin_yaw * self.x_m - cos_yaw * self.y_m,
            yaw_rad=normalize_angle(-self.yaw_rad),
        )

    def to_json(self) -> dict[str, float]:
        return {
            "x_m": self.x_m,
            "y_m": self.y_m,
            "yaw_rad": self.yaw_rad,
            "x_mm": self.x_m * 1000.0,
            "y_mm": self.y_m * 1000.0,
            "heading_deg": math.degrees(self.yaw_rad),
        }


@dataclass(frozen=True)
class TagAnchor:
    tag_id: int
    map_from_tag: Pose2D
    label: str | None = None


@dataclass(frozen=True)
class TagDetection2D:
    tag_id: int
    camera_from_tag: Pose2D
    stamp_s: float
    confidence: float | None = None


@dataclass(frozen=True)
class ObjectObservation:
    name: str
    camera_from_object: Pose2D
    stamp_s: float
    confidence: float | None = None
    source: str = "operator_indication"
    object_id: str | None = None
    status: str = "confirmed"
    seen_frames: int | None = None
    last_seen_s: float | None = None
    age_s: float | None = None
    range_source: str | None = None
    position_uncertainty_m: float | None = None


@dataclass(frozen=True)
class SceneObject:
    name: str
    map_from_object: Pose2D
    source: str
    confidence: float | None = None
    object_id: str | None = None
    status: str = "confirmed"
    seen_frames: int | None = None
    last_seen_s: float | None = None
    age_s: float | None = None
    range_source: str | None = None
    position_uncertainty_m: float | None = None


@dataclass(frozen=True)
class SceneMap:
    frame_id: str
    stamp_s: float
    map_from_camera: Pose2D
    map_from_robot: Pose2D
    tags: dict[int, Pose2D]
    objects: list[SceneObject]
    anchor_tag_ids: list[int]
    observed_tag_ids: list[int]
    localization: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "stamp_s": self.stamp_s,
            "camera_pose": self.map_from_camera.to_json(),
            "robot_pose": self.map_from_robot.to_json(),
            "tags": {
                str(tag_id): pose.to_json()
                for tag_id, pose in sorted(self.tags.items())
            },
            "objects": [
                _strip_none(
                    {
                        "id": obj.object_id,
                        "name": obj.name,
                        "class": obj.name,
                        "pose": obj.map_from_object.to_json(),
                        "map_pose": obj.map_from_object.to_json(),
                        "source": obj.source,
                        "confidence": obj.confidence,
                        "status": obj.status,
                        "seen_frames": obj.seen_frames,
                        "last_seen_s": obj.last_seen_s,
                        "age_s": obj.age_s,
                        "range_source": obj.range_source,
                        "position_uncertainty_m": obj.position_uncertainty_m,
                    }
                )
                for obj in self.objects
            ],
            "anchor_tag_ids": self.anchor_tag_ids,
            "observed_tag_ids": self.observed_tag_ids,
            "localization": self.localization
            or {
                "source": "apriltag",
                "pose_confidence": 1.0,
                "pose_age_s": 0.0,
                "visible_anchor_count": len(self.observed_tag_ids),
                "tag_residual_m": 0.0,
                "tag_residual_deg": 0.0,
            },
        }

    def to_json_string(self) -> str:
        return json.dumps(self.to_json(), separators=(",", ":"), sort_keys=True)


def pose_from_mapping(raw: Mapping[str, Any]) -> Pose2D:
    if "x_mm" in raw or "y_mm" in raw:
        yaw = (
            math.radians(float(raw["heading_deg"]))
            if "heading_deg" in raw
            else float(raw.get("yaw_rad", 0.0))
        )
        return Pose2D(
            x_m=float(raw.get("x_mm", 0.0)) / 1000.0,
            y_m=float(raw.get("y_mm", 0.0)) / 1000.0,
            yaw_rad=yaw,
        )
    return Pose2D(
        x_m=float(raw.get("x_m", raw.get("x", 0.0))),
        y_m=float(raw.get("y_m", raw.get("y", 0.0))),
        yaw_rad=float(raw.get("yaw_rad", raw.get("heading", 0.0))),
    )


def parse_tag_anchors(raw: str | Mapping[str, Any]) -> dict[int, TagAnchor]:
    payload: Mapping[str, Any]
    if isinstance(raw, str):
        payload = json.loads(raw)
    else:
        payload = raw

    anchors: dict[int, TagAnchor] = {}
    if isinstance(payload.get("tags"), list):
        for item in payload["tags"]:
            if not isinstance(item, Mapping):
                raise ValueError("workspace map tags must be JSON objects")
            tag_id = int(item["id"])
            anchors[tag_id] = TagAnchor(
                tag_id=tag_id,
                map_from_tag=pose_from_mapping(item["pose"]),
                label=str(item.get("role", item.get("description", tag_id))),
            )
        return anchors

    for key, value in payload.items():
        if not isinstance(value, Mapping):
            raise ValueError(f"tag anchor {key!r} must be an object")
        tag_id = int(value.get("tag_id", key))
        anchors[tag_id] = TagAnchor(
            tag_id=tag_id,
            map_from_tag=pose_from_mapping(value),
            label=str(value["label"]) if "label" in value else None,
        )
    return anchors


def parse_object_observations(
    raw: str | Mapping[str, Any] | list[Mapping[str, Any]], *, stamp_s: float
) -> list[ObjectObservation]:
    payload: Any
    if isinstance(raw, str):
        payload = json.loads(raw)
    else:
        payload = raw
    if isinstance(payload, Mapping):
        payload = payload.get("tracks", payload.get("objects", [payload]))
    if not isinstance(payload, list):
        raise ValueError("object indications must be a JSON object or list")

    observations: list[ObjectObservation] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("each object indication must be a JSON object")
        status = str(item.get("status", "confirmed"))
        if status == "expired":
            continue
        name = str(item.get("name", item.get("class", "object")))
        camera_pose = item.get("camera_pose")
        if isinstance(camera_pose, Mapping):
            if "forward_m" in camera_pose or "left_m" in camera_pose:
                pose = Pose2D(
                    x_m=float(camera_pose.get("forward_m", 0.0)),
                    y_m=float(camera_pose.get("left_m", 0.0)),
                    yaw_rad=float(camera_pose.get("yaw_rad", 0.0)),
                )
            else:
                pose = pose_from_mapping(camera_pose)
        elif "forward_m" in item or "left_m" in item:
            pose = Pose2D(
                x_m=float(item.get("forward_m", 0.0)),
                y_m=float(item.get("left_m", 0.0)),
                yaw_rad=float(item.get("yaw_rad", 0.0)),
            )
        else:
            pose = pose_from_mapping(item)
        observations.append(
            ObjectObservation(
                name=name,
                camera_from_object=pose,
                stamp_s=float(item.get("stamp_s", stamp_s)),
                confidence=(
                    float(item["confidence"]) if "confidence" in item else None
                ),
                source=str(item.get("source", "operator_indication")),
                object_id=(
                    str(item["id"])
                    if item.get("id") is not None
                    else (
                        str(item["track_id"])
                        if item.get("track_id") is not None
                        else None
                    )
                ),
                status=status,
                seen_frames=(
                    int(item["seen_frames"])
                    if item.get("seen_frames") is not None
                    else None
                ),
                last_seen_s=(
                    float(item["last_seen_s"])
                    if item.get("last_seen_s") is not None
                    else None
                ),
                age_s=float(item["age_s"]) if item.get("age_s") is not None else None,
                range_source=(
                    str(item["range_source"])
                    if item.get("range_source") is not None
                    else None
                ),
                position_uncertainty_m=(
                    float(item["position_uncertainty_m"])
                    if item.get("position_uncertainty_m") is not None
                    else None
                ),
            )
        )
    return observations


def camera_from_apriltag_translation(
    *, optical_x_m: float, optical_z_m: float, yaw_rad: float = 0.0
) -> Pose2D:
    """Convert ROS optical-frame tag translation into the planar camera frame.

    ROS optical frames use +x right and +z forward. The planar map layer uses
    +x forward and +y left, so optical x changes sign.
    """

    return Pose2D(x_m=float(optical_z_m), y_m=-float(optical_x_m), yaw_rad=yaw_rad)


def robot_from_camera_pose(camera_from_pose: Pose2D, camera_in_robot: Pose2D) -> Pose2D:
    """Transform a camera-relative planar pose into the calibrated robot frame."""

    return camera_in_robot.compose(camera_from_pose)


def tag_id_from_frame_id(frame_id: str, *, family: str = "tag36h11") -> int | None:
    frame = frame_id.strip().lstrip("/")
    prefixes = (f"{family}_", "tag_")
    for prefix in prefixes:
        if not frame.startswith(prefix):
            continue
        suffix = frame.removeprefix(prefix)
        if suffix.isdigit():
            return int(suffix)
    return None


def estimate_camera_pose(
    anchors: Mapping[int, TagAnchor],
    detections: list[TagDetection2D],
) -> Pose2D:
    candidates = estimate_camera_pose_candidates(anchors, detections)
    if not candidates:
        raise ValueError("at least one observed tag must match a configured map anchor")
    return average_poses(candidates)


def estimate_camera_pose_candidates(
    anchors: Mapping[int, TagAnchor],
    detections: list[TagDetection2D],
) -> list[Pose2D]:
    candidates: list[Pose2D] = []
    for detection in detections:
        anchor = anchors.get(detection.tag_id)
        if anchor is None:
            continue
        candidates.append(
            anchor.map_from_tag.compose(detection.camera_from_tag.inverse())
        )
    return candidates


def average_poses(poses: list[Pose2D]) -> Pose2D:
    if not poses:
        raise ValueError("cannot average an empty pose list")
    return Pose2D(
        x_m=sum(p.x_m for p in poses) / len(poses),
        y_m=sum(p.y_m for p in poses) / len(poses),
        yaw_rad=math.atan2(
            sum(math.sin(p.yaw_rad) for p in poses),
            sum(math.cos(p.yaw_rad) for p in poses),
        ),
    )


def build_scene_map(
    *,
    anchors: Mapping[int, TagAnchor],
    detections: list[TagDetection2D],
    object_observations: list[ObjectObservation] | None = None,
    camera_in_robot: Pose2D | None = None,
    frame_id: str = "map",
    stamp_s: float | None = None,
) -> SceneMap:
    pose_candidates = estimate_camera_pose_candidates(anchors, detections)
    if not pose_candidates:
        raise ValueError("at least one observed tag must match a configured map anchor")
    map_from_camera = average_poses(pose_candidates)
    robot_from_camera = camera_in_robot or Pose2D(0.0, 0.0, 0.0)
    map_from_robot = map_from_camera.compose(robot_from_camera.inverse())
    tags = {
        detection.tag_id: map_from_camera.compose(detection.camera_from_tag)
        for detection in detections
    }
    objects = [
        SceneObject(
            name=observation.name,
            map_from_object=map_from_camera.compose(observation.camera_from_object),
            source=observation.source,
            confidence=observation.confidence,
            object_id=observation.object_id,
            status=observation.status,
            seen_frames=observation.seen_frames,
            last_seen_s=observation.last_seen_s,
            age_s=observation.age_s,
            range_source=observation.range_source,
            position_uncertainty_m=observation.position_uncertainty_m,
        )
        for observation in object_observations or []
    ]
    scene_stamp_s = (
        float(stamp_s)
        if stamp_s is not None
        else max(detection.stamp_s for detection in detections)
    )
    return SceneMap(
        frame_id=frame_id,
        stamp_s=scene_stamp_s,
        map_from_camera=map_from_camera,
        map_from_robot=map_from_robot,
        tags=tags,
        objects=objects,
        anchor_tag_ids=sorted(anchors),
        observed_tag_ids=sorted({detection.tag_id for detection in detections}),
        localization=_localization_summary(
            candidates=pose_candidates,
            detections=detections,
            stamp_s=scene_stamp_s,
            observed_anchor_ids=sorted({detection.tag_id for detection in detections}),
        ),
    )


def scene_map_from_json(raw: str | Mapping[str, Any]) -> SceneMap:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    objects = [
        SceneObject(
            name=str(item["name"]),
            map_from_object=pose_from_mapping(item["pose"]),
            source=str(item.get("source", "unknown")),
            confidence=(
                float(item["confidence"])
                if item.get("confidence") is not None
                else None
            ),
            object_id=str(item["id"]) if item.get("id") is not None else None,
            status=str(item.get("status", "confirmed")),
            seen_frames=(
                int(item["seen_frames"])
                if item.get("seen_frames") is not None
                else None
            ),
            last_seen_s=(
                float(item["last_seen_s"])
                if item.get("last_seen_s") is not None
                else None
            ),
            age_s=float(item["age_s"]) if item.get("age_s") is not None else None,
            range_source=(
                str(item["range_source"])
                if item.get("range_source") is not None
                else None
            ),
            position_uncertainty_m=(
                float(item["position_uncertainty_m"])
                if item.get("position_uncertainty_m") is not None
                else None
            ),
        )
        for item in payload.get("objects", [])
    ]
    return SceneMap(
        frame_id=str(payload.get("frame_id", "map")),
        stamp_s=float(payload.get("stamp_s", 0.0)),
        map_from_camera=pose_from_mapping(payload["camera_pose"]),
        map_from_robot=pose_from_mapping(payload["robot_pose"]),
        tags={
            int(tag_id): pose_from_mapping(pose)
            for tag_id, pose in payload.get("tags", {}).items()
        },
        objects=objects,
        anchor_tag_ids=[int(tag_id) for tag_id in payload.get("anchor_tag_ids", [])],
        observed_tag_ids=[
            int(tag_id) for tag_id in payload.get("observed_tag_ids", [])
        ],
        localization=dict(payload.get("localization") or {}),
    )


def _localization_summary(
    *,
    candidates: list[Pose2D],
    detections: list[TagDetection2D],
    stamp_s: float,
    observed_anchor_ids: list[int],
) -> dict[str, Any]:
    pose = average_poses(candidates)
    residuals_m = [
        math.hypot(item.x_m - pose.x_m, item.y_m - pose.y_m) for item in candidates
    ]
    residuals_deg = [
        abs(math.degrees(normalize_angle(item.yaw_rad - pose.yaw_rad)))
        for item in candidates
    ]
    mean_position_error_m = sum(residuals_m) / len(residuals_m)
    mean_heading_error_deg = sum(residuals_deg) / len(residuals_deg)
    max_position_error_m = max(residuals_m)
    confidence = localization_confidence(
        visible_anchor_count=len(observed_anchor_ids),
        tag_residual_m=mean_position_error_m,
        tag_residual_deg=mean_heading_error_deg,
    )
    latest_detection_s = max(detection.stamp_s for detection in detections)
    return {
        "source": "apriltag",
        "pose_confidence": confidence,
        "pose_age_s": max(0.0, stamp_s - latest_detection_s),
        "visible_anchor_count": len(observed_anchor_ids),
        "tag_residual_m": mean_position_error_m,
        "tag_residual_deg": mean_heading_error_deg,
        "max_position_error_m": max_position_error_m,
        "observed_tag_ids": observed_anchor_ids,
        "dead_reckoning_age_s": 0.0,
    }


def localization_confidence(
    *,
    visible_anchor_count: int,
    tag_residual_m: float,
    tag_residual_deg: float,
    pose_age_s: float = 0.0,
) -> float:
    if visible_anchor_count <= 0:
        return 0.0
    tag_bonus = 0.18 if visible_anchor_count >= 2 else 0.0
    residual_penalty = min(0.45, tag_residual_m * 3.0 + tag_residual_deg / 90.0)
    age_penalty = min(0.35, max(0.0, pose_age_s) * 0.12)
    return max(0.0, min(1.0, 0.72 + tag_bonus - residual_penalty - age_penalty))


def _strip_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_none(item) for key, item in value.items() if item is not None
        }
    if isinstance(value, list):
        return [_strip_none(item) for item in value]
    return value


def dataclass_to_dict(value: Any) -> dict[str, Any]:
    return asdict(value)
