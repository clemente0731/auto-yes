.DEFAULT_GOAL := help
PYTHON ?= python

.PHONY: help install dev lint fmt test cov build clean

help: ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## install package in editable mode
	$(PYTHON) -m pip install -e .

dev: ## install with all dev dependencies
	$(PYTHON) -m pip install -e ".[dev]"
	pre-commit install

lint: ## run ruff linter
	ruff check src/ tests/

fmt: ## format code with ruff
	ruff format src/ tests/

test: ## run test suite
	pytest

cov: ## run tests with coverage report
	pytest --cov=auto_yes --cov-report=term-missing --cov-report=html

build: clean ## build sdist and wheel
	$(PYTHON) -m build
	twine check dist/*

clean: ## remove build artifacts
	rm -rf dist/ build/ src/*.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
