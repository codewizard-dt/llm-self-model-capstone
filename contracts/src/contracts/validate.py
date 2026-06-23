"""make validate — parse every line in contracts/fixtures/*.jsonl against ContractLine.

``validate.py`` lives at ``contracts/src/contracts/validate.py``; its grandparent
(``parents[2]``) is the contracts root where ``fixtures/`` lives (DEC-VALIDATE-PATH).
For each ``*.jsonl`` fixture, every non-blank line is validated against
``ContractLine``. Any failure is reported as ``name:lineno: error`` on stderr and
exits 1; otherwise an OK line is printed and the process exits 0. An empty or
absent fixtures dir still exits 0.
"""

import sys
from pathlib import Path

from contracts import ContractLine


def main() -> int:
    fixtures_dir = Path(__file__).resolve().parents[2] / "fixtures"
    errors: list[str] = []
    fixtures = sorted(fixtures_dir.glob("*.jsonl")) if fixtures_dir.is_dir() else []
    for path in fixtures:
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line:
                continue
            try:
                ContractLine.model_validate_json(line)
            except Exception as exc:  # noqa: BLE001 — collect every line's failure
                errors.append(f"{path.name}:{lineno}: {exc}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK — all fixtures valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
