from __future__ import annotations

import json
from typing import Any

# bpy is only available within Blender.
import bpy  # type: ignore[import-not-found]

from tp.bootstrap.utils import dcc
from tp.libs.metadict import MetadataDictionary

METADATA_PROPERTY_PREFIX = "tp_metadata_"


class BlenderMetadataDictionary(MetadataDictionary):
    """Metadata dictionary class for Blender application.

    This implementation stores metadata as custom properties on the scene object.
    The data is stored as a JSON-encoded string with a prefixed property name.

    Attributes:
        priority: Higher priority ensures Blender implementation is used when available.
    """

    priority = 2

    @classmethod
    def usable(cls) -> bool:
        """Return whether this MetadataDictionary is usable in Blender.

        Returns:
            True if running inside Blender, False otherwise.
        """

        return dcc.is_blender()

    @property
    def _property_name(self) -> str:
        """Return the custom property name for storing metadata.

        Returns:
            Custom property name.
        """

        return f"{METADATA_PROPERTY_PREFIX}{self.id}"

    def _load_data(self) -> dict[str, Any]:
        """Load raw data from Blender's scene custom properties.

        Returns:
            Dictionary of loaded data.
        """

        try:
            scene = bpy.context.scene
            if self._property_name in scene:
                data = scene[self._property_name]
                if isinstance(data, str):
                    return json.loads(data)
        except (json.JSONDecodeError, TypeError, KeyError):
            # No existing data or invalid JSON.
            pass
        return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save raw data to Blender's scene custom properties.

        Args:
            data: Dictionary data to save.

        Raises:
            ValueError: If the dictionary data cannot be serialized to JSON.
        """

        try:
            json_data = json.dumps(data)
        except (TypeError, ValueError) as err:
            raise ValueError(
                f"Could not serialize MetadataDictionary to JSON: {err}. "
                "Ensure all stored data is JSON serializable."
            ) from err

        bpy.context.scene[self._property_name] = json_data

    def delete(self) -> bool:
        """Delete the metadata from Blender's scene custom properties.

        Returns:
            True if the property was deleted, False if it didn't exist.
        """

        scene = bpy.context.scene
        if self._property_name in scene:
            del scene[self._property_name]
            return True
        return False
