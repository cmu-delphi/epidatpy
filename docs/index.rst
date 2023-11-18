Delphi Epidata
===============

This package provides Python access to the `Delphi Epidata API
<https://cmu-delphi.github.io/delphi-epidata/>`_ published by
the `Delphi group <https://delphi.cmu.edu>`_ at `Carnegie Mellon University
<https://www.cmu.edu>`_.

The package source code and bug tracker can be found `on GitHub
<https://github.com/cmu-delphi/epidatpy>`_.


.. note :: **You should consider subscribing** to the `API mailing list
   <https://lists.andrew.cmu.edu/mailman/listinfo/delphi-covidcast-api>`_ to be
   notified of package updates, new data sources, corrections, and other
   updates.

.. warning :: If you use data from the COVIDcast API to power a public product,
   dashboard, app, or other service, please download the data you need and store
   it centrally rather than making API requests for every user. Our server
   resources are limited and cannot support high-volume interactive use.

   See also the `COVIDcast Terms of Use
   <https://covidcast.cmu.edu/terms-of-use.html>`_, noting that the data is a
   research product and not warranted for a particular purpose.


Installation
------------

This package is available on PyPI as `covidcast
<https://pypi.org/project/epidatpy/>`_, and can be installed using ``pip`` or
your favorite Python package manager:

.. code-block:: sh

   pip install epidatpy

The package requires `pandas <https://pandas.pydata.org/>`_ and `requests
<https://requests.readthedocs.io/en/master/>`_; these should be installed
automatically.

Contents
--------

.. toctree::
   :maxdepth: 2

   getting_started

   signals_covid

