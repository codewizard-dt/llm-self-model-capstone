"""Strict motor telemetry contracts grounded in the VEXcode V5 Motor API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


API_BINDING = "vexcode_python"
MOTOR_API_FIELDS = (
    "position_deg",
    "velocity_rpm",
    "current_amp",
    "power_w",
    "torque_nm",
    "efficiency_pct",
    "temperature_c",
)
MOTOR_API_METHODS = {
    "position_deg": "position",
    "velocity_rpm": "velocity",
    "current_amp": "current",
    "power_w": "power",
    "torque_nm": "torque",
    "efficiency_pct": "efficiency",
    "temperature_c": "temperature",
}

Subsystem = Literal["claw", "arm", "drivetrain"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class MotorApiValues(StrictModel):
    position_deg: float
    velocity_rpm: float
    current_amp: float
    power_w: float
    torque_nm: float
    efficiency_pct: float
    temperature_c: float


class MotorApiSample(StrictModel):
    device: str
    subsystem: Subsystem
    api_binding: Literal["vexcode_python"] = API_BINDING
    sample_ms: int = Field(ge=0)
    values: MotorApiValues
    source_api: dict[str, str]

    @model_validator(mode="after")
    def require_full_vexcode_motor_api(self) -> "MotorApiSample":
        source_keys: set[str] = set(self.source_api)
        required_keys: set[str] = set(MOTOR_API_FIELDS)
        if source_keys != required_keys:
            missing = sorted(required_keys - source_keys)
            extra = sorted(source_keys - required_keys)
            raise ValueError(
                f"source_api must match required motor fields; missing={missing}; extra={extra}"
            )

        for field_name, method_name in MOTOR_API_METHODS.items():
            call = self.source_api[field_name]
            expected_prefix = f"{self.device}.{method_name}("
            if not call.startswith(expected_prefix):
                raise ValueError(f"{field_name} source_api must start with {expected_prefix}")
        return self


class ContractSource(StrictModel):
    raw_session_path: Optional[str] = None
    brain_start_ms: Optional[int] = Field(default=None, ge=0)
    brain_end_ms: Optional[int] = Field(default=None, ge=0)
    pi_received_ms: Optional[int] = Field(default=None, ge=0)
    telemetry_sample_count: int = Field(ge=0)


def vexcode_motor_source_api(device: str) -> dict[str, str]:
    return {
        "position_deg": f"{device}.position(DEGREES)",
        "velocity_rpm": f"{device}.velocity(RPM)",
        "current_amp": f"{device}.current(AMP)",
        "power_w": f"{device}.power(WATT)",
        "torque_nm": f"{device}.torque(NM)",
        "efficiency_pct": f"{device}.efficiency(PERCENT)",
        "temperature_c": f"{device}.temperature(CELSIUS)",
    }


def motor_sample_from_vexcode(
    *,
    device: str,
    subsystem: Subsystem,
    sample_ms: int,
    values: dict[str, float],
) -> MotorApiSample:
    return MotorApiSample(
        device=device,
        subsystem=subsystem,
        sample_ms=sample_ms,
        values=MotorApiValues(**values),
        source_api=vexcode_motor_source_api(device),
    )


def motor_sample_from_pros(
    *,
    device: str,
    subsystem: Subsystem,
    sample_ms: int,
    sample: dict[str, float],
) -> MotorApiSample:
    values = {
        "position_deg": float(sample["pos"]),
        "velocity_rpm": float(sample["vel"]),
        "current_amp": float(sample["cur"]) / 1000.0,
        "power_w": float(sample["power_w"]),
        "torque_nm": float(sample["trq"]),
        "efficiency_pct": float(sample["efficiency_pct"]),
        "temperature_c": float(sample["temp_c"]),
    }
    return motor_sample_from_vexcode(
        device=device,
        subsystem=subsystem,
        sample_ms=sample_ms,
        values=values,
    )
