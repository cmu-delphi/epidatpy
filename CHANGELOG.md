# Changelog

## Unreleased

### Breaking changes

- `epidata_archive()` and `epidata()`: passing a bare date or the `=` operator
  to `report_time` now raises `InvalidArgumentException`. Use a comparison
  operator (e.g. `"<2025-01-01"`) or an `EpiRange` instead, or `snapshot_date`
  for point-in-time data.
- `EpiRange` values for `report_time` are now sent to the server as an
  inclusive `from:to` range; the local lower-bound filter is gone.
- The `report_time` column is now a UTC timestamp (`datetime64[ns, UTC]`)
  rather than a date, matching the server, which now reports publication
  instants (e.g. `2025-10-16T13:45:00Z`).
- `epidata_meta(source=...)` returns that source's entry directly instead of a
  one-key dict.
- `pub_covidcast_meta()` returns `last_update` as a UTC datetime instead of an
  integer.

### New features

- `snapshot_date` and `report_time` bounds accept a `datetime` or a UTC
  timestamp string with a trailing `Z`, in addition to dates.
- Failed requests raise `EpiDataHTTPError` carrying the server's own error
  message (JSON `message`/`detail`, or the text of an HTML error page).
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
