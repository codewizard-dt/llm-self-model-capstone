# Slice: pydantic-models

| Field | Value |
|---|---|
| Feature | telemetry-contract (F1) |
| Stack | contracts |
| Depends on | package-scaffold |

## What this slice delivers

All pydantic v2 models for the Task Telemetry Contract, plus the JSON Schema export. This is a **migration + extension** — the `MotorApiSample` family is moved from the branch into the right vertical; `ContractLine` and `VisionBlock` are added on top.

## Migration source

The following already exist in `robot/pi-runtime/src/vexy_system2/contracts/motor_telemetry.py` on the current branch. **Do not rewrite them — move and adjust imports.**

Move to `contracts/src/contracts/motor_telemetry.py`:
- `StrictModel` (BaseModel subclass with `extra="forbid", strict=True`)
- `API_BINDING`, `MOTOR_API_FIELDS`, `MOTOR_API_METHODS` constants
- `Subsystem = Literal["claw", "arm", "drivetrain"]`
- `MotorApiValues` (7 float fields: position_deg, velocity_rpm, current_amp, power_w, torque_nm, efficiency_pct, temperature_c)
- `MotorApiSample` with `model_validator(mode="after")` enforcing source_api completeness and call-name format
- `ContractSource` (raw_session_path, brain_start_ms, brain_end_ms, pi_received_ms, telemetry_sample_count)
- `vexcode_motor_source_api(device: str) -> dict[str, str]`
- `motor_sample_from_vexcode(...)` factory
- `motor_sample_from_pros(...)` factory (PROS key normalization: pos→position_deg, cur/1000→current_amp, trq→torque_nm)

**Discard** (do not migrate — violate D2):
- `BaseTaskContract`, `ScorePredicted`, `ScoreObserved`, `ScoreGap`, `ScoreContract`
- `MotorTelemetryContract` alias, `MotorTelemetryContractAdapter`
- `validate_motor_telemetry`, `validate_motor_telemetry_json` (replaced by ContractLine's own validation)

## New models to add

In `contracts/src/contracts/contract_line.py`:

```python
class AprilTagPose(StrictModel):
    x: float
    y: float
    heading: float

class VisionBlock(StrictModel):
    object_detected: bool
    object_bbox: list[int] | None = None
    apriltag_pose: AprilTagPose | None = None
    bbox_iou: float | None = None

class ContractLine(BaseModel):
    model_config = ConfigDict(extra="allow")   # forward-compatible at envelope level

    schema_version: Literal["1.0"] = "1.0"
    session_id: str
    generation: int
    round: int
    task: str                                  # free string — no enum, no per-task schema
    motor_samples: list[MotorApiSample] = Field(min_length=1)
    predicted: dict[str, float | bool | str]
    gap: dict[str, float]
    outcome: dict[str, Any] | None = None
    vision: VisionBlock | None = None
    source: ContractSource | None = None
```

In `contracts/src/contracts/__init__.py` — public API:

```python
from contracts.motor_telemetry import (
    MotorApiSample, MotorApiValues, ContractSource,
    motor_sample_from_vexcode, motor_sample_from_pros,
    vexcode_motor_source_api,
)
from contracts.contract_line import ContractLine, VisionBlock, AprilTagPose

__all__ = [
    "ContractLine", "VisionBlock", "AprilTagPose",
    "MotorApiSample", "MotorApiValues", "ContractSource",
    "motor_sample_from_vexcode", "motor_sample_from_pros",
    "vexcode_motor_source_api",
]
```

Schema export module at `contracts/src/contracts/schema.py`:

```python
import json, sys
from contracts.contract_line import ContractLine

def main() -> None:
    print(json.dumps(ContractLine.model_json_schema(), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
```

The Makefile `schema` target (already wired in package-scaffold) writes stdout to `contracts/schemas/contract_line.json`. Commit the generated file.

## Acceptance

- `from contracts import ContractLine, MotorApiSample, VisionBlock` works after `uv sync`
- `make schema` exits 0; `contracts/schemas/contract_line.json` is non-empty
- `make lint` exits 0 on all new source files
- A `ContractLine` with valid motor_samples, predicted, gap round-trips through `model_dump_json()` / `model_validate_json()`
- A `ContractLine` with no `vision` or `outcome` parses without error
- `make test` must not regress (tests from fixtures-and-gates not yet present, but existing pytest invocation must exit 0 with 0 tests collected)
