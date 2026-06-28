"""ROS-free one-skill executor core for supervised pilot skill runs."""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import TypeAdapter, ValidationError

from contracts import CommandStatus, PilotSkillName, PilotSkillResult
from pilot.safety import (
    DEFAULT_SAFETY_POLICY,
    SafetyPolicy,
    ValidationMode,
    ValidationReasonCode,
    ValidationResult,
    validate_skill_command,
)
from pilot.trace import PilotTraceWriter, TraceSink, monotonic_ms


class ExecutionStatus(StrEnum):
    """Stable executor-level outcome status for later CLI integration."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    STALE = "stale"
    TIMED_OUT = "timed_out"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True, slots=True)
class TransportTerminalOutcome:
    """Transport-neutral terminal result shape for pilot skill execution."""

    status: CommandStatus | str
    command_id: str | None = None
    skill: PilotSkillName | str | None = None
    completed_ms: int | None = None
    message: str | None = None
    fault: str | None = None


TerminalOutcome = PilotSkillResult | TransportTerminalOutcome | Mapping[str, object]


@runtime_checkable
class SkillExecutionTransport(Protocol):
    """Minimal ROS-free transport boundary for one terminal pilot skill execution."""

    def dispatch(self, command: object) -> None:
        """Send exactly one validated command to the execution backend."""

    def wait_for_terminal_result(
        self,
        command: object,
        *,
        timeout_ms: int,
    ) -> TerminalOutcome:
        """Wait for one terminal result or raise TimeoutError/KeyboardInterrupt."""

    def cancel(self, command: object, *, reason: str) -> None:
        """Stop/cancel the in-flight command after timeout or interrupt."""


@dataclass(frozen=True, slots=True)
class SkillExecutionOutcome:
    """Structured executor return value for the future hardware CLI."""

    status: ExecutionStatus
    command_id: str | None
    skill: PilotSkillName | None
    validation: ValidationResult
    result: PilotSkillResult | None
    message: str

    @property
    def succeeded(self) -> bool:
        return self.status is ExecutionStatus.SUCCEEDED


_SKILL_RESULT_ADAPTER = TypeAdapter(PilotSkillResult)
_STATUS_ALIASES: dict[str, CommandStatus] = {
    "success": CommandStatus.OK,
    "succeeded": CommandStatus.OK,
    "ok": CommandStatus.OK,
    "rejected": CommandStatus.REJECTED,
    "reject": CommandStatus.REJECTED,
    "failed": CommandStatus.FAILED,
    "failure": CommandStatus.FAILED,
    "error": CommandStatus.FAILED,
    "stale": CommandStatus.STALE,
    "timeout": CommandStatus.STALE,
    "timed_out": CommandStatus.STALE,
    "expired": CommandStatus.STALE,
}


def execute_one_skill(
    command: object,
    observation: object,
    *,
    mode: ValidationMode | str,
    human_supervised: bool,
    timeout_ms: int,
    session_id: str,
    trace_sink: TraceSink | PilotTraceWriter,
    transport: SkillExecutionTransport,
    policy: SafetyPolicy = DEFAULT_SAFETY_POLICY,
    start_seq: int = 0,
    clock_ms: Callable[[], int] = monotonic_ms,
) -> SkillExecutionOutcome:
    """Validate, dispatch, wait for one terminal result, trace, and return."""

    if timeout_ms <= 0:
        raise ValueError("timeout_ms must be positive")
    trace_writer = _trace_writer(
        trace_sink,
        session_id=session_id,
        start_seq=start_seq,
        clock_ms=clock_ms,
    )

    validation = validate_skill_command(
        command,
        observation,
        mode=mode,
        policy=policy,
        human_supervised=human_supervised,
    )
    if not validation.accepted or validation.command is None:
        message = _validation_message(validation)
        trace_writer.write_stop(reason=_validation_stop_reason(validation), message=message)
        return SkillExecutionOutcome(
            status=ExecutionStatus.REJECTED,
            command_id=getattr(validation.command, "command_id", None),
            skill=validation.skill,
            validation=validation,
            result=None,
            message=message,
        )

    accepted_command = validation.command
    trace_writer.write_command(accepted_command)
    transport.dispatch(accepted_command)

    try:
        terminal = transport.wait_for_terminal_result(accepted_command, timeout_ms=timeout_ms)
    except TimeoutError:
        transport.cancel(accepted_command, reason="timeout")
        message = f"timed out waiting for terminal result after {timeout_ms} ms"
        trace_writer.write_stop(reason="failure", message=message)
        return SkillExecutionOutcome(
            status=ExecutionStatus.TIMED_OUT,
            command_id=accepted_command.command_id,
            skill=PilotSkillName(str(accepted_command.skill)),
            validation=validation,
            result=None,
            message=message,
        )
    except KeyboardInterrupt:
        transport.cancel(accepted_command, reason="interrupt")
        message = "execution interrupted by operator"
        trace_writer.write_stop(reason="operator", message=message)
        return SkillExecutionOutcome(
            status=ExecutionStatus.INTERRUPTED,
            command_id=accepted_command.command_id,
            skill=PilotSkillName(str(accepted_command.skill)),
            validation=validation,
            result=None,
            message=message,
        )

    result = normalize_skill_result(terminal, command=accepted_command)
    trace_writer.write_result(result)
    stop_reason = "success" if result.status is CommandStatus.OK else "failure"
    trace_writer.write_stop(reason=stop_reason, message=result.message or _result_message(result))
    return SkillExecutionOutcome(
        status=_execution_status(result.status),
        command_id=result.command_id,
        skill=result.skill,
        validation=validation,
        result=result,
        message=result.message or _result_message(result),
    )


def normalize_skill_result(terminal: TerminalOutcome, *, command: object) -> PilotSkillResult:
    """Normalize a transport terminal outcome to a contract-owned skill result."""

    command_id = getattr(command, "command_id")
    skill = PilotSkillName(str(getattr(command, "skill")))
    if isinstance(terminal, PilotSkillResult):
        return _SKILL_RESULT_ADAPTER.validate_python(terminal)

    if isinstance(terminal, TransportTerminalOutcome):
        payload: dict[str, object] = {
            "command_id": terminal.command_id or command_id,
            "skill": terminal.skill or skill,
            "status": _normalize_status(terminal.status),
            "completed_ms": terminal.completed_ms,
            "message": terminal.message,
            "fault": terminal.fault,
        }
    else:
        payload = dict(terminal)
        payload["command_id"] = payload.get("command_id") or command_id
        payload["skill"] = payload.get("skill") or skill
        payload["status"] = _normalize_status(payload["status"])

    return _validate_result_payload(payload)


def _validate_result_payload(payload: Mapping[str, object]) -> PilotSkillResult:
    compact = {key: value for key, value in payload.items() if value is not None}
    try:
        return _SKILL_RESULT_ADAPTER.validate_python(compact)
    except ValidationError as exc:
        raise ValueError("terminal outcome is not a contract-valid pilot skill result") from exc


def _normalize_status(status: CommandStatus | str | object) -> CommandStatus:
    if isinstance(status, CommandStatus):
        return status
    value = str(status)
    try:
        return CommandStatus(value)
    except ValueError:
        pass
    try:
        return _STATUS_ALIASES[value.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown terminal status: {value}") from exc


def _execution_status(status: CommandStatus) -> ExecutionStatus:
    match status:
        case CommandStatus.OK:
            return ExecutionStatus.SUCCEEDED
        case CommandStatus.REJECTED:
            return ExecutionStatus.REJECTED
        case CommandStatus.STALE:
            return ExecutionStatus.STALE
        case _:
            return ExecutionStatus.FAILED


def _result_message(result: PilotSkillResult) -> str:
    return f"{result.skill.value} completed with status {result.status.value}"


def _validation_message(validation: ValidationResult) -> str:
    reasons = "; ".join(f"{reason.code.value}: {reason.message}" for reason in validation.reasons)
    return f"validation rejected: {reasons}"


def _validation_stop_reason(validation: ValidationResult) -> str:
    if any(
        reason.code is ValidationReasonCode.HUMAN_SUPERVISION_REQUIRED
        for reason in validation.reasons
    ):
        return "request_human"
    return "failure"


def _trace_writer(
    trace_sink: TraceSink | PilotTraceWriter,
    *,
    session_id: str,
    start_seq: int,
    clock_ms: Callable[[], int],
) -> PilotTraceWriter:
    if isinstance(trace_sink, PilotTraceWriter):
        if trace_sink.session_id != session_id:
            raise ValueError("trace writer session_id must match executor session_id")
        return trace_sink
    return PilotTraceWriter(
        trace_sink,
        session_id=session_id,
        start_seq=start_seq,
        clock_ms=clock_ms,
    )


__all__ = [
    "ExecutionStatus",
    "SkillExecutionOutcome",
    "SkillExecutionTransport",
    "TerminalOutcome",
    "TransportTerminalOutcome",
    "execute_one_skill",
    "normalize_skill_result",
]
