#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

import os
import sys

# Make the cosmonium package importable from the repo root.
sys.path.insert(0, os.path.abspath('..'))
# Also add third-party libraries bundled with the project.
sys.path.insert(1, os.path.abspath('../third-party'))
# CEFPanda and glTF modules aree not at top level
sys.path.insert(1, '../third-party/cefpanda')
sys.path.insert(1, '../third-party/gltf')

# -- Project information -----------------------------------------------------

project = 'Cosmonium'
author = 'Laurent Deru'
copyright = '2018-2026, Laurent Deru'

# Read version from the package without importing optional C extensions.
try:
    from cosmonium.version import version_str

    release = version_str
except Exception:
    release = '0.3.0'

version = '.'.join(release.split('.')[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    # Auto-generate API docs from docstrings.
    'sphinx.ext.autodoc',
    # Parse Google-style docstrings (Args:, Returns:, Raises:, ...).
    'sphinx.ext.napoleon',
    # Add [source] links back to highlighted source code.
    'sphinx.ext.viewcode',
    # Cross-reference the Python standard library.
    'sphinx.ext.intersphinx',
    # Collect summary tables of all documented items.
    'sphinx.ext.autosummary',
]

# -- Napoleon (Google-style docstring) settings ------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# -- Autodoc settings --------------------------------------------------------

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'special-members': '__init__',
}

# Suppress warnings about missing stubs for C extensions
autodoc_mock_imports = [
    # Cosmonium C extension module
    'cosmonium_engine',
]

# -- Autosummary settings ----------------------------------------------------

autosummary_generate = True
autosummary_generate_overwrite = True

# -- Intersphinx mapping -----------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'titles_only': False,
}
html_static_path = ['_static']

# -- Templates and static assets ---------------------------------------------

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
