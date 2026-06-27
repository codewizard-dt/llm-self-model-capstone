# Delegate to per-vertical Makefiles. Add a vertical's target once its Makefile exists.
.PHONY: sync validate test lint schema schema-check catalog catalog-check m1 m1-judge send-task rebuild-pi sync-pi
PI_REPO ?= ~/llm-self-model-capstone
PI_ROS_WS ?= ~/ros2_ws

# m1 contracts-frozen milestone gate (delegates into contracts/).
m1:
	$(MAKE) -C contracts m1

m1-judge:
	$(MAKE) -C contracts m1-judge

sync:
	$(MAKE) -C contracts sync
	$(MAKE) -C self_model_generator sync
	$(MAKE) -C robot/ros2-runtime sync

validate:
	$(MAKE) -C contracts validate
	$(MAKE) -C self_model_generator validate
	$(MAKE) -C robot/ros2-runtime validate

test:
	$(MAKE) -C contracts test
	$(MAKE) -C self_model_generator test
	$(MAKE) -C robot/ros2-runtime test

lint:
	$(MAKE) -C contracts lint
	$(MAKE) -C self_model_generator lint
	$(MAKE) -C robot/ros2-runtime lint

schema:
	$(MAKE) -C contracts schema

schema-check:
	$(MAKE) -C contracts schema-check

catalog:
	$(MAKE) -C contracts catalog

catalog-check:
	$(MAKE) -C contracts catalog-check

sync-telemetry:
	bash scripts/sync_telemetry.sh

send-task:
	@test -n "$(FILE)" || (echo "usage: make send-task FILE=path/to/task.json" >&2; exit 2)
	bash scripts/send_task_to_pi.sh "$(FILE)"

sync-pi:
	bash scripts/sync_pi_runtime.sh

rebuild-pi:
	pip uninstall --break-system-packages -y vexy-ros || true
	pip install --break-system-packages "pydantic>=2,<3"
	pip install --break-system-packages -e contracts/
	bash -c "cd $(PI_REPO) && source /opt/ros/jazzy/setup.bash && colcon --log-base $(PI_ROS_WS)/log build --base-paths robot/ros2-runtime --build-base $(PI_ROS_WS)/build --install-base $(PI_ROS_WS)/install --packages-select vexy_ros --cmake-args -DCMAKE_BUILD_TYPE=Release --event-handlers console_direct+"
	systemctl --user restart vexy-ros-stack.service
	systemctl --user --no-pager --plain status vexy-ros-stack.service

# Stubs — filled in by later features
# brain:       $(MAKE) -C robot/v5-brain     sync / validate / test / lint
# pilot:       $(MAKE) -C pilot              sync / validate / test / lint
