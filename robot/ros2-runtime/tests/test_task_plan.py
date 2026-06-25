from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.task_plan import TaskPlanRequest, build_task_plan
from vexy_ros.vision_map import Pose2D, SceneMap, SceneObject


class TaskPlanTests(unittest.TestCase):
    def test_tag_target_plan_dispatches_to_align_goal(self) -> None:
        scene = _scene()

        plan = build_task_plan(
            scene,
            TaskPlanRequest(
                target="tag:0",
                action="approach",
                target_distance_m=0.8,
                dispatch=True,
            ),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "ready")
        self.assertTrue(plan["executable_now"])
        self.assertEqual(plan["steps"][0]["type"], "align_to_tag")
        self.assertEqual(plan["steps"][0]["goal"]["tag_id"], 0)
        self.assertEqual(plan["steps"][0]["goal"]["target_distance_m"], 0.8)
        self.assertEqual(plan["request"]["target"], "tag:0")

    def test_object_target_plan_is_mapped_but_not_motion_dispatchable_yet(self) -> None:
        scene = _scene()

        plan = build_task_plan(
            scene,
            TaskPlanRequest(target="object:bin", action="inspect"),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "mapped")
        self.assertFalse(plan["executable_now"])
        self.assertEqual(
            plan["blocked_reason"], "object_go_to_pose_controller_not_proven"
        )
        self.assertEqual(plan["target"]["nearest_tag_id"], 0)
        self.assertEqual(plan["steps"][1]["type"], "go_to_map_pose")
        self.assertIn("fresh_vex_ack", plan["steps"][1]["required_proofs"])

    def test_survey_all_plan_describes_non_dispatching_360_scan(self) -> None:
        scene = _scene()

        plan = build_task_plan(
            scene,
            TaskPlanRequest(target="survey:all", action="survey_all"),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "planned")
        self.assertFalse(plan["executable_now"])
        self.assertEqual(plan["blocked_reason"], "survey_motion_controller_not_proven")
        self.assertEqual(plan["request"]["target"], "survey:all")
        self.assertEqual(plan["target"]["scope"], "all")
        self.assertEqual(plan["target"]["observed_tag_ids"], [0])
        self.assertEqual(plan["target"]["unobserved_anchor_tag_ids"], [1, 2])
        self.assertEqual(plan["target"]["objects"][0]["name"], "bin")
        self.assertEqual(plan["steps"][1]["type"], "rotate_in_place")
        self.assertAlmostEqual(plan["steps"][1]["angle_rad"], 6.283185307179586)
        self.assertFalse(plan["steps"][1]["dispatchable"])
        self.assertIn("scan_only_mcap", plan["steps"][1]["required_proofs"])

    def test_missing_target_blocks_plan(self) -> None:
        plan = build_task_plan(
            _scene(),
            TaskPlanRequest(target="object:missing"),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["blocked_reason"], "object_not_in_scene")
        self.assertEqual(plan["request"]["target"], "object:missing")

    def test_object_bearing_is_normalized(self) -> None:
        scene = SceneMap(
            frame_id="map",
            stamp_s=1.0,
            map_from_camera=Pose2D(0.0, 0.0, 0.0),
            map_from_robot=Pose2D(0.0, 0.0, -3.0),
            tags={1: Pose2D(1.0, 0.0, 0.0)},
            objects=[
                SceneObject(
                    name="yellow_ball",
                    map_from_object=Pose2D(1.0, 0.0, 0.0),
                    source="yellow_ball_color",
                    confidence=0.8,
                )
            ],
            anchor_tag_ids=[1],
            observed_tag_ids=[1],
        )

        plan = build_task_plan(
            scene,
            TaskPlanRequest(target="object:yellow_ball"),
            now_s=12.0,
        )

        self.assertLessEqual(plan["target"]["bearing_from_robot_rad"], 3.141592654)
        self.assertGreaterEqual(plan["target"]["bearing_from_robot_rad"], -3.141592654)


def _scene() -> SceneMap:
    return SceneMap(
        frame_id="map",
        stamp_s=1.0,
        map_from_camera=Pose2D(0.0, 0.0, 0.0),
        map_from_robot=Pose2D(0.0, 0.0, 0.0),
        tags={0: Pose2D(1.0, 0.0, 0.0)},
        objects=[
            SceneObject(
                name="bin",
                map_from_object=Pose2D(1.2, 0.2, 0.0),
                source="yolo_ncnn_projection",
                confidence=0.8,
            )
        ],
        anchor_tag_ids=[0, 1, 2],
        observed_tag_ids=[0],
    )


if __name__ == "__main__":
    unittest.main()
