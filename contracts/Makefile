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
