
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


Signal metadata
---------------

The ``source_df`` property lets us obtain a Pandas DataFrame of metadata describing all
data streams which are publically accessible from the COVIDcast API. See the `data source
and signals documentation <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_
for descriptions of the available sources.

>>> from epidatpy import CovidcastEpidata
>>> epidata = CovidcastEpidata()
>>> sources = epidata.source_df
>>> sources.head()
            source                                         name                                        description          reference_signal                                            license                                                dua                                            signals
0             chng                            Change Healthcare  Change Healthcare is a healthcare technology c...   smoothed_outpatient_cli                                           CC BY-NC  https://cmu.box.com/s/cto4to822zecr3oyq1kkk9xm...  smoothed_outpatient_cli,smoothed_adj_outpatien...
1    covid-act-now                          Covid Act Now (CAN)  COVID Act Now (CAN) tracks COVID-19 testing st...  pcr_specimen_total_tests                                           CC BY-NC                                               None  pcr_specimen_positivity_rate,pcr_specimen_tota...
2    doctor-visits                    Doctor Visits From Claims  Information about outpatient visits, provided ...              smoothed_cli                                              CC BY  https://cmu.box.com/s/l2tz6kmiws6jyty2azwb43po...                      smoothed_cli,smoothed_adj_cli
3        fb-survey  Delphi US COVID-19 Trends and Impact Survey  We conduct the Delphi US COVID-19 Trends and I...              smoothed_cli                                              CC BY  https://cmu.box.com/s/qfxplcdrcn9retfzx4zniyug...  raw_wcli,raw_cli,smoothed_cli,smoothed_wcli,ra...
4  google-symptoms                Google Symptoms Search Trends  Google's [COVID-19 Search Trends symptoms data...       s05_smoothed_search  To download or use the data, you must agree to...                                               None  ageusia_raw_search,ageusia_smoothed_search,ano...

This DataFrame contains the following columns:

- ``source`` - Data source name.
- ``signal`` - Signal name.
- ``description`` - Description of the signal.
- ``reference_signal`` - Geographic level for which this signal is available, such as county, state, msa, hss, hrr, or nation. Most signals are available at multiple geographic levels and will hence be listed in multiple rows with their own metadata.
- ``license`` - The license
- ``dua`` - Link to the Data Use Agreement.

The ``signal_df`` DataFrame can also be used to obtain information about the signals
that are available - for example, what time range they are available for,
and when they have been updated.

>>> signals = epidata.signal_df
>>> signals.head()
  source                         signal                                          name  active                                  short_description                                        description time_type time_label value_label format category high_values_are  is_smoothed is_weighted is_cumulative has_stderr has_sample_size                        geo_types
0   chng        smoothed_outpatient_cli                   COVID-Related Doctor Visits   False  Estimated percentage of outpatient doctor visi...  Estimated percentage of outpatient doctor visi...       day       Date       Value    raw    early             bad         True       False         False      False           False  county,hhs,hrr,msa,nation,state
1   chng    smoothed_adj_outpatient_cli    COVID-Related Doctor Visits (Day-adjusted)   False  Estimated percentage of outpatient doctor visi...  Estimated percentage of outpatient doctor visi...       day       Date       Value    raw    early             bad         True       False         False      False           False  county,hhs,hrr,msa,nation,state
2   chng      smoothed_outpatient_covid                 COVID-Confirmed Doctor Visits   False                      COVID-Confirmed Doctor Visits  Estimated percentage of outpatient doctor visi...       day       Date       Value    raw    early             bad         True       False         False      False           False  county,hhs,hrr,msa,nation,state
3   chng  smoothed_adj_outpatient_covid  COVID-Confirmed Doctor Visits (Day-adjusted)   False                      COVID-Confirmed Doctor Visits  Estimated percentage of outpatient doctor visi...       day       Date       Value    raw    early             bad         True       False         False      False           False  county,hhs,hrr,msa,nation,state
4   chng        smoothed_outpatient_flu             Influenza-Confirmed Doctor Visits   False  Estimated percentage of outpatient doctor visi...  Estimated percentage of outpatient doctor visi...       day        Day       Value    raw    early             bad         True       False         False       None            None  county,hhs,hrr,msa,nation,state

This DataFrame contains one row each available signal, with the following columns:

- ``data_source`` - Data source name.
- ``signal`` - Signal name.
- ``name`` - Name of signal.
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
