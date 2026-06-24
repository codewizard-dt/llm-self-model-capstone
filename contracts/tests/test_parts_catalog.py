"""Tests for the parts catalog grammar (F3): drift guard, rules, enumeration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contracts import PartsCatalog, SelfModelConfig, validate_config
from contracts import vocabulary as vocab
from contracts.parts_catalog import (
    CLAW_MOTOR_BUDGET,
    FLYWHEEL_CARTRIDGE,
    enumerate_buildable,
)

# contracts/tests/test_parts_catalog.py -> parents[1] is the contracts root.
CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
CATALOG_JSON = CONTRACTS_ROOT / "parts_catalog.json"


def _config(**overrides) -> SelfModelConfig:
    base = {
        "motor_allocation": "2drive+1arm+1claw",
        "arm_position": "front",
        "end_effector": "claw_grasper",
        "wheel_config": "front_omni+rear_standard",
        "arm_gear_ratio": "7:1",
        "cartridge": "200rpm",
    }
    base.update(overrides)
    return SelfModelConfig(**base)


# --- acc-drift-guard --------------------------------------------------------


def test_catalog_axes_equal_vocabulary_value_sets():
    catalog = PartsCatalog.model_validate(json.loads(CATALOG_JSON.read_text()))
    axes = {
        "motor_allocation": vocab.MotorAllocation,
        "arm_position": vocab.ArmPosition,
        "end_effector": vocab.EndEffector,
        "wheel_config": vocab.WheelConfig,
        "arm_gear_ratio": vocab.ArmGearRatio,
        "cartridge": vocab.Cartridge,
    }
    for field, enum_cls in axes.items():
        catalog_values = [member.value for member in getattr(catalog, field)]
        expected = [member.value for member in enum_cls]
        assert catalog_values == expected, f"{field} drifted from vocabulary"


def test_motor_allocation_has_no_4drive():
    assert "4drive" not in {member.value for member in vocab.MotorAllocation}
    catalog = PartsCatalog.model_validate(json.loads(CATALOG_JSON.read_text()))
    assert all(member.value != "4drive" for member in catalog.motor_allocation)


# --- acc-gen0-buildable -----------------------------------------------------


def test_gen0_clawbot_config_buildable():
    verdict = validate_config(_config())
    assert verdict.buildable is True
    assert verdict.violations == []


# --- acc-claw-budget-2free / acc-claw-budget-3drive -------------------------


@pytest.mark.parametrize("allocation", ["2drive+2free", "3drive+1manip"])
def test_claw_grasper_wrong_allocation_violates_motor_budget(allocation):
    verdict = validate_config(_config(motor_allocation=allocation))
    assert verdict.buildable is False
    codes = [v.code for v in verdict.violations]
    assert CLAW_MOTOR_BUDGET in codes
    # human-readable message present
    assert all(v.message.strip() for v in verdict.violations)


# --- acc-flywheel-cartridge -------------------------------------------------


def test_flywheel_wrong_cartridge_violates():
    verdict = validate_config(
        _config(motor_allocation="3drive+1manip", end_effector="flywheel", cartridge="200rpm")
    )
    assert verdict.buildable is False
    violation = next(v for v in verdict.violations if v.code == FLYWHEEL_CARTRIDGE)
    assert violation.message.strip()
    assert "600rpm" in violation.message


def test_flywheel_with_600rpm_buildable():
    verdict = validate_config(
        _config(motor_allocation="3drive+1manip", end_effector="flywheel", cartridge="600rpm")
    )
    assert verdict.buildable is True


# --- acc-scoop-each-allocation ----------------------------------------------


@pytest.mark.parametrize("allocation", ["2drive+1arm+1claw", "2drive+2free", "3drive+1manip"])
def test_scoop_buildable_on_each_allocation(allocation):
    verdict = validate_config(_config(motor_allocation=allocation, end_effector="scoop"))
    assert verdict.buildable is True
    assert verdict.violations == []


# --- acc-enum-60 ------------------------------------------------------------


def test_full_enumeration_is_exactly_60():
    buildable = enumerate_buildable()
    assert len(buildable) == 60

    # Re-derive the breakdown: claw 12 + scoop 36 + flywheel 12.
    by_effector = {"claw_grasper": 0, "scoop": 0, "flywheel": 0}
    for cfg in buildable:
        by_effector[cfg.end_effector.value] += 1
    assert by_effector == {"claw_grasper": 12, "scoop": 36, "flywheel": 12}


# --- acc-json-roundtrip -----------------------------------------------------


def test_parts_catalog_json_roundtrips():
    payload = json.loads(CATALOG_JSON.read_text())
    catalog = PartsCatalog.model_validate(payload)
    assert catalog.schema_version == "1.0"
    # round-trips with no loss
    assert catalog.model_dump(mode="json") == payload
    # the embedded constraints carry the two rule codes
    assert catalog.constraints.claw_motor_budget.code == CLAW_MOTOR_BUDGET
    assert catalog.constraints.flywheel_cartridge.code == FLYWHEEL_CARTRIDGE
