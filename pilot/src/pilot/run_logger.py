"""ROS-free core API for pilot run trace records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final, Literal, TypeAlias, cast
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from contracts import (
    AssertionTraceRecord,
    CommandTraceRecord,
    DecisionTraceRecord,
    ObservationTraceRecord,
    PilotAssertion,
    PilotDecision,
    PilotObservation,
    PilotSkillCommand,
    PilotSkillResult,
    PilotTraceRecord,
    ResultTraceRecord,
    StopTraceRecord,
)

SESSION_ID_MAX_LENGTH: Final = 80
STOP_REASONS: Final = ("success", "failure", "operator", "fault", "request_human")

MonotonicClock: TypeAlias = Callable[[], int]
StopReason: TypeAlias = Literal["success", "failure", "operator", "fault", "request_human"]

_TRACE_RECORD_ADAPTER: Final[TypeAdapter[PilotTraceRecord]] = TypeAdapter(PilotTraceRecord)


class RunLoggerError(ValueError):
    """Raised when a trace record cannot be built without consuming sequence state."""


@dataclass(frozen=True, slots=True)
class RunLoggerConfig:
    """Immutable configuration for a single pilot run logger instance."""

    session_id: str | None = None
    start_seq: int = 0
    monotonic_clock: MonotonicClock | None = None

    def __post_init__(self) -> None:
        if self.session_id is not None:
            _validate_session_id(self.session_id)
        _validate_sequence(self.start_seq)
        if self.monotonic_clock is not None and not callable(self.monotonic_clock):
            raise RunLoggerError("monotonic_clock must be callable")


class RunLogger:
    """Build contract-valid pilot trace records with stable session metadata."""

    def __init__(self, config: RunLoggerConfig | None = None) -> None:
        self._config = config or RunLoggerConfig()
        self._session_id = self._config.session_id or default_session_id()
        _validate_session_id(self._session_id)
        self._next_seq = self._config.start_seq

    @property
    def session_id(self) -> str:
        """Stable session identifier written to every record from this logger."""

        return self._session_id

    @property
    def next_seq(self) -> int:
        """Sequence number that will be used by the next successful record build."""

        return self._next_seq

    def append_observation(
        self,
        observation: PilotObservation | object,
        *,
        monotonic_ms: int | None = None,
    ) -> ObservationTraceRecord:
        """Build an observation trace record without performing file I/O."""

        record = self._build_record(
            "observation",
            {"observation": observation},
            monotonic_ms=monotonic_ms,
        )
        return cast(ObservationTraceRecord, record)

    def append_decision(
        self,
        decision: PilotDecision | object,
        *,
        monotonic_ms: int | None = None,
    ) -> DecisionTraceRecord:
        """Build a decision trace record without performing file I/O."""

        record = self._build_record("decision", {"decision": decision}, monotonic_ms=monotonic_ms)
        return cast(DecisionTraceRecord, record)

    def append_command(
        self,
        command: PilotSkillCommand | object,
        *,
        monotonic_ms: int | None = None,
    ) -> CommandTraceRecord:
        """Build a command trace record without performing file I/O."""

        record = self._build_record("command", {"command": command}, monotonic_ms=monotonic_ms)
        return cast(CommandTraceRecord, record)

    def append_result(
        self,
        result: PilotSkillResult | object,
        *,
        monotonic_ms: int | None = None,
    ) -> ResultTraceRecord:
        """Build a result trace record without performing file I/O."""

        record = self._build_record("result", {"result": result}, monotonic_ms=monotonic_ms)
        return cast(ResultTraceRecord, record)

    def append_assertion(
        self,
        assertion: PilotAssertion | object,
        *,
        monotonic_ms: int | None = None,
    ) -> AssertionTraceRecord:
        """Build an assertion trace record without performing file I/O."""

        record = self._build_record(
            "assertion",
            {"assertion": assertion},
            monotonic_ms=monotonic_ms,
        )
        return cast(AssertionTraceRecord, record)

    def append_stop(
        self,
        reason: StopReason | str,
        *,
        message: str | None = None,
        monotonic_ms: int | None = None,
    ) -> StopTraceRecord:
        """Build a stop trace record without performing file I/O."""

        record = self._build_record(
            "stop",
            {"reason": reason, "message": message},
            monotonic_ms=monotonic_ms,
        )
        return cast(StopTraceRecord, record)

    def _build_record(
        self,
        event: str,
        payload: dict[str, object],
        *,
        monotonic_ms: int | None,
    ) -> PilotTraceRecord:
        seq = self._next_seq
        resolved_monotonic_ms = self._resolve_monotonic_ms(monotonic_ms)
        raw_record = {
            "v": 1,
            "session_id": self._session_id,
            "seq": seq,
            "monotonic_ms": resolved_monotonic_ms,
            "event": event,
            **payload,
        }

        try:
            record = _TRACE_RECORD_ADAPTER.validate_python(raw_record)
        except ValidationError as exc:
            raise RunLoggerError(f"invalid {event} trace record") from exc

        self._next_seq = seq + 1
        return record

    def _resolve_monotonic_ms(self, monotonic_ms: int | None) -> int:
        if monotonic_ms is not None:
            return _validate_monotonic_ms(monotonic_ms)
        if self._config.monotonic_clock is None:
            raise RunLoggerError("monotonic_ms requires an explicit value or monotonic_clock")
        return _validate_monotonic_ms(self._config.monotonic_clock())


def default_session_id() -> str:
    """Return a non-empty session id without using ROS or hardware state."""

    return f"run-{uuid4().hex}"


def _validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id.strip():
        raise RunLoggerError("session_id must be a non-empty string")
    if len(session_id) > SESSION_ID_MAX_LENGTH:
        raise RunLoggerError(f"session_id must be {SESSION_ID_MAX_LENGTH} characters or fewer")


def _validate_sequence(seq: int) -> None:
    if type(seq) is not int or seq < 0:
        raise RunLoggerError("start_seq must be a non-negative integer")


def _validate_monotonic_ms(monotonic_ms: int) -> int:
    if type(monotonic_ms) is not int or monotonic_ms < 0:
        raise RunLoggerError("monotonic_ms must be a non-negative integer")
    return monotonic_ms


__all__ = [
    "STOP_REASONS",
    "RunLogger",
    "RunLoggerConfig",
    "RunLoggerError",
    "StopReason",
    "default_session_id",
]
