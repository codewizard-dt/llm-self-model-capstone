.PHONY: sync test validate lint schema schema-check catalog catalog-check m1 m1-judge

UV := uv run

sync:
	uv sync

test:
	$(UV) pytest tests/ -v

validate:
	$(UV) python -m contracts.validate

lint:
	$(UV) ruff check src/ tests/ scripts/
	$(UV) ruff format --check src/ tests/ scripts/

schema:
	$(UV) python -m contracts.schema

schema-check: schema
	git diff --exit-code schemas/

catalog:
	$(UV) python -m contracts.catalog

catalog-check: catalog
	git diff --exit-code parts_catalog.json

# m1 contracts-frozen gate. Runs the full mechanical floor (every contract loads,
# round-trips, and has not drifted), then the advisory LLM review of the
# irreducibly-human checks. m1-judge never fails the gate (advisory only).
m1: sync lint validate schema-check catalog-check test
	@echo ""
	@echo "================================================================"
	@echo "m1 contracts-frozen — MECHANICAL GATE: PASS"
	@echo "  sync · lint · validate · schema-check · catalog-check · test"
	@echo "  F1 telemetry · F2 self-model · F3 parts-catalog · F4 adapters · F19 control-grammar"
	@echo "================================================================"
	@$(MAKE) m1-judge
	@echo ""
	@echo "Remaining: human freeze sign-off (accept the contracts as frozen)."

m1-judge:
	@$(UV) python scripts/m1_review.py
