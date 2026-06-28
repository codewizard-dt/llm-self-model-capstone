"""ROS-free executor core for accepted pilot skill commands."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from time import monotonic_ns
from typing import Protocol, TypeAlias

from contracts import CommandStatus, PilotSkillCommand, PilotSkillName
from pilot.safety import ValidationResult, ValidationStatus
from pilot.skills import SkillDefinition, get_skill_definition

ClockMs: TypeAlias = Callable[[], int]
JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
ExecutorPayload: TypeAlias = dict[str, JsonValue]

OPERATOR_COMMAND_ROUTE = "/operator/command"
BOUNDED_CONTROL_ROUTE = "bounded_control"
ASSERTION_ONLY_ROUTE = "assertion_only"
_ASSERTION_ONLY_SKILLS = frozenset({PilotSkillName.VERIFY_GRASP, PilotSkillName.VERIFY_DROP})


class ExecutorReasonCode(StrEnum):
    """Stable executor-local reason codes for boundary outcomes."""

    QUEUED = "queued"
    ASSERTION_VALIDATED = "assertion_validated"
    MISSING_COMMAND = "missing_command"
    MALFORMED_VALIDATION = "malformed_validation"
    TRANSPORT_FAILED = "transport_failed"


@dataclass(frozen=True, slots=True)
class ExecutorPolicy:
    """Executor timing policy stored for later transport/result slices."""

    transport_grace_ms: int = 0

    def __post_init__(self) -> None:
        if self.transport_grace_ms < 0:
            raise ValueError("transport_grace_ms must be non-negative")


@dataclass(frozen=True, slots=True)
class ExecutorDeadline:
    """Deadline metadata derived from the skill registry."""

    max_duration_ms: int
    transport_grace_ms: int
    deadline_ms: int | None


@dataclass(frozen=True, slots=True)
class ExecutorRoute:
    """Symbolic route metadata handed to concrete adapters in later slices."""

    command_path: str
    expected_result_source: str
    max_duration_ms: int


@dataclass(frozen=True, slots=True)
class TransportRequest:
    """Normalized command plus symbolic metadata passed across the transport boundary."""

    command: PilotSkillCommand
    command_id: str
    skill: PilotSkillName
    route: ExecutorRoute
    deadline: ExecutorDeadline
    payload: ExecutorPayload


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Deterministic executor outcome for logging and replay."""

    command_id: str | None
    skill: PilotSkillName | None
    status: CommandStatus
    reason_code: str
    message: str
    issued_ms: int | None
    completed_ms: int
    raw_transport_payload: object | None = None


class ExecutorTransport(Protocol):
    """ROS-free boundary implemented by fake tests and later concrete adapters."""

    def send(self, request: TransportRequest) -> object | None:
        """Hand off one normalized transport request."""


TransportBoundary: TypeAlias = ExecutorTransport | Callable[[TransportRequest], object | None]

DEFAULT_EXECUTOR_POLICY = ExecutorPolicy()


class SkillExecutor:
    """Execute accepted validation results through a narrow transport boundary."""

    def __init__(
        self,
        transport: TransportBoundary,
        *,
        policy: ExecutorPolicy = DEFAULT_EXECUTOR_POLICY,
        clock_ms: ClockMs | None = None,
    ) -> None:
        self._transport = transport
        self._policy = policy
        self._clock_ms = clock_ms or _monotonic_ms

    def execute(self, validation: object) -> ExecutionResult:
        """Queue one accepted validation result or return a deterministic refusal."""

        if not isinstance(validation, ValidationResult):
            return ExecutionResult(
                command_id=None,
                skill=None,
                status=CommandStatus.REJECTED,
                reason_code=ExecutorReasonCode.MALFORMED_VALIDATION.value,
                message="validation result is not a pilot safety ValidationResult",
                issued_ms=None,
                completed_ms=self._clock_ms(),
            )

        command = validation.command
        skill = _validation_skill(validation)
        if validation.status is not ValidationStatus.ACCEPTED:
            return ExecutionResult(
                command_id=_command_id(command),
                skill=skill,
                status=CommandStatus.REJECTED,
                reason_code=_validation_reason_code(validation),
                message=f"validation refused command: {_validation_message(validation)}",
                issued_ms=_issued_ms(command),
                completed_ms=self._clock_ms(),
            )
        if command is None:
            return ExecutionResult(
                command_id=None,
                skill=skill,
                status=CommandStatus.REJECTED,
                reason_code=ExecutorReasonCode.MISSING_COMMAND.value,
                message="accepted validation result is missing command",
                issued_ms=None,
                completed_ms=self._clock_ms(),
            )

        command_skill = PilotSkillName(str(command.skill))
        definition = get_skill_definition(command_skill)
        if command_skill in _ASSERTION_ONLY_SKILLS:
            return ExecutionResult(
                command_id=command.command_id,
                skill=command_skill,
                status=CommandStatus.OK,
                reason_code=ExecutorReasonCode.ASSERTION_VALIDATED.value,
                message=(
                    "assertion-only skill satisfied by accepted safety validation evidence; "
                    "no transport request issued"
                ),
                issued_ms=command.issued_ms,
                completed_ms=self._clock_ms(),
            )

        request = _transport_request(command, definition, policy=self._policy)
        try:
            raw_payload = _send(self._transport, request)
        except Exception as exc:  # pragma: no cover - defensive boundary for later adapters.
            return ExecutionResult(
                command_id=command.command_id,
                skill=command_skill,
                status=CommandStatus.FAILED,
                reason_code=ExecutorReasonCode.TRANSPORT_FAILED.value,
                message=f"transport boundary failed: {exc}",
                issued_ms=command.issued_ms,
                completed_ms=self._clock_ms(),
            )

        return ExecutionResult(
            command_id=command.command_id,
            skill=command_skill,
            status=CommandStatus.QUEUED,
            reason_code=ExecutorReasonCode.QUEUED.value,
            message="command queued at executor boundary",
            issued_ms=command.issued_ms,
            completed_ms=self._clock_ms(),
            raw_transport_payload=raw_payload,
        )


def execute_validated_command(
    validation: object,
    transport: TransportBoundary,
    *,
    policy: ExecutorPolicy = DEFAULT_EXECUTOR_POLICY,
    clock_ms: ClockMs | None = None,
) -> ExecutionResult:
    """Execute one safety validation result through the ROS-free executor core."""

    return SkillExecutor(transport, policy=policy, clock_ms=clock_ms).execute(validation)


def _transport_request(
    command: PilotSkillCommand,
    definition: SkillDefinition,
    *,
    policy: ExecutorPolicy,
) -> TransportRequest:
    issued_ms = command.issued_ms
    max_duration_ms = definition.max_duration_ms
    deadline = ExecutorDeadline(
        max_duration_ms=max_duration_ms,
        transport_grace_ms=policy.transport_grace_ms,
        deadline_ms=issued_ms + max_duration_ms + policy.transport_grace_ms,
    )
    route = ExecutorRoute(
        command_path=definition.command_path,
        expected_result_source=definition.expected_result_source,
        max_duration_ms=max_duration_ms,
    )
    return TransportRequest(
        command=command,
        command_id=command.command_id,
        skill=definition.name,
        route=route,
        deadline=deadline,
        payload=_transport_payload(command, definition, route=route, deadline=deadline),
    )


def _transport_payload(
    command: PilotSkillCommand,
    definition: SkillDefinition,
    *,
    route: ExecutorRoute,
    deadline: ExecutorDeadline,
) -> ExecutorPayload:
    command_skill = PilotSkillName(str(command.skill))
    mapping = _skill_transport_mapping(command_skill, _command_parameters(command))
    payload: ExecutorPayload = {
        "v": 1,
        "route": mapping["route"],
        "action": mapping["action"],
        "command_id": command.command_id,
        "skill": command_skill.value,
        "issued_ms": command.issued_ms,
        "command_path": route.command_path,
        "expected_result_source": route.expected_result_source,
        "max_duration_ms": route.max_duration_ms,
        "deadline_ms": deadline.deadline_ms,
        "parameters": mapping["parameters"],
        "registry": {
            "command_path": definition.command_path,
            "expected_result_source": definition.expected_result_source,
            "max_duration_ms": definition.max_duration_ms,
            "success_assertion": definition.success_assertion.assertion_id,
        },
    }
    payload.update(mapping["publish_fields"])
    return payload


def _skill_transport_mapping(
    skill: PilotSkillName,
    parameters: ExecutorPayload,
) -> ExecutorPayload:
    match skill:
        case PilotSkillName.STOP:
            return _bounded_control_mapping("halt", parameters)
        case PilotSkillName.SURVEY_SCENE:
            return _operator_mapping(
                "survey_scan",
                parameters,
                {
                    "duration_s": _ms_to_s(parameters["timeout_ms"]),
                    "omega_rad_s": None,
                },
            )
        case PilotSkillName.FACE_TARGET:
            tag_id = _tag_id_from_identifier(parameters["target_id"])
            if tag_id is None:
                return _bounded_control_mapping("face_target", parameters)
            return _operator_mapping(
                "align_to_tag",
                parameters,
                {
                    "tag_id": tag_id,
                    "tag_index": tag_id,
                    "timeout_s": _ms_to_s(parameters["timeout_ms"]),
                    "max_omega": parameters["max_turn_rad_s"],
                },
            )
        case PilotSkillName.APPROACH_TARGET:
            tag_id = _tag_id_from_identifier(parameters["target_id"])
            if tag_id is None:
                return _bounded_control_mapping("approach_target", parameters)
            return _operator_mapping(
                "move_to_tag",
                parameters,
                {
                    "tag_id": tag_id,
                    "tag_index": tag_id,
                    "target_distance_m": parameters["standoff_m"],
                },
            )
        case PilotSkillName.CENTER_OBJECT_IN_GRIPPER:
            return _bounded_control_mapping("center_object_in_gripper", parameters)
        case PilotSkillName.ARM_TO_ANGLE:
            return _operator_mapping(
                "arm",
                parameters,
                {
                    "target_deg": parameters["deg"],
                    "vel_rpm": parameters["vel_rpm"],
                },
            )
        case PilotSkillName.CLAW_OPEN:
            return _operator_mapping("release", parameters, {})
        case PilotSkillName.CLAW_CLOSE:
            return _operator_mapping("grab", parameters, {})
        case PilotSkillName.GO_TO_DESTINATION:
            destination_id = parameters["destination_id"]
            tag_id = _tag_id_from_identifier(destination_id) if destination_id is not None else None
            if tag_id is None:
                return _bounded_control_mapping("go_to_destination", parameters)
            return _operator_mapping(
                "move_to_tag",
                parameters,
                {
                    "tag_id": tag_id,
                    "tag_index": tag_id,
                    "target_distance_m": parameters["position_tolerance_m"],
                },
            )
        case PilotSkillName.VERIFY_GRASP | PilotSkillName.VERIFY_DROP:
            return _assertion_only_mapping(parameters)


def _operator_mapping(
    action: str,
    parameters: ExecutorPayload,
    publish_fields: Mapping[str, JsonValue],
) -> ExecutorPayload:
    return {
        "route": OPERATOR_COMMAND_ROUTE,
        "action": action,
        "parameters": parameters,
        "publish_fields": _without_none({**parameters, **dict(publish_fields)}),
    }


def _bounded_control_mapping(action: str, parameters: ExecutorPayload) -> ExecutorPayload:
    return {
        "route": BOUNDED_CONTROL_ROUTE,
        "action": action,
        "parameters": parameters,
        "publish_fields": parameters,
    }


def _assertion_only_mapping(parameters: ExecutorPayload) -> ExecutorPayload:
    return {
        "route": ASSERTION_ONLY_ROUTE,
        "action": "assertion_validated",
        "parameters": parameters,
        "publish_fields": {},
    }


def _command_parameters(command: PilotSkillCommand) -> ExecutorPayload:
    return command.params.model_dump(mode="json")


def _without_none(values: Mapping[str, JsonValue]) -> ExecutorPayload:
    return {key: value for key, value in values.items() if value is not None}


def _tag_id_from_identifier(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None
    candidate = value.removeprefix("tag-").removeprefix("tag_").removeprefix("apriltag-")
    return int(candidate) if candidate.isdecimal() else None


def _ms_to_s(value: JsonValue) -> float:
    return int(value) / 1000.0


def _send(transport: TransportBoundary, request: TransportRequest) -> object | None:
    if callable(transport):
        return transport(request)
    return transport.send(request)


def _validation_skill(validation: ValidationResult) -> PilotSkillName | None:
    if validation.command is not None:
        return PilotSkillName(str(validation.command.skill))
    return validation.skill


def _validation_reason_code(validation: ValidationResult) -> str:
    if not validation.reasons:
        return ExecutorReasonCode.MALFORMED_VALIDATION.value
    return str(validation.reasons[0].code.value)


def _validation_message(validation: ValidationResult) -> str:
    if not validation.reasons:
        return "validation result has no refusal reason"
    return validation.reasons[0].message


def _command_id(command: PilotSkillCommand | None) -> str | None:
    return command.command_id if command is not None else None


def _issued_ms(command: PilotSkillCommand | None) -> int | None:
    return command.issued_ms if command is not None else None


def _monotonic_ms() -> int:
    return monotonic_ns() // 1_000_000


__all__ = [
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
]
