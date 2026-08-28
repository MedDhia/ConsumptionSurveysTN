PYTHON ?= python3
export PYTHONPATH := src

.PHONY: help setup fetch build verify test docs all clean

help:
	@echo "setup   install bsdtar, pdftotext and the Python requirements"
	@echo "fetch   download the 21 INS artefacts into data/raw (~86 MB)"
	@echo "build   build every dataset into data/processed and write codebooks"
	@echo "verify  re-check data/raw against data/raw/manifest.json"
	@echo "test    reproduce INS's published figures from the microdata"
	@echo "docs    regenerate docs/SOURCES.md from the manifest"
	@echo "all     fetch, build, docs, test"

setup:
	./scripts/setup.sh

fetch:
	$(PYTHON) -m consumptiontn.cli fetch

build:
	$(PYTHON) -m consumptiontn.cli build

verify:
	$(PYTHON) -m consumptiontn.cli verify

test:
	$(PYTHON) -m pytest tests

docs:
	$(PYTHON) scripts/write_sources_doc.py

all: fetch build docs test

clean:
	rm -rf data/interim/* data/processed/*
	touch data/interim/.gitkeep
