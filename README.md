# `epidatpy`

[![License: MIT][mit-image]][mit-url] [![Github Actions][github-actions-image]][github-actions-url] [![PyPi][pypi-image]][pypi-url] [![Read the Docs][docs-image]][docs-url]

The Python client for the [Delphi Epidata API](https://cmu-delphi.github.io/delphi-epidata/).

## Install

Install with the following commands:

```sh
# Latest dev version
pip install -e "git+https://github.com/cmu-delphi/epidatpy.git#egg=epidatpy"

# PyPI version (not yet available)
pip install epidatpy
```

## Usage

```py
from epidatpy import CovidcastEpidata, EpiDataContext, EpiRange

# All calls using the `epidata` object will now be cached for 7 days
epidata = EpiDataContext(use_cache=True, cache_max_age_days=7)

# Obtain a DataFrame of the most up-to-date version of the smoothed covid-like illness (CLI)
# signal from the COVID-19 Trends and Impact survey for the US
epidata.pub_covidcast(
    data_source="jhu-csse",
    signals="confirmed_cumulative_num",
    geo_type="nation",
    time_type="day",
    geo_values="us",
    time_values=EpiRange(20210405, 20210410),
).df()
```

## Development

The following commands are available for developers:

```sh
make install  # setup venv, install dependencies and local package
make test     # run unit tests
make format   # format code
make lint     # check linting
make docs     # build docs
make dist     # build distribution packages
make release  # upload the current version to pypi
make clean    # clean build and docs artifacts
```

Building the documentation additionally requires the Pandoc package. These
commands can be used to install the package on common platforms (see the
[official documentation](https://pandoc.org/installing.html) for more options):

```sh
# Linux (Debian/Ubuntu)
sudo apt-get install pandoc

# OS X / Linux (with Homebrew)
brew install pandoc

# Windows (with Chocolatey)
choco install pandoc
```

### Release Process

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
