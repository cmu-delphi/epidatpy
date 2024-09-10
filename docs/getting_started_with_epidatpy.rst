Getting started with epidatpy
=============================

The epidatpy package provides access to all the endpoints of the `Delphi Epidata
API <https://cmu-delphi.github.io/delphi-epidata/>`_, and can be used to make
requests for specific signals on specific dates and in select geographic
regions.

Setup
-----

**Installation**

You can install the stable version of this package from PyPi:

.. code-block:: sh

   pip install epidatpy

Or if you want the development version, install from GitHub:

.. code-block:: sh

   pip install -e "git+https://github.com/cmu-delphi/epidatpy.git#egg=epidatpy"

**API Keys**

The Delphi API requires a (free) API key for full functionality. While most
endpoints are available without one, there are
`limits on API usage for anonymous users <https://cmu-delphi.github.io/delphi-epidata/api/api_keys.html>`_,
including a rate limit.

To generate your key,
`register for a pseudo-anonymous account <https://api.delphi.cmu.edu/epidata/admin/registration_form>`_.

*Note* that private endpoints (i.e. those prefixed with ``pvt_``) require a
separate key that needs to be passed as an argument. These endpoints require
specific data use agreements to access.

Basic Usage
-----------

Fetching data from the Delphi Epidata API is simple. Suppose we are
interested in the ``covidcast``
`endpoint <https://cmu-delphi.github.io/delphi-epidata/api/covidcast.html>`_,
which provides access to a
`wide range of data <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_
on COVID-19. Reviewing the endpoint documentation, we see that we
`need to specify <https://cmu-delphi.github.io/delphi-epidata/api/covidcast.html#constructing-api-queries>`_
a data source name, a signal name, a geographic level, a time resolution, and
the location and times of interest.

The ``pub_covidcast`` function lets us access the ``covidcast`` endpoint:

.. exec::
   :context: true

   from epidatpy import EpiDataContext, EpiRange
   import pandas as pd

   # Set common options and context
   pd.set_option('display.max_columns', None)
   pd.set_option('display.max_rows', None)
   pd.set_option('display.width', 1000)

   epidata = EpiDataContext(use_cache=False)

   # Obtain the most up-to-date version of the smoothed covid-like illness (CLI)
   # signal from the COVID-19 Trends and Impact survey for the US
   apicall = epidata.pub_covidcast(
      data_source = "fb-survey",
      signals = "smoothed_cli",
      geo_type = "nation",
      time_type = "day",
      geo_values = "us",
      time_values = EpiRange(20210405, 20210410))

   print(apicall)

``pub_covidcast`` returns an ``EpiDataCall``, which is a not-yet-executed query that can be inspected. The query can be executed and converted to a DataFrame by using the ``.df()`` method:

.. exec::
   :context: true

   data = apicall.df()
   print(data.head())

Each row represents one observation in the US on one
day. The geographical abbreviation is given in the ``geo_value`` column, the date in
the ``time_value`` column. Here `value` is the requested signal -- in this
case, the smoothed estimate of the percentage of people with COVID-like
illness, based on the symptom surveys, and ``stderr`` is its standard error.

The Epidata API makes signals available at different geographic levels,
depending on the endpoint. To request signals for all states instead of the
entire US, we use the ``geo_type`` argument paired with ``*`` for the
``geo_values`` argument. (Only some endpoints allow for the use of ``*`` to
access data at all locations. Check the help for a given endpoint to see if
it supports ``*``.)

.. exec::
   :context: true

   apicall = epidata.pub_covidcast(
      data_source = "fb-survey",
      signals = "smoothed_cli",
      geo_type = "state",
      time_type = "day",
      geo_values = "*",
      time_values = EpiRange(20210405, 20210410))

   print(apicall)
   print(apicall.df().head())

We can fetch a subset of states by listing out the desired locations:

.. exec::
   :context: true

   apicall = epidata.pub_covidcast(
      data_source = "fb-survey",
      signals = "smoothed_cli",
      geo_type = "state",
      time_type = "day",
      geo_values = "pa,ca,fl",
      time_values = EpiRange(20210405, 20210410))

   print(apicall)
   print(apicall.df().head())

We can also request data for a single location at a time, via the ``geo_values`` argument.

.. exec::
   :context: true

   apicall = epidata.pub_covidcast(
      data_source = "fb-survey",
      signals = "smoothed_cli",
      geo_type = "state",
      time_type = "day",
      geo_values = "pa",
      time_values = EpiRange(20210405, 20210410))

   print(apicall)
   print(apicall.df().head())

Getting versioned data
----------------------

The Epidata API stores a historical record of all data, including corrections
and updates, which is particularly useful for accurately backtesting
forecasting models. To fetch versioned data, we can use the ``as_of``
argument:

.. exec::
   :context: true

   apicall = epidata.pub_covidcast(
      data_source = "fb-survey",
      signals = "smoothed_cli",
      geo_type = "state",
      time_type = "day",
      geo_values = "pa",
      time_values = EpiRange(20210405, 20210410),
      as_of = "2021-06-01")

   print(apicall)
   print(apicall.df().head())

Plotting
--------

Because the output data is a standard Pandas DataFrame, we can easily plot
it using any of the available Python libraries:

.. code-block:: python
   
   import matplotlib.pyplot as plt

   fig, ax = plt.subplots(figsize=(6, 5))
   plt.rc("axes", titlesize=16)
   plt.rc("axes", labelsize=16)
   plt.rc("xtick", labelsize=14)
   plt.rc("ytick", labelsize=14)
   ax.spines["right"].set_visible(False)
   ax.spines["left"].set_visible(False)
   ax.spines["top"].set_visible(False)

   data.pivot_table(values = "value", index = "time_value", columns = "geo_value").plot(
      title="Smoothed CLI from Facebook Survey",
      xlabel="Date",
      ylabel="CLI",
      ax = ax,
      linewidth = 1.5
   )

   plt.subplots_adjust(bottom=.2)
   plt.show()

.. image:: images/Getting_Started.png
   :width: 800
   :alt: Smoothed CLI from Facebook Survey

Finding locations of interest
-----------------------------

Most data is only available for the US. Select endpoints report other countries at the national and/or regional levels. Endpoint descriptions explicitly state when they cover non-US locations.

For endpoints that report US data, see the
`geographic coding documentation <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_geography.html>`_
for available geographic levels.

International data
------------------

International data is available via

- ``pub_dengue_nowcast`` (North and South America)
- ``pub_ecdc_ili`` (Europe)
- ``pub_kcdc_ili`` (Korea)
- ``pub_nidss_dengue`` (Taiwan)
- ``pub_nidss_flu`` (Taiwan)
- ``pub_paho_dengue`` (North and South America)
- ``pvt_dengue_sensors`` (North and South America)

Finding data sources and signals of interest
--------------------------------------------

Above we used data from `Delphi’s symptom surveys <https://delphi.cmu.edu/covid19/ctis/>`_,
but the Epidata API includes numerous data streams: medical claims data, cases
and deaths, mobility, and many others. This can make it a challenge to find
the data stream that you are most interested in.

The Epidata documentation lists all the data sources and signals available
through the API for `COVID-19 <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_
and for `other diseases <https://cmu-delphi.github.io/delphi-epidata/api/README.html#source-specific-parameters>`_.
