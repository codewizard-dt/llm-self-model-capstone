"""Print the ContractLine JSON Schema."""

from __future__ import annotations

import json

from contracts.contract_line import ContractLine


def main() -> None:
    print(json.dumps(ContractLine.model_json_schema(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
