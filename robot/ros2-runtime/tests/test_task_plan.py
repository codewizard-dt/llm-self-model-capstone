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

    def test_survey_all_plan_dispatches_to_bounded_scan(self) -> None:
        scene = _scene()

        plan = build_task_plan(
            scene,
            TaskPlanRequest(target="survey:all", action="survey_all"),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "ready")
        self.assertTrue(plan["executable_now"])
        self.assertEqual(plan["request"]["target"], "survey:all")
        self.assertEqual(plan["target"]["scope"], "all")
        self.assertEqual(plan["target"]["observed_tag_ids"], [0])
        self.assertEqual(plan["target"]["unobserved_anchor_tag_ids"], [1, 2])
        self.assertEqual(plan["target"]["objects"][0]["name"], "bin")
        self.assertEqual(plan["steps"][1]["type"], "survey_scan")
        self.assertAlmostEqual(plan["steps"][1]["angle_rad"], 6.283185307179586)
        self.assertAlmostEqual(plan["steps"][1]["duration_s"], 14.5)
        self.assertAlmostEqual(plan["steps"][1]["omega_rad_s"], 0.45)
        self.assertTrue(plan["steps"][1]["dispatchable"])
        self.assertAlmostEqual(plan["steps"][1]["goal"]["duration_s"], 14.5)
        self.assertAlmostEqual(plan["steps"][1]["goal"]["omega_rad_s"], 0.45)
        self.assertIn("scan_only_mcap", plan["steps"][1]["required_proofs"])
        self.assertEqual(plan["steps"][1]["proven_by"], "full-survey-20260624-223313")

    def test_survey_all_plan_accepts_short_scan_overrides(self) -> None:
        scene = _scene()

        plan = build_task_plan(
            scene,
            TaskPlanRequest(
                target="survey:all",
                action="survey_all",
                dispatch=True,
                survey_duration_s=3.0,
                survey_omega_rad_s=0.22,
            ),
            now_s=12.0,
        )

        self.assertTrue(plan["request"]["dispatch"])
        self.assertEqual(plan["request"]["survey_duration_s"], 3.0)
        self.assertEqual(plan["request"]["survey_omega_rad_s"], 0.22)
        self.assertAlmostEqual(plan["steps"][1]["duration_s"], 3.0)
        self.assertAlmostEqual(plan["steps"][1]["omega_rad_s"], 0.22)
        self.assertAlmostEqual(plan["steps"][1]["goal"]["duration_s"], 3.0)
        self.assertAlmostEqual(plan["steps"][1]["goal"]["omega_rad_s"], 0.22)

    def test_routine_slot_plan_is_dispatchable_without_scene_map(self) -> None:
        plan = build_task_plan(
            None,
            TaskPlanRequest(target="routine:3", action="brain_self_test", dispatch=True),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "ready")
        self.assertTrue(plan["executable_now"])
        self.assertEqual(plan["request"]["target"], "routine:3")
        self.assertEqual(plan["target"]["slot"], 3)
        self.assertEqual(plan["target"]["name"], "arm_full_cycle")
        self.assertEqual(plan["steps"][0]["type"], "brain_routine")
        self.assertEqual(plan["steps"][0]["cmd"]["cmd"], "routine")
        self.assertEqual(plan["steps"][0]["cmd"]["slot"], 3)
        self.assertTrue(plan["steps"][0]["dispatchable"])

    def test_return_home_plan_dispatches_to_home_tag_alignment(self) -> None:
        plan = build_task_plan(
            _scene_with_home(),
            TaskPlanRequest(
                target="home:tag",
                action="return_home",
                target_distance_m=0.45,
                dispatch=True,
            ),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "ready")
        self.assertTrue(plan["executable_now"])
        self.assertEqual(plan["request"]["target"], "home:tag")
        self.assertEqual(plan["target"]["type"], "home")
        self.assertEqual(plan["target"]["home_tag_id"], 2)
        self.assertEqual(plan["target"]["strategy"], "align_to_home_tag")
        self.assertEqual(plan["steps"][0]["type"], "capture_home_anchor_snapshot")
        self.assertEqual(plan["steps"][1]["type"], "align_to_tag")
        self.assertEqual(plan["steps"][1]["purpose"], "return_home")
        self.assertTrue(plan["steps"][1]["dispatchable"])
        self.assertEqual(plan["steps"][1]["goal"]["tag_id"], 2)
        self.assertEqual(plan["steps"][1]["goal"]["target_distance_m"], 0.45)
        self.assertIn("home_tag_visible", plan["steps"][1]["required_proofs"])
        self.assertEqual(plan["steps"][2]["type"], "confirm_home_stop")

    def test_return_home_plan_accepts_explicit_home_tag_id(self) -> None:
        plan = build_task_plan(
            _scene_with_home(),
            TaskPlanRequest(target="home:2", action="return_home"),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["target"]["home_tag_id"], 2)
        self.assertEqual(plan["steps"][1]["goal"]["tag_id"], 2)

    def test_return_home_blocks_when_home_tag_is_not_visible(self) -> None:
        plan = build_task_plan(
            _scene(),
            TaskPlanRequest(target="home:tag", action="return_home"),
            now_s=12.0,
        )

        self.assertEqual(plan["status"], "blocked")
        self.assertFalse(plan["executable_now"])
        self.assertEqual(plan["blocked_reason"], "home_tag_not_in_scene")
        self.assertEqual(plan["target"]["type"], "home")
        self.assertEqual(plan["target"]["home_tag_id"], 2)
        self.assertEqual(plan["steps"], [])

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


def _scene_with_home() -> SceneMap:
    return SceneMap(
        frame_id="map",
        stamp_s=1.0,
        map_from_camera=Pose2D(0.0, 0.0, 0.0),
        map_from_robot=Pose2D(0.0, 0.0, 0.0),
        tags={
            0: Pose2D(1.0, 0.0, 0.0),
            2: Pose2D(0.25, 0.25, 1.57079632679),
        },
        objects=[],
        anchor_tag_ids=[0, 1, 2],
        observed_tag_ids=[0, 2],
    )


if __name__ == "__main__":
    unittest.main()
