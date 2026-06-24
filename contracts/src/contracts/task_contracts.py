"""Typed per-task contract blocks for `predicted` / `outcome` / `gap`.

Restores the field-level guarantees the flexible `dict` edges on `ContractLine`
do not provide (PR #9 review): the `score` task is fully typed here, so
`ball_in_bin` and the score fields are *required and type-checked* rather than
free-form. Tasks that are not yet specified keep ContractLine's flexible dicts;
adding a typed task later is a new block in this module and never changes the
existing tasks — specificity without global rigidity.

These supersede the original `ScorePredicted` / `ScoreObserved` / `ScoreGap`
contracts that lived in the pre-migration `motor_telemetry.py`; the envelope
role of the old `BaseTaskContract` is now carried by `ContractLine`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TaskContractModel(BaseModel):
    """Base for typed task blocks.

    `extra="forbid"` rejects a missing or mistyped field (the guarantee the
    flexible dict lacks). Numeric coercion stays lenient (no model-wide
    `strict=True`) so an integer JSON value still satisfies a `float` field,
    while boolean fields opt into `strict=True` individually to keep the
    metric's integrity (a stray `"yes"` must not silently become `True`).
    """

    model_config = ConfigDict(extra="forbid")


class ScorePredicted(TaskContractModel):
    distance_from_bin_m: float = Field(ge=0.0)
    success: bool = Field(strict=True)


class ScoreObserved(TaskContractModel):
    ball_in_bin: bool = Field(strict=True)
    score_value: float = Field(ge=0.0)
    success: bool = Field(strict=True)
    distance_from_bin_m: float | None = Field(default=None, ge=0.0)


class ScoreGap(TaskContractModel):
    distance_error_m: float
    success_correct: bool | None = Field(default=None, strict=True)
