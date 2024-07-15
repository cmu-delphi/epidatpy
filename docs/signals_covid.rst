Fetching Data
=============

>>> from epidatpy.request import Epidata
>>> epi = Epidata()
>>> epi.pub_covidcast('usa-facts', 'confirmed_7dav_incidence_num', '20210101', '20210131', 'state', 'tx')

This package provides various functions that can be called on the ``Epidata`` object to obtain any :ref:`Epidata endpoint <epidata-endpoints>` signals of interest. The functions below are inherited by the ``Epidata`` object.

Detailed examples are provided in the :ref:`usage examples <getting-started>`.

COVIDcast Signals
-----------------

.. automethod:: epidatpy.AEpiDataEndpoints.pub_covidcast

.. automethod:: epidatpy.AEpiDataEndpoints.pub_covidcast_meta

.. automethod:: epidatpy.AEpiDataEndpoints.pub_covid_hosp_facility

.. automethod:: epidatpy.AEpiDataEndpoints.pub_covid_hosp_facility_lookup

.. automethod:: epidatpy.AEpiDataEndpoints.pub_covid_hosp_state_timeseries

Other Epidata Signals
---------------------

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_cdc

.. automethod:: epidatpy.AEpiDataEndpoints.pub_delphi

.. automethod:: epidatpy.AEpiDataEndpoints.pub_ecdc_ili

.. automethod:: epidatpy.AEpiDataEndpoints.pub_flusurv

.. automethod:: epidatpy.AEpiDataEndpoints.pub_fluview

.. automethod:: epidatpy.AEpiDataEndpoints.pub_fluview_meta

.. automethod:: epidatpy.AEpiDataEndpoints.pub_fluview_clinical

.. automethod:: epidatpy.AEpiDataEndpoints.pub_gft

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_ght

.. automethod:: epidatpy.AEpiDataEndpoints.pub_kcdc_ili

.. automethod:: epidatpy.AEpiDataEndpoints.pub_meta

.. automethod:: epidatpy.AEpiDataEndpoints.pub_nidss_flu

.. automethod:: epidatpy.AEpiDataEndpoints.pub_nowcast

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_quidel

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_sensors

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_twitter

.. automethod:: epidatpy.AEpiDataEndpoints.pub_wiki

.. automethod:: epidatpy.AEpiDataEndpoints.pub_dengue_nowcast

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_dengue_sensors

.. automethod:: epidatpy.AEpiDataEndpoints.pub_nidss_dengue

.. automethod:: epidatpy.AEpiDataEndpoints.pub_paho_dengue

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_meta_norostat

.. automethod:: epidatpy.AEpiDataEndpoints.pvt_norostat
