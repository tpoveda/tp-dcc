from __future__ import annotations

import json
from typing import Any

# maya.cmds is only available within Maya.
from maya import cmds  # type: ignore[import-not-found]
from tp.bootstrap.utils import dcc
from tp.libs.metadict import MetadataDictionary

DEFAULT_NODE_NAME = "tp_metanode"
DEFAULT_ATTRIBUTE_NAME = "tp_metadata"
ID_ATTRIBUTE_NAME = "tp_metadata_id"


class MayaMetadataDictionary(MetadataDictionary):
    """Metadata dictionary class for Maya application.

    This implementation stores metadata as a JSON-encoded string within a
    custom string attribute on a network node in the Maya scene.

    Attributes:
        priority: Higher priority ensures Maya implementation is used when available.
    """

    priority = 2

    def __init__(self, identifier: str, *args: Any, **kwargs: Any):
        """Initialize a Maya MetadataDictionary.

        Args:
            identifier: Unique identifier for this metadata dictionary.
            *args: Variable length argument list passed to parent.
            attribute_name: Optional custom attribute name for storing metadata.
                Defaults to DEFAULT_ATTRIBUTE_NAME.
            **kwargs: Arbitrary keyword arguments passed to parent.
        """

        # The name of the attribute that will hold the metadata dictionary.
        self._attribute_name: str = kwargs.pop(
            "attribute_name", DEFAULT_ATTRIBUTE_NAME
        )

        super().__init__(identifier=identifier, *args, **kwargs)

    @classmethod
    def usable(cls) -> bool:
        """Return whether this MetadataDictionary is usable in Maya.

        Returns:
            True if running inside Maya, False otherwise.
        """

        return dcc.is_maya()

    def _load_data(self) -> dict[str, Any]:
        """Load raw data from the Maya scene.

        Returns:
            Dictionary of loaded data.
        """

        try:
            attr_path = self._get_or_create_attribute()
            data = cmds.getAttr(attr_path)
            if data:
                return json.loads(data)
        except (json.JSONDecodeError, RuntimeError):
            # No existing data or invalid JSON.
            pass
        return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save raw data to the Maya scene.

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

        cmds.setAttr(self._get_or_create_attribute(), json_data, type="string")

    def delete(self) -> bool:
        """Delete the metadata node from the Maya scene.

        Returns:
            True if the node was deleted, False if it didn't exist.
        """

        for attr in cmds.ls(f"*.{ID_ATTRIBUTE_NAME}", recursive=True) or []:
            if cmds.getAttr(attr) == self.id:
                node_name = attr.split(".")[0]
                cmds.delete(node_name)
                return True
        return False

    def _get_or_create_attribute(self) -> str:
        """Return the attribute path for storing metadata, creating it if needed.

        Returns:
            Full path to the attribute (e.g., "tp_metanode.tp_metadata").
        """

        # Try to find a node within the scene with the metadata attribute.
        for attr in cmds.ls(f"*.{ID_ATTRIBUTE_NAME}", recursive=True) or []:
            if cmds.getAttr(attr) == self.id:
                return f"{attr.split('.')[0]}.{self._attribute_name}"

        # Create a new node and return the path to the metadata attribute.
        node = cmds.createNode("network", name=DEFAULT_NODE_NAME)
        attrs_to_create = {
            ID_ATTRIBUTE_NAME: self.id,
            self._attribute_name: "{}",
        }
        for attr_name, value in attrs_to_create.items():
            cmds.addAttr(node, shortName=attr_name, dataType="string")
            cmds.setAttr(f"{node}.{attr_name}", value, type="string")

        return f"{node}.{self._attribute_name}"
