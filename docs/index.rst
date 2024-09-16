epidatpy
===============

This package provides Python access to the `Delphi Epidata API
<https://cmu-delphi.github.io/delphi-epidata/>`_ published by
the `Delphi research group <https://delphi.cmu.edu>`_ at `Carnegie Mellon University
<https://www.cmu.edu>`_.

The package source code and bug tracker can be found `on GitHub
<https://github.com/cmu-delphi/epidatpy>`_.


Installation
------------

This package will be available on PyPI as `epidatpy
<https://pypi.org/project/epidatpy/>`_ and will be installable with ``pip``.
Meanwhile, it can be installed from GitHub:

.. code-block:: sh

   pip install -e "git+https://github.com/cmu-delphi/epidatpy.git#egg=epidatpy"

The package requires `pandas <https://pandas.pydata.org/>`_ and `requests
<https://requests.readthedocs.io/en/master/>`_; these should be installed
automatically.

API Keys
--------

The Delphi Epidata API requires a (free) API key for full functionality. To
generate your key, register for a pseudo-anonymous account `here
<https://api.delphi.cmu.edu/epidata/admin/registration_form>`_ and see more
discussion on the `general API website
<https://cmu-delphi.github.io/delphi-epidata/api/api_keys.html>`_. The ``epidatpy``
client will automatically look for this key in the environment variable
``DELPHI_EPIDATA_KEY``. We recommend storing your key in a ``.env`` file and using
`python-dotenv <https://github.com/theskumar/python-dotenv>`_ to load it into
your environment.

Note that for the time being, the private endpoints (i.e. those prefixed with
``pvt``) will require a separate key that needs to be passed as an argument.

See also the `COVIDcast Terms of Use
<https://covidcast.cmu.edu/terms-of-use.html>`_, noting that the data is a
research product and not warranted for a particular purpose.

For users of the covidcast Python package
------------------------------------------

The `covidcast <https://cmu-delphi.github.io/covidcast/covidcast-py/html/>`_
package is deprecated and will no longer be updated. The ``epidatpy`` package is a
complete rewrite with a focus on speed, reliability, and ease of use. It also
supports more endpoints and data sources than ``covidcast``. When migrating from
that package, you will need to use the ``pub_covidcast`` function in
``epidatpy``.

.. note :: **You should consider subscribing** to the `API mailing list
   <https://lists.andrew.cmu.edu/mailman/listinfo/delphi-covidcast-api>`_ to be
   notified of package updates, new data sources, corrections, and other
   updates.

Contents
--------

.. toctree::
   :maxdepth: 2

   getting_started

   signal_discovery

   versioned_data

   epidatpy
