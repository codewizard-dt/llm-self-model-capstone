from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.align_to_tag import (
    AlignToTagController,
    AlignToTagGoal,
    BridgeHealth,
    TagObservation,
)


def tag(
    now_s: float, yaw: float, lateral: float, distance: float, tag_id: int = 0
) -> TagObservation:
    return TagObservation(
        tag_id=tag_id,
        stamp_s=now_s,
        yaw_error_rad=yaw,
        lateral_error_m=lateral,
        distance_m=distance,
    )


def bridge(now_s: float, fault: str | None = None) -> BridgeHealth:
    return BridgeHealth(stamp_s=now_s, last_ack_seq=12, fault=fault, status="ok")


class AlignToTagControllerTests(unittest.TestCase):
    def test_refuses_to_start_without_current_tag_and_ack(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal()

        no_tag = controller.start(goal, now_s=1.0, tag=None, bridge=bridge(1.0))
        stale_ack = controller.start(
            goal, now_s=2.0, tag=tag(2.0, 0.2, 0.1, 0.7), bridge=bridge(0.0)
        )

        self.assertEqual(no_tag.result.reason, "stale_tag")
        self.assertEqual(stale_ack.result.reason, "stale_ack")
        self.assertFalse(controller.active)

    def test_decreasing_error_reaches_success_and_sends_stop(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal(target_distance_m=0.45, lateral_tolerance_m=0.06)

        started = controller.start(
            goal, now_s=1.0, tag=tag(1.0, 0.2, 0.1, 0.7), bridge=bridge(1.0)
        )
        running = controller.step(
            now_s=1.1, tag=tag(1.1, 0.04, 0.05, 0.55), bridge=bridge(1.1)
        )
        done = controller.step(
            now_s=1.2, tag=tag(1.2, 0.01, 0.01, 0.46), bridge=bridge(1.2)
        )

        self.assertIsNone(started.result)
        self.assertEqual(running.command.cmd, "drive")
        self.assertTrue(done.result.success)
        self.assertEqual(done.result.reason, "success")
        self.assertEqual(done.command.cmd, "stop")
        self.assertFalse(controller.active)

    def test_timeout_fails_and_stops(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal(timeout_s=1.0)

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, 0.2, 0.1, 0.7), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=2.1, tag=tag(2.1, 0.2, 0.1, 0.7), bridge=bridge(2.1)
        )

        self.assertFalse(decision.result.success)
        self.assertEqual(decision.result.reason, "timeout")
        self.assertEqual(decision.command.cmd, "stop")

    def test_stale_pose_fails_and_stops(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal(tag_stale_s=0.2)

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, 0.2, 0.1, 0.7), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=1.4, tag=tag(1.0, 0.2, 0.1, 0.7), bridge=bridge(1.4)
        )

        self.assertEqual(decision.result.reason, "stale_tag")
        self.assertEqual(decision.command.cmd, "stop")

    def test_bridge_fault_fails_and_stops(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal()

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, 0.2, 0.1, 0.7), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=1.1,
            tag=tag(1.1, 0.2, 0.1, 0.7),
            bridge=bridge(1.1, fault="serial_disconnect"),
        )

        self.assertEqual(decision.result.reason, "bridge_fault")
        self.assertEqual(decision.result.fault, "serial_disconnect")
        self.assertEqual(decision.command.cmd, "stop")

    def test_cancel_fails_and_stops(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal()

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, 0.2, 0.1, 0.7), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=1.1, tag=tag(1.1, 0.2, 0.1, 0.7), bridge=bridge(1.1), cancel=True
        )

        self.assertEqual(decision.result.reason, "cancelled")
        self.assertEqual(decision.command.cmd, "stop")

    def test_turns_in_place_before_approaching_when_tag_is_off_center(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal(max_omega=0.5, min_turn_omega=0.35)

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, -0.15, -0.12, 0.7), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=1.1, tag=tag(1.1, -0.15, -0.12, 0.7), bridge=bridge(1.1)
        )

        self.assertEqual(decision.command.cmd, "turn")
        self.assertEqual(decision.command.vx, 0.0)
        self.assertEqual(decision.command.vy, 0.0)
        self.assertLessEqual(decision.command.omega, -0.35)
        self.assertEqual(decision.command.reason, "center_tag")

    def test_approach_uses_tank_drive_without_lateral_strafe(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal(
            target_distance_m=0.45,
            lateral_tolerance_m=0.06,
            max_vx=0.05,
            min_vx=0.03,
            max_omega=0.1,
            max_step_ms=75,
        )

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, 0.02, 0.01, 0.7), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=1.1, tag=tag(1.1, 0.02, 0.01, 0.7), bridge=bridge(1.1)
        )

        self.assertEqual(decision.command.cmd, "drive")
        self.assertEqual(decision.command.ttl_ms, 75)
        self.assertLessEqual(abs(decision.command.vx), 0.05)
        self.assertEqual(decision.command.vy, 0.0)
        self.assertLessEqual(abs(decision.command.omega), 0.1)
        self.assertEqual(decision.command.reason, "approach_tag")

    def test_approach_uses_minimum_effective_forward_speed(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal(
            target_distance_m=0.45,
            lateral_tolerance_m=0.06,
            distance_tolerance_m=0.01,
            max_vx=0.1,
            min_vx=0.06,
        )

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, 0.0, 0.0, 0.50), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=1.1, tag=tag(1.1, 0.0, 0.0, 0.50), bridge=bridge(1.1)
        )

        self.assertEqual(decision.command.cmd, "drive")
        self.assertAlmostEqual(decision.command.vx, 0.06)

    def test_command_is_clamped_to_goal_bounds(self) -> None:
        controller = AlignToTagController()
        goal = AlignToTagGoal(max_vx=0.05, max_vy=0.04, max_omega=0.1, max_step_ms=75)

        controller.start(
            goal, now_s=1.0, tag=tag(1.0, 2.0, -2.0, 2.0), bridge=bridge(1.0)
        )
        decision = controller.step(
            now_s=1.1, tag=tag(1.1, 2.0, -2.0, 2.0), bridge=bridge(1.1)
        )

        self.assertEqual(decision.command.ttl_ms, 75)
        self.assertEqual(decision.command.cmd, "turn")
        self.assertLessEqual(abs(decision.command.omega), 0.1)


if __name__ == "__main__":
    unittest.main()
