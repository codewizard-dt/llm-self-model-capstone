"""Motor telemetry contract tests.

The three VEXcode-grounded tests are migrated from the now-deleted
legacy motor-telemetry contract tests with imports rewritten
to the ``contracts`` package (DEC-MIGRATE-NOT-REWRITE-TESTS). The four ScoreContract
tests are dropped because ScoreContract was discarded in the pydantic-models slice;
the schema-export test now targets ContractLine instead.
"""

import json

import pytest
from pydantic import ValidationError

from contracts import (
    ContractLine,
    MotorApiSample,
    MotorApiValues,
    motor_sample_from_pros,
    vexcode_motor_source_api,
)


def full_values(**overrides: float) -> dict[str, float]:
    values = {
        "position_deg": 120.0,
        "velocity_rpm": 14.0,
        "current_amp": 1.8,
        "power_w": 21.6,
        "torque_nm": 0.9,
        "efficiency_pct": 72.0,
        "temperature_c": 34.0,
    }
    values.update(overrides)
    return values


def test_motor_sample_requires_all_vexcode_observations() -> None:
    values = full_values()
    del values["power_w"]

    with pytest.raises(ValidationError):
        MotorApiSample(
            device="claw_motor",
            subsystem="claw",
            sample_ms=1,
            values=MotorApiValues(**values),
            source_api=vexcode_motor_source_api("claw_motor"),
        )


def test_motor_sample_rejects_missing_source_api_mapping() -> None:
    source_api = vexcode_motor_source_api("claw_motor")
    del source_api["efficiency_pct"]

    with pytest.raises(ValidationError):
        MotorApiSample(
            device="claw_motor",
            subsystem="claw",
            sample_ms=1,
            values=MotorApiValues(**full_values()),
            source_api=source_api,
        )


def test_motor_sample_rejects_unknown_source_api_call() -> None:
    source_api = vexcode_motor_source_api("claw_motor")
    source_api["torque_nm"] = "claw_motor.get_torque()"

    with pytest.raises(ValidationError):
        MotorApiSample(
            device="claw_motor",
            subsystem="claw",
            sample_ms=1,
            values=MotorApiValues(**full_values()),
            source_api=source_api,
        )


def test_motor_sample_from_pros_normalises_keys() -> None:
    sample = {
        "pos": 540.0,
        "vel": 180.0,
        "cur": 2100.0,
        "power_w": 37.8,
        "trq": 1.1,
        "efficiency_pct": 68.0,
        "temp_c": 38.0,
    }
    motor = motor_sample_from_pros(
        device="left_drive",
        subsystem="drivetrain",
        sample_ms=2200,
        sample=sample,
    )
    assert motor.values.position_deg == 540.0
    assert motor.values.current_amp == pytest.approx(2.1)
    assert motor.values.torque_nm == 1.1


def test_schema_export_contains_contract_line() -> None:
    dumped = json.dumps(ContractLine.model_json_schema())
    assert "motor_samples" in dumped
    assert "session_id" in dumped
