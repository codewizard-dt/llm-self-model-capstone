from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.align_to_tag import BridgeHealth
from vexy_ros.survey_scan import (
    SurveyScanController,
    SurveyScanGoal,
    SurveyTelemetry,
    bounded_goal,
)


def bridge(now_s: float, fault: str | None = None) -> BridgeHealth:
    return BridgeHealth(stamp_s=now_s, last_ack_seq=12, fault=fault, status="ok")


def telemetry(
    now_s: float,
    *,
    motion_enabled: bool = True,
    estop: bool = False,
    drive_ports_ok: bool = True,
) -> SurveyTelemetry:
    return SurveyTelemetry(
        stamp_s=now_s,
        motion_enabled=motion_enabled,
        estop=estop,
        drive_ports_ok=drive_ports_ok,
        left_pos_deg=1.0,
        right_pos_deg=-1.0,
        left_vel_rpm=0.0,
        right_vel_rpm=0.0,
    )


class SurveyScanControllerTests(unittest.TestCase):
    def test_refuses_to_start_without_current_ack_and_telemetry(self) -> None:
        controller = SurveyScanController()
        goal = SurveyScanGoal()

        no_ack = controller.start(
            goal,
            now_s=1.0,
            bridge=BridgeHealth(stamp_s=None),
            telemetry=telemetry(1.0),
        )
        no_telemetry = controller.start(
            goal,
            now_s=1.0,
            bridge=bridge(1.0),
            telemetry=SurveyTelemetry(stamp_s=None),
        )

        self.assertEqual(no_ack.result.reason, "stale_ack")
        self.assertEqual(no_telemetry.result.reason, "stale_telemetry")
        self.assertFalse(controller.active)

    def test_successful_scan_sends_turn_then_stop(self) -> None:
        controller = SurveyScanController()
        goal = SurveyScanGoal(duration_s=1.0, omega_rad_s=0.22, max_step_ms=90)

        started = controller.start(
            goal,
            now_s=1.0,
            bridge=bridge(1.0),
            telemetry=telemetry(1.0),
            observed_tag_ids=[0],
        )
        running = controller.step(
            now_s=1.2,
            bridge=bridge(1.2),
            telemetry=telemetry(1.2),
            observed_tag_ids=[0, 2],
        )
        done = controller.step(
            now_s=2.0,
            bridge=bridge(2.0),
            telemetry=telemetry(2.0),
            observed_tag_ids=[1],
        )

        self.assertIsNone(started.result)
        self.assertEqual(running.command.cmd, "turn")
        self.assertEqual(running.command.ttl_ms, 90)
        self.assertAlmostEqual(running.command.omega, 0.22)
        self.assertTrue(done.result.success)
        self.assertEqual(done.result.reason, "success")
        self.assertEqual(done.command.cmd, "stop")
        self.assertEqual(done.result.observed_tag_ids, [0, 1, 2])
        self.assertFalse(controller.active)

    def test_cancel_sends_stop(self) -> None:
        controller = SurveyScanController()
        goal = SurveyScanGoal()

        controller.start(goal, now_s=1.0, bridge=bridge(1.0), telemetry=telemetry(1.0))
        decision = controller.step(
            now_s=1.1,
            bridge=bridge(1.1),
            telemetry=telemetry(1.1),
            cancel=True,
        )

        self.assertEqual(decision.result.reason, "cancelled")
        self.assertEqual(decision.command.cmd, "stop")
        self.assertFalse(controller.active)

    def test_bad_replacement_goal_stops_active_scan(self) -> None:
        controller = SurveyScanController()
        controller.start(
            SurveyScanGoal(),
            now_s=1.0,
            bridge=bridge(1.0),
            telemetry=telemetry(1.0),
        )

        decision = controller.start(
            SurveyScanGoal(),
            now_s=1.1,
            bridge=BridgeHealth(stamp_s=None),
            telemetry=telemetry(1.1),
        )

        self.assertEqual(decision.result.reason, "stale_ack")
        self.assertEqual(decision.command.cmd, "stop")
        self.assertFalse(controller.active)

    def test_active_scan_fails_closed_on_stale_inputs(self) -> None:
        for bridge_health, sample, reason in [
            (bridge(0.0), telemetry(1.1), "stale_ack"),
            (bridge(1.1), telemetry(0.0), "stale_telemetry"),
        ]:
            with self.subTest(reason=reason):
                controller = SurveyScanController()
                controller.start(
                    SurveyScanGoal(ack_stale_s=0.2, telemetry_stale_s=0.2),
                    now_s=1.0,
                    bridge=bridge(1.0),
                    telemetry=telemetry(1.0),
                )

                decision = controller.step(
                    now_s=1.1, bridge=bridge_health, telemetry=sample
                )

                self.assertEqual(decision.result.reason, reason)
                self.assertEqual(decision.command.cmd, "stop")
                self.assertFalse(controller.active)

    def test_safety_telemetry_blocks_or_stops_scan(self) -> None:
        for sample, reason in [
            (telemetry(1.0, motion_enabled=False), "motion_disabled"),
            (telemetry(1.0, estop=True), "estop"),
            (telemetry(1.0, drive_ports_ok=False), "drive_fault"),
        ]:
            with self.subTest(reason=reason):
                controller = SurveyScanController()
                decision = controller.start(
                    SurveyScanGoal(),
                    now_s=1.0,
                    bridge=bridge(1.0),
                    telemetry=sample,
                )

                self.assertEqual(decision.result.reason, reason)
                self.assertFalse(controller.active)

    def test_bridge_fault_stops_active_scan(self) -> None:
        controller = SurveyScanController()
        controller.start(
            SurveyScanGoal(),
            now_s=1.0,
            bridge=bridge(1.0),
            telemetry=telemetry(1.0),
        )

        decision = controller.step(
            now_s=1.1,
            bridge=bridge(1.1, fault="serial_disconnect"),
            telemetry=telemetry(1.1),
        )

        self.assertEqual(decision.result.reason, "bridge_fault")
        self.assertEqual(decision.result.fault, "serial_disconnect")
        self.assertEqual(decision.command.cmd, "stop")

    def test_goal_bounds_are_clamped(self) -> None:
        high = bounded_goal(SurveyScanGoal(duration_s=60.0, omega_rad_s=2.0))
        low = bounded_goal(
            SurveyScanGoal(duration_s=0.01, omega_rad_s=-0.001, max_step_ms=1)
        )

        self.assertEqual(high.duration_s, 20.0)
        self.assertEqual(high.omega_rad_s, 0.5)
        self.assertEqual(low.duration_s, 0.2)
        self.assertEqual(low.omega_rad_s, -0.02)
        self.assertEqual(low.max_step_ms, 20)


if __name__ == "__main__":
    unittest.main()
