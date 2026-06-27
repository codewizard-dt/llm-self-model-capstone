from __future__ import annotations

import dataclasses
import importlib
import sys

import pytest
from contracts.control_command import (
    ARM_DEG_MAX,
    ARM_DEG_MIN,
    MAX_ARM_RPM,
    MAX_CLAW_GRIP_FORCE_N,
    MAX_LINEAR,
    MAX_OMEGA,
)
from contracts.pilot import (
    PILOT_TIMEOUT_MS_MAX,
    ApproachTargetParams,
    ApproachTargetSkillCommand,
    ArmToAngleParams,
    ArmToAngleSkillCommand,
    CenterObjectInGripperParams,
    CenterObjectInGripperSkillCommand,
    ClawCloseParams,
    ClawCloseSkillCommand,
    ClawOpenParams,
    ClawOpenSkillCommand,
    FaceTargetParams,
    FaceTargetSkillCommand,
    GoToDestinationParams,
    GoToDestinationSkillCommand,
    PilotSkillName,
    StopSkillCommand,
    StopSkillParams,
    SurveySceneParams,
    SurveySceneSkillCommand,
    VerifyDropParams,
    VerifyDropSkillCommand,
    VerifyGraspParams,
    VerifyGraspSkillCommand,
)

from pilot.skills import (
    MovementEnvelope,
    SkillDefinition,
    get_skill_definition,
    list_skill_definitions,
)


EXPECTED_MODELS = {
    PilotSkillName.STOP: (StopSkillParams, StopSkillCommand),
    PilotSkillName.SURVEY_SCENE: (SurveySceneParams, SurveySceneSkillCommand),
    PilotSkillName.FACE_TARGET: (FaceTargetParams, FaceTargetSkillCommand),
    PilotSkillName.APPROACH_TARGET: (ApproachTargetParams, ApproachTargetSkillCommand),
    PilotSkillName.CENTER_OBJECT_IN_GRIPPER: (
        CenterObjectInGripperParams,
        CenterObjectInGripperSkillCommand,
    ),
    PilotSkillName.ARM_TO_ANGLE: (ArmToAngleParams, ArmToAngleSkillCommand),
    PilotSkillName.CLAW_OPEN: (ClawOpenParams, ClawOpenSkillCommand),
    PilotSkillName.CLAW_CLOSE: (ClawCloseParams, ClawCloseSkillCommand),
    PilotSkillName.VERIFY_GRASP: (VerifyGraspParams, VerifyGraspSkillCommand),
    PilotSkillName.GO_TO_DESTINATION: (GoToDestinationParams, GoToDestinationSkillCommand),
    PilotSkillName.VERIFY_DROP: (VerifyDropParams, VerifyDropSkillCommand),
}


def test_registry_covers_exact_contract_skill_enum_once() -> None:
    definitions = list_skill_definitions()

    assert [definition.name for definition in definitions] == list(PilotSkillName)
    assert len({definition.name for definition in definitions}) == len(PilotSkillName)
    assert set(EXPECTED_MODELS) == set(PilotSkillName)
    assert all(isinstance(definition.name, PilotSkillName) for definition in definitions)


def test_list_skill_definitions_has_deterministic_enum_order() -> None:
    first = list_skill_definitions()
    second = list_skill_definitions()

    assert first == second
    assert [definition.name for definition in first] == list(PilotSkillName)
    assert tuple(get_skill_definition(name) for name in PilotSkillName) == first


def test_get_skill_definition_is_strict_for_enum_and_string_names() -> None:
    for skill_name in PilotSkillName:
        definition = get_skill_definition(skill_name)
        assert definition.name is skill_name
        assert get_skill_definition(skill_name.value) is definition

    with pytest.raises(ValueError, match="unknown pilot skill"):
        get_skill_definition("fly_to_goal")


def test_definitions_and_nested_metadata_are_immutable() -> None:
    definition = get_skill_definition(PilotSkillName.STOP)

    assert dataclasses.is_dataclass(definition)
    assert dataclasses.is_dataclass(definition.inputs[0])
    assert dataclasses.is_dataclass(definition.defaults[0])
    assert dataclasses.is_dataclass(definition.movement)
    assert isinstance(definition.inputs, tuple)
    assert isinstance(definition.defaults, tuple)
    assert isinstance(definition.preconditions, tuple)
    assert isinstance(definition.failure_reasons, tuple)
    assert isinstance(definition.recovery_hints, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        definition.max_duration_ms = 999
    with pytest.raises(dataclasses.FrozenInstanceError):
        definition.inputs[0].required = False


def test_every_definition_has_complete_static_metadata() -> None:
    for definition in list_skill_definitions():
        assert isinstance(definition, SkillDefinition)
        assert definition.inputs
        assert definition.defaults
        assert definition.preconditions
        assert definition.max_duration_ms > 0
        assert isinstance(definition.movement, MovementEnvelope)
        assert definition.command_path
        assert definition.expected_result_source
        assert definition.success_assertion.assertion_id
        assert definition.success_assertion.name
        assert definition.failure_reasons
        assert definition.recovery_hints
        assert definition.bound_references
        assert all(input_metadata.name for input_metadata in definition.inputs)
        assert all(default.name for default in definition.defaults)


def test_definitions_reuse_contract_models_and_bounds() -> None:
    seen_bound_names: set[str] = set()

    for definition in list_skill_definitions():
        params_model, command_model = EXPECTED_MODELS[definition.name]
        assert definition.params_model is params_model
        assert definition.command_model is command_model
        assert definition.max_duration_ms <= PILOT_TIMEOUT_MS_MAX
        assert 0.0 <= definition.movement.linear_mps <= MAX_LINEAR
        assert 0.0 <= definition.movement.omega_rad_s <= MAX_OMEGA
        if definition.movement.arm_deg_min is not None:
            assert definition.movement.arm_deg_min == ARM_DEG_MIN
            assert definition.movement.arm_deg_max == ARM_DEG_MAX
        if definition.movement.arm_rpm is not None:
            assert definition.movement.arm_rpm == MAX_ARM_RPM
        if definition.movement.claw_grip_force_n is not None:
            assert definition.movement.claw_grip_force_n == MAX_CLAW_GRIP_FORCE_N
        for bound in definition.bound_references:
            assert bound.source.startswith("contracts.")
            seen_bound_names.add(bound.name)

    assert {
        "PILOT_TIMEOUT_MS_MAX",
        "MAX_LINEAR",
        "MAX_OMEGA",
        "ARM_DEG_MIN",
        "ARM_DEG_MAX",
        "MAX_ARM_RPM",
        "MAX_CLAW_GRIP_FORCE_N",
    }.issubset(seen_bound_names)


def test_command_paths_and_result_sources_are_symbolic_ros_free_strings() -> None:
    forbidden_fragments = ("rclpy", "std_msgs", "sensor_msgs", "geometry_msgs", "/")

    for definition in list_skill_definitions():
        assert isinstance(definition.command_path, str)
        assert isinstance(definition.expected_result_source, str)
        assert not any(fragment in definition.command_path for fragment in forbidden_fragments)
        assert not any(
            fragment in definition.expected_result_source for fragment in forbidden_fragments
        )


def test_package_exports_registry_surface_additively() -> None:
    import pilot

    assert pilot.SkillDefinition is SkillDefinition
    assert pilot.list_skill_definitions is list_skill_definitions
    assert pilot.get_skill_definition is get_skill_definition
    assert pilot.ObservationCache is not None


def test_skills_module_imports_without_ros_packages(monkeypatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(
                ("rclpy.", "std_msgs.", "sensor_msgs.", "geometry_msgs.")
            ):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.skills", None)

    module = importlib.import_module("pilot.skills")

    assert [definition.name for definition in module.list_skill_definitions()] == list(
        PilotSkillName
    )
    assert "rclpy" not in sys.modules
