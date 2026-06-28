from __future__ import annotations

import importlib
import math
import sys

import pytest
from contracts import PilotObservation, PilotTaskPhase

from pilot.live_observation import build_live_observation, build_live_observation_cache
from pilot.observation import build_observation_snapshot


def test_agent_scene_payload_builds_contract_valid_snapshot() -> None:
    snapshot = build_live_observation(
        objective="collect the red cube",
        observed_ms=12_500,
        task_phase=PilotTaskPhase.MANIPULATE,
        agent_scene={
            "type": "agent_scene",
            "robot": {
                "pose": {"x_m": 1.1, "y_m": -0.2, "yaw_rad": 0.5},
                "pose_confidence": 0.84,
                "pose_age_s": 0.042,
                "bridge_status": "ok",
                "estop": False,
                "holding": "cube-red-1",
            },
            "localization": {
                "source": "apriltag",
                "pose_confidence": 0.84,
                "pose_age_s": 0.042,
            },
            "objects": [
                {
                    "id": "cube-red-1",
                    "class": "red_cube",
                    "confidence": 0.92,
                    "status": "confirmed",
                    "bbox_xyxy": [100, 80, 140, 132],
                    "source": "object_tracks",
                },
                {
                    "id": "cube-debug",
                    "class": "red_cube",
                    "confidence": 0.2,
                    "status": "candidate",
                },
            ],
            "visible_tags": [
                {
                    "tag_id": 4,
                    "family": "tag36h11",
                    "confidence": 0.7,
                    "pose": {"x_m": 0.0, "y_m": 1.0, "heading_deg": 90.0},
                    "visible": True,
                },
                {"tag_id": 9, "visible": False},
            ],
            "health": {"bridge_status_available": True},
        },
        telemetry={
            "battery_pct": 81.5,
            "last_heartbeat_age_ms": 18,
            "arm_deg": 35.0,
        },
    )

    assert PilotObservation.model_validate(snapshot.model_dump()) == snapshot
    assert snapshot.objective == "collect the red cube"
    assert snapshot.observed_ms == 12_500
    assert snapshot.task_phase is PilotTaskPhase.MANIPULATE
    assert snapshot.robot_pose is not None
    assert snapshot.robot_pose.heading_rad == pytest.approx(0.5)
    assert snapshot.localization.pose == snapshot.robot_pose
    assert snapshot.localization.confidence == pytest.approx(0.84)
    assert snapshot.localization.age_ms == 42
    assert [obj.object_id for obj in snapshot.visible_objects] == ["cube-red-1"]
    assert snapshot.visible_objects[0].label == "red_cube"
    assert snapshot.visible_objects[0].bbox is not None
    assert snapshot.visible_objects[0].bbox.width_px == 40
    assert [tag.tag_id for tag in snapshot.visible_tags] == [4]
    assert snapshot.visible_tags[0].pose is not None
    assert snapshot.visible_tags[0].pose.heading_rad == pytest.approx(math.pi / 2)
    assert snapshot.bridge.state == "ok"
    assert snapshot.bridge.last_heartbeat_age_ms == 18
    assert snapshot.bridge.battery_pct == pytest.approx(81.5)
    assert snapshot.manipulator.arm_deg == pytest.approx(35.0)
    assert snapshot.manipulator.claw_state == "holding"
    assert snapshot.manipulator.held_object_id == "cube-red-1"


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("heading_rad", 0.25, 0.25),
        ("yaw_rad", -0.5, -0.5),
        ("heading", 0.75, 0.75),
        ("heading_deg", 180.0, math.pi),
    ],
)
def test_pose_heading_aliases_emit_heading_rad(field: str, value: float, expected: float) -> None:
    snapshot = build_live_observation(
        objective="face the anchor",
        observed_ms=1,
        agent_scene={
            "robot": {
                "pose": {"x_m": 0.1, "y_m": 0.2, field: value},
                "pose_confidence": 0.5,
            },
            "localization": {"pose_confidence": 0.5, "age_ms": 7},
            "visible_tags": [
                {
                    "tag_id": 1,
                    "confidence": 0.6,
                    "pose": {"x_m": 1.0, "y_m": 2.0, field: value},
                }
            ],
        },
    )

    assert snapshot.robot_pose is not None
    assert snapshot.robot_pose.heading_rad == pytest.approx(expected)
    assert snapshot.visible_tags[0].pose is not None
    assert snapshot.visible_tags[0].pose.heading_rad == pytest.approx(expected)


def test_fallback_payloads_build_snapshot_without_agent_scene() -> None:
    snapshot = build_live_observation(
        objective="survey the field",
        observed_ms=3_000,
        scene_map={
            "robot_pose": {"x_m": 2.0, "y_m": 1.5, "heading_deg": 45.0},
            "localization": {
                "source": "stale_apriltag",
                "pose_confidence": 0.31,
                "pose_age_s": 1.2,
            },
            "tags": {
                "2": {"x_m": 0.0, "y_m": 0.0, "yaw_rad": 0.0},
                "3": {"x_m": 1.0, "y_m": 0.0, "heading": 0.3},
            },
        },
        object_tracks={
            "tracks": [
                {
                    "id": "blue-ball-1",
                    "class": "blue_ball",
                    "status": "confirmed",
                    "confidence": 0.63,
                    "bbox": {"x_px": 12, "y_px": 9, "width_px": 30, "height_px": 26},
                }
            ]
        },
        telemetry={
            "motion_enabled": True,
            "estop": False,
            "battery_pct": 67.0,
            "motor_samples": [
                {"device": "arm", "subsystem": "arm", "position_deg": 22.5},
            ],
        },
        bridge_status={"state": "degraded", "observed_ms": 2_750},
        task_plan={"phase": "survey"},
        operator_status={"claw_state": "open"},
    )

    assert PilotObservation.model_validate(snapshot.model_dump()) == snapshot
    assert snapshot.task_phase is PilotTaskPhase.SURVEY
    assert snapshot.robot_pose is not None
    assert snapshot.robot_pose.heading_rad == pytest.approx(math.pi / 4)
    assert snapshot.localization.confidence == pytest.approx(0.31)
    assert snapshot.localization.age_ms == 1_200
    assert [obj.object_id for obj in snapshot.visible_objects] == ["blue-ball-1"]
    assert [tag.tag_id for tag in snapshot.visible_tags] == [2, 3]
    assert snapshot.bridge.state == "degraded"
    assert snapshot.bridge.last_heartbeat_age_ms == 250
    assert snapshot.bridge.battery_pct == pytest.approx(67.0)
    assert snapshot.manipulator.arm_deg == pytest.approx(22.5)
    assert snapshot.manipulator.claw_state == "open"


def test_missing_and_unavailable_evidence_stays_unknown_or_stale() -> None:
    snapshot = build_live_observation(
        objective="wait",
        observed_ms=20,
        agent_scene={
            "robot": {
                "pose": {"heading_deg": 90.0},
                "bridge_status": "unknown",
            },
            "localization": {"source": "unavailable"},
            "objects": [
                {"id": "old", "class": "cube", "status": "expired", "confidence": 0.9},
            ],
            "visible_tags": [{"tag_id": 5, "visible": False}],
            "health": {"bridge_status_available": False},
        },
    )

    assert snapshot.robot_pose is None
    assert snapshot.localization.pose is None
    assert snapshot.localization.confidence == 0.0
    assert snapshot.visible_objects == []
    assert snapshot.visible_tags == []
    assert snapshot.bridge.state == "stale"
    assert snapshot.bridge.last_heartbeat_age_ms is None
    assert snapshot.manipulator.arm_deg is None
    assert snapshot.manipulator.claw_state == "unknown"
    assert snapshot.manipulator.held_object_id is None


def test_localization_preserves_explicit_zero_age_over_robot_fallback() -> None:
    snapshot = build_live_observation(
        objective="use fresh localization",
        observed_ms=50,
        agent_scene={
            "robot": {
                "pose": {"x_m": 0.5, "y_m": 0.25, "heading_rad": 0.0},
                "pose_confidence": 0.4,
                "pose_age_ms": 50,
            },
            "localization": {"confidence": 0.9, "age_ms": 0},
        },
    )

    assert snapshot.localization.age_ms == 0
    assert snapshot.localization.confidence == pytest.approx(0.9)
    assert snapshot.localization.pose == snapshot.robot_pose


def test_bridge_preserves_explicit_zero_heartbeat_age() -> None:
    snapshot = build_live_observation(
        objective="use fresh bridge heartbeat",
        observed_ms=50,
        agent_scene={
            "robot": {
                "bridge_status": "ok",
                "last_heartbeat_age_ms": 0,
            },
        },
    )

    assert snapshot.bridge.state == "ok"
    assert snapshot.bridge.last_heartbeat_age_ms == 0


@pytest.mark.parametrize("objective", [None, "", "   "])
def test_live_observation_rejects_missing_objective(objective: str | None) -> None:
    with pytest.raises(ValueError, match="objective is required"):
        build_live_observation(objective=objective, observed_ms=1)


def test_cache_delegates_final_sorting_and_validation_to_builder() -> None:
    cache = build_live_observation_cache(
        objective="sort evidence",
        observed_ms=1,
        agent_scene={
            "objects": [
                {"id": "low", "class": "cube", "confidence": 0.1, "status": "confirmed"},
                {"id": "high", "class": "cube", "confidence": 0.9, "status": "confirmed"},
            ],
            "visible_tags": [
                {"tag_id": 7, "family": "tag36h11", "confidence": 0.5},
                {"tag_id": 2, "family": "tag36h11", "confidence": 0.5},
            ],
        },
    )

    snapshot = build_observation_snapshot(cache, observed_ms=1)

    assert [obj.object_id for obj in snapshot.visible_objects] == ["high", "low"]
    assert [tag.tag_id for tag in snapshot.visible_tags] == [2, 7]


def test_live_observation_imports_without_ros_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    class RejectRosImports:
        def find_spec(self, fullname: str, path: object, target: object = None) -> object:
            if fullname == "rclpy" or fullname.startswith(("rclpy.", "std_msgs.", "sensor_msgs.")):
                raise AssertionError(f"unexpected ROS import: {fullname}")
            return None

    monkeypatch.setattr(sys, "meta_path", [RejectRosImports(), *sys.meta_path])
    sys.modules.pop("pilot.live_observation", None)

    module = importlib.import_module("pilot.live_observation")
    snapshot = module.build_live_observation(objective="ros-free", observed_ms=1)

    assert isinstance(snapshot, PilotObservation)
    assert "rclpy" not in sys.modules
