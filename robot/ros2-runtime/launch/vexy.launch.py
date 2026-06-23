"""
Main launch file for the vexy coprocessor stack on ROS 2 Jazzy.

Nodes launched:
  camera_node   — Camera Module 3 via camera_ros (RPi libcamera fork)
                  Publishes: /camera/image_raw, /camera/camera_info
  vex_bridge       — USB serial bridge to V5 Brain
                     Subscribes: /vex/cmd
                     Publishes:  /vex/telemetry
  foxglove_bridge  — WebSocket bridge for Foxglove Studio
                     Connect at: ws://<Pi-IP>:8765

Usage:
  ros2 launch vexy_ros vexy.launch.py
  ros2 launch vexy_ros vexy.launch.py serial_port:=/dev/ttyACM1
  ros2 launch vexy_ros vexy.launch.py camera_width:=1280 camera_height:=720
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
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

            # ----------------------------------------------------------
            # Camera Module 3 via camera_ros (requires RPi libcamera fork)
            # Publishes /camera/image_raw @ camera_fps Hz
            # ----------------------------------------------------------
            Node(
                package="camera_ros",
                executable="camera_node",
                name="camera",
                parameters=[
                    {
                        "width": LaunchConfiguration("camera_width"),
                        "height": LaunchConfiguration("camera_height"),
                        "fps": LaunchConfiguration("camera_fps"),
                    }
                ],
                remappings=[
                    ("~/image_raw", "/camera/image_raw"),
                    ("~/camera_info", "/camera/camera_info"),
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
    )
