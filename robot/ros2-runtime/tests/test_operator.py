from __future__ import annotations

import importlib
import json
import math
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1] / "contracts" / "src"))

from vexy_ros.operator._core import (  # noqa: E402
    MotorSample,
    ObjectObservation,
    Operator,
    OperatorConfig,
    OperatorEvent,
    OperatorResult,
    PacketCommandSink,
    PrimitiveCommand,
    TagObservation,
    TelemetrySnapshot,
    VisionSnapshot,
    telemetry_snapshot_from_mapping,
)
from vexy_ros.operator_run_capture import (  # noqa: E402
    BAG_TOPICS,
    STRING_TELEMETRY_TOPICS,
    start_operator_run_capture,
)
from vexy_ros.vision_map import Pose2D, TagAnchor  # noqa: E402


APRIL_TAG_MAP = {
    tag_id: TagAnchor(tag_id, Pose2D(float(tag_id), 0.0, 0.0)) for tag_id in range(15)
}
TASK_CONTRACT = {
    "schema_version": "1.0",
    "session_id": "operator-test",
    "generation": 0,
    "round": 0,
    "task": "operator_test",
    "motor_samples": [{"device": "left_drive"}],
    "predicted": {"success": True},
    "gap": {"distance_error_m": 0.0},
}
TASK_OUTLINE = (
    ("locate_nearest_apriltag", ()),
    ("orient_to_tag", (0,)),
    ("move_to_tag", (1,), {"target_distance_m": 0.45}),
    ("grab", (), {"duration_ms": 700}),
    ("lift", ()),
    ("release", ()),
)


def make_operator(
    sink: PacketCommandSink,
    *,
    clock: Any = time.monotonic,
    config: OperatorConfig | None = None,
    event_sink: Any = None,
) -> Operator:
    return Operator(
        sink,
        april_tag_map=APRIL_TAG_MAP,
        camera_in_robot=Pose2D(0.0, -0.08, 0.0),
        task_contract=TASK_CONTRACT,
        task_outline=TASK_OUTLINE,
        config=config,
        clock=clock,
        event_sink=event_sink,
    )


class OperatorCoreTests(unittest.TestCase):
    def test_tag_abstractions_take_zero_based_index_argument(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)

        for tag_id in range(15):
            self.assertFalse(hasattr(operator, f"orient_to_tag_{tag_id}"))
            self.assertFalse(hasattr(operator, f"move_to_tag_{tag_id}"))
        self.assertTrue(callable(operator.orient_to_tag))
        self.assertTrue(callable(operator.move_to_tag))

    def test_reset_state_clears_runtime_state(self) -> None:
        sink = PacketCommandSink()
        events: list[OperatorEvent] = []
        operator = make_operator(sink, clock=lambda: 10.0, event_sink=events.append)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 10.0, forward_m=0.8, left_m=0.0)},
            )
        )
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=10.0,
                motor_samples=(
                    MotorSample(
                        "claw",
                        "manipulator",
                        100,
                        current_amp=2.0,
                        velocity_rpm=1.0,
                    ),
                ),
            )
        )
        operator.pickup_phase = "done"
        operator.pickup_phase_start_s = 10.0
        operator.pickup_visual_capture_confirmed = True
        operator.pickup_grip_confirmed = True
        operator.pickup_attempts = 2
        operator.arm_raise_sent_for_tags.add(1)
        operator.last_command = PrimitiveCommand("drive", vx=0.1)

        operator.reset_state()

        self.assertEqual(operator.vision.stamp_s, 0.0)
        self.assertEqual(operator.vision.tags, {})
        self.assertIsNone(operator.telemetry)
        self.assertIsNone(operator.map_pose)
        self.assertEqual(operator.localization_source, "unknown")
        self.assertIsNone(operator.last_pose_update_s)
        self.assertIsNone(operator.last_command)
        self.assertEqual(operator.pickup_phase, "idle")
        self.assertIsNone(operator.pickup_phase_start_s)
        self.assertFalse(operator.pickup_visual_capture_confirmed)
        self.assertFalse(operator.pickup_grip_confirmed)
        self.assertEqual(operator.pickup_attempts, 0)
        self.assertEqual(operator.arm_raise_sent_for_tags, set())
        self.assertEqual(events[-1].name, "operator_state_reset")

    def test_operator_requires_apriltag_map_and_task_contract(self) -> None:
        sink = PacketCommandSink()
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map={},
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
            )
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract={},
                task_outline=TASK_OUTLINE,
            )
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
            )

    def test_task_contract_requires_operator_method_tuples_not_primitives(self) -> None:
        sink = PacketCommandSink()
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
                task_outline=(("drive", ()),),
            )
        with self.assertRaises(ValueError):
            Operator(
                sink,
                april_tag_map=APRIL_TAG_MAP,
                camera_in_robot=Pose2D(0.0, 0.0, 0.0),
                task_contract=TASK_CONTRACT,
                task_outline=(("move_to_tag", (), {"target_distance_m": 0.45}),),
            )
        operator = Operator(
            sink,
            april_tag_map=APRIL_TAG_MAP,
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
        )
        self.assertEqual(
            operator.task_contract.method_plan[0], ("locate_nearest_apriltag", (), {})
        )
        self.assertEqual(operator.task_contract.method_plan[2][0], "move_to_tag")
        self.assertIn("move_to_tag", operator.allowed_operator_methods)

    def test_operator_method_allowlist_comes_from_task_outline(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map=APRIL_TAG_MAP,
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(("move_to_tag", (1,), {"target_distance_m": 0.45}),),
        )

        operator.require_allowed_method("move_to_tag")
        with self.assertRaises(ValueError):
            operator.require_allowed_method("grab")

    def test_operator_uses_loaded_map_as_available_tag_set(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={0: APRIL_TAG_MAP[0]},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
            clock=lambda: 10.0,
        )
        self.assertEqual(operator.available_april_tag_ids, (0,))
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={
                    0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0),
                    1: TagObservation(1, 9.9, forward_m=0.2, left_m=0.0),
                },
            )
        )

        result = operator.locate_nearest_apriltag()

        self.assertTrue(result.success)
        self.assertEqual(result.tag.tag_id if result.tag else None, 0)
        with self.assertRaises(ValueError):
            operator.move_to_tag(1, target_distance_m=0.45)

    def test_locate_nearest_apriltag_uses_fresh_distance(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={
                    0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0),
                    2: TagObservation(2, 9.9, forward_m=0.4, left_m=0.1),
                },
            )
        )

        result = operator.locate_nearest_apriltag()

        self.assertTrue(result.success)
        self.assertEqual(result.tag.tag_id if result.tag else None, 2)
        self.assertEqual(sink.packets, [])
        self.assertEqual(result.localization_source, "apriltag")
        self.assertIsNotNone(result.map_pose)

    def test_move_to_tag_uses_explicit_standoff_for_loaded_map_pose(self) -> None:
        sink = PacketCommandSink()
        target_distance_m = 0.4064
        tag_anchor = TagAnchor(0, Pose2D(0.8, 0.0, math.pi / 2), "bin")
        operator = Operator(
            sink,
            april_tag_map={0: tag_anchor},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(
                ("move_to_tag", (0,), {"target_distance_m": target_distance_m}),
            ),
            clock=lambda: 10.0,
        )
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )

        result = operator.move_to_tag(0, target_distance_m=target_distance_m)
        expected_target = tag_anchor.map_from_tag.compose(
            Pose2D(target_distance_m, 0.0, 0.0)
        )

        self.assertEqual(result.reason, "moving_to_tag")
        self.assertAlmostEqual(result.target_distance_m, target_distance_m)
        self.assertIsNotNone(result.target_pose)
        self.assertAlmostEqual(result.target_pose.x_m, expected_target.x_m)
        self.assertAlmostEqual(result.target_pose.y_m, expected_target.y_m)
        self.assertAlmostEqual(result.target_pose.yaw_rad, expected_target.yaw_rad)

    def test_target_distance_for_tag_uses_camera_visible_role_standoffs(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={
                0: TagAnchor(0, Pose2D(0.8, 0.0, math.pi / 2), "bin"),
                1: TagAnchor(1, Pose2D(1.2, 0.4, math.pi), "ball_staging"),
                2: TagAnchor(2, Pose2D(0.0, 1.0, -math.pi / 2), "home"),
                3: TagAnchor(3, Pose2D(0.0, 0.0, 0.0), "unknown"),
            },
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(("locate_nearest_apriltag", ()),),
            clock=lambda: 10.0,
        )

        self.assertAlmostEqual(operator.target_distance_for_tag(0), 0.20)
        self.assertAlmostEqual(operator.target_distance_for_tag(1), 0.381)
        self.assertAlmostEqual(operator.target_distance_for_tag(2), 0.45)
        self.assertAlmostEqual(operator.target_distance_for_tag(3), 0.45)

    def test_move_to_tag_raises_arm_once_at_32_inches(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=0.8128, left_m=0.0)},
            )
        )

        result = operator.move_to_tag(0, target_distance_m=0.4064)

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "raising_arm_for_tag")
        self.assertEqual(sink.packets[-1]["cmd"], "arm")
        self.assertEqual(sink.packets[-1]["target_deg"], 20.0)

        result = operator.move_to_tag(0, target_distance_m=0.4064)

        self.assertEqual(result.reason, "moving_to_tag")
        self.assertEqual(sink.packets[-1]["cmd"], "drive")

    def test_pose_is_estimated_from_visible_mapped_apriltags(self) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={0: TagAnchor(0, Pose2D(2.0, 0.0, 0.0))},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
            clock=lambda: 10.0,
        )

        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )

        pose = operator.current_pose()
        self.assertEqual(operator.localization_source, "apriltag")
        self.assertIsNotNone(pose)
        self.assertAlmostEqual(pose.x_m, 1.0)
        self.assertAlmostEqual(pose.y_m, 0.0)

    def test_pose_dead_reckons_when_no_apriltags_are_visible(self) -> None:
        now = 10.0

        def clock() -> float:
            return now

        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={0: TagAnchor(0, Pose2D(2.0, 0.0, 0.0))},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=TASK_OUTLINE,
            clock=clock,
        )
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=0.9, left_m=0.0)},
            )
        )
        operator.move_to_tag(0, target_distance_m=0.4)
        now = 10.1
        operator.update_vision(VisionSnapshot(stamp_s=10.1, tags={}))

        pose = operator.current_pose()
        self.assertEqual(operator.localization_source, "dead_reckoning")
        self.assertIsNotNone(pose)
        self.assertGreater(pose.x_m, 1.0)

    def test_move_to_tag_orients_to_predicted_pose_when_target_is_not_visible(
        self,
    ) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={
                0: TagAnchor(0, Pose2D(1.0, 0.0, 0.0)),
                1: TagAnchor(1, Pose2D(1.0, 1.0, 0.0)),
            },
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(("move_to_tag", (1,), {"target_distance_m": 0.45}),),
            clock=lambda: 10.0,
        )
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={0: TagObservation(0, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )
        operator.update_vision(VisionSnapshot(stamp_s=10.0, tags={}))

        result = operator.move_to_tag(1, target_distance_m=0.45)

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "turning_to_predicted_tag")
        self.assertEqual(sink.packets[-1]["cmd"], "turn")
        self.assertEqual(sink.packets[-1]["reason"], "orient_to_predicted_tag_1")
        self.assertIsNone(result.tag)
        self.assertIsNotNone(result.target_pose)

    def test_move_to_tag_drives_to_predicted_pose_when_heading_is_aligned(
        self,
    ) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={1: TagAnchor(1, Pose2D(1.0, 0.0, 0.0))},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(("move_to_tag", (1,), {"target_distance_m": 0.45}),),
            clock=lambda: 10.0,
        )
        operator.map_pose = Pose2D(0.0, 0.0, 0.0)
        operator.localization_source = "dead_reckoning"
        operator.last_pose_update_s = 10.0
        operator.update_vision(VisionSnapshot(stamp_s=10.0, tags={}))

        result = operator.move_to_tag(1, target_distance_m=0.45)

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "moving_to_predicted_tag")
        self.assertEqual(sink.packets[-1]["cmd"], "drive")
        self.assertEqual(sink.packets[-1]["reason"], "move_to_predicted_tag_1")
        self.assertGreater(sink.packets[-1]["vx"], 0.0)
        self.assertEqual(sink.packets[-1]["omega"], 0.0)

    def test_move_to_tag_turns_at_predicted_pose_before_arrival(
        self,
    ) -> None:
        sink = PacketCommandSink()
        operator = Operator(
            sink,
            april_tag_map={1: TagAnchor(1, Pose2D(1.0, 0.0, math.pi / 2.0))},
            camera_in_robot=Pose2D(0.0, 0.0, 0.0),
            task_contract=TASK_CONTRACT,
            task_outline=(("move_to_tag", (1,), {"target_distance_m": 0.45}),),
            clock=lambda: 10.0,
        )
        operator.map_pose = operator.target_pose_for_tag(1, 0.45)
        operator.map_pose = Pose2D(
            operator.map_pose.x_m,
            operator.map_pose.y_m,
            0.0,
        )
        operator.localization_source = "dead_reckoning"
        operator.last_pose_update_s = 10.0
        operator.update_vision(VisionSnapshot(stamp_s=10.0, tags={}))

        result = operator.move_to_tag(1, target_distance_m=0.45)

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "turning_to_predicted_tag")
        self.assertEqual(sink.packets[-1]["cmd"], "turn")
        self.assertEqual(sink.packets[-1]["reason"], "align_at_predicted_tag_1")

    def test_orient_wrapper_sends_turn_then_stop(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=1.0, left_m=0.2)},
            )
        )

        result = operator.orient_to_tag(1)

        self.assertFalse(result.success)
        self.assertEqual(sink.packets[-1]["cmd"], "turn")
        self.assertEqual(sink.packets[-1]["reason"], "orient_to_tag_1")

        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=1.0, left_m=0.0)},
            )
        )
        result = operator.orient_to_tag(1)

        self.assertTrue(result.success)
        self.assertEqual(sink.packets[-1]["cmd"], "stop")

    def test_grabbed_event_uses_manipulator_telemetry(self) -> None:
        events: list[OperatorEvent] = []
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0, event_sink=events.append)
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=9.9,
                motor_samples=(
                    MotorSample(
                        device="release_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        velocity_rpm=0.5,
                        current_amp=0.4,
                    ),
                ),
            )
        )

        result = operator.grab()

        self.assertTrue(result.has_object)
        self.assertEqual(events[-1].name, "grabbed")
        self.assertEqual(sink.packets[-1]["cmd"], "grab")

    def test_pickup_ball_opens_approaches_and_closes_on_visual_ball(self) -> None:
        now = 10.0

        def clock() -> float:
            return now

        sink = PacketCommandSink()
        operator = make_operator(sink, clock=clock)

        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "opening_claw")
        self.assertEqual(sink.packets[-1]["cmd"], "release")

        now = 10.8
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.35,
                        left_m=0.04,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "moving_to_ball")
        self.assertEqual(sink.packets[-1]["cmd"], "drive")
        self.assertEqual(sink.packets[-1]["reason"], "push_ball_to_wall")
        self.assertGreater(sink.packets[-1]["omega"], 0.0)
        self.assertGreater(sink.packets[-1]["vx"], 0.0)

        now = 11.0
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.10,
                        left_m=-0.08,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "moving_to_ball")
        self.assertEqual(sink.packets[-1]["cmd"], "drive")
        self.assertEqual(sink.packets[-1]["reason"], "push_ball_to_wall")
        self.assertEqual(sink.packets[-1]["omega"], 0.0)

        now = 11.4
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.01,
                        left_m=-0.08,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "closing_claw")
        self.assertEqual(sink.packets[-1]["cmd"], "grab")
        self.assertEqual(sink.packets[-1]["reason"], "close_claw_after_wall_contact")

        now = 15.4
        operator.update_vision(VisionSnapshot(stamp_s=now, objects=()))
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=now,
                motor_samples=(
                    MotorSample(
                        device="effector_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        position_deg=320.0,
                        velocity_rpm=0.0,
                        current_amp=0.0,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "verifying_grab")

        now = 16.1
        result = operator.pickup_ball(duration_ms=700)
        self.assertTrue(result.success)
        self.assertEqual(result.reason, "ball_grabbed")

    def test_pickup_ball_fails_closed_when_closed_claw_does_not_have_object(
        self,
    ) -> None:
        now = 10.0

        def clock() -> float:
            return now

        sink = PacketCommandSink()
        operator = make_operator(sink, clock=clock)

        operator.pickup_ball(duration_ms=700)
        now = 10.8
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.10,
                        left_m=-0.08,
                    ),
                ),
            )
        )
        operator.pickup_ball(duration_ms=700)
        self.assertEqual(sink.packets[-1]["cmd"], "drive")
        self.assertEqual(sink.packets[-1]["reason"], "push_ball_to_wall")

        now = 14.3
        operator.pickup_ball(duration_ms=700)
        self.assertEqual(sink.packets[-1]["cmd"], "grab")
        self.assertEqual(sink.packets[-1]["reason"], "close_claw_after_wall_contact")

        now = 15.4
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=now,
                motor_samples=(
                    MotorSample(
                        device="effector_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        position_deg=500.0,
                        velocity_rpm=0.0,
                        current_amp=0.0,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "grab_not_confirmed")

        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "grab_failed")
        self.assertEqual(sink.packets[-1]["cmd"], "grab")

    def test_pickup_ball_latches_low_grip_current_during_close(self) -> None:
        now = 10.0

        def clock() -> float:
            return now

        events: list[OperatorEvent] = []
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=clock, event_sink=events.append)

        operator.pickup_ball(duration_ms=700)
        now = 10.8
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.05,
                        left_m=-0.08,
                    ),
                ),
            )
        )
        operator.pickup_ball(duration_ms=700)

        now = 14.3
        operator.pickup_ball(duration_ms=700)
        self.assertEqual(sink.packets[-1]["cmd"], "grab")

        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=now + 0.35,
                motor_samples=(
                    MotorSample(
                        device="effector_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        position_deg=237.0,
                        velocity_rpm=-91.7,
                        current_amp=0.507,
                    ),
                ),
            )
        )

        now = 15.4
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=now,
                motor_samples=(
                    MotorSample(
                        device="effector_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        position_deg=237.0,
                        velocity_rpm=0.0,
                        current_amp=0.0,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "verifying_grab")

        now = 16.1
        result = operator.pickup_ball(duration_ms=700)

        self.assertTrue(result.success)
        self.assertTrue(result.has_object)
        self.assertEqual(result.reason, "ball_grabbed")
        self.assertEqual(events[-1].name, "grabbed")
        self.assertTrue(events[-1].detail["grip_confirmed"])
        self.assertEqual(sink.packets[-1]["cmd"], "grab")

    def test_pickup_ball_fails_when_ball_visible_outside_lateral_zone_after_close(
        self,
    ) -> None:
        now = 10.0

        def clock() -> float:
            return now

        sink = PacketCommandSink()
        operator = make_operator(sink, clock=clock)

        operator.pickup_ball(duration_ms=700)
        now = 10.8
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.05,
                        left_m=-0.08,
                    ),
                ),
            )
        )
        operator.pickup_ball(duration_ms=700)

        now = 14.3
        operator.pickup_ball(duration_ms=700)
        self.assertEqual(sink.packets[-1]["cmd"], "grab")

        now = 15.4
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.05,
                        left_m=-0.28,
                    ),
                ),
            )
        )
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=now,
                motor_samples=(
                    MotorSample(
                        device="effector_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        position_deg=320.0,
                        velocity_rpm=0.0,
                        current_amp=0.0,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "grab_not_confirmed")

    def test_pickup_ball_without_visual_lock_searches_then_fails(self) -> None:
        now = 10.0

        def clock() -> float:
            return now

        sink = PacketCommandSink()
        operator = make_operator(
            sink,
            clock=clock,
            config=OperatorConfig(
                ball_search_s=1.0,
                ball_search_segment_s=0.25,
                ball_search_omega=0.2,
            ),
        )

        operator.pickup_ball(duration_ms=700)
        now = 10.8
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "searching_for_ball")
        self.assertEqual(sink.packets[-1]["cmd"], "drive")
        self.assertEqual(sink.packets[-1]["reason"], "search_for_ball")
        self.assertEqual(sink.packets[-1]["vx"], 0.0)
        self.assertGreater(sink.packets[-1]["omega"], 0.0)

        now = 11.2
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "searching_for_ball")
        self.assertEqual(sink.packets[-1]["cmd"], "drive")
        self.assertEqual(sink.packets[-1]["vx"], 0.0)
        self.assertLess(sink.packets[-1]["omega"], 0.0)

        now = 12.0
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "ball_not_found")
        self.assertEqual(sink.packets[-1]["cmd"], "stop")
        self.assertEqual(sink.packets[-1]["reason"], "ball_search_exhausted")

    def test_pickup_ball_search_acquires_ball_then_approaches(self) -> None:
        now = 10.0

        def clock() -> float:
            return now

        events: list[OperatorEvent] = []
        sink = PacketCommandSink()
        operator = make_operator(
            sink,
            clock=clock,
            config=OperatorConfig(ball_search_s=2.0, ball_search_omega=0.2),
            event_sink=events.append,
        )

        operator.pickup_ball(duration_ms=700)
        now = 10.8
        result = operator.pickup_ball(duration_ms=700)
        self.assertEqual(result.reason, "searching_for_ball")
        self.assertEqual(sink.packets[-1]["reason"], "search_for_ball")
        self.assertEqual(sink.packets[-1]["vx"], 0.0)

        now = 11.0
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.35,
                        left_m=0.04,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "moving_to_ball")
        self.assertEqual(sink.packets[-1]["cmd"], "drive")
        self.assertEqual(sink.packets[-1]["reason"], "push_ball_to_wall")
        self.assertGreater(sink.packets[-1]["vx"], 0.0)
        self.assertIn("ball_search_acquired", [event.name for event in events])

    def test_pickup_ball_fails_after_empty_close_attempts(self) -> None:
        now = 10.0

        def clock() -> float:
            return now

        sink = PacketCommandSink()
        operator = make_operator(sink, clock=clock)

        result = operator.pickup_ball(duration_ms=700)
        self.assertEqual(result.reason, "opening_claw")
        now += 0.8
        operator.update_vision(
            VisionSnapshot(
                stamp_s=now,
                objects=(
                    ObjectObservation(
                        "yellow_ball",
                        "yellow_ball",
                        now,
                        forward_m=0.10,
                        left_m=-0.08,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertEqual(result.reason, "moving_to_ball")
        now += 3.5
        result = operator.pickup_ball(duration_ms=700)
        self.assertEqual(result.reason, "closing_claw")
        now += 1.1
        operator.update_telemetry(
            TelemetrySnapshot(
                stamp_s=now,
                motor_samples=(
                    MotorSample(
                        device="effector_motor",
                        subsystem="manipulator",
                        sample_ms=100,
                        position_deg=500.0,
                        velocity_rpm=0.0,
                        current_amp=0.0,
                    ),
                ),
            )
        )
        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "grab_not_confirmed")

        result = operator.pickup_ball(duration_ms=700)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "grab_failed")

    def test_telemetry_parser_extracts_manipulator_sample(self) -> None:
        snapshot = telemetry_snapshot_from_mapping(
            {
                "motion_enabled": True,
                "drive_ports_ok": True,
                "left_vel_rpm": 1.0,
                "right_vel_rpm": 2.0,
                "motor_samples": [
                    {
                        "device": "release_motor",
                        "subsystem": "manipulator",
                        "sample_ms": 42,
                        "values": {"velocity_rpm": 0.0, "current_amp": 0.5},
                    }
                ],
            },
            stamp_s=3.0,
        )

        self.assertIsNotNone(snapshot.manipulator_sample)
        self.assertEqual(snapshot.manipulator_sample.current_amp, 0.5)

    def test_contract_result_matches_locked_contract_shape(self) -> None:
        sink = PacketCommandSink()
        operator = make_operator(sink, clock=lambda: 10.0)
        operator.update_vision(
            VisionSnapshot(
                stamp_s=10.0,
                tags={1: TagObservation(1, 9.9, forward_m=0.8, left_m=0.0)},
            )
        )
        operator.update_telemetry(
            telemetry_snapshot_from_mapping(
                {
                    "t_ms": 1234,
                    "motion_enabled": True,
                    "drive_ports_ok": True,
                    "left_vel_rpm": 1.0,
                    "right_vel_rpm": 2.0,
                    "motor_samples": [
                        {
                            "device": "release_motor",
                            "subsystem": "manipulator",
                            "sample_ms": 1234,
                            "values": {
                                "position_deg": 1.0,
                                "velocity_rpm": 0.0,
                                "current_amp": 0.5,
                                "power_w": 0.0,
                                "torque_nm": 0.0,
                                "efficiency_pct": 0.0,
                                "temperature_c": 30.0,
                            },
                        }
                    ],
                },
                stamp_s=10.0,
            )
        )
        result = operator.move_to_tag(1, target_distance_m=0.45)

        payload = operator.contract_result(method_name="move_to_tag", result=result)

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["task"], "operator_test")
        self.assertEqual(payload["motor_samples"][0]["subsystem"], "claw")
        self.assertEqual(payload["motor_samples"][0]["api_binding"], "vexcode_python")
        self.assertEqual(
            set(payload["motor_samples"][0]["source_api"]),
            {
                "position_deg",
                "velocity_rpm",
                "current_amp",
                "power_w",
                "torque_nm",
                "efficiency_pct",
                "temperature_c",
            },
        )
        self.assertIn("object_detected", payload["vision"])
        self.assertEqual(payload["outcome"]["method"], "move_to_tag")


class String:
    def __init__(self, data: str = "") -> None:
        self.data = data


class Image:
    def __init__(
        self,
        *,
        width: int = 1,
        height: int = 1,
        encoding: str = "bgr8",
        data: bytes = b"\x00\x00\x00",
        header: Any | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.encoding = encoding
        self.data = data
        self.header = header


class Publisher:
    def __init__(self) -> None:
        self.messages: list[String] = []

    def publish(self, msg: String) -> None:
        self.messages.append(msg)


class Node:
    parameter_defaults: dict[str, Any] = {}

    def __init__(self, name: str) -> None:
        self.name = name
        self.publishers: list[Publisher] = []
        self._parameters = {
            "camera_in_robot_json": '{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}',
            "workspace_map_path": "",
            "tag_anchors_json": json.dumps(
                {
                    str(tag_id): {"x_m": float(tag_id), "y_m": 0.0, "yaw_rad": 0.0}
                    for tag_id in range(15)
                }
            ),
            "task_contract_json": json.dumps(
                {
                    "schema_version": "1.0",
                    "session_id": "operator-node-test",
                    "generation": 0,
                    "round": 0,
                    "task": "operator_node_test",
                    "motor_samples": [{"device": "left_drive"}],
                    "predicted": {"success": True},
                    "gap": {"distance_error_m": 0.0},
                }
            ),
            "task_outline_json": json.dumps(
                [
                    ["locate_nearest_apriltag", []],
                    ["move_to_tag", [1], {"target_distance_m": 0.45}],
                    ["grab", [], {"duration_ms": 700}],
                ]
            ),
            "command_topic": "/operator/command",
            "event_topic": "/operator/events",
            "result_topic": "/operator/results",
            "status_topic": "/operator/status",
        }
        self._parameters.update(self.parameter_defaults)

    def declare_parameter(self, name: str, default: Any) -> None:
        self._parameters.setdefault(name, default)

    def get_parameter(self, name: str) -> Any:
        value = self._parameters[name]
        return types.SimpleNamespace(
            get_parameter_value=lambda: types.SimpleNamespace(string_value=value)
        )

    def create_publisher(self, *_args: Any) -> Publisher:
        publisher = Publisher()
        self.publishers.append(publisher)
        return publisher

    def create_subscription(self, *_args: Any) -> object:
        return object()

    def create_timer(self, *_args: Any) -> object:
        return object()

    def get_logger(self) -> Any:
        return types.SimpleNamespace(warn=lambda *_args, **_kwargs: None)

    def destroy_node(self) -> None:
        return None


def install_ros_stubs() -> None:
    rclpy = types.ModuleType("rclpy")
    rclpy.spin = lambda *_args, **_kwargs: None
    rclpy.init = lambda *_args, **_kwargs: None
    rclpy.shutdown = lambda: None

    rclpy_node = types.ModuleType("rclpy.node")
    rclpy_node.Node = Node

    std_msgs = types.ModuleType("std_msgs")
    std_msgs_msg = types.ModuleType("std_msgs.msg")
    std_msgs_msg.String = String

    tf2_msgs = types.ModuleType("tf2_msgs")
    tf2_msgs_msg = types.ModuleType("tf2_msgs.msg")
    tf2_msgs_msg.TFMessage = object

    sensor_msgs = types.ModuleType("sensor_msgs")
    sensor_msgs_msg = types.ModuleType("sensor_msgs.msg")
    sensor_msgs_msg.Image = Image

    sys.modules["rclpy"] = rclpy
    sys.modules["rclpy.node"] = rclpy_node
    sys.modules["std_msgs"] = std_msgs
    sys.modules["std_msgs.msg"] = std_msgs_msg
    sys.modules["tf2_msgs"] = tf2_msgs
    sys.modules["tf2_msgs.msg"] = tf2_msgs_msg
    sys.modules["sensor_msgs"] = sensor_msgs
    sys.modules["sensor_msgs.msg"] = sensor_msgs_msg


class OperatorNodeTests(unittest.TestCase):
    def tearDown(self) -> None:
        Node.parameter_defaults = {}

    def test_node_accepts_ad_hoc_move_command(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        stamp_s = time.monotonic()
        node.operator.update_vision(
            VisionSnapshot(
                stamp_s=stamp_s,
                tags={1: TagObservation(1, stamp_s, forward_m=0.9, left_m=0.0)},
            )
        )

        node._on_command(
            String(
                data=json.dumps(
                    {
                        "action": "move_to_tag",
                        "tag_index": 1,
                        "target_distance_m": 0.45,
                    }
                )
            )
        )

        cmd_packet = json.loads(node._sink.pub.messages[-1].data)
        self.assertEqual(cmd_packet["cmd"], "drive")
        self.assertEqual(cmd_packet["reason"], "move_to_tag_1")
        result_payload = json.loads(node._result_pub.messages[-1].data)
        run_start = json.loads(node._run_start_pub.messages[-1].data)
        self.assertEqual(result_payload["schema_version"], "1.0")
        self.assertEqual(result_payload["outcome"]["method"], "move_to_tag")
        self.assertEqual(result_payload["run_id"], run_start["run_id"])
        self.assertEqual(result_payload["session_id"], run_start["run_id"])

    def test_node_runs_align_to_tag_through_operator_sink(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        node._on_ack(String(data=json.dumps({"ack": 1, "state": "ok"})))
        stamp_s = time.monotonic()
        node._latest_align_tag = node_module.AlignTagObservation(
            tag_id=1,
            stamp_s=stamp_s,
            yaw_error_rad=0.2,
            lateral_error_m=0.05,
            distance_m=0.9,
        )

        node._on_command(
            String(
                data=json.dumps(
                    {
                        "action": "align_to_tag",
                        "tag_id": 1,
                        "target_distance_m": 0.45,
                    }
                )
            )
        )
        node._tick_controllers()

        cmd_packet = json.loads(node._sink.pub.messages[-1].data)
        self.assertIn(cmd_packet["cmd"], {"drive", "turn"})
        self.assertIn(cmd_packet["reason"], {"approach_tag", "center_tag"})
        self.assertTrue(node._align_feedback_pub.messages)

    def test_node_align_to_tag_accepts_requested_mapped_tag_and_rejects_unmapped_tag(
        self,
    ) -> None:
        install_ros_stubs()
        Node.parameter_defaults = {
            "tag_anchors_json": json.dumps(
                {
                    "0": {"x_m": 0.0, "y_m": 0.0, "yaw_rad": 0.0},
                    "2": {"x_m": 2.0, "y_m": 0.0, "yaw_rad": 0.0},
                }
            )
        }
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        node._on_ack(String(data=json.dumps({"ack": 1, "state": "ok"})))
        stamp_s = time.monotonic()
        node._latest_align_tag = node_module.AlignTagObservation(
            tag_id=2,
            stamp_s=stamp_s,
            yaw_error_rad=0.2,
            lateral_error_m=0.05,
            distance_m=0.9,
        )

        node._on_command(
            String(
                data=json.dumps(
                    {
                        "action": "align_to_tag",
                        "tag_id": 2,
                        "target_distance_m": 0.45,
                    }
                )
            )
        )
        node._tick_controllers()
        accepted = json.loads(node._status_pub.messages[-1].data)
        self.assertTrue(accepted["success"])
        self.assertEqual(accepted["reason"], "align_started")
        self.assertTrue(node._align_feedback_pub.messages)

        node._on_command(
            String(
                data=json.dumps(
                    {
                        "action": "align_to_tag",
                        "tag_id": 1,
                        "target_distance_m": 0.45,
                    }
                )
            )
        )
        rejected = json.loads(node._event_pub.messages[-1].data)
        self.assertEqual(rejected["name"], "command_rejected")
        self.assertIn("AprilTag index 1 is not available", rejected["detail"]["error"])

    def test_node_runs_survey_scan_through_operator_sink(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        node._on_ack(String(data=json.dumps({"ack": 1, "state": "ok"})))
        node._on_telemetry(
            String(
                data=json.dumps(
                    {
                        "motion_enabled": True,
                        "drive_ports_ok": True,
                        "estop": False,
                        "left_pos_deg": 1.0,
                        "right_pos_deg": 2.0,
                    }
                )
            )
        )
        node._on_scene_map(String(data=json.dumps({"observed_tag_ids": [0, 2]})))

        node._on_command(
            String(
                data=json.dumps(
                    {
                        "action": "survey_scan",
                        "duration_s": 1.0,
                        "omega_rad_s": 0.22,
                    }
                )
            )
        )
        node._tick_controllers()

        cmd_packet = json.loads(node._sink.pub.messages[-1].data)
        self.assertEqual(cmd_packet["cmd"], "turn")
        self.assertAlmostEqual(cmd_packet["omega"], 0.22)
        self.assertTrue(node._survey_feedback_pub.messages)

    def test_node_runs_routine_through_operator_sink(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()

        node._on_command(String(data=json.dumps({"action": "run_routine", "slot": 3})))

        cmd_packet = json.loads(node._sink.pub.messages[-1].data)
        self.assertEqual(cmd_packet["cmd"], "routine")
        self.assertEqual(cmd_packet["slot"], 3)

    def test_node_accepts_arm_target_command(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        Node.parameter_defaults = {
            "task_outline_json": json.dumps(
                [
                    ["locate_nearest_apriltag", []],
                    ["pickup_ball", []],
                    ["arm", []],
                    ["release", []],
                ]
            )
        }
        node = node_module.OperatorNode()

        node._on_command(
            String(data=json.dumps({"action": "arm", "target_deg": 300.0}))
        )

        cmd_packet = json.loads(node._sink.pub.messages[-1].data)
        self.assertEqual(cmd_packet["cmd"], "arm")
        self.assertEqual(cmd_packet["target_deg"], 300.0)
        result_payload = json.loads(node._result_pub.messages[-1].data)
        self.assertEqual(result_payload["outcome"]["method"], "arm")
        self.assertTrue(result_payload["outcome"]["success"])

    def test_node_resets_operator_state_and_command_lifecycle(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        node.operator.pickup_phase = "done"
        node.operator.pickup_grip_confirmed = True
        node.operator.arm_raise_sent_for_tags.add(1)
        node._command_lifecycle[123] = node_module.CommandLifecycle(
            seq=123,
            packet={"seq": 123, "cmd": "arm", "ttl_ms": 4000},
            sent_monotonic_s=1.0,
            sent_wall_s=1.0,
            expected_end_monotonic_s=5.0,
            expected_end_wall_s=5.0,
        )

        node._on_command(String(data=json.dumps({"action": "reset_operator"})))

        self.assertEqual(node.operator.pickup_phase, "idle")
        self.assertFalse(node.operator.pickup_grip_confirmed)
        self.assertEqual(node.operator.arm_raise_sent_for_tags, set())
        self.assertEqual(node._command_lifecycle, {})
        result_payload = json.loads(node._result_pub.messages[-1].data)
        self.assertEqual(result_payload["outcome"]["method"], "reset_operator")
        self.assertTrue(result_payload["outcome"]["success"])
        command_logs = [
            json.loads(message.data) for message in node._command_log_pub.messages
        ]
        self.assertEqual(command_logs[-1]["event"], "reset")

    def test_node_logs_command_sent_and_ttl_elapsed(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        stamp_s = time.monotonic()
        node.operator.update_vision(
            VisionSnapshot(
                stamp_s=stamp_s,
                tags={1: TagObservation(1, stamp_s, forward_m=0.9, left_m=0.0)},
            )
        )

        node._on_command(
            String(
                data=json.dumps(
                    {
                        "action": "move_to_tag",
                        "tag_index": 1,
                        "target_distance_m": 0.45,
                    }
                )
            )
        )
        sent_logs = [
            json.loads(message.data) for message in node._command_log_pub.messages
        ]
        self.assertEqual(sent_logs[-1]["event"], "sent")
        self.assertEqual(sent_logs[-1]["packet"]["cmd"], "drive")

        for lifecycle in node._command_lifecycle.values():
            object.__setattr__(lifecycle, "expected_end_monotonic_s", 0.0)
        node._tick_command_lifecycle()

        ttl_logs = [
            json.loads(message.data) for message in node._command_log_pub.messages
        ]
        self.assertEqual(ttl_logs[-1]["event"], "ttl_elapsed")

    def test_node_consumes_task_file_and_archives_it(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "inbox"
            archive = Path(tmp) / "archive"
            rejected = Path(tmp) / "rejected"
            Node.parameter_defaults = {
                "task_inbox_dir": str(inbox),
                "task_archive_dir": str(archive),
                "task_rejected_dir": str(rejected),
            }
            inbox.mkdir()
            (inbox / "task.json").write_text(
                json.dumps(
                    {
                        "contract": {
                            "schema_version": "1.0",
                            "session_id": "from-file",
                            "generation": 2,
                            "round": 1,
                            "task": "grab_task",
                            "motor_samples": [
                                {
                                    "device": "left_drive",
                                    "subsystem": "drivetrain",
                                    "sample_ms": 100,
                                    "values": {
                                        "position_deg": 0.0,
                                        "velocity_rpm": 0.0,
                                        "current_amp": 0.0,
                                        "power_w": 0.0,
                                        "torque_nm": 0.0,
                                        "efficiency_pct": 100.0,
                                        "temperature_c": 25.0,
                                    },
                                    "source_api": {
                                        "position_deg": "left_drive.position(DEGREES)",
                                        "velocity_rpm": "left_drive.velocity(RPM)",
                                        "current_amp": (
                                            "left_drive.current(CurrentUnits.AMP)"
                                        ),
                                        "power_w": "left_drive.power(WattUnits.WATT)",
                                        "torque_nm": (
                                            "left_drive.torque(TorqueUnits.NM)"
                                        ),
                                        "efficiency_pct": (
                                            "left_drive.efficiency(PERCENT)"
                                        ),
                                        "temperature_c": (
                                            "left_drive.temperature(CELSIUS)"
                                        ),
                                    },
                                }
                            ],
                            "predicted": {"success": True},
                            "gap": {"distance_error_m": 0.0},
                        },
                        "outline": [["grab", [], {"duration_ms": 700}]],
                    }
                )
            )
            node = node_module.OperatorNode()

            node._poll_task_inbox()
            node._tick_task_outline()

            self.assertFalse((inbox / "task.json").exists())
            self.assertEqual(len(list(archive.glob("task.*.json"))), 1)
            self.assertEqual(list(rejected.glob("*.json")), [])
            run_start = json.loads(node._run_start_pub.messages[-1].data)
            self.assertEqual(
                node.operator.task_contract.contract_line["session_id"],
                run_start["run_id"],
            )
            self.assertEqual(run_start["source_session_id"], "from-file")
            cmd_packet = json.loads(node._sink.pub.messages[-1].data)
            self.assertEqual(cmd_packet["cmd"], "grab")

    def test_task_outline_publishes_visual_snapshot_at_step_completion(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        Node.parameter_defaults = {
            "task_outline_json": json.dumps([["locate_nearest_apriltag", []]]),
        }
        node = node_module.OperatorNode()
        node._on_image(
            Image(
                width=2,
                height=1,
                encoding="bgr8",
                data=bytes([0, 0, 255, 0, 255, 0]),
            )
        )
        node.operator.locate_nearest_apriltag = lambda: OperatorResult(
            True, "nearest_apriltag_located"
        )

        node._run_task_outline("unit-outline.json")
        node._tick_task_outline()

        events = [json.loads(message.data) for message in node._event_pub.messages]
        snapshots = [event for event in events if event["name"] == "visual_snapshot"]
        self.assertTrue(snapshots)
        snapshot = snapshots[-1]
        self.assertEqual(snapshot["detail"]["trigger"], "step_completed")
        self.assertEqual(snapshot["detail"]["step_index"], 0)
        self.assertTrue(snapshot["detail"]["snapshot_available"])
        image = snapshot["detail"]["image"]
        self.assertIn(image["format"], {"jpeg;base64", "ppm;base64"})
        self.assertGreater(len(image["data_b64"]), 0)

    def test_task_outline_publishes_periodic_visual_snapshot(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "inbox"
            archive = Path(tmp) / "archive"
            rejected = Path(tmp) / "rejected"
            Node.parameter_defaults = {
                "task_inbox_dir": str(inbox),
                "task_archive_dir": str(archive),
                "task_rejected_dir": str(rejected),
                "task_timed_primitive_settle_s": 10.0,
                "visual_snapshot_period_s": 1.0,
            }
            inbox.mkdir()
            fixture = ROOT / "fixtures" / "task_deliver_ball.json"
            (inbox / "task_deliver_ball.json").write_text(fixture.read_text())
            node = node_module.OperatorNode()
            node._on_image(
                Image(
                    width=1,
                    height=1,
                    encoding="bgr8",
                    data=bytes([10, 20, 30]),
                )
            )

            node._poll_task_inbox()
            node._tick_task_outline()
            assert node._task_outline_run is not None
            node._task_outline_run.last_visual_snapshot_s = time.monotonic() - 1.1
            before_count = len(node._event_pub.messages)

            node._tick_task_outline()

            events = [
                json.loads(message.data)
                for message in node._event_pub.messages[before_count:]
            ]
            snapshots = [
                event for event in events if event["name"] == "visual_snapshot"
            ]
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(snapshots[0]["detail"]["trigger"], "periodic")
            self.assertEqual(snapshots[0]["detail"]["step_index"], 0)

    def test_task_outline_waits_for_timed_primitive_deadline_without_resend(
        self,
    ) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "inbox"
            archive = Path(tmp) / "archive"
            rejected = Path(tmp) / "rejected"
            Node.parameter_defaults = {
                "task_inbox_dir": str(inbox),
                "task_archive_dir": str(archive),
                "task_rejected_dir": str(rejected),
                "task_timed_primitive_settle_s": 0.0,
            }
            inbox.mkdir()
            fixture = ROOT / "fixtures" / "task_deliver_ball.json"
            (inbox / "task_deliver_ball.json").write_text(fixture.read_text())
            node = node_module.OperatorNode()

            node._poll_task_inbox()
            node._tick_task_outline()

            self.assertIsNotNone(node._task_outline_run)
            assert node._task_outline_run is not None
            pending = node._task_outline_run.pending_timed_primitive
            self.assertIsNotNone(pending)
            assert pending is not None
            self.assertEqual(pending.method_name, "grab")
            self.assertEqual(pending.duration_ms, 500)
            self.assertEqual(node._task_outline_run.step_index, 0)
            self.assertEqual(len(node._sink.pub.messages), 1)

            node._tick_task_outline()

            self.assertEqual(node._task_outline_run.step_index, 0)
            self.assertEqual(len(node._sink.pub.messages), 1)

            pending.deadline_s = time.monotonic() - 1.0
            node._tick_task_outline()

            self.assertEqual(node._task_outline_run.step_index, 1)
            self.assertIsNone(node._task_outline_run.pending_timed_primitive)
            self.assertEqual(len(node._sink.pub.messages), 1)

    def test_task_outline_waits_for_pickup_ball_before_bin_steps(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "inbox"
            archive = Path(tmp) / "archive"
            rejected = Path(tmp) / "rejected"
            Node.parameter_defaults = {
                "task_inbox_dir": str(inbox),
                "task_archive_dir": str(archive),
                "task_rejected_dir": str(rejected),
            }
            inbox.mkdir()
            fixture = ROOT / "fixtures" / "task_deliver_ball.json"
            (inbox / "task_deliver_ball.json").write_text(fixture.read_text())
            node = node_module.OperatorNode()

            calls: list[str] = []
            pickup_results = [
                OperatorResult(False, "opening_claw"),
                OperatorResult(False, "moving_to_ball"),
                OperatorResult(False, "closing_claw"),
                OperatorResult(True, "ball_grabbed"),
            ]

            def grab(*_args: Any, **_kwargs: Any) -> OperatorResult:
                calls.append("grab")
                return OperatorResult(True, "grab_sent")

            def locate_nearest_apriltag(*_args: Any, **_kwargs: Any) -> OperatorResult:
                calls.append("locate_nearest_apriltag")
                return OperatorResult(True, "nearest_apriltag_located")

            def move_to_tag(
                tag_index: int, *_args: Any, **_kwargs: Any
            ) -> OperatorResult:
                calls.append(f"move_to_tag:{tag_index}")
                return OperatorResult(True, "arrived")

            def pickup_ball(*_args: Any, **_kwargs: Any) -> OperatorResult:
                calls.append("pickup_ball")
                return pickup_results.pop(0)

            def lift(*_args: Any, **_kwargs: Any) -> OperatorResult:
                calls.append("lift")
                return OperatorResult(True, "lift_sent")

            def release(*_args: Any, **_kwargs: Any) -> OperatorResult:
                calls.append("release")
                return OperatorResult(True, "release_sent")

            node.operator.grab = grab
            node.operator.locate_nearest_apriltag = locate_nearest_apriltag
            node.operator.move_to_tag = move_to_tag
            node.operator.pickup_ball = pickup_ball
            node.operator.lift = lift
            node.operator.release = release

            node._poll_task_inbox()
            while calls.count("pickup_ball") < 3:
                node._tick_task_outline()
                if (
                    node._task_outline_run is not None
                    and node._task_outline_run.pending_timed_primitive is not None
                ):
                    node._task_outline_run.pending_timed_primitive.deadline_s = (
                        time.monotonic() - 1.0
                    )
                    node._tick_task_outline()
                self.assertNotIn("move_to_tag:0", calls)
                self.assertNotIn("lift", calls)
                self.assertNotIn("release", calls)

            node._tick_task_outline()
            self.assertEqual(calls[-1], "pickup_ball")
            self.assertNotIn("move_to_tag:0", calls)
            self.assertNotIn("lift", calls)
            self.assertNotIn("release", calls)

            node._tick_task_outline()
            self.assertEqual(calls[-1], "move_to_tag:0")

    def test_task_outline_timeout_stops_before_bin_steps(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "inbox"
            archive = Path(tmp) / "archive"
            rejected = Path(tmp) / "rejected"
            Node.parameter_defaults = {
                "task_inbox_dir": str(inbox),
                "task_archive_dir": str(archive),
                "task_rejected_dir": str(rejected),
                "task_step_timeout_s": 0.1,
            }
            inbox.mkdir()
            fixture = ROOT / "fixtures" / "task_deliver_ball.json"
            (inbox / "task_deliver_ball.json").write_text(fixture.read_text())
            node = node_module.OperatorNode()

            calls: list[str] = []

            def success(method_name: str) -> Any:
                def call(*_args: Any, **_kwargs: Any) -> OperatorResult:
                    calls.append(method_name)
                    return OperatorResult(True, "ok")

                return call

            def pickup_ball(*_args: Any, **_kwargs: Any) -> OperatorResult:
                calls.append("pickup_ball")
                return OperatorResult(False, "opening_claw")

            def move_to_tag(
                tag_index: int, *_args: Any, **_kwargs: Any
            ) -> OperatorResult:
                calls.append(f"move_to_tag:{tag_index}")
                return OperatorResult(True, "ok")

            node.operator.grab = success("grab")
            node.operator.locate_nearest_apriltag = success("locate_nearest_apriltag")
            node.operator.move_to_tag = move_to_tag
            node.operator.pickup_ball = pickup_ball
            node.operator.lift = success("lift")
            node.operator.release = success("release")

            node._poll_task_inbox()
            while "pickup_ball" not in calls:
                node._tick_task_outline()
                if (
                    node._task_outline_run is not None
                    and node._task_outline_run.pending_timed_primitive is not None
                ):
                    node._task_outline_run.pending_timed_primitive.deadline_s = (
                        time.monotonic() - 1.0
                    )
                    node._tick_task_outline()
                self.assertNotIn("move_to_tag:0", calls)
                self.assertNotIn("lift", calls)
                self.assertNotIn("release", calls)
            assert node._task_outline_run is not None
            node._task_outline_run.step_started_s -= 1.0

            node._tick_task_outline()

            self.assertEqual(calls[-1], "pickup_ball")
            self.assertNotIn("move_to_tag:0", calls)
            self.assertNotIn("lift", calls)
            self.assertNotIn("release", calls)
            self.assertIsNone(node._task_outline_run)
            self.assertFalse(node._task_file_active)
            event = json.loads(node._event_pub.messages[-1].data)
            self.assertEqual(event["name"], "task_file_execution_failed")
            self.assertEqual(event["detail"]["reason"], "step_timeout")

    def test_node_rejects_invalid_task_file_with_error_sidecar(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "inbox"
            archive = Path(tmp) / "archive"
            rejected = Path(tmp) / "rejected"
            Node.parameter_defaults = {
                "task_inbox_dir": str(inbox),
                "task_archive_dir": str(archive),
                "task_rejected_dir": str(rejected),
            }
            inbox.mkdir()
            (inbox / "bad.json").write_text(
                json.dumps(
                    {
                        "contract": {"schema_version": "1.0"},
                        "outline": [["drive", []]],
                        "extra": True,
                    }
                )
            )
            node = node_module.OperatorNode()

            node._poll_task_inbox()

            self.assertFalse((inbox / "bad.json").exists())
            self.assertEqual(list(archive.glob("*.json")), [])
            rejected_files = [
                path
                for path in rejected.glob("bad.*.json")
                if not path.name.endswith(".error.json")
            ]
            self.assertEqual(len(rejected_files), 1)
            self.assertTrue(
                rejected_files[0]
                .with_suffix(rejected_files[0].suffix + ".error.json")
                .exists()
            )

    def test_node_applies_camera_offset_to_tag_observations(self) -> None:
        Node.parameter_defaults = {
            "camera_in_robot_json": '{"x_m":0.0,"y_m":-0.08,"yaw_rad":0.0}'
        }
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()
        msg = types.SimpleNamespace(
            transforms=[
                types.SimpleNamespace(
                    child_frame_id="tag36h11_1",
                    transform=types.SimpleNamespace(
                        translation=types.SimpleNamespace(x=0.0, z=1.0)
                    ),
                )
            ]
        )

        node._on_tf(msg)

        observed = node.operator.vision.tags[1]
        self.assertAlmostEqual(observed.forward_m, 1.0)
        self.assertAlmostEqual(observed.left_m, -0.08)
        self.assertAlmostEqual(node.operator.camera_in_robot.y_m, -0.08)

    def test_node_rejects_bad_ad_hoc_command_with_event(self) -> None:
        install_ros_stubs()
        node_module = importlib.import_module("vexy_ros.operator.node")
        node = node_module.OperatorNode()

        node._on_command(String(data=json.dumps({"action": "nope"})))

        event = json.loads(node._event_pub.messages[-1].data)
        self.assertEqual(event["name"], "command_rejected")


class OperatorRunCaptureTests(unittest.TestCase):
    def test_capture_starts_json_writer_and_bag_with_visual_topics(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch("vexy_ros.operator_run_capture.subprocess.Popen") as popen,
        ):
            out_dir = Path(tmp)

            processes = start_operator_run_capture(out_dir, label="test-name")
            label = (out_dir / "test.txt").read_text()

        self.assertEqual(len(processes), 3)
        self.assertEqual(label, "test-name\n")
        writer_cmd = popen.call_args_list[0].args[0]
        image_cmd = popen.call_args_list[1].args[0]
        bag_cmd = popen.call_args_list[2].args[0]
        self.assertEqual(
            writer_cmd[:4],
            ["ros2", "run", "vexy_ros", "vexy_telemetry_writer_node"],
        )
        self.assertEqual(
            image_cmd[:4],
            ["ros2", "run", "vexy_ros", "vexy_image_writer_node"],
        )
        self.assertIn("--out-dir", image_cmd)
        self.assertEqual(bag_cmd[:3], ["ros2", "bag", "record"])
        self.assertIn("/operator/events", STRING_TELEMETRY_TOPICS)
        self.assertIn("/operator/command_log", STRING_TELEMETRY_TOPICS)
        self.assertIn("/camera/image_rect", BAG_TOPICS)
        self.assertIn("/vision/object_detections", bag_cmd)


if __name__ == "__main__":
    unittest.main()
