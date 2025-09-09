from __future__ import annotations

import typing
from typing import Any
from abc import ABC, abstractmethod
from collections.abc import Generator

from tp.libs.python.helpers import ObjectDict

from ...base import constants
from ..nodes import NodeDescriptorType
from ..utils import traverse_descriptor_layer_dag

if typing.TYPE_CHECKING:
    from ..attributes import AttributeDescriptor


class LayerDescriptor(ObjectDict, ABC):
    """Base layer descriptor class.

    Layers are containers or organized data for a single scene
    structure (such as guides, rig, skeleton, ...).
    """

    # noinspection PyUnusedLocal
    @classmethod
    def from_data(cls, layer_data: dict[str, Any]) -> LayerDescriptor:
        """Creates a layer descriptor instance from a data dictionary.

        Args:
            layer_data: Dictionary containing the layer data.

        Returns:
            The created layer descriptor instance.
        """

        return cls()

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        """Serializes the layer descriptor to a dictionary.

        Returns:
            The serialized layer descriptor.
        """

        raise NotImplementedError(
            f"{self.__class__.__name__}.serialize() not implemented"
        )

    @property
    def settings(self) -> list[AttributeDescriptor]:
        """Returns the settings attributes for this layer.

        Returns:
            The settings attributes list.
        """

        return self.get(constants.SETTINGS_DESCRIPTOR_KEY, [])

    @property
    def metadata(self) -> list[AttributeDescriptor]:
        """Returns the metadata dictionary for this layer.

        Returns:
            The metadata dictionary.
        """

        return self.get(constants.METADATA_DESCRIPTOR_KEY, [])

    # === region Hierarchy === #

    def node(self, node_id: str) -> NodeDescriptorType:
        """Returns the node descriptor for the given node ID.

        Args:
            node_id: The ID of the node.

        Returns:
            The node descriptor.
        """

        found_node: NodeDescriptorType | None = None
        for dag_node in traverse_descriptor_layer_dag(self):
            if dag_node.id == node_id:
                found_node = dag_node
                break

        return found_node

    def has_node(self, node_id: str) -> bool:
        """Returns whether the layer has a node with the given ID.

        Args:
            node_id: The ID of the node.

        Returns:
            `True` if the node exists; `False` otherwise.
        """

        return self.node(node_id) is not None

    def find_nodes(self, *node_ids: str) -> list[NodeDescriptorType]:
        """Finds and returns a list of node descriptors for the given node IDs.

        Args:
            *node_ids: The IDs of the nodes to find.

        Returns:
            A list of found node descriptors.
        """

        found_nodes: list[NodeDescriptorType | None] = [None] * len(node_ids)
        for dag_node in traverse_descriptor_layer_dag(self):
            node_id = dag_node.id
            if node_id not in node_ids:
                continue
            found_nodes[node_ids.index(node_id)] = dag_node

        return found_nodes

    def nodes(self, include_root: bool = True) -> Generator[NodeDescriptorType]:
        """Generator that yields all node descriptors in the layer.

        Args:
            include_root: Whether to include the root node in the results.

        Yields:
            The next node descriptor in the layer.
        """

        for dag_node in traverse_descriptor_layer_dag(self):
            if not include_root and dag_node.id == "root":
                continue
            yield dag_node
