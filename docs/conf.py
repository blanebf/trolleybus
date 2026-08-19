# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys

# Make the library importable for local builds; ReadTheDocs installs the
# package itself (see .readthedocs.yaml).
sys.path.insert(0, os.path.abspath('..'))

from trolleybus import __version__  # noqa: E402

# -- Project information -----------------------------------------------------

project = 'trolleybus'
copyright = "2021-2026, Pavel 'Blane' Tuchin"
author = "Pavel 'Blane' Tuchin"

version = '.'.join(__version__.split('.')[:2])
release = __version__

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
