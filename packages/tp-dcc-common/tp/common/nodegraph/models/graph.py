from __future__ import annotations

import typing

from tp.common.nodegraph.core import consts

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import BaseNode


class NodeGraphModel:
    """
    Class that defines the model of a node graph
    """

    def __init__(self):
        super().__init__()

        self.nodes: dict[str, BaseNode] = {}
        self.layout_direction = consts.LayoutDirection.Horizontal.value

        self._common_node_properties: dict[str, dict] = {}

    def common_properties(self) -> dict:
        """
        Returns all common node properties.

        :return: common node properties.
        """

        return self._common_node_properties

    def node_common_properties(self, node_type: int | str) -> dict | None:
        """
        Returns all the common properties for the registered node.

        :param str or int node_type: node type to get common properties of.
        :return: dictionary of node common properties.
        :rtype: dict or None
        """

        return self._common_node_properties.get(node_type)

    def set_node_common_properties(self, node_attributes: dict):
        """
        Stores common node properties.

        :param dict node_attributes: dictionary containing node IDs as keys and node attributes as values.
        {
            'node_type':
            {
                'my_property':
                {
                    'widget_type': 0,
                    'tab': 'Properties',
                    'items': ['foo', 'bar', 'test'],
                    'range': (0, 100)
                }
            }
        }
        """

        for node_type, node_properties in node_attributes.items():

            # register properties into the graph
            if node_type not in self._common_node_properties:
                self._common_node_properties[node_type] = node_properties
                continue

            # update properties
            for property_name, property_attrs in node_properties.items():
                common_properties = self._common_node_properties[node_type]
                if property_name not in common_properties:
                    common_properties[property_name] = property_attrs
                    continue
                common_properties[property_name].update(property_attrs)
