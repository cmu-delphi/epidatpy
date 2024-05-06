Getting Started
===============

Overview
--------------

This package provides access to data from various Epidata API endpoints including COVIDcast, 
which provides numerous COVID-related data streams, updated daily. 

.. _epidata-endpoints:

Epidata Data Sources
--------------
The parameters available for each source data are documented in each linked source-specific API page.

|
**COVID-19 Data**

.. list-table:: 
   :widths: 20 20 40
   :header-rows: 1

   * - Endpoint
     - Name
     - Description
   * - `covidcast <https://cmu-delphi.github.io/delphi-epidata/api/covidcast.html>`_
     - COVIDcast
     - Delphi’s COVID-19 surveillance streams.
   * - `covidcast_meta <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_meta.html>`_
     - COVIDcast metadata
     - Metadata for Delphi's COVID-19 surveillance streams.
   * - `covid_hosp_facility <https://cmu-delphi.github.io/delphi-epidata/api/covid_hosp_facility.html>`_
     - COVID-19 Hospitalization by Facility
     - COVID-19 Reported Patient Impact and Hospital Capacity - Facility Lookup
   * - `covid_hosp <https://cmu-delphi.github.io/delphi-epidata/api/covid_hosp.html>`_
     - COVID-19 Hospitalization
     - COVID-19 Reported Patient Impact and Hospital Capacity.

|
**Influenza Data**

.. list-table:: 
   :widths: 20 20 40
   :header-rows: 1

   * - Endpoint
     - Name
     - Description
   * - `afhsb <https://cmu-delphi.github.io/delphi-epidata/api/afhsb.html>`_
     - AFHSB
     - ...
   * - `meta_afhsb <https://cmu-delphi.github.io/delphi-epidata/api/meta_afhsb.html>`_
     - AFHSB Metadata
     - ...
   * - `cdc <https://cmu-delphi.github.io/delphi-epidata/api/cdc.html>`_
     - CDC Page Hits 
     - ...
   * - `delphi <https://cmu-delphi.github.io/delphi-epidata/api/delphi.html>`_
     - Delphi’s Forecast 
     - ...
   * - `ecdc_ili <https://cmu-delphi.github.io/delphi-epidata/api/ecdc_ili.html>`_
     - ECDC ILI
     - ECDC ILI data from the ECDC website.
   * - `flusurv <https://cmu-delphi.github.io/delphi-epidata/api/flusurv.html>`_
     - FluSurv 
     - FluSurv-NET data (flu hospitaliation rates) from CDC.
   * - `fluview <https://cmu-delphi.github.io/delphi-epidata/api/fluview.html>`_
     - FluView
     - Influenza-like illness (ILI) from U.S. Outpatient Influenza-like Illness Surveillance Network (ILINet).
   * - `fluview_meta <https://cmu-delphi.github.io/delphi-epidata/api/fluview_meta.html>`_
     - FluView Metadata
     - Summary data about ``fluview``.
   * - `fluview_clinical <https://cmu-delphi.github.io/delphi-epidata/api/fluview_clinical.html>`_
     - FluView Clinical
     - ...
   * - `gft <https://cmu-delphi.github.io/delphi-epidata/api/gft.html>`_
     - Google Flu Trends
     - Estimate of influenza activity based on volume of certain search queries. This is now a static endpoint due to discontinuation.
   * - `ght <https://cmu-delphi.github.io/delphi-epidata/api/ght.html>`_
     - Google Health Trends
     - Estimate of influenza activity based on volume of certain search queries.
   * - `kcdc_ili <https://cmu-delphi.github.io/delphi-epidata/api/kcdc_ili.html>`_
     - KCDC ILI
     - KCDC ILI data from KCDC website.
   * - `meta <https://cmu-delphi.github.io/delphi-epidata/api/meta.html>`_
     - API Metadata
     - Metadata for ``fluview``, ``twitter``, ``wiki``, and ``delphi``.
   * - `nidss_flu <https://cmu-delphi.github.io/delphi-epidata/api/nidss_flu.html>`_
     - NIDSS Flu
     - Outpatient ILI from Taiwan's National Infectious Disease Statistics System (NIDSS).
   * - `nowcast <https://cmu-delphi.github.io/delphi-epidata/api/nowcast.html>`_
     - ILI Nearby
     - A nowcast of U.S. national, regional, and state-level (weighted) percent ILI, available seven days (regionally) or five days (state-level) before the first ILINet report for the corresponding week.
   * - `quidel <https://cmu-delphi.github.io/delphi-epidata/api/quidel.html>`_
     - Quidel
     - Data provided by Quidel Corp., which contains flu lab test results.
   * - `sensors <https://cmu-delphi.github.io/delphi-epidata/api/sensors.html>`_
     - Delphi's Digital Surveillance Sensors
     - ...
   * - `twitter <https://cmu-delphi.github.io/delphi-epidata/api/twitter.html>`_
     - Twitter Stream
     - Estimate of influenza activity based on analysis of language used in tweets from HealthTweets.
   * - `wiki <https://cmu-delphi.github.io/delphi-epidata/api/wiki.html>`_
     - Wikipedia Access Logs
     - Number of page visits for selected English, Influenza-related wikipedia articles.
|

**Dengue Data**

.. list-table:: 
   :widths: 20 20 40
   :header-rows: 1

   * - Endpoint
     - Name
     - Description
   * - `dengue_nowcast <https://cmu-delphi.github.io/delphi-epidata/api/dengue_nowcast.html>`_
     - Delphi's Dengue Nowcast
     - ...
   * - `dengue_sensors <https://cmu-delphi.github.io/delphi-epidata/api/dengue_sensors.html>`_
     - Delphi’s Dengue Digital Surveillance Sensors
     - ...
   * - `nidss_dengue <https://cmu-delphi.github.io/delphi-epidata/api/nidss_dengue.html>`_
     - NIDSS Dengue
     - Counts of confirmed dengue cases from Taiwan's NIDSS.
   * - `paho_dengue <https://cmu-delphi.github.io/delphi-epidata/api/paho_dengue.html>`_
     - PAHO Dengue
     - ...
|

**Norovirus Data**

.. list-table:: 
   :widths: 20 20 40
   :header-rows: 1

   * - Endpoint
     - Name
     - Description
   * - `meta_norostat <https://cmu-delphi.github.io/delphi-epidata/api/meta_norostat.html>`_
     - NoroSTAT Metadata
     - ...
   * - `norostat <https://cmu-delphi.github.io/delphi-epidata/api/norostat.html>`_
     - NoroSTAT
     - Suspected and confirmed norovirus outbreaks reported by state health departments to the CDC.

|

Epiweeks and Dates
------------------
Epiweeks use the U.S. definition. That is, the first epiweek each year is the week, starting on a Sunday, 
containing January 4. See `this page <https://www.cmmcp.org/mosquito-surveillance-data/pages/epi-week-calendars-2008-2021>`_ for more information.

Formatting for epiweeks is YYYYWW and for dates is YYYYMMDD.

Use individual values, comma-separated lists or, a hyphenated range of values to specify single or several dates.  
An ``EpiRange`` object can be also used to construct a range of epiweeks or dates. Examples include:

- ``param = 201530`` (A single epiweek)
- ``param = '201401,201501,201601'`` (Several epiweeks)
- ``param = '200501-200552'`` (A range of epiweeks)
- ``param = '201440,201501-201510'`` (Several epiweeks, including a range)
- ``param = EpiRange(20070101, 20071231)`` (A range of dates)

|

.. _getting-started:

Basic examples
--------------

**COVIDcast**

To obtain smoothed estimates of COVID-like illness from our symptom survey,
distributed through Facebook, for every county in the United States between
2020-05-01 and 2020-05-07:

>>> from epidatpy.request import Epidata, EpiRange
>>> apicall = Epidata.covidcast("fb-survey", "smoothed_cli", 
...                              "day", "county", 
...                              EpiRange(20200501, 20200507), "*")
>>> data = apicall.df()
>>> data.head()
      source	signal	geo_type	geo_value	time_type	time_value	issue	lag	value	stderr	sample_size	direction	missing_value	missing_stderr	missing_sample_size
0	fb-survey	smoothed_cli	county	01000	day	2020-05-01	2020-09-03	125	0.825410	0.136003	1722	None	0	0	0
1	fb-survey	smoothed_cli	county	01001	day	2020-05-01	2020-09-03	125	1.299425	0.967136	115	None	0	0	0
2	fb-survey	smoothed_cli	county	01003	day	2020-05-01	2020-09-03	125	0.696597	0.324753	584	None	0	0	0
3	fb-survey	smoothed_cli	county	01015	day	2020-05-01	2020-09-03	125	0.428271	0.548566	122	None	0	0	0
4	fb-survey	smoothed_cli	county	01031	day	2020-05-01	2020-09-03	125	0.025579	0.360827	114	None	0	0	0

Each row represents one observation in one county per day. The county FIPS
code is given in the ``geo_value`` column, and the date is given in the ``time_value``
column. The ``value`` is the requested signal - the smoothed
estimate of the percentage of people with COVID-like illness based on the
symptom surveys. The ``issue`` column indicates when this data was reported; in this case, the survey estimates for
May 1st were updated on September 3rd based on new data, giving a ``lag`` of 125 days.
See the :py:func:`epidatpy.request.Epidata.covidcast` documentation for further details on the returned
columns.

In the above code, the ``.df()`` function on the ``apicall`` variable generated a Pandas DataFrame. We can use 
other :ref:`output functions <output-data>` to parse the requested API call in different formats. To parse the data
into JSON format, we can use the following command:

>>> data = apicall.json()
>>> data
[{'geo_value': '01000',
  'signal': 'smoothed_cli',
  'source': 'fb-survey',
  'geo_type': 'county',
  'time_type': 'day',
  'time_value': datetime.date(2020, 5, 1),
  'direction': None,
  'issue': datetime.date(2020, 9, 3),
  'lag': 125,
  'missing_value': 0,
  'missing_stderr': 0,
  'missing_sample_size': 0,
  'value': 0.8254101,
  'stderr': 0.1360033,
  'sample_size': 1722.4551},
 {'geo_value': '01001',
  'signal': 'smoothed_cli',
  'source': 'fb-survey',
  'geo_type': 'county',
  'time_type': 'day',
  'time_value': datetime.date(2020, 5, 1),
  'direction': None,
  'issue': datetime.date(2020, 9, 3),
  'lag': 125,
  'missing_value': 0,
  'missing_stderr': 0,
  'missing_sample_size': 0,
  'value': 1.2994255,
  'stderr': 0.9671356,
  'sample_size': 115.8025},
  .
  .
  .
  }]

Note that all of the :ref:`output functions <output-data>` have a ``field`` parameter which takes in any form of iterator objects 
to enable fetching the data with customization (e.g. specifying which fields or columns to output). Similar to the previous example,
to parse the data in JSON format, but customize the field to show only ``geo_value`` and ``value``, we would use the following
command:

>>> data = apicall.json(fields = ['geo_value', 'value'])
>>> data
[{'geo_value': '01000', 'value': 0.8254101},
 {'geo_value': '01001', 'value': 1.2994255},
 {'geo_value': '01003', 'value': 0.6965968},
 {'geo_value': '01015', 'value': 0.4282713},
 {'geo_value': '01031', 'value': 0.0255788},
 {'geo_value': '01045', 'value': 1.0495589},
 {'geo_value': '01051', 'value': 1.5783991},
 {'geo_value': '01069', 'value': 1.6789546},
 {'geo_value': '01071', 'value': 2.1313118},
 .
 .
 .
 }]


|

**Wikipedia Access article "influenza" on 2020w01**

>>> apicall_wiki = Epidata.wiki(articles='influenza', epiweeks='202001')
>>> data = apicall_wiki.json()
>>> print(data)
[{'article': 'influenza', 'count': 6516, 'total': 663604044, 'hour': -1, 'epiweek': datetime.date(2019, 12, 29), 'value': 9.81910834}]

|

**FluView on 2019w01 (national)**

>>> apicall_fluview = Epidata.fluview(regions='nat', epiweeks='201901')
>>> data = apicall_fluview.classic()
>>> data
{'epidata': [{'release_date': '2020-10-02',
   'region': 'nat',
   'issue': datetime.date(2020, 3, 9),
   'epiweek': datetime.date(2018, 12, 30),
   'lag': 90,
   'num_ili': 42135,
   'num_patients': 1160440,
   'num_providers': 2630,
   'num_age_0': 11686,
   'num_age_1': 9572,
   'num_age_2': None,
   'num_age_3': 11413,
   'num_age_4': 5204,
   'num_age_5': 4260,
   'wili': 3.45972,
   'ili': 3.63095}],
 'result': 1,
 'message': 'success'}

|

Other examples (TODO)
--------------

(TODO)