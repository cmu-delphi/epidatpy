===============
epidatpy
===============

This package provides Python access to the `Delphi Epidata API
<https://cmu-delphi.github.io/delphi-epidata/>`_ published by the `Delphi
research group <https://delphi.cmu.edu>`_ at `Carnegie Mellon University
<https://www.cmu.edu>`_.

Useful links:
- source code and bug tracker https://github.com/cmu-delphi/epidatpy
- listing on PyPI https://pypi.org/project/epidatpy/
- Epidata API key registration form https://api.delphi.cmu.edu/epidata/admin/registration_form
- Epidata API key documentation https://cmu-delphi.github.io/delphi-epidata/api/api_keys.html

See also the `CMU Delphi Terms of Use
<https://delphi.cmu.edu/epidemic-signals/terms-of-use/>`_, noting that the data
is a research product and not warranted for a particular purpose.

Installation
===============

Install from PyPI using pip:

.. code-block:: sh

   pip install epidatpy

Documentation Contents
======================

.. toctree::
   :maxdepth: 1

   getting_started

   signal_discovery

   versioned_data

   epidatpy

.. note :: **You should consider subscribing** to the `API mailing list
   <https://lists.andrew.cmu.edu/mailman/listinfo/delphi-covidcast-api>`_ to be
   notified of package updates, new data sources, corrections, and other
   updates.

API Keys
===============

The Delphi Epidata API requires a (free) API key for full functionality. To
generate your key, register for a pseudo-anonymous account `here
<https://api.delphi.cmu.edu/epidata/admin/registration_form>`_ and see more
discussion on the `general API website
<https://cmu-delphi.github.io/delphi-epidata/api/api_keys.html>`_. The ``epidatpy``
client will automatically look for this key in the environment variable
``DELPHI_EPIDATA_KEY``. We recommend storing your key in a ``.env`` file, using
`python-dotenv <https://github.com/theskumar/python-dotenv>`_ to load it into
your environment, and adding ``.env`` to your ``.gitignore`` file.

Note that for the time being, the private endpoints (i.e. those prefixed with
``pvt``) will require additional permissions (contact us for more information).
