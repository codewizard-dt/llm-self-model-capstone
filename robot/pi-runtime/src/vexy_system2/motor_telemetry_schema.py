"""Print the motor telemetry contract JSON Schema."""

from __future__ import annotations

import json

from vexy_system2.contracts.motor_telemetry import motor_telemetry_json_schema


def main() -> None:
    print(json.dumps(motor_telemetry_json_schema(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

