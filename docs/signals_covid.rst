Fetching Data
=============
>>> from delphi_epidata.request import Epidata

This package provides various functions that can be called on the ``Epidata`` object to obtain any :ref:`Epidata endpoint <epidata-endpoints>` signals of interest. 

The functions below will return an ``EpiDataCall`` object, which contains the appropriate URL 
and parameters required to make an API request. The signal of interest can then be obtained in 5 different :ref:`output formats <output-data>`.

Detailed examples are provided in the :ref:`usage examples <getting-started>`.

COVIDcast Signals
-----------------

.. autofunction:: delphi_epidata.request.Epidata.covidcast
|
.. autofunction:: delphi_epidata.request.Epidata.covidcast_meta
|
.. autofunction:: delphi_epidata.request.Epidata.covid_hosp_facility
|
.. autofunction:: delphi_epidata.request.Epidata.covid_hosp_facility_lookup
|
.. autofunction:: delphi_epidata.request.Epidata.covid_hosp_state_timeseries
|
Other Epidata Signals
-----------------
.. autofunction:: delphi_epidata.request.Epidata.pvt_afhsb
|
.. autofunction:: delphi_epidata.request.Epidata.pvt_meta_afhsb
|
.. autofunction:: delphi_epidata.request.Epidata.cdc
|
.. autofunction:: delphi_epidata.request.Epidata.delphi
|
.. autofunction:: delphi_epidata.request.Epidata.ecdc_ili
|
.. autofunction:: delphi_epidata.request.Epidata.flusurv
|
.. autofunction:: delphi_epidata.request.Epidata.fluview
|
.. autofunction:: delphi_epidata.request.Epidata.fluview_meta
|
.. autofunction:: delphi_epidata.request.Epidata.fluview_clinical
|
.. autofunction:: delphi_epidata.request.Epidata.gft
|
.. autofunction:: delphi_epidata.request.Epidata.ght
|
.. autofunction:: delphi_epidata.request.Epidata.kcdc_ili
|
.. autofunction:: delphi_epidata.request.Epidata.meta
|
.. autofunction:: delphi_epidata.request.Epidata.nidss_flu
|
.. autofunction:: delphi_epidata.request.Epidata.nowcast
|
.. autofunction:: delphi_epidata.request.Epidata.pvt_quidel
|
.. autofunction:: delphi_epidata.request.Epidata.pvt_sensors
|
.. autofunction:: delphi_epidata.request.Epidata.pvt_twitter
|
.. autofunction:: delphi_epidata.request.Epidata.wiki
|
.. autofunction:: delphi_epidata.request.Epidata.dengue_nowcast
|
.. autofunction:: delphi_epidata.request.Epidata.pvt_dengue_sensors
|
.. autofunction:: delphi_epidata.request.Epidata.nidss_dengue
|
.. autofunction:: delphi_epidata.request.Epidata.paho_dengue
|
.. autofunction:: delphi_epidata.request.Epidata.pvt_meta_norostat
|
.. autofunction:: delphi_epidata.request.Epidata.pvt_norostat


.. _output-data:

Output Functions
--------

The following functions can be called on an ``EpiDataCall`` object to make an API request and parse the signal in 
5 different formats: 
    - Classic
    - JSON
    - Pandas DataFrame
    - CSV
    - Iterator
|
.. autofunction:: delphi_epidata.request.EpiDataCall.classic
|
.. autofunction:: delphi_epidata.request.EpiDataCall.json
|
.. autofunction:: delphi_epidata.request.EpiDataCall.df
|
.. autofunction:: delphi_epidata.request.EpiDataCall.csv
|
.. autofunction:: delphi_epidata.request.EpiDataCall.iter


More on COVIDcast (TODO)
------------------------

Many data sources and signals are available, so one can also obtain a data frame
of all signals and their associated metadata:

>>> from epidatpy.request import CovidcastEpidata
>>> covid_ds = CovidcastEpidata()
>>> df_source = covid_ds.source_df
>>> df_signal = covid_ds.signal_df

Calling ``CovidcastEpidata`` function will return a class object ``CovidcastDataSources``, 
which has the property ``source_df`` and ``signal_df``, two data frames containing 
the information of all available sources and signals.
More details of the two data frames are listed below.

.. autoclass:: epidatpy.request.CovidcastDataSources()
    :members:

More metadata statistics can also be obtained as follows:

>>> from epidatpy.request import Epidata
>>> df = Epidata.covidcast_meta().df()

.. autofunction:: epidatpy.request.Epidata.covidcast_meta()