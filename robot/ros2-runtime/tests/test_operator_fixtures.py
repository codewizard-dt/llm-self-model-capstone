import json
import pathlib
import os
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REPO_ROOT = HERE.parents[2]
FIXTURES = HERE.parent / "fixtures"
ROS_RUNTIME_SRC = ROOT / "robot" / "ros2-runtime" / "src"

sys.path.insert(0, str(ROS_RUNTIME_SRC))
sys.path.insert(0, str(REPO_ROOT / "contracts" / "src"))

from contracts.task_envelope import TaskEnvelope  # noqa: E402
from vexy_ros.operator._core import (  # noqa: E402
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


def test_deliver_ball_task_fixture_embeds_contract_and_outline() -> None:
    contract = json.loads((FIXTURES / "contract_deliver_ball.json").read_text())
    outline = json.loads((FIXTURES / "outline_deliver_ball.json").read_text())
    task = json.loads((FIXTURES / "task_deliver_ball.json").read_text())

    assert task == {"contract": contract, "outline": outline}
    envelope = TaskEnvelope.model_validate(task)
    assert envelope.contract.session_id == "stub-deliver-ball-gen0"
    assert [call[0] for call in envelope.outline.method_plan()] == [
        "grab",
        "locate_nearest_apriltag",
        "move_to_tag",
        "pickup_ball",
        "move_to_tag",
        "lift",
        "release",
    ]


def test_send_task_script_sends_deliver_ball_fixture_with_vexy_env(tmp_path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.log"
    for name in ("ssh", "scp"):
        tool = bin_dir / name
        tool.write_text(
            "#!/usr/bin/env bash\n"
            f"printf '{name} ' >> {log}\n"
            f"printf '%q ' \"$@\" >> {log}\n"
            f"printf '\\n' >> {log}\n"
        )
        tool.chmod(0o755)
    sshpass = bin_dir / "sshpass"
    sshpass.write_text(
        "#!/usr/bin/env bash\n"
        f"printf 'sshpass ' >> {log}\n"
        f"printf '%q ' \"$@\" >> {log}\n"
        f"printf '\\n' >> {log}\n"
        "shift 2\n"
        '"$@"\n'
    )
    sshpass.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "VEXY_HOST": "vexy.local",
            "VEXY_SSH_USER": "vexy",
            "VEXY_SSH_PW": "vexytime",
        }
    )

    result = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "send_task_to_pi.sh"),
            str(FIXTURES / "task_deliver_ball.json"),
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    calls = log.read_text()
    assert "sshpass -p vexytime ssh vexy@vexy.local" in calls
    assert "sshpass -p vexytime scp" in calls
    assert str(FIXTURES / "task_deliver_ball.json") in calls
    assert "vexy@vexy.local:/vexy/tasks/inbox/task_deliver_ball.json" in calls
