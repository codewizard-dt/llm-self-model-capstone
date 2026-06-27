"""Demo perception profile for multi-object scene modeling.

This includes the normal Vexy stack, enables the lightweight HSV yellow-ball
detector, raises the detection cap for multi-ball scenes, and leaves YOLO off.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    main_launch = PathJoinSubstitution(
        [FindPackageShare("vexy_ros"), "launch", "vexy.launch.py"]
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument("yellow_ball_max_detections", default_value="20"),
            DeclareLaunchArgument("yellow_ball_max_hz", default_value="8.0"),
            DeclareLaunchArgument("object_track_min_hits", default_value="2"),
            DeclareLaunchArgument("floor_projection_enabled", default_value="false"),
            DeclareLaunchArgument("camera_height_m", default_value="0.0"),
            DeclareLaunchArgument("camera_pitch_rad", default_value="0.0"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(main_launch),
                launch_arguments={
                    "yolo_enabled": "false",
                    "yellow_ball_detector_enabled": "true",
                    "yellow_ball_max_detections": LaunchConfiguration(
                        "yellow_ball_max_detections"
                    ),
                    "yellow_ball_max_hz": LaunchConfiguration("yellow_ball_max_hz"),
                    "object_track_min_hits": LaunchConfiguration(
                        "object_track_min_hits"
                    ),
                    "floor_projection_enabled": LaunchConfiguration(
                        "floor_projection_enabled"
                    ),
                    "camera_height_m": LaunchConfiguration("camera_height_m"),
                    "camera_pitch_rad": LaunchConfiguration("camera_pitch_rad"),
                }.items(),
            ),
        ]
    )
