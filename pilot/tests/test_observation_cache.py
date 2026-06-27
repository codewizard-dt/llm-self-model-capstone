from __future__ import annotations

import importlib
import sys

from contracts import (
    AssertionState,
    BridgeHealth,
    ClawCloseSkillCommand,
    ClawCloseParams,
    CommandStatus,
    ImageBox,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotFailure,
    PilotSkillResult,
    PilotTaskPhase,
    VisibleObject,
    VisibleTag,
)

from pilot.observation import (
    ObservationCache,
    assertion_sort_key,
    sorted_assertions,
    sorted_failures,
    sorted_visible_objects,
    sorted_visible_tags,
)


def test_cache_construction_reuses_contract_models() -> None:
    localization = LocalizationState(confidence=0.8, age_ms=40)
    manipulator = ManipulatorState(arm_deg=12.0, claw_state="holding", held_object_id="ball-1")
    bridge = BridgeHealth(state="ok", last_heartbeat_age_ms=10, battery_pct=91.0)
    command = ClawCloseSkillCommand(
        command_id="cmd-1",
        issued_ms=100,
        params=ClawCloseParams(grip_force_n=2.0),
    )
    result = PilotSkillResult(
        command_id="cmd-1",
        skill="claw_close",
        status=CommandStatus.OK,
        completed_ms=140,
    )

    cache = ObservationCache.from_inputs(
        objective="pick up the yellow ball",
        task_phase=PilotTaskPhase.MANIPULATE,
        localization=localization,
        visible_objects=[VisibleObject(object_id="ball-1", label="yellow_ball", confidence=0.9)],
        visible_tags=[VisibleTag(tag_id=4, confidence=0.7)],
        manipulator=manipulator,
        bridge=bridge,
        last_command=command,
        last_result=result,
        recent_failures=[
            PilotFailure(failed_ms=90, source="vision", summary="target briefly lost")
        ],
        current_assertions=[
            PilotAssertion(
                assertion_id="assert-1",
                predicate="object centered",
                state=AssertionState.UNKNOWN,
                confidence=0.0,
                age_ms=20,
            )
        ],
    )

    assert cache.objective == "pick up the yellow ball"
    assert cache.task_phase is PilotTaskPhase.MANIPULATE
    assert cache.localization is localization
    assert cache.manipulator is manipulator
    assert cache.bridge is bridge
    assert cache.last_command is command
    assert cache.last_result is result
    assert isinstance(cache.visible_objects[0], VisibleObject)
    assert isinstance(cache.visible_tags[0], VisibleTag)
    assert isinstance(cache.recent_failures[0], PilotFailure)
    assert isinstance(cache.current_assertions[0], PilotAssertion)


def test_missing_inputs_are_explicit_unknown_or_empty() -> None:
    cache = ObservationCache.from_inputs()

    assert cache.objective is None
    assert cache.task_phase is PilotTaskPhase.IDLE
    assert cache.robot_pose is None
    assert cache.localization.pose is None
    assert cache.localization.confidence == 0.0
    assert cache.localization.age_ms == 0
    assert cache.visible_objects == ()
    assert cache.visible_tags == ()
    assert cache.manipulator.arm_deg is None
    assert cache.manipulator.claw_state == "unknown"
    assert cache.manipulator.held_object_id is None
    assert cache.bridge.state == "stale"
    assert cache.bridge.last_heartbeat_age_ms is None
    assert cache.last_command is None
    assert cache.last_result is None
    assert cache.recent_failures == ()
    assert cache.current_assertions == ()


def test_stale_inputs_are_carried_without_fabricated_confidence() -> None:
    stale_localization = LocalizationState(pose=None, confidence=0.0, age_ms=25_000)
    stale_bridge = BridgeHealth(
        state="stale",
        last_heartbeat_age_ms=30_000,
        fault="heartbeat timeout",
    )

    cache = ObservationCache.from_inputs(localization=stale_localization, bridge=stale_bridge)

    assert cache.localization is stale_localization
    assert cache.localization.pose is None
    assert cache.localization.confidence == 0.0
    assert cache.bridge is stale_bridge
    assert cache.bridge.state == "stale"
    assert cache.bridge.fault == "heartbeat timeout"


def test_deterministic_visible_object_ordering() -> None:
    objects = [
        VisibleObject(
            object_id="obj-b",
            label="yellow_ball",
            confidence=0.9,
            bbox=ImageBox(x_px=20, y_px=10, width_px=5, height_px=5),
        ),
        VisibleObject(
            object_id="obj-a",
            label="yellow_ball",
            confidence=0.9,
            bbox=ImageBox(x_px=30, y_px=10, width_px=5, height_px=5),
        ),
        VisibleObject(object_id="obj-c", label="blue_goal", confidence=0.7),
    ]

    assert [obj.object_id for obj in sorted_visible_objects(objects)] == ["obj-a", "obj-b", "obj-c"]
    assert sorted_visible_objects(objects) == sorted_visible_objects(tuple(reversed(objects)))


def test_deterministic_tag_failure_and_assertion_ordering() -> None:
    tags = [
        VisibleTag(tag_id=7, family="tag36h11", confidence=0.7),
        VisibleTag(tag_id=2, family="tag36h11", confidence=0.9),
        VisibleTag(tag_id=1, family="tag25h9", confidence=0.5),
    ]
    failures = [
        PilotFailure(failed_ms=100, source="vision", summary="lost target", command_id="cmd-2"),
        PilotFailure(failed_ms=120, source="bridge", summary="ack timeout", command_id="cmd-1"),
        PilotFailure(failed_ms=100, source="command", summary="rejected", command_id="cmd-3"),
    ]
    assertions = [
        PilotAssertion(
            assertion_id="assert-b",
            predicate="target visible",
            state=AssertionState.TRUE,
            confidence=0.9,
            observed_ms=200,
        ),
        PilotAssertion(
            assertion_id="assert-a",
            predicate="bridge healthy",
            state=AssertionState.UNKNOWN,
            confidence=0.0,
            age_ms=500,
        ),
    ]

    assert [(tag.family, tag.tag_id) for tag in sorted_visible_tags(tags)] == [
        ("tag25h9", 1),
        ("tag36h11", 2),
        ("tag36h11", 7),
    ]
    assert [failure.command_id for failure in sorted_failures(failures)] == [
        "cmd-1",
        "cmd-3",
        "cmd-2",
    ]
    assert [assertion.assertion_id for assertion in sorted_assertions(assertions)] == [
        "assert-a",
        "assert-b",
    ]
    assert assertion_sort_key(assertions[0]) == assertion_sort_key(assertions[0])


def test_observation_module_imports_without_ros_packages(monkeypatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(("rclpy.", "std_msgs.", "sensor_msgs.")):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.observation", None)

    module = importlib.import_module("pilot.observation")

    assert module.ObservationCache.from_inputs().visible_objects == ()
    assert "rclpy" not in sys.modules
