# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import re
import sys
from datetime import datetime
from os import path

from babel.dates import format_date

sys.path.insert(0, path.abspath(".."))

from ELAN import __about__

project = "ELAN"
copyright = datetime.now().strftime("%Y") + ", REVERSAAL et Oslandia"
author = "REVERSAAL (INRAE) et Oslandia"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinxcontrib.mermaid'
]

templates_path = ["_templates"]
exclude_patterns = []
figure_language_filename = '{docs/}{en}/{basename}{.mmd}'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "piccolo_theme"
html_static_path = ["_static"]


# -- Choose variables to export to be usable in .rst files -------------------
# -- Need to do this in setup() because we need to know which language is being used


def setup(app):
    # Get latest version of ELAN
    CHANGELOG_REGEXP = r"(?<=##)\s*\[*(v?0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\]?(\(.*\))?(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\]*\s-\s*([\d\-/]{10})(.*?)(?=##|\Z)"
    match = re.search(
        pattern=CHANGELOG_REGEXP,
        string=(__about__.DIR_PLUGIN_ROOT.parent / "CHANGELOG.md").read_text(),
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        version = app.config.release = app.config.version = "ELAN VERSION NOT FOUND"
    else:
        version = app.config.release = app.config.version = match[0].split(" - ")[0].strip()

    date_update = format_date(datetime.now(), format="long", locale=app.config.language)
    qgis_version_min = __about__.__plugin_md__.get("general").get("qgisminimumversion")

    variables_to_export = ["version", "date_update", "qgis_version_min"]
    frozen_locals = dict(locals())
    app.config.rst_epilog = "\n".join(map(lambda x: f".. |{x}| replace:: {frozen_locals[x]}", variables_to_export))
