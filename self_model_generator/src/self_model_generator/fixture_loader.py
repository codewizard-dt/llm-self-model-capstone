"""Load committed telemetry fixtures as contract-validated downstream evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from contracts import ContractLine

DEFAULT_RUN_ID = "grab-align-baseline"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def fixture_evidence_path(run_id: str = DEFAULT_RUN_ID, *, repo_root: Path | None = None) -> Path:
    """Return the canonical ContractLine JSONL evidence path for a telemetry fixture run."""
    if not run_id:
        raise ValueError("run_id must be non-empty")

    root = repo_root if repo_root is not None else _default_repo_root()
    return root / "telemetry-fixtures" / run_id / "contract.jsonl"


def load_contract_jsonl(path: Path) -> list[ContractLine]:
    """Validate every non-empty JSONL record at path as a ContractLine."""
    lines: list[ContractLine] = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        record = raw_line.strip()
        if not record:
            continue

        try:
            lines.append(ContractLine.model_validate_json(record))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: invalid ContractLine record") from exc

    if not lines:
        raise ValueError(f"{path}: no ContractLine records found")

    return lines


def load_fixture_contract_lines(
    run_id: str = DEFAULT_RUN_ID, *, repo_root: Path | None = None
) -> list[ContractLine]:
    """Load a fixture run's canonical downstream evidence as ContractLine records."""
    return load_contract_jsonl(fixture_evidence_path(run_id, repo_root=repo_root))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    args = parser.parse_args(argv)

    path = fixture_evidence_path(args.run_id)
    lines = load_contract_jsonl(path)
    print(f"validated {len(lines)} ContractLine record(s) from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
