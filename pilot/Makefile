.PHONY: sync test validate lint

UV := PYTHONPATH=src:../contracts/src uv run

sync:
	uv sync

test:
	$(UV) pytest tests/ -v

validate:
	$(UV) python -c "import pilot.observation"

lint:
	$(UV) ruff check src/ tests/
	$(UV) ruff format --check src/ tests/
