from __future__ import annotations

import dataclasses
import importlib
import json
import sys
from enum import Enum

from contracts import (
    AssertionState,
    BridgeHealth,
    ClawCloseParams,
    ClawCloseSkillCommand,
    CommandStatus,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotObservation,
    PilotSkillResult,
    PilotTaskPhase,
    Pose2D,
    VisibleObject,
)

from pilot.decision import (
    PROMPT_SECTION_ORDER,
    build_decision_prompt,
    build_prompt_payload,
    render_prompt,
)
from pilot.skills import list_skill_summaries


def _observation() -> PilotObservation:
    command = ClawCloseSkillCommand(
        command_id="cmd-close-1",
        issued_ms=1000,
        params=ClawCloseParams(grip_force_n=3.0),
    )
    return PilotObservation(
        observed_ms=1250,
        task_phase=PilotTaskPhase.MANIPULATE,
        objective="pick up the yellow ball",
        robot_pose=Pose2D(x_m=1.0, y_m=0.5, heading_rad=0.2),
        localization=LocalizationState(
            pose=Pose2D(x_m=1.0, y_m=0.5, heading_rad=0.2),
            confidence=0.83,
            age_ms=30,
        ),
        visible_objects=[
            VisibleObject(object_id="obj-yellow-1", label="yellow_ball", confidence=0.91)
        ],
        manipulator=ManipulatorState(
            arm_deg=35.0,
            claw_state="holding",
            held_object_id="obj-yellow-1",
        ),
        bridge=BridgeHealth(state="ok", last_heartbeat_age_ms=12, battery_pct=88.0),
        last_command=command,
        last_result=PilotSkillResult(
            command_id="cmd-close-1",
            skill="claw_close",
            status=CommandStatus.OK,
            completed_ms=1200,
            message="grip verified",
        ),
        current_assertions=[
            PilotAssertion(
                assertion_id="assert-grasp",
                predicate="object held",
                state=AssertionState.TRUE,
                confidence=0.86,
                observed_ms=1230,
            )
        ],
    )


def _assert_plain_json_value(value: object) -> None:
    assert not dataclasses.is_dataclass(value), f"dataclass leaked into prompt: {value!r}"
    assert not isinstance(value, Enum), f"enum leaked into prompt: {value!r}"
    assert not isinstance(value, type), f"class leaked into prompt: {value!r}"
    assert not isinstance(value, tuple), f"tuple leaked into prompt: {value!r}"

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
        f"non-JSON value leaked into prompt: {value!r}"
    )


def _assert_no_object_repr_strings(value: object) -> None:
    if isinstance(value, str):
        assert "<class" not in value
        assert "object at 0x" not in value
        assert "PilotTaskPhase." not in value
        assert "PilotSkillName." not in value
        return

    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_object_repr_strings(nested)
        return

    if isinstance(value, list):
        for nested in value:
            _assert_no_object_repr_strings(nested)


def test_prompt_payload_and_text_include_required_sections() -> None:
    payload, prompt = build_decision_prompt(
        _observation(),
        recent_history="cmd-close-1 completed with grip verified",
        safety_constraints=["Stop if bridge is stale.", "Do not exceed contract bounds."],
    )

    assert tuple(payload) == PROMPT_SECTION_ORDER
    for section in PROMPT_SECTION_ORDER:
        assert section in payload

    for label in (
        "objective",
        "current phase",
        "observation snapshot",
        "assertions",
        "last skill/result",
        "recent history",
        "allowed skills",
        "safety constraints",
        "output schema",
    ):
        assert f"## {label}" in prompt

    assert payload["objective"] == "pick up the yellow ball"
    assert payload["current_phase"] == "manipulate"
    assert payload["last_skill_result"]["last_result"]["status"] == "ok"
    assert payload["recent_history"] == "cmd-close-1 completed with grip verified"


def test_prompt_payload_is_plain_json_serializable_data() -> None:
    payload = build_prompt_payload(
        _observation(),
        recent_history="history",
        safety_constraints=("constraint one", "constraint two"),
    )

    encoded = json.dumps(payload, sort_keys=True)

    assert json.loads(encoded) == payload
    _assert_plain_json_value(payload)
    _assert_no_object_repr_strings(payload)


def test_prompt_payload_and_rendering_are_deterministic() -> None:
    observation = _observation()
    kwargs = {
        "recent_history": "surveyed scene; closed claw",
        "safety_constraints": ["operator interrupt wins", "ttl_ms must remain bounded"],
    }

    first_payload, first_prompt = build_decision_prompt(observation, **kwargs)
    second_payload, second_prompt = build_decision_prompt(observation, **kwargs)

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(second_payload, sort_keys=True)
    assert first_prompt == second_prompt
    assert render_prompt(first_payload) == first_prompt


def test_allowed_skills_are_sourced_from_registry_summary_api(monkeypatch) -> None:
    import pilot.decision as decision

    sentinel = [
        {
            "name": "sentinel_skill",
            "inputs": [],
            "defaults": [],
            "preconditions": ["sentinel precondition"],
        }
    ]

    monkeypatch.setattr(decision.skill_registry, "list_skill_summaries", lambda: sentinel)

    payload = decision.build_prompt_payload(_observation())

    assert payload["allowed_skills"] == sentinel


def test_registry_summaries_flow_into_allowed_skills_without_duplication() -> None:
    payload = build_prompt_payload(_observation())
    summaries = list_skill_summaries()

    assert payload["allowed_skills"] == summaries
    assert [summary["name"] for summary in payload["allowed_skills"]] == [
        summary["name"] for summary in summaries
    ]


def test_decision_module_imports_without_ros_or_provider_packages(monkeypatch) -> None:
    forbidden_roots = {
        "anthropic",
        "geometry_msgs",
        "google_genai",
        "openai",
        "rclpy",
        "sensor_msgs",
        "std_msgs",
    }

    class RejectForbiddenImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            root = fullname.split(".", maxsplit=1)[0]
            if root in forbidden_roots:
                raise AssertionError(f"unexpected runtime/provider import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectForbiddenImports(), *sys.meta_path])
    sys.modules.pop("pilot.decision", None)

    module = importlib.import_module("pilot.decision")
    payload, prompt = module.build_decision_prompt(_observation())

    assert payload["allowed_skills"]
    assert prompt.startswith("Pilot decision prompt")
    assert forbidden_roots.isdisjoint(sys.modules)


def test_package_exports_prompt_helpers_additively() -> None:
    import pilot

    assert pilot.build_prompt_payload is build_prompt_payload
    assert pilot.render_prompt is render_prompt
    assert pilot.build_decision_prompt is build_decision_prompt
    assert pilot.PROMPT_SECTION_ORDER is PROMPT_SECTION_ORDER
    assert pilot.ObservationCache is not None
    assert pilot.list_skill_definitions is not None
