"""Tests for the parts catalog grammar (F3): drift guard, rules, enumeration.

Post-PR-#16 review: `motor_allocation` is effector-encoded, three single-value
axes were removed from the config, `cartridge` lost 100rpm, and the rule set
grew (R1b SCOOP_ALLOCATION, R1c FLYWHEEL_ALLOCATION, R4 CLAW_CARTRIDGE). The
buildable space is now exactly 4 — claw 1 + scoop 2 + flywheel 1.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contracts import PartsCatalog, SelfModelConfig, validate_config
from contracts import vocabulary as vocab
from contracts.parts_catalog import (
    CLAW_CARTRIDGE,
    CLAW_MOTOR_BUDGET,
    FLYWHEEL_ALLOCATION,
    FLYWHEEL_CARTRIDGE,
    SCOOP_ALLOCATION,
    enumerate_buildable,
)

# contracts/tests/test_parts_catalog.py -> parents[1] is the contracts root.
CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
CATALOG_JSON = CONTRACTS_ROOT / "parts_catalog.json"


def _config(**overrides) -> SelfModelConfig:
    base = {
        "motor_allocation": "2drive+1arm+1claw",
        "end_effector": "claw_grasper",
        "cartridge": "200rpm",
    }
    base.update(overrides)
    return SelfModelConfig(**base)


# --- acc-drift-guard --------------------------------------------------------


def test_catalog_axes_equal_vocabulary_value_sets():
    catalog = PartsCatalog.model_validate(json.loads(CATALOG_JSON.read_text()))
    axes = {
        "motor_allocation": vocab.MotorAllocation,
        "end_effector": vocab.EndEffector,
        "cartridge": vocab.Cartridge,
    }
    for field, enum_cls in axes.items():
        catalog_values = [member.value for member in getattr(catalog, field)]
        expected = [member.value for member in enum_cls]
        assert catalog_values == expected, f"{field} drifted from vocabulary"


def test_motor_allocation_is_effector_encoded():
    catalog = PartsCatalog.model_validate(json.loads(CATALOG_JSON.read_text()))
    values = {member.value for member in catalog.motor_allocation}
    assert values == {"2drive+1arm+1claw", "2drive+1arm", "2drive+1flywheel"}
    # The pre-PR-#16 allocations are gone.
    for retired in ("4drive", "2drive+2free", "3drive+1manip"):
        assert retired not in values


def test_cartridge_drops_100rpm():
    catalog = PartsCatalog.model_validate(json.loads(CATALOG_JSON.read_text()))
    values = {member.value for member in catalog.cartridge}
    assert values == {"200rpm", "600rpm"}


# --- acc-gen0-buildable -----------------------------------------------------


def test_gen0_clawbot_config_buildable():
    verdict = validate_config(_config())
    assert verdict.buildable is True
    assert verdict.violations == []


# --- R1: CLAW_MOTOR_BUDGET --------------------------------------------------


@pytest.mark.parametrize("allocation", ["2drive+1arm", "2drive+1flywheel"])
def test_claw_grasper_wrong_allocation_violates_motor_budget(allocation):
    verdict = validate_config(_config(motor_allocation=allocation))
    assert verdict.buildable is False
    codes = [v.code for v in verdict.violations]
    assert CLAW_MOTOR_BUDGET in codes
    assert all(v.message.strip() for v in verdict.violations)


# --- R1b: SCOOP_ALLOCATION --------------------------------------------------


@pytest.mark.parametrize("allocation", ["2drive+1arm+1claw", "2drive+1flywheel"])
def test_scoop_wrong_allocation_violates(allocation):
    verdict = validate_config(_config(end_effector="scoop", motor_allocation=allocation))
    assert verdict.buildable is False
    codes = [v.code for v in verdict.violations]
    assert SCOOP_ALLOCATION in codes


def test_scoop_with_correct_allocation_buildable():
    verdict = validate_config(_config(end_effector="scoop", motor_allocation="2drive+1arm"))
    assert verdict.buildable is True
    assert verdict.violations == []


# --- R1c: FLYWHEEL_ALLOCATION -----------------------------------------------


@pytest.mark.parametrize("allocation", ["2drive+1arm+1claw", "2drive+1arm"])
def test_flywheel_wrong_allocation_violates(allocation):
    verdict = validate_config(
        _config(end_effector="flywheel", motor_allocation=allocation, cartridge="600rpm")
    )
    assert verdict.buildable is False
    codes = [v.code for v in verdict.violations]
    assert FLYWHEEL_ALLOCATION in codes


# --- R3: FLYWHEEL_CARTRIDGE -------------------------------------------------


def test_flywheel_wrong_cartridge_violates():
    verdict = validate_config(
        _config(end_effector="flywheel", motor_allocation="2drive+1flywheel", cartridge="200rpm")
    )
    assert verdict.buildable is False
    violation = next(v for v in verdict.violations if v.code == FLYWHEEL_CARTRIDGE)
    assert violation.message.strip()
    assert "600rpm" in violation.message


def test_flywheel_with_600rpm_buildable():
    verdict = validate_config(
        _config(end_effector="flywheel", motor_allocation="2drive+1flywheel", cartridge="600rpm")
    )
    assert verdict.buildable is True


# --- R4: CLAW_CARTRIDGE -----------------------------------------------------


def test_claw_with_600rpm_violates_cartridge_rule():
    verdict = validate_config(_config(cartridge="600rpm"))
    assert verdict.buildable is False
    violation = next(v for v in verdict.violations if v.code == CLAW_CARTRIDGE)
    assert "200rpm" in violation.message


def test_scoop_cartridge_unconstrained_by_f3():
    # Scoop can use either cartridge — F9 may have an opinion, but F3 does not.
    for cartridge in ("200rpm", "600rpm"):
        verdict = validate_config(
            _config(end_effector="scoop", motor_allocation="2drive+1arm", cartridge=cartridge)
        )
        assert verdict.buildable is True


# --- acc-enum-4 -------------------------------------------------------------


def test_full_enumeration_is_exactly_4():
    buildable = enumerate_buildable()
    assert len(buildable) == 4

    by_effector = {"claw_grasper": 0, "scoop": 0, "flywheel": 0}
    for cfg in buildable:
        by_effector[cfg.end_effector.value] += 1
    assert by_effector == {"claw_grasper": 1, "scoop": 2, "flywheel": 1}


# --- acc-json-roundtrip -----------------------------------------------------


def test_parts_catalog_json_roundtrips():
    payload = json.loads(CATALOG_JSON.read_text())
    catalog = PartsCatalog.model_validate(payload)
    assert catalog.schema_version == "1.0"
    assert catalog.model_dump(mode="json") == payload
    assert catalog.constraints.claw_motor_budget.code == CLAW_MOTOR_BUDGET
    assert catalog.constraints.scoop_allocation.code == SCOOP_ALLOCATION
    assert catalog.constraints.flywheel_allocation.code == FLYWHEEL_ALLOCATION
    assert catalog.constraints.flywheel_cartridge.code == FLYWHEEL_CARTRIDGE
    assert catalog.constraints.claw_cartridge.code == CLAW_CARTRIDGE
