"""tp.libs.templating.discovery - Pattern matching and asset discovery module.

This module provides template-based asset discovery including:
- TemplateDiscovery: Find files matching templates
- DiscoveredAsset: Discovered asset with parsed tokens
- Glob/regex pattern generation from templates
"""

from __future__ import annotations

from tp.libs.templating.discovery.finder import (
    DiscoveredAsset,
    TemplateDiscovery,
)
from tp.libs.templating.discovery.glob import (
    glob_from_template,
    partial_regex_from_template,
    regex_from_template,
)

__all__ = [
    "TemplateDiscovery",
    "DiscoveredAsset",
    "glob_from_template",
    "regex_from_template",
    "partial_regex_from_template",
]
