"""Asset type registry for managing asset type definitions."""

from __future__ import annotations

import logging
from typing import Iterator

from tp.libs.templating.assets.types import (
    BUILTIN_ASSET_TYPES,
    AssetTypeDefinition,
)

logger = logging.getLogger(__name__)


class AssetTypeRegistry:
    """Registry for managing asset type definitions.

    This class provides a centralized registry for asset types, allowing
    registration, lookup, and management of asset type definitions.

    Example:
        >>> from tp.libs.templating.assets import AssetTypeRegistry, AssetTypeDefinition
        >>>
        >>> # Create registry with built-in types
        >>> registry = AssetTypeRegistry(include_builtin=True)
        >>>
        >>> # Get a built-in type
        >>> character = registry.get_type("character")
        >>> print(character.description)
        'Character asset (humanoid, creature, NPC)'
        >>>
        >>> # Register a custom type
        >>> custom_type = AssetTypeDefinition(
        ...     name="vehicle",
        ...     description="Vehicle asset",
        ...     required_tokens=["name", "type"],
        ... )
        >>> registry.register_type(custom_type)
    """

    def __init__(self, include_builtin: bool = True):
        """AssetTypeRegistry constructor.

        Args:
            include_builtin: If True, register built-in asset types.
        """

        self._types: dict[str, AssetTypeDefinition] = {}

        if include_builtin:
            for asset_type in BUILTIN_ASSET_TYPES.values():
                self._types[asset_type.name] = asset_type

    def register_type(
        self, asset_type: AssetTypeDefinition, overwrite: bool = False
    ):
        """Register an asset type.

        Args:
            asset_type: Asset type definition to register.
            overwrite: If True, overwrite existing type with same name.

        Raises:
            ValueError: If type already exists and overwrite is False.
        """

        if asset_type.name in self._types and not overwrite:
            raise ValueError(
                f"Asset type '{asset_type.name}' already registered. "
                "Use overwrite=True to replace."
            )

        self._types[asset_type.name] = asset_type
        logger.debug(f"Registered asset type: {asset_type.name}")

    def unregister_type(self, name: str) -> bool:
        """Unregister an asset type.

        Args:
            name: Name of the asset type to unregister.

        Returns:
            True if type was unregistered, False if not found.
        """

        if name in self._types:
            del self._types[name]
            logger.debug(f"Unregistered asset type: {name}")
            return True
        return False

    def get_type(self, name: str) -> AssetTypeDefinition | None:
        """Get an asset type by name.

        Args:
            name: Name of the asset type.

        Returns:
            Asset type definition or None if not found.
        """

        return self._types.get(name)

    def has_type(self, name: str) -> bool:
        """Check if an asset type is registered.

        Args:
            name: Name of the asset type.

        Returns:
            True if type is registered.
        """

        return name in self._types

    def list_types(self) -> list[str]:
        """List all registered asset type names.

        Returns:
            List of registered type names.
        """

        return list(self._types.keys())

    def iterate_types(self) -> Iterator[AssetTypeDefinition]:
        """Iterate over all registered asset types.

        Yields:
            Asset type definitions.
        """

        yield from self._types.values()

    def types_by_category(self, category: str) -> list[AssetTypeDefinition]:
        """Get all asset types in a category.

        Args:
            category: Category name (from metadata).

        Returns:
            List of asset types in the category.
        """

        return [
            asset_type
            for asset_type in self._types.values()
            if asset_type.metadata.get("category") == category
        ]

    def types_with_extension(
        self, extension: str
    ) -> list[AssetTypeDefinition]:
        """Get all asset types that support a file extension.

        Args:
            extension: File extension (with or without dot).

        Returns:
            List of asset types supporting the extension.
        """

        if not extension.startswith("."):
            extension = f".{extension}"

        return [
            asset_type
            for asset_type in self._types.values()
            if extension.lower()
            in [ext.lower() for ext in asset_type.file_extensions]
        ]

    def clear(self):
        """Clear all registered asset types."""

        self._types.clear()
        logger.debug("Cleared all asset types from registry")

    def type_count(self) -> int:
        """Return the number of registered asset types.

        Returns:
            Number of registered types.
        """

        return len(self._types)

    def to_dict(self) -> dict[str, dict]:
        """Serialize registry to dictionary.

        Returns:
            Dictionary representation of all asset types.
        """

        return {
            name: {
                "name": asset_type.name,
                "description": asset_type.description,
                "naming_rule": asset_type.naming_rule,
                "path_template": asset_type.path_template,
                "required_tokens": asset_type.required_tokens,
                "allowed_tokens": asset_type.allowed_tokens,
                "file_extensions": asset_type.file_extensions,
                "metadata": asset_type.metadata,
            }
            for name, asset_type in self._types.items()
        }

    @classmethod
    def from_dict(cls, data: dict[str, dict]) -> AssetTypeRegistry:
        """Create registry from dictionary.

        Args:
            data: Dictionary of asset type definitions.

        Returns:
            New registry instance.
        """

        registry = cls(include_builtin=False)

        for name, type_data in data.items():
            asset_type = AssetTypeDefinition(
                name=type_data.get("name", name),
                description=type_data.get("description", ""),
                naming_rule=type_data.get("naming_rule", ""),
                path_template=type_data.get("path_template", ""),
                required_tokens=type_data.get("required_tokens", []),
                allowed_tokens=type_data.get("allowed_tokens", []),
                file_extensions=type_data.get("file_extensions", []),
                metadata=type_data.get("metadata", {}),
            )
            registry.register_type(asset_type)

        return registry
