.PHONY: sync test validate lint schema schema-check catalog catalog-check

UV := uv run

sync:
	uv sync

test:
	$(UV) pytest tests/ -v

validate:
	$(UV) python -m contracts.validate

lint:
	$(UV) ruff check src/ tests/
	$(UV) ruff format --check src/ tests/

schema:
	$(UV) python -m contracts.schema

schema-check: schema
	git diff --exit-code schemas/

catalog:
	$(UV) python -m contracts.catalog

catalog-check: catalog
	git diff --exit-code parts_catalog.json
