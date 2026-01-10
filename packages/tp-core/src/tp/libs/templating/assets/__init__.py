"""tp.libs.templating.assets - Asset type management module.

This module provides asset type classification and validation including:
- AssetTypeDefinition: Definition of asset types with rules
- AssetTypeRegistry: Registry for managing asset types
- AssetValidator: Validation of names and paths
- ValidationResult: Result of validation operations
"""

from __future__ import annotations

from tp.libs.templating.assets.registry import AssetTypeRegistry
from tp.libs.templating.assets.types import (
    ANIMATION_ASSET,
    AUDIO_ASSET,
    BUILTIN_ASSET_TYPES,
    CHARACTER_ASSET,
    ENVIRONMENT_ASSET,
    MATERIAL_ASSET,
    PROP_ASSET,
    RIG_ASSET,
    TEXTURE_ASSET,
    AssetTypeDefinition,
)
from tp.libs.templating.assets.validator import (
    AssetValidator,
    ValidationResult,
)

__all__ = [
    # Types
    "AssetTypeDefinition",
    "BUILTIN_ASSET_TYPES",
    "CHARACTER_ASSET",
    "PROP_ASSET",
    "ENVIRONMENT_ASSET",
    "TEXTURE_ASSET",
    "MATERIAL_ASSET",
    "ANIMATION_ASSET",
    "RIG_ASSET",
    "AUDIO_ASSET",
    # Registry
    "AssetTypeRegistry",
    # Validator
    "AssetValidator",
    "ValidationResult",
]
