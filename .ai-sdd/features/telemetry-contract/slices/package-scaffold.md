# Slice: package-scaffold

| Field | Value |
|---|---|
| Feature | telemetry-contract (F1) |
| Stack | contracts |
| Depends on | — (zero-dependency) |

## What this slice delivers

The `contracts/` Python package skeleton: every file needed for `uv sync` and `make lint` to pass against an empty source tree. No models yet — this is infrastructure only.

## Files to create

```
contracts/
  pyproject.toml          Python 3.12, hatchling build, pydantic v2 >=2.12 <3, pytest dep
  .python-version         3.12
  ruff.toml               line-length=100, target-version=py312, src=["src"]
  Makefile                targets: test, validate, lint, schema (see below)
  src/
    contracts/
      __init__.py         empty — models added in pydantic-models slice
  tests/
      __init__.py         empty
```

Root `Makefile` (repo root — create if absent):

```makefile
# Delegate to per-vertical Makefiles. Add a vertical's target once its Makefile exists.
.PHONY: validate test lint schema

validate:
	$(MAKE) -C contracts validate

test:
	$(MAKE) -C contracts test

lint:
	$(MAKE) -C contracts lint

schema:
	$(MAKE) -C contracts schema

# Stubs — filled in by later features
# operator:  $(MAKE) -C operator  validate / test / lint
# coprocessor: $(MAKE) -C robot/pi-runtime validate / test / lint
# brain:     $(MAKE) -C robot/v5-brain validate / test / lint
# pilot:     $(MAKE) -C pilot validate / test / lint
```

`contracts/Makefile`:

```makefile
.PHONY: test validate lint schema

UV := uv run

test:
	$(UV) pytest tests/ -v

validate:
	$(UV) python -m contracts.validate

lint:
	$(UV) ruff check src/ tests/
	$(UV) ruff format --check src/ tests/

schema:
	$(UV) python -m contracts.schema > schemas/contract_line.json
```

`contracts/pyproject.toml` must include:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "contracts"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.12,<3"]

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.hatch.build.targets.wheel]
packages = ["src/contracts"]

[tool.uv]
dev-dependencies = ["pytest>=8"]
```

## Acceptance

- `cd contracts && uv sync` exits 0
- `cd contracts && make lint` exits 0 (nothing to lint yet; ruff finds no files → exit 0)
- Root `make lint` delegates and exits 0
- `contracts/schemas/` directory exists (empty; populated by pydantic-models slice)
