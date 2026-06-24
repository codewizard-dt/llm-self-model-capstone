"""The runtime ContractLine envelope, its vision sub-models, and typed task lines."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from contracts.motor_telemetry import ContractSource, MotorApiSample, StrictModel
from contracts.task_contracts import ScoreGap, ScoreObserved, ScorePredicted


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

    @model_validator(mode="after")
    def _enforce_typed_task_blocks(self) -> ContractLine:
        """Hold typed tasks to their block contracts.

        The flexible `predicted` / `gap` / `outcome` dicts stay the default for
        not-yet-specified tasks. The `score` task is validated against its typed
        blocks, so a missing or mistyped `ball_in_bin` (etc.) is rejected here
        rather than silently passing as a free-form dict. Subclasses that already
        type these fields (e.g. `ScoreContractLine`) are skipped.
        """
        if type(self) is ContractLine and self.task == "score":
            try:
                ScorePredicted.model_validate(self.predicted)
                ScoreGap.model_validate(self.gap)
                if self.outcome is None:
                    raise ValueError("score task requires a typed `outcome` (with ball_in_bin)")
                ScoreObserved.model_validate(self.outcome)
            except ValidationError as exc:
                raise ValueError(f"invalid score task blocks: {exc}") from exc
        return self


class ScoreContractLine(ContractLine):
    """Fully-typed `score` contract line — the typed successor to `ScoreContract`.

    Same envelope as `ContractLine`, but `predicted` / `gap` / `outcome` are the
    typed score blocks and `task` is pinned to `"score"`. Use this when you want
    attribute access (`line.outcome.ball_in_bin`) and a schema that documents the
    score fields; `ContractLine` itself still enforces the same blocks for a
    `task == "score"` line via the validator above.
    """

    task: Literal["score"] = "score"
    predicted: ScorePredicted
    gap: ScoreGap
    outcome: ScoreObserved
