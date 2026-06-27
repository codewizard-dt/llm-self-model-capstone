from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from contracts import (
    ARM_DEG_MAX,
    MAX_CLAW_GRIP_FORCE_N,
    MAX_LINEAR,
    AssertionState,
    PilotAssertion,
    PilotDecision,
    PilotDecisionAction,
    PilotObservation,
    PilotSkillCommand,
    PilotSkillName,
    PilotTraceRecord,
)

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = CONTRACTS_ROOT / "schemas"

SKILL_COMMAND_TA = TypeAdapter(PilotSkillCommand)
TRACE_RECORD_TA = TypeAdapter(PilotTraceRecord)


def _command(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {"v": 1, "command_id": "cmd-1", "issued_ms": 100}
    base.update(overrides)
    return base


def _assertion(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": 1,
        "assertion_id": "assertion-1",
        "predicate": "object is held",
        "state": "true",
        "confidence": 0.8,
        "observed_ms": 120,
        "evidence": [
            {
                "source": "vision",
                "summary": "object remains centered between claw fingers",
                "confidence": 0.8,
                "age_ms": 40,
            }
        ],
    }
    base.update(overrides)
    return base


def _observation(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": 1,
        "observed_ms": 1000,
        "task_phase": "manipulate",
        "objective": "pick up the nearest red block",
        "robot_pose": {"x_m": 0.4, "y_m": 0.2, "heading_rad": 1.57},
        "localization": {
            "pose": {"x_m": 0.4, "y_m": 0.2, "heading_rad": 1.57},
            "confidence": 0.92,
            "age_ms": 30,
        },
        "visible_objects": [
            {
                "object_id": "block-1",
                "label": "red_block",
                "confidence": 0.88,
                "bbox": {"x_px": 120, "y_px": 80, "width_px": 42, "height_px": 38},
            }
        ],
        "visible_tags": [
            {
                "tag_id": 3,
                "family": "tag36h11",
                "confidence": 0.97,
                "pose": {"x_m": 0.5, "y_m": 0.1, "heading_rad": 0.0},
            }
        ],
        "manipulator": {"arm_deg": 35.0, "claw_state": "open"},
        "bridge": {
            "state": "ok",
            "last_heartbeat_age_ms": 45,
            "estop": False,
            "battery_pct": 74.0,
        },
        "last_command": _command(
            skill="arm_to_angle",
            params={"deg": 35.0, "vel_rpm": 90.0},
        ),
        "last_result": {
            "v": 1,
            "command_id": "cmd-0",
            "skill": "survey_scene",
            "status": "ok",
            "completed_ms": 900,
        },
        "recent_failures": [
            {
                "failed_ms": 850,
                "source": "vision",
                "summary": "first grasp check was occluded",
                "recovery_hint": "survey_scene",
            }
        ],
        "current_assertions": [_assertion()],
    }
    base.update(overrides)
    return base


def test_pilot_skill_name_is_closed() -> None:
    assert {member.value for member in PilotSkillName} == {
        "stop",
        "survey_scene",
        "face_target",
        "approach_target",
        "center_object_in_gripper",
        "arm_to_angle",
        "claw_open",
        "claw_close",
        "verify_grasp",
        "go_to_destination",
        "verify_drop",
    }
    with pytest.raises(ValueError):
        PilotSkillName("drive")


@pytest.mark.parametrize(
    "payload,expected_skill",
    [
        (_command(skill="stop", params={"reason": "operator"}), "stop"),
        (_command(skill="survey_scene", params={"yaw_span_deg": 180.0}), "survey_scene"),
        (_command(skill="face_target", params={"target_id": "block-1"}), "face_target"),
        (
            _command(
                skill="approach_target",
                params={"target_id": "block-1", "standoff_m": 0.2, "max_speed_mps": 0.2},
            ),
            "approach_target",
        ),
        (
            _command(
                skill="center_object_in_gripper",
                params={"object_id": "block-1", "image_tolerance_px": 12},
            ),
            "center_object_in_gripper",
        ),
        (_command(skill="arm_to_angle", params={"deg": ARM_DEG_MAX}), "arm_to_angle"),
        (_command(skill="claw_open", params={"opening_pct": 100.0}), "claw_open"),
        (
            _command(skill="claw_close", params={"grip_force_n": MAX_CLAW_GRIP_FORCE_N}),
            "claw_close",
        ),
        (_command(skill="verify_grasp", params={"min_confidence": 0.7}), "verify_grasp"),
        (
            _command(
                skill="go_to_destination",
                params={"destination_id": "drop-zone", "max_speed_mps": MAX_LINEAR},
            ),
            "go_to_destination",
        ),
        (_command(skill="verify_drop", params={"destination_id": "drop-zone"}), "verify_drop"),
    ],
)
def test_each_pilot_skill_command_variant_validates(
    payload: dict[str, object], expected_skill: str
) -> None:
    parsed = SKILL_COMMAND_TA.validate_python(payload)
    assert parsed.skill == expected_skill


def test_pilot_skill_command_rejects_unknown_skill_and_bad_bounds() -> None:
    with pytest.raises(ValidationError):
        SKILL_COMMAND_TA.validate_python(_command(skill="drive", params={}))

    with pytest.raises(ValidationError):
        SKILL_COMMAND_TA.validate_python(_command(skill="arm_to_angle", params={"deg": 91.0}))

    with pytest.raises(ValidationError):
        SKILL_COMMAND_TA.validate_python(
            _command(skill="approach_target", params={"target_id": "block-1", "max_speed_mps": 9.0})
        )

    with pytest.raises(ValidationError):
        SKILL_COMMAND_TA.validate_python(
            _command(skill="go_to_destination", params={"max_speed_mps": 0.1})
        )


def test_pilot_observation_snapshot_contains_required_boundary_fields() -> None:
    observation = PilotObservation.model_validate(_observation())

    assert observation.task_phase == "manipulate"
    assert observation.objective == "pick up the nearest red block"
    assert observation.robot_pose is not None
    assert observation.localization.confidence == 0.92
    assert observation.localization.age_ms == 30
    assert observation.visible_objects[0].object_id == "block-1"
    assert observation.visible_tags[0].tag_id == 3
    assert observation.manipulator.claw_state == "open"
    assert observation.bridge.state == "ok"
    assert observation.last_command is not None
    assert observation.last_result is not None
    assert observation.recent_failures[0].source == "vision"
    assert observation.current_assertions[0].state is AssertionState.TRUE

    with pytest.raises(ValidationError):
        PilotObservation.model_validate({**_observation(), "ros_topic": "/camera/image"})


def test_pilot_assertion_state_evidence_and_time_metadata() -> None:
    assertion = PilotAssertion.model_validate(
        _assertion(state="unknown", age_ms=50, observed_ms=None)
    )

    assert assertion.state is AssertionState.UNKNOWN
    assert assertion.confidence == 0.8
    assert assertion.evidence[0].source == "vision"
    assert assertion.age_ms == 50
    assert assertion.recovery_hint is None

    with pytest.raises(ValidationError):
        PilotAssertion.model_validate(_assertion(state="maybe"))

    with pytest.raises(ValidationError):
        PilotAssertion.model_validate(_assertion(observed_ms=None, age_ms=None))

    with pytest.raises(ValidationError):
        PilotAssertion.model_validate(_assertion(confidence=1.5))


def test_pilot_decision_actions_are_bounded() -> None:
    decision = PilotDecision.model_validate(
        {
            "v": 1,
            "decision_id": "decision-1",
            "decided_ms": 1100,
            "action": "continue",
            "rationale": "target remains visible and bridge is healthy",
            "confidence": 0.76,
            "command": _command(skill="face_target", params={"target_id": "block-1"}),
        }
    )

    assert decision.action is PilotDecisionAction.CONTINUE
    assert decision.command is not None

    with pytest.raises(ValidationError):
        PilotDecision.model_validate(
            {
                "v": 1,
                "decision_id": "decision-2",
                "decided_ms": 1101,
                "action": "wander",
                "rationale": "not a valid bounded pilot decision",
                "confidence": 0.5,
            }
        )


@pytest.mark.parametrize(
    "payload,expected_event",
    [
        (
            {
                "v": 1,
                "session_id": "pilot-run-1",
                "seq": 1,
                "monotonic_ms": 1000,
                "event": "observation",
                "observation": _observation(),
            },
            "observation",
        ),
        (
            {
                "v": 1,
                "session_id": "pilot-run-1",
                "seq": 2,
                "monotonic_ms": 1010,
                "event": "decision",
                "decision": {
                    "v": 1,
                    "decision_id": "decision-1",
                    "decided_ms": 1010,
                    "action": "retry",
                    "rationale": "the first grasp assertion is unknown",
                    "confidence": 0.62,
                    "retry_of_command_id": "cmd-1",
                },
            },
            "decision",
        ),
        (
            {
                "v": 1,
                "session_id": "pilot-run-1",
                "seq": 3,
                "monotonic_ms": 1020,
                "event": "command",
                "command": _command(skill="claw_close", params={"grip_force_n": 10.0}),
            },
            "command",
        ),
        (
            {
                "v": 1,
                "session_id": "pilot-run-1",
                "seq": 4,
                "monotonic_ms": 1030,
                "event": "result",
                "result": {
                    "v": 1,
                    "command_id": "cmd-1",
                    "skill": "claw_close",
                    "status": "ok",
                },
            },
            "result",
        ),
        (
            {
                "v": 1,
                "session_id": "pilot-run-1",
                "seq": 5,
                "monotonic_ms": 1040,
                "event": "assertion",
                "assertion": _assertion(),
            },
            "assertion",
        ),
        (
            {
                "v": 1,
                "session_id": "pilot-run-1",
                "seq": 6,
                "monotonic_ms": 1050,
                "event": "stop",
                "reason": "success",
                "message": "object delivered",
            },
            "stop",
        ),
    ],
)
def test_pilot_trace_record_union_validates_each_event(
    payload: dict[str, object], expected_event: str
) -> None:
    record = TRACE_RECORD_TA.validate_python(payload)
    assert record.event == expected_event


def test_pilot_trace_record_rejects_invalid_discriminator() -> None:
    with pytest.raises(ValidationError):
        TRACE_RECORD_TA.validate_python(
            {
                "v": 1,
                "session_id": "pilot-run-1",
                "seq": 1,
                "monotonic_ms": 1000,
                "event": "telemetry",
            }
        )


def test_pilot_schema_files_are_present_and_non_empty() -> None:
    for filename in [
        "pilot_skill_command.json",
        "pilot_observation.json",
        "pilot_assertion.json",
        "pilot_decision.json",
        "pilot_trace_record.json",
    ]:
        schema_path = SCHEMAS_DIR / filename
        assert schema_path.exists()
        assert schema_path.stat().st_size > 0
