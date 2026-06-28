from __future__ import annotations

import dataclasses
import importlib
import sys

import pytest
from contracts import (
    ApproachTargetParams,
    ApproachTargetSkillCommand,
    CommandStatus,
    PilotSkillName,
    StopSkillParams,
    StopSkillCommand,
)

from pilot.executor import (
    DEFAULT_EXECUTOR_POLICY,
    ExecutionResult,
    ExecutorPolicy,
    ExecutorReasonCode,
    SkillExecutor,
    TransportRequest,
    execute_validated_command,
)
from pilot.safety import (
    ValidationMode,
    ValidationReason,
    ValidationReasonCode,
    ValidationResult,
    ValidationStatus,
)
from pilot.skills import get_skill_definition


def _accepted_validation(command: object | None = None) -> ValidationResult:
    normalized_command = command if command is not None else _motion_command()
    return ValidationResult(
        status=ValidationStatus.ACCEPTED,
        command=normalized_command,
        mode=ValidationMode.REPLAY,
        skill=PilotSkillName(str(normalized_command.skill)) if normalized_command else None,
        reasons=(ValidationReason(ValidationReasonCode.OK, "command accepted"),),
    )


def _motion_command() -> ApproachTargetSkillCommand:
    return ApproachTargetSkillCommand(
        command_id="cmd-approach",
        issued_ms=100,
        params=ApproachTargetParams(target_id="block-1"),
    )


def _stop_command() -> StopSkillCommand:
    return StopSkillCommand(
        command_id="cmd-stop",
        issued_ms=200,
        params=StopSkillParams(reason="unsafe"),
    )


def test_executor_module_imports_without_ros_packages_and_exports_public_api(monkeypatch) -> None:
    ros_roots = {"rclpy", "std_msgs", "sensor_msgs", "geometry_msgs"}

    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in ros_roots:
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.executor", None)

    module = importlib.import_module("pilot.executor")
    import pilot

    assert module.SkillExecutor is not None
    assert module.execute_validated_command is not None
    assert "SkillExecutor" in pilot.__all__
    assert "execute_validated_command" in pilot.__all__
    assert ros_roots.isdisjoint(sys.modules)


def test_executor_public_helper_types_are_immutable_and_use_contract_status() -> None:
    policy = ExecutorPolicy(transport_grace_ms=50)
    result = ExecutionResult(
        command_id="cmd-1",
        skill=PilotSkillName.STOP,
        status=CommandStatus.QUEUED,
        reason_code=ExecutorReasonCode.QUEUED.value,
        message="queued",
        issued_ms=10,
        completed_ms=20,
    )

    assert DEFAULT_EXECUTOR_POLICY.transport_grace_ms == 0
    assert dataclasses.is_dataclass(policy)
    assert dataclasses.is_dataclass(result)
    assert isinstance(result.status, CommandStatus)
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.transport_grace_ms = 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.status = CommandStatus.REJECTED
    with pytest.raises(ValueError, match="transport_grace_ms"):
        ExecutorPolicy(transport_grace_ms=-1)


def test_accepted_validation_hands_normalized_command_to_transport_once() -> None:
    command = _motion_command()
    calls: list[TransportRequest] = []

    def fake_transport(request: TransportRequest) -> dict[str, object]:
        calls.append(request)
        return {"queued": True, "route": request.route.command_path}

    result = execute_validated_command(
        _accepted_validation(command),
        fake_transport,
        policy=ExecutorPolicy(transport_grace_ms=25),
        clock_ms=lambda: 175,
    )

    definition = get_skill_definition(PilotSkillName.APPROACH_TARGET)
    assert len(calls) == 1
    request = calls[0]
    assert request.command == command
    assert request.command_id == "cmd-approach"
    assert request.skill is PilotSkillName.APPROACH_TARGET
    assert request.route.command_path == definition.command_path
    assert request.route.expected_result_source == definition.expected_result_source
    assert request.route.max_duration_ms == definition.max_duration_ms
    assert request.deadline.max_duration_ms == definition.max_duration_ms
    assert request.deadline.transport_grace_ms == 25
    assert request.deadline.deadline_ms == 100 + definition.max_duration_ms + 25
    assert result.status is CommandStatus.QUEUED
    assert result.reason_code == ExecutorReasonCode.QUEUED.value
    assert result.command_id == "cmd-approach"
    assert result.skill is PilotSkillName.APPROACH_TARGET
    assert result.issued_ms == 100
    assert result.completed_ms == 175
    assert result.raw_transport_payload == {"queued": True, "route": definition.command_path}


def test_executor_accepts_transport_object_protocol() -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.requests: list[TransportRequest] = []

        def send(self, request: TransportRequest) -> object | None:
            self.requests.append(request)
            return None

    transport = FakeTransport()
    result = SkillExecutor(transport, clock_ms=lambda: 250).execute(
        _accepted_validation(_stop_command())
    )

    assert len(transport.requests) == 1
    assert transport.requests[0].skill is PilotSkillName.STOP
    assert result.status is CommandStatus.QUEUED
    assert result.completed_ms == 250


@pytest.mark.parametrize("status", [ValidationStatus.REJECTED, ValidationStatus.STOPPED])
def test_non_accepted_validation_refuses_without_transport(status: ValidationStatus) -> None:
    calls: list[TransportRequest] = []
    validation = ValidationResult(
        status=status,
        command=_motion_command(),
        mode=ValidationMode.HARDWARE,
        skill=PilotSkillName.APPROACH_TARGET,
        reasons=(
            ValidationReason(
                ValidationReasonCode.HUMAN_SUPERVISION_REQUIRED,
                "hardware mode requires human supervision",
            ),
        ),
    )

    result = execute_validated_command(validation, calls.append, clock_ms=lambda: 150)

    assert calls == []
    assert result.status is CommandStatus.REJECTED
    assert result.reason_code == ValidationReasonCode.HUMAN_SUPERVISION_REQUIRED.value
    assert result.message == "validation refused command: hardware mode requires human supervision"
    assert result.command_id == "cmd-approach"
    assert result.skill is PilotSkillName.APPROACH_TARGET
    assert result.issued_ms == 100
    assert result.completed_ms == 150
    assert result.raw_transport_payload is None


def test_malformed_non_accepted_validation_without_reasons_refuses_without_transport() -> None:
    calls: list[TransportRequest] = []
    validation = ValidationResult(
        status=ValidationStatus.REJECTED,
        command=_motion_command(),
        mode=ValidationMode.HARDWARE,
        skill=PilotSkillName.APPROACH_TARGET,
        reasons=(),
    )

    result = execute_validated_command(validation, calls.append, clock_ms=lambda: 155)

    assert calls == []
    assert result.status is CommandStatus.REJECTED
    assert result.reason_code == ExecutorReasonCode.MALFORMED_VALIDATION.value
    assert result.message == "validation refused command: validation result has no refusal reason"
    assert result.command_id == "cmd-approach"
    assert result.skill is PilotSkillName.APPROACH_TARGET
    assert result.issued_ms == 100
    assert result.completed_ms == 155
    assert result.raw_transport_payload is None


def test_accepted_validation_missing_command_refuses_without_transport() -> None:
    calls: list[TransportRequest] = []
    validation = ValidationResult(
        status=ValidationStatus.ACCEPTED,
        command=None,
        mode=ValidationMode.REPLAY,
        skill=PilotSkillName.STOP,
        reasons=(ValidationReason(ValidationReasonCode.OK, "command accepted"),),
    )

    result = execute_validated_command(validation, calls.append, clock_ms=lambda: 300)

    assert calls == []
    assert result.status is CommandStatus.REJECTED
    assert result.reason_code == ExecutorReasonCode.MISSING_COMMAND.value
    assert result.message == "accepted validation result is missing command"
    assert result.command_id is None
    assert result.skill is PilotSkillName.STOP
    assert result.issued_ms is None
    assert result.completed_ms == 300
    assert result.raw_transport_payload is None


def test_malformed_validation_refuses_without_transport() -> None:
    calls: list[TransportRequest] = []

    result = execute_validated_command(object(), calls.append, clock_ms=lambda: 400)

    assert calls == []
    assert result.status is CommandStatus.REJECTED
    assert result.reason_code == ExecutorReasonCode.MALFORMED_VALIDATION.value
    assert result.command_id is None
    assert result.skill is None
    assert result.completed_ms == 400


def test_pilot_package_exports_executor_api() -> None:
    import pilot

    expected_exports = {
        "DEFAULT_EXECUTOR_POLICY",
        "ExecutionResult",
        "ExecutorDeadline",
        "ExecutorPolicy",
        "ExecutorReasonCode",
        "ExecutorRoute",
        "ExecutorTransport",
        "SkillExecutor",
        "TransportBoundary",
        "TransportRequest",
        "execute_validated_command",
    }

    assert expected_exports <= set(pilot.__all__)
    for name in expected_exports:
        assert getattr(pilot, name) is not None
