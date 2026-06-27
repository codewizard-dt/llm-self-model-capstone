---
topic: "$research How to fix this pidentic error once and for all."
slug: pydantic-dependency-fix
researched: 2026-06-27
---

# Primary Sources — Pydantic Dependency Fix

| ID | Type | Locator | Accessed | What it contributed |
|---|---|---:|---|---|
| S1 | codebase | `contracts/pyproject.toml` | 2026-06-27 | `contracts` declares Python `>=3.12,<3.13` and runtime dependencies `pydantic>=2.12,<3` and `reactivex>=4.1.0`. |
| S2 | codebase | `robot/ros2-runtime/pyproject.toml` | 2026-06-27 | ROS runtime declares `contracts`, `pydantic>=2.12,<3`, and a `uv` editable source for `contracts`, but also sets `tool.uv.package = false`. |
| S3 | codebase | `robot/ros2-runtime/src/vexy_ros/operator/node.py` | 2026-06-27 | The operator node imports `contracts.task_envelope.TaskEnvelope` and `pydantic.ValidationError`. |
| S4 | codebase | `robot/ros2-runtime/setup.py` | 2026-06-27 | The ament/setuptools package installs `vexy_ros` and console scripts, but currently lacks `install_requires`. |
| S5 | codebase | `robot/ros2-runtime/package.xml` | 2026-06-27 | ROS package metadata declares `python3-pydantic` as an `exec_depend`. |
| S6 | codebase | `robot/ros2-runtime/tests/test_operator_fixtures.py` | 2026-06-27 | The fixture test computes a broken `ROS_RUNTIME_SRC` path by adding `robot/ros2-runtime/src` below an already nested `robot` path. |
| S7 | codebase | `Makefile` | 2026-06-27 | Root `test`/`lint` do not delegate into `robot/ros2-runtime`; `rebuild-pi` manually installs Pydantic and editable `contracts`. |
| S8 | context7 | `/astral-sh/uv` — project packaging query | 2026-06-27 | `tool.uv.package = false` prevents a project package from being built and installed. |
| S9 | context7 | `/pypa/setuptools` — dependency metadata query | 2026-06-27 | Setuptools dependencies should be declared with `install_requires` or declarative `project.dependencies`; dynamic metadata needs explicit configuration. |
| S10 | command | `cd robot/ros2-runtime && uv run python -c 'import pydantic'` | 2026-06-27 | The ROS vertical environment can import Pydantic 2.13.4. |
| S11 | command | `uv run python -c 'import pydantic'` from repo root | 2026-06-27 | The repo-root `uv run` environment cannot import Pydantic. |
| S12 | command | `cd robot/ros2-runtime && uv run python -c 'import vexy_ros'` | 2026-06-27 | The ROS vertical `uv` environment cannot import `vexy_ros` as an installed package while `package = false` is set. |
| S13 | command | `cd robot/ros2-runtime && uv run pytest tests/test_operator.py` | 2026-06-27 | `test_operator.py` passes from the vertical environment. |
| S14 | command | `cd robot/ros2-runtime && uv run pytest tests/test_operator_fixtures.py` | 2026-06-27 | Fixture test fails on `ModuleNotFoundError: No module named 'vexy_ros'`, showing the path/package issue separate from Pydantic. |
| S15 | codebase | `AGENTS.md` | 2026-06-27 | Repo guide requires `uv` for deps/envs and `ruff` for lint/format. |

## Excerpts

### S1 — contracts dependency metadata

`contracts/pyproject.toml`

> requires-python = ">=3.12,<3.13"
> dependencies = [
>     "pydantic>=2.12,<3",
>     "reactivex>=4.1.0",
> ]

### S2 — ROS runtime dependency metadata

`robot/ros2-runtime/pyproject.toml`

> dependencies = [
>     "contracts",
>     "numpy>=2.2,<3",
>     "opencv-python-headless>=4.12,<5",
>     "pydantic>=2.12,<3",
>     "pyserial>=3.5,<4",
> ]
> [tool.uv]
> package = false
> [tool.uv.sources]
> contracts = { path = "../../contracts", editable = true }

### S3 — operator node imports

`robot/ros2-runtime/src/vexy_ros/operator/node.py`

> from contracts.task_envelope import TaskEnvelope
> from pydantic import ValidationError

### S4 — current ROS setup.py shape

`robot/ros2-runtime/setup.py`

> packages=find_packages(where="src"),
> package_dir={"": "src"},
> entry_points={
>     "console_scripts": [
>         "vexy_operator_node = vexy_ros.operator.node:main",

### S5 — ROS package dependency

`robot/ros2-runtime/package.xml`

> <exec_depend>python3-pydantic</exec_depend>

### S6 — broken fixture-test path

`robot/ros2-runtime/tests/test_operator_fixtures.py`

> HERE = pathlib.Path(__file__).resolve().parent
> ROOT = HERE.parent.parent
> ROS_RUNTIME_SRC = ROOT / "robot" / "ros2-runtime" / "src"

### S7 — root Makefile behavior

`Makefile`

> test:
> 	$(MAKE) -C contracts test
> 	$(MAKE) -C self_model_generator test
>
> rebuild-pi:
> 	pip install --break-system-packages "pydantic>=2,<3"
> 	pip install --break-system-packages -e contracts/

### S8 — uv package setting

Context7 source: `https://github.com/astral-sh/uv/blob/main/docs/concepts/projects/config.md`

> Setting `tool.uv.package = false` prevents a project package from being built and installed, even if a build system is declared, though explicit `uv build` commands are still respected.

### S9 — setuptools dependency metadata

Context7 source: `https://github.com/pypa/setuptools/blob/main/docs/userguide/quickstart.rst`

> Declare project dependencies in setup.py. These will be automatically installed with your package.

Context7 source: `https://context7.com/pypa/setuptools/llms.txt`

> Defines required and optional dependency groups for a project using the pyproject.toml file.

### S10 — Pydantic imports in vertical uv env

Command output:

> /Users/davidtaylor/Repositories/gauntlet/capstone/robot/ros2-runtime/.venv/bin/python3
> 2.13.4

### S11 — Pydantic missing from repo-root uv env

Command output:

> ModuleNotFoundError: No module named 'pydantic'
> /opt/homebrew/Caskroom/miniforge/base/bin/python3

### S12 — vexy_ros missing from vertical uv env

Command output:

> ModuleNotFoundError: No module named 'vexy_ros'

### S13 — operator tests pass from vertical env

Command output:

> tests/test_operator.py .........................................         [100%]
> 41 passed

### S14 — fixture tests fail from vertical env

Command output:

> ModuleNotFoundError: No module named 'vexy_ros'

### S15 — repo toolchain rule

`AGENTS.md`

> Toolchain is non-negotiable: **`uv`** for deps/envs, **`ruff`** for lint/format
