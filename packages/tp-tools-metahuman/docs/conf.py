from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tp"))

project = "tp-tools-metahuman"
author = "Tomi Poveda"
release = "0.1.0"

extensions = [
    "myst_parser",  # Markdown support
    "sphinx.ext.autodoc",  # Extract docstrings
    "sphinx.ext.autosummary",  # Summary tables
    "sphinx.ext.napoleon",  # Google/Numpy docstring styles
    "sphinx.ext.todo",  # TODOs
    "sphinx.ext.viewcode",  # Add "View source" links
    "sphinx.ext.intersphinx",  # Link to external docs
    "sphinx.ext.coverage",  # Show undocumented objects
    "sphinx.ext.doctest",  # Docstring-based tests
    "sphinx_autodoc_typehints",  # Better type hint rendering
]

html_theme = "furo"
todo_include_todos = True
autosummary_generate = True
autodoc_typehints = "description"
napoleon_google_docstring = True

# Allow .md as well as .rst
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

exclude_patterns = ["_build"]
