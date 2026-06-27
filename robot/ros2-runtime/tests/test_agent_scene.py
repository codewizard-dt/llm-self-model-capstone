from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.agent_scene import build_agent_scene


class AgentSceneTests(unittest.TestCase):
    def test_builds_compact_llm_scene_with_affordances(self) -> None:
        payload = build_agent_scene(
            scene_map={
                "robot_pose": {"x_m": 0.62, "y_m": 1.11, "yaw_rad": 1.518},
                "anchor_tag_ids": [0, 1, 2],
                "observed_tag_ids": [0, 2],
                "tags": {"0": {"x_m": 0.0, "y_m": 0.0, "yaw_rad": 0.0}},
                "localization": {
                    "source": "apriltag",
                    "pose_confidence": 0.82,
                    "pose_age_s": 0.12,
                    "visible_anchor_count": 2,
                    "tag_residual_m": 0.047,
                    "tag_residual_deg": 4.8,
                },
                "objects": [
                    {
                        "id": "yellow_ball_01",
                        "class": "yellow_ball",
                        "pose": {"x_m": 1.02, "y_m": 1.47, "yaw_rad": 0.0},
                        "confidence": 0.78,
                        "position_uncertainty_m": 0.12,
                    }
                ],
            },
            object_tracks={
                "tracks": [
                    {
                        "id": "yellow_ball_01",
                        "class": "yellow_ball",
                        "status": "confirmed",
                        "camera_pose": {"forward_m": 0.72, "left_m": -0.08},
                        "confidence": 0.78,
                        "seen_frames": 8,
                        "age_s": 0.20,
                        "range_source": "bbox_size",
                        "position_uncertainty_m": 0.12,
                        "source": "yellow_hsv",
                    }
                ]
            },
            telemetry={"motion_enabled": True},
            bridge_status={"status": "ok"},
            task_plan=None,
            operator_status={"holding": None},
            now_s=100.0,
        )

        self.assertEqual(payload["robot"]["localization_source"], "apriltag")
        self.assertTrue(payload["robot"]["motion_enabled"])
        self.assertEqual(payload["missing_anchor_tags"], [1])
        self.assertEqual(payload["objects"][0]["id"], "yellow_ball_01")
        self.assertTrue(payload["objects"][0]["reachable"])
        self.assertEqual(payload["affordances"][0]["dispatchable"], False)
        self.assertIn(
            "object-facing controller not yet proven",
            payload["affordances"][1]["reason"],
        )

    def test_gracefully_reports_unavailable_scene(self) -> None:
        payload = build_agent_scene(scene_map=None, now_s=100.0)

        self.assertIsNone(payload["robot"]["pose"])
        self.assertEqual(payload["robot"]["localization_source"], "unavailable")
        self.assertFalse(payload["health"]["scene_map_available"])
        self.assertEqual(payload["objects"], [])


if __name__ == "__main__":
    unittest.main()
