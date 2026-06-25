from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Detection:
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    stamp_s: float | None = None

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
) -> dict[str, Any] | None:
    dims = dimensions.get(detection.label) or dimensions.get("*")
    height_m = None if dims is None else dims.effective_height_m
    width_m = None if dims is None else dims.effective_width_m
    if height_m is None and width_m is None and default_height_m is not None:
        height_m = default_height_m

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
    }


def indications_from_detections(
    detections: list[Detection],
    *,
    intrinsics: CameraIntrinsics,
    dimensions: Mapping[str, ObjectDimensions],
    default_height_m: float | None = None,
    min_confidence: float = 0.0,
    source: str = "yolo_ncnn",
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
