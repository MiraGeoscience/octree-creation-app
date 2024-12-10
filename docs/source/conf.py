# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                                '
#                                                                                         '
#  This file is part of octree-creation-app package.                                      '
#                                                                                         '
#  octree-creation-app is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                            '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from datetime import datetime
from importlib.metadata import version

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "octree-creation"
author = "Mira Geoscience Ltd."
project_copyright = "%Y, Mira Geoscience Ltd"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# The full version, including alpha/beta/rc tags.
release = version("octree-creation-app")
# The short X.Y.Z version.
version = ".".join(release.split(".")[:3])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = []
todo_include_todos = True

# -- Options for auto-doc ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#module-sphinx.ext.autodoc

autodoc_typehints = "signature"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_theme_options = {
    'description': f"version {release}",
}

# Enable numref
numfig = True

def get_copyright_notice():
    return f"Copyright {datetime.now().strftime(project_copyright)}"


rst_epilog = f"""
.. |copyright_notice| replace:: {get_copyright_notice()}.
"""

