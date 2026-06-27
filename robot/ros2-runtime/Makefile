.PHONY: sync validate test lint import-smoke

sync:
	uv sync --locked --dev

validate:
	uv run pytest tests/test_operator_fixtures.py

test:
	uv run pytest tests

lint:
	uv run ruff check .
	uv run ruff format --check .

import-smoke:
	uv run python -c "import pydantic, contracts, vexy_ros; import vexy_ros.operator._core"
