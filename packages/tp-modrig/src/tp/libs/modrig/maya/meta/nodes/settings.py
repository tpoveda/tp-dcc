from __future__ import annotations

from typing import Any

from tp.libs.maya.om import attributetypes, plugs
from tp.libs.maya.wrapper import DGNode, factory

from ...base import constants


class SettingsNode(DGNode):
    """Class that represents a settings metanode within the Maya scene."""

    # noinspection PyMethodOverriding,PyShadowingBuiltins
    def create(
        self,
        name: str,
        id: str,
        node_type: str = "network",
    ) -> SettingsNode:
        """Build the node within the Maya scene.

        Args:
            name: Name of the new node.
            id: ID to assign to the node.
            node_type: Maya node type to create. Default is 'network'.

        Returns:
            Newly created metanode instance.
        """

        node = factory.create_dg_node(name=name, node_type=node_type)
        self.setObject(node)
        self.addAttribute(
            constants.ID_ATTR, type=attributetypes.kMFnDataString, value=id, locked=True
        )

        return self

    def serializeFromScene(self, *args, **kwargs) -> list[dict[str, Any]]:
        """Serialize this node's data from the scene into a dictionary.

        Returns:
            A list of dictionaries containing the serialized data of the node's
            extra attributes.
        """

        skip = (constants.ID_ATTR,)
        attr_data = [
            plugs.serialize_plug(p.plug())
            for p in self.iterateExtraAttributes(skip=skip)
        ]
        return [i for i in attr_data if i]

    def id(self) -> str:
        """Return the ID of this settings node.

        The ID is a UUID (Unique Universal Identifier) assigned to the node
        when it is created. Used to uniquely identify the node within the
        scene.

        Returns:
            The node ID as a string.
        """

        id_attr = self.attribute(constants.ID_ATTR)
        return id_attr.value() if id_attr is not None else ""
