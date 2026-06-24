"""The parts catalog grammar (F3): legal-config model + buildability engine.

`PartsCatalog` is the pydantic v2 data model for `parts_catalog.json` — the six
config axes (typed against the shared `contracts.vocabulary` enums, D1) plus a
typed `CatalogConstraints` sub-model carrying the machine-readable rule set (D4).
`validate_config` is the deterministic combinatorial-buildability engine that
consumes F2's `SelfModelConfig` (D3) and applies rules R1/R2/R3.

Strictly additive over F1+F2: this module never redefines a vocabulary value set
and never touches the frozen telemetry/self-model schemas. It answers only
deterministic structural buildability (motor budget, part availability); physics
(torque/CoM/geometry/reach) is F9's concern (D2).
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from contracts.motor_telemetry import StrictModel
from contracts.self_model import SelfModelConfig
from contracts.vocabulary import (
    ArmGearRatio,
    ArmPosition,
    Cartridge,
    EndEffector,
    MotorAllocation,
    WheelConfig,
)

# --- Rule codes (stable machine codes F8/F9 route on, D9) ------------------

CLAW_MOTOR_BUDGET = "CLAW_MOTOR_BUDGET"
FLYWHEEL_CARTRIDGE = "FLYWHEEL_CARTRIDGE"

# The single allocation that supplies the two manipulator motors a powered claw
# needs (arm-lift + claw). R1 (D7).
CLAW_REQUIRED_ALLOCATION = MotorAllocation.DRIVE2_ARM1_CLAW1

# The cartridge a flywheel requires (R3, D8 forward-only).
FLYWHEEL_REQUIRED_CARTRIDGE = Cartridge.RPM_600


# --- Verdict shapes (D9) ----------------------------------------------------


class Violation(StrictModel):
    """A single buildability failure: a stable code plus a human-readable message."""

    code: str
    message: str


class CatalogVerdict(StrictModel):
    """The result of validating one config against the catalog grammar."""

    buildable: bool
    violations: list[Violation] = Field(default_factory=list)


# --- Machine-readable constraint set (D4) -----------------------------------


class ClawMotorBudgetRule(StrictModel):
    """R1: a claw end effector requires the two-manipulator-motor allocation."""

    # strict=False so the committed JSON strings coerce into the StrEnum members
    # on round-trip (mirrors SelfModelConfig).
    model_config = ConfigDict(extra="forbid", strict=False)
    code: Literal["CLAW_MOTOR_BUDGET"] = CLAW_MOTOR_BUDGET
    when_end_effector: EndEffector = EndEffector.CLAW_GRASPER
    requires_motor_allocation: MotorAllocation = CLAW_REQUIRED_ALLOCATION


class FlywheelCartridgeRule(StrictModel):
    """R3: a flywheel end effector requires the 600rpm cartridge (forward-only)."""

    model_config = ConfigDict(extra="forbid", strict=False)
    code: Literal["FLYWHEEL_CARTRIDGE"] = FLYWHEEL_CARTRIDGE
    when_end_effector: EndEffector = EndEffector.FLYWHEEL
    requires_cartridge: Cartridge = FLYWHEEL_REQUIRED_CARTRIDGE


class CatalogConstraints(StrictModel):
    """The machine-readable rule set embedded in PartsCatalog / parts_catalog.json.

    R2 is intentionally unrepresented as a positive constraint: scoop/flywheel are
    valid on every remaining allocation (each supplies >=1 manipulator motor since
    `4drive` was dropped), so R2 imposes no allocation-grounds violation.
    """

    claw_motor_budget: ClawMotorBudgetRule = Field(default_factory=ClawMotorBudgetRule)
    flywheel_cartridge: FlywheelCartridgeRule = Field(default_factory=FlywheelCartridgeRule)


# --- The catalog data model -------------------------------------------------


class PartsCatalog(StrictModel):
    """The legal per-axis value sets plus the machine-readable constraints.

    Each axis field is typed against the IMPORTED `contracts.vocabulary` enum
    (D1) — the value sets are never redefined here. `extra="forbid"` is inherited
    from `StrictModel`; `strict=False` lets the committed JSON strings coerce into
    the StrEnum members on round-trip.
    """

    model_config = ConfigDict(extra="forbid", strict=False)

    schema_version: Literal["1.0"] = "1.0"
    motor_allocation: list[MotorAllocation]
    arm_position: list[ArmPosition]
    end_effector: list[EndEffector]
    wheel_config: list[WheelConfig]
    arm_gear_ratio: list[ArmGearRatio]
    cartridge: list[Cartridge]
    constraints: CatalogConstraints = Field(default_factory=CatalogConstraints)


# --- The buildability engine ------------------------------------------------


def validate_config(config: SelfModelConfig) -> CatalogVerdict:
    """Deterministically decide whether a config is buildable per R1/R2/R3.

    Reuses F2's `SelfModelConfig` (D3); judges only structural buildability
    (motor budget + flywheel cartridge), never physics (D2).
    """
    violations: list[Violation] = []

    # R1 (D7): a powered claw needs arm-lift + claw = two manipulator motors,
    # which only the 2drive+1arm+1claw allocation supplies.
    if (
        config.end_effector == EndEffector.CLAW_GRASPER
        and config.motor_allocation != CLAW_REQUIRED_ALLOCATION
    ):
        violations.append(
            Violation(
                code=CLAW_MOTOR_BUDGET,
                message=(
                    f"end_effector '{EndEffector.CLAW_GRASPER.value}' requires "
                    f"motor_allocation '{CLAW_REQUIRED_ALLOCATION.value}' "
                    f"(arm-lift + claw = 2 manipulator motors); got "
                    f"'{config.motor_allocation.value}'"
                ),
            )
        )

    # R2: scoop/flywheel need >=1 manipulator motor; every remaining allocation
    # supplies one, so no allocation-grounds violation is possible (4drive gone).

    # R3 (D8, forward-only): a flywheel requires the 600rpm cartridge. Claw/scoop
    # cartridge suitability is NOT judged here (F9's torque call).
    if (
        config.end_effector == EndEffector.FLYWHEEL
        and config.cartridge != FLYWHEEL_REQUIRED_CARTRIDGE
    ):
        violations.append(
            Violation(
                code=FLYWHEEL_CARTRIDGE,
                message=(
                    f"end_effector '{EndEffector.FLYWHEEL.value}' requires "
                    f"cartridge '{FLYWHEEL_REQUIRED_CARTRIDGE.value}'; got "
                    f"'{config.cartridge.value}'"
                ),
            )
        )

    return CatalogVerdict(buildable=not violations, violations=violations)


def enumerate_buildable() -> list[SelfModelConfig]:
    """Enumerate every config in the full vocabulary cross-product that is buildable.

    Deterministic order: axes iterate in their declared enum order. Used by the
    enumeration test asserting the legal design space is exactly 60 (D13).
    """
    buildable: list[SelfModelConfig] = []
    for motor_allocation in MotorAllocation:
        for arm_position in ArmPosition:
            for end_effector in EndEffector:
                for wheel_config in WheelConfig:
                    for arm_gear_ratio in ArmGearRatio:
                        for cartridge in Cartridge:
                            config = SelfModelConfig(
                                motor_allocation=motor_allocation,
                                arm_position=arm_position,
                                end_effector=end_effector,
                                wheel_config=wheel_config,
                                arm_gear_ratio=arm_gear_ratio,
                                cartridge=cartridge,
                            )
                            if validate_config(config).buildable:
                                buildable.append(config)
    return buildable
