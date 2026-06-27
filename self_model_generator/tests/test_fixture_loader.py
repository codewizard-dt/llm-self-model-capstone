from __future__ import annotations

import importlib
import math
import sys
from pathlib import Path
from types import ModuleType

from contracts import ContractLine

REPO_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_MODULE_PREFIXES = (
    "rclpy",
    "rosbag2_py",
    "mcap",
    "camera_ros",
    "picamera2",
    "serial",
)
FORBIDDEN_ROBOT_PATH_PARTS = (("robot", "ros2-runtime"),)


def _forbidden_loaded_modules() -> set[str]:
    return {
        name
        for name in sys.modules
        if any(
            name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_MODULE_PREFIXES
        )
    }


def _module_file(module: ModuleType) -> Path | None:
    module_file = getattr(module, "__file__", None)
    if not module_file:
        return None
    return Path(module_file).resolve()


def _forbidden_robot_runtime_modules() -> set[str]:
    loaded_paths: set[str] = set()
    for module in sys.modules.values():
        module_path = _module_file(module)
        if module_path is None:
            continue
        path_parts = module_path.parts
        for forbidden_parts in FORBIDDEN_ROBOT_PATH_PARTS:
            if all(part in path_parts for part in forbidden_parts):
                loaded_paths.add(str(module_path))
    return loaded_paths


def test_fixture_loader_import_and_load_do_not_pull_hardware_modules() -> None:
    modules_before = _forbidden_loaded_modules()
    robot_paths_before = _forbidden_robot_runtime_modules()

    fixture_loader = importlib.import_module("self_model_generator.fixture_loader")
    lines = fixture_loader.load_fixture_contract_lines(repo_root=REPO_ROOT)

    assert lines
    assert _forbidden_loaded_modules() == modules_before
    assert _forbidden_robot_runtime_modules() == robot_paths_before


def test_fixture_loader_validates_contract_lines() -> None:
    fixture_loader = importlib.import_module("self_model_generator.fixture_loader")

    path = fixture_loader.fixture_evidence_path(repo_root=REPO_ROOT)
    lines = fixture_loader.load_fixture_contract_lines(repo_root=REPO_ROOT)

    assert path == REPO_ROOT / "telemetry-fixtures" / "grab-align-baseline" / "contract.jsonl"
    assert all(isinstance(line, ContractLine) for line in lines)


def test_loaded_evidence_exposes_downstream_fields_without_reshaping() -> None:
    fixture_loader = importlib.import_module("self_model_generator.fixture_loader")

    line = fixture_loader.load_fixture_contract_lines(repo_root=REPO_ROOT)[0]

    assert line.task == "grab_align"
    assert line.predicted
    assert line.gap
    assert line.outcome is not None
    assert line.motor_samples
    assert hasattr(line, "vision")


def test_loaded_fixture_contains_finite_numeric_gap_residual() -> None:
    fixture_loader = importlib.import_module("self_model_generator.fixture_loader")

    lines = fixture_loader.load_fixture_contract_lines(repo_root=REPO_ROOT)
    gap_values = [value for line in lines for value in line.gap.values()]

    assert any(math.isfinite(value) for value in gap_values)
