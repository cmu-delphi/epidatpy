===============
epidatpy
===============

This package provides Python access to the `Delphi Epidata API
<https://cmu-delphi.github.io/delphi-epidata/>`_ published by the `Delphi
research group <https://delphi.cmu.edu>`_ at `Carnegie Mellon University
<https://www.cmu.edu>`_.

.. grid:: 1 1 3 3
   :gutter: 3

   .. grid-item-card:: Get started
      :link: getting_started
      :link-type: doc

      Install the package, set your API key, and fetch your first signal.

   .. grid-item-card:: Find signals
      :link: signal_discovery
      :link-type: doc

      Search the available sources and signals before you query them.

   .. grid-item-card:: Reference
      :link: epidatpy
      :link-type: doc

      Every endpoint, its arguments, and what it returns.

See also the `CMU Delphi Terms of Use
<https://delphi.cmu.edu/epidemic-signals/terms-of-use/>`_, noting that the data
is a research product and not warranted for a particular purpose.

Installation
===============

Install from PyPI using pip:

.. code-block:: sh

   pip install epidatpy

The Delphi Epidata API has three generations of endpoints. Start with the V5
methods (``epidata_snapshot``, ``epidata_archive``, ``epidata_aux``,
``epidata_meta``); the covidcast (V4) and legacy (V3) methods remain for sources
that have not moved yet and are being deprecated as of October 2026. See the
:doc:`migration guide <migration_guide>` for how to update covidcast queries.

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

Useful links
===============

- `Source code and bug tracker <https://github.com/cmu-delphi/epidatpy>`_
- `Listing on PyPI <https://pypi.org/project/epidatpy/>`_
- `Epidata API key registration form <https://api.delphi.cmu.edu/epidata/admin/registration_form>`_
- `Epidata API key documentation <https://cmu-delphi.github.io/delphi-epidata/api/api_keys.html>`_
- `The R client, epidatr <https://cmu-delphi.github.io/epidatr/>`_

.. Hidden toctree: these entries become the top navbar
   (Get started, Articles, Reference, Changelog), like pkgdown.
   The navbar itself is _templates/delphi-navbar.html.

.. toctree::
   :hidden:
   :maxdepth: 2

   Get started <getting_started>
   signal_discovery
   versioned_data
   migration_guide
   Reference <epidatpy>
   changelog
