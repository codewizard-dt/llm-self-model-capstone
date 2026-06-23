---
topic: how to update the contracts for the TASK — motor contract stays the same
slug: task-contract-score-redesign
researched: 2026-06-23
---

# Primary Sources — Task Contract Redesign

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/pi-runtime/src/vexy_system2/contracts/motor_telemetry.py` | 2026-06-23 | Full class hierarchy: BaseTaskContract, GrabContract/PullContract/ThrowContract structure, MotorTelemetryContract union with discriminator="task", Subsystem literal, MotorApiValues fields |
| S2 | codebase | `robot/pi-runtime/tests/test_motor_telemetry_contracts.py` | 2026-06-23 | All test method names; which tests target motor-layer vs task-layer; test_schema_export_includes_three_task_variants assertion pattern |
| S3 | codebase | `robot/pi-runtime/src/vexy_system2/bridge.py`, `protocol.py`, `dashboard.py`, `planner_demo.py`, `robot/v5-brain/pros_bridge/src/main.cpp` | 2026-06-23 | Zero references to "grab", "pull", "throw", or task contract names in these files — protocol.py validates cmd in {"stop","drive","turn","set_goal"}, independent of task names |
| S4 | codebase | `wiki/knowledge/concepts/task-telemetry-contract.md` | 2026-06-23 | Wiki page documents grab/pull/throw contracts in detail; aliases include "Grab/Pull/Throw Contract"; will become stale after redesign |

## Excerpts

### S1 — motor_telemetry.py: MotorTelemetryContract union
```python
MotorTelemetryContract = Annotated[
    Union[GrabContract, PullContract, ThrowContract],
    Field(discriminator="task"),
]
MotorTelemetryContractAdapter = TypeAdapter(MotorTelemetryContract)
```

### S1 — motor_telemetry.py: BaseTaskContract (unchanged layer)
```python
class BaseTaskContract(StrictModel):
    schema_version: Literal["v1"] = "v1"
    run_id: str
    episode_id: str
    created_ms: int = Field(ge=0)
    motor_samples: list[MotorApiSample] = Field(min_length=1)
    source: ContractSource
```

### S1 — motor_telemetry.py: Subsystem
```python
Subsystem = Literal["claw", "arm", "drivetrain"]
```

### S3 — protocol.py: validate_outbound cmd check (independent of task names)
```python
if cmd not in {"stop", "drive", "turn", "set_goal"}:
    raise ProtocolError(f"unsupported command: {cmd}")
```
