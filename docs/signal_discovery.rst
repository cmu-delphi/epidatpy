
Finding data sources and signals of interest
============================================

The Epidata API includes numerous data streams -- medical claims data, cases and deaths,
mobility, and many others -- covering different geographic regions. This can make it a
challenge to find the data stream that you are most interested in.

Example queries with all the endpoint functions available in this package are
given below.


Using the documentation
-----------------------

The Epidata documentation lists all the data sources and signals available
through the API for
`COVID-19 <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_ and
for `other diseases <https://cmu-delphi.github.io/delphi-epidata/api/README.html#source-specific-parameters>`_.
The site also includes a search tool if you have a keyword (e.g. "Taiwan") in mind.

Epidata Data Sources
--------------------
The parameters available for each source data are documented in each linked source-specific API page.

.. csv-table::
   :file: data/endpoints.csv
   :widths: 20 40
   :header-rows: 1

Signal metadata
---------------

The ``source_df`` property lets us obtain a Pandas DataFrame of metadata describing all
data streams which are publically accessible from the COVIDcast API. See the `data source
and signals documentation <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_
for descriptions of the available sources.

.. exec::
  :context: true

  from epidatpy import CovidcastEpidata
  import pandas as pd

  pd.set_option('display.max_columns', None)
  pd.set_option('display.max_rows', None)
  pd.set_option('display.width', 1000)

  epidata = CovidcastEpidata()
  sources = epidata.source_df

  print(sources.head())

This DataFrame contains the following columns:

- ``source`` - API-internal source name.
- ``name`` - Human-readable source name.
- ``description`` - Description of the signal.
- ``reference_signal`` - Geographic level for which this signal is available, such as county, state, msa, hss, hrr, or nation. Most signals are available at multiple geographic levels and will hence be listed in multiple rows with their own metadata.
- ``license`` - The license.
- ``dua`` - Link to the Data Use Agreement.
- ``signals`` - List of signals available from this data source.

The ``signal_df`` DataFrame can also be used to obtain information about the signals
that are available - for example, what time range they are available for,
and when they have been updated.

.. exec::
  :context: true

  signals = epidata.signal_df

  print(signals.head())

This DataFrame contains one row each available signal, with the following columns:

- ``source`` - Data source name.
- ``signal`` - API-internal signal name.
- ``name`` - Human-readable signal name.
- ``active`` - Whether the signal is currently not updated or not. Signals may be inactive because the sources have become unavailable, other sources have replaced them, or additional work is required for us to continue updating them.
- ``short_description`` - Brief description of the signal.
- ``description`` - Full description of the signal.
- ``geo_types`` - Spatial resolution of the signal (e.g., `county`, `hrr`, `msa`, `dma`, `state`). More detail about all `geo_types` is given in the `geographic coding documentation <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_geography.html>`_.
- ``time_type`` - Temporal resolution of the signal (e.g., day, week; see `date coding details <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_times.html>`_).
- ``time_label`` - The time label ("Date", "Week").
- ``value_label`` - The value label ("Value", "Percentage", "Visits", "Visits per 100,000 people").
- ``format`` - The value format ("per100k", "percent", "fraction", "count", "raw").
- ``category`` - The signal category ("early", "public", "late", "other").
- ``high_values_are``- What the higher value of signal indicates ("good", "bad", "neutral").
- ``is_smoothed`` - Whether the signal is smoothed.
- ``is_weighted`` - Whether the signal is weighted.
- ``is_cumulative`` - Whether the signal is cumulative.
- ``has_stderr`` - Whether the signal has `stderr` statistic.
- ``has_sample_size`` - Whether the signal has `sample_size` statistic.
- ``geo_types`` - Geographical levels for which this signal is available.
