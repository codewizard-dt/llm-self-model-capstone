from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.observation_proof import (
    object_localization_errors,
    proof_passed,
    summarize_observation_bundle,
    task_request_payload,
)


class ObservationProofTests(unittest.TestCase):
    def test_survey_request_payload_is_non_dispatching(self) -> None:
        payload = json.loads(task_request_payload("survey:all"))

        self.assertEqual(payload["target"], "survey:all")
        self.assertEqual(payload["action"], "survey_all")
        self.assertFalse(payload["dispatch"])

    def test_object_request_payload_is_non_dispatching_inspection(self) -> None:
        payload = json.loads(task_request_payload("object:yellow_ball"))

        self.assertEqual(payload["target"], "object:yellow_ball")
        self.assertEqual(payload["action"], "inspect")
        self.assertFalse(payload["dispatch"])

    def test_summarizes_scene_object_and_plan_counts(self) -> None:
        summary = summarize_observation_bundle(
            {
                "requested_targets": ["object:yellow_ball", "survey:all"],
                "object_detections": {"detections": [{"label": "yellow_ball"}]},
                "object_indications": [{"name": "yellow_ball"}],
                "scene_map": {
                    "observed_tag_ids": [1],
                    "objects": [{"name": "yellow_ball"}],
                },
                "object_tracks": {
                    "tracks": [
                        {
                            "id": "yellow_ball_01",
                            "class": "yellow_ball",
                            "status": "confirmed",
                        }
                    ]
                },
                "agent_scene": {
                    "robot": {"pose_confidence": 0.8},
                    "localization": {"tag_residual_m": 0.02},
                    "objects": [
                        {
                            "id": "yellow_ball_01",
                            "class": "yellow_ball",
                            "status": "confirmed",
                            "pose": {"x_m": 1.0, "y_m": 1.0},
                        }
                    ],
                },
                "task_plans": {
                    "survey:all": {
                        "status": "ready",
                        "executable_now": True,
                        "steps": [{}, {}, {}],
                    }
                },
            }
        )

        self.assertFalse(summary["motion_commanded"])
        self.assertEqual(summary["observed_tag_ids"], [1])
        self.assertEqual(summary["scene_object_names"], ["yellow_ball"])
        self.assertEqual(summary["object_detection_count"], 1)
        self.assertEqual(summary["object_indication_count"], 1)
        self.assertEqual(summary["scene_object_count"], 1)
        self.assertEqual(summary["object_track_count"], 1)
        self.assertEqual(summary["agent_scene_object_count"], 1)
        self.assertIsNone(summary["task_plan_statuses"]["survey:all"]["blocked_reason"])
        self.assertEqual(summary["task_plan_statuses"]["survey:all"]["step_count"], 3)

    def test_expected_count_and_ground_truth_errors_are_reported(self) -> None:
        bundle = {
            "object_tracks": {
                "tracks": [
                    {
                        "id": "yellow_ball_01",
                        "class": "yellow_ball",
                        "status": "confirmed",
                    }
                ]
            },
            "agent_scene": {
                "objects": [
                    {
                        "id": "yellow_ball_01",
                        "class": "yellow_ball",
                        "status": "confirmed",
                        "pose": {"x_m": 1.0, "y_m": 1.0},
                    }
                ]
            },
        }

        summary = summarize_observation_bundle(
            bundle,
            expected_ball_count=2,
            ground_truth={
                "objects": [
                    {
                        "id": "truth_ball_01",
                        "class": "yellow_ball",
                        "pose": {"x_m": 1.03, "y_m": 1.04},
                    }
                ]
            },
        )

        self.assertEqual(summary["observed_ball_count"], 1)
        self.assertEqual(summary["false_negative_count"], 1)
        self.assertEqual(summary["localization_error_count"], 1)
        self.assertAlmostEqual(summary["mean_object_localization_error_m"], 0.05)

    def test_proof_requires_new_scene_topics_and_expected_count(self) -> None:
        bundle = {
            "scene_map": {},
            "object_tracks": {},
            "agent_scene": {},
            "expected_ball_count": 1,
            "summary": {"observed_ball_count": 0},
            "task_plans": {"object:yellow_ball": {}},
        }

        self.assertFalse(proof_passed(bundle, targets=["object:yellow_ball"]))
        bundle["summary"] = {"observed_ball_count": 1}
        self.assertTrue(proof_passed(bundle, targets=["object:yellow_ball"]))

    def test_object_localization_errors_match_nearest_same_class(self) -> None:
        errors = object_localization_errors(
            {
                "objects": [
                    {
                        "id": "yellow_ball_01",
                        "class": "yellow_ball",
                        "pose": {"x_m": 1.0, "y_m": 1.0},
                    }
                ]
            },
            {
                "objects": [
                    {
                        "id": "truth_ball_01",
                        "class": "yellow_ball",
                        "pose": {"x_m": 1.0, "y_m": 1.2},
                    }
                ]
            },
        )

        self.assertAlmostEqual(errors[0]["error_m"], 0.2)


if __name__ == "__main__":
    unittest.main()
