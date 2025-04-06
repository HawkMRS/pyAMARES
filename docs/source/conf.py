# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import pathlib
import sys

import pyAMARES

project = "pyAMARES"
copyright = (
    " 2023-2025, Jia Xu, Magnetic Resonance Research Facility, University of Iowa "
)
author = pyAMARES.__author__
release = pyAMARES.__version__
print(author, release)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
#

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.

sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())

extensions = [
    "nbsphinx",
    "sphinx_tabs.tabs",
    "sphinx.ext.mathjax",
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
]


templates_path = ["_templates"]
exclude_patterns = []

source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
# html_static_path = ["_static"]
html_static_path = []


# This goes in conf.py
# nb_execution_mode = 'cache'  # Options: 'auto', 'cache', 'force', 'off'
# nb_source_folder = './notebooks'  # Adjust the path as necessary

nbsphinx_execute = "never"  # Other options: 'never', 'auto' (default)
