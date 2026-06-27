---
topic: "$research How to fix this pidentic error once and for all."
slug: pydantic-dependency-fix
researched: 2026-06-27
sources: [./sources.md]
---

# Research: Pydantic Dependency Fix

> The Pydantic failure is not a Pydantic API problem. It is an environment and packaging-contract problem: running `uv run pytest robot/ros2-runtime/...` from the repo root uses a Python environment that does not know the ROS runtime dependencies, while `robot/ros2-runtime` is marked `tool.uv.package = false`, preventing the local `vexy_ros` package from being installed. Fix it by making the ROS runtime a proper installable `uv`/setuptools project, restoring runtime dependency metadata, fixing one broken test path shim, and adding vertical Makefile targets so test commands always execute inside the ROS runtime environment.

## Research Questions

- Why does `ModuleNotFoundError: No module named 'pydantic'` occur when `robot/ros2-runtime/pyproject.toml` declares `pydantic`?
- Does the ROS runtime environment resolve and install Pydantic correctly when invoked from the vertical?
- Why do some tests still fail from the ROS runtime directory after Pydantic is available?
- Which packaging metadata should be the source of truth for local `uv` tests and ROS/ament runtime installs?
- What repo change prevents this class of error from returning?

## Current State (Codebase)

`contracts` is the real schema package and declares `pydantic>=2.12,<3` in its project dependencies [S1]. The ROS operator imports `contracts.task_envelope` and `pydantic.ValidationError`, so the ROS runtime cannot treat Pydantic as an optional test-only dependency [S3].

`robot/ros2-runtime/pyproject.toml` currently declares `contracts`, `numpy`, `opencv-python-headless`, `pydantic>=2.12,<3`, and `pyserial`; it also maps `contracts` to `../../contracts` as an editable `uv` path source [S2]. However, the same file sets `tool.uv.package = false`, which tells `uv` not to build and install the local `vexy-ros` project [S2][S8].

`robot/ros2-runtime/setup.py` currently installs the `vexy_ros` Python package and console scripts, but the previous `install_requires` metadata is absent [S4]. `package.xml` still has ROS-side runtime dependencies including `python3-pydantic` [S5].

One fixture test has a wrong path shim: `test_operator_fixtures.py` computes `ROOT = HERE.parent.parent`, then constructs `ROOT / "robot" / "ros2-runtime" / "src"`, which becomes a non-existent nested path when the file is already under `robot/ros2-runtime/tests` [S6].

The root `Makefile` does not delegate `test`, `lint`, or `sync` into `robot/ros2-runtime`; the ROS vertical is still listed as a future stub [S7]. This makes it easy to run tests from the wrong environment.

## Key Findings

1. Pydantic is resolved in the ROS runtime environment. `cd robot/ros2-runtime && uv run python -c 'import pydantic'` imported Pydantic 2.13.4 successfully [S10].

2. Running `uv run` from the repo root does not use the ROS runtime project. `uv run python -c 'import pydantic'` from the repo root used a base interpreter and failed with `ModuleNotFoundError` [S11].

3. The ROS runtime local package is not installed into its `uv` environment. `cd robot/ros2-runtime && uv run python -c 'import vexy_ros'` failed with `ModuleNotFoundError`, which matches the documented meaning of `tool.uv.package = false` [S8][S12].

4. `test_operator.py` passes from inside the ROS runtime because it inserts `robot/ros2-runtime/src` and `contracts/src` manually. `test_operator_fixtures.py` fails from the same directory because its path shim is wrong, not because Pydantic is absent [S13][S14].

5. Official packaging docs say setuptools runtime dependencies belong in `install_requires` or declarative `project.dependencies`; if metadata is dynamic, the dynamic fields need explicit configuration [S9]. Keeping dependencies only in a non-installed `pyproject.toml` is not enough for `ament_python`/`setup.py` consumers.

## Constraints

- The repo standard is `uv`, not pip/poetry/black/isort/flake8 [S15].
- The ROS runtime uses `ament_python`, so `setup.py`, `package.xml`, launch/config data files, and console scripts still matter [S4][S5].
- `contracts` is a local vertical with its own Python version bound (`>=3.12,<3.13`) and Pydantic dependency [S1].
- Hardware/Pi rebuilds currently install Pydantic and editable `contracts` manually before `colcon build`, which is a workaround rather than a durable local dev/test contract [S7].

## Solution Comparison

| Criteria | Option A: Just install Pydantic globally | Option B: Only run tests from `robot/ros2-runtime` | Option C: Make ROS runtime installable and delegate commands |
|---|---|---|---|
| Approach | Run `pip install pydantic` or rely on base Python. | Document `cd robot/ros2-runtime && uv run pytest`. | Package the vertical correctly, remove `package = false`, restore metadata, fix tests, add Makefile targets. |
| Pros | Fast immediate unblock. | Uses the existing `uv` lock and dependencies. | Prevents root/vertical drift and validates the package the same way runtime uses it. |
| Cons | Reintroduces hidden global state; fails on another machine. | Still leaves `vexy_ros` uninstalled and path hacks brittle. | Requires a small coordinated packaging cleanup. |
| Complexity | Low | Low | Medium |
| Dependencies | None new | None new | None new |
| Codebase fit | Poor; violates `uv` discipline. | Partial; keeps current vertical model. | Best; matches `uv`, setuptools, and ROS/ament needs. |
| Maintenance | High hidden cost | Medium | Low |

## Recommendation

Use Option C.

Implementation outline:

1. In `robot/ros2-runtime/pyproject.toml`, make the project installable:
   - Add `requires-python = ">=3.12,<3.13"` to match the contracts vertical.
   - Add a setuptools build backend:
     - `[build-system]`
     - `requires = ["setuptools>=61", "wheel"]`
     - `build-backend = "setuptools.build_meta"`
   - Remove `[tool.uv] package = false`.
   - Keep `[tool.uv.sources] contracts = { path = "../../contracts", editable = true }`.

2. Restore runtime dependency metadata in `robot/ros2-runtime/setup.py` or migrate it cleanly into declarative setuptools config. For the smallest ROS-compatible fix, restore:
   - `install_requires=["setuptools", "pydantic>=2.12,<3"]`
   - Keep `package.xml` `python3-pydantic` for ROS system dependency declaration.
   - Do not depend on a PyPI `contracts` package in `setup.py` unless this repo publishes one; local dev should continue to use the `uv` path source, and Pi rebuilds should install `contracts/` explicitly.

3. Fix `robot/ros2-runtime/tests/test_operator_fixtures.py`:
   - Change `ROOT = HERE.parent.parent` to the ROS runtime root (`HERE.parent`), or remove manual `sys.path` insertion once `vexy_ros` is installed by `uv`.
   - Prefer package installation over path mutation for new tests.

4. Add `robot/ros2-runtime/Makefile` with `sync`, `test`, `lint`, and maybe `validate` targets:
   - `sync`: `uv sync --locked --dev`
   - `test`: `uv run pytest tests`
   - `lint`: `uv run ruff check . && uv run ruff format --check .`

5. Wire the root `Makefile` to delegate into `robot/ros2-runtime` so root commands do not accidentally run ROS tests in the wrong environment.

6. Add a regression guard:
   - A test or Makefile smoke target that runs `uv run python -c "import pydantic, contracts, vexy_ros; import vexy_ros.operator.node"` from `robot/ros2-runtime`.

Risk mitigation:

- If `uv sync --locked --dev` changes `uv.lock`, commit that lockfile with the packaging fix.
- If ROS `colcon build` dislikes declarative metadata, keep `setup.py` as the ament entry point and use `pyproject.toml` only to provide build-system/project metadata for `uv`; this is a normal transitional shape for setuptools projects.
- If the Pi system Python has an older `python3-pydantic`, keep the explicit Pi rebuild step installing `pydantic>=2.12,<3` until the runtime image is rebuilt around the pinned package set.

## Next Steps

- Create a task: `/task-add Make robot/ros2-runtime an installable uv/setuptools package and fix Pydantic import drift`
- After implementation, run:
  - `cd robot/ros2-runtime && uv sync --locked --dev`
  - `cd robot/ros2-runtime && uv run pytest tests/test_operator.py tests/test_operator_fixtures.py tests/test_launch_contract.py`
  - `cd robot/ros2-runtime && uv run python -c "import pydantic, contracts, vexy_ros; import vexy_ros.operator.node"`
  - root `make test` after wiring the root Makefile
