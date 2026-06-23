#!/usr/bin/env bash
# Run this script on the Raspberry Pi after Ubuntu 24.04 + ROS 2 Jazzy are installed.
# It builds the RPi libcamera fork + camera_ros, then builds vexy_ros.
#
# Usage (on Pi, after cloning the repo):
#   bash robot/ros2-runtime/scripts/setup_pi.sh
set -euo pipefail

ROS_DISTRO=jazzy
WS=~/ros2_ws

echo "=== [1/6] Installing system dependencies ==="
sudo apt-get update -qq
sudo apt-get install -y \
    python3-meson meson ninja-build \
    libssl-dev libgnutls28-dev libboost-dev \
    libglib2.0-dev libpython3-dev pybind11-dev \
    python3-yaml python3-ply \
    libevent-dev libdrm-dev libjpeg-dev \
    libdw-dev libudev-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    libcamera-dev libyaml-dev \
    python3-rosdep

echo "=== [2/6] Installing colcon-meson ==="
pip install colcon-meson --break-system-packages

echo "=== [3/6] Creating ROS 2 workspace ==="
mkdir -p "$WS/src"
cd "$WS/src"

if [ ! -d libcamera ]; then
    echo "  Cloning RPi libcamera fork (IMX708 support) ..."
    git clone --depth=1 https://github.com/raspberrypi/libcamera.git
else
    echo "  libcamera already present, pulling ..."
    git -C libcamera pull --ff-only
fi

if [ ! -d camera_ros ]; then
    echo "  Cloning camera_ros ..."
    git clone --depth=1 https://github.com/christianrauch/camera_ros.git
else
    echo "  camera_ros already present, pulling ..."
    git -C camera_ros pull --ff-only
fi

# Symlink vexy_ros package from this repo
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
if [ ! -L vexy_ros ]; then
    ln -s "$REPO_ROOT/robot/ros2-runtime" vexy_ros
    echo "  Linked vexy_ros → $REPO_ROOT/robot/ros2-runtime"
fi

echo "=== [4/6] Running rosdep ==="
cd "$WS"
source "/opt/ros/$ROS_DISTRO/setup.bash"

if ! [ -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init
fi
rosdep update --include-eol-distros -q
rosdep install --from-paths src --ignore-src -y --skip-keys=libcamera

echo "=== [5/6] Building workspace (libcamera fork + camera_ros + vexy_ros) ==="
colcon build \
    --packages-select libcamera camera_ros vexy_ros \
    --cmake-args -DCMAKE_BUILD_TYPE=Release \
    --event-handlers console_direct+

echo "=== [6/6] Sourcing workspace ==="
source "$WS/install/setup.bash"

echo ""
echo "Build complete! To verify the camera:"
echo "  source ~/ros2_ws/install/setup.bash"
echo "  ros2 run camera_ros camera_node &"
echo "  ros2 topic hz /camera/image_raw"
echo ""
echo "To launch the full stack:"
echo "  ros2 launch vexy_ros vexy.launch.py"
