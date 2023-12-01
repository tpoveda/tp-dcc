from __future__ import annotations

import uuid
import typing
from typing import Any

from tp.common.nodegraph.core import consts, errors

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.models.graph import NodeGraphModel
    from tp.common.nodegraph.models.socket import SocketModel


class NodeModel:
    def __init__(self):
        super().__init__()

        self.type: str | None = None
        self.uuid = str(uuid.uuid4())
        self.icon: str | None = None
        self.name = 'node'
        self.color = consts.NODE_COLOR
        self.border_color = consts.NODE_BORDER_COLOR
        self.header_color = consts.NODE_HEADER_COLOR
        self.text_color = consts.NODE_TEXT_COLOR
        self.disabled = False
        self.selected = False
        self.visible = True
        self.width = 100.0
        self.height = 80.0
        self.pos = [0.0, 0.0]
        self.layout_direction = consts.LayoutDirection.Horizontal.value
        self._custom_properties: dict = {}

        self.inputs: dict[str, SocketModel] = {}
        self.outputs: dict[str, SocketModel] = {}
        self.socket_deletion_allowed = False

        self._graph_model: NodeGraphModel | None = None

        # temporal caches used to store node property attributes and widget types.
        # those caches are cleared when node is added to the graph.
        self._temp_property_attributes: dict = {}
        self._temp_property_widget_types = {}

    def __repr__(self) -> str:
        return f'>{self.__class__.__name__}("{self.name}") object at {self.uuid}>'

    @property
    def graph_model(self) -> NodeGraphModel:
        """
        Returns graph model (which is set when node is added into a graph).

        :return: NodeGraphModel
        """

        return self._graph_model

    @graph_model.setter
    def graph_model(self, value: NodeGraphModel):
        """
        Sets graph model this node belongs to.

        :param NodeGraphModel value: graph model.
        """

        self._graph_model = value

    @property
    def properties(self) -> dict:
        """
        Getter method that returns all default node properties.

        :return: node properties.
        :rtype: dict
        """

        properties = self.__dict__.copy()
        exclude = ['_custom_properties', '_graph_model', '_temp_property_attrs', '_temp_property_widget_types']
        [properties.pop(i) for i in exclude if i in properties.keys()]
        return properties

    @property
    def custom_properties(self) -> dict:
        """
        Returns all custom properties specified by the user.

        :return: node custom properties.
        :rtype: dict
        """

        return self._custom_properties

    def add_property(
            self, name: str, value: Any, items: list[str] | None = None, value_range: tuple[int, int] | None = None,
            widget_type: int | None = None, widget_tooltip: str | None = None, tab: str | None = None):
        """
        Adds a custom property to the node model.

        :param str name: name of the property.
        :param Any value: property value to set.
        :param list[str] or None items: list of items (used by NODE_PROPERTY_COMBOBOX).
        :param tuple[int, int] or None value_range: minimum and maximum values (used by NODE_PROPERTY_SLIDER).
        :param str or None widget_type: widget type flag.
        :param str or None widget_tooltip: custom tooltip for the property widget.
        :param str or None tab: widget tab name.
        :raises errors.NodePropertyError: if given property name is reserved for default node properties.
        :raises errors.NodePropertyError: if property with given name already exists.
        """

        widget_type = widget_type or consts.NodePropertyWidget.Hidden.value
        tab = tab or 'Properties'

        if name in self.properties:
            raise errors.NodePropertyError(f'"{name}" reserved for default property.')
        if name in self.custom_properties:
            raise errors.NodePropertyError(f'"{name}" property already exists.')

        self._custom_properties[name] = value

        if self._graph_model is None:
            self._temp_property_widget_types[name] = widget_type
            self._temp_property_attributes[name] = {'tab': tab}
            if items:
                self._temp_property_attributes[name]['items'] = items
            if value_range:
                self._temp_property_attributes[name]['range'] = value_range
            if widget_tooltip:
                self._temp_property_attributes[name]['tooltip'] = widget_tooltip
        else:
            attrs = {self.type: {name: {'widget_type': widget_type, 'tab': tab}}}
            if items:
                attrs[self.type][name]['items'] = items
            if value_range:
                attrs[self.type][name]['range'] = value_range
            if widget_tooltip:
                attrs[self.type][name]['tooltip'] = widget_tooltip
            self._graph_model.set_node_common_properties(attrs)

    def property(self, name: str) -> Any:
        """
        Returns the value of the property with given name.

        :param str name: name of the property whose value we want to retrieve.
        :return: property value.
        :rtype: Any
        """

        return self.properties[name] if name in self.properties else self._custom_properties.get(name)

    def set_property(self, name: str, value: Any):
        """
        Sets the value of the property with given name.

        :param str name: name of the property to set.
        :param Any value: new property value.
        :raises errors.NodePropertyError: if the property to set does not exist.
        """

        if name in self.properties:
            self.properties[name] = value
        elif name in self._custom_properties:
            self._custom_properties[name] = value
        else:
            raise errors.NodePropertyError(f'No property "{name}"')
