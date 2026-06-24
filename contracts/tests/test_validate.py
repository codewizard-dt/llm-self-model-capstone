"""Tests for the `contracts.validate` entrypoint — focused on the F3 third dispatch.

The F1 (`*.jsonl → ContractLine`) and F2 (`self_model_*.json → SelfModel`) dispatches
are exercised end-to-end by `make validate` over the committed fixtures; here we cover
the additive F3 dispatch: the `parts_catalog.json` round-trip against `PartsCatalog`,
the per-fixture buildability assertion, and that a non-buildable config makes the
entrypoint exit non-zero with a readable reason. The committed fixtures stay buildable —
the unbuildable case is constructed in a temp fixtures dir, never by mutating a
committed file.
"""

from __future__ import annotations

import json
from pathlib import Path

from contracts import PartsCatalog, SelfModel, validate_config
from contracts.validate import main

# contracts/tests/test_validate.py -> parents[1] is the contracts root.
CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
CATALOG_JSON = CONTRACTS_ROOT / "parts_catalog.json"
FIXTURES_DIR = CONTRACTS_ROOT / "fixtures"


# --- catalog round-trip -----------------------------------------------------


def test_committed_parts_catalog_json_validates_against_model():
    catalog = PartsCatalog.model_validate_json(CATALOG_JSON.read_text())
    assert catalog.schema_version == "1.0"


# --- committed fixtures are buildable through the validate path --------------


def test_committed_self_model_fixtures_report_buildable():
    fixtures = sorted(FIXTURES_DIR.glob("self_model_*.json"))
    assert fixtures, "expected committed self_model_*.json fixtures"
    for path in fixtures:
        model = SelfModel.model_validate_json(path.read_text())
        verdict = validate_config(model.config)
        assert verdict.buildable is True, f"{path.name} should be buildable"


def test_validate_entrypoint_exits_zero_over_committed_tree():
    # The real contracts tree: F1 jsonl + F2 self-models + the F3 catalog/buildability
    # dispatch all pass against the committed fixtures.
    assert main() == 0


# --- unbuildable fixture is rejected with a readable reason ------------------


def _write_self_model(path: Path, config: dict) -> None:
    base = json.loads((FIXTURES_DIR / "self_model_gen0.json").read_text())
    base["config"] = config
    path.write_text(json.dumps(base))


def test_unbuildable_fixture_makes_entrypoint_exit_nonzero(tmp_path, monkeypatch, capsys):
    # Stand up a temp contracts root: copy the committed catalog, and add an
    # unbuildable fixture (flywheel + 200rpm cartridge violates FLYWHEEL_CARTRIDGE).
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (tmp_path / "parts_catalog.json").write_text(CATALOG_JSON.read_text())
    unbuildable = json.loads((FIXTURES_DIR / "self_model_gen0.json").read_text())["config"]
    unbuildable["motor_allocation"] = "2drive+1flywheel"
    unbuildable["end_effector"] = "flywheel"
    unbuildable["cartridge"] = "200rpm"
    _write_self_model(fixtures / "self_model_bad.json", unbuildable)

    # Sanity: the constructed config really is unbuildable.
    bad_model = SelfModel.model_validate_json((fixtures / "self_model_bad.json").read_text())
    assert validate_config(bad_model.config).buildable is False

    # Redirect the entrypoint at the temp root by pointing parents[2] resolution there.
    monkeypatch.setattr(
        "contracts.validate.Path",
        _PathStub(tmp_path / "src" / "contracts" / "validate.py"),
    )

    assert main() == 1
    err = capsys.readouterr().err
    assert "self_model_bad.json" in err
    assert "not buildable" in err
    assert "600rpm" in err  # the flywheel-cartridge violation message


class _PathStub:
    """Make `Path(__file__)` resolve to a chosen path inside the entrypoint only.

    `validate.main` computes its contracts root as `Path(__file__).resolve().parents[2]`.
    We swap in a Path whose `parents[2]` is the temp root, while leaving every other
    `Path(...)` call (the glob/read_text on real sub-paths) behaving normally.
    """

    def __init__(self, fake_file: Path) -> None:
        self._fake_file = fake_file

    def __call__(self, arg):
        # The entrypoint's only `Path(__file__)` call — return the fake file path.
        return self._fake_file
