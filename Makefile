PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
INVENTORY ?= inventory/home.env

.PHONY: setup check help install list status remove update

setup:
	python3 -m venv .venv
	$(PIP) install -r requirements.txt

check:
	$(PYTHON) -m compileall cloak_manager.py cloak_manager
	$(PYTHON) cloak_manager.py --help

help:
	$(PYTHON) cloak_manager.py --help

install:
	$(PYTHON) cloak_manager.py install $(INVENTORY)

list:
	$(PYTHON) cloak_manager.py list $(INVENTORY)

status:
	$(PYTHON) cloak_manager.py status $(INVENTORY)

remove:
	$(PYTHON) cloak_manager.py remove $(INVENTORY)

update:
	$(PYTHON) cloak_manager.py update $(INVENTORY)
