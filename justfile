# Justfile for autopage - https://github.com/casey/just

# List available recipes
default:
    @just --list

# Run all tests
test:
    poetry run pytest tests/ -v

# Run tests with coverage
test-cov:
    poetry run pytest tests/ -v --cov=autopage --cov-report=term-missing

# Run linter
lint:
    poetry run ruff check src/ tests/

# Auto-fix linting issues
lint-fix: lint-format
    poetry run ruff check --fix src/ tests/

# Format code
lint-format:
    poetry run ruff format src/ tests/

# Build the package
build:
    poetry build

# Install dependencies
install:
    poetry install

# Update dependencies
update:
    poetry update

# Run autopage with example file (dry-run)
example:
    poetry run autopage --dry-run doc/example-shell.ap.toml

# instead of pulling toml-repo from pypi, use the local submodule
use-toml-repo-local:
    poetry add --editable ./toml-repo

use-toml-repo-pypi:
    poetry remove toml-repo
    poetry add toml-repo

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name '*.pyc' -delete

# Run all checks (lint + test)
check: lint test

# release a new version to pypi
bump-version newver="patch": test
    bin/new-version.sh {{newver}}
