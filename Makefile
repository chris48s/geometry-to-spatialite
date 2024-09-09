SHELL := /bin/bash
.PHONY: help build-docs deploy-docs build format install lint test release venv

help:
	@grep '^\.PHONY' Makefile | cut -d' ' -f2- | tr ' ' '\n'

venv:
	python3 -m venv .venv

build-docs:
	source .venv/bin/activate && \
	cd docs && make clean html

deploy-docs:
	source .venv/bin/activate && \
	make build-docs && \
	ghp-import -n -p docs/build/html/

format:
	source .venv/bin/activate && \
	isort . && \
	black .

install:
	python3 -m venv .venv
	source .venv/bin/activate && \
	pip install -e .[dev]

lint:
	source .venv/bin/activate && \
	isort -c --diff . && \
	black --check . && \
	flake8 .

test:
	source .venv/bin/activate && \
	coverage run --source=geometry_to_spatialite ./run_tests.py && \
	coverage report && \
	coverage xml

build:
	source .venv/bin/activate && \
	flit build

release:
	# usage: `make release version=0.0.0`
	make test
	@echo ""
	make lint
	@echo ""
	source .venv/bin/activate && \
	./release.sh "$(version)"
