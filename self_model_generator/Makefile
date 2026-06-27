.PHONY: sync test validate lint

UV := PYTHONPATH=src:../contracts/src:../robot/ros2-runtime/src uv run

sync:
	uv sync

test:
	$(UV) pytest tests/ -v

validate:
	$(UV) python -m self_model_generator.validate
	$(UV) python -c "from self_model_generator.fixture_loader import main; raise SystemExit(main())"

lint:
	$(UV) ruff check src/ tests/
	$(UV) ruff format --check src/ tests/
