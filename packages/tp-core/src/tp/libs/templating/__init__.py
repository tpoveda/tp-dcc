"""tp.libs.templating - Unified templating system for AAA game production.

This library provides:
- Name templating: Token-based naming conventions
- Path templating: Path pattern resolution with template references
- Version management: Auto-increment and version tracking (coming soon)
- Asset validation: Asset type classification and validation (coming soon)
- Pattern discovery: Find assets matching templates (coming soon)
- Configuration: YAML/JSON configuration management (coming soon)
- Context inheritance: Hierarchical template contexts (coming soon)

Example:
    >>> from tp.libs.templating import api
    >>>
    >>> # Set up naming convention
    >>> convention = api.naming_convention("global", set_as_active=True)
    >>>
    >>> # Solve a name using tokens
    >>> name = api.solve(rule_name="asset", side="left", type="control")
    >>> print(name)  # "L_arm_CTRL"
    >>>
    >>> # Use path templates
    >>> from tp.libs.templating.paths import Template, PathResolver
    >>> template = Template(name="asset", pattern="/content/{type}/{name}")
    >>> path = template.format({"type": "characters", "name": "hero"})
    >>> print(path)  # "/content/characters/hero"
"""

from __future__ import annotations

__version__ = "1.0.0"

# Convenient imports for direct access
from tp.libs.templating.api import *
