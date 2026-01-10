"""tp.libs.templating.config - Enhanced configuration module.

This module provides configuration management including:
- TemplateConfiguration: Complete serializable configuration
- Schema classes for tokens, rules, templates, asset types
- Configuration merging utilities
"""

from __future__ import annotations

from tp.libs.templating.config.loader import TemplateConfiguration
from tp.libs.templating.config.merger import (
    ConfigurationMerger,
    apply_overrides,
    deep_merge,
    merge_lists_by_key,
)
from tp.libs.templating.config.schema import (
    AssetTypeSchema,
    PathTemplateSchema,
    RuleSchema,
    TemplateConfigurationSchema,
    TokenSchema,
)

__all__ = [
    # Loader
    "TemplateConfiguration",
    # Schema
    "TemplateConfigurationSchema",
    "TokenSchema",
    "RuleSchema",
    "PathTemplateSchema",
    "AssetTypeSchema",
    # Merger
    "deep_merge",
    "merge_lists_by_key",
    "apply_overrides",
    "ConfigurationMerger",
]
