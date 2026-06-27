from __future__ import annotations

import importlib
import sys

import pytest
from contracts import (
    AssertionState,
    BridgeHealth,
    ClawCloseParams,
    ClawCloseSkillCommand,
    CommandStatus,
    ImageBox,
    LocalizationState,
    ManipulatorState,
    PilotAssertion,
    PilotFailure,
    PilotObservation,
    PilotSkillResult,
    PilotTaskPhase,
    Pose2D,
    VisibleObject,
    VisibleTag,
)
from contracts.pilot import (
    MAX_ASSERTIONS,
    MAX_RECENT_FAILURES,
    MAX_VISIBLE_OBJECTS,
    MAX_VISIBLE_TAGS,
)

from pilot.observation import ObservationCache, build_observation_snapshot


def test_build_observation_snapshot_maps_complete_cache() -> None:
    robot_pose = Pose2D(x_m=1.2, y_m=0.4, heading_rad=0.25)
    tag_pose = Pose2D(x_m=1.0, y_m=2.0, heading_rad=0.5)
    localization = LocalizationState(pose=robot_pose, confidence=0.82, age_ms=45)
    visible_object = VisibleObject(
        object_id="obj-yellow-1",
        label="yellow_ball",
        confidence=0.91,
        bbox=ImageBox(x_px=120, y_px=80, width_px=24, height_px=20),
    )
    visible_tag = VisibleTag(tag_id=3, family="tag36h11", confidence=0.77, pose=tag_pose)
    manipulator = ManipulatorState(
        arm_deg=37.5,
        claw_state="holding",
        held_object_id="obj-yellow-1",
    )
    bridge = BridgeHealth(state="ok", last_heartbeat_age_ms=12, battery_pct=87.5)
    command = ClawCloseSkillCommand(
        command_id="cmd-close-1",
        issued_ms=1000,
        params=ClawCloseParams(grip_force_n=3.0),
    )
    result = PilotSkillResult(
        command_id="cmd-close-1",
        skill="claw_close",
        status=CommandStatus.OK,
        completed_ms=1125,
        message="grip verified",
    )
    failure = PilotFailure(
        failed_ms=900,
        source="vision",
        summary="target occluded",
        command_id="cmd-face-1",
        recovery_hint="survey again",
    )
    assertion = PilotAssertion(
        assertion_id="assert-grasp",
        predicate="object held",
        state=AssertionState.TRUE,
        confidence=0.86,
        observed_ms=1130,
    )
    cache = ObservationCache.from_inputs(
        objective="pick up the yellow ball",
        task_phase=PilotTaskPhase.MANIPULATE,
        robot_pose=robot_pose,
        localization=localization,
        visible_objects=[visible_object],
        visible_tags=[visible_tag],
        manipulator=manipulator,
        bridge=bridge,
        last_command=command,
        last_result=result,
        recent_failures=[failure],
        current_assertions=[assertion],
    )

    snapshot = build_observation_snapshot(cache, observed_ms=1200)

    assert isinstance(snapshot, PilotObservation)
    assert PilotObservation.model_validate(snapshot.model_dump()) == snapshot
    assert snapshot.observed_ms == 1200
    assert snapshot.objective == "pick up the yellow ball"
    assert snapshot.task_phase is PilotTaskPhase.MANIPULATE
    assert snapshot.robot_pose == robot_pose
    assert snapshot.localization == localization
    assert snapshot.visible_objects == [visible_object]
    assert snapshot.visible_tags == [visible_tag]
    assert snapshot.manipulator == manipulator
    assert snapshot.bridge == bridge
    assert snapshot.last_command == command
    assert snapshot.last_result == result
    assert snapshot.recent_failures == [failure]
    assert snapshot.current_assertions == [assertion]


def test_build_observation_snapshot_carries_missing_and_stale_optional_evidence() -> None:
    stale_localization = LocalizationState(pose=None, confidence=0.0, age_ms=25_000)
    stale_bridge = BridgeHealth(
        state="stale",
        last_heartbeat_age_ms=30_000,
        fault="heartbeat timeout",
    )
    cache = ObservationCache.from_inputs(
        objective="wait for operator",
        localization=stale_localization,
        bridge=stale_bridge,
    )

    snapshot = build_observation_snapshot(cache, observed_ms=30_500)

    assert snapshot.robot_pose is None
    assert snapshot.localization == stale_localization
    assert snapshot.localization.pose is None
    assert snapshot.localization.confidence == 0.0
    assert snapshot.visible_objects == []
    assert snapshot.visible_tags == []
    assert snapshot.manipulator.arm_deg is None
    assert snapshot.manipulator.claw_state == "unknown"
    assert snapshot.manipulator.held_object_id is None
    assert snapshot.bridge == stale_bridge
    assert snapshot.last_command is None
    assert snapshot.last_result is None
    assert snapshot.recent_failures == []
    assert snapshot.current_assertions == []


def test_build_observation_snapshot_sorts_before_contract_truncation() -> None:
    objects = [
        VisibleObject(
            object_id=f"obj-{idx:02d}",
            label="target",
            confidence=0.5,
        )
        for idx in reversed(range(MAX_VISIBLE_OBJECTS + 2))
    ]
    tags = [
        VisibleTag(tag_id=idx, family="tag36h11", confidence=0.7)
        for idx in reversed(range(MAX_VISIBLE_TAGS + 2))
    ]
    failures = [
        PilotFailure(
            failed_ms=idx,
            source="vision",
            summary=f"failure {idx}",
            command_id=f"cmd-{idx:02d}",
        )
        for idx in range(MAX_RECENT_FAILURES + 2)
    ]
    assertions = [
        PilotAssertion(
            assertion_id=f"assert-{idx:02d}",
            predicate="bounded assertion",
            state=AssertionState.UNKNOWN,
            confidence=0.0,
            age_ms=idx,
        )
        for idx in reversed(range(MAX_ASSERTIONS + 2))
    ]
    cache = ObservationCache.from_inputs(
        objective="compact deterministic evidence",
        visible_objects=objects,
        visible_tags=tags,
        recent_failures=failures,
        current_assertions=assertions,
    )

    snapshot = build_observation_snapshot(cache, observed_ms=50)

    assert [obj.object_id for obj in snapshot.visible_objects] == [
        f"obj-{idx:02d}" for idx in range(MAX_VISIBLE_OBJECTS)
    ]
    assert [tag.tag_id for tag in snapshot.visible_tags] == list(range(MAX_VISIBLE_TAGS))
    assert [failure.failed_ms for failure in snapshot.recent_failures] == list(
        range(MAX_RECENT_FAILURES + 1, 1, -1)
    )
    assert [assertion.assertion_id for assertion in snapshot.current_assertions] == [
        f"assert-{idx:02d}" for idx in range(MAX_ASSERTIONS)
    ]
    assert len(snapshot.visible_objects) == MAX_VISIBLE_OBJECTS
    assert len(snapshot.visible_tags) == MAX_VISIBLE_TAGS
    assert len(snapshot.recent_failures) == MAX_RECENT_FAILURES
    assert len(snapshot.current_assertions) == MAX_ASSERTIONS


@pytest.mark.parametrize("objective", [None, "", "   "])
def test_build_observation_snapshot_rejects_missing_or_blank_objective(
    objective: str | None,
) -> None:
    cache = ObservationCache.from_inputs(objective=objective)

    with pytest.raises(ValueError, match="objective is required"):
        build_observation_snapshot(cache, observed_ms=0)


def test_build_observation_snapshot_rejects_negative_observed_ms() -> None:
    cache = ObservationCache.from_inputs(objective="hold position")

    with pytest.raises(ValueError, match="observed_ms must be non-negative"):
        build_observation_snapshot(cache, observed_ms=-1)


def test_observation_builder_imports_without_ros_packages(monkeypatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(("rclpy.", "std_msgs.", "sensor_msgs.")):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.observation", None)

    module = importlib.import_module("pilot.observation")
    snapshot = module.build_observation_snapshot(
        module.ObservationCache.from_inputs(objective="ros-free"),
        observed_ms=1,
    )

    assert isinstance(snapshot, PilotObservation)
    assert "rclpy" not in sys.modules
