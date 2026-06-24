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
  align_to_tag  — bounded local-control skill for visible AprilTag alignment
                  Subscribes: /align_to_tag/goal, /apriltag/detections, /vex/ack, /vex/bridge_status
                  Publishes: /vex/cmd, /align_to_tag/feedback, /align_to_tag/result
  vex_bridge       — USB serial bridge to V5 Brain
                     Subscribes: /vex/cmd
                     Publishes:  /vex/ack, /vex/telemetry, /vex/bridge_status
  foxglove_bridge  — WebSocket bridge for Foxglove Studio
                     Connect at: ws://<Pi-IP>:8765

Usage:
  ros2 launch vexy_ros vexy.launch.py
  ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1
  ros2 launch vexy_ros vexy.launch.py camera_width:=1280 camera_height:=720
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    TextSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


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
    width = _as_int(context, "camera_width")
    height = _as_int(context, "camera_height")
    fps = _as_int(context, "camera_fps")
    frame_duration_us = int(round(1_000_000 / fps))
    camera_info_url = LaunchConfiguration("camera_info_url").perform(context)
    if not camera_info_url:
        raise RuntimeError(
            "camera_info_url is required for rectification/tag-pose proof; "
            "use a URL such as file:///home/vexy/ros2_ws/src/vexy_ros/config/imx708_wide_640x480.yaml"
        )
    if "://" not in camera_info_url:
        raise RuntimeError("camera_info_url must be a URL, not a plain filesystem path")

    camera_frame_id = LaunchConfiguration("camera_frame_id").perform(context)
    apriltag_config = LaunchConfiguration("apriltag_config").perform(context)
    workspace_map_path = LaunchConfiguration("workspace_map_path").perform(context)
    camera_in_robot_json = LaunchConfiguration("camera_in_robot_json").perform(context)

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
                }
            ],
        ),
        # ----------------------------------------------------------
        # Bounded local-control skill for tag alignment.
        # ----------------------------------------------------------
        Node(
            package="vexy_ros",
            executable="align_to_tag_node",
            name="align_to_tag",
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
                }
            ],
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
            DeclareLaunchArgument("camera_width", default_value="640"),
            DeclareLaunchArgument("camera_height", default_value="480"),
            DeclareLaunchArgument("camera_fps", default_value="15"),
            DeclareLaunchArgument(
                "camera_frame_id", default_value="camera_optical_frame"
            ),
            DeclareLaunchArgument(
                "camera_info_url",
                default_value=[
                    TextSubstitution(text="file://"),
                    package_config,
                    TextSubstitution(text="/imx708_wide_640x480.yaml"),
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
                "workspace_map_path",
                default_value=[
                    package_config,
                    TextSubstitution(text="/maps/table-grab-toss-v1.json"),
                ],
            ),
            DeclareLaunchArgument(
                "camera_in_robot_json",
                default_value='{"x_m":0.0,"y_m":0.0,"yaw_rad":0.0}',
            ),
            OpaqueFunction(function=_launch_nodes),
        ]
    )
