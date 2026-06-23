# Slice: fixtures-and-gates

| Field | Value |
|---|---|
| Feature | telemetry-contract (F1) |
| Stack | contracts |
| Depends on | pydantic-models |

## What this slice delivers

JSONL fixtures demonstrating all four task types, a full pytest suite (migrating and extending the branch tests), and the `make validate` gate. This is the acceptance layer that proves the models are correct and reviewers can reproduce it.

## Fixtures

Create `contracts/fixtures/session_example.jsonl` — one JSON object per line, no trailing comma, newline-terminated. Four lines:

**Line 1 — grab (with vision)**
```json
{"schema_version":"1.0","session_id":"session_20260624_141200","generation":0,"round":1,"task":"grab","motor_samples":[{"device":"claw_motor","subsystem":"claw","api_binding":"vexcode_python","sample_ms":1100,"values":{"position_deg":120.0,"velocity_rpm":14.0,"current_amp":1.8,"power_w":21.6,"torque_nm":0.9,"efficiency_pct":72.0,"temperature_c":34.0},"source_api":{"position_deg":"claw_motor.position(DEGREES)","velocity_rpm":"claw_motor.velocity(RPM)","current_amp":"claw_motor.current(AMP)","power_w":"claw_motor.power(WATT)","torque_nm":"claw_motor.torque(NM)","efficiency_pct":"claw_motor.efficiency(PERCENT)","temperature_c":"claw_motor.temperature(CELSIUS)"}}],"predicted":{"grip_force_N":14.7,"duration_s":1.2,"success":true},"gap":{"force_error_N":-3.4,"duration_error_s":0.2},"outcome":{"success":true},"vision":{"object_detected":true,"object_bbox":[310,220,64,58],"apriltag_pose":{"x":487,"y":-12,"heading":2},"bbox_iou":0.71}}
```

**Line 2 — pull (motor-only, no vision)**
```json
{"schema_version":"1.0","session_id":"session_20260624_141200","generation":0,"round":2,"task":"pull","motor_samples":[{"device":"left_drive","subsystem":"drivetrain","api_binding":"vexcode_python","sample_ms":2200,"values":{"position_deg":540.0,"velocity_rpm":180.0,"current_amp":2.1,"power_w":37.8,"torque_nm":1.1,"efficiency_pct":68.0,"temperature_c":38.0},"source_api":{"position_deg":"left_drive.position(DEGREES)","velocity_rpm":"left_drive.velocity(RPM)","current_amp":"left_drive.current(AMP)","power_w":"left_drive.power(WATT)","torque_nm":"left_drive.torque(NM)","efficiency_pct":"left_drive.efficiency(PERCENT)","temperature_c":"left_drive.temperature(CELSIUS)"}}],"predicted":{"load_mass_kg":2.0,"distance_m":0.5,"success":true},"gap":{"force_error_N":6.6,"efficiency_loss":0.23},"outcome":{"success":true}}
```

**Line 3 — throw (with vision)**
```json
{"schema_version":"1.0","session_id":"session_20260624_141200","generation":0,"round":3,"task":"throw","motor_samples":[{"device":"arm_motor","subsystem":"arm","api_binding":"vexcode_python","sample_ms":3100,"values":{"position_deg":200.0,"velocity_rpm":27.1,"current_amp":1.5,"power_w":18.0,"torque_nm":0.7,"efficiency_pct":65.0,"temperature_c":36.0},"source_api":{"position_deg":"arm_motor.position(DEGREES)","velocity_rpm":"arm_motor.velocity(RPM)","current_amp":"arm_motor.current(AMP)","power_w":"arm_motor.power(WATT)","torque_nm":"arm_motor.torque(NM)","efficiency_pct":"arm_motor.efficiency(PERCENT)","temperature_c":"arm_motor.temperature(CELSIUS)"}}],"predicted":{"range_m":0.4,"object_mass_g":50},"gap":{"range_error_m":-0.15,"velocity_loss_ratio":0.16},"outcome":{"observed_range_m":0.25},"vision":{"object_detected":true,"object_bbox":[400,180,30,28],"apriltag_pose":null,"bbox_iou":0.61}}
```

**Line 4 — score (with vision, outcome.ball_in_bin)**
```json
{"schema_version":"1.0","session_id":"session_20260624_141200","generation":0,"round":4,"task":"score","motor_samples":[{"device":"claw_motor","subsystem":"claw","api_binding":"vexcode_python","sample_ms":4100,"values":{"position_deg":95.0,"velocity_rpm":8.0,"current_amp":1.6,"power_w":16.0,"torque_nm":0.8,"efficiency_pct":70.0,"temperature_c":35.0},"source_api":{"position_deg":"claw_motor.position(DEGREES)","velocity_rpm":"claw_motor.velocity(RPM)","current_amp":"claw_motor.current(AMP)","power_w":"claw_motor.power(WATT)","torque_nm":"claw_motor.torque(NM)","efficiency_pct":"claw_motor.efficiency(PERCENT)","temperature_c":"claw_motor.temperature(CELSIUS)"}}],"predicted":{"distance_from_bin_m":0.3,"success":true},"gap":{"distance_error_m":-0.05},"outcome":{"ball_in_bin":true,"score_value":1.0,"success":true},"vision":{"object_detected":true,"object_bbox":[290,210,55,52],"apriltag_pose":{"x":320,"y":5,"heading":1},"bbox_iou":0.68}}
```

## Validate script

Create `contracts/src/contracts/validate.py`:

```python
"""make validate — parse every line in contracts/fixtures/*.jsonl against ContractLine."""
import json, sys
from pathlib import Path
from contracts import ContractLine

def main() -> None:
    fixture_dir = Path(__file__).parents[3] / "fixtures"
    errors = []
    for path in sorted(fixture_dir.glob("*.jsonl")):
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                ContractLine.model_validate_json(raw)
            except Exception as exc:
                errors.append(f"{path.name}:{lineno}: {exc}")
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)
    print(f"OK — all fixtures valid")

if __name__ == "__main__":
    main()
```

## Tests

Create `contracts/tests/test_contract_line.py` — new tests for the envelope:

- Round-trip all 4 fixture lines through `ContractLine.model_validate_json(model.model_dump_json())`
- Motor-only line (no `vision`) parses without error
- Line with `outcome=None` parses without error
- Missing `session_id` raises `ValidationError`
- `task` accepts any string — `"custom_task"` does not raise

Create `contracts/tests/test_motor_telemetry.py` — migrate from branch:

Migrate these three tests verbatim from `robot/pi-runtime/tests/test_motor_telemetry_contracts.py`, updating imports to `from contracts import MotorApiSample, MotorApiValues` and helpers:

- `test_motor_sample_requires_all_vexcode_observations`
- `test_motor_sample_rejects_missing_source_api_mapping`
- `test_motor_sample_rejects_unknown_source_api_call`

Add:

- `test_motor_sample_from_pros_normalises_keys` — verify `cur` → `current_amp` division by 1000, `pos` → `position_deg`, `trq` → `torque_nm`
- `test_schema_export_contains_contract_line` — `json.dumps(ContractLine.model_json_schema())` contains `"motor_samples"` and `"session_id"`

## Acceptance

- `cd contracts && make validate` exits 0 against `fixtures/session_example.jsonl`
- `cd contracts && make test` exits 0; all migrated + new tests pass
- `cd contracts && make lint` exits 0 across `src/` and `tests/`
- Root `make validate` / `make test` / `make lint` all exit 0
- The `score` task fixture parses correctly with `outcome.ball_in_bin=true` in the flexible dict — no schema change required
- The pull fixture (no `vision`) parses correctly
