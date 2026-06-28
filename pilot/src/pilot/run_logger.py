"""ROS-free core API for pilot run trace records."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import json
from json import JSONDecodeError
from os import PathLike
from pathlib import Path
import re
from typing import Callable, Final, Literal, TextIO, TypeAlias, cast
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
DEFAULT_HISTORY_MAX_RECORDS: Final = 12
DEFAULT_HISTORY_MAX_CHARS: Final = 2_000
_SUMMARY_FIELD_MAX_CHARS: Final = 96
_SUMMARY_LIST_LIMIT: Final = 3
_TRUNCATION_SUFFIX: Final = " ... [truncated]"
_SECRET_ASSIGNMENT_RE: Final = re.compile(
    r"\b[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)[A-Z0-9_]*\s*=\s*[^\s,;|]+",
    re.IGNORECASE,
)
_JSON_FRAGMENT_RE: Final = re.compile(r"[\[{][^\[\]{}]{2,240}[\]}]")
_TRANSCRIPT_MARKER_RE: Final = re.compile(
    r"\b(?:system|user|assistant|human)\s*:\s*[^|;]+",
    re.IGNORECASE,
)

MonotonicClock: TypeAlias = Callable[[], int]
StopReason: TypeAlias = Literal["success", "failure", "operator", "fault", "request_human"]

_TRACE_RECORD_ADAPTER: Final[TypeAdapter[PilotTraceRecord]] = TypeAdapter(PilotTraceRecord)


class RunLoggerError(ValueError):
    """Raised when a trace record cannot be built without consuming sequence state."""


class RunLoggerReadbackError(RunLoggerError):
    """Raised when a persisted JSONL trace line cannot be read as a trace record."""

    def __init__(self, line_number: int, message: str) -> None:
        self.line_number = line_number
        super().__init__(f"line {line_number}: {message}")


@dataclass(frozen=True, slots=True)
class RunLoggerConfig:
    """Immutable configuration for a single pilot run logger instance."""

    session_id: str | None = None
    trace_path: str | PathLike[str] | None = None
    start_seq: int = 0
    monotonic_clock: MonotonicClock | None = None
    flush_after_append: bool = True

    def __post_init__(self) -> None:
        if self.session_id is not None:
            _validate_session_id(self.session_id)
        if self.trace_path is not None:
            _validate_trace_path(self.trace_path)
        _validate_sequence(self.start_seq)
        if self.monotonic_clock is not None and not callable(self.monotonic_clock):
            raise RunLoggerError("monotonic_clock must be callable")
        if type(self.flush_after_append) is not bool:
            raise RunLoggerError("flush_after_append must be a bool")


class RunLogger:
    """Build contract-valid pilot trace records with stable session metadata."""

    def __init__(self, config: RunLoggerConfig | None = None) -> None:
        self._config = config or RunLoggerConfig()
        self._session_id = self._config.session_id or default_session_id()
        _validate_session_id(self._session_id)
        self._trace_path = _resolve_trace_path(self._session_id, self._config.trace_path)
        self._next_seq = self._config.start_seq
        self._file: TextIO | None = None

    @property
    def session_id(self) -> str:
        """Stable session identifier written to every record from this logger."""

        return self._session_id

    @property
    def trace_path(self) -> Path:
        """JSONL path owned by this logger."""

        return self._trace_path

    @property
    def next_seq(self) -> int:
        """Sequence number that will be used by the next successful record build."""

        return self._next_seq

    def __enter__(self) -> RunLogger:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the trace file if it has been opened."""

        if self._file is None:
            return
        self._file.close()
        self._file = None

    def append_observation(
        self,
        observation: PilotObservation | object,
        *,
        monotonic_ms: int | None = None,
    ) -> ObservationTraceRecord:
        """Append an observation trace record to this logger's JSONL trace."""

        record = self._build_record(
            "observation",
            {"observation": observation},
            monotonic_ms=monotonic_ms,
        )
        self._append_validated_record(record)
        return cast(ObservationTraceRecord, record)

    def append_decision(
        self,
        decision: PilotDecision | object,
        *,
        monotonic_ms: int | None = None,
    ) -> DecisionTraceRecord:
        """Append a decision trace record to this logger's JSONL trace."""

        record = self._build_record("decision", {"decision": decision}, monotonic_ms=monotonic_ms)
        self._append_validated_record(record)
        return cast(DecisionTraceRecord, record)

    def append_command(
        self,
        command: PilotSkillCommand | object,
        *,
        monotonic_ms: int | None = None,
    ) -> CommandTraceRecord:
        """Append a command trace record to this logger's JSONL trace."""

        record = self._build_record("command", {"command": command}, monotonic_ms=monotonic_ms)
        self._append_validated_record(record)
        return cast(CommandTraceRecord, record)

    def append_result(
        self,
        result: PilotSkillResult | object,
        *,
        monotonic_ms: int | None = None,
    ) -> ResultTraceRecord:
        """Append a result trace record to this logger's JSONL trace."""

        record = self._build_record("result", {"result": result}, monotonic_ms=monotonic_ms)
        self._append_validated_record(record)
        return cast(ResultTraceRecord, record)

    def append_assertion(
        self,
        assertion: PilotAssertion | object,
        *,
        monotonic_ms: int | None = None,
    ) -> AssertionTraceRecord:
        """Append an assertion trace record to this logger's JSONL trace."""

        record = self._build_record(
            "assertion",
            {"assertion": assertion},
            monotonic_ms=monotonic_ms,
        )
        self._append_validated_record(record)
        return cast(AssertionTraceRecord, record)

    def append_stop(
        self,
        reason: StopReason | str,
        *,
        message: str | None = None,
        monotonic_ms: int | None = None,
    ) -> StopTraceRecord:
        """Append a stop trace record to this logger's JSONL trace."""

        record = self._build_record(
            "stop",
            {"reason": reason, "message": message},
            monotonic_ms=monotonic_ms,
        )
        self._append_validated_record(record)
        return cast(StopTraceRecord, record)

    def _build_record(
        self,
        event: str,
        payload: dict[str, object],
        *,
        monotonic_ms: int | None,
    ) -> PilotTraceRecord:
        resolved_monotonic_ms = self._resolve_monotonic_ms(monotonic_ms)
        raw_record = {
            "v": 1,
            "session_id": self._session_id,
            "seq": self._next_seq,
            "monotonic_ms": resolved_monotonic_ms,
            "event": event,
            **payload,
        }

        try:
            record = _TRACE_RECORD_ADAPTER.validate_python(raw_record)
        except ValidationError as exc:
            raise RunLoggerError(f"invalid {event} trace record") from exc

        return record

    def _append_validated_record(self, record: PilotTraceRecord) -> None:
        line = record.model_dump_json() + "\n"
        trace_file = self._open_trace_file()
        trace_file.write(line)
        if self._config.flush_after_append:
            trace_file.flush()
        self._next_seq = record.seq + 1

    def _open_trace_file(self) -> TextIO:
        if self._file is not None:
            return self._file
        self._trace_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._trace_path.open("a", encoding="utf-8")
        return self._file

    def _resolve_monotonic_ms(self, monotonic_ms: int | None) -> int:
        if monotonic_ms is not None:
            return _validate_monotonic_ms(monotonic_ms)
        if self._config.monotonic_clock is None:
            raise RunLoggerError("monotonic_ms requires an explicit value or monotonic_clock")
        return _validate_monotonic_ms(self._config.monotonic_clock())


def default_session_id() -> str:
    """Return a non-empty session id without using ROS or hardware state."""

    return f"run-{uuid4().hex}"


def default_trace_path(session_id: str) -> Path:
    """Return the default ignored JSONL path for a pilot run session."""

    _validate_session_id(session_id)
    return Path(__file__).resolve().parents[2] / "runs" / f"{session_id}.jsonl"


def read_trace_records(source: str | PathLike[str] | TextIO) -> list[PilotTraceRecord]:
    """Read contract-validated pilot trace records from a JSONL path or text stream."""

    if _is_text_stream(source):
        return _read_trace_record_lines(source)

    with Path(source).open(encoding="utf-8") as trace_file:
        return _read_trace_record_lines(trace_file)


def format_recent_history(
    records: Sequence[PilotTraceRecord],
    *,
    max_records: int = DEFAULT_HISTORY_MAX_RECORDS,
    max_chars: int = DEFAULT_HISTORY_MAX_CHARS,
) -> str:
    """Return compact deterministic prompt history derived from typed trace records."""

    _validate_history_bound("max_records", max_records)
    _validate_history_bound("max_chars", max_chars)
    if max_records == 0 or max_chars == 0:
        return ""

    recent_records = records[-max_records:]
    summaries = [_summarize_trace_record(record) for record in recent_records]
    return _fit_recent_summaries(summaries, max_chars)


def _resolve_trace_path(session_id: str, trace_path: str | PathLike[str] | None) -> Path:
    if trace_path is None:
        return default_trace_path(session_id)
    return Path(trace_path)


def _validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id.strip():
        raise RunLoggerError("session_id must be a non-empty string")
    if len(session_id) > SESSION_ID_MAX_LENGTH:
        raise RunLoggerError(f"session_id must be {SESSION_ID_MAX_LENGTH} characters or fewer")


def _validate_trace_path(trace_path: str | PathLike[str]) -> None:
    try:
        path_text = str(trace_path)
    except TypeError as exc:
        raise RunLoggerError("trace_path must be a path-like value") from exc
    if not path_text.strip():
        raise RunLoggerError("trace_path must be a non-empty path")


def _validate_sequence(seq: int) -> None:
    if type(seq) is not int or seq < 0:
        raise RunLoggerError("start_seq must be a non-negative integer")


def _validate_monotonic_ms(monotonic_ms: int) -> int:
    if type(monotonic_ms) is not int or monotonic_ms < 0:
        raise RunLoggerError("monotonic_ms must be a non-negative integer")
    return monotonic_ms


def _is_text_stream(source: object) -> bool:
    return hasattr(source, "read") and callable(source.read)


def _read_trace_record_lines(lines: Iterable[str]) -> list[PilotTraceRecord]:
    records: list[PilotTraceRecord] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        records.append(_read_trace_record_line(line, line_number))
    return records


def _read_trace_record_line(line: str, line_number: int) -> PilotTraceRecord:
    try:
        raw_record = json.loads(line)
    except JSONDecodeError as exc:
        raise RunLoggerReadbackError(line_number, f"malformed JSON: {exc.msg}") from exc

    if not isinstance(raw_record, dict):
        raise RunLoggerReadbackError(line_number, "trace record must be a JSON object")

    try:
        return _TRACE_RECORD_ADAPTER.validate_python(raw_record)
    except ValidationError as exc:
        raise RunLoggerReadbackError(
            line_number,
            f"schema-invalid trace record: {_format_validation_error(exc)}",
        ) from exc


def _format_validation_error(exc: ValidationError) -> str:
    formatted_errors: list[str] = []
    for error in exc.errors()[:3]:
        loc = ".".join(str(part) for part in error.get("loc", ())) or "record"
        message = str(error.get("msg", "invalid value"))
        formatted_errors.append(f"{loc}: {message}")
    return "; ".join(formatted_errors)


def _validate_history_bound(name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise RunLoggerError(f"{name} must be a non-negative integer")


def _fit_recent_summaries(summaries: Sequence[str], max_chars: int) -> str:
    selected: list[str] = []
    used_chars = 0
    for summary in reversed(summaries):
        separator_chars = 1 if selected else 0
        next_chars = len(summary) + separator_chars
        if used_chars + next_chars <= max_chars:
            selected.append(summary)
            used_chars += next_chars
            continue
        if not selected:
            selected.append(_clip_text(summary, max_chars))
        break
    return "\n".join(reversed(selected))


def _summarize_trace_record(record: PilotTraceRecord) -> str:
    prefix = f"seq={record.seq} {record.event}"
    if isinstance(record, ObservationTraceRecord):
        return _summarize_observation(prefix, record.observation)
    if isinstance(record, DecisionTraceRecord):
        return _summarize_decision(prefix, record.decision)
    if isinstance(record, CommandTraceRecord):
        return f"{prefix}: {_summarize_command(record.command)}"
    if isinstance(record, ResultTraceRecord):
        return f"{prefix}: {_summarize_result(record.result)}"
    if isinstance(record, AssertionTraceRecord):
        return f"{prefix}: {_summarize_assertion(record.assertion)}"
    return _summarize_stop(prefix, cast(StopTraceRecord, record))


def _summarize_observation(prefix: str, observation: PilotObservation) -> str:
    parts = [
        f"phase={_value(observation.task_phase)}",
        f"objective={_safe_text(observation.objective)}",
        f"bridge={observation.bridge.state}",
        f"claw={observation.manipulator.claw_state}",
    ]
    if observation.last_command is not None:
        parts.append(f"last_command={_summarize_command(observation.last_command)}")
    if observation.last_result is not None:
        parts.append(f"last_result={_summarize_result(observation.last_result)}")
    if observation.current_assertions:
        assertions = ", ".join(
            _summarize_assertion(assertion)
            for assertion in observation.current_assertions[:_SUMMARY_LIST_LIMIT]
        )
        parts.append(f"assertions={assertions}")
    if observation.recent_failures:
        failures = ", ".join(
            _summarize_failure(failure)
            for failure in observation.recent_failures[:_SUMMARY_LIST_LIMIT]
        )
        parts.append(f"failures={failures}")
    return f"{prefix}: {'; '.join(parts)}"


def _summarize_decision(prefix: str, decision: PilotDecision) -> str:
    parts = [
        f"id={_safe_text(decision.decision_id)}",
        f"action={_value(decision.action)}",
        f"confidence={decision.confidence:.2f}",
    ]
    if decision.command is not None:
        parts.append(f"command={_summarize_command(decision.command)}")
    if decision.retry_of_command_id is not None:
        parts.append(f"retry_of={_safe_text(decision.retry_of_command_id)}")
    if decision.stop_reason is not None:
        parts.append(f"stop_reason={_safe_text(decision.stop_reason)}")
    parts.append(f"rationale={_safe_text(decision.rationale)}")
    return f"{prefix}: {'; '.join(parts)}"


def _summarize_command(command: PilotSkillCommand) -> str:
    return f"{_safe_text(command.command_id)}/{command.skill} issued_ms={command.issued_ms}"


def _summarize_result(result: PilotSkillResult) -> str:
    parts = [
        f"{_safe_text(result.command_id)}/{_value(result.skill)}",
        f"status={_value(result.status)}",
    ]
    if result.completed_ms is not None:
        parts.append(f"completed_ms={result.completed_ms}")
    if result.message is not None:
        parts.append(f"message={_safe_text(result.message)}")
    if result.fault is not None:
        parts.append(f"fault={_safe_text(result.fault)}")
    return " ".join(parts)


def _summarize_assertion(assertion: PilotAssertion) -> str:
    parts = [
        _safe_text(assertion.assertion_id),
        f"state={_value(assertion.state)}",
        f"confidence={assertion.confidence:.2f}",
        f"predicate={_safe_text(assertion.predicate)}",
    ]
    if assertion.recovery_hint is not None:
        parts.append(f"recovery={_safe_text(assertion.recovery_hint)}")
    return " ".join(parts)


def _summarize_failure(failure: object) -> str:
    source = _safe_text(str(getattr(failure, "source", "unknown")))
    summary = _safe_text(str(getattr(failure, "summary", "failure")))
    command_id = getattr(failure, "command_id", None)
    recovery_hint = getattr(failure, "recovery_hint", None)
    parts = [f"{source}: {summary}"]
    if command_id is not None:
        parts.append(f"command_id={_safe_text(str(command_id))}")
    if recovery_hint is not None:
        parts.append(f"recovery={_safe_text(str(recovery_hint))}")
    return " ".join(parts)


def _summarize_stop(prefix: str, record: StopTraceRecord) -> str:
    parts = [f"reason={record.reason}"]
    if record.message is not None:
        parts.append(f"message={_safe_text(record.message)}")
    return f"{prefix}: {'; '.join(parts)}"


def _safe_text(value: str, max_chars: int = _SUMMARY_FIELD_MAX_CHARS) -> str:
    text = "".join(char if char.isprintable() else " " for char in value)
    text = " ".join(text.split())
    text = _SECRET_ASSIGNMENT_RE.sub("[redacted-secret]", text)
    text = _TRANSCRIPT_MARKER_RE.sub("[redacted-transcript]", text)
    text = _JSON_FRAGMENT_RE.sub("[redacted-json]", text)
    return _clip_text(text, max_chars)


def _clip_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= len(_TRUNCATION_SUFFIX):
        return _TRUNCATION_SUFFIX[:max_chars]
    return f"{text[: max_chars - len(_TRUNCATION_SUFFIX)]}{_TRUNCATION_SUFFIX}"


def _value(value: object) -> object:
    return getattr(value, "value", value)


__all__ = [
    "DEFAULT_HISTORY_MAX_CHARS",
    "DEFAULT_HISTORY_MAX_RECORDS",
    "STOP_REASONS",
    "RunLogger",
    "RunLoggerConfig",
    "RunLoggerError",
    "RunLoggerReadbackError",
    "StopReason",
    "default_session_id",
    "default_trace_path",
    "format_recent_history",
    "read_trace_records",
]
