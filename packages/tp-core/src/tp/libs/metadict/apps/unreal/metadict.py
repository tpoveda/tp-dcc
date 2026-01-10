from __future__ import annotations

import json
from typing import Any

# unreal is only available within Unreal Engine.
import unreal  # type: ignore[import-not-found]
from tp.bootstrap.utils import dcc
from tp.libs.metadict import MetadataDictionary

METADATA_TAG_PREFIX = "tp_metadata_"


class UnrealMetadataDictionary(MetadataDictionary):
    """Metadata dictionary class for Unreal Engine.

    This implementation stores metadata as asset metadata tags on the
    current level or a specified asset. The data is stored as a JSON-encoded
    string with a prefixed tag name.

    Attributes:
        priority: Higher priority ensures Unreal implementation is used when available.
    """

    priority = 2

    def __init__(self, identifier: str, *args: Any, **kwargs: Any):
        """Initialize an Unreal MetadataDictionary.

        Args:
            identifier: Unique identifier for this metadata dictionary.
            *args: Variable length argument list passed to parent.
            asset_path: Optional asset path for storing metadata. If not provided,
                uses the current world/level.
            **kwargs: Arbitrary keyword arguments passed to parent.
        """

        self._asset_path: str | None = kwargs.pop("asset_path", None)
        super().__init__(identifier=identifier, *args, **kwargs)

    @classmethod
    def usable(cls) -> bool:
        """Return whether this MetadataDictionary is usable in Unreal.

        Returns:
            True if running inside Unreal Engine, False otherwise.
        """

        return dcc.is_unreal()

    @property
    def _tag_name(self) -> str:
        """Return the metadata tag name for storing data.

        Returns:
            Metadata tag name.
        """

        return f"{METADATA_TAG_PREFIX}{self.id}"

    def _get_asset(self) -> "unreal.Object | None":  # type: ignore[name-defined]
        """Get the asset object to store metadata on.

        Returns:
            Asset object or None if not found.
        """

        if self._asset_path:
            return unreal.load_asset(self._asset_path)
        else:
            # Use the current world/level
            world = unreal.EditorLevelLibrary.get_editor_world()
            return world

    def _load_data(self) -> dict[str, Any]:
        """Load raw data from Unreal asset metadata.

        Returns:
            Dictionary of loaded data.
        """

        try:
            asset = self._get_asset()
            if asset is None:
                return {}

            # Get metadata using the asset registry
            asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
            asset_data = asset_registry.get_asset_by_object_path(
                unreal.Paths.get_path(asset.get_path_name())
            )

            if asset_data.is_valid():
                tag_value = asset_data.get_tag_value(self._tag_name)
                if tag_value:
                    return json.loads(tag_value)
        except (json.JSONDecodeError, TypeError, AttributeError):
            # No existing data or invalid JSON.
            pass
        return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save raw data to Unreal asset metadata.

        Args:
            data: Dictionary data to save.

        Raises:
            ValueError: If the dictionary data cannot be serialized to JSON.
            RuntimeError: If no valid asset is available.
        """

        asset = self._get_asset()
        if asset is None:
            raise RuntimeError("No valid asset found for storing metadata")

        try:
            json_data = json.dumps(data)
        except (TypeError, ValueError) as err:
            raise ValueError(
                f"Could not serialize MetadataDictionary to JSON: {err}. "
                "Ensure all stored data is JSON serializable."
            ) from err

        # Use EditorAssetLibrary to set metadata
        if self._asset_path:
            unreal.EditorAssetLibrary.set_metadata_tag(
                self._asset_path, self._tag_name, json_data
            )
        else:
            # For world/level, use different approach
            world = unreal.EditorLevelLibrary.get_editor_world()
            if world:
                # Store as level metadata using custom approach
                # Note: This may vary based on your Unreal setup
                level = world.get_current_level()
                if level:
                    unreal.EditorAssetLibrary.set_metadata_tag(
                        level.get_path_name(), self._tag_name, json_data
                    )

    def delete(self) -> bool:
        """Delete the metadata from Unreal asset.

        Returns:
            True if the metadata was deleted, False if it didn't exist.
        """

        asset = self._get_asset()
        if asset is None:
            return False

        try:
            if self._asset_path:
                # Remove metadata tag
                unreal.EditorAssetLibrary.remove_metadata_tag(
                    self._asset_path, self._tag_name
                )
                return True
            else:
                world = unreal.EditorLevelLibrary.get_editor_world()
                if world:
                    level = world.get_current_level()
                    if level:
                        unreal.EditorAssetLibrary.remove_metadata_tag(
                            level.get_path_name(), self._tag_name
                        )
                        return True
        except Exception:
            pass
        return False
