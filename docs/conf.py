# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from babel.dates import format_date
from datetime import datetime
from os import path

sys.path.insert(0, path.abspath(".."))

from ELAN import __about__

language = "fr"
project = "ELAN"
copyright = datetime.now().strftime("%Y") + ", REVERSAAL et Oslandia"
author = "REVERSAAL (INRAE) et Oslandia"
version = release = __about__.__version__

date_update = format_date(datetime.now(), format='long', locale=language)
qgis_version_min = __about__.__plugin_md__.get("general").get("qgisminimumversion")

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = []

# -- Choose variables to export to be usable in .rst files -------------------

variables_to_export = ["version", "date_update", "qgis_version_min"]
frozen_locals = dict(locals())
rst_epilog = "\n".join(map(lambda x: f".. |{x}| replace:: {frozen_locals[x]}", variables_to_export))

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "piccolo_theme"
html_static_path = ["_static"]
