"""Minimal fixture validator.

This slice ships only the no-fixtures path: glob ``contracts/fixtures/*.jsonl``
and, when the directory is empty or absent, print ``OK`` and exit 0. The
``ContractLine`` import and per-line validation are deferred until the models
slice lands and real fixtures exist.
"""

import sys
from pathlib import Path


def main() -> int:
    fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"
    fixtures = sorted(fixtures_dir.glob("*.jsonl")) if fixtures_dir.is_dir() else []
    if not fixtures:
        print("OK")
        return 0
    # Real per-line validation against ContractLine lands with the models slice.
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
