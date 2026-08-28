PYTHON ?= python3
export PYTHONPATH := src

.PHONY: help setup fetch build verify check-upstream lint test test-fast docs all clean

help:
	@echo "setup           install bsdtar, pdftotext and the Python requirements"
	@echo "fetch           download the 21 INS artefacts into data/raw (~86 MB)"
	@echo "build           build every dataset into data/processed and write codebooks"
	@echo "verify          re-check data/raw against data/raw/manifest.json"
	@echo "check-upstream  force a re-download and report anything INS has republished"
	@echo "lint            ruff check"
	@echo "test-fast       structural tests only -- no data, no network"
	@echo "test            everything, including reproducing INS's published figures"
	@echo "docs            regenerate docs/SOURCES.md from the manifest"
	@echo "all             fetch, build, docs, lint, test"

setup:
	./scripts/setup.sh

fetch:
	$(PYTHON) -m consumptiontn.cli fetch

build:
	$(PYTHON) -m consumptiontn.cli build

verify:
	$(PYTHON) -m consumptiontn.cli verify

check-upstream:
	$(PYTHON) -m consumptiontn.cli check-upstream

lint:
	ruff check .

test-fast:
	$(PYTHON) -m pytest -m "not needs_raw"

test:
	$(PYTHON) -m pytest

docs:
	$(PYTHON) scripts/write_sources_doc.py

all: fetch build docs lint test

clean:
	rm -rf data/interim/* data/processed/*
	touch data/interim/.gitkeep
