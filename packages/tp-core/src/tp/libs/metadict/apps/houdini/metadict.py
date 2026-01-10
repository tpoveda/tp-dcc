from __future__ import annotations

import json
from typing import Any

# hou module is only available within Houdini.
import hou  # type: ignore[import-not-found]
from loguru import logger

from tp.bootstrap.utils import dcc
from tp.libs.metadict import MetadataDictionary


class HoudiniMetadataDictionary(MetadataDictionary):
    """Metadata dictionary class for Houdini application.

    This implementation stores metadata as userData on the root Houdini node (hou.node("/")).
    The userData is stored as a JSON-encoded string with the dictionary's identifier as the key.

    Attributes:
        priority: Higher priority ensures Houdini implementation is used when available.
    """

    priority = 2

    @classmethod
    def usable(cls) -> bool:
        """Return whether this MetadataDictionary is usable in Houdini.

        Returns:
            True if running inside Houdini, False otherwise.
        """

        return dcc.is_houdini()

    def _load_data(self) -> dict[str, Any]:
        """Load raw data from Houdini's root node userData.

        Returns:
            Dictionary of loaded data.
        """

        try:
            user_data = hou.node("/").userData(self.id)
            if user_data:
                return json.loads(user_data)
        except (json.JSONDecodeError, TypeError) as err:
            logger.warning(f"Could not load metadata ({self.id}): {err}")
        return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save raw data to Houdini's root node userData.

        Args:
            data: Dictionary data to save.

        Raises:
            ValueError: If the dictionary data cannot be serialized to JSON.
        """

        try:
            hou.node("/").setUserData(self.id, json.dumps(data))
        except (TypeError, ValueError) as err:
            raise ValueError(
                f"Could not serialize MetadataDictionary to JSON: {err}. "
                "Ensure all stored data is JSON serializable."
            ) from err

    def delete(self) -> bool:
        """Delete the metadata from Houdini's root node userData.

        Returns:
            True if the userData was deleted, False if it didn't exist.
        """

        root = hou.node("/")
        if root.userData(self.id) is not None:
            root.destroyUserData(self.id)
            return True
        return False
