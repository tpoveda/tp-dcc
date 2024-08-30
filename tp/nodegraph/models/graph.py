from __future__ import annotations

import typing

from ..core import consts

if typing.TYPE_CHECKING:
    from ..core.node import BaseNode


class NodeGraphModel:
    """Class that defines the model of the node graph."""

    def __init__(self):
        super().__init__()

        self.nodes: dict[str, BaseNode] = {}
        self.layout_direction: int = consts.LayoutDirection.Horizontal.value
        self.connector_style: int = consts.ConnectorStyle.Curved.value
        self.acyclic: bool = True
        self.connector_collision: bool = False
        self.connector_slicing: bool = True
        self.accept_connection_types: dict[str, set[str]] = {}
        self.reject_connection_types: dict[str, set[str]] = {}
        self.session: str = ""
        self.variables: list[consts.Variable] = []

        self._common_node_properties: dict[str, dict[str, dict[str, typing.Any]]] = {}

    def common_properties(self) -> dict[str, dict[str, dict[str, typing.Any]]]:
        """
        Returns the common properties of all nodes.

        :return: dictionary with the common properties of all nodes.
        """

        return self._common_node_properties

    def set_node_common_properties(self, attributes: dict):
        """
        Sets the common properties of all nodes.

        :param attributes: dictionary with the attributes to set.
        {
            "tp.nodegraph.nodes.BaseNode": {
                "attribute_name": {
                    "widget_type": 0",
                    "tab": "Properties",
                    "items": ["a", "b", "c"],
                    "range": (0, 100)
                }
            }
        }
        """

        for node_type, node_props in attributes.items():
            if node_type not in self._common_node_properties:
                self._common_node_properties[node_type] = node_props
                continue

            for prop_name, prop_attrs in node_props.items():
                common_props = self._common_node_properties[node_type]
                if prop_name not in common_props:
                    common_props[prop_name] = prop_attrs
                    continue
                common_props[prop_name].update(prop_attrs)

    def node_common_properties(
        self, node_type: str
    ) -> dict[str, dict[str, typing.Any]] | None:
        """
        Returns the common properties of a specific node type.

        :param node_type: type of the node.
        :return: dictionary with the common properties of the node.
        """

        return self._common_node_properties.get(node_type, None)

    def port_accept_connection_types(
        self, node_type: str, port_type: str, port_name: str
    ) -> dict[str, dict[str, str]]:
        """
        Returns the accepted port types for a given node type, port type and port name.

        :param node_type: type of the node.
        :param port_type: type of the port.
        :param port_name: name of the port.
        :return: accepted port types.
        """

        data = self.accept_connection_types.get(node_type) or {}
        accepted_types = data.get(port_type) or {}
        return accepted_types.get(port_name) or {}

    def add_port_accept_connection_type(
        self,
        port_name: str,
        port_type: str,
        node_type: str,
        accept_port_name: str,
        accept_port_type: str,
        accept_node_type: str,
    ):
        """
        Adds a constraint to "accept" a connection of a specific port type from a specific node type.

        :param port_name: name of the port.
        :param port_type: type of the port.
        :param node_type: type of the node.
        :param accept_port_name: port name to accept.
        :param accept_port_type: port type to accept.
        :param accept_node_type: port node type to accept.
        """

        connection_data = self.accept_connection_types
        keys = [node_type, port_type, port_name, accept_node_type]
        for key in keys:
            if key not in connection_data:
                # noinspection PyTypeChecker
                connection_data[key] = {}
            connection_data = connection_data[key]

        if accept_port_type not in connection_data:
            connection_data[accept_port_type] = {accept_port_name}
        else:
            connection_data[accept_port_type] = set(
                connection_data[accept_port_type]
            ) | {accept_port_name}

    def port_reject_connection_types(
        self, node_type: str, port_type: str, port_name: str
    ) -> dict[str, dict[str, str]]:
        """
        Returns the rejected port types for a given node type, port type and port name.

        :param node_type: type of the node.
        :param port_type: type of the port.
        :param port_name: name of the port.
        :return: rejected port types.
        """

        data = self.reject_connection_types.get(node_type) or {}
        rejected_types = data.get(port_type) or {}
        return rejected_types.get(port_name) or {}

    def add_port_reject_connection_type(
        self,
        port_name: str,
        port_type: str,
        node_type: str,
        reject_port_name: str,
        reject_port_type: str,
        reject_node_type: str,
    ):
        """
        Adds a constraint to "reject" a connection of a specific port type from a specific node type.

        :param port_name: name of the port.
        :param port_type: type of the port.
        :param node_type: type of the node.
        :param reject_port_name: port name to reject.
        :param reject_port_type: port type to reject.
        :param reject_node_type: port node type to reject.
        """

        connection_data = self.reject_connection_types
        keys = [node_type, port_type, port_name, reject_node_type]
        for key in keys:
            if key not in connection_data:
                # noinspection PyTypeChecker
                connection_data[key] = {}
            connection_data = connection_data[key]

        if reject_port_type not in connection_data:
            connection_data[reject_port_type] = {reject_port_name}
        else:
            connection_data[reject_port_type] = set(
                connection_data[reject_port_type]
            ) | {reject_port_name}
