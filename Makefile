.PHONY: help build-docs deploy-docs format install lint test

help:
	@grep '^\.PHONY' Makefile | cut -d' ' -f2- | tr ' ' '\n'

build-docs:
	cd docs && poetry run make clean html

deploy-docs:
	make build-docs
	poetry run ghp-import -n -p docs/build/html/

format:
	poetry run isort --profile black .
	poetry run black .

install:
	poetry install

lint:
	poetry run isort --profile black -c --diff .
	poetry run black --check .
	poetry run flake8 .

test:
	poetry run coverage run --source=geometry_to_spatialite ./run_tests.py
	poetry run coverage xml
