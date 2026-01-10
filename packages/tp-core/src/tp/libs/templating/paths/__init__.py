"""tp.libs.templating.paths - Path templating module.

This module provides path pattern resolution functionality including:
- Template: Path patterns with placeholders and regex support
- Pattern: Functions for parsing and formatting paths
- PathResolver: Links path templates to naming conventions
"""

from __future__ import annotations

# Import pattern functions first (no dependencies on template)
from tp.libs.templating.paths.pattern import (
    expand_pattern,
    keys_from_pattern,
    parse_path_by_pattern,
    path_from_parsed_data,
    regular_expression_from_pattern,
)

# Import resolver (depends on template)
from tp.libs.templating.paths.resolver import PathResolver

# Import template classes (depends on pattern)
from tp.libs.templating.paths.template import Resolver, Template

__all__ = [
    "Template",
    "Resolver",
    "PathResolver",
    "regular_expression_from_pattern",
    "expand_pattern",
    "keys_from_pattern",
    "parse_path_by_pattern",
    "path_from_parsed_data",
]
