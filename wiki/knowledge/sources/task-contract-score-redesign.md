---
id: task-contract-score-redesign
title: Research: Task Contract Redesign — Single "Score" Task
updated: 2026-06-23
sources:
  - ../../raw/research/task-contract-score-redesign/index.md
tags: [task-telemetry-contract, contracts, pydantic, fitness, scoring, vex-v5]
---

# Research: Task Contract Redesign — Single "Score" Task

The three-task contract family (grab / pull / throw) is replaced with a single **`ScoreContract`** whose fitness signal is **distance from the bin at the moment the ball enters**. The motor contract layer (`MotorApiValues`, `MotorApiSample`, `ContractSource`, `BaseTaskContract`) is completely unchanged.

## Why

The old tasks modelled three *sub-capabilities* of the robot independently. The new design collapses them into the single *outcome* that matters: did the ball go in, and from how far? This lets Gen-0 (claw) score from 0 m while incentivising Gen-1+ (scoop / flywheel) to score from further away — the robot has one task, but richer designs do it better. relates_to::[[task-telemetry-contract]] relates_to::[[llm-authored-self-model]]

## What Changes (Code)

Only two files change; the protocol, bridge, dashboard, and V5 C++ bridge have **zero coupling** to task names.

**`motor_telemetry.py`** — delete 12 grab/pull/throw classes, add 4:

```python
class ScorePredicted(StrictModel):
    distance_from_bin_m: float = Field(ge=0.0)
    success: bool

class ScoreObserved(StrictModel):
    ball_in_bin: bool
    distance_from_bin_m: float = Field(ge=0.0)
    score_value: float = Field(ge=0.0)   # distance if ball_in_bin else 0.0

class ScoreGap(StrictModel):
    distance_error_m: float              # observed − predicted distance
    success_correct: bool

class ScoreContract(BaseTaskContract):
    task: Literal["score"]
    predicted: ScorePredicted
    observed: ScoreObserved
    gap: ScoreGap
```

Union simplifies to:
```python
MotorTelemetryContract = Annotated[ScoreContract, Field(discriminator="task")]
```

**`test_motor_telemetry_contracts.py`** — 5 task-level tests replaced/deleted/added; 4 motor-level tests untouched.

## Fitness Semantics

`score_value = distance_from_bin_m if ball_in_bin else 0.0` — Gen-0 always scores near 0 m; Gen-1+ earns positive score by throwing from a distance. The gap block (`distance_error_m`, `success_correct`) feeds the LLM self-model revision loop the same way the old gap blocks did.

derived_from::[[raw/research/task-contract-score-redesign/index.md]]
updates::[[task-telemetry-contract]]
