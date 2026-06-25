from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.vision_map import (
    ObjectObservation,
    Pose2D,
    TagAnchor,
    TagDetection2D,
    build_scene_map,
    camera_from_apriltag_translation,
    parse_tag_anchors,
    pose_from_mapping,
    robot_from_camera_pose,
    tag_id_from_frame_id,
)


class VisionMapTests(unittest.TestCase):
    def test_estimates_camera_and_robot_pose_from_anchor_tag(self) -> None:
        map_from_camera = Pose2D(1.0, 2.0, 0.2)
        camera_in_robot = Pose2D(0.10, 0.0, 0.0)
        map_from_tag = Pose2D(1.5, 2.2, 0.25)
        camera_from_tag = map_from_camera.inverse().compose(map_from_tag)

        scene = build_scene_map(
            anchors={0: TagAnchor(0, map_from_tag)},
            detections=[TagDetection2D(0, camera_from_tag, stamp_s=10.0)],
            camera_in_robot=camera_in_robot,
        )

        self.assertAlmostEqual(scene.map_from_camera.x_m, 1.0, places=6)
        self.assertAlmostEqual(scene.map_from_camera.y_m, 2.0, places=6)
        self.assertAlmostEqual(
            scene.map_from_robot.x_m, 1.0 - 0.10 * math.cos(0.2), places=6
        )
        self.assertEqual(scene.anchor_tag_ids, [0])
        self.assertEqual(scene.observed_tag_ids, [0])

    def test_maps_indicated_objects_into_scene_coordinates(self) -> None:
        scene = build_scene_map(
            anchors={0: TagAnchor(0, Pose2D(2.0, 0.0, 0.0))},
            detections=[TagDetection2D(0, Pose2D(1.0, 0.0, 0.0), stamp_s=10.0)],
            object_observations=[
                ObjectObservation(
                    "red_block",
                    Pose2D(0.5, -0.2, 0.0),
                    stamp_s=10.0,
                    confidence=0.9,
                )
            ],
        )

        self.assertEqual(scene.objects[0].name, "red_block")
        self.assertAlmostEqual(scene.objects[0].map_from_object.x_m, 1.5)
        self.assertAlmostEqual(scene.objects[0].map_from_object.y_m, -0.2)

    def test_converts_ros_optical_translation_to_planar_camera_pose(self) -> None:
        pose = camera_from_apriltag_translation(optical_x_m=0.25, optical_z_m=1.2)

        self.assertEqual(pose.x_m, 1.2)
        self.assertEqual(pose.y_m, -0.25)

    def test_robot_from_camera_pose_applies_measured_camera_offset(self) -> None:
        camera_from_tag = Pose2D(1.2, -0.25, 0.0)
        camera_in_robot = Pose2D(0.10, 0.04, 0.0)

        robot_from_tag = robot_from_camera_pose(camera_from_tag, camera_in_robot)

        self.assertAlmostEqual(robot_from_tag.x_m, 1.3)
        self.assertAlmostEqual(robot_from_tag.y_m, -0.21)

    def test_parses_apriltag_tf_frame_id(self) -> None:
        self.assertEqual(tag_id_from_frame_id("tag36h11_0"), 0)
        self.assertEqual(tag_id_from_frame_id("/tag36h11_12"), 12)
        self.assertEqual(tag_id_from_frame_id("tag_3"), 3)
        self.assertIsNone(tag_id_from_frame_id("camera_optical_frame"))

    def test_parse_tag_anchors_accepts_json_map(self) -> None:
        anchors = parse_tag_anchors('{"0":{"x_m":1.0,"y_m":2.0,"yaw_rad":0.3}}')

        self.assertEqual(anchors[0].map_from_tag, Pose2D(1.0, 2.0, 0.3))

    def test_parse_workspace_map_format_from_wiki_reference(self) -> None:
        anchors = parse_tag_anchors(
            '{"tags":[{"id":0,"role":"bin","pose":{"x_mm":1800,"y_mm":750,"heading_deg":180}}]}'
        )

        self.assertEqual(anchors[0].label, "bin")
        self.assertAlmostEqual(anchors[0].map_from_tag.x_m, 1.8)
        self.assertAlmostEqual(anchors[0].map_from_tag.y_m, 0.75)
        self.assertAlmostEqual(anchors[0].map_from_tag.yaw_rad, math.pi)

    def test_parse_gen0_workspace_map_from_current_pr(self) -> None:
        raw = (
            Path(__file__).resolve().parents[1]
            / "config"
            / "maps"
            / "gen0-grab-toss-v1.json"
        ).read_text()

        anchors = parse_tag_anchors(raw)

        self.assertEqual(sorted(anchors), [0, 1, 2])
        self.assertEqual(anchors[0].label, "bin")
        self.assertAlmostEqual(anchors[0].map_from_tag.x_m, 0.813)
        self.assertAlmostEqual(anchors[1].map_from_tag.y_m, 1.473)
        self.assertAlmostEqual(anchors[2].map_from_tag.yaw_rad, 3 * math.pi / 2)

    def test_pose_json_emits_wiki_mm_fields_and_ros_meter_fields(self) -> None:
        payload = Pose2D(1.5, 0.25, math.pi / 2).to_json()

        self.assertEqual(payload["x_m"], 1.5)
        self.assertEqual(payload["x_mm"], 1500.0)
        self.assertEqual(payload["heading_deg"], 90.0)
        self.assertEqual(pose_from_mapping(payload), Pose2D(1.5, 0.25, math.pi / 2))


if __name__ == "__main__":
    unittest.main()
