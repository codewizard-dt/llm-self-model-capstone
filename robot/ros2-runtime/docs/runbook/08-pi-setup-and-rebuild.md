# Pi Setup And Rebuild Model

This page is the source-of-truth for how the Pi runtime is laid out and when to
use the full setup script versus the fast rebuild path.

## Mental Model

`~/llm-self-model-capstone` is the authoritative source checkout.

`~/ros2_ws` is the ROS workspace used for build products, installed overlays,
logs, and lower-level camera dependencies.

For `vexy_ros`, do not treat `~/ros2_ws/src/vexy_ros` as authoritative. The
normal rebuild command reads source from:

```text
~/llm-self-model-capstone/robot/ros2-runtime
```

and writes build/install/log output to:

```text
~/ros2_ws/build
~/ros2_ws/install
~/ros2_ws/log
```

The user systemd service currently runs from the ROS overlay:

```bash
source /opt/ros/jazzy/setup.bash
source /home/vexy/ros2_ws/install/setup.bash
ros2 launch vexy_ros vexy.launch.py ...
```

That is expected. Repo-root source remains authoritative because `make
rebuild-pi` installs repo-root `vexy_ros` into `~/ros2_ws/install`.

## Normal Update: Rebuild `vexy_ros`

Use this after pulling code changes to `robot/ros2-runtime/`, contracts, launch
files, config, or operator behavior.

```bash
cd ~/llm-self-model-capstone
git pull
make rebuild-pi
```

`make rebuild-pi` does the following:

1. Removes any stale pip-installed `vexy-ros` package metadata.
2. Ensures Pydantic is available in the Pi user Python environment.
3. Installs `contracts/` editable from the repo root.
4. Builds only `vexy_ros` with source from `robot/ros2-runtime`.
5. Writes build products into `~/ros2_ws/build`, `~/ros2_ws/install`, and
   `~/ros2_ws/log`.
6. Restarts `vexy-ros-stack.service`.

The important colcon shape is:

```bash
cd ~/llm-self-model-capstone
source /opt/ros/jazzy/setup.bash
colcon --log-base ~/ros2_ws/log build \
  --base-paths robot/ros2-runtime \
  --build-base ~/ros2_ws/build \
  --install-base ~/ros2_ws/install \
  --packages-select vexy_ros \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  --event-handlers console_direct+
```

`--log-base` is a global `colcon` option and must appear before `build`.
`--build-base` and `--install-base` are build-command options and appear after
`build`.

## Full Setup: Bootstrap Camera Dependencies

Use this only for first-time Pi setup, a fresh OS image, a damaged
`~/ros2_ws`, or deliberate camera stack work.

```bash
cd ~/llm-self-model-capstone
bash robot/ros2-runtime/scripts/setup_pi.sh
```

The full setup script does more than `make rebuild-pi`:

- Installs apt packages needed by ROS, libcamera, camera calibration, serial,
  AprilTags, image processing, and Foxglove.
- Adds the user to `video`, `render`, and `dialout`.
- Installs `colcon-meson`, Pydantic, and editable `contracts`.
- Creates `~/ros2_ws/src`.
- Clones or updates Raspberry Pi `libcamera`.
- Clones or updates `camera_ros`.
- Links `~/ros2_ws/src/vexy_ros` to the repo checkout for initial bootstrap.
- Runs `rosdep`.
- Builds `libcamera`, `camera_ros`, and `vexy_ros`.

The full setup can take many minutes because it builds camera dependencies.
The normal `make rebuild-pi` path should take seconds because it builds only
the Python `vexy_ros` package.

## What Can Be Deleted

Safe cleanup for only `vexy_ros` build artifacts:

```bash
rm -rf ~/ros2_ws/build/vexy_ros ~/ros2_ws/install/vexy_ros
cd ~/llm-self-model-capstone
make rebuild-pi
```

Do not casually delete all of `~/ros2_ws`. It may contain `libcamera` and
`camera_ros` source/build/install state created by the full setup script. If
`~/ros2_ws` is deleted, rerun the full setup script before expecting the camera
stack to work.

## Known Non-Fatal Warning

During `colcon build`, this warning can appear:

```text
SetuptoolsWarning: `install_requires` overwritten in `pyproject.toml` (dependencies)
```

This is not a build failure. It means `robot/ros2-runtime/pyproject.toml`
contains PEP 621 dependencies and `setup.py` also contains `install_requires`.
Setuptools chooses the `pyproject.toml` dependency metadata for the generated
package info. The warning should be cleaned up eventually by making one metadata
path authoritative, but it does not block runtime deployment.

## Verify The Active Runtime

After `make rebuild-pi`, verify the package and service:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 pkg prefix vexy_ros
systemctl --user --no-pager --plain status vexy-ros-stack.service
```

Expected package prefix:

```text
/home/vexy/ros2_ws/install/vexy_ros
```

Expected service command includes:

```text
source /home/vexy/ros2_ws/install/setup.bash
```

That is correct: the service runs the `~/ros2_ws/install` overlay, and that
overlay was built from repo-root source by `make rebuild-pi`.

## Troubleshooting

If `make rebuild-pi` still runs `cd ~/ros2_ws`, the Pi has an old root
`Makefile`. Run:

```bash
cd ~/llm-self-model-capstone
git pull
git rev-parse --short HEAD
```

The commit should include the repo-root source rebuild path.

If `colcon` reports:

```text
colcon: error: unrecognized arguments: --log-base ...
```

the Pi has an old `Makefile` with `--log-base` after `build`. Pull latest and
rerun.

If `colcon` reports an `ast.literal_eval` syntax error containing
`SpecifierSet(...)`, `robot/ros2-runtime/pyproject.toml` still has a
colcon-breaking `requires-python` value. Pull latest and confirm that file does
not set `requires-python`.

If Python imports fail at runtime, confirm the service was restarted after the
rebuild:

```bash
systemctl --user restart vexy-ros-stack.service
systemctl --user status vexy-ros-stack.service
```
