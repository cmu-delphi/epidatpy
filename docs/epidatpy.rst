epidatpy Reference
==================

All endpoints are methods of :class:`~epidatpy.EpiDataContext`. Each returns an
:class:`~epidatpy.request.EpiDataCall` describing the request; call ``.df()`` on
it to fetch a :class:`pandas.DataFrame`.

Query the new Epidata API (V5)
------------------------------

The current API. Sources are moving here from the covidcast endpoint; see the
:doc:`migration guide <migration_guide>` for how to update covidcast queries.

.. automethod:: epidatpy.EpiDataContext.epidata_meta
.. automethod:: epidatpy.EpiDataContext.epidata_snapshot
.. automethod:: epidatpy.EpiDataContext.epidata_archive
.. automethod:: epidatpy.EpiDataContext.epidata

Query the covidcast endpoint (V4)
---------------------------------

The previous main endpoint. It still carries the sources that have not moved to
V5 yet, and warns on every call ahead of its October 2026 deprecation.

.. automethod:: epidatpy.EpiDataContext.pub_covidcast
.. automethod:: epidatpy.EpiDataContext.pub_covidcast_meta
.. autofunction:: epidatpy.CovidcastEpidata

Query legacy endpoints (V3)
---------------------------

Older endpoints, each with its own dataset. Most are static or no longer
updated; see the :doc:`migration guide <migration_guide>` for which ones are
kept for historical reference.

.. automethod:: epidatpy.EpiDataContext.pub_covid_hosp_facility
.. automethod:: epidatpy.EpiDataContext.pub_covid_hosp_facility_lookup
.. automethod:: epidatpy.EpiDataContext.pub_covid_hosp_state_timeseries
.. automethod:: epidatpy.EpiDataContext.pub_delphi
.. automethod:: epidatpy.EpiDataContext.pub_dengue_nowcast
.. automethod:: epidatpy.EpiDataContext.pub_ecdc_ili
.. automethod:: epidatpy.EpiDataContext.pub_flusurv
.. automethod:: epidatpy.EpiDataContext.pub_fluview
.. automethod:: epidatpy.EpiDataContext.pub_fluview_clinical
.. automethod:: epidatpy.EpiDataContext.pub_fluview_meta
.. automethod:: epidatpy.EpiDataContext.pub_gft
.. automethod:: epidatpy.EpiDataContext.pub_kcdc_ili
.. automethod:: epidatpy.EpiDataContext.pub_meta
.. automethod:: epidatpy.EpiDataContext.pub_nidss_dengue
.. automethod:: epidatpy.EpiDataContext.pub_nidss_flu
.. automethod:: epidatpy.EpiDataContext.pub_nowcast
.. automethod:: epidatpy.EpiDataContext.pub_paho_dengue
.. automethod:: epidatpy.EpiDataContext.pub_wiki

Make requests to private API endpoints
--------------------------------------

These endpoints require additional authorization to use.

.. automethod:: epidatpy.EpiDataContext.pvt_cdc
.. automethod:: epidatpy.EpiDataContext.pvt_dengue_sensors
.. automethod:: epidatpy.EpiDataContext.pvt_ght
.. automethod:: epidatpy.EpiDataContext.pvt_meta_norostat
.. automethod:: epidatpy.EpiDataContext.pvt_norostat
.. automethod:: epidatpy.EpiDataContext.pvt_quidel
.. automethod:: epidatpy.EpiDataContext.pvt_sensors
.. automethod:: epidatpy.EpiDataContext.pvt_twitter

Make API requests
-----------------

Discover endpoints and control how queries are built, cached, and fetched.

.. autoclass:: epidatpy.EpiDataContext
   :members: with_base_url, with_session

.. autoclass:: epidatpy.request.EpiDataCall
   :members: df, classic, request_url, request_arguments, with_base_url, with_session

.. autofunction:: epidatpy.available_endpoints

Configuration and utilities
---------------------------

.. autoclass:: epidatpy.EpiRange

.. autoexception:: epidatpy.InvalidArgumentException
.. autoexception:: epidatpy.EpiDataHTTPError
.. autoexception:: epidatpy.EmptyResultWarning
