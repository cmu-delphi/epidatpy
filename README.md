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
make install        # setup venv, install dependencies and local package
make test           # run unit tests
make format         # format code
make lint           # check linting
make doc            # build docs
make doc-preview    # preview docs in browser
make release        # build distribution packages
make upload         # upload the current version to pypi
make clean          # clean build and docs artifacts
```

### Release Process

`dev` is the only long-lived branch; each release line lives on a `rel-X.Y` branch.
Everything is driven by the [create_release](https://github.com/cmu-delphi/epidatpy/actions/workflows/create_release.yml)
workflow, run with a `bump` of `major`, `minor`, or `patch`:

- **`major` / `minor`:** bumps the version on `dev`, cuts a new `rel-X.Y` branch at
  that commit, and tags `vX.Y.0`.
- **`patch` (hotfix):** bumps the patch version on an existing `rel-X.Y` branch and
  tags `vX.Y.Z`. Land the fix on that branch first (commit directly or cherry-pick
  from `dev`); set `release_branch` to pick the branch (defaults to the line
  matching `dev`'s version).

Either way the workflow creates a [GitHub release](https://github.com/cmu-delphi/epidatpy/releases)
with auto-generated notes. Pushing the `vX.Y.Z` tag then triggers `pypi_publish`
(build + upload to [PyPI](https://pypi.python.org/pypi/epidatpy/)) and `documentation`
(docs rebuild). Because publishing is a separate workflow keyed off the tag rather
than a step inside `create_release`, a failed PyPI upload can be re-run against the
existing tag via the `pypi_publish` workflow's `Run workflow` button — without redoing
the release cut.

[mit-image]: https://img.shields.io/badge/License-MIT-yellow.svg
[mit-url]: https://opensource.org/licenses/MIT
[github-actions-image]: https://github.com/cmu-delphi/epidatpy/workflows/ci/badge.svg
[github-actions-url]: https://github.com/cmu-delphi/epidatpy/actions
[pypi-image]: https://img.shields.io/pypi/v/epidatpy
[pypi-url]: https://pypi.python.org/pypi/epidatpy/
[docs-image]: https://readthedocs.org/projects/epidatpy/badge/?version=latest
[docs-url]: https://epidatpy.readthedocs.io/en/latest/?badge=latest
