from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

try:
    from reactivex import Observable
except ModuleNotFoundError:
    Observable = Any

from contracts.contract_line import ContractLine, VisionBlock


@runtime_checkable
class TelemetrySource(Protocol):
    """Swap-in boundary for all telemetry producers.

    Implementations must return a cold or hot ``Observable[ContractLine]``.
    Exhaustion signals ``on_completed``; errors signal ``on_error``.
    Lifecycle (open/close) is managed by the concrete class, not this protocol.
    """

    def observe(self) -> Observable[ContractLine]: ...


@runtime_checkable
class VisionSource(Protocol):
    """Swap-in boundary for all vision producers.

    Implementations must return a cold or hot ``Observable[VisionBlock]``.
    A frame with no detection emits a sentinel ``VisionBlock(object_detected=False, ...)``;
    callers check ``item.object_detected`` rather than receiving ``None``.
    """

    def observe(self) -> Observable[VisionBlock]: ...
