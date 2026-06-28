from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vexy_ros.pickup_goal_loop import (  # noqa: E402
    _is_ball_indication,
    _robot_object_pose,
    _validate_pickup_config,
    build_parser,
    collect_pickup_config,
    collect_pickup_config_candidates,
)
from vexy_ros.vision_map import Pose2D  # noqa: E402


class PickupGoalLoopHelperTests(unittest.TestCase):
    def test_collect_pickup_config_accepts_json_and_cli_overrides(self) -> None:
        args = _args(
            config_json=json.dumps(
                {
                    "ball_claw_lateral_target_m": -0.08,
                    "ball_close_forward_m": 0.08,
                }
            ),
            ball_claw_lateral_target_m=-0.03,
            pickup_verify_settle_s=0.8,
        )

        config = collect_pickup_config(args)

        self.assertEqual(config["ball_claw_lateral_target_m"], -0.03)
        self.assertEqual(config["ball_close_forward_m"], 0.08)
        self.assertEqual(config["pickup_verify_settle_s"], 0.8)

    def test_collect_pickup_config_candidates_builds_tuning_grid(self) -> None:
        args = _args(
            ball_capture_forward_m=0.14,
            sweep_ball_claw_lateral_target_m="-0.03,-0.06",
            sweep_ball_close_forward_m="0.06,0.08",
        )

        candidates = collect_pickup_config_candidates(args)

        self.assertEqual(len(candidates), 4)
        self.assertEqual(
            [
                (
                    candidate["ball_claw_lateral_target_m"],
                    candidate["ball_close_forward_m"],
                    candidate["ball_capture_forward_m"],
                )
                for candidate in candidates
            ],
            [
                (-0.03, 0.06, 0.14),
                (-0.03, 0.08, 0.14),
                (-0.06, 0.06, 0.14),
                (-0.06, 0.08, 0.14),
            ],
        )

    def test_collect_pickup_config_candidates_accepts_json_sweep(self) -> None:
        args = _args(
            ball_wall_contact_vx=0.10,
            sweep_json=json.dumps(
                [
                    {
                        "ball_claw_lateral_target_m": -0.03,
                        "ball_close_forward_m": 0.06,
                    },
                    {
                        "ball_claw_lateral_target_m": -0.03,
                        "ball_close_forward_m": 0.06,
                    },
                ]
            ),
        )

        candidates = collect_pickup_config_candidates(args)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["ball_wall_contact_vx"], 0.10)
        self.assertEqual(candidates[0]["ball_close_forward_m"], 0.06)

    def test_parser_accepts_equals_form_for_negative_sweep_values(self) -> None:
        args = build_parser().parse_args(
            [
                "--sweep-ball-claw-lateral-target-m=-0.02,-0.05",
                "--sweep-ball-close-forward-m=0.06",
            ]
        )

        candidates = collect_pickup_config_candidates(args)

        self.assertEqual(
            [candidate["ball_claw_lateral_target_m"] for candidate in candidates],
            [-0.02, -0.05],
        )

    def test_validate_pickup_config_rejects_unknown_and_unsafe_values(self) -> None:
        with self.assertRaises(ValueError):
            _validate_pickup_config({"max_vx": 0.4})
        with self.assertRaises(ValueError):
            _validate_pickup_config({"ball_search_omega": 1.2})

    def test_ball_indication_name_accepts_yellow_ball_labels(self) -> None:
        self.assertTrue(_is_ball_indication({"name": "yellow_ball"}))
        self.assertTrue(_is_ball_indication({"class": "sports ball"}))
        self.assertFalse(_is_ball_indication({"label": "bin"}))

    def test_robot_object_pose_applies_camera_offset(self) -> None:
        pose = _robot_object_pose(
            {"forward_m": 0.10, "left_m": 0.02},
            camera_in_robot=Pose2D(0.05, -0.08, 0.0),
        )

        assert pose is not None
        self.assertAlmostEqual(pose.x_m, 0.15)
        self.assertAlmostEqual(pose.y_m, -0.06)


def _args(**overrides) -> argparse.Namespace:
    defaults = {
        "config_json": "",
        "sweep_json": "",
        "sweep_ball_claw_lateral_target_m": "",
        "sweep_ball_close_forward_m": "",
        "sweep_ball_capture_lateral_m": "",
        "ball_claw_lateral_target_m": None,
        "ball_close_forward_m": None,
        "ball_capture_forward_m": None,
        "ball_capture_lateral_m": None,
        "ball_wall_contact_vx": None,
        "ball_search_s": None,
        "ball_search_segment_s": None,
        "ball_search_omega": None,
        "pickup_verify_settle_s": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


if __name__ == "__main__":
    unittest.main()
