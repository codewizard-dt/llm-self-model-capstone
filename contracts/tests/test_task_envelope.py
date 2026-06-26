from __future__ import annotations

import pytest
from pydantic import ValidationError

from contracts import TaskEnvelope, TaskOutline


def _motor_sample() -> dict[str, object]:
    return {
        "device": "left_drive",
        "subsystem": "drivetrain",
        "sample_ms": 100,
        "values": {
            "position_deg": 0.0,
            "velocity_rpm": 0.0,
            "current_amp": 0.0,
            "power_w": 0.0,
            "torque_nm": 0.0,
            "efficiency_pct": 100.0,
            "temperature_c": 25.0,
        },
        "source_api": {
            "position_deg": "left_drive.position(DEGREES)",
            "velocity_rpm": "left_drive.velocity(RPM)",
            "current_amp": "left_drive.current(CurrentUnits.AMP)",
            "power_w": "left_drive.power(WattUnits.WATT)",
            "torque_nm": "left_drive.torque(TorqueUnits.NM)",
            "efficiency_pct": "left_drive.efficiency(PERCENT)",
            "temperature_c": "left_drive.temperature(CELSIUS)",
        },
    }


def _contract() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "session_id": "self-model-to-operator",
        "generation": 2,
        "round": 1,
        "task": "deliver_ball",
        "motor_samples": [_motor_sample()],
        "predicted": {"success": True},
        "gap": {"distance_error_m": 0.0},
    }


def test_task_envelope_requires_exact_contract_and_outline() -> None:
    envelope = TaskEnvelope.model_validate(
        {
            "contract": _contract(),
            "outline": [["grab", [], {"duration_ms": 700}]],
        }
    )

    assert envelope.contract.session_id == "self-model-to-operator"
    assert envelope.outline.method_plan() == (("grab", (), {"duration_ms": 700}),)

    with pytest.raises(ValidationError):
        TaskEnvelope.model_validate(
            {
                "contract": _contract(),
                "outline": [["grab", [], {"duration_ms": 700}]],
                "extra": True,
            }
        )


def test_task_envelope_rejects_invalid_contract_line() -> None:
    contract = _contract()
    contract.pop("motor_samples")

    with pytest.raises(ValidationError):
        TaskEnvelope.model_validate({"contract": contract, "outline": [["grab", []]]})


def test_task_outline_rejects_invalid_operator_method_calls() -> None:
    with pytest.raises(ValidationError):
        TaskOutline.model_validate([["drive", []]])

    with pytest.raises(ValidationError):
        TaskOutline.model_validate([["move_to_tag", [99]]])

    with pytest.raises(ValidationError):
        TaskOutline.model_validate([["grab", [], {"duration_ms": 0}]])
