.PHONY: help install install-dev test test-cov lint format clean

help:		## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:	## Install package
	pip install -e .

install-dev:	## Install package with development dependencies
	pip install -e ".[dev]"

install-test:	## Install package with testing dependencies
	pip install -e ".[test]"

test:		## Run tests
	pytest

test-cov:	## Run tests with coverage
	pytest --cov=src --cov-report=term-missing --cov-report=html

test-watch:	## Run tests in watch mode
	pytest-watch

lint:		## Run linting
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503

format:		## Format code
	black src/ tests/

format-check:	## Check code formatting
	black --check src/ tests/

clean:		## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

session-start:	## Start a development session
	@read -p "Session name: " name; \
	read -p "Description: " desc; \
	claude-rag session start "$$name" -d "$$desc"

session-update:	## Update current session
	@read -p "Progress notes: " notes; \
	claude-rag session update "$$notes"

session-end:	## End current session
	@read -p "Summary: " summary; \
	claude-rag session end -s "$$summary"

session-status:	## Show current session status
	claude-rag session current