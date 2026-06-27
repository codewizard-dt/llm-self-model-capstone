from __future__ import annotations

import dataclasses
import importlib
import json
import sys
from enum import Enum

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
    get_skill_summary,
    get_skill_definition,
    list_skill_definitions,
    list_skill_summaries,
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

SUMMARY_KEYS = {
    "name",
    "params_model",
    "command_model",
    "inputs",
    "defaults",
    "preconditions",
    "max_duration_ms",
    "movement",
    "command_path",
    "expected_result_source",
    "success_assertion",
    "failure_reasons",
    "recovery_hints",
    "bound_references",
}

FORBIDDEN_ROUTE_FRAGMENTS = (
    "/",
    "://",
    "rclpy",
    "ros2",
    "std_msgs",
    "sensor_msgs",
    "geometry_msgs",
    "Twist",
)


def _qualified_name(model: type[object]) -> str:
    return f"{model.__module__}.{model.__qualname__}"


def _assert_plain_json_value(value: object) -> None:
    assert not dataclasses.is_dataclass(value), f"dataclass leaked into summary: {value!r}"
    assert not isinstance(value, Enum), f"enum leaked into summary: {value!r}"
    assert not isinstance(value, type), f"class leaked into summary: {value!r}"
    assert not isinstance(value, tuple), f"tuple leaked into summary: {value!r}"

    if isinstance(value, dict):
        assert all(isinstance(key, str) for key in value)
        for nested in value.values():
            _assert_plain_json_value(nested)
        return

    if isinstance(value, list):
        for nested in value:
            _assert_plain_json_value(nested)
        return

    assert value is None or isinstance(value, str | int | float | bool), (
        f"non-JSON value leaked into summary: {value!r}"
    )


def _assert_no_object_repr_strings(value: object) -> None:
    if isinstance(value, str):
        assert "<class" not in value
        assert "object at 0x" not in value
        assert "PilotSkillName." not in value
        assert "SkillDefinition(" not in value
        return

    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_object_repr_strings(nested)
        return

    if isinstance(value, list):
        for nested in value:
            _assert_no_object_repr_strings(nested)


def _assert_symbolic_route(value: str) -> None:
    assert value
    assert not any(fragment in value for fragment in FORBIDDEN_ROUTE_FRAGMENTS)


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


def test_skill_summaries_are_json_serializable_plain_data() -> None:
    summaries = list_skill_summaries()

    encoded = json.dumps(summaries, sort_keys=True)

    assert json.loads(encoded) == summaries
    for summary in summaries:
        _assert_plain_json_value(summary)
        _assert_no_object_repr_strings(summary)


def test_skill_summaries_have_deterministic_contract_order() -> None:
    first = list_skill_summaries()
    second = list_skill_summaries()

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert [summary["name"] for summary in first] == [name.value for name in PilotSkillName]
    assert [get_skill_summary(name)["name"] for name in PilotSkillName] == [
        name.value for name in PilotSkillName
    ]


def test_get_skill_definition_is_strict_for_enum_and_string_names() -> None:
    for skill_name in PilotSkillName:
        definition = get_skill_definition(skill_name)
        assert definition.name is skill_name
        assert get_skill_definition(skill_name.value) is definition
        assert get_skill_summary(skill_name)["name"] == skill_name.value
        assert get_skill_summary(skill_name.value)["name"] == skill_name.value

    with pytest.raises(ValueError, match="unknown pilot skill"):
        get_skill_definition("fly_to_goal")
    with pytest.raises(ValueError, match="unknown pilot skill"):
        get_skill_summary("fly_to_goal")


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


def test_every_summary_has_complete_static_metadata() -> None:
    for definition, summary in zip(list_skill_definitions(), list_skill_summaries(), strict=True):
        assert set(summary) == SUMMARY_KEYS
        assert summary["name"] == definition.name.value
        assert summary["params_model"] == _qualified_name(definition.params_model)
        assert summary["command_model"] == _qualified_name(definition.command_model)
        assert summary["inputs"]
        assert summary["defaults"]
        assert summary["preconditions"]
        assert summary["max_duration_ms"] == definition.max_duration_ms
        assert summary["command_path"] == definition.command_path
        assert summary["expected_result_source"] == definition.expected_result_source
        assert summary["failure_reasons"]
        assert summary["recovery_hints"]
        assert summary["bound_references"]

        inputs = summary["inputs"]
        defaults = summary["defaults"]
        success_assertion = summary["success_assertion"]
        assert isinstance(inputs, list)
        assert isinstance(defaults, list)
        assert isinstance(success_assertion, dict)
        assert all(isinstance(input_metadata, dict) for input_metadata in inputs)
        assert all(isinstance(default, dict) for default in defaults)
        assert all(input_metadata["name"] for input_metadata in inputs)
        assert all(input_metadata["description"] for input_metadata in inputs)
        assert all("required" in input_metadata for input_metadata in inputs)
        assert all(default["name"] for default in defaults)
        assert success_assertion["assertion_id"] == definition.success_assertion.assertion_id
        assert success_assertion["name"] == definition.success_assertion.name


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


def test_summaries_reuse_contract_names_models_and_bounds() -> None:
    summaries = list_skill_summaries()
    seen_bound_names: set[str] = set()

    assert [summary["name"] for summary in summaries] == [name.value for name in PilotSkillName]
    assert len({summary["name"] for summary in summaries}) == len(PilotSkillName)

    for definition, summary in zip(list_skill_definitions(), summaries, strict=True):
        params_model, command_model = EXPECTED_MODELS[definition.name]
        assert summary["params_model"] == _qualified_name(params_model)
        assert summary["command_model"] == _qualified_name(command_model)
        assert summary["max_duration_ms"] == definition.max_duration_ms
        assert 0 < summary["max_duration_ms"] <= PILOT_TIMEOUT_MS_MAX

        movement = summary["movement"]
        assert isinstance(movement, dict)
        assert 0.0 <= movement["linear_mps"] <= MAX_LINEAR
        assert 0.0 <= movement["omega_rad_s"] <= MAX_OMEGA
        if movement["arm_deg_min"] is not None:
            assert movement["arm_deg_min"] == ARM_DEG_MIN
            assert movement["arm_deg_max"] == ARM_DEG_MAX
        if movement["arm_rpm"] is not None:
            assert movement["arm_rpm"] == MAX_ARM_RPM
        if movement["claw_grip_force_n"] is not None:
            assert movement["claw_grip_force_n"] == MAX_CLAW_GRIP_FORCE_N

        bound_references = summary["bound_references"]
        assert isinstance(bound_references, list)
        for bound in bound_references:
            assert isinstance(bound, dict)
            assert isinstance(bound["source"], str)
            assert bound["source"].startswith("contracts.")
            seen_bound_names.add(str(bound["name"]))

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
    for definition in list_skill_definitions():
        assert isinstance(definition.command_path, str)
        assert isinstance(definition.expected_result_source, str)
        _assert_symbolic_route(definition.command_path)
        _assert_symbolic_route(definition.expected_result_source)

    for summary in list_skill_summaries():
        assert isinstance(summary["command_path"], str)
        assert isinstance(summary["expected_result_source"], str)
        _assert_symbolic_route(summary["command_path"])
        _assert_symbolic_route(summary["expected_result_source"])


def test_skill_summary_helpers_are_public_from_skills_module_only() -> None:
    import pilot.skills as skills

    assert skills.list_skill_summaries is list_skill_summaries
    assert skills.get_skill_summary is get_skill_summary
    assert "list_skill_summaries" in skills.__all__
    assert "get_skill_summary" in skills.__all__


def test_package_exports_registry_surface_additively() -> None:
    import pilot

    assert pilot.SkillDefinition is SkillDefinition
    assert pilot.list_skill_definitions is list_skill_definitions
    assert pilot.get_skill_definition is get_skill_definition
    assert pilot.ObservationCache is not None


def test_skills_module_imports_without_ros_packages(monkeypatch) -> None:
    ros_roots = {"rclpy", "std_msgs", "sensor_msgs", "geometry_msgs"}

    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in ros_roots:
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.skills", None)

    module = importlib.import_module("pilot.skills")

    assert [definition.name for definition in module.list_skill_definitions()] == list(
        PilotSkillName
    )
    assert [summary["name"] for summary in module.list_skill_summaries()] == [
        name.value for name in PilotSkillName
    ]
    assert ros_roots.isdisjoint(sys.modules)
