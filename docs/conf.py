# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from importlib.metadata import version as _version

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../epidatpy"))

# -- Project information -----------------------------------------------------

project = "epidatpy"
copyright = "2024, Delphi Research Group"
author = "Delphi Research Group"

# The full version, including alpha/beta/rc tags
release = _version("epidatpy")
version = release


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# myst_nb (Markdown + notebook support) implies myst_parser, so narrative pages
# can be authored in either Markdown (.md) or reStructuredText (.rst).
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_nb",
    "sphinx_copybutton",
    "sphinx_design",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    # myst_nb writes executed notebook copies here; not standalone source docs.
    "jupyter_execute",
    "Thumbs.db",
    ".DS_Store",
    "smoke_covid_test",
    "smoke_test_async",
    "smoke_test",
    "tasks",
    "test_pydantic",
]

add_module_names = False
autoclass_content = "class"

# Let notebooks link to each other's headings, e.g. versioned_data.ipynb#calculating-reporting-lag.
myst_heading_anchors = 3
autodoc_typehints = "description"

# -- Options for HTML output -------------------------------------------------

# Delphi colors and fonts (from the delphidocs pkgdown template) live in _static/delphi.css.
html_theme = "pydata_sphinx_theme"
html_title = "epidatpy"
html_static_path = ["_static"]
html_css_files = ["delphi.css", "notebooks.css"]

html_theme_options = {
    # delphi-navbar replaces the theme's flat navbar so Articles can be a dropdown.
    "navbar_center": ["delphi-navbar"],
    "icon_links": [
        {"name": "GitHub", "url": "https://github.com/cmu-delphi/epidatpy", "icon": "fa-brands fa-github"},
        {"name": "PyPI", "url": "https://pypi.org/project/epidatpy/", "icon": "fa-brands fa-python"},
    ],
    "external_links": [
        {"name": "Epidata API", "url": "https://cmu-delphi.github.io/delphi-epidata/"},
        {"name": "epidatr (R)", "url": "https://cmu-delphi.github.io/epidatr/"},
    ],
    "secondary_sidebar_items": ["page-toc"],
    "show_toc_level": 2,
    "footer_start": ["delphi-links"],
    "footer_end": ["copyright"],
}
# delphidocs opens in light mode; readers can still switch.
html_context = {"default_mode": "light"}
# The left sidebar lists a section's subpages; no page has any, so drop it everywhere.
html_sidebars = {"**": []}
# "On this page" shows epidata_meta() rather than EpiDataContext.epidata_meta().
toc_object_entries_show_parents = "hide"

# https://pypi.org/project/sphinx-autodoc-typehints/
always_document_param_types = True

# https://myst-nb.readthedocs.io/
# "auto" runs only notebooks that lack stored outputs (committed notebooks ship
# with outputs, so they render as-is without hitting the live API).
nb_execution_mode = "auto"
