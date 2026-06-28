"""ROS-free JSONL trace helpers for pilot executor runs."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

from pydantic import TypeAdapter

from contracts import (
    CommandTraceRecord,
    PilotSkillCommand,
    PilotSkillResult,
    PilotTraceRecord,
    ResultTraceRecord,
    StopTraceRecord,
)


class TraceSink(Protocol):
    """Minimal text sink used by the JSONL writer."""

    def write(self, text: str, /) -> object:
        """Write one JSONL fragment."""

    def flush(self) -> object:
        """Flush buffered trace output."""


_TRACE_RECORD_ADAPTER = TypeAdapter(PilotTraceRecord)


def monotonic_ms() -> int:
    """Return a non-negative monotonic timestamp in milliseconds."""

    return time.monotonic_ns() // 1_000_000


class PilotTraceWriter:
    """Append contract-valid pilot trace records as JSONL with stable sequence numbers."""

    def __init__(
        self,
        sink: TraceSink,
        *,
        session_id: str,
        start_seq: int = 0,
        clock_ms: Callable[[], int] = monotonic_ms,
    ) -> None:
        if start_seq < 0:
            raise ValueError("start_seq must be non-negative")
        self._sink = sink
        self._session_id = session_id
        self._next_seq = start_seq
        self._clock_ms = clock_ms

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def next_seq(self) -> int:
        return self._next_seq

    def write_command(self, command: PilotSkillCommand) -> CommandTraceRecord:
        record = CommandTraceRecord(
            session_id=self._session_id,
            seq=self._consume_seq(),
            monotonic_ms=self._monotonic_ms(),
            command=command,
        )
        self.write_record(record)
        return record

    def write_result(self, result: PilotSkillResult) -> ResultTraceRecord:
        record = ResultTraceRecord(
            session_id=self._session_id,
            seq=self._consume_seq(),
            monotonic_ms=self._monotonic_ms(),
            result=result,
        )
        self.write_record(record)
        return record

    def write_stop(
        self,
        *,
        reason: str,
        message: str | None = None,
    ) -> StopTraceRecord:
        record = StopTraceRecord(
            session_id=self._session_id,
            seq=self._consume_seq(),
            monotonic_ms=self._monotonic_ms(),
            reason=reason,
            message=message,
        )
        self.write_record(record)
        return record

    def write_record(self, record: PilotTraceRecord) -> PilotTraceRecord:
        validated = _TRACE_RECORD_ADAPTER.validate_python(record)
        self._sink.write(validated.model_dump_json())
        self._sink.write("\n")
        self._sink.flush()
        return validated

    def _consume_seq(self) -> int:
        seq = self._next_seq
        self._next_seq += 1
        return seq

    def _monotonic_ms(self) -> int:
        value = self._clock_ms()
        if value < 0:
            raise ValueError("clock_ms must return a non-negative integer")
        return value


__all__ = [
    "PilotTraceWriter",
    "TraceSink",
    "monotonic_ms",
]
