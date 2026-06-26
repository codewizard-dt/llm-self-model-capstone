.PHONY: sync test validate lint

UV := PYTHONPATH=src:../contracts/src uv run --project ../contracts

sync:
	uv sync --project ../contracts

test:
	$(UV) pytest tests/ -v

validate:
	$(UV) python -c "from self_model_operator.fixture_loader import main; raise SystemExit(main())"

lint:
	$(UV) ruff check src/ tests/
	$(UV) ruff format --check src/ tests/
