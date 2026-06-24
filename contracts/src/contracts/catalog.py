"""Generate the committed parts catalog data document from the vocabulary.

`make catalog` invokes this as the single generator: it writes
`contracts/parts_catalog.json` directly (mirrors `schema.py` — a registry plus
`write_text`, NO stdout redirect). The six axis arrays are materialized from the
`contracts.vocabulary` enum members (their values, in declared order) so the file
can never drift from the vocabulary; the payload also carries `schema_version`
and the machine-readable `constraints` block (D4).

`parts_catalog.json` is a DATA document at the contracts root — NOT a JSON
Schema. No schema is emitted for `PartsCatalog` and `schema.py` is untouched (D5).
"""

from __future__ import annotations

import json
from pathlib import Path

from contracts.parts_catalog import CatalogConstraints, PartsCatalog
from contracts.vocabulary import (
    ArmGearRatio,
    ArmPosition,
    Cartridge,
    EndEffector,
    MotorAllocation,
    WheelConfig,
)


def _build_catalog() -> PartsCatalog:
    """Materialize the catalog from the vocabulary enum members (declared order)."""
    return PartsCatalog(
        motor_allocation=list(MotorAllocation),
        arm_position=list(ArmPosition),
        end_effector=list(EndEffector),
        wheel_config=list(WheelConfig),
        arm_gear_ratio=list(ArmGearRatio),
        cartridge=list(Cartridge),
        constraints=CatalogConstraints(),
    )


def _render(catalog: PartsCatalog) -> str:
    return json.dumps(catalog.model_dump(mode="json"), indent=2, sort_keys=True)


def main() -> None:
    contracts_root = Path(__file__).resolve().parents[2]
    (contracts_root / "parts_catalog.json").write_text(_render(_build_catalog()) + "\n")


if __name__ == "__main__":
    main()
