# `epidatpy`

[![License: MIT][mit-image]][mit-url] [![Github Actions][github-actions-image]][github-actions-url] [![PyPi][pypi-image]][pypi-url] [![Read the Docs][docs-image]][docs-url]

The Python client for the [Delphi Epidata API](https://cmu-delphi.github.io/delphi-epidata/).

The Delphi Epidata API provides real-time access to epidemiological
surveillance data for influenza, COVID-19, and other diseases from official
government sources such as the [CDC](https://www.cdc.gov/) and from private
partners. It is built and maintained by the Carnegie Mellon University
[Delphi Research Group](https://delphi.cmu.edu/).

`epidatpy` streamlines downloading data from the API into pandas data frames.
It can fetch the latest values of a signal, the values as they were known on a
past date, or the full revision history of a signal, which is what you need to
backtest forecasting models honestly. It can also fetch accessory data associated
with a signal, such as source-specific metadata, via `epidata_aux()`. The R equivalent
is [`epidatr`](https://cmu-delphi.github.io/epidatr/).

## Install

```sh
# PyPI version
pip install epidatpy

# Latest dev version
pip install "git+https://github.com/cmu-delphi/epidatpy.git#egg=epidatpy"
```

### API keys

The Delphi Epidata API requires a (free) API key for full functionality. To
generate your key, register for a pseudo-anonymous account
[here](https://api.delphi.cmu.edu/epidata/admin/registration_form) and see more
discussion on the [general API
website](https://cmu-delphi.github.io/delphi-epidata/api/api_keys.html).
`epidatpy` reads the key from the `DELPHI_EPIDATA_KEY` environment variable. We
recommend keeping it in a `.env` file loaded with
[python-dotenv](https://github.com/theskumar/python-dotenv), and adding `.env`
to your `.gitignore`.

Note that for the time being, the private endpoints (those prefixed with
`pvt_`) require a separate key that is passed as an argument.

## Usage

To get started, see the [Getting started
guide](https://cmu-delphi.github.io/epidatpy/getting_started.html).

```py
from epidatpy import EpiDataContext, EpiRange

epidata = EpiDataContext()

# Discover what a source offers: signals, geo types, and date ranges.
meta = epidata.epidata_meta(source="nssp")
meta["signals"]

# Fetch the latest snapshot of NSSP influenza ED visit percentages by state.
flu = epidata.epidata_snapshot(
    source="nssp",
    signals="pct_ed_visits_influenza",
    geo_type="state",
).df()

# Data as it was known on a past date, for two states and a date range.
epidata.epidata_snapshot(
    source="nssp",
    signals="pct_ed_visits_influenza",
    geo_type="state",
    geo_values=["ca", "ny"],
    reference_time=EpiRange("2025-01-01", "2025-06-01"),
    snapshot_date="2025-06-15",
).df()

# Full revision history, restricted to reports published before 2025-10-16.
epidata.epidata_archive(
    source="nssp",
    signals="pct_ed_visits_influenza",
    geo_type="state",
    report_time="<2025-10-16",
).df()
```

`report_time` is a UTC timestamp column. `geo_values` and `reference_time` are
filtered locally after the request; `report_time` filters are applied
server-side and take a comparison string or an `EpiRange`.

This is just a glimpse of what `epidatpy` can do. See the
[documentation](https://cmu-delphi.github.io/epidatpy/) for walkthroughs of
specific tasks (finding signals, understanding versioned data, migrating from
`pub_covidcast`) and for the full reference of methods and their arguments.

## Which endpoint has my data?

The Delphi Epidata API has three generations of endpoints, and this package has
client methods for all of them:

- **V5 (current):** `epidata_snapshot()`, `epidata_archive()`, and
  `epidata_meta()`. Start here; sources are moving to V5 one at a time.
- **V4 (covidcast):** `pub_covidcast()`. Still carries the sources that have
  not moved to V5 yet.
- **V3 (legacy):** the many other `pub_*` methods (e.g. `pub_fluview()`,
  `pub_gft()`), one per dataset. Most of these datasets are static or no
  longer updated; they remain available for historical work.

If you have existing `pub_covidcast()` code, see the
[migration guide](https://cmu-delphi.github.io/epidatpy/migration_guide.html)
for the argument and column mapping to the V5 methods.

## Migrating from covidcast and to the V5 API

If you are migrating existing workflows, there are two transitions to keep in
mind:

- From the `covidcast` package to `epidatpy`. The standalone [`covidcast`
  package](https://cmu-delphi.github.io/covidcast/covidcast-py/html/) is
  deprecated and superseded by `epidatpy`, which is a complete rewrite offering
  better speed, reliability, and broader endpoint support.
- From V3/V4 endpoints to the V5 API. Within `epidatpy`, `pub_covidcast()` and
  the other V3/V4 methods are being deprecated as of October 2026, and calling
  them now emits a warning. See the [migration
  guide](https://cmu-delphi.github.io/epidatpy/migration_guide.html), which maps
  `pub_covidcast()` arguments and columns onto the V5 methods. New code should
  use the current V5 methods (`epidata_snapshot()`, `epidata_archive()`, and
  `epidata_meta()`), reserving `pub_covidcast()` only for sources that have not
  yet transitioned.

## Get updates

**You should consider subscribing to the [API mailing
list](https://lists.andrew.cmu.edu/mailman/listinfo/delphi-covidcast-api)** to
be notified of package updates, new data sources, corrections, and more.

## Usage terms and citation

If you use `epidatpy` or data from the Delphi Epidata API in your work, please
cite the package. If you use data that originated from the COVIDcast project
(whether accessed via V5 endpoints or `pub_covidcast()`), please include the
[COVIDcast citation](https://cmu-delphi.github.io/covidcast/covidcastR/authors.html#citation)
as well.

Certain data sources have specific attribution and licensing terms. See the
[Epidata data licensing
documentation](https://cmu-delphi.github.io/delphi-epidata/api/README.html#data-licensing)
and the [COVIDcast licensing
documentation](https://cmu-delphi.github.io/delphi-epidata/api/covidcast_licensing.html)
for information about citing specific datasets.

**Warning:** If you use data from the Epidata API to power a product,
dashboard, app, or other service, please download the data you need and store
it centrally rather than making API requests for every user. Our server
resources are limited and cannot support high-volume interactive use.

See also the [Terms of Use](https://delphi.cmu.edu/covidcast/terms-of-use/),
noting that the data is a research product and not warranted for a particular
purpose.

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
