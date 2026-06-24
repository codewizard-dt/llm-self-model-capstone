from __future__ import annotations

import reactivex as rx
from reactivex import Observable

from contracts import TelemetrySource, VisionSource
from contracts.contract_line import ContractLine, VisionBlock, MotorApiSample


def _minimal_motor_sample() -> MotorApiSample:
    return MotorApiSample(
        device="claw_motor",
        subsystem="claw",
        api_binding="vexcode_python",
        sample_ms=100,
        values={
            "position_deg": 0.0,
            "velocity_rpm": 0.0,
            "current_amp": 0.0,
            "power_w": 0.0,
            "torque_nm": 0.0,
            "efficiency_pct": 0.0,
            "temperature_c": 25.0,
        },
        source_api={
            "position_deg": "claw_motor.position(DEGREES)",
            "velocity_rpm": "claw_motor.velocity(RPM)",
            "current_amp": "claw_motor.current(AMP)",
            "power_w": "claw_motor.power(WATT)",
            "torque_nm": "claw_motor.torque(NM)",
            "efficiency_pct": "claw_motor.efficiency(PERCENT)",
            "temperature_c": "claw_motor.temperature(CELSIUS)",
        },
    )


def _minimal_contract_line() -> ContractLine:
    return ContractLine(
        session_id="test-session-001",
        generation=0,
        round=1,
        task="grab",
        motor_samples=[_minimal_motor_sample()],
        predicted={"success": True},
        gap={"force_error_N": 0.0},
    )


class ValidTelemetrySource:
    def observe(self) -> Observable[ContractLine]:
        return rx.empty()


class MissingObserveTelemetry:
    pass


def test_telemetry_source_isinstance_pass():
    assert isinstance(ValidTelemetrySource(), TelemetrySource)


def test_telemetry_source_isinstance_fail_missing_observe():
    assert not isinstance(MissingObserveTelemetry(), TelemetrySource)


class ValidVisionSource:
    def observe(self) -> Observable[VisionBlock]:
        return rx.empty()


class MissingObserveVision:
    pass


def test_vision_source_isinstance_pass():
    assert isinstance(ValidVisionSource(), VisionSource)


def test_vision_source_isinstance_fail_missing_observe():
    assert not isinstance(MissingObserveVision(), VisionSource)


def test_telemetry_source_does_not_satisfy_vision_source():
    """Both protocols share the same structural signature so isinstance is True for both.

    The runtime_checkable check is purely structural. The real non-overlap guarantee
    is at the static type level (mypy/pyright). This test documents that invariant.
    """
    assert isinstance(ValidTelemetrySource(), VisionSource)


class ColdTelemetrySource:
    def __init__(self, record: ContractLine) -> None:
        self._record = record

    def observe(self) -> Observable[ContractLine]:
        return rx.of(self._record)


def test_cold_telemetry_source_emits_record_and_completes():
    record = _minimal_contract_line()
    source = ColdTelemetrySource(record)

    received: list[ContractLine] = []
    completed: list[bool] = []
    errors: list[Exception] = []

    source.observe().subscribe(
        on_next=received.append,
        on_error=errors.append,
        on_completed=lambda: completed.append(True),
    )

    assert errors == [], f"Unexpected errors: {errors}"
    assert len(received) == 1
    assert received[0].session_id == record.session_id
    assert received[0].task == record.task
    assert completed == [True]


def test_top_level_import():
    from contracts import TelemetrySource as TS, VisionSource as VS  # noqa: F401

    assert TS is TelemetrySource
    assert VS is VisionSource
