"""ROS-free executor core for accepted pilot skill commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from time import monotonic_ns
from typing import Protocol, TypeAlias

from contracts import CommandStatus, PilotSkillCommand, PilotSkillName
from pilot.safety import ValidationResult, ValidationStatus
from pilot.skills import SkillDefinition, get_skill_definition

ClockMs: TypeAlias = Callable[[], int]


class ExecutorReasonCode(StrEnum):
    """Stable executor-local reason codes for boundary outcomes."""

    QUEUED = "queued"
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
    return TransportRequest(
        command=command,
        command_id=command.command_id,
        skill=definition.name,
        route=ExecutorRoute(
            command_path=definition.command_path,
            expected_result_source=definition.expected_result_source,
            max_duration_ms=max_duration_ms,
        ),
        deadline=ExecutorDeadline(
            max_duration_ms=max_duration_ms,
            transport_grace_ms=policy.transport_grace_ms,
            deadline_ms=issued_ms + max_duration_ms + policy.transport_grace_ms,
        ),
    )


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
