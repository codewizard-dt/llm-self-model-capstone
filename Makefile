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
# operator:    $(MAKE) -C operator           validate / test / lint
# coprocessor: $(MAKE) -C robot/pi-runtime   validate / test / lint
# brain:       $(MAKE) -C robot/v5-brain     validate / test / lint
# pilot:       $(MAKE) -C pilot              validate / test / lint
