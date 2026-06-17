.PHONY = lint, test, ci, clean, release

# Runner for python tooling. Override with `make PY="poetry run" ...` etc.
PY = uv run

install:
	uv sync --extra dev

lint_ruff:
	$(PY) ruff check epidatpy tests

lint_mypy:
	$(PY) mypy epidatpy tests

lint: lint_ruff lint_mypy

ci: lint test

format:
	$(PY) ruff format epidatpy tests
	$(PY) ruff check --fix epidatpy tests

test:
	$(PY) pytest -m "not live" .

# Live network tests gated on DELPHI_EPIDATA_KEY (skipped per-test when unset).
test_live:
	$(PY) pytest -m live .

doc:
	$(PY) sphinx-build -b html docs docs/_build

doc-preview: doc
	$(PY) python -m webbrowser -t "docs/_build/index.html"

clean_doc:
	rm -rf docs/_build docs/jupyter_execute

clean_build:
	rm -rf build dist .eggs
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean_python:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean: clean_doc clean_build clean_python

# Mirrors pypi_publish.yml, which builds with `uv build`. Releases normally go
# through CI (tag push -> pypi_publish.yml via trusted publishing); these targets
# are for local/manual fallback only.
release: clean lint test
	uv build

# We don't have the tokens setup for this to work locally, but in theory it
# could be provisioned.
upload: release
	uv publish
