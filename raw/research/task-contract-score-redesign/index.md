---
topic: how to update the contracts for the TASK — motor contract stays the same
slug: task-contract-score-redesign
researched: 2026-06-23
sources: [./sources.md]
---

# Research: Task Contract Redesign — Single "Score" Task

> Replace the three-task contract family (grab / pull / throw) with a single **`ScoreContract`** whose fitness signal is distance-from-bin at the moment the ball enters the bin. The motor contract layer (`MotorApiValues`, `MotorApiSample`, `ContractSource`, `BaseTaskContract`) is unchanged. Two code files change: `motor_telemetry.py` (contract definitions) and `test_motor_telemetry_contracts.py` (tests). One wiki page needs updating.

---

## Research Questions

1. What is the full current contract structure (classes, fields, discriminated union)?
2. Which layers are explicitly off-limits ("motor contract stays the same")?
3. What fields does the new single-task contract need to express the distance-from-bin fitness signal?
4. What changes are required in the test suite?
5. Are there any other call-sites (bridge, protocol, dashboard, V5 brain) that reference the old task names?

---

## Current State (Codebase)

File: `robot/pi-runtime/src/vexy_system2/contracts/motor_telemetry.py`

**Unchanged layer (motor contract)** — all of these stay as-is [S1]:
| Symbol | Role |
|---|---|
| `Subsystem = Literal["claw", "arm", "drivetrain"]` | Motor subsystem tags |
| `MotorApiValues` | 7 motor telemetry fields (position_deg, velocity_rpm, current_amp, power_w, torque_nm, efficiency_pct, temperature_c) |
| `MotorApiSample` | Per-motor sample: device, subsystem, values, source_api; enforces full VEXcode V5 API surface |
| `ContractSource` | Session metadata: raw_session_path, brain timestamps, telemetry_sample_count |
| `BaseTaskContract` | Common envelope: schema_version, run_id, episode_id, created_ms, motor_samples, source |

**Task-specific layer (to be replaced)** — these 12 classes + union will be removed [S1]:
| Symbol | Status |
|---|---|
| `GrabPredicted`, `GrabObserved`, `GrabGap`, `GrabContract` | DELETE |
| `PullPredicted`, `PullObserved`, `PullGap`, `PullContract` | DELETE |
| `ThrowPredicted`, `ThrowObserved`, `ThrowGap`, `ThrowContract` | DELETE |
| `MotorTelemetryContract = Union[GrabContract, PullContract, ThrowContract]` | REPLACE |

Test file: `robot/pi-runtime/tests/test_motor_telemetry_contracts.py`

Current test methods that test task contracts [S2]:
- `test_grab_contract_validates`
- `test_pull_contract_requires_drivetrain_motor_samples`
- `test_pull_contract_accepts_left_and_right_drivetrain_samples`
- `test_throw_contract_validates_arm_sample`
- `test_schema_export_includes_three_task_variants`

Motor-level tests (keep unchanged):
- `test_motor_sample_requires_all_vexcode_observations`
- `test_motor_sample_rejects_missing_source_api_mapping`
- `test_motor_sample_rejects_unknown_source_api_call`
- `test_pros_adapter_maps_to_canonical_vexcode_sample`

**Other call-sites** — no references to `grab`, `pull`, or `throw` exist in `bridge.py`, `protocol.py`, `dashboard.py`, `planner_demo.py`, or the V5 brain C++ files [S3]. The protocol layer validates `cmd` values (`stop`, `drive`, `turn`, `set_goal`), not task names — these are independent dimensions.

---

## Key Findings

- **Motor contract is a clean layer boundary** [S1]: `BaseTaskContract` inherits from `StrictModel` and the task-specific classes only add `task`, `predicted`, `observed`, `gap` on top. Replacing those four fields in a new class is self-contained.
- **Discriminated union uses `task` as discriminator** [S1]: `MotorTelemetryContract = Annotated[Union[...], Field(discriminator="task")]`. With one variant this simplifies to `Annotated[ScoreContract, Field(discriminator="task")]`.
- **No bridge/protocol coupling** [S3]: Task names only appear inside the contracts package and its tests — zero refactoring needed in `bridge.py`, `protocol.py`, `dashboard.py`, or the V5 C++ code.
- **Fitness semantics**: the new task's core measurement is `distance_from_bin_m` at the moment of scoring. Gen0 (claw) will always score from ≈0 m; Gen1+ (scoop/flywheel) scores from > 0 m. Score value = distance if `ball_in_bin` is true, else 0. *(inference — no primary source)*
- **Wiki concept page references grab/pull/throw** [S4] and will become stale; it should be updated after the code change.

---

## Constraints

1. `MotorApiValues`, `MotorApiSample`, `ContractSource`, `BaseTaskContract` — **do not modify**.
2. `Subsystem` literal — keep as-is; future flywheel/scoop additions can be appended when the mechanism is built.
3. `StrictModel` base — all new Pydantic models must inherit it (maintains `model_config = ConfigDict(extra="forbid")`).
4. Pydantic discriminated union with `task` literal discriminator — the pattern must be preserved for `validate_motor_telemetry_json` and `validate_motor_telemetry` callers.
5. Test file imports from `vexy_system2.contracts.motor_telemetry` — imports must be updated to match new exports.

---

## Recommendation

### New classes to add to `motor_telemetry.py`

```python
class ScorePredicted(StrictModel):
    distance_from_bin_m: float = Field(ge=0.0)   # planned firing distance
    success: bool                                  # model's prediction of ball-in-bin

class ScoreObserved(StrictModel):
    ball_in_bin: bool                              # did the ball enter the bin?
    distance_from_bin_m: float = Field(ge=0.0)   # actual robot distance at release
    score_value: float = Field(ge=0.0)            # distance if ball_in_bin else 0.0

class ScoreGap(StrictModel):
    distance_error_m: float                        # observed − predicted distance
    success_correct: bool                          # True if prediction matched outcome

class ScoreContract(BaseTaskContract):
    task: Literal["score"]
    predicted: ScorePredicted
    observed: ScoreObserved
    gap: ScoreGap
```

### Updated discriminated union (bottom of file)

```python
MotorTelemetryContract = Annotated[
    ScoreContract,
    Field(discriminator="task"),
]
MotorTelemetryContractAdapter = TypeAdapter(MotorTelemetryContract)
```

> Note: `Union[X]` with a single type is valid Pydantic; the discriminator still works and keeps the JSON schema structure consistent for future additional tasks.

### Test replacements in `test_motor_telemetry_contracts.py`

| Old test | New test | Notes |
|---|---|---|
| `test_grab_contract_validates` | `test_score_contract_validates_close_range` | Gen0: distance=0, ball_in_bin=True, score_value=0.0 |
| `test_pull_contract_requires_drivetrain_motor_samples` | DELETE | No pull task |
| `test_pull_contract_accepts_left_and_right_drivetrain_samples` | DELETE | No pull task |
| `test_throw_contract_validates_arm_sample` | `test_score_contract_validates_distant_shot` | Gen1: distance=1.5, ball_in_bin=True, score_value=1.5 |
| `test_schema_export_includes_three_task_variants` | `test_schema_export_includes_score_variant` | Check `"score"` in schema, not `"grab"/"pull"/"throw"` |

Add one new test:
- `test_score_contract_zero_score_value_when_ball_not_in_bin` — ball_in_bin=False, score_value must equal 0.0

### Wiki

Update `wiki/knowledge/concepts/task-telemetry-contract.md`:
- Replace grab/pull/throw JSON blocks with a score contract example block
- Update the aliases frontmatter (remove `Grab/Pull/Throw Contract`, add `Score Contract`)
- Update the `updated:` date

---

## Implementation Outline

1. **Edit `motor_telemetry.py`**:
   - Remove the 12 grab/pull/throw classes
   - Add `ScorePredicted`, `ScoreObserved`, `ScoreGap`, `ScoreContract`
   - Replace the `MotorTelemetryContract` union

2. **Edit `test_motor_telemetry_contracts.py`**:
   - Remove imports of `GrabContract`, `GrabPredicted`, `GrabObserved`, `GrabGap`, `PullContract`, `PullPredicted`, `PullObserved`, `PullGap`, `ThrowContract`, `ThrowPredicted`, `ThrowObserved`, `ThrowGap`
   - Add imports of `ScoreContract`, `ScorePredicted`, `ScoreObserved`, `ScoreGap`
   - Replace/delete the five task-specific test methods with three new ones

3. **Update `wiki/knowledge/concepts/task-telemetry-contract.md`**

4. **Verify**: run `uv run pytest robot/pi-runtime/tests/` — all tests green.

---

## Next Steps

- To create a task: `/task-add Refactor motor_telemetry.py — replace grab/pull/throw contracts with single ScoreContract`
- After implementation: `/wiki-ingest raw/research/task-contract-score-redesign/index.md` to update the knowledge base
