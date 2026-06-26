from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Detection:
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    stamp_s: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def width_px(self) -> float:
        x1, _, x2, _ = self.bbox_xyxy
        return max(0.0, x2 - x1)

    @property
    def height_px(self) -> float:
        _, y1, _, y2 = self.bbox_xyxy
        return max(0.0, y2 - y1)

    @property
    def center_px(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def to_json(self) -> dict[str, Any]:
        x1, y1, x2, y2 = self.bbox_xyxy
        cx, cy = self.center_px
        payload: dict[str, Any] = {
            "label": self.label,
            "class_id": self.class_id,
            "confidence": self.confidence,
            "bbox_xyxy": [x1, y1, x2, y2],
            "bbox_xywh": [x1, y1, self.width_px, self.height_px],
            "center_px": [cx, cy],
        }
        if self.stamp_s is not None:
            payload["stamp_s"] = self.stamp_s
        payload.update(self.metadata)
        return payload


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class ObjectDimensions:
    width_m: float | None = None
    height_m: float | None = None
    diameter_m: float | None = None

    @property
    def effective_width_m(self) -> float | None:
        return self.width_m if self.width_m is not None else self.diameter_m

    @property
    def effective_height_m(self) -> float | None:
        return self.height_m if self.height_m is not None else self.diameter_m


def detections_payload(
    *,
    detections: list[Detection],
    width: int,
    height: int,
    frame_id: str,
    stamp_s: float,
    model_path: str,
    source: str = "yolo_ncnn",
) -> str:
    return json.dumps(
        {
            "type": "object_detections",
            "source": source,
            "model_path": model_path,
            "frame_id": frame_id,
            "stamp_s": stamp_s,
            "image": {"width": width, "height": height},
            "detections": [detection.to_json() for detection in detections],
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def detections_source(raw: str | Mapping[str, Any]) -> str:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    return str(payload.get("source", "object_detector"))


def parse_detections_payload(raw: str | Mapping[str, Any]) -> list[Detection]:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    detections: list[Detection] = []
    for item in payload.get("detections", []):
        if not isinstance(item, Mapping):
            continue
        bbox = item.get("bbox_xyxy") or _xywh_to_xyxy(item.get("bbox_xywh"))
        if not bbox or len(bbox) != 4:
            continue
        detections.append(
            Detection(
                label=str(item.get("label", item.get("name", "object"))),
                class_id=int(item.get("class_id", item.get("class", -1))),
                confidence=float(item.get("confidence", 0.0)),
                bbox_xyxy=tuple(float(value) for value in bbox),  # type: ignore[arg-type]
                stamp_s=(
                    float(item["stamp_s"]) if item.get("stamp_s") is not None else None
                ),
                metadata={
                    key: item[key]
                    for key in (
                        "area_px",
                        "circularity",
                        "fill_ratio",
                        "source",
                    )
                    if key in item
                },
            )
        )
    return detections


def parse_dimensions_json(raw: str | Mapping[str, Any]) -> dict[str, ObjectDimensions]:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    dimensions: dict[str, ObjectDimensions] = {}
    for label, value in payload.items():
        if not isinstance(value, Mapping):
            raise ValueError(f"dimension entry {label!r} must be a JSON object")
        dimensions[str(label)] = ObjectDimensions(
            width_m=_optional_float(value.get("width_m")),
            height_m=_optional_float(value.get("height_m")),
            diameter_m=_optional_float(value.get("diameter_m")),
        )
    return dimensions


def indication_from_detection(
    detection: Detection,
    *,
    intrinsics: CameraIntrinsics,
    dimensions: Mapping[str, ObjectDimensions],
    default_height_m: float | None = None,
    source: str = "yolo_ncnn",
    floor_projection_enabled: bool = False,
    camera_height_m: float | None = None,
    camera_pitch_rad: float = 0.0,
) -> dict[str, Any] | None:
    dims = dimensions.get(detection.label) or dimensions.get("*")
    height_m = None if dims is None else dims.effective_height_m
    width_m = None if dims is None else dims.effective_width_m
    if height_m is None and width_m is None and default_height_m is not None:
        height_m = default_height_m

    range_source = "bbox_size"
    forward_m: float
    left_m: float
    projected = (
        floor_project_detection(
            detection,
            intrinsics=intrinsics,
            camera_height_m=camera_height_m,
            camera_pitch_rad=camera_pitch_rad,
        )
        if floor_projection_enabled
        else None
    )
    if projected is not None:
        forward_m, left_m = projected
        range_source = "floor_plane"
    else:
        distance_candidates: list[float] = []
        if height_m is not None and detection.height_px > 0:
            distance_candidates.append(intrinsics.fy * height_m / detection.height_px)
        if width_m is not None and detection.width_px > 0:
            distance_candidates.append(intrinsics.fx * width_m / detection.width_px)
        if not distance_candidates:
            return None

        forward_m = _median(distance_candidates)
        center_x, _ = detection.center_px
        optical_x_m = (center_x - intrinsics.cx) * forward_m / intrinsics.fx
        left_m = -optical_x_m

    uncertainty_m = position_uncertainty_m(
        range_source=range_source,
        forward_m=forward_m,
        confidence=detection.confidence,
    )
    return {
        "name": detection.label,
        "forward_m": forward_m,
        "left_m": left_m,
        "yaw_rad": math.atan2(left_m, forward_m),
        "confidence": detection.confidence,
        "source": source,
        "class_id": detection.class_id,
        "bbox_xyxy": list(detection.bbox_xyxy),
        "stamp_s": detection.stamp_s,
        "range_source": range_source,
        "position_uncertainty_m": uncertainty_m,
    }


def indications_from_detections(
    detections: list[Detection],
    *,
    intrinsics: CameraIntrinsics,
    dimensions: Mapping[str, ObjectDimensions],
    default_height_m: float | None = None,
    min_confidence: float = 0.0,
    source: str = "yolo_ncnn",
    floor_projection_enabled: bool = False,
    camera_height_m: float | None = None,
    camera_pitch_rad: float = 0.0,
) -> list[dict[str, Any]]:
    indications: list[dict[str, Any]] = []
    for detection in detections:
        if detection.confidence < min_confidence:
            continue
        indication = indication_from_detection(
            detection,
            intrinsics=intrinsics,
            dimensions=dimensions,
            default_height_m=default_height_m,
            source=source,
            floor_projection_enabled=floor_projection_enabled,
            camera_height_m=camera_height_m,
            camera_pitch_rad=camera_pitch_rad,
        )
        if indication is not None:
            indications.append(
                {key: value for key, value in indication.items() if value is not None}
            )
    return indications


def intrinsics_from_camera_info(k: list[float] | tuple[float, ...]) -> CameraIntrinsics:
    if len(k) != 9:
        raise ValueError("CameraInfo.k must contain 9 values")
    fx, fy = float(k[0]), float(k[4])
    if fx <= 0.0 or fy <= 0.0:
        raise ValueError("CameraInfo fx/fy must be positive")
    return CameraIntrinsics(fx=fx, fy=fy, cx=float(k[2]), cy=float(k[5]))


def floor_project_detection(
    detection: Detection,
    *,
    intrinsics: CameraIntrinsics,
    camera_height_m: float | None,
    camera_pitch_rad: float,
) -> tuple[float, float] | None:
    """Project the bbox bottom-center ray onto the floor plane.

    Optical frame convention is the ROS camera convention: +x right, +y down,
    +z forward. `camera_pitch_rad` is positive when the camera optical axis is
    pitched downward relative to horizontal.
    """

    if camera_height_m is None or camera_height_m <= 0.0:
        return None

    x1, _, x2, y2 = detection.bbox_xyxy
    u = (x1 + x2) / 2.0
    v = y2
    ray_right = (u - intrinsics.cx) / intrinsics.fx
    ray_down = (v - intrinsics.cy) / intrinsics.fy
    pitch = float(camera_pitch_rad)
    down_component = ray_down * math.cos(pitch) + math.sin(pitch)
    forward_component = math.cos(pitch) - ray_down * math.sin(pitch)
    if down_component <= 1e-6 or forward_component <= 0.0:
        return None

    scale = float(camera_height_m) / down_component
    forward_m = forward_component * scale
    left_m = -ray_right * scale
    return forward_m, left_m


def position_uncertainty_m(
    *, range_source: str, forward_m: float, confidence: float
) -> float:
    confidence_penalty = max(0.0, 1.0 - max(0.0, min(1.0, confidence)))
    if range_source == "floor_plane":
        return max(0.04, 0.05 + 0.04 * abs(forward_m) + 0.10 * confidence_penalty)
    return max(0.08, 0.10 + 0.08 * abs(forward_m) + 0.18 * confidence_penalty)


def _xywh_to_xyxy(value: Any) -> list[float] | None:
    if not value or len(value) != 4:
        return None
    x, y, width, height = (float(item) for item in value)
    return [x, y, x + width, y + height]


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0
