import json
import pathlib
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIXTURES = HERE.parent / "fixtures"
ROS_RUNTIME_SRC = ROOT / "robot" / "ros2-runtime" / "src"

sys.path.insert(0, str(ROS_RUNTIME_SRC))

from vexy_ros.operator.core import (  # noqa: E402
    parse_operator_method_plan,
    validate_contract_line_shape,
)


def test_align_each_apriltag_once_contract_is_valid() -> None:
    contract = json.loads((FIXTURES / "contract_align_each_apriltag_once.json").read_text())

    validate_contract_line_shape(contract)

    assert contract["task"] == "align_each_apriltag_once"
    assert contract["predicted"]["visited_tag_ids"] == [0, 1, 2]
    assert contract["predicted"]["target_distance_m"] == 0.3048


def test_align_each_apriltag_once_outline_visits_each_tag_with_12_in_standoff() -> None:
    outline = json.loads((FIXTURES / "outline_align_each_apriltag_once.json").read_text())

    plan = parse_operator_method_plan(outline)

    assert [call[0] for call in plan] == [
        "locate_nearest_apriltag",
        "orient_to_tag",
        "move_to_tag",
        "orient_to_tag",
        "move_to_tag",
        "orient_to_tag",
        "move_to_tag",
    ]
    assert [(call[0], call[1][0]) for call in plan if call[0] != "locate_nearest_apriltag"] == [
        ("orient_to_tag", 0),
        ("move_to_tag", 0),
        ("orient_to_tag", 1),
        ("move_to_tag", 1),
        ("orient_to_tag", 2),
        ("move_to_tag", 2),
    ]
    assert [call[2]["target_distance_m"] for call in plan if call[0] == "move_to_tag"] == [
        0.3048,
        0.3048,
        0.3048,
    ]
