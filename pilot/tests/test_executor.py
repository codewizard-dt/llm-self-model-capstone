from __future__ import annotations

import dataclasses
import importlib
import json
import sys

import pytest
from contracts import (
    ApproachTargetParams,
    ApproachTargetSkillCommand,
    ArmToAngleParams,
    ArmToAngleSkillCommand,
    CenterObjectInGripperParams,
    CenterObjectInGripperSkillCommand,
    ClawCloseParams,
    ClawCloseSkillCommand,
    ClawOpenParams,
    ClawOpenSkillCommand,
    CommandStatus,
    FaceTargetParams,
    FaceTargetSkillCommand,
    GoToDestinationParams,
    GoToDestinationSkillCommand,
    PilotSkillName,
    StopSkillParams,
    StopSkillCommand,
    SurveySceneParams,
    SurveySceneSkillCommand,
    VerifyDropParams,
    VerifyDropSkillCommand,
    VerifyGraspParams,
    VerifyGraspSkillCommand,
)

from pilot.executor import (
    DEFAULT_EXECUTOR_POLICY,
    ASSERTION_ONLY_ROUTE,
    BOUNDED_CONTROL_ROUTE,
    ExecutionResult,
    ExecutorPolicy,
    ExecutorReasonCode,
    OPERATOR_COMMAND_ROUTE,
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
from pilot.skills import get_skill_definition, list_skill_definitions


def _accepted_validation(command: object | None = None) -> ValidationResult:
    normalized_command = command if command is not None else _motion_command()
    return ValidationResult(
        status=ValidationStatus.ACCEPTED,
        command=normalized_command,
        mode=ValidationMode.REPLAY,
        skill=PilotSkillName(str(normalized_command.skill)) if normalized_command else None,
        reasons=(ValidationReason(ValidationReasonCode.OK, "command accepted"),),
    )


class _FakeTerminalTransport:
    def __init__(self, terminal_payloads: list[object] | None = None) -> None:
        self.requests: list[TransportRequest] = []
        self.waits_ms: list[int] = []
        self._terminal_payloads = list(terminal_payloads or [])

    def send(self, request: TransportRequest) -> dict[str, object]:
        self.requests.append(request)
        return {"published": True}

    def receive_result(self, request: TransportRequest, timeout_ms: int) -> object | None:
        self.waits_ms.append(timeout_ms)
        if not self._terminal_payloads:
            return None
        return self._terminal_payloads.pop(0)


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


def _command_for_skill(skill: PilotSkillName):
    commands = {
        PilotSkillName.STOP: _stop_command(),
        PilotSkillName.SURVEY_SCENE: SurveySceneSkillCommand(
            command_id="cmd-survey",
            issued_ms=210,
            params=SurveySceneParams(yaw_span_deg=90.0, timeout_ms=3000),
        ),
        PilotSkillName.FACE_TARGET: FaceTargetSkillCommand(
            command_id="cmd-face",
            issued_ms=220,
            params=FaceTargetParams(target_id="tag-7", max_turn_rad_s=0.4, timeout_ms=2500),
        ),
        PilotSkillName.APPROACH_TARGET: ApproachTargetSkillCommand(
            command_id="cmd-approach-tag",
            issued_ms=230,
            params=ApproachTargetParams(
                target_id="tag-7",
                standoff_m=0.35,
                max_speed_mps=0.2,
                timeout_ms=4500,
            ),
        ),
        PilotSkillName.CENTER_OBJECT_IN_GRIPPER: CenterObjectInGripperSkillCommand(
            command_id="cmd-center",
            issued_ms=240,
            params=CenterObjectInGripperParams(
                object_id="block-1",
                image_tolerance_px=12,
                timeout_ms=3500,
            ),
        ),
        PilotSkillName.ARM_TO_ANGLE: ArmToAngleSkillCommand(
            command_id="cmd-arm",
            issued_ms=250,
            params=ArmToAngleParams(deg=45.0, vel_rpm=60.0),
        ),
        PilotSkillName.CLAW_OPEN: ClawOpenSkillCommand(
            command_id="cmd-claw-open",
            issued_ms=260,
            params=ClawOpenParams(opening_pct=80.0),
        ),
        PilotSkillName.CLAW_CLOSE: ClawCloseSkillCommand(
            command_id="cmd-claw-close",
            issued_ms=270,
            params=ClawCloseParams(grip_force_n=15.0),
        ),
        PilotSkillName.VERIFY_GRASP: VerifyGraspSkillCommand(
            command_id="cmd-verify-grasp",
            issued_ms=280,
            params=VerifyGraspParams(object_id="block-1", min_confidence=0.7),
        ),
        PilotSkillName.GO_TO_DESTINATION: GoToDestinationSkillCommand(
            command_id="cmd-go",
            issued_ms=290,
            params=GoToDestinationParams(
                destination_id="tag-7",
                position_tolerance_m=0.15,
                max_speed_mps=0.2,
                timeout_ms=5000,
            ),
        ),
        PilotSkillName.VERIFY_DROP: VerifyDropSkillCommand(
            command_id="cmd-verify-drop",
            issued_ms=300,
            params=VerifyDropParams(destination_id="drop-zone", min_confidence=0.75),
        ),
    }
    assert set(commands) == set(PilotSkillName)
    return commands[skill]


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
    terminal_payload = {
        "command_id": "cmd-approach",
        "skill": PilotSkillName.APPROACH_TARGET.value,
        "status": "ok",
        "completed_ms": 180,
        "message": "standoff reached",
    }
    transport = _FakeTerminalTransport([terminal_payload])

    result = execute_validated_command(
        _accepted_validation(command),
        transport,
        policy=ExecutorPolicy(transport_grace_ms=25),
        clock_ms=lambda: 175,
    )

    definition = get_skill_definition(PilotSkillName.APPROACH_TARGET)
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.command == command
    assert request.command_id == "cmd-approach"
    assert request.skill is PilotSkillName.APPROACH_TARGET
    assert request.route.command_path == definition.command_path
    assert request.route.expected_result_source == definition.expected_result_source
    assert request.route.max_duration_ms == definition.max_duration_ms
    assert request.deadline.max_duration_ms == definition.max_duration_ms
    assert request.deadline.effective_timeout_ms == 10_000
    assert request.deadline.transport_grace_ms == 25
    assert request.deadline.deadline_ms == 175 + definition.max_duration_ms + 25
    assert request.payload["route"] == BOUNDED_CONTROL_ROUTE
    assert request.payload["action"] == "approach_target"
    assert request.payload["command_id"] == "cmd-approach"
    assert request.payload["skill"] == PilotSkillName.APPROACH_TARGET.value
    assert request.payload["effective_timeout_ms"] == 10_000
    assert request.payload["parameters"] == command.params.model_dump(mode="json")
    assert transport.waits_ms == [10_025]
    assert result.status is CommandStatus.OK
    assert result.reason_code == ExecutorReasonCode.TERMINAL_OK.value
    assert result.command_id == "cmd-approach"
    assert result.skill is PilotSkillName.APPROACH_TARGET
    assert result.issued_ms == 100
    assert result.completed_ms == 180
    assert result.message == "terminal transport result ok: standoff reached"
    assert result.raw_transport_payload == terminal_payload


def test_executor_accepts_transport_object_protocol() -> None:
    transport = _FakeTerminalTransport([{"command_id": "cmd-stop", "status": "ok"}])
    result = SkillExecutor(transport, clock_ms=lambda: 250).execute(
        _accepted_validation(_stop_command())
    )

    assert len(transport.requests) == 1
    assert transport.requests[0].skill is PilotSkillName.STOP
    assert transport.requests[0].payload["route"] == BOUNDED_CONTROL_ROUTE
    assert transport.requests[0].payload["action"] == "halt"
    assert transport.requests[0].payload["reason"] == "unsafe"
    assert result.status is CommandStatus.OK
    assert result.reason_code == ExecutorReasonCode.TERMINAL_OK.value
    assert result.completed_ms == 250


def test_publish_return_is_not_skill_success_and_missing_terminal_times_out() -> None:
    command = _command_for_skill(PilotSkillName.FACE_TARGET)
    transport = _FakeTerminalTransport()

    result = execute_validated_command(
        _accepted_validation(command),
        transport,
        policy=ExecutorPolicy(transport_grace_ms=50),
        clock_ms=lambda: 1_000,
    )

    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.deadline.effective_timeout_ms == 2_500
    assert request.deadline.deadline_ms == 3_550
    assert transport.waits_ms == [2_550]
    assert result.status is CommandStatus.STALE
    assert result.reason_code == ExecutorReasonCode.TRANSPORT_TIMEOUT.value
    assert result.message == "no matching terminal transport result before deadline"
    assert result.completed_ms == 3_550


@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_reason", "message_fragment"),
    [
        (
            {"command_id": "cmd-approach", "status": "rejected", "message": "operator rejected"},
            CommandStatus.REJECTED,
            ExecutorReasonCode.TERMINAL_REJECTED.value,
            "operator rejected",
        ),
        (
            {"command_id": "cmd-approach", "success": False, "reason": "motor fault"},
            CommandStatus.FAILED,
            ExecutorReasonCode.TERMINAL_FAILED.value,
            "motor fault",
        ),
        (
            {"command_id": "cmd-approach", "status": "stale", "fault": "bridge stale"},
            CommandStatus.STALE,
            ExecutorReasonCode.TERMINAL_STALE.value,
            "bridge stale",
        ),
    ],
)
def test_terminal_rejected_failed_and_stale_payloads_are_parsed(
    payload: dict[str, object],
    expected_status: CommandStatus,
    expected_reason: str,
    message_fragment: str,
) -> None:
    transport = _FakeTerminalTransport([payload])

    result = execute_validated_command(
        _accepted_validation(_motion_command()),
        transport,
        clock_ms=lambda: 2_000,
    )

    assert result.status is expected_status
    assert result.reason_code == expected_reason
    assert message_fragment in result.message
    assert result.raw_transport_payload == payload


def test_terminal_json_payload_is_parsed_into_success_result() -> None:
    payload = json.dumps(
        {
            "command_id": "cmd-approach",
            "status": "ok",
            "completed_ms": 2_345,
            "message": "arrived",
        }
    )
    transport = _FakeTerminalTransport([payload])

    result = execute_validated_command(
        _accepted_validation(_motion_command()),
        transport,
        clock_ms=lambda: 2_000,
    )

    assert result.status is CommandStatus.OK
    assert result.reason_code == ExecutorReasonCode.TERMINAL_OK.value
    assert result.completed_ms == 2_345
    assert result.raw_transport_payload == payload


def test_command_id_correlation_ignores_nonmatching_terminal_payloads() -> None:
    transport = _FakeTerminalTransport(
        [
            {"command_id": "cmd-other", "status": "ok", "message": "wrong command"},
            {"command_id": "cmd-approach", "status": "ok", "message": "matched"},
        ]
    )

    result = execute_validated_command(
        _accepted_validation(_motion_command()),
        transport,
        clock_ms=lambda: 3_000,
    )

    assert len(transport.requests) == 1
    assert transport.waits_ms == [10_000, 10_000]
    assert result.status is CommandStatus.OK
    assert result.message == "terminal transport result ok: matched"
    assert result.command_id == "cmd-approach"


def test_ordered_terminal_payload_without_command_id_matches_active_request() -> None:
    transport = _FakeTerminalTransport(
        [
            {
                "outcome": {"success": True, "reason": "operator_complete"},
                "source": {"brain_end_ms": 4_200},
            }
        ]
    )

    result = execute_validated_command(
        _accepted_validation(_motion_command()),
        transport,
        clock_ms=lambda: 4_000,
    )

    assert result.status is CommandStatus.OK
    assert result.reason_code == ExecutorReasonCode.TERMINAL_OK.value
    assert result.command_id == "cmd-approach"
    assert result.completed_ms == 4_200
    assert result.message == "terminal transport result ok: operator_complete"


def test_deadline_uses_min_command_timeout_and_registry_max_plus_grace() -> None:
    command = _command_for_skill(PilotSkillName.FACE_TARGET)
    transport = _FakeTerminalTransport([{"command_id": "cmd-face", "status": "ok"}])

    execute_validated_command(
        _accepted_validation(command),
        transport,
        policy=ExecutorPolicy(transport_grace_ms=75),
        clock_ms=lambda: 5_000,
    )

    request = transport.requests[0]
    assert get_skill_definition(PilotSkillName.FACE_TARGET).max_duration_ms == 4_000
    assert request.deadline.max_duration_ms == 4_000
    assert request.deadline.effective_timeout_ms == 2_500
    assert request.deadline.deadline_ms == 7_575
    assert request.payload["effective_timeout_ms"] == 2_500
    assert request.payload["deadline_ms"] == 7_575
    assert transport.waits_ms == [2_575]


def test_stop_halt_timeout_returns_deterministic_ok_after_prior_timeout() -> None:
    transport = _FakeTerminalTransport()
    executor = SkillExecutor(transport, clock_ms=lambda: 10_000)

    failed = executor.execute(_accepted_validation(_motion_command()))
    stopped = executor.execute(_accepted_validation(_stop_command()))

    assert [request.skill for request in transport.requests] == [
        PilotSkillName.APPROACH_TARGET,
        PilotSkillName.STOP,
    ]
    assert failed.status is CommandStatus.STALE
    assert failed.reason_code == ExecutorReasonCode.TRANSPORT_TIMEOUT.value
    assert stopped.status is CommandStatus.OK
    assert stopped.reason_code == ExecutorReasonCode.STOP_POLICY_TIMEOUT.value
    assert (
        stopped.message == "stop halt request sent; no terminal evidence before stop policy timeout"
    )
    assert stopped.completed_ms == 10_500


def test_all_contract_skills_have_mapping_or_assertion_only_executor_outcome() -> None:
    expected = {
        PilotSkillName.STOP: (BOUNDED_CONTROL_ROUTE, "halt"),
        PilotSkillName.SURVEY_SCENE: (OPERATOR_COMMAND_ROUTE, "survey_scan"),
        PilotSkillName.FACE_TARGET: (OPERATOR_COMMAND_ROUTE, "align_to_tag"),
        PilotSkillName.APPROACH_TARGET: (OPERATOR_COMMAND_ROUTE, "move_to_tag"),
        PilotSkillName.CENTER_OBJECT_IN_GRIPPER: (
            BOUNDED_CONTROL_ROUTE,
            "center_object_in_gripper",
        ),
        PilotSkillName.ARM_TO_ANGLE: (OPERATOR_COMMAND_ROUTE, "arm"),
        PilotSkillName.CLAW_OPEN: (OPERATOR_COMMAND_ROUTE, "release"),
        PilotSkillName.CLAW_CLOSE: (OPERATOR_COMMAND_ROUTE, "grab"),
        PilotSkillName.VERIFY_GRASP: (ASSERTION_ONLY_ROUTE, "assertion_validated"),
        PilotSkillName.GO_TO_DESTINATION: (OPERATOR_COMMAND_ROUTE, "move_to_tag"),
        PilotSkillName.VERIFY_DROP: (ASSERTION_ONLY_ROUTE, "assertion_validated"),
    }
    assert set(expected) == set(PilotSkillName)
    assert {definition.name for definition in list_skill_definitions()} == set(PilotSkillName)

    for skill in PilotSkillName:
        command = _command_for_skill(skill)
        calls: list[TransportRequest] = []

        result = execute_validated_command(
            _accepted_validation(command),
            calls.append,
            clock_ms=lambda: 10_000,
        )

        route, action = expected[skill]
        if route == ASSERTION_ONLY_ROUTE:
            assert calls == []
            assert result.status is CommandStatus.OK
            assert result.reason_code == ExecutorReasonCode.ASSERTION_VALIDATED.value
            assert "accepted safety validation evidence" in result.message
            assert result.raw_transport_payload is None
            continue

        assert len(calls) == 1
        payload = calls[0].payload
        definition = get_skill_definition(skill)
        assert payload["route"] == route
        assert payload["action"] == action
        assert payload["command_id"] == command.command_id
        assert payload["skill"] == skill.value
        assert payload["command_path"] == definition.command_path
        assert payload["expected_result_source"] == definition.expected_result_source
        assert payload["max_duration_ms"] == definition.max_duration_ms
        assert payload["parameters"] == command.params.model_dump(mode="json")
        assert payload["registry"] == {
            "command_path": definition.command_path,
            "expected_result_source": definition.expected_result_source,
            "max_duration_ms": definition.max_duration_ms,
            "success_assertion": definition.success_assertion.assertion_id,
        }
        if skill is PilotSkillName.STOP:
            assert result.status is CommandStatus.OK
            assert result.reason_code == ExecutorReasonCode.STOP_POLICY_TIMEOUT.value
            continue
        assert result.status is CommandStatus.STALE
        assert result.reason_code == ExecutorReasonCode.TRANSPORT_TIMEOUT.value


def test_transport_payloads_are_json_compatible_plain_data() -> None:
    command = _command_for_skill(PilotSkillName.FACE_TARGET)
    calls: list[TransportRequest] = []

    execute_validated_command(_accepted_validation(command), calls.append)

    payload = calls[0].payload
    encoded = json.dumps(payload, sort_keys=True)
    assert json.loads(encoded) == payload
    assert payload["route"] == OPERATOR_COMMAND_ROUTE
    assert payload["action"] == "align_to_tag"
    assert payload["tag_id"] == 7
    assert payload["tag_index"] == 7
    assert payload["timeout_s"] == 2.5
    assert payload["max_omega"] == 0.4
    assert isinstance(payload["parameters"], dict)


def test_non_tag_targets_use_bounded_control_payloads() -> None:
    command = _motion_command()
    calls: list[TransportRequest] = []

    execute_validated_command(_accepted_validation(command), calls.append)

    assert calls[0].payload["route"] == BOUNDED_CONTROL_ROUTE
    assert calls[0].payload["action"] == "approach_target"
    assert calls[0].payload["target_id"] == "block-1"
    assert "tag_id" not in calls[0].payload


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
