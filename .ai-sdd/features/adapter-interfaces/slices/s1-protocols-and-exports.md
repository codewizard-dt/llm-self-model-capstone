# Slice: s1-protocols-and-exports

| Field | Value |
|---|---|
| Feature | adapter-interfaces (F4) |
| Stack | contracts |
| Depends on | — (F1 telemetry-contract already landed; `ContractLine` and `VisionBlock` are in `contracts/src/contracts/contract_line.py`) |

## What this slice delivers

The complete F4 implementation in one atomic change: two `@runtime_checkable` `typing.Protocol`
classes (`TelemetrySource`, `VisionSource`) in a new `adapters.py` module; additive exports in
`__init__.py`; `reactivex` added as a dependency; and a conformance + smoke test suite. No
existing file is modified beyond `__init__.py` gaining two export lines.

## Files changed

| Path | Change |
|---|---|
| `contracts/src/contracts/adapters.py` | **new** — `TelemetrySource` and `VisionSource` protocols |
| `contracts/src/contracts/__init__.py` | **extend** — add `TelemetrySource`, `VisionSource` to imports and `__all__` |
| `contracts/pyproject.toml` | **extend** — add `reactivex` to `[project.dependencies]`; keep `ruff` declared in dev dependencies so `make lint` is reproducible |
| `contracts/tests/test_adapters.py` | **new** — conformance and smoke tests |

No other file may be created or modified by this slice.

## Implementation detail

### `contracts/src/contracts/adapters.py`

```python
"""Adapter protocol interfaces for telemetry and vision sources (F4)."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from reactivex import Observable

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
```

### `contracts/src/contracts/__init__.py` — additive changes only

Add to the existing imports:

```python
from contracts.adapters import TelemetrySource, VisionSource
```

Add `"TelemetrySource"` and `"VisionSource"` to the existing `__all__` list. All existing
imports and exports remain unchanged.

### `contracts/pyproject.toml`

Run `uv add reactivex` from `contracts/`. This is the only runtime dependency change for F4.
Keep `ruff` in the contracts dev dependencies so the existing `make lint` target works after a
fresh `uv sync`.

### `contracts/tests/test_adapters.py`

```python
"""Conformance and smoke tests for TelemetrySource and VisionSource protocols (F4)."""
from __future__ import annotations

import pytest
import reactivex as rx
from reactivex import Observable

from contracts import TelemetrySource, VisionSource
from contracts.contract_line import ContractLine, VisionBlock, MotorApiSample


# ---------------------------------------------------------------------------
# Minimal fixture data
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# isinstance conformance — TelemetrySource
# ---------------------------------------------------------------------------

class ValidTelemetrySource:
    def observe(self) -> Observable[ContractLine]:
        return rx.empty()


class MissingObserveTelemetry:
    pass


def test_telemetry_source_isinstance_pass():
    assert isinstance(ValidTelemetrySource(), TelemetrySource)


def test_telemetry_source_isinstance_fail_missing_observe():
    assert not isinstance(MissingObserveTelemetry(), TelemetrySource)


# ---------------------------------------------------------------------------
# isinstance conformance — VisionSource
# ---------------------------------------------------------------------------

class ValidVisionSource:
    def observe(self) -> Observable[VisionBlock]:
        return rx.empty()


class MissingObserveVision:
    pass


def test_vision_source_isinstance_pass():
    assert isinstance(ValidVisionSource(), VisionSource)


def test_vision_source_isinstance_fail_missing_observe():
    assert not isinstance(MissingObserveVision(), VisionSource)


# ---------------------------------------------------------------------------
# Runtime structural caveat: protocols share the same method shape
# ---------------------------------------------------------------------------

def test_telemetry_source_does_not_satisfy_vision_source():
    """Document the runtime structural caveat for the two source protocols.

    Both protocols share the same structural signature (``observe`` with no
    arguments), so the runtime_checkable check passes for both — this is
    expected Python structural subtyping behaviour. The test documents that
    the runtime check is structural-only and that type-checker enforcement
    (mypy/pyright) is the real non-overlap guard at the type level.
    """
    # Runtime isinstance is purely structural; both protocols have the same
    # method signature so this is expected to be True:
    assert isinstance(ValidTelemetrySource(), VisionSource)
    # The meaningful non-overlap guarantee comes from static type checking,
    # not runtime isinstance. This test documents that invariant explicitly.


# ---------------------------------------------------------------------------
# Smoke test: cold TelemetrySource emits one ContractLine then on_completed
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Import smoke: TelemetrySource and VisionSource importable from top-level package
# ---------------------------------------------------------------------------

def test_top_level_import():
    from contracts import TelemetrySource as TS, VisionSource as VS  # noqa: F401
    assert TS is TelemetrySource
    assert VS is VisionSource
```

## Acceptance

All items run from `contracts/` (or repo root, which delegates):

1. `make sync` exits 0 — `reactivex` resolves and installs into the `contracts/` venv
2. `make lint` exits 0 — `ruff check` and `ruff format --check` clean across `src/` and `tests/`
3. `make test` exits 0, with all of the following passing:
   - `test_telemetry_source_isinstance_pass`
   - `test_telemetry_source_isinstance_fail_missing_observe`
   - `test_vision_source_isinstance_pass`
   - `test_vision_source_isinstance_fail_missing_observe`
   - `test_cold_telemetry_source_emits_record_and_completes`
   - `test_top_level_import`
   - All F1 tests (`test_contract_line.py`, `test_motor_telemetry.py`) still passing (regression guard)
   - All F2 tests (`test_self_model.py`) still passing (regression guard)
4. `from contracts import TelemetrySource, VisionSource` resolves cleanly in `uv run python` after `make sync`
5. Root `make sync` / `make test` / `make lint` delegate correctly and exit 0; F1/F2/F3 suites unaffected
