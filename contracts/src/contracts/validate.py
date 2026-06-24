"""make validate — parse the contracts fixtures against their frozen models.

``validate.py`` lives at ``contracts/src/contracts/validate.py``; its grandparent
(``parents[2]``) is the contracts root where ``fixtures/`` and ``parts_catalog.json``
live (DEC-VALIDATE-PATH). Four dispatches run over that one contracts root:

* ``session_*.jsonl`` → ``ContractLine`` — every non-blank line is validated; a failure
  is reported as ``name:lineno: error`` on stderr. The glob is narrowed to the
  ``session_*.jsonl`` family (D15) so the F19 ``control_command_*.jsonl`` family can
  live in the same directory without falling into this loop; behavioral no-op for the
  committed fixtures (only ``session_example.jsonl`` matches today).
* ``self_model_*.json`` → ``SelfModel`` — each whole-file JSON document is validated;
  a failure is reported as ``name: error`` on stderr (single-document files, no lineno).
* ``parts_catalog.json`` → ``PartsCatalog`` (F3) — the catalog round-trips against the
  model (a failure is reported as ``parts_catalog.json: error``), and each
  ``self_model_*.json`` fixture's ``config`` is asserted buildable via
  ``validate_config`` (a non-buildable fixture is reported as
  ``name: not buildable — <messages>``). A missing ``parts_catalog.json`` is skipped,
  consistent with an absent fixtures dir.
* ``control_command_*.jsonl`` → ``ControlLine`` | ``AckLine`` (F19) — every non-blank
  line is JSON-parsed, then routed by the closed ``type`` discriminator (D2/D16):
  ``type == "ack"`` → ``AckLine.model_validate``; otherwise →
  ``TypeAdapter(ControlLine).validate_python`` (which sub-routes ``type ∈ {cmd,
  heartbeat}`` and, for ``cmd`` lines, sub-discriminates by the inner ``cmd`` verb).
  A failure is reported as ``name:lineno: error`` on stderr.

Any failure on any dispatch exits 1; otherwise an OK line is printed and the
process exits 0. An empty or absent fixtures dir still exits 0.
"""

import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

from contracts import AckLine, ContractLine, ControlLine, PartsCatalog, SelfModel, validate_config

# Build the ControlLine TypeAdapter once at import time (D16). ControlLine is a
# discriminated-union *type alias* (Annotated[Union[...], Discriminator(...)]),
# not a BaseModel subclass — so `.model_validate` is unavailable and a TypeAdapter
# is the canonical pydantic-v2 entry point.
_control_line_adapter: TypeAdapter[ControlLine] = TypeAdapter(ControlLine)


def main() -> int:
    contracts_root = Path(__file__).resolve().parents[2]
    fixtures_dir = contracts_root / "fixtures"
    errors: list[str] = []
    fixtures = sorted(fixtures_dir.glob("session_*.jsonl")) if fixtures_dir.is_dir() else []
    for path in fixtures:
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line:
                continue
            try:
                ContractLine.model_validate_json(line)
            except Exception as exc:  # noqa: BLE001 — collect every line's failure
                errors.append(f"{path.name}:{lineno}: {exc}")
    self_models = sorted(fixtures_dir.glob("self_model_*.json")) if fixtures_dir.is_dir() else []
    for path in self_models:
        try:
            SelfModel.model_validate_json(path.read_text())
        except Exception as exc:  # noqa: BLE001 — collect every fixture's failure
            errors.append(f"{path.name}: {exc}")

    # F3 third dispatch (additive): round-trip parts_catalog.json against
    # PartsCatalog, then assert each self_model_*.json fixture's config is
    # buildable. A missing parts_catalog.json is skipped, consistent with an
    # absent fixtures dir.
    catalog_path = contracts_root / "parts_catalog.json"
    if catalog_path.is_file():
        try:
            PartsCatalog.model_validate_json(catalog_path.read_text())
        except Exception as exc:  # noqa: BLE001 — surface the catalog parse/validation failure
            errors.append(f"parts_catalog.json: {exc}")
        for path in self_models:
            try:
                model = SelfModel.model_validate_json(path.read_text())
            except Exception:  # noqa: BLE001 — already reported by the F2 dispatch above
                continue
            verdict = validate_config(model.config)
            if not verdict.buildable:
                reasons = "; ".join(v.message for v in verdict.violations)
                errors.append(f"{path.name}: not buildable — {reasons}")

    # F19 fourth dispatch (additive): control_command_*.jsonl is per-line routed
    # by the closed `type` discriminator (D2/D16). `type == "ack"` lines validate
    # against AckLine; every other line validates against ControlLine (which
    # itself sub-routes `type ∈ {cmd, heartbeat}` and, for cmd lines, the inner
    # `cmd` verb discriminator).
    control_fixtures = (
        sorted(fixtures_dir.glob("control_command_*.jsonl")) if fixtures_dir.is_dir() else []
    )
    for path in control_fixtures:
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and obj.get("type") == "ack":
                    AckLine.model_validate(obj)
                else:
                    _control_line_adapter.validate_python(obj)
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
