# Delphi Epidata Python Client `epidatpy`

[![License: MIT][mit-image]][mit-url] [![Github Actions][github-actions-image]][github-actions-url] [![PyPi][pypi-image]][pypi-url] [![Read the Docs][docs-image]][docs-url]

## Install

Install latest version:

```sh
pip install -e "git+https://github.com/cmu-delphi/epidatpy.git#egg=epidatpy"
```

## Usage

TODO

## Development Environment

Prepare virtual environment and install dependencies

```sh
python -m venv venv
source ./venv/bin/activate
pip install --use-feature=2020-resolver -r requirements.txt -r requirements-dev.txt
```

### Common Commands

```sh
source ./venv/bin/activate
inv format   # format code
inv lint     # check linting
inv docs     # build docs
inv test     # run unit tests
inv coverage # run unit tests with coverage
inv clean    # clean build artifacts
inv dist     # build distribution packages
inv release  # upload the current version to pypi
```

## Release Process

The release consists of multiple steps which can be all done via the GitHub website:

1. Go to [create_release GitHub Action](https://github.com/cmu-delphi/epidatpy/actions/workflows/create_release.yml) and click the `Run workflow` button. Enter the next version number or one of the magic keywords (patch, minor, major) and hit the green `Run workflow` button.
2. The action will prepare a new release and will end up with a new [Pull Request](https://github.com/cmu-delphi/epidatpy/pulls)
3. Let the code owner review the PR and its changes and let the CI check whether everything builds successfully
4. Once approved and merged, another GitHub action job starts which automatically will
    1. create a git tag
    2. create another [Pull Request](https://github.com/cmu-delphi/epidatpy/pulls) to merge the changes back to the `dev` branch
    3. create a [GitHub release](https://github.com/cmu-delphi/epidatpy/releases) with automatically derived release notes
5. Done

[mit-image]: https://img.shields.io/badge/License-MIT-yellow.svg
[mit-url]: https://opensource.org/licenses/MIT
[github-actions-image]: https://github.com/cmu-delphi/epidatpy/workflows/ci/badge.svg
[github-actions-url]: https://github.com/cmu-delphi/epidatpy/actions
[pypi-image]: https://img.shields.io/pypi/v/epidatpy
[pypi-url]: https://pypi.python.org/pypi/epidatpy/
[docs-image]: https://readthedocs.org/projects/epidatpy/badge/?version=latest
[docs-url]: https://epidatpy.readthedocs.io/en/latest/?badge=latest
