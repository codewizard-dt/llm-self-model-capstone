# Delegate to per-vertical Makefiles. Add a vertical's target once its Makefile exists.
.PHONY: sync validate test lint schema schema-check catalog catalog-check m1 m1-judge

# m1 contracts-frozen milestone gate (delegates into contracts/).
m1:
	$(MAKE) -C contracts m1

m1-judge:
	$(MAKE) -C contracts m1-judge

sync:
	$(MAKE) -C contracts sync
	$(MAKE) -C operator sync

validate:
	$(MAKE) -C contracts validate
	$(MAKE) -C operator validate

test:
	$(MAKE) -C contracts test
	$(MAKE) -C operator test

lint:
	$(MAKE) -C contracts lint
	$(MAKE) -C operator lint

schema:
	$(MAKE) -C contracts schema

schema-check:
	$(MAKE) -C contracts schema-check

catalog:
	$(MAKE) -C contracts catalog

catalog-check:
	$(MAKE) -C contracts catalog-check

# Stubs — filled in by later features
# operator:    $(MAKE) -C operator           sync / validate / test / lint
# coprocessor: $(MAKE) -C robot/pi-runtime   sync / validate / test / lint
# brain:       $(MAKE) -C robot/v5-brain     sync / validate / test / lint
# pilot:       $(MAKE) -C pilot              sync / validate / test / lint
