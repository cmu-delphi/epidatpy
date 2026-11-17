# Runner for python tooling. Override with `just py="poetry run" ...` etc.
py := "uv run"

# Base URL for cast-API live tests; empty uses the default server, e.g.
#   just cast_url=https://development.delphi.cmu.edu/epidata/v5/ test-live
cast_url := ""

[private]
default:
    @just --list

[group('setup')]
install:
    uv sync --extra dev

[group('check')]
lint-ruff:
    {{py}} ruff check epidatpy tests

[group('check')]
lint-mypy:
    {{py}} mypy epidatpy tests

[group('check')]
lint: lint-ruff lint-mypy

[group('check')]
format:
    {{py}} ruff format epidatpy tests
    {{py}} ruff check --fix epidatpy tests

[group('check')]
ci: lint test

[group('test')]
test:
    {{py}} pytest -m "not live" tests

# Live network tests gated on DELPHI_EPIDATA_KEY (skipped per-test when unset).
[group('test')]
test-live:
    EPIDATPY_CAST_BASE_URL={{cast_url}} {{py}} pytest -m live tests

[group('test')]
test-live-cast:
    EPIDATPY_CAST_BASE_URL={{cast_url}} {{py}} pytest -m live tests/test_cast_endpoints.py

[group('docs')]
doc:
    {{py}} sphinx-build -b html docs docs/_build

[group('docs')]
doc-preview: doc
    {{py}} python -m webbrowser -t "docs/_build/index.html"

[group('clean')]
clean-doc:
    rm -rf docs/_build docs/jupyter_execute

[group('clean')]
clean-build:
    rm -rf build dist .eggs
    find . -name '*.egg-info' -exec rm -rf {} +
    find . -name '*.egg' -exec rm -f {} +

[group('clean')]
clean-python:
    find . -name '*.pyc' -exec rm -f {} +
    find . -name '*.pyo' -exec rm -f {} +
    find . -name '__pycache__' -exec rm -fr {} +

[group('clean')]
clean: clean-doc clean-build clean-python

# Prints what happened since the last release tag (merged PRs with their
# descriptions, then every commit) for an agent or a person to turn into the
# `## X.Y.Z` section of CHANGELOG.md. Pass `since` to start from another tag and
# `branch` to compare against another branch.
# Needs the `gh` CLI. See DEVELOPMENT.md "Release process".
[group('release')]
changelog since="" branch="dev":
    #!/usr/bin/env bash
    set -euo pipefail
    since="{{since}}"
    [ -n "$since" ] || since=$(git describe --tags --abbrev=0 "origin/{{branch}}")
    echo "# Changes on {{branch}} since $since"
    echo
    echo "Version in pyproject.toml: $(uv version --short)"
    echo
    echo "## Merged pull requests"
    echo
    # PR numbers come from the commit subjects: "(#12)" for squash merges and
    # "Merge pull request #12" for merge commits.
    for n in $(git log --format=%s "$since..origin/{{branch}}" \
            | grep -oE '(\(#|pull request #)[0-9]+' | grep -oE '[0-9]+' | sort -un); do
        gh pr view "$n" --json number,title,body \
            --jq '"### #\(.number) \(.title)\n\n\(.body)\n"'
    done
    echo "## Commits"
    echo
    git log --format='- %h %s' "$since..origin/{{branch}}"

# Mirrors pypi_publish.yml, which builds with `uv build`. Releases normally go
# through CI (tag push -> pypi_publish.yml via trusted publishing); this is a
# local/manual fallback only.
[group('release')]
release: clean lint test
    uv build

# We don't have the tokens setup for this to work locally, but in theory it
# could be provisioned.
[group('release')]
upload: release
    uv publish
