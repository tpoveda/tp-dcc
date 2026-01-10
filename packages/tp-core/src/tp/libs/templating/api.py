"""Unified API for tp.libs.templating.

This module provides the public API for all templating functionality:
- Naming conventions (solve, parse)
- Path templates (Template, PathResolver)
- Version management (VersionToken, VersionResolver)
- Asset validation (AssetValidator, AssetTypeRegistry)
- Discovery (TemplateDiscovery, DiscoveredAsset)
- Configuration (TemplateConfiguration)
- Context (TemplateContext, ContextStack)
"""

from __future__ import annotations

# =============================================================================
# Re-export asset management functionality
# =============================================================================
from tp.libs.templating.assets import (
    BUILTIN_ASSET_TYPES,
    AssetTypeDefinition,
    AssetTypeRegistry,
    AssetValidator,
    ValidationResult,
)

# =============================================================================
# Re-export configuration functionality
# =============================================================================
from tp.libs.templating.config import (
    ConfigurationMerger,
    TemplateConfiguration,
    TemplateConfigurationSchema,
    deep_merge,
)

# =============================================================================
# Re-export context functionality
# =============================================================================
from tp.libs.templating.context import (
    ContextStack,
    TemplateContext,
)

# =============================================================================
# Re-export discovery functionality
# =============================================================================
from tp.libs.templating.discovery import (
    DiscoveredAsset,
    TemplateDiscovery,
    glob_from_template,
    regex_from_template,
)

# =============================================================================
# Re-export error classes
# =============================================================================
from tp.libs.templating.errors import (
    ConfigurationError,
    ConventionNotFoundError,
    FormatError,
    ParseError,
    ResolveError,
    RuleNotFoundError,
    TokenNotFoundError,
    ValidationError,
    VersionParseError,
)

# =============================================================================
# Re-export naming functionality
# =============================================================================
from tp.libs.templating.naming.api import (
    active_naming_convention,
    naming_convention,
    naming_preset_manager,
    parse,
    parse_by_rule,
    reset_preset_manager,
    set_active_naming_convention,
    solve,
)
from tp.libs.templating.naming.config import (
    NamingConfiguration,
    add_preset_path,
    builtin_presets_path,
    get_configuration,
    preset_paths,
    remove_preset_path,
    reset_configuration,
    set_configuration,
)

# =============================================================================
# Re-export naming classes for type hints
# =============================================================================
from tp.libs.templating.naming.convention import NamingConvention
from tp.libs.templating.naming.preset import NamingPreset, PresetsManager
from tp.libs.templating.naming.rule import Rule
from tp.libs.templating.naming.token import KeyValue, Token

# =============================================================================
# Re-export path templating functionality
# =============================================================================
from tp.libs.templating.paths import (
    PathResolver,
    Resolver,
    Template,
    expand_pattern,
    keys_from_pattern,
    parse_path_by_pattern,
    path_from_parsed_data,
    regular_expression_from_pattern,
)

# =============================================================================
# Re-export versioning functionality
# =============================================================================
from tp.libs.templating.versioning import (
    VersionResolver,
    VersionToken,
)

__all__ = [
    # Naming API functions
    "naming_preset_manager",
    "reset_preset_manager",
    "naming_convention",
    "active_naming_convention",
    "set_active_naming_convention",
    "solve",
    "parse",
    "parse_by_rule",
    # Naming classes
    "NamingConvention",
    "Rule",
    "Token",
    "KeyValue",
    "PresetsManager",
    "NamingPreset",
    # Configuration (naming)
    "NamingConfiguration",
    "get_configuration",
    "set_configuration",
    "reset_configuration",
    "add_preset_path",
    "remove_preset_path",
    "preset_paths",
    "builtin_presets_path",
    # Path templating
    "Template",
    "Resolver",
    "PathResolver",
    "regular_expression_from_pattern",
    "expand_pattern",
    "keys_from_pattern",
    "parse_path_by_pattern",
    "path_from_parsed_data",
    # Versioning
    "VersionToken",
    "VersionResolver",
    # Asset management
    "AssetTypeDefinition",
    "AssetTypeRegistry",
    "AssetValidator",
    "ValidationResult",
    "BUILTIN_ASSET_TYPES",
    # Discovery
    "TemplateDiscovery",
    "DiscoveredAsset",
    "glob_from_template",
    "regex_from_template",
    # Configuration (unified)
    "TemplateConfiguration",
    "TemplateConfigurationSchema",
    "ConfigurationMerger",
    "deep_merge",
    # Context
    "TemplateContext",
    "ContextStack",
    # Errors
    "ParseError",
    "FormatError",
    "ResolveError",
    "TokenNotFoundError",
    "RuleNotFoundError",
    "ConventionNotFoundError",
    "ValidationError",
    "VersionParseError",
    "ConfigurationError",
]
