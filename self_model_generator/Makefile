.PHONY: sync test validate lint

UV := PYTHONPATH=src:../contracts/src:../robot/ros2-runtime/src uv run
SELF_MODEL ?= ../contracts/fixtures/self_model_gen0.json
PARTS_CATALOG ?= ../contracts/parts_catalog.json
OUT_DIR ?= /tmp/vexy-full-loop-latest
PROVENANCE ?= live
TAG_ID ?= 0
TARGET_DISTANCE_M ?= 0.45
PICKUP_DURATION_MS ?= 700

LOOP_ARGS = --self-model "$(SELF_MODEL)" --parts-catalog "$(PARTS_CATALOG)" --contract-jsonl "$(CONTRACT_JSONL)" --out-dir "$(OUT_DIR)" --provenance "$(PROVENANCE)" --tag-id "$(TAG_ID)" --target-distance-m "$(TARGET_DISTANCE_M)" --pickup-duration-ms "$(PICKUP_DURATION_MS)"
ifneq ($(strip $(RUN_ID)),)
LOOP_ARGS += --expected-run-id "$(RUN_ID)"
endif
ifneq ($(strip $(SESSION_ID)),)
LOOP_ARGS += --expected-session-id "$(SESSION_ID)"
endif

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

loop:
	@test -n "$(CONTRACT_JSONL)" || (echo "usage: make loop CONTRACT_JSONL=path/to/contract.jsonl OUT_DIR=/tmp/vexy-loop [PROVENANCE=live] [RUN_ID=run-id] [SESSION_ID=session-id]" >&2; exit 2)
	$(UV) python -m self_model_generator.loop_runner $(LOOP_ARGS)
