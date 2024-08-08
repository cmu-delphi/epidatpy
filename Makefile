.PHONY = venv, lint, test, clean, release

venv:
	python3.8 -m venv env

install: venv
	env/bin/python -m pip install --upgrade pip
	env/bin/pip install -e ".[dev]"

lint_ruff:
	env/bin/ruff check epidatpy tests

lint_mypy:
	env/bin/mypy epidatpy tests

lint_pylint:
	env/bin/pylint epidatpy tests

lint: lint_ruff lint_mypy lint_pylint

format:
	env/bin/ruff format epidatpy tests

test:
	env/bin/pytest .

docs:
	env/bin/sphinx-build -b html docs docs/_build
	env/bin/python -m webbrowser -t "docs/_build/index.html"

clean_docs:
	rm -rf docs/_build

clean_build:
	rm -rf build dist .eggs
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean_python:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean: clean_docs clean_build clean_python

release: clean lint test
	env/bin/python -m build --sdist --wheel

upload: release
	env/bin/twine upload dist/*
