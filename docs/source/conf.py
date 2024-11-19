from sarpy import _version

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "sarpy"
copyright = "2024, National Geospatial-Intelligence Agency"
author = "National Geospatial-Intelligence Agency"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.duration",
    "sphinx.ext.intersphinx",
    "numpydoc",
    "sphinx_rtd_theme",
    "sphinxcontrib.autoprogram",
]

templates_path = ["_templates"]
exclude_patterns = []
default_role = "any"

version = _version.__version__

suppress_warnings = [
    "ref.citation",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_logo = "_static/SARPy_logo.png"
html_favicon = "_static/nga_favicon.ico"

html_theme_options = {
    "navigation_depth": -1,
}

autosummary_generate = True
autodoc_typehints = "none"
add_module_names = False

# intersphinx
intersphinx_mapping = {
    "lxml": ("https://lxml.de/apidoc/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "python": ("https://docs.python.org/3", None),
}

# numpydoc
numpydoc_xref_param_type = True
numpydoc_xref_ignore = {"optional", "of"}
numpydoc_validation_checks = {
    "PR10",  # requires a space before the colon separating the parameter name and type
}
