"""The parts catalog grammar (F3): legal-config model + buildability engine.

`PartsCatalog` is the pydantic v2 data model for `parts_catalog.json` — the three
config axes (typed against the shared `contracts.vocabulary` enums, D1) plus a
typed `CatalogConstraints` sub-model carrying the machine-readable rule set (D4).
`validate_config` is the deterministic combinatorial-buildability engine that
consumes F2's `SelfModelConfig` (D3) and applies the rule set.

Post-PR-#16 review: `motor_allocation` is now effector-encoded (one allocation
per effector), `arm_position`/`arm_gear_ratio`/`wheel_config` were removed
(single-valued, no real choice), and `cartridge` dropped 100rpm. The rule set
grew accordingly — R1b/R1c pin each effector to its allocation, R4 pins the
claw cartridge — so F8/F9 can still route on stable, per-rule codes (D9).

Strictly bounded by F1+F2: this module never redefines a vocabulary value set
and never touches the frozen telemetry schemas. It answers only deterministic
structural buildability (motor budget, part availability, cartridge selection);
physics judgement (torque/CoM/geometry/reach) remains F9's concern (D2).
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from contracts.motor_telemetry import StrictModel
from contracts.self_model import SelfModelConfig
from contracts.vocabulary import Cartridge, EndEffector, MotorAllocation

# --- Rule codes (stable machine codes F8/F9 route on, D9) ------------------

CLAW_MOTOR_BUDGET = "CLAW_MOTOR_BUDGET"
SCOOP_ALLOCATION = "SCOOP_ALLOCATION"
FLYWHEEL_ALLOCATION = "FLYWHEEL_ALLOCATION"
FLYWHEEL_CARTRIDGE = "FLYWHEEL_CARTRIDGE"
CLAW_CARTRIDGE = "CLAW_CARTRIDGE"

# Effector ↔ allocation identities (R1 / R1b / R1c).
CLAW_REQUIRED_ALLOCATION = MotorAllocation.DRIVE2_ARM1_CLAW1
SCOOP_REQUIRED_ALLOCATION = MotorAllocation.DRIVE2_ARM1
FLYWHEEL_REQUIRED_ALLOCATION = MotorAllocation.DRIVE2_FLYWHEEL1

# Cartridge pins (R3 / R4).
FLYWHEEL_REQUIRED_CARTRIDGE = Cartridge.RPM_600
CLAW_REQUIRED_CARTRIDGE = Cartridge.RPM_200


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
    """R1: a claw end effector requires the 2drive+1arm+1claw allocation."""

    # strict=False so the committed JSON strings coerce into the StrEnum members
    # on round-trip (mirrors SelfModelConfig).
    model_config = ConfigDict(extra="forbid", strict=False)
    code: Literal["CLAW_MOTOR_BUDGET"] = CLAW_MOTOR_BUDGET
    when_end_effector: EndEffector = EndEffector.CLAW_GRASPER
    requires_motor_allocation: MotorAllocation = CLAW_REQUIRED_ALLOCATION


class ScoopAllocationRule(StrictModel):
    """R1b: a scoop end effector requires the 2drive+1arm allocation (passive scoop)."""

    model_config = ConfigDict(extra="forbid", strict=False)
    code: Literal["SCOOP_ALLOCATION"] = SCOOP_ALLOCATION
    when_end_effector: EndEffector = EndEffector.SCOOP
    requires_motor_allocation: MotorAllocation = SCOOP_REQUIRED_ALLOCATION


class FlywheelAllocationRule(StrictModel):
    """R1c: a flywheel end effector requires the 2drive+1flywheel allocation."""

    model_config = ConfigDict(extra="forbid", strict=False)
    code: Literal["FLYWHEEL_ALLOCATION"] = FLYWHEEL_ALLOCATION
    when_end_effector: EndEffector = EndEffector.FLYWHEEL
    requires_motor_allocation: MotorAllocation = FLYWHEEL_REQUIRED_ALLOCATION


class FlywheelCartridgeRule(StrictModel):
    """R3: a flywheel end effector requires the 600rpm cartridge."""

    model_config = ConfigDict(extra="forbid", strict=False)
    code: Literal["FLYWHEEL_CARTRIDGE"] = FLYWHEEL_CARTRIDGE
    when_end_effector: EndEffector = EndEffector.FLYWHEEL
    requires_cartridge: Cartridge = FLYWHEEL_REQUIRED_CARTRIDGE


class ClawCartridgeRule(StrictModel):
    """R4: a claw end effector requires the 200rpm cartridge (torque over speed)."""

    model_config = ConfigDict(extra="forbid", strict=False)
    code: Literal["CLAW_CARTRIDGE"] = CLAW_CARTRIDGE
    when_end_effector: EndEffector = EndEffector.CLAW_GRASPER
    requires_cartridge: Cartridge = CLAW_REQUIRED_CARTRIDGE


class CatalogConstraints(StrictModel):
    """The machine-readable rule set embedded in PartsCatalog / parts_catalog.json.

    R2 (scoop/flywheel allocation-grounds positivity) is retired: with
    `motor_allocation` now effector-encoded, R1b/R1c express the same constraint
    as identity rules.
    """

    claw_motor_budget: ClawMotorBudgetRule = Field(default_factory=ClawMotorBudgetRule)
    scoop_allocation: ScoopAllocationRule = Field(default_factory=ScoopAllocationRule)
    flywheel_allocation: FlywheelAllocationRule = Field(default_factory=FlywheelAllocationRule)
    flywheel_cartridge: FlywheelCartridgeRule = Field(default_factory=FlywheelCartridgeRule)
    claw_cartridge: ClawCartridgeRule = Field(default_factory=ClawCartridgeRule)


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
    end_effector: list[EndEffector]
    cartridge: list[Cartridge]
    constraints: CatalogConstraints = Field(default_factory=CatalogConstraints)


# --- The buildability engine ------------------------------------------------


def validate_config(config: SelfModelConfig) -> CatalogVerdict:
    """Deterministically decide whether a config is buildable per the rule set.

    Reuses F2's `SelfModelConfig` (D3); judges only structural buildability
    (effector↔allocation identity + per-effector cartridge pins), never physics (D2).
    """
    violations: list[Violation] = []

    # R1: claw_grasper ⇒ 2drive+1arm+1claw.
    if (
        config.end_effector == EndEffector.CLAW_GRASPER
        and config.motor_allocation != CLAW_REQUIRED_ALLOCATION
    ):
        violations.append(
            Violation(
                code=CLAW_MOTOR_BUDGET,
                message=(
                    f"end_effector '{EndEffector.CLAW_GRASPER.value}' requires "
                    f"motor_allocation '{CLAW_REQUIRED_ALLOCATION.value}'; got "
                    f"'{config.motor_allocation.value}'"
                ),
            )
        )

    # R1b: scoop ⇒ 2drive+1arm (passive scoop uses the arm motor only).
    if (
        config.end_effector == EndEffector.SCOOP
        and config.motor_allocation != SCOOP_REQUIRED_ALLOCATION
    ):
        violations.append(
            Violation(
                code=SCOOP_ALLOCATION,
                message=(
                    f"end_effector '{EndEffector.SCOOP.value}' requires "
                    f"motor_allocation '{SCOOP_REQUIRED_ALLOCATION.value}'; got "
                    f"'{config.motor_allocation.value}'"
                ),
            )
        )

    # R1c: flywheel ⇒ 2drive+1flywheel.
    if (
        config.end_effector == EndEffector.FLYWHEEL
        and config.motor_allocation != FLYWHEEL_REQUIRED_ALLOCATION
    ):
        violations.append(
            Violation(
                code=FLYWHEEL_ALLOCATION,
                message=(
                    f"end_effector '{EndEffector.FLYWHEEL.value}' requires "
                    f"motor_allocation '{FLYWHEEL_REQUIRED_ALLOCATION.value}'; got "
                    f"'{config.motor_allocation.value}'"
                ),
            )
        )

    # R3: flywheel ⇒ 600rpm cartridge.
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

    # R4: claw_grasper ⇒ 200rpm cartridge (torque over speed for grasping).
    if (
        config.end_effector == EndEffector.CLAW_GRASPER
        and config.cartridge != CLAW_REQUIRED_CARTRIDGE
    ):
        violations.append(
            Violation(
                code=CLAW_CARTRIDGE,
                message=(
                    f"end_effector '{EndEffector.CLAW_GRASPER.value}' requires "
                    f"cartridge '{CLAW_REQUIRED_CARTRIDGE.value}'; got "
                    f"'{config.cartridge.value}'"
                ),
            )
        )

    return CatalogVerdict(buildable=not violations, violations=violations)


def enumerate_buildable() -> list[SelfModelConfig]:
    """Enumerate every config in the full vocabulary cross-product that is buildable.

    Deterministic order: axes iterate in their declared enum order. Used by the
    enumeration test asserting the legal design space is exactly 4 (claw 1 +
    scoop 2 + flywheel 1) after the PR #16 narrowing.
    """
    buildable: list[SelfModelConfig] = []
    for motor_allocation in MotorAllocation:
        for end_effector in EndEffector:
            for cartridge in Cartridge:
                config = SelfModelConfig(
                    motor_allocation=motor_allocation,
                    end_effector=end_effector,
                    cartridge=cartridge,
                )
                if validate_config(config).buildable:
                    buildable.append(config)
    return buildable
