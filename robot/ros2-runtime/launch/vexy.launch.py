"""
Main launch file for the vexy coprocessor stack on ROS 2 Jazzy.

Nodes launched:
  camera_node   — Camera Module 3 via camera_ros (RPi libcamera fork)
                  Publishes: /camera/image_raw, /camera/camera_info
  camera_rectify — image_proc rectification
                  Publishes: /camera/image_rect
  apriltag      — AprilTag 36h11 detector over rectified camera stream
                  Publishes: /apriltag/detections, /tf
  scene_map     — AprilTag detections + workspace map → robot/object map coordinates
                  Publishes: /vision/scene_map
  yolo_ncnn     — optional YOLO NCNN object detector over rectified camera frames
                  Publishes: /vision/object_detections
  yellow_ball_detector — lightweight HSV yellow ball detector
                         Publishes: /vision/object_detections
  object_indication — object boxes + CameraInfo → camera-relative object indications
                      Publishes: /vision/object_indications
  object_track   — object indications → stable object tracks
                   Publishes: /vision/object_tracks
  agent_scene    — compact LLM-facing scene summary
                   Publishes: /vision/agent_scene
  object_overlay — rectified camera image + object boxes → annotated debug image
                   Publishes: /vision/object_overlay
  task_plan     — scene map + target request → bounded tag/object task plan
                  Publishes: /task_plan/current
  vexy_operator — sole runtime command authority for bounded robot interaction
                  Subscribes: /operator/command, /tf, /vex/ack, /vex/telemetry, /vex/bridge_status
                  Publishes: /vex/cmd, /operator/status, /operator/events, /operator/results
  vex_bridge       — USB serial bridge to V5 Brain
                     Subscribes: /vex/cmd
                     Publishes:  /vex/ack, /vex/telemetry, /vex/bridge_status
  telemetry_writer — always-on JSONL recorder for operator topics
                     Writes: /home/vexy/telemetry/run-<timestamp>/
  foxglove_bridge  — WebSocket bridge for Foxglove Studio
                     Connect at: ws://<Pi-IP>:8765

Usage:
  ros2 launch vexy_ros vexy.launch.py
  ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1
  ros2 launch vexy_ros vexy.launch.py camera_width:=1280 camera_height:=720
"""

from datetime import datetime
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
    TextSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from vexy_ros.proof_runner import telemetry_bag_record_cmd
from vexy_ros.vision_map import DEFAULT_CAMERA_IN_ROBOT

DEFAULT_OPERATOR_TASK_CONTRACT = (
    '{"schema_version":"1.0","session_id":"operator-runtime",'
    '"generation":0,"round":0,"task":"runtime_operator",'
    '"motor_samples":[{"device":"left_drive"}],'
    '"predicted":{"success":true},"gap":{"distance_error_m":0.0}}'
)
DEFAULT_OPERATOR_TASK_OUTLINE = (
    '[["locate_nearest_apriltag",[]],["orient_to_tag",[0]],'
    '["move_to_tag",[0],{"target_distance_m":0.45}],'
    '["pickup_ball",[]],["arm",[]],["grab",[]],["lift",[]],["release",[]]]'
)


def _as_int(context, name):
    value = LaunchConfiguration(name).perform(context)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {value!r}") from exc
    if parsed <= 0:
        raise RuntimeError(f"{name} must be positive, got {parsed}")
    return parsed


def _launch_nodes(context, *args, **kwargs):
    telemetry_dir = "/home/vexy/telemetry/run-" + datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    width = _as_int(context, "camera_width")
    height = _as_int(context, "camera_height")
    fps = _as_int(context, "camera_fps")
    frame_duration_us = int(round(1_000_000 / fps))
    camera_info_url = LaunchConfiguration("camera_info_url").perform(context)
    if not camera_info_url:
        raise RuntimeError(
            "camera_info_url is required for rectification/tag-pose proof; "
            "use a URL such as file:///home/vexy/ros2_ws/src/vexy_ros/config/imx708_wide_640x360.yaml"
        )
    if "://" not in camera_info_url:
        raise RuntimeError("camera_info_url must be a URL, not a plain filesystem path")

    camera_frame_id = LaunchConfiguration("camera_frame_id").perform(context)
    apriltag_config = LaunchConfiguration("apriltag_config").perform(context)
    workspace_map_path = LaunchConfiguration("workspace_map_path").perform(context)
    workspace_map_name = LaunchConfiguration("workspace_map_name").perform(context)
    if not workspace_map_path:
        if "/" in workspace_map_name or "\\" in workspace_map_name:
            raise RuntimeError(
                "workspace_map_name must be a map id; use workspace_map_path for paths"
            )
        map_filename = (
            workspace_map_name
            if workspace_map_name.endswith(".json")
            else f"{workspace_map_name}.json"
        )
        map_path = (
            Path(get_package_share_directory("vexy_ros"))
            / "config"
            / "maps"
            / map_filename
        )
        if not map_path.exists():
            raise RuntimeError(f"workspace map does not exist: {map_path}")
        workspace_map_path = str(map_path)
    camera_in_robot_json = LaunchConfiguration("camera_in_robot_json").perform(context)
    object_dimensions_json = LaunchConfiguration("object_dimensions_json").perform(
        context
    )

    return [
        # ----------------------------------------------------------
        # Camera Module 3 via camera_ros (requires RPi libcamera fork)
        # Publishes /camera/image_raw and /camera/camera_info
        # ----------------------------------------------------------
        Node(
            package="camera_ros",
            executable="camera_node",
            name="camera",
            parameters=[
                {
                    "width": width,
                    "height": height,
                    "frame_id": camera_frame_id,
                    "camera_info_url": camera_info_url,
                    "FrameDurationLimits": [frame_duration_us, frame_duration_us],
                }
            ],
            remappings=[
                ("~/image_raw", "/camera/image_raw"),
                ("~/camera_info", "/camera/camera_info"),
            ],
        ),
        # ----------------------------------------------------------
        # Rectify raw camera frames using calibrated CameraInfo.
        # ----------------------------------------------------------
        Node(
            package="image_proc",
            executable="rectify_node",
            name="camera_rectify",
            remappings=[
                ("image", "/camera/image_raw"),
                ("camera_info", "/camera/camera_info"),
                ("image_rect", "/camera/image_rect"),
            ],
        ),
        # ----------------------------------------------------------
        # AprilTag detector over rectified frames.
        # ----------------------------------------------------------
        Node(
            package="apriltag_ros",
            executable="apriltag_node",
            name="apriltag",
            parameters=[apriltag_config],
            remappings=[
                ("image_rect", "/camera/image_rect"),
                ("camera_info", "/camera/camera_info"),
                ("detections", "/apriltag/detections"),
            ],
        ),
        # ----------------------------------------------------------
        # Scene map: fixed AprilTag anchors + current detections into
        # workspace coordinates. The default map follows
        # wiki/knowledge/concepts/apriltag-workspace-layout.md and
        # wiki/knowledge/sources/apriltag-larger-workspace-map.md.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="scene_map_node",
            name="scene_map",
            parameters=[
                {
                    "workspace_map_path": workspace_map_path,
                    "map_frame": "map",
                    "camera_in_robot_json": camera_in_robot_json,
                    "publish_hz": LaunchConfiguration("scene_map_publish_hz"),
                    "tag_max_age_s": LaunchConfiguration("scene_map_tag_max_age_s"),
                }
            ],
        ),
        # ----------------------------------------------------------
        # Optional YOLO NCNN object detector. Disabled by default so
        # camera/tag/bridge proof still runs on Pis before model install.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="yolo_ncnn_node",
            name="yolo_ncnn",
            condition=IfCondition(LaunchConfiguration("yolo_enabled")),
            parameters=[
                {
                    "model_path": LaunchConfiguration("yolo_model_path"),
                    "confidence_threshold": LaunchConfiguration("yolo_confidence"),
                    "nms_iou_threshold": LaunchConfiguration("yolo_nms_iou"),
                    "max_hz": LaunchConfiguration("yolo_max_hz"),
                    "classes_json": LaunchConfiguration("yolo_classes_json"),
                    "class_names_json": LaunchConfiguration("yolo_class_names_json"),
                    "input_size": LaunchConfiguration("yolo_input_size"),
                    "input_name": LaunchConfiguration("yolo_input_name"),
                    "output_name": LaunchConfiguration("yolo_output_name"),
                }
            ],
        ),
        # ----------------------------------------------------------
        # Lightweight color detector for the yellow ball. This runs
        # without a trained NCNN model and feeds the same detection path.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="yellow_ball_detector_node",
            name="yellow_ball_detector",
            condition=IfCondition(LaunchConfiguration("yellow_ball_detector_enabled")),
            parameters=[
                {
                    "max_hz": LaunchConfiguration("yellow_ball_max_hz"),
                    "min_area_px": LaunchConfiguration("yellow_ball_min_area_px"),
                    "min_circularity": LaunchConfiguration(
                        "yellow_ball_min_circularity"
                    ),
                    "max_detections": LaunchConfiguration("yellow_ball_max_detections"),
                    "h_min": LaunchConfiguration("yellow_ball_h_min"),
                    "s_min": LaunchConfiguration("yellow_ball_s_min"),
                    "v_min": LaunchConfiguration("yellow_ball_v_min"),
                    "h_max": LaunchConfiguration("yellow_ball_h_max"),
                    "s_max": LaunchConfiguration("yellow_ball_s_max"),
                    "v_max": LaunchConfiguration("yellow_ball_v_max"),
                    "label": "yellow_ball",
                }
            ],
        ),
        # ----------------------------------------------------------
        # Object projection into the existing scene-map input.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="object_indication_node",
            name="object_indication",
            parameters=[
                {
                    "object_dimensions_json": object_dimensions_json,
                    "default_height_m": LaunchConfiguration("default_object_height_m"),
                    "min_confidence": LaunchConfiguration("object_min_confidence"),
                    "floor_projection_enabled": LaunchConfiguration(
                        "floor_projection_enabled"
                    ),
                    "camera_height_m": LaunchConfiguration("camera_height_m"),
                    "camera_pitch_rad": LaunchConfiguration("camera_pitch_rad"),
                }
            ],
        ),
        # ----------------------------------------------------------
        # Stable object tracks with candidate/confirmed/stale states.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="object_track_node",
            name="object_track",
            parameters=[
                {
                    "min_hits": LaunchConfiguration("object_track_min_hits"),
                    "association_gate_m": LaunchConfiguration(
                        "object_track_association_gate_m"
                    ),
                    "stale_after_s": LaunchConfiguration("object_track_stale_after_s"),
                    "expire_after_s": LaunchConfiguration(
                        "object_track_expire_after_s"
                    ),
                    "publish_hz": LaunchConfiguration("object_track_publish_hz"),
                }
            ],
        ),
        # ----------------------------------------------------------
        # LLM-facing compact scene contract. No raw images.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="agent_scene_node",
            name="agent_scene",
            parameters=[
                {
                    "publish_hz": LaunchConfiguration("agent_scene_publish_hz"),
                    "include_debug_tracks": LaunchConfiguration(
                        "agent_scene_include_debug_tracks"
                    ),
                }
            ],
        ),
        # ----------------------------------------------------------
        # Annotated image stream for Foxglove's Image panel.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="object_overlay_node",
            name="object_overlay",
            condition=IfCondition(LaunchConfiguration("object_overlay_enabled")),
            parameters=[
                {
                    "max_detection_age_s": LaunchConfiguration(
                        "object_overlay_max_detection_age_s"
                    ),
                }
            ],
        ),
        # ----------------------------------------------------------
        # Dynamic task planner for tag/object/survey targets. It publishes
        # plans only; Operator owns dispatch and all /vex/cmd writes.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="task_plan_node",
            name="task_plan",
        ),
        # ----------------------------------------------------------
        # Sole production runtime command authority.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="vexy_operator_node",
            name="vexy_operator",
            parameters=[
                {
                    "workspace_map_path": workspace_map_path,
                    "camera_in_robot_json": camera_in_robot_json,
                    "task_contract_json": DEFAULT_OPERATOR_TASK_CONTRACT,
                    "task_outline_json": DEFAULT_OPERATOR_TASK_OUTLINE,
                    "brain_program_slot": LaunchConfiguration("brain_program_slot"),
                    "require_brain_program_ready": LaunchConfiguration(
                        "require_brain_program_ready"
                    ),
                }
            ],
        ),
        # ----------------------------------------------------------
        # VEX V5 serial bridge
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="vex_bridge_node",
            name="vex_bridge",
            parameters=[
                {
                    "serial_port": LaunchConfiguration("serial_port"),
                    "baud_rate": LaunchConfiguration("baud_rate"),
                    "brain_program_slot": LaunchConfiguration("brain_program_slot"),
                    "brain_program_start_command": LaunchConfiguration(
                        "brain_program_start_command"
                    ),
                    "brain_program_start_timeout_s": LaunchConfiguration(
                        "brain_program_start_timeout_s"
                    ),
                    "brain_program_start_settle_s": LaunchConfiguration(
                        "brain_program_start_settle_s"
                    ),
                }
            ],
        ),
        # ----------------------------------------------------------
        # Always-on telemetry recorder — writes operator topics as
        # JSONL to /home/vexy/telemetry/run-<timestamp>/ so every
        # test and live run is captured for make sync-telemetry.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="vexy_telemetry_writer_node",
            name="telemetry_writer",
            arguments=["--out-dir", telemetry_dir],
            condition=IfCondition(LaunchConfiguration("telemetry_writer_enabled")),
        ),
        # ----------------------------------------------------------
        # Foxglove Studio WebSocket bridge
        # Connect from browser: ws://<Pi-IP>:8765
        # Note: use IP address, not vexy.local — mDNS fails for
        # browser WebSocket even when SSH works fine.
        # ----------------------------------------------------------
        Node(
            package="foxglove_bridge",
            executable="foxglove_bridge",
            name="foxglove_bridge",
            parameters=[{"port": 8765}],
        ),
        # ----------------------------------------------------------
        # MCAP bag recorder — records operator and VEX telemetry topics
        # alongside the live JSONL writer so each run has both formats.
        # ----------------------------------------------------------
        *(
            [
                ExecuteProcess(
                    cmd=telemetry_bag_record_cmd(telemetry_dir + "/bag"),
                )
            ]
            if LaunchConfiguration("bag_record_enabled").perform(context).lower()
            == "true"
            else []
        ),
    ]


def generate_launch_description():
    package_config = PathJoinSubstitution([FindPackageShare("vexy_ros"), "config"])
    return LaunchDescription(
        [
            # ----------------------------------------------------------
            # Launch arguments
            # ----------------------------------------------------------
            DeclareLaunchArgument("serial_port", default_value="auto"),
            DeclareLaunchArgument("baud_rate", default_value="115200"),
            DeclareLaunchArgument("brain_program_slot", default_value="8"),
            DeclareLaunchArgument("require_brain_program_ready", default_value="true"),
            DeclareLaunchArgument(
                "brain_program_start_command",
                default_value="pros v5 run {slot}",
            ),
            DeclareLaunchArgument("brain_program_start_timeout_s", default_value="8.0"),
            DeclareLaunchArgument("brain_program_start_settle_s", default_value="2.0"),
            DeclareLaunchArgument("camera_width", default_value="640"),
            DeclareLaunchArgument("camera_height", default_value="360"),
            DeclareLaunchArgument("camera_fps", default_value="5"),
            DeclareLaunchArgument(
                "camera_frame_id", default_value="camera_optical_frame"
            ),
            DeclareLaunchArgument(
                "camera_info_url",
                default_value=[
                    TextSubstitution(text="file://"),
                    package_config,
                    TextSubstitution(text="/imx708_wide_640x360.yaml"),
                ],
            ),
            DeclareLaunchArgument(
                "apriltag_config",
                default_value=[
                    package_config,
                    TextSubstitution(text="/apriltag_36h11.yaml"),
                ],
            ),
            DeclareLaunchArgument(
                "workspace_map_name",
                default_value=EnvironmentVariable(
                    "VEXY_MAP", default_value="gen0-grab-toss-v1"
                ),
            ),
            DeclareLaunchArgument(
                "workspace_map_path",
                default_value="",
            ),
            DeclareLaunchArgument(
                "camera_in_robot_json",
                default_value=DEFAULT_CAMERA_IN_ROBOT,
            ),
            DeclareLaunchArgument("scene_map_publish_hz", default_value="3.0"),
            DeclareLaunchArgument("scene_map_tag_max_age_s", default_value="0.75"),
            DeclareLaunchArgument("yolo_enabled", default_value="false"),
            DeclareLaunchArgument(
                "yolo_model_path",
                default_value=EnvironmentVariable("VEXY_YOLO_MODEL", default_value=""),
            ),
            DeclareLaunchArgument("yolo_confidence", default_value="0.35"),
            DeclareLaunchArgument("yolo_nms_iou", default_value="0.45"),
            DeclareLaunchArgument("yolo_max_hz", default_value="5.0"),
            DeclareLaunchArgument("yolo_classes_json", default_value="[]"),
            DeclareLaunchArgument("yolo_class_names_json", default_value="{}"),
            DeclareLaunchArgument("yolo_input_size", default_value="640"),
            DeclareLaunchArgument("yolo_input_name", default_value=""),
            DeclareLaunchArgument("yolo_output_name", default_value=""),
            DeclareLaunchArgument(
                "yellow_ball_detector_enabled", default_value="false"
            ),
            DeclareLaunchArgument("yellow_ball_max_hz", default_value="5.0"),
            DeclareLaunchArgument("yellow_ball_min_area_px", default_value="200.0"),
            DeclareLaunchArgument("yellow_ball_min_circularity", default_value="0.55"),
            DeclareLaunchArgument("yellow_ball_max_detections", default_value="1"),
            DeclareLaunchArgument("yellow_ball_h_min", default_value="20"),
            DeclareLaunchArgument("yellow_ball_s_min", default_value="80"),
            DeclareLaunchArgument("yellow_ball_v_min", default_value="100"),
            DeclareLaunchArgument("yellow_ball_h_max", default_value="45"),
            DeclareLaunchArgument("yellow_ball_s_max", default_value="255"),
            DeclareLaunchArgument("yellow_ball_v_max", default_value="255"),
            DeclareLaunchArgument(
                "object_dimensions_json",
                default_value=(
                    '{"*":{"height_m":0.12},"bin":{"height_m":0.20,'
                    '"width_m":0.30},"bottle":{"height_m":0.20,'
                    '"width_m":0.065},"cup":{"height_m":0.12,'
                    '"width_m":0.08},"sports ball":{"diameter_m":0.065},'
                    '"yellow ball":{"diameter_m":0.065},'
                    '"yellow_ball":{"diameter_m":0.065}}'
                ),
            ),
            DeclareLaunchArgument("default_object_height_m", default_value="0.12"),
            DeclareLaunchArgument("object_min_confidence", default_value="0.35"),
            DeclareLaunchArgument("floor_projection_enabled", default_value="false"),
            DeclareLaunchArgument("camera_height_m", default_value="0.0"),
            DeclareLaunchArgument("camera_pitch_rad", default_value="0.0"),
            DeclareLaunchArgument("object_track_min_hits", default_value="3"),
            DeclareLaunchArgument(
                "object_track_association_gate_m", default_value="0.25"
            ),
            DeclareLaunchArgument("object_track_stale_after_s", default_value="0.75"),
            DeclareLaunchArgument("object_track_expire_after_s", default_value="3.0"),
            DeclareLaunchArgument("object_track_publish_hz", default_value="4.0"),
            DeclareLaunchArgument("agent_scene_publish_hz", default_value="3.0"),
            DeclareLaunchArgument(
                "agent_scene_include_debug_tracks", default_value="false"
            ),
            DeclareLaunchArgument("object_overlay_enabled", default_value="true"),
            DeclareLaunchArgument("telemetry_writer_enabled", default_value="true"),
            DeclareLaunchArgument("bag_record_enabled", default_value="true"),
            DeclareLaunchArgument(
                "object_overlay_max_detection_age_s", default_value="0.5"
            ),
            OpaqueFunction(function=_launch_nodes),
        ]
    )
