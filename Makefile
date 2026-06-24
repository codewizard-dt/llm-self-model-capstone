# Delegate to per-vertical Makefiles. Add a vertical's target once its Makefile exists.
.PHONY: sync validate test lint schema catalog catalog-check

sync:
	$(MAKE) -C contracts sync

validate:
	$(MAKE) -C contracts validate

test:
	$(MAKE) -C contracts test

lint:
	$(MAKE) -C contracts lint

schema:
	$(MAKE) -C contracts schema

catalog:
	$(MAKE) -C contracts catalog

catalog-check:
	$(MAKE) -C contracts catalog-check

# Stubs — filled in by later features
# operator:    $(MAKE) -C operator           sync / validate / test / lint
# coprocessor: $(MAKE) -C robot/pi-runtime   sync / validate / test / lint
# brain:       $(MAKE) -C robot/v5-brain     sync / validate / test / lint
# pilot:       $(MAKE) -C pilot              sync / validate / test / lint
