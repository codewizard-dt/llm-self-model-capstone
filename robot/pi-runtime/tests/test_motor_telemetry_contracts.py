import json
import unittest

from pydantic import ValidationError

from vexy_system2.contracts.motor_telemetry import (
    MOTOR_API_FIELDS,
    ContractSource,
    MotorApiSample,
    MotorApiValues,
    ScoreContract,
    ScoreGap,
    ScoreObserved,
    ScorePredicted,
    motor_sample_from_pros,
    motor_sample_from_vexcode,
    motor_telemetry_json_schema,
    validate_motor_telemetry,
    validate_motor_telemetry_json,
    vexcode_motor_source_api,
)


def full_values(**overrides):
    values = {
        "position_deg": 120.0,
        "velocity_rpm": 14.0,
        "current_amp": 1.8,
        "power_w": 21.6,
        "torque_nm": 0.9,
        "efficiency_pct": 72.0,
        "temperature_c": 34.0,
    }
    values.update(overrides)
    return values


def source():
    return ContractSource(
        raw_session_path="session_20260623_120000.raw.jsonl",
        brain_start_ms=1000,
        brain_end_ms=1300,
        pi_received_ms=2000,
        telemetry_sample_count=3,
    )


def motor(device="claw_motor", subsystem="claw", **overrides):
    return motor_sample_from_vexcode(
        device=device,
        subsystem=subsystem,
        sample_ms=1100,
        values=full_values(**overrides),
    )


class MotorTelemetryContractTests(unittest.TestCase):
    def test_motor_sample_requires_all_vexcode_observations(self):
        values = full_values()
        del values["power_w"]

        with self.assertRaises(ValidationError):
            MotorApiSample(
                device="claw_motor",
                subsystem="claw",
                sample_ms=1,
                values=MotorApiValues(**values),
                source_api=vexcode_motor_source_api("claw_motor"),
            )

    def test_motor_sample_rejects_missing_source_api_mapping(self):
        source_api = vexcode_motor_source_api("claw_motor")
        del source_api["efficiency_pct"]

        with self.assertRaises(ValidationError):
            MotorApiSample(
                device="claw_motor",
                subsystem="claw",
                sample_ms=1,
                values=MotorApiValues(**full_values()),
                source_api=source_api,
            )

    def test_motor_sample_rejects_unknown_source_api_call(self):
        source_api = vexcode_motor_source_api("claw_motor")
        source_api["torque_nm"] = "claw_motor.get_torque()"

        with self.assertRaises(ValidationError):
            MotorApiSample(
                device="claw_motor",
                subsystem="claw",
                sample_ms=1,
                values=MotorApiValues(**full_values()),
                source_api=source_api,
            )

    def test_score_contract_validates_close_range(self):
        contract = ScoreContract(
            run_id="run-1",
            episode_id="score-1",
            created_ms=2000,
            task="score",
            predicted=ScorePredicted(distance_from_bin_m=0.0, success=True),
            observed=ScoreObserved(ball_in_bin=True, distance_from_bin_m=0.0, score_value=0.0),
            gap=ScoreGap(distance_error_m=0.0, success_correct=True),
            motor_samples=[motor()],
            source=source(),
        )

        validated = validate_motor_telemetry_json(contract.model_dump_json())
        self.assertEqual(validated.task, "score")

    def test_score_contract_validates_distant_shot(self):
        contract = ScoreContract(
            run_id="run-1",
            episode_id="score-2",
            created_ms=2000,
            task="score",
            predicted=ScorePredicted(distance_from_bin_m=1.5, success=True),
            observed=ScoreObserved(ball_in_bin=True, distance_from_bin_m=1.3, score_value=1.3),
            gap=ScoreGap(distance_error_m=-0.2, success_correct=True),
            motor_samples=[motor("flywheel_motor", "arm", velocity_rpm=600.0)],
            source=source(),
        )

        self.assertEqual(validate_motor_telemetry(contract.model_dump()).task, "score")
        self.assertEqual(validate_motor_telemetry(contract.model_dump()).observed.score_value, 1.3)

    def test_score_contract_zero_score_value_when_ball_not_in_bin(self):
        contract = ScoreContract(
            run_id="run-1",
            episode_id="score-3",
            created_ms=2000,
            task="score",
            predicted=ScorePredicted(distance_from_bin_m=1.0, success=True),
            observed=ScoreObserved(ball_in_bin=False, distance_from_bin_m=1.0, score_value=0.0),
            gap=ScoreGap(distance_error_m=0.0, success_correct=False),
            motor_samples=[motor()],
            source=source(),
        )

        validated = validate_motor_telemetry(contract.model_dump())
        self.assertEqual(validated.observed.score_value, 0.0)
        self.assertFalse(validated.observed.ball_in_bin)

    def test_schema_export_includes_score_variant(self):
        schema = motor_telemetry_json_schema()
        dumped = json.dumps(schema)

        self.assertIn("score", dumped)
        self.assertIn("MotorApiSample", dumped)


if __name__ == "__main__":
    unittest.main()

