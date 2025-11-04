.PHONY = venv, lint, test, clean, release

venv:
	python3.8 -m venv .venv

install: venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

lint_ruff:
	.venv/bin/ruff check epidatpy tests

lint_mypy:
	.venv/bin/mypy epidatpy tests

lint_pylint:
	.venv/bin/pylint epidatpy tests

lint: lint_ruff lint_mypy lint_pylint

format:
	.venv/bin/ruff format epidatpy tests

test:
	.venv/bin/pytest .

doc:
	@pandoc --version >/dev/null 2>&1 || (echo "ERROR: pandoc is required (install via your platform's package manager)"; exit 1)
	.venv/bin/sphinx-build -b html docs docs/_build
	.venv/bin/python -m webbrowser -t "docs/_build/index.html"

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
	.venv/bin/python -m build --sdist --wheel

upload: release
	.venv/bin/twine upload dist/*
