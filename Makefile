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
	$(PY) pytest .

# Live network tests gated on DELPHI_EPIDATA_KEY (skipped when unset).
test_live:
	$(PY) pytest tests/test_epidata_calls.py tests/test_cast_endpoints.py

test_live_cast:
	$(PY) pytest tests/test_cast_endpoints.py

doc:
	@pandoc --version >/dev/null 2>&1 || (echo "ERROR: pandoc is required (install via your platform's package manager)"; exit 1)
	$(PY) sphinx-build -b html docs docs/_build
	$(PY) python -m webbrowser -t "docs/_build/index.html"

clean_doc:
	rm -rf docs/_build

clean_build:
	rm -rf build dist .eggs
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean_python:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean: clean_doc clean_build clean_python

release: clean lint test
	$(PY) python -m build --sdist --wheel

upload: release
	$(PY) twine upload dist/*
