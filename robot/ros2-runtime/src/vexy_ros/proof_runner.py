from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from .operator_run_capture import (
    BAG_TOPICS,
    start_operator_run_capture,
    stop_operator_run_capture,
    telemetry_bag_record_cmd as _telemetry_bag_record_cmd,
)

TELEMETRY_TOPICS = BAG_TOPICS
telemetry_bag_record_cmd = _telemetry_bag_record_cmd


def default_proof_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"/home/vexy/telemetry/run-{stamp}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run calibrated tag-action proof with JSON telemetry and ContractLine export."
    )
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--mode", default="visual-one-foot-scan")
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--settle-before-s", type=float, default=2.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    proof_dir = args.proof_dir or default_proof_dir()
    proof_dir.mkdir(parents=True, exist_ok=True)
    (proof_dir / "proof-dir.txt").write_text(str(proof_dir) + "\n")

    capture_processes: list[subprocess.Popen] = []
    try:
        capture_processes = start_operator_run_capture(proof_dir)
        time.sleep(max(0.0, args.settle_before_s))

        proof_cmd = [
            "ros2",
            "run",
            "vexy_ros",
            "vexy_tag_action_proof",
            "--mode",
            args.mode,
            "--summary-out",
            str(proof_dir / "summary.json"),
        ]
        with (proof_dir / "tag-action.log").open("w") as log:
            result = subprocess.run(proof_cmd, stdout=log, stderr=subprocess.STDOUT)
        (proof_dir / "proof-rc.txt").write_text(f"proof_rc={result.returncode}\n")
        return_code = result.returncode
    finally:
        stop_operator_run_capture(capture_processes)

    if not args.no_export:
        with (proof_dir / "export.log").open("w") as log:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "vexy_ros.evidence_export",
                    "--proof-dir",
                    str(proof_dir),
                    "--out",
                    str(proof_dir / "contract.jsonl"),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
            )

    print(proof_dir)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
