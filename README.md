# `epidatpy`

[![License: MIT][mit-image]][mit-url] [![Github Actions][github-actions-image]][github-actions-url] [![PyPi][pypi-image]][pypi-url] [![Read the Docs][docs-image]][docs-url]

The Python client for the [Delphi Epidata API](https://cmu-delphi.github.io/delphi-epidata/).

## Install

Install with the following commands:

```sh
# Latest dev version
pip install "git+https://github.com/cmu-delphi/epidatpy.git#egg=epidatpy"

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

### CAST API (snapshot / archive)

The CAST API exposes versioned signals (NSSP, pophive, NWSS, ...). Use
`epidata_snapshot` for a single as-of view, `epidata_archive` for the full
report-time history, or `epidata` to dispatch between them.

```py
from epidatpy import EpiDataContext, EpiRange

epidata = EpiDataContext()

# Source-level metadata (signals, geo_types, available date ranges).
epidata.epidata_meta(source="nssp")

# Latest snapshot of a signal (omit `snapshot_date` to fetch the newest version).
epidata.epidata_snapshot(
    source="nssp",
    signals="pct_ed_visits_influenza",
    geo_type="state",
    geo_values="ca,ny",
    reference_time=EpiRange("2025-01-01", "2025-06-01"),
).df()

# Full report-time history, filtered to report_times on or before 2025-10-16.
epidata.epidata_archive(
    source="nssp",
    signals="pct_ed_visits_influenza",
    geo_type="state",
    report_time="<2025-10-16",
).df()

# Router: pass `report_time` (or `snapshot_date="*"`) for archive, `snapshot_date` for snapshot.
epidata.epidata(
    source="nssp",
    signals="pct_ed_visits_influenza",
    geo_type="state",
    report_time=EpiRange("2025-01-01", "2025-10-16"),
).df()
```

`geo_values`, `reference_time`, and an `EpiRange` `report_time` lower
bound are filtered locally after the request.

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

`dev` is the only long-lived branch. Each release cuts a `rel-X.Y` maintenance
branch, which is where patch (hotfix) releases for that line are made. Releases are
driven entirely by the [create_release GitHub Action](https://github.com/cmu-delphi/epidatpy/actions/workflows/create_release.yml):

- **New release (`major` / `minor`):** Run the workflow with the `bump` set to
  `major` or `minor`. It bumps the version on `dev`, cuts a new `rel-X.Y` branch at
  that commit, tags `vX.Y.0`, and creates a [GitHub release](https://github.com/cmu-delphi/epidatpy/releases)
  with auto-generated notes.
- **Hotfix (`patch`):** First land the fix on the relevant `rel-X.Y` branch (commit
  directly or cherry-pick from `dev`). Then run the workflow with `bump` = `patch`,
  optionally setting `release_branch` (defaults to the line matching `dev`'s current
  version). It bumps the patch version on that branch and tags `vX.Y.Z`. It fails if
  the `rel-X.Y` branch doesn't exist.

Pushing the `vX.Y.Z` tag then triggers two workflows: `pypi_publish` builds and
uploads the release to [PyPI](https://pypi.python.org/pypi/epidatpy/), and
`documentation` rebuilds the docs. Publishing is decoupled from the release cut, so
a failed PyPI upload can be re-run (via the `pypi_publish` workflow's `Run workflow`
button, against the existing tag) without redoing the release.

[mit-image]: https://img.shields.io/badge/License-MIT-yellow.svg
[mit-url]: https://opensource.org/licenses/MIT
[github-actions-image]: https://github.com/cmu-delphi/epidatpy/workflows/ci/badge.svg
[github-actions-url]: https://github.com/cmu-delphi/epidatpy/actions
[pypi-image]: https://img.shields.io/pypi/v/epidatpy
[pypi-url]: https://pypi.python.org/pypi/epidatpy/
[docs-image]: https://readthedocs.org/projects/epidatpy/badge/?version=latest
[docs-url]: https://epidatpy.readthedocs.io/en/latest/?badge=latest
