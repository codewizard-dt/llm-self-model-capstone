"""The runtime ContractLine envelope and its vision sub-models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from contracts.motor_telemetry import ContractSource, MotorApiSample, StrictModel


class AprilTagPose(StrictModel):
    x: float
    y: float
    heading: float


class VisionBlock(StrictModel):
    object_detected: bool
    object_bbox: list[int] | None = None
    apriltag_pose: AprilTagPose | None = None
    bbox_iou: float | None = None


class ContractLine(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: Literal["1.0"] = "1.0"
    session_id: str
    generation: int
    round: int
    task: str
    motor_samples: list[MotorApiSample] = Field(min_length=1)
    predicted: dict[str, float | bool | str]
    gap: dict[str, float]
    outcome: dict[str, Any] | None = None
    vision: VisionBlock | None = None
    source: ContractSource | None = None
