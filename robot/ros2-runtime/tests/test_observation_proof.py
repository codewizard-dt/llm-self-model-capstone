from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.observation_proof import (
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
        self.assertIsNone(summary["task_plan_statuses"]["survey:all"]["blocked_reason"])
        self.assertEqual(summary["task_plan_statuses"]["survey:all"]["step_count"], 3)


if __name__ == "__main__":
    unittest.main()
