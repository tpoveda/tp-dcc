from __future__ import annotations

import typing
import logging
from collections import deque
from typing import Type, Callable, Iterable, Any

from tp.python import decorators, paths

from .port import NodePort
from .consts import PortType
from . import exceptions, datatypes
from ..views import uiconsts
from ..models.node import NodeModel
from ..views.node import AbstractNodeView, NodeView
from ..widgets.node import AbstractNodeWidget, NodeComboBox, NodeLineEdit, NodeCheckBox
from ..core.commands import (
    PropertyChangedCommand,
    NodeVisibleCommand,
    NodeWidgetVisibleCommand,
)

if typing.TYPE_CHECKING:
    from .datatypes import DataType
    from .graph import NodeGraph  # pragma: no cover
    from ..widgets.properties.abstract import AbstractPropertyWidget  # pragma: no cover

logger = logging.getLogger(__name__)


class BaseNode:
    """Base class for all nodes in the node graph."""

    # noinspection SpellCheckingInspection
    # Unique node identifier domain.
    __identifier__ = "tp.nodegraph.nodes"

    # Initial base node name.
    NODE_NAME: str | None = "Node"

    # Node category. Used to group nodes in the nodes palette.
    CATEGORY: str = "General"

    # Node palette label. Used to display the node in the nodes palette.
    PALETTE_LABEL: str = ""

    # Node icon path. Used to display the node icon in the nodes palette.
    ICON_PATH: str = paths.canonical_path("../resources/icons/node_base.png")

    def __init__(self, view_class: Type[AbstractNodeView | NodeView]):
        super().__init__()

        self._graph: NodeGraph | None = None
        self._model = NodeModel()
        self._model.type = self.type
        self._model.name = self.NODE_NAME
        self.model.icon_path = self.ICON_PATH

        self._view = view_class()
        self._view.node_type = self.type
        self._view.name = self.name
        self._view.icon = self.icon
        self._view.id = self.id
        self._view.layout_direction = self.layout_direction

    def __repr__(self) -> str:
        """
        Returns a string representation of the node.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self.NODE_NAME}") object at {hex(id(self))}>'  # pragma: no cover

    # noinspection PyMethodParameters
    @decorators.classproperty
    def type(cls) -> str:
        """
        Returns the type of the node.

        :return: node type.
        """

        return f"{cls.__identifier__}.{cls.__name__}"

    @property
    def model(self) -> NodeModel:
        """
        Returns the model of the node.

        :return: node model.
        """

        return self._model

    @model.setter
    def model(self, value: NodeModel):
        """
        Setter method that sets the model of the node.

        :param value: node model.
        """

        self._model = value
        self._model.type = self.type
        self._model.id = self.view.id

        self.update_view()

    @property
    def view(self) -> AbstractNodeView | NodeView:
        """
        Getter method that returns the view of the node.

        :return: node view.
        """

        return self._view

    @view.setter
    def view(self, value: AbstractNodeView | NodeView):
        """
        Setter method that sets the view of the node.

        :param value: node view.
        """

        if self._view:
            old_view = self._view
            scene = self._view.scene()
            scene.removeItem(old_view)
            self._view = value
            scene.addItem(self._view)
        else:
            self._view = value
        self.NODE_NAME = self._view.name

        self.update_view()

    @property
    def id(self) -> str:
        """
        Returns the ID of the node.

        :return: node ID.
        """

        return self.model.id

    @property
    def graph(self) -> NodeGraph:
        """
        Returns the graph the node belongs to.

        :return: node graph.
        """

        return self._graph

    @graph.setter
    def graph(self, value: NodeGraph):
        """
        Setter method that sets the graph the node belongs to.

        :param value: node graph.
        """

        self._graph = value
        self._model.graph_model = value.model

        if self._graph:
            nodes_title_font, nodes_title_size = self._graph.settings.node_title_font
            self._model.title_font_name = nodes_title_font
            self._model.title_font_size = nodes_title_size

        self.update_view()

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of the node.

        :return: node name.
        """

        return self.model.name

    @name.setter
    def name(self, value: str):
        """
        Setter method that sets the name of the node.

        :param value:  name to set.
        """

        self.set_property("name", value)

    @property
    def icon(self) -> str:
        """
        Getter method that returns the icon of the node.

        :return: node icon.
        """

        return self.model.icon_path

    @icon.setter
    def icon(self, value: str):
        """
        Setter method that sets the icon of the node.

        :param value: icon to set.
        """

        self.set_property("icon_path", value)

    @property
    def enabled(self):
        """
        Getter method that returns whether the node is enabled.

        :return: whether the node is enabled.
        """

        return not self.model.disabled

    @enabled.setter
    def enabled(self, flag: bool):
        """
        Setter method that sets whether the node is enabled.

        :param flag: whether the node is enabled.
        """

        self.set_property("disabled", not flag)

    @property
    def disabled(self):
        """
        Getter method that returns whether the node is disabled.

        :return: whether the node is disabled.
        """

        return self.model.disabled

    @disabled.setter
    def disabled(self, flag: bool):
        """
        Setter method that sets whether the node is disabled.

        :param flag: whether the node is disabled.
        """

        self.set_property("disabled", flag)

    @property
    def selected(self) -> bool:
        """
        Getter method that returns whether the node is selected.

        :return: whether the node is selected.
        """

        self._model.selected = self.view.isSelected()
        return self.model.selected

    @selected.setter
    def selected(self, flag: bool):
        """
        Setter method that sets whether the node is selected.

        :param flag: whether the node is selected.
        """

        self.set_property("selected", flag)

    @property
    def color(self) -> tuple[int, int, int]:
        """
        Getter method that returns the RGB color of the node in 0 - 255 range.

        :return: node color.
        """

        r, g, b, _ = self.model.color
        return r, g, b

    @color.setter
    def color(self, value: tuple[int, int, int]):
        """
        Setter method that sets the RGB color of the node in 0 - 255 range.

        :param value: node color.
        """

        r, g, b = value
        self.set_property("color", (r, g, b, 255))

    @property
    def text_color(self) -> tuple[int, int, int]:
        """
        Getter method that returns the RGB text color of the node in 0 - 255 range.

        :return: node text color.
        """

        r, g, b, _ = self.model.text_color
        return r, g, b

    @text_color.setter
    def text_color(self, value: tuple[int, int, int]):
        """
        Setter method that sets the RGB text color of the node in 0 - 255 range.

        :param value: node text color.
        """

        r, g, b = value
        self.set_property("text_color", (r, g, b, 255))

    @property
    def layout_direction(self) -> int:
        """
        Getter method that returns the layout direction of the node.

        :return: layout direction of the node.
        """

        return self.model.layout_direction

    @layout_direction.setter
    def layout_direction(self, value: int):
        """
        Setter method that sets the layout direction of the node.

        :param value: layout direction of the node.
        """

        self.model.layout_direction = value
        self.view.layout_direction = value

    @property
    def x_pos(self) -> float:
        """
        Getter method that returns the x position of the node.

        :return: x position of the node.
        """

        return self.model.xy_pos[0]

    @x_pos.setter
    def x_pos(self, value: float):
        """
        Setter method that sets the x position of the node.

        :param value: x position of the node.
        """

        self.xy_pos = (value, self.xy_pos[1])

    @property
    def y_pos(self) -> float:
        """
        Getter method that returns the y position of the node.

        :return: y position of the node.
        """

        return self.model.xy_pos[1]

    @y_pos.setter
    def y_pos(self, value: float):
        """
        Setter method that sets the y position of the node.

        :param value: y position of the node.
        """

        self.xy_pos = (self.xy_pos[0], value)

    @property
    def xy_pos(self) -> tuple[float, float]:
        """
        Getter method that returns the position of the node.

        :return: node position.
        """

        if self.view.xy_pos and self.view.xy_pos != self.model.xy_pos:
            self.model.xy_pos = self.view.xy_pos

        return self.model.xy_pos

    @xy_pos.setter
    def xy_pos(self, value: tuple[float, float]):
        """
        Setter method that sets the position of the node.

        :param value: node position.
        """

        self.set_property("xy_pos", (float(value[0]), float(value[1])))

    def has_property(self, name: str) -> bool:
        """
        Returns whether the node has a property with given name.

        :param name: name of the property to check.
        :return: whether the node has the property.
        """

        return name in self.model.custom_properties

    def property(self, name: str) -> Any:
        """
        Returns a property value of the node.

        :param name: name of the property to get.
        :return: property value.
        """

        if self.graph and name == "selected":
            self.model.set_property(name, self.view.selected)

        return self.model.property(name)

    def properties(self) -> dict[str, Any]:
        """
        Returns the custom properties of the node.

        :return: custom properties.
        """

        properties = self.model.to_dict()[self.id].copy()
        properties["id"] = self.id
        return properties

    def create_property(
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
        Creates a custom property for the node.

        :param name: name of the property to create.
        :param value: value of the property.
        :param items: list of items for the property.
        :param value_range: range of the property.
        :param widget_type: type of widget to use for the property.
        :param widget_tooltip: tooltip to display for the widget.
        :param tab: tab to display the property in.
        """

        self.model.add_property(
            name=name,
            value=value,
            items=items,
            value_range=value_range,
            widget_type=widget_type,
            widget_tooltip=widget_tooltip,
            tab=tab,
        )

    def set_property(self, name: str, value: Any, push_undo: bool = True):
        """
        Sets a custom property of the node.

        :param name: name of the property to set.
        :param value: value to set.
        :param push_undo: whether to push the change to the undo stack.
        """

        if self.property(name) == value:
            return

        # Prevent nodes from having the same name.
        if self.graph and name == "name":
            value = self.graph.unique_node_name(value)
            self.NODE_NAME = value

        if self.graph:
            command = PropertyChangedCommand(self, name, value)
            if push_undo:
                self.graph.undo_stack.push(command)
            else:
                command.redo()
        else:
            if hasattr(self.view, name):
                setattr(self.view, name, value)
            self.model.set_property(name, value)

        if self.model.is_custom_property(name):
            self.view.draw()

    def update_model(self):
        """
        Updates the node model from view.
        """

        for name, value in self.view.properties().items():
            if name in self.model.properties:
                setattr(self.model, name, value)
            if name in self.model.custom_properties.keys():
                self.model.custom_properties[name] = value

    def update_view(self):
        """
        Updates the node view from model.
        """

        data = self.model.to_dict()[self.model.id]
        data["id"] = self.model.id
        self.view.from_dict(data)

    def serialize(self) -> dict:
        """
        Serializes the node to a dictionary.

        :return: serialized node dictionary.
        """

        return self.model.to_dict()

    def pre_deserialize(self, data: dict):
        """
        Called before deserializing the node.

        :param data: data to deserialize.
        """

    def post_deserialize(self, data: dict):
        """
        Called after deserializing the node.

        :param data: data to deserialize.
        """

        pass

    def deserialize(self, data: dict):
        """
        Deserializes the node from a dictionary.

        :param data: data to deserialize.
        """

        self.pre_deserialize(data)

        # Set node properties and custom properties
        for property_name, property_value in self.model.properties.items():
            if property_name in data:
                self.model.set_property(property_name, property_value)
        for property_name, property_value in data.get("custom", {}).items():
            self.model.set_property(property_name, property_value)
            if isinstance(self, BaseNode):
                self.view.widgets[property_name].set_value(property_value)

        if data.get("port_deletion_allowed", False):
            self.set_ports(
                {
                    "input_ports": data["input_ports"],
                    "output_ports": data["output_ports"],
                }
            )

        self.post_deserialize(data)


class Node(BaseNode):
    """Class that defines a node in the node graph."""

    # Defines whether the node can be executed.
    IS_EXEC: bool = True

    # Defines whether default input and output executable ports should be created.
    # This only applies if IS_EXEC is True.
    AUTO_INIT_EXECS: bool = True

    def __init__(self, view_class: Type[AbstractNodeView | NodeView] | None = None):
        super().__init__(view_class=view_class or NodeView)

        self._inputs: list[NodePort] = []
        self._outputs: list[NodePort] = []
        self._required_inputs: deque[NodePort] = deque()
        self._exec_in_socket: NodePort | None = None
        self._exec_out_socket: NodePort | None = None
        self._is_compiled: bool = False
        self._is_invalid: bool = False

        self._setup_ports()
        self.setup_signals()
        self.setup_widgets()

    @property
    def icon(self) -> str | None:
        """
        Returns the icon of the node.

        :return: path to the node icon.
        """

        return self.model.icon_path

    @icon.setter
    def icon(self, value: str | None):
        """
        Setter method that sets the icon of the node.

        :param value: path to the node icon.
        """

        self.set_property("icon", value)

    @property
    def inputs(self) -> list[NodePort]:
        """
        Returns the input ports of the node.

        :return: input ports.
        """

        return self._inputs

    @property
    def outputs(self) -> list[NodePort]:
        """
        Returns the output ports of the node.

        :return: output ports.
        """

        return self._outputs

    @property
    def exec_inputs(self) -> list[NodePort]:
        """
        Returns the executable input ports of the node.

        :return: executable input ports.
        """

        return [port for port in self.inputs if port.data_type == datatypes.Exec]

    @property
    def non_exec_inputs(self) -> list[NodePort]:
        """
        Returns the non-executable input ports of the node.

        :return: non-executable input ports.
        """

        return [port for port in self.inputs if port.data_type != datatypes.Exec]

    @property
    def exec_outputs(self) -> list[NodePort]:
        """
        Returns the executable output ports of the node.

        :return: executable output ports.
        """

        return [port for port in self.outputs if port.data_type == datatypes.Exec]

    @property
    def non_exec_outputs(self) -> list[NodePort]:
        """
        Returns the non-executable output ports of the node.

        :return: non-executable output ports.
        """

        return [port for port in self.outputs if port.data_type != datatypes.Exec]

    @property
    def port_deletion_allowed(self) -> bool:
        """
        Returns whether ports can be deleted from the node.

        :return: whether ports can be deleted.
        """

        return self.model.port_deletion_allowed

    @port_deletion_allowed.setter
    def port_deletion_allowed(self, flag: bool):
        """
        Setter method that sets whether ports can be deleted from the node.

        :param flag: whether ports can be deleted.
        """

        self.set_property("port_deletion_allowed", flag)

    @property
    def is_compiled(self) -> bool:
        """
        Returns whether the node is compiled.

        :return: whether the node is compiled.
        """

        return self._is_compiled

    @is_compiled.setter
    def is_compiled(self, flag: bool):
        """
        Setter method that sets whether the node is compiled.

        :param flag: whether the node is compiled.
        """

        if self._is_compiled == flag:
            return

        self._is_compiled = flag
        self.mark_children_compiled(flag)

    @property
    def is_invalid(self) -> bool:
        """
        Returns whether the node is invalid.

        :return: whether the node is invalid.
        """

        return self._is_invalid

    @is_invalid.setter
    def is_invalid(self, flag: bool):
        """
        Setter method that sets whether the node is invalid.

        :param flag: whether the node is invalid.
        """

        self._is_invalid = flag
        logger.debug(f"{self} marked as invalid")

    @property
    def exec_in_socket(self) -> NodePort | None:
        """
        Returns the input executable port of the node.

        :return: input executable port.
        """

        return self._exec_in_socket

    @property
    def exec_out_socket(self) -> NodePort | None:
        """
        Returns the output executable port of the node.

        :return: output executable port.
        """

        return self._exec_out_socket

    def update_model(self):
        """
        Updates the node model from view.
        """

        for name, value in self.view.properties().items():
            if name in ["inputs", "outputs"]:
                continue
            self.model.set_property(name, value)

        try:
            widgets = self.view.widgets
        except AttributeError:
            widgets = {}
        for name, widget in widgets:
            self.model.set_property(name, widget.value())

    def set_property(self, name: str, value: Any, push_undo: bool = True):
        """
        Sets a custom property of the node.

        :param name: name of the property to set.
        :param value: value to set.
        :param push_undo: whether to push the change to the undo stack.
        """

        if self.property(name) == value:
            return

        if name == "visible":
            if self.graph:
                command = NodeVisibleCommand(self, value)
                self.graph.undo_stack.push(command) if push_undo else command.redo()
                return
        elif name == "disabled":
            # Redraw the connectors in the scene.
            for port_view in self.view.inputs + self.view.outputs:
                for connector_view in port_view.connected_connectors:
                    connector_view.update()

        super().set_property(name, value, push_undo=push_undo)

    def setup_ports(self):
        """
        Function that sets up the default ports for the node.

        Note:
            This function should be overridden by subclasses.
        """

        pass

    def input_ports(self) -> dict[str, NodePort]:
        """
        Returns the input ports of the node.

        :return: input ports.
        """

        return {port.name: port for port in self._inputs}

    def output_ports(self) -> dict[str, NodePort]:
        """
        Returns the output ports of the node.

        :return: output ports.
        """

        return {port.name: port for port in self._outputs}

    def add_input_port(self, port: NodePort):
        """
        Adds an input port to the node.

        :param port: input port to add.
        """

        port.model.type = PortType.Input.value
        self._inputs.append(port)
        self.model.inputs[port.name] = port.model

    def delete_input_port(
        self, port: NodePort | str | int, force: bool = False
    ) -> bool:
        """
        Deletes given input port from the node.

        :param port: input port to delete.
        :param force: whether to force the deletion of the port.
        :return: whether the port was removed.
        """

        if type(port) in [int, str]:
            port = self.input(port)
            if port is None:
                return False
        if not self.port_deletion_allowed and not force:
            raise exceptions.NodePortNotRemovableError(port.name, self.type)
        if port.locked and not force:
            raise exceptions.NodePortLockedError(port.name, self.type)

        self._inputs.remove(port)
        self.model.inputs.pop(port.name)
        self.view.delete_input(port.view)
        port.model.node = None
        self.view.draw()

        return True

    def add_input(
        self,
        data_type: DataType,
        name: str = "input",
        value: Any = None,
        display_name: bool = True,
        multi_port: bool = False,
        color: tuple[int, int, int] | None = None,
        locked: bool = False,
        painter_function: Callable = None,
    ) -> NodePort:
        """
        Adds a new input port to the node.

        :param data_type: type of input data.
        :param name: name of the input port.
        :param value: value of the input port.
        :param display_name: whether to display the name of the input port.
        :param multi_port: whether to allow port to have more than one connection.
        :param color: optional RGB port color (0 - 255).
        :param locked: whether the port is locked.
        :param painter_function: optional painter function to use for the port.
        :return: newly added input port.
        :raises NodeInputPortAlreadyExistsError: When the input port already exists.
        """

        if name in self.input_ports():
            raise exceptions.NodeInputPortAlreadyExistsError(name, self.type)

        display_name = display_name if data_type != datatypes.Exec else False

        view = self.view.add_input(
            data_type=data_type,
            name=name,
            display_name=display_name,
            multi_port=multi_port,
            locked=locked,
            painter_function=painter_function,
        )
        if color:
            view.color = color
            view.border_color = [min([255, max([0, i + 80])]) for i in color]

        port = NodePort(self, view)
        port.model.name = name
        port.model.data_type = data_type
        port.model.display_name = display_name
        port.model.multi_connection = multi_port
        port.model.locked = locked
        port.model.value = value
        self.add_input_port(port)

        return port

    def input(self, index: int | str) -> NodePort | None:
        """
        Returns the input port at given index or with given name.

        :param index: index or name of the input port to return.
        :return: input port.
        """

        if type(index) is int:
            if index < len(self._inputs):
                return self._inputs[index]
        elif type(index) is str:
            return self.input_ports().get(index, None)

        return None

    def set_input(self, index: int, port: NodePort):
        """
        Creates a connection from input port of given index to the given target port.

        :param index: index of the input port to connect.
        :param port: target port to connect to.
        """

        source_port = self.input(index)
        source_port.connect_to(port)

    def mark_input_as_required(self, port: NodePort | str | int) -> bool:
        """
        Marks given input port as required.

        :param port: input port to mark as required.
        :return: whether the input port was marked as required
        """

        input_port = self.input(port) if isinstance(port, (str, int)) else port
        if not input_port:
            logger.error(
                f"Cannot mark input {port} as required. Failed to find socket."
            )
            return False

        if not input_port.type == PortType.Input.value:
            logger.error(
                "Cannot mark output port as required. Use `mark_output_as_required()` instead."
            )
            return False

        self._required_inputs.append(input_port)

        return True

    def mark_inputs_as_required(self, ports: Iterable[NodePort]):
        """
        Marks given input ports as required.

        :param ports: input ports to mark as required.
        """

        for port in ports:
            self.mark_input_as_required(port)

    def add_output_port(self, port: NodePort):
        """
        Adds an output port to the node.

        :param port: output port to add.
        """

        port.model.type = PortType.Output.value
        self._outputs.append(port)
        self.model.outputs[port.name] = port.model

    def add_output(
        self,
        data_type: DataType,
        name: str = "output",
        value: Any = None,
        max_connections: int = 0,
        multi_port: bool = True,
        display_name: bool = True,
        color: tuple[int, int, int] | None = None,
        locked: bool = False,
        painter_function: Callable = None,
    ):
        """
        Adds a new output port to the node.

        :param data_type: type of output data.
        :param name: name of the output port.
        :param value: value of the output port.
        :param max_connections: maximum number of connections the port can have.
        :param multi_port: whether to allow port to have more than one connection.
        :param display_name: whether to display the name of the output port.
        :param color: optional RGB port color (0 - 255).
        :param locked: whether the port is locked.
        :param painter_function: optional painter function to use for the port.
        :return: newly added output port.
        :raises NodeOutputPortAlreadyExistsError: When the output port already exists.
        """

        if name in self.output_ports():
            raise exceptions.NodeOutputPortAlreadyExistsError(name, self.type)

        view = self.view.add_output(
            data_type=data_type,
            name=name,
            display_name=display_name,
            multi_port=multi_port,
            locked=locked,
            painter_function=painter_function,
        )
        if color:
            view.color = color
            view.border_color = [min([255, max([0, i + 80])]) for i in color]

        port = NodePort(self, view)
        port.model.name = name
        port.model.data_type = data_type
        port.model.display_name = display_name
        port.model.multi_connection = multi_port
        port.model.locked = locked
        port.model.value = value
        self.add_output_port(port)

        return port

    def delete_output_port(
        self, port: NodePort | str | int, force: bool = False
    ) -> bool:
        """
        Deletes given output port from the node.

        :param port: output port to delete.
        :param force: whether to force the deletion of the port.
        :return: whether the port was removed.
        """

        if type(port) in [int, str]:
            port = self.output(port)
            if port is None:
                return False
        if not self.port_deletion_allowed and not force:
            raise exceptions.NodePortNotRemovableError(port.name, self.type)
        if port.locked and not force:
            raise exceptions.NodePortLockedError(port.name, self.type)

        self._outputs.remove(port)
        self.model.outputs.pop(port.name)
        self.view.delete_output(port.view)
        port.model.node = None
        self.view.draw()

        return True

    def output(self, index: int | str) -> NodePort | None:
        """
        Returns the output port at given index.

        :param index: index of the output port to return.
        :return: output port.
        """

        if type(index) is int:
            if index < len(self._outputs):
                return self._outputs[index]
        elif type(index) is str:
            return self.output_ports().get(index, None)

        return None

    def set_output(self, index: int, port: NodePort):
        """
        Creates a connection from output port of given index to the given target port.

        :param index: index of the output port to connect.
        :param port: target port to connect to.
        """

        source_port = self.output(index)
        source_port.connect_to(port)

    def clear_and_set_ports(self, port_data: dict):
        """
        Clears all existing ports and sets new ports to the node.

        :param port_data: dictionary of port data.
        """

        if not self.port_deletion_allowed:
            raise RuntimeError(
                "Ports can only be set if port_deletion_allowed is set to True"
            )

        # TODO: This function does not requires into account some stuff such as required inputs, etc.

        for port in self._inputs:
            self._view.delete_input(port.view)
            port.model.node = None
        for port in self._outputs:
            self._view.delete_output(port.view)
            port.model.node = None
        self._inputs.clear()
        self._outputs.clear()
        self._model.outputs.clear()
        self._model.inputs.clear()

        [
            self.add_input(
                self.graph.factory.data_type_by_name(port["data_type"]),
                name=port["name"],
                multi_port=port["multi_connection"],
                display_name=port["display_name"],
                locked=port.get("locked") or False,
                value=port.get("value", None),
            )
            for port in port_data["input_ports"]
        ]
        [
            self.add_output(
                self.graph.factory.data_type_by_name(port["data_type"]),
                name=port["name"],
                multi_port=port["multi_connection"],
                display_name=port["display_name"],
                locked=port.get("locked") or False,
                value=port.get("value", None),
            )
            for port in port_data["output_ports"]
        ]

        self._view.draw()

    def set_ports(self, port_data: dict):
        """
        Updates node input and output ports from serialized port data.

        :param port_data: dictionary of port data.
        .notes:: this function only can be used if `port_deletion_allowed` is set to True.
        Example of port data:
        {
            'input_ports':
                [{
                    'name': 'input',
                    'multi_connection': True,
                    'display_name': 'Input',
                    'locked': False
                }],
            'output_ports':
                [{
                    'name': 'output',
                    'multi_connection': True,
                    'display_name': 'Output',
                    'locked': False
                }]
        }
        """

        for data in port_data["input_ports"]:
            input_port = self.input(data["name"])
            if input_port is None:
                logger.warning(
                    f'Input port "{data["name"]}" not found in node "{self.name}"'
                )
                continue

            input_port.data_type = self.graph.factory.data_type_by_name(
                data["data_type"]
            )
            input_port.set_visible(data["visible"], push_undo=False)
            input_port.set_locked(data["locked"], push_undo=False)
            input_port.view.display_name = data["display_name"]
            input_port.multi_connection = data["multi_connection"]
            input_port.max_connections = data["max_connections"]
            input_port.set_value(data.get("value", None))

        for data in port_data["output_ports"]:
            output_port = self.output(data["name"])
            output_port.data_type = self.graph.factory.data_type_by_name(
                data["data_type"]
            )
            output_port.set_visible(data["visible"], push_undo=False)
            output_port.set_locked(data["locked"], push_undo=False)
            output_port.view.display_name = data["display_name"]
            output_port.multi_connection = data["multi_connection"]
            output_port.max_connections = data["max_connections"]
            output_port.set_value(data.get("value", None))

    def connected_input_nodes(self) -> dict[NodePort, list[BaseNode]]:
        """
        Returns a dictionary of connected input nodes.

        :return: dictionary of connected input nodes.
        """

        nodes: dict[NodePort, list[BaseNode]] = {}
        for port in self.inputs:
            nodes[port] = [
                connected_port.node for connected_port in port.connected_ports()
            ]

        return nodes

    def connected_output_nodes(self) -> dict[NodePort, list[BaseNode]]:
        """
        Returns a dictionary of connected output nodes.

        :return: dictionary of connected output nodes.
        """

        nodes: dict[NodePort, list[BaseNode]] = {}
        for port in self.outputs:
            nodes[port] = [
                connected_port.node for connected_port in port.connected_ports()
            ]

        return nodes

    def remove_existing_ports(self, force: bool = True) -> bool:
        """
        Removes all existing ports from the node.

        :return: whether the ports were removed.
        """

        if not force and not self.port_deletion_allowed:
            return False

        for port in self.inputs.copy():
            self.delete_input_port(port, force=force)
        for port in self.outputs.copy():
            self.delete_output_port(port, force=force)

        return True

    def accepted_port_types(self, port: NodePort):
        """
        Returns a dictionary of connection constraints of the port types that allow for a connection with this port.

        :return: dictionary of connection constraints.
        """

        ports = self.inputs + self.outputs
        if port not in ports:
            raise exceptions.NodePortNotFoundError(port.name, self.type)

        if self.graph:
            accepted_types = self.graph.model.port_accept_connection_types(
                node_type=self.type, port_type=port.type, port_name=port.name
            )
        else:
            # noinspection PyProtectedMember
            data = self.model._temp_accept_connection_types.get(self.type) or {}
            accepted_types = data.get(port.type) or {}
            accepted_types = accepted_types.get(port.name) or {}

        return accepted_types

    def add_accept_port_type(self, port: NodePort, port_type_data: dict):
        """
        Adds a constraint to "accept" a connection of a specific port type from a specific node type.

        Once a constraint has been added, only ports of that type specified will be allowed a connection.

        :param port: port to add the constraint to.
        :param port_type_data: port type data to add.

        Example of port_type_data:
        {
            'port_name': 'foo',
            'port_type': PortType.Input.value,
            'node_type': 'tp.nodegraph.nodes.NodeClass'
        }
        """

        # Check if the port is in the node's inputs or outputs.
        node_ports = self.inputs + self.outputs
        if port not in node_ports:
            raise exceptions.NodePortNotFoundError(port.name, self.type)

        self.model.add_port_accept_connection_type(
            port_name=port.name,
            port_type=port.type,
            node_type=self.type,
            accept_port_name=port_type_data["port_name"],
            accept_port_type=port_type_data["port_type"],
            accept_node_type=port_type_data["node_type"],
        )

    def rejected_port_types(self, port: NodePort):
        """
        Returns a dictionary of connection constraints of the port types that are not allowed for a connection with
         this port.

        :return: dictionary of connection constraints.
        """

        ports = self.inputs + self.outputs
        if port not in ports:
            raise exceptions.NodePortNotFoundError(port.name, self.type)

        if self.graph:
            rejected_types = self.graph.model.port_reject_connection_types(
                node_type=self.type, port_type=port.type, port_name=port.name
            )
        else:
            # noinspection PyProtectedMember
            data = self.model._temp_reject_connection_types.get(self.type) or {}
            rejected_types = data.get(port.type) or {}
            rejected_types = rejected_types.get(port.name) or {}

        return rejected_types

    def add_reject_port_type(self, port: NodePort, port_type_data: dict):
        """
        Adds a constraint to "reject" a connection of a specific port type from a specific node type.

        Once a constraint has been added, only ports of that type specified will be allowed a connection.

        :param port: port to add the constraint to.
        :param port_type_data: port type data to add.

        Example of port_type_data:
        {
            'port_name': 'foo',
            'port_type': PortType.Input.value,
            'node_type': 'tp.nodegraph.nodes.NodeClass'
        }
        """

        # Check if the port is in the node's inputs or outputs.
        node_ports = self.inputs + self.outputs
        if port not in node_ports:
            raise exceptions.NodePortNotFoundError(port.name, self.type)

        self.model.add_port_reject_connection_type(
            port_name=port.name,
            port_type=port.type,
            node_type=self.type,
            reject_port_name=port_type_data["port_name"],
            reject_port_type=port_type_data["port_type"],
            reject_node_type=port_type_data["node_type"],
        )

    def setup_signals(self):
        """
        Function that sets up the default signals for the node.

        Note:
            This function should be overridden by subclasses.
        """

        pass

    def setup_widgets(self):
        """
        Function that sets up the default widgets for the node.

        Note:
            This function should be overridden by subclasses.
        """

        pass

    def widgets(self) -> dict[str, AbstractNodeWidget]:
        """
        Returns the widgets of the node.

        :return: list of property widgets.
        """

        return self.view.widgets

    def widget(self, name: str) -> AbstractPropertyWidget | None:
        """
        Returns the widget with given name.

        :param name: name of the widget to return.
        :return: property widget.
        """

        return self.widgets().get(name, None)

    def add_custom_widget(
        self,
        widget: AbstractNodeWidget,
        widget_type: int | None = None,
        tab: str | None = None,
    ):
        """
        Adds a custom widget to the node.

        :param widget: widget to add.
        :param widget_type: type of the widget.
        :param tab: tab to display the widget in.
        """

        widget_type = widget_type or uiconsts.PropertyWidget.Hidden.value
        self.create_property(
            widget.name, value=widget.get_value(), widget_type=widget_type, tab=tab
        )
        widget.valueChanged.connect(lambda k, v: self.set_property(k, v))
        widget.node = self
        self.view.add_widget(widget)
        self.view.draw()

    def add_combo_menu(
        self,
        name: str,
        label: str = "",
        items: list[str] | None = None,
        tooltip: str | None = None,
        tab: str | None = None,
    ):
        """
        Creates a custom property and embeds a `QComboBox` widget into the node.

        :param name: name for the custom property.
        :param label: label to be displayed.
        :param items: optional items to be added into the menu.
        :param tooltip: optional widget tooltip.
        :param tab: name of the widget tab to display in.
        """

        self.create_property(
            name,
            value=items[0] if items else None,
            items=items or [],
            widget_type=uiconsts.PropertyWidget.ComboBox.value,
            widget_tooltip=tooltip,
            tab=tab,
        )
        widget = NodeComboBox(label, name=name, items=items, parent=self.view)
        widget.setToolTip(tooltip or "")
        widget.valueChanged.connect(lambda k, v: self.set_property(k, v))
        # noinspection PyTypeChecker
        self.view.add_widget(widget)
        self.view.draw()

    def add_text_input(
        self,
        name: str,
        label: str = "",
        text: str = "",
        placeholder_text: str = "",
        tooltip: str | None = None,
        tab: str | None = None,
    ):
        """
        Creates a custom property and embeds a `QLineEdit` widget into the node.

        :param name: name for the custom property.
        :param label: label to be displayed.
        :param text: optional default text.
        :param placeholder_text: optional placeholder text.
        :param tooltip: optional widget tooltip.
        :param tab: name of the widget tab to display in.
        """

        self.create_property(
            name,
            value=text,
            widget_type=uiconsts.PropertyWidget.LineEdit.value,
            widget_tooltip=tooltip,
            tab=tab,
        )
        widget = NodeLineEdit(
            label,
            name=name,
            text=text,
            placeholder_text=placeholder_text,
            parent=self.view,
        )
        widget.setToolTip(tooltip or "")
        widget.valueChanged.connect(lambda k, v: self.set_property(k, v))
        # noinspection PyTypeChecker
        self.view.add_widget(widget)
        self.view.draw()

    def add_checkbox(
        self,
        name: str,
        label: str = "",
        text: str = "",
        state: bool = False,
        tooltip: str | None = None,
        tab: str | None = None,
    ):
        """
        Creates a custom property and embeds a `QCheckBox` widget into the node.

        :param name: name for the custom property.
        :param label: label to be displayed.
        :param text: optional text to display next to the checkbox.
        :param state: default check state.
        :param tooltip: optional widget tooltip.
        :param tab: name of the widget tab to display in.
        """

        self.create_property(
            name,
            value=state,
            widget_type=uiconsts.PropertyWidget.CheckBox.value,
            widget_tooltip=tooltip,
            tab=tab,
        )
        widget = NodeCheckBox(
            label, name=name, text=text, state=state, parent=self.view
        )
        widget.setToolTip(tooltip or "")
        widget.valueChanged.connect(lambda k, v: self.set_property(k, v))
        # noinspection PyTypeChecker
        self.view.add_widget(widget)
        self.view.draw()

    def show_widget(self, name: str, push_undo: bool = True):
        """
        Shows an embedded node widget.

        :param name: node property name for the widget.
        :param push_undo: whether to register the command to the undo stack.
        """

        if not self.view.has_widget(name):
            return
        command = NodeWidgetVisibleCommand(self, name, True)
        self.graph.undo_stack.push(command) if push_undo else command.redo()

    def hide_widget(self, name: str, push_undo: bool = True):
        """
        Hides an embedded node widget.

        :param name: node property name for the widget.
        :param push_undo: whether to register the command to the undo stack.
        """

        if not self.view.has_widget(name):
            return
        command = NodeWidgetVisibleCommand(self, name, False)
        self.graph.undo_stack.push(command) if push_undo else command.redo()

    def children(self, recursive: bool = False) -> list[Node]:
        """
        Returns the children nodes of the node.

        :param recursive: whether to return children recursively.
        :return: list of children nodes.
        """

        children: list[Node] = []
        for output in self.outputs:
            for child_port in output.connected_ports():
                children.append(child_port.node)
        if recursive:
            for child_node in children:
                children += child_node.children(recursive=True)

        return children

    def executable_children(self) -> list[Node]:
        """
        Returns the executable children nodes of the node.

        :return: list of executable children nodes.
        """

        children: list[Node] = []
        for exec_out in self.exec_outputs:
            children += [port.node for port in exec_out.connected_ports()]

        return children

    def mark_children_compiled(self, flag: bool):
        """
        Marks all children of the node as compiled.

        :param flag: whether to mark children as compiled.
        """

        if flag:
            return
        for child_node in self.children():
            child_node.is_compiled = flag
            child_node.mark_children_compiled(flag)

    def verify(self) -> bool:
        """
        Verifies the node.

        :return: whether the node is valid.
        """

        self.view.setToolTip("")
        return self.verify_inputs()

    def verify_inputs(self) -> bool:
        """
        Verifies the input ports of the node.

        :return: whether the input ports are valid.
        """

        invalid_inputs: deque[NodePort] = deque()
        for port in self._required_inputs:
            if not port.connected_ports() and not port.value():
                invalid_inputs.append(port)
        if invalid_inputs:
            tool_tip: str = ""
            for invalid_input in invalid_inputs:
                tool_tip += f"Invalid input: {invalid_input.name}\n"
            self.view.setToolTip(f"{self.view.toolTip()} + {tool_tip}")
            return False

        return True

    def exec_queue(self) -> deque[Node]:
        """
        Returns the execution queue of the node.

        :return: execution queue.
        """

        exec_queue = deque([self])

        for exec_output in self.exec_outputs:
            connected_ports = exec_output.connected_ports()
            if not connected_ports:
                continue
            exec_queue.extend(connected_ports[0].node.exec_queue())

        return exec_queue

    def update_affected_outputs(self):
        """
        Updates all affected output ports in a node execution.
        """

        for port in self.inputs:
            port.update_affected()

    def execute(self):
        """
        Executes the node.
        This function should be overridden by subclasses.
        """

        pass

    def execute_children(self):
        """
        Executes all children of the node.
        """

        for child in self.executable_children():
            child._execute()

    def on_input_connected(self, in_port: NodePort, out_port: NodePort):
        """
        Callback function that is triggered when a new connection is made.

        :param in_port: source input port from this node.
        :param out_port: output por that connected to this node.
        """

        pass

    def on_input_disconnected(self, in_port: NodePort, out_port: NodePort):
        """
        Callback function that is triggered when a connection has been disconnected from an input port.

        :param in_port: source input port from this node.
        :param out_port: output port that was disconnected.
        """

        pass

    def _setup_ports(self, reset: bool = True):
        """
        Internal function that creates default ports for this node.

        :param reset: whether to remove already existing ports.
        """

        self._required_inputs.clear()
        self._exec_in_socket = None
        self._exec_out_socket = None
        if reset:
            self.remove_existing_ports()

        if self.__class__.IS_EXEC and self.__class__.AUTO_INIT_EXECS:
            self._exec_in_socket = self.add_input(datatypes.Exec, display_name=False)
            self._exec_out_socket = self.add_output(
                datatypes.Exec, max_connections=1, display_name=False
            )

        self.setup_ports()

    def _execute(self) -> int:
        """
        Executes the node.
        This function should only be called by executor.

        :return: execution result.
        """

        logger.debug(f"Executing {self}...")
        if not self.enabled:
            logger.debug(f'Skipping execution of disabled node "{self}"')
            return 0

        try:
            self.execute()
            self.update_affected_outputs()
        except Exception:
            logger.exception(f"Failed to execute {self.name} {self}")
            self.view.setToolTip(self.view.toolTip() + "Execution error")
            self.is_invalid = True
            raise

        self.is_compiled = True
        self.is_invalid = False

        return 0
