import json
import unittest

from pydantic import ValidationError

from vexy_system2.contracts.motor_telemetry import (
    MOTOR_API_FIELDS,
    ContractSource,
    GrabContract,
    GrabGap,
    GrabObserved,
    GrabPredicted,
    MotorApiSample,
    MotorApiValues,
    PullContract,
    PullGap,
    PullObserved,
    PullPredicted,
    ThrowContract,
    ThrowGap,
    ThrowObserved,
    ThrowPredicted,
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

    def test_grab_contract_validates(self):
        contract = GrabContract(
            run_id="run-1",
            episode_id="grab-1",
            created_ms=2000,
            task="grab",
            predicted=GrabPredicted(object_width_mm=40.0, grip_force_n=14.7, success=True),
            observed=GrabObserved(
                gripped=True,
                claw_position_delta_deg=120.0,
                claw_current_amp=1.8,
                claw_torque_nm=0.9,
            ),
            gap=GrabGap(force_error_n=-0.9, width_error_mm=5.0),
            motor_samples=[motor()],
            source=source(),
        )

        validated = validate_motor_telemetry_json(contract.model_dump_json())
        self.assertEqual(validated.task, "grab")

    def test_pull_contract_requires_drivetrain_motor_samples(self):
        with self.assertRaises(ValidationError):
            PullContract(
                run_id="run-1",
                episode_id="pull-1",
                created_ms=2000,
                task="pull",
                predicted=PullPredicted(load_mass_kg=2.0, distance_m=0.5, success=True),
                observed=PullObserved(
                    pull_force_n=22.4,
                    velocity_ratio=0.77,
                    distance_m=0.5,
                    energy_j=11.2,
                ),
                gap=PullGap(force_error_n=6.6, distance_error_m=0.0, efficiency_loss=0.23),
                motor_samples=[motor()],
                source=source(),
            )

    def test_pull_contract_accepts_left_and_right_drivetrain_samples(self):
        contract = PullContract(
            run_id="run-1",
            episode_id="pull-1",
            created_ms=2000,
            task="pull",
            predicted=PullPredicted(load_mass_kg=2.0, distance_m=0.5, success=True),
            observed=PullObserved(
                pull_force_n=22.4,
                velocity_ratio=0.77,
                distance_m=0.5,
                energy_j=11.2,
            ),
            gap=PullGap(force_error_n=6.6, distance_error_m=0.0, efficiency_loss=0.23),
            motor_samples=[
                motor("left_drive_motor", "drivetrain"),
                motor("right_drive_motor", "drivetrain"),
            ],
            source=source(),
        )

        validated = validate_motor_telemetry(contract.model_dump())
        self.assertEqual(validated.task, "pull")
        self.assertEqual(len(validated.motor_samples), 2)

    def test_throw_contract_validates_arm_sample(self):
        contract = ThrowContract(
            run_id="run-1",
            episode_id="throw-1",
            created_ms=2000,
            task="throw",
            predicted=ThrowPredicted(range_m=0.4, object_mass_g=50.0),
            observed=ThrowObserved(
                release_velocity_ms=0.38,
                observed_range_m=0.25,
                arm_velocity_at_release_rpm=27.1,
            ),
            gap=ThrowGap(range_error_m=-0.15, velocity_loss_ratio=0.16),
            motor_samples=[motor("arm_motor", "arm", velocity_rpm=27.1)],
            source=source(),
        )

        self.assertEqual(validate_motor_telemetry(contract.model_dump()).task, "throw")

    def test_pros_adapter_maps_to_canonical_vexcode_sample(self):
        sample = motor_sample_from_pros(
            device="arm_motor",
            subsystem="arm",
            sample_ms=1200,
            sample={
                "pos": 90.0,
                "vel": 27.1,
                "cur": 1800.0,
                "power_w": 20.0,
                "trq": 0.8,
                "efficiency_pct": 70.0,
                "temp_c": 36.0,
            },
        )

        self.assertEqual(sample.api_binding, "vexcode_python")
        self.assertEqual(sample.values.current_amp, 1.8)
        self.assertEqual(set(sample.source_api), set(MOTOR_API_FIELDS))
        self.assertEqual(sample.source_api["velocity_rpm"], "arm_motor.velocity(RPM)")

    def test_schema_export_includes_three_task_variants(self):
        schema = motor_telemetry_json_schema()
        dumped = json.dumps(schema)

        self.assertIn("grab", dumped)
        self.assertIn("pull", dumped)
        self.assertIn("throw", dumped)
        self.assertIn("MotorApiSample", dumped)


if __name__ == "__main__":
    unittest.main()

