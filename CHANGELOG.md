# Changelog

## Unreleased

### Breaking changes

- Python 3.11 or newer is required (it was 3.9). CI tests 3.11 through 3.14.

### New features

- `epidata_snapshot()`, `epidata_archive()`, and `epidata()` send `geo_values`
  and `reference_time` to the server as the `geo_value` and `reference_times`
  filters instead of filtering the response locally. `reference_time` also
  accepts comparison strings such as `">=2025-01-01"`. `limit` now caps the
  rows that match these filters; before, it capped the rows first and the local
  filters could leave fewer, or none.
- Failed requests raise `EpiDataHTTPError`, a `requests.HTTPError` subclass,
  so existing handlers keep working. It exposes the server's message as
  `.message`, plus `.status_code` and `.url`.
- `epidata_snapshot()`, `epidata_archive()`, and `epidata()` accept named
  filters on the source's extra key columns as keyword arguments (e.g.
  `pcr_target="sars-cov-2"`), sent server-side as `extra_keys`.
- When a cast query returns nothing, the `EmptyResultWarning` also gives the
  source's `reference_time` range.
- Cast snapshot/archive responses with columns the client doesn't declare
  warn, like epidatr; those columns are kept as strings.

### Fixes

- Requests are retried (3 tries in all) after a connection failure, a 500, 502,
  503 or 504, or a 429 that comes with a `Retry-After`, and now time out after
  15 minutes of silence instead of never. A `Retry-After` longer than
  `EPIDATPY_MAX_RETRY_WAIT` seconds (default 60) is never waited on: the call
  fails at once with the server's message, which now also says when the server
  suggests retrying. This replaces the `tenacity` dependency.
- Classic (V4) endpoints no longer turn a bad response into an empty frame.
  `.df()` raises `EpiDataAPIError` for an error envelope (e.g. `result` -1),
  and both `.df()` and `.classic()` raise `MalformedResponseError` for a body
  that is not JSON or lacks `result`, `message`, or `epidata`. A non-success
  `message` (a truncated result, "no results") warns with `EpiDataWarning`, and
  columns the endpoint promises but the response lacks warn with
  `DroppedMetaFieldsWarning` and are filled with missing values.
- The POST fallback for a 414 (URI too long) response now sends the
  parameters in the form body; before, it repeated them in the URL and failed
  the same way.
- The cache now keeps only cast results for a fixed past version: a
  `snapshot_date`, or a `report_time` of the form `"<date"` or an `EpiRange`,
  ending at least two days ago (UTC). "Latest" and open-ended queries and
  calls with a row `limit` are not cached, so they no longer go stale for days.
  It stores the raw response and parses it on every read (so a cache hit is
  filtered and checked like a fresh result), and the cache key now includes the
  epidatpy version and the server URL. Existing cast cache entries are
  ignored.
- `fields` on the cast endpoints no longer makes the request fail with a 422;
  the columns are selected locally, and calls with different `fields` share one
  cache entry.

### Documentation

- The `fill_method` values are `"source"`, `"ave"`, and `"zero"`; the docs said
  `"fill_ave"` and `"fill_zero"`, which the server rejects.

## 0.7.0

### Breaking changes

- `epidata_archive()` and `epidata()`: passing a bare date or the `=` operator
  to `report_time` now raises `InvalidArgumentException`. Use a comparison
  operator (e.g. `"<2025-01-01"`) or an `EpiRange` instead, or `snapshot_date`
  for point-in-time data.
- `EpiRange` values for `report_time` are now sent to the server as an
  inclusive `from:to` range; the local lower-bound filter is gone.
- The `report_time` column is now a UTC timestamp (a timezone-aware
  `datetime64` column) rather than a date, matching the server, which now
  reports publication instants (e.g. `2025-10-16T13:45:00Z`).
- `epidata_meta(source=...)` returns that source's entry directly instead of a
  one-key dict.
- `pub_covidcast_meta()` returns `last_update` as a UTC datetime instead of an
  integer.

### New features

- `snapshot_date` and `report_time` bounds accept a `datetime` or a UTC
  timestamp string with a trailing `Z`, in addition to dates.
- Failed requests raise `requests.HTTPError` with the server's own error
  message appended (JSON `message`/`detail`, or the text of an HTML error page).
- `epidata_snapshot()`, `epidata_archive()`, and `epidata()` gain `limit`, a
  cap on the rows the server returns. `None` or `-1` means no limit. The query
  has no stable sort order, so use it only to preview or debug a query.
- `epidata_meta()` with no `source` returns the metadata for every source.
- `geo_type` accepts several values (a sequence or comma-joined string); the
  call issues one request per geo type and concatenates the results.
- Empty or partially empty cast results warn with `EmptyResultWarning`, naming
  the signals and geo types that returned nothing. When nothing comes back at
  all and the source's metadata says a requested signal or geo type does not
  exist, the call raises `InvalidArgumentException` instead, matching epidatr.
  `return_empty=True` silences this.
- Cast responses parse `ci_lower` and `ci_upper` when present.
- `epidata_aux()` fetches a cast source's auxiliary data (e.g. nwss
  sample-site descriptors) from `/aux_data/`, with key filters passed as
  keyword arguments. Passing it a DataFrame from `epidata_snapshot()` or
  `epidata_archive()` instead merges the auxiliary data onto each row, as of
  that row's version.
- `pub_covidcast_meta()` gains `signals`, `time_type`, and `geo_type` arguments
  for server-side filtering, and now returns the `geo_type` column.
- `pub_covidcast()` validates `time_type`, requires `time_type="week"` for
  `nssp`, and accepts the `hsa_nci` and `dma` geo types.

### Documentation

- README and the getting-started, signal-discovery, and versioned-data guides
  now lead with the V5 API; the migration guide covers the V3 endpoints
  (FluView example) and the current `report_time` rules.
- The reference page is grouped by API generation.

## 0.6.0

- Added deprecation warnings and documentation for the V4 endpoints ahead of
  the V5 transition.
- Added the cast-API endpoints `epidata_meta()`, `epidata_snapshot()`,
  `epidata_archive()`, and `epidata()`.
