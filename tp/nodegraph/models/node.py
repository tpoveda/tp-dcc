from __future__ import annotations


import typing
from typing import Any

from ..core import consts
from ..views import uiconsts
from ..core.exceptions import (
    NodePropertyNotFoundError,
    NodePropertyReservedError,
    NodePropertyAlreadyExistsError,
)

if typing.TYPE_CHECKING:
    from .graph import NodeGraphModel  # pragma: no coverage
    from .port import PortModel  # pragma: no coverage


class NodeModel:
    """Base model class for all nodes in the node graph."""

    def __init__(self):
        super().__init__()

        self.id = hex(id(self))
        self.name: str = "node"
        self.type: str | None = None
        self.visible: bool = True
        self.selected: bool = False
        self.disabled: bool = False
        self.color: tuple[int, int, int, int] = (13, 18, 23, 255)
        self.border_color: tuple[int, int, int, int] = (74, 84, 85, 255)
        self.text_color: tuple[int, int, int, int] = (255, 255, 255, 180)
        self.width: float = uiconsts.NODE_WIDTH
        self.height: float = uiconsts.NODE_HEIGHT
        self.xy_pos: tuple[float, float] = (0.0, 0.0)
        self.layout_direction: int = consts.LayoutDirection.Horizontal.value
        self.icon_path: str | None = None
        self.title_font_name: str = "Roboto"
        self.title_font_size: int = 10
        self.title_color: tuple[int, int, int, int] = (30, 30, 30, 200)
        self.title_text_color: tuple[int, int, int, int] = (255, 255, 255, 180)
        self.inputs: dict[str, PortModel] = {}
        self.outputs: dict[str, PortModel] = {}
        self.port_deletion_allowed: bool = False
        self.subgraph_session: dict = {}

        self._graph_model: NodeGraphModel | None = None
        self._custom_properties: dict[str, Any] = {}

        # Temporal properties to store data before the graph model is set. Clear once the node is added to a graph.
        self._temp_property_attributes: dict[str, dict[str, Any]] = {}
        # Temporal property widget types to store data before the graph model is set.
        # Clear once the node is added to a graph.
        self._temp_property_widget_types = {
            "type": uiconsts.PropertyWidget.Label.value,
            "id": uiconsts.PropertyWidget.Label.value,
            "icon_path": uiconsts.PropertyWidget.Hidden.value,
            "name": uiconsts.PropertyWidget.LineEdit.value,
            "color": uiconsts.PropertyWidget.ColorPicker.value,
            "border_color": uiconsts.PropertyWidget.ColorPicker.value,
            "text_color": uiconsts.PropertyWidget.ColorPicker.value,
            "disabled": uiconsts.PropertyWidget.CheckBox.value,
            "selected": uiconsts.PropertyWidget.Hidden.value,
            "width": uiconsts.PropertyWidget.Hidden.value,
            "height": uiconsts.PropertyWidget.Hidden.value,
            "xy_pos": uiconsts.PropertyWidget.Hidden.value,
            "layout_direction": uiconsts.PropertyWidget.Hidden.value,
            "inputs": uiconsts.PropertyWidget.Hidden.value,
            "outputs": uiconsts.PropertyWidget.Hidden.value,
            "title_font_name": uiconsts.PropertyWidget.Hidden.value,
            "title_font_size": uiconsts.PropertyWidget.Hidden.value,
            "title_color": uiconsts.PropertyWidget.Hidden.value,
            "title_text_color": uiconsts.PropertyWidget.Hidden.value,
        }
        self._temp_accept_connection_types: dict[str, set[str]] = {}
        self._temp_reject_connection_types: dict[str, set[str]] = {}

    def __repr__(self) -> str:
        """
        Returns a string representation of the node model.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self.name}") object at {self.id}>'  # pragma: no coverage

    @property
    def graph_model(self) -> NodeGraphModel:
        """
        Getter method that returns the node graph model.

        :return: node graph model.
        """

        return self._graph_model

    @graph_model.setter
    def graph_model(self, value: NodeGraphModel):
        """
        Setter method that sets the node graph model.

        :param value: node graph model.
        """

        self._graph_model = value

    @property
    def properties(self) -> dict[str, Any]:
        """
        Getter method that returns all node properties.

        :return: all node properties.
        """

        properties = self.__dict__.copy()
        exclude = [
            "_custom_properties",
            "_graph_model",
            "_temp_property_attributes",
            "_temp_property_widget_types",
            "_temp_accept_connection_types",
            "_temp_reject_connection_types",
        ]
        [properties.pop(i) for i in exclude if i in properties]

        return properties

    @property
    def custom_properties(self) -> dict[str, Any]:
        """
        Getter method that returns all custom node properties.

        :return: all custom node properties.
        """

        return self._custom_properties

    def is_custom_property(self, name: bool) -> bool:
        """
        Returns whether the property with given name is a custom property.

        :param name: name of the property to check.
        :return: whether the property is a custom property.
        """

        return name in self._custom_properties

    def property(self, name: str) -> Any:
        """
        Returns the value of the property with given name.

        :param name: name of the property whose value to retrieve.
        :return: property value.
        """

        properties = self.properties
        return (
            properties[name]
            if name in properties
            else self._custom_properties.get(name)
        )

    def add_property(
        self,
        name: str,
        value: Any,
        items: list[str] | None = None,
        value_range: tuple[int, int] | list[int, int] | None = None,
        widget_type: int | None = None,
        widget_tooltip: str | None = None,
        tab: str | None = None,
    ):
        """
        Adds a custom property for the node.

        :param name: name of the property to create.
        :param value: value of the property.
        :param items: list of items for the property.
        :param value_range: range of the property.
        :param widget_type: type of widget to use for the property.
        :param widget_tooltip: tooltip to display for the widget.
        :param tab: tab to display the property in.
        """

        widget_type = widget_type or uiconsts.PropertyWidget.Hidden
        tab = tab or "Properties"

        if name in self.properties:
            raise NodePropertyReservedError(name)
        if name in self._custom_properties:
            raise NodePropertyAlreadyExistsError(self.type, name)

        self._custom_properties[name] = value

        if self._graph_model is None:
            self._temp_property_widget_types[name] = widget_type
            self._temp_property_attributes[name] = {"tab": tab}
            if items:
                self._temp_property_attributes[name]["items"] = items
            if value_range:
                self._temp_property_attributes[name]["range"] = value_range
            if widget_tooltip:
                self._temp_property_attributes[name]["tooltip"] = widget_tooltip
        else:
            attrs = {self.type: {name: {"widget_type": widget_type, "tab": tab}}}
            if items:
                attrs[self.type][name]["items"] = items
            if value_range:
                attrs[self.type][name]["range"] = value_range
            if widget_tooltip:
                attrs[self.type][name]["tooltip"] = widget_tooltip
            self._graph_model.set_node_common_properties(attrs)

    def set_property(self, name: str, value: Any):
        """
        Sets the value of the property with given name.

        :param name: name of the property to set.
        :param value: value to set.
        :raises NodePropertyNotFoundError: If the property with given name is not found.
        """

        # If the property already has the same value, we skip it.
        if self.property(name) == value:
            return

        if name == "node_type":
            name = "type"

        if name in self.properties:
            setattr(self, name, value)
        elif name in self._custom_properties:
            self._custom_properties[name] = value
        else:
            raise NodePropertyNotFoundError(self.type, name)

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

        if self.graph_model:
            self.graph_model.add_port_accept_connection_type(
                port_name,
                port_type,
                node_type,
                accept_port_name,
                accept_port_type,
                accept_node_type,
            )
            return

        connection_data = self._temp_accept_connection_types
        keys = [node_type, port_type, port_name, accept_node_type]
        for key in keys:
            if key not in connection_data:
                # noinspection PyTypeChecker
                connection_data[key] = {}
            connection_data = connection_data[key]

        if accept_port_type not in connection_data:
            connection_data[accept_port_type] = {accept_port_name}
        else:
            connection_data[accept_port_type].add(accept_port_name)

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

        if self.graph_model:
            self.graph_model.add_port_reject_connection_type(
                port_name,
                port_type,
                node_type,
                reject_port_name,
                reject_port_type,
                reject_node_type,
            )
            return

        connection_data = self._temp_reject_connection_types
        keys = [node_type, port_type, port_name, reject_node_type]
        for key in keys:
            if key not in connection_data:
                # noinspection PyTypeChecker
                connection_data[key] = {}
            connection_data = connection_data[key]

        if reject_port_type not in connection_data:
            connection_data[reject_port_type] = {reject_port_name}
        else:
            connection_data[reject_port_type].add(reject_port_name)

    def tab_name(self, name) -> str:
        """
        Returns the name of the tab to show within properties editor.

        :param name: name of the tab.
        :return: string
        """

        model = self._graph_model
        if model is None:
            attrs = self._temp_property_attributes.get(name)
            if attrs:
                return attrs[name].get("tab")

        return model.node_common_properties(self.type)[name]["tab"]

    def widget_type(self, name: str) -> int:
        """
        Returns the widget type of the property with given name.

        :param name: name of the property.
        :return: widget type.
        """

        model = self._graph_model
        if model is None:
            return self._temp_property_widget_types.get(name)
        return model.node_common_properties(self.type)[name]["widget_type"]

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """
        Returns a dictionary representation of the port model.

        :return: dictionary representation.
        """

        node_dict = self.__dict__.copy()
        node_id = node_dict.pop("id")

        inputs: dict = {}
        outputs: dict = {}
        input_ports: list = []
        output_ports: list = []
        for name, model in node_dict.pop("inputs").items():
            if self.port_deletion_allowed:
                input_ports.append(
                    {
                        "name": name,
                        "multi_connection": model.multi_connection,
                        "display_name": model.display_name,
                    }
                )
            connected_ports = model.to_dict()["connected_ports"]
            if connected_ports:
                inputs[name] = connected_ports
        for name, model in node_dict.pop("outputs").items():
            if self.port_deletion_allowed:
                output_ports.append(
                    {
                        "name": name,
                        "multi_connection": model.multi_connection,
                        "display_name": model.display_name,
                    }
                )
            connected_ports = model.to_dict()["connected_ports"]
            if connected_ports:
                outputs[name] = connected_ports
        if inputs:
            node_dict["inputs"] = inputs
        if outputs:
            node_dict["outputs"] = outputs
        if self.port_deletion_allowed:
            node_dict["input_ports"] = input_ports
            node_dict["output_ports"] = output_ports
        if self.subgraph_session:
            node_dict["subgraph_session"] = self.subgraph_session
        custom_properties = node_dict.pop("_custom_properties")
        if custom_properties:
            node_dict["custom_properties"] = custom_properties
        exclude = [
            "_graph_model",
            "_temp_property_attributes",
            "_temp_property_widget_types",
            "_temp_accept_connection_types",
            "_temp_reject_connection_types",
        ]
        [node_dict.pop(i) for i in exclude if i in node_dict.keys()]

        return {node_id: node_dict}
