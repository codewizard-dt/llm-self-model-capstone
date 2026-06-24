"""The runtime SelfModel envelope (F2) and its layered sub-models.

Strictly additive over F1: reuses F1's `StrictModel` base and does not touch any
frozen telemetry contract. `SelfModelConfig` types its six axes against the
shared `contracts.vocabulary` enums (single source of truth, D1).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from contracts.motor_telemetry import StrictModel
from contracts.vocabulary import (
    ArmGearRatio,
    ArmPosition,
    Cartridge,
    EndEffector,
    MotorAllocation,
    WheelConfig,
)


class SelfModelConfig(StrictModel):
    # Reuse F1's StrictModel for extra="forbid"; relax strict so JSON string
    # inputs coerce into the StrEnum vocabulary (fixtures are plain JSON).
    model_config = ConfigDict(extra="forbid", strict=False)
    motor_allocation: MotorAllocation
    arm_position: ArmPosition
    end_effector: EndEffector
    wheel_config: WheelConfig
    arm_gear_ratio: ArmGearRatio
    cartridge: Cartridge


class Part(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    type: str


class Connection(BaseModel):
    model_config = ConfigDict(extra="allow")
    source: str
    target: str
    kind: str


class StructuralLayer(BaseModel):
    parts: list[Part] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)


class CapabilityLayer(StrictModel):
    # Reuse F1's StrictModel for extra="forbid"; relax strict so JSON int/float
    # inputs coerce into the float fields.
    model_config = ConfigDict(extra="forbid", strict=False)
    reach_mm: float = 0
    max_grip_force_N: float = 0
    max_pull_force_N: float = 0
    com_height_mm: float = 0


class SelfModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: Literal["1.0"] = "1.0"
    generation: int = Field(ge=0)
    parent_generation: int | None = None
    config: SelfModelConfig
    structural: StructuralLayer
    capability: CapabilityLayer
    predictive: dict[str, dict[str, float | bool | str]]
    gap_model: dict[str, dict[str, float]]
    # One keyed rationale per change/choice (PR #13 review): e.g. an
    # `end_effector` change carries its own line, and a generation that changes
    # `end_effector` and `cartridge` carries a line for each. Gen 0 keys by its
    # initial structural choices.
    reasoning: dict[str, str] = Field(min_length=1)

    @field_validator("reasoning")
    @classmethod
    def reasoning_entries_are_nonempty(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not str(rationale).strip() for rationale in value.values()):
            raise ValueError("each reasoning entry must be a non-empty rationale")
        return value

    @model_validator(mode="after")
    def enforce_lineage(self) -> SelfModel:
        if self.generation == 0:
            if self.parent_generation is not None:
                raise ValueError("generation 0 must have parent_generation = None")
        else:
            if self.parent_generation is None:
                raise ValueError("generation > 0 must have an int parent_generation")
            if self.parent_generation >= self.generation:
                raise ValueError("parent_generation must be strictly less than generation")
        return self
