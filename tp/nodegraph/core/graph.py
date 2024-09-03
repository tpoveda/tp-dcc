from __future__ import annotations

import os
import re
import sys
import json
import typing
import logging
import pathlib
import importlib.util
from typing import Type, Iterable, Any

from Qt.QtCore import QObject, Signal
from Qt.QtWidgets import QApplication, QUndoStack, QUndoView, QTabBar

from . import exceptions
from .factory import NodeFactory
from .executor import NodeGraphExecutor
from .menu import NodeGraphMenu, NodesMenu
from .commands import (
    AddNodeCommand,
    NodeMovedCommand,
    RemoveNodesCommand,
    PortConnectedCommand,
    AddVariableCommand,
    RenameVariableCommand,
    RemoveVariablesCommand,
    VariableDataTypeChangedCommand,
)
from . import consts, datatypes
from ..views import uiconsts
from ..core.port import NodePort
from ..core.node import BaseNode, Node
from ..nodes.node_group import GroupNode
from ..models.graph import NodeGraphModel
from ..views.graph import NodeGraphView
from ..widgets.graph import NodeGraphWidget
from ..core.settings import NodeGraphSettings
from ..nodes.node_backdrop import BackdropNode
from ..nodes.node_function import FunctionNode
from ..nodes.node_getset import GetNode, SetNode
from ...python import jsonio

if typing.TYPE_CHECKING:
    from .subgraph import SubGraph
    from .events import DropNodeEvent, DropVariableEvent
    from ..views.port import PortView
    from ..views.scene import NodeGraphScene
    from ..views.node import AbstractNodeView

logger = logging.getLogger(__name__)


class NodeGraph(QObject):
    """Class that defines the node graph."""

    nodeCreated = Signal(BaseNode)
    nodeSelected = Signal(BaseNode)
    nodeSelectionChanged = Signal(list, list)
    nodeDoubleClicked = Signal(BaseNode)
    nodesDeleted = Signal(object)
    variableCreated = Signal(consts.Variable)
    variableRenamed = Signal(consts.Variable)
    variableValueChanged = Signal(str)
    variableDataTypeChanged = Signal(str)
    variablesDeleted = Signal(object)
    propertyChanged = Signal(BaseNode, str, object)
    portConnected = Signal(NodePort, NodePort)
    portDisconnected = Signal(NodePort, NodePort)
    sessionChanged = Signal(str)
    contextMenuPrompted = Signal(object, object)

    def __init__(
        self,
        model: NodeGraphModel | None = None,
        factory: NodeFactory | None = None,
        settings: NodeGraphSettings | None = None,
        undo_stack: QUndoStack | None = None,
        executor: NodeGraphExecutor | None = None,
        viewer: NodeGraphView | None = None,
        layout_direction: int | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent=parent)

        self._file_name: str = ""
        self._is_executing: bool = False
        self._widget: NodeGraphWidget | None = None
        self._factory = factory or NodeFactory()
        self._settings = settings or NodeGraphSettings()
        self._model = model or NodeGraphModel()
        self._undo_stack = undo_stack or QUndoStack(parent=self)
        self._undo_view: QUndoView | None = None
        self._executor = executor or NodeGraphExecutor(self)
        self._viewer = viewer or NodeGraphView(undo_stack=self._undo_stack)
        if layout_direction is not None:
            layout_direction = (
                layout_direction
                if layout_direction in consts.LayoutDirection
                else consts.LayoutDirection.Horizontal.value
            )
            self._model.layout_direction = layout_direction
        else:
            layout_direction = self._model.layout_direction
        self._viewer.layout_direction = layout_direction
        self._context_menus: dict[str, NodeGraphMenu] = {}
        self._sub_graphs: dict[str, SubGraph] = {}

        self._register_context_menus()
        self._setup_signals()

        self.setObjectName("NodeGraph")

    def __repr__(self) -> str:
        """
        Returns a string representation of the node graph.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("root") object at {hex(id(self))}'

    @property
    def factory(self) -> NodeFactory:
        """
        Getter method that returns the node factory.

        :return: node factory.
        """

        return self._factory

    @property
    def settings(self) -> NodeGraphSettings:
        """
        Getter method that returns the node graph settings.

        :return: node graph settings.
        """

        return self._settings

    @property
    def is_executing(self) -> bool:
        """
        Getter method that returns whether the graph is executing or not.

        :return: whether the graph is executing or not.
        """

        return self._is_executing

    @is_executing.setter
    def is_executing(self, value: bool):
        """
        Setter method that sets whether the graph is executing or not.

        :param value: whether the graph is executing or not.
        """

        self._is_executing = value

    @property
    def model(self) -> NodeGraphModel:
        """
        Getter method that returns the node graph model.

        :return: node graph model.
        """

        return self._model

    @property
    def layout_direction(self) -> int:
        """
        Getter method that returns the layout direction of the graph.

        :return: layout direction.
        """

        return self._model.layout_direction

    @layout_direction.setter
    def layout_direction(self, value: int):
        """
        Setter method that sets the layout direction of the graph.

        :param value: layout direction.
        """

        direction_types = [e.value for e in consts.LayoutDirection]
        value = (
            value
            if value in direction_types
            else consts.LayoutDirection.Horizontal.value
        )
        self._model.layout_direction = value
        for node in self.nodes():
            node.layout_direction = value
        self._viewer.layout_direction = value

    @property
    def connector_style(self) -> int:
        """
        Getter method that returns the connector style of the graph.

        :return: connector style.
        """

        return self._model.connector_style

    @connector_style.setter
    def connector_style(self, value: int):
        """
        Setter method that sets the connector style of the graph.

        :param value: connector style.
        """

        connector_styles = max([e.value for e in consts.ConnectorStyle])
        style = (
            value
            if 0 <= value <= connector_styles
            else consts.ConnectorStyle.Curved.value
        )
        self._model.connector_style = style
        self._viewer.connector_style = style

    @property
    def grid_mode(self) -> int:
        """
        Getter method that returns the grid mode of the graph.

        :return: grid mode.
        """

        scene: NodeGraphScene = self.scene
        return scene.grid_mode

    @grid_mode.setter
    def grid_mode(self, value: int):
        """
        Setter method that sets the grid mode of the graph.

        :param value: grid mode.
        """

        display_types = [
            uiconsts.NODE_GRAPH_GRID_DISPLAY_NONE,
            uiconsts.NODE_GRAPH_GRID_DISPLAY_DOTS,
            uiconsts.NODE_GRAPH_GRID_DISPLAY_LINES,
        ]
        value = (
            value if value in display_types else uiconsts.NODE_GRAPH_GRID_DISPLAY_LINES
        )
        scene: NodeGraphScene = self.scene
        scene.grid_mode = value
        self.viewer.force_update()

    @property
    def background_color(self) -> tuple[int, int, int]:
        """
        Getter method that returns the background color of the graph.

        :return: background color.
        """

        scene: NodeGraphScene = self.scene
        return scene.background_color

    @background_color.setter
    def background_color(self, value: tuple[int, int, int]):
        """
        Setter method that sets the background color of the graph.

        :param value: color to set.
        """

        scene: NodeGraphScene = self.scene
        scene.background_color = value
        self.viewer.force_update()

    @property
    def grid_color(self) -> tuple[int, int, int]:
        """
        Getter method that returns the grid color of the graph.

        :return: grid color.
        """

        scene: NodeGraphScene = self.scene
        return scene.grid_color

    @grid_color.setter
    def grid_color(self, value: tuple[int, int, int]):
        """
        Setter method that sets the grid color of the graph.

        :param value: color to set.
        """

        scene: NodeGraphScene = self.scene
        scene.grid_color = value
        self.viewer.force_update()

    @property
    def acyclic(self) -> bool:
        """
        Getter method that returns whether the graph is acyclic or not.

        :return: whether the graph is acyclic or not.
        """

        return self._model.acyclic

    @acyclic.setter
    def acyclic(self, value: bool):
        """
        Setter method that sets whether the graph is acyclic or not.

        :param value: whether the graph is acyclic or not.
        """

        self._model.acyclic = value
        self._viewer.acyclic = self._model.acyclic

    @property
    def connector_collision(self) -> bool:
        """
        Getter method that returns whether collision is enabled.

        :return: whether dragging a node over a connector will allow the node to be inserted as a new connection
            between the connector.
        """

        return self._model.connector_collision

    @connector_collision.setter
    def connector_collision(self, value: bool):
        """
        Setter method that sets whether collision is enabled.

        :param value: whether dragging a node over a connector will allow the node to be inserted as a new connection
            between the connector.
        """

        self._model.connector_collision = value
        self._viewer.connector_collision = self._model.connector_collision

    @property
    def connector_slicing(self) -> bool:
        """
        Getter method that returns whether slicing is enabled.

        :return: whether holding down ``Alt + Shift + LMB drag`` will allow node connectors to be sliced.
        """

        return self._model.connector_slicing

    @connector_slicing.setter
    def connector_slicing(self, value: bool):
        """
        Setter method that sets whether slicing is enabled.

        :param value: whether holding down ``Alt + Shift + LMB drag`` will allow node connectors to be sliced.
        """

        self._model.connector_slicing = value
        self._viewer.connector_slicing = self._model.connector_slicing

    @property
    def viewer(self) -> NodeGraphView:
        """
        Getter method that returns the node graph view.

        :return: node graph view.
        """

        return self._viewer

    @property
    def scene(self) -> NodeGraphScene:
        """
        Getter method that returns the scene of the graph view.

        :return: scene.
        """

        # noinspection PyTypeChecker
        return self._viewer.scene()

    @property
    def undo_stack(self) -> QUndoStack:
        """
        Getter method that returns the undo stack.

        :return: undo stack.
        """

        return self._undo_stack

    @property
    def executor(self) -> NodeGraphExecutor:
        """
        Getter method that returns the node graph executor.

        :return: node graph executor.
        """

        return self._executor

    @property
    def session(self) -> str:
        """
        Getter method that returns the currently loaded session of the graph.

        :return: session file path.
        """

        return self._model.session

    @property
    def undo_view(self) -> QUndoView:
        """
        Getter method that returns the undo view.

        :return: undo view.
        """

        if self._undo_view is None:
            self._undo_view = QUndoView(self._undo_stack)
            self._undo_view.setWindowTitle("Undo History")

        return self._undo_view

    @property
    def is_root(self) -> bool:
        """
        Getter method that returns whether the graph is the root graph or not.

        :return: whether the graph is the root graph or not.
        """

        return True

    @property
    def sub_graphs(self) -> dict[str, SubGraph]:
        """
        Getter method that returns the sub graphs of the graph.

        :return: sub graphs.
        """

        return self._sub_graphs

    def add_node(self, node: BaseNode, pos: tuple[float, float] | None = None):
        """
        Adds a node to the graph.

        :param node: node to add.
        :param pos: position to add the node at.
        """

        node.graph = self
        self.model.nodes[node.model.id] = node
        self.viewer.add_node(node.view, pos=pos)

        # We make sure to update model width and height, which are re-calculated once a node is added into the scene.
        node.model.width = node.view.width
        node.model.height = node.view.height

    def remove_node(self, node: BaseNode):
        """
        Removes a node from the graph.

        :param node: node to remove.
        """

        self.model.nodes.pop(node.id)
        node.view.delete()

    def delete_node(
        self,
        node: BaseNode | GroupNode,
        push_undo: bool = True,
        emit_signal: bool = True,
    ):
        """
        Deletes a node from the graph.

        :param node: node to delete.
        :param push_undo: whether to push the command to the undo stack.
        :param emit_signal: whether to emit the signal or not.
        """

        if push_undo:
            self._undo_stack.beginMacro(f'Delete Node: "{node.name}"')

        # Collapse group node before removing.
        if isinstance(node, GroupNode) and node.is_expanded:
            node.collapse()

        if isinstance(node, Node):
            for input_port in node.inputs:
                if input_port.locked:
                    input_port.set_locked(
                        False, connected_ports=False, push_undo=push_undo
                    )
                input_port.clear_connections(push_undo=push_undo)
            for output_port in node.outputs:
                if output_port.locked:
                    output_port.set_locked(
                        False, connected_ports=False, push_undo=push_undo
                    )
                output_port.clear_connections(push_undo=push_undo)

        command = RemoveNodesCommand(self, [node], emit_signal=emit_signal)
        if push_undo:
            self._undo_stack.push(command)
            self._undo_stack.endMacro()
        else:
            command.redo()

    def delete_nodes(self, nodes: list[BaseNode] | None = None, push_undo: bool = True):
        """
        Deletes a list of nodes from the graph.

        :param nodes: nodes to delete.
        :param push_undo: whether to push the command to the undo stack.
        """

        nodes = nodes or self.selected_nodes()
        if not nodes:
            return

        if len(nodes) == 1:
            self.delete_node(nodes[0], push_undo=push_undo)
            return

        node_ids = [node.id for node in nodes]
        if push_undo:
            self._undo_stack.beginMacro(f'Delete "{len(nodes)}" Node(s)')
        for node in nodes:
            # Collapse group node before removing.
            if isinstance(node, GroupNode) and node.is_expanded:
                node.collapse()
            if isinstance(node, Node):
                for input_port in node.inputs:
                    if input_port.locked:
                        input_port.set_locked(
                            False, connected_ports=False, push_undo=push_undo
                        )
                    input_port.clear_connections(push_undo=push_undo)
                for output_port in node.outputs:
                    if output_port.locked:
                        output_port.set_locked(
                            False, connected_ports=False, push_undo=push_undo
                        )
                    output_port.clear_connections(push_undo=push_undo)

        command = RemoveNodesCommand(self, nodes, emit_signal=True)
        if push_undo:
            self._undo_stack.push(command)
            self._undo_stack.endMacro()
        else:
            command.redo()

        self.nodesDeleted.emit(node_ids)

    def extract_nodes(
        self,
        nodes: list[BaseNode] | None = None,
        push_undo: bool = True,
        prompt_warning: bool = True,
    ):
        """
        Extracts the given nodes from its connections.

        :param nodes: nodes to extract.
        :param push_undo: whether to push the command to the undo stack.
        :param prompt_warning: whether to prompt a warning dialog before extracting the nodes.
        """

        nodes = nodes or self.selected_nodes()
        if not nodes:
            return

        locked_ports: list[str] = []
        base_nodes: list[Node] = []
        for node in nodes:
            if not isinstance(node, Node):
                continue
            for port in node.inputs + node.outputs:
                if port.locked:
                    locked_ports.append(f"{port.node.name}: {port.name}")
            base_nodes.append(node)

        if locked_ports:
            message = (
                "Selected nodes cannot be extracted because the following "
                "ports are locked:\n{}".format("\n".join(sorted(locked_ports)))
            )
            if prompt_warning:
                self._viewer.message_dialog(message, "Can't Extract Nodes")
            return

        if push_undo:
            self._undo_stack.beginMacro(f'Extracted "{len(nodes)}" Node(s)')

        for node in base_nodes:
            for port in node.inputs + node.outputs:
                for connected_port in port.connected_ports():
                    if connected_port.node in base_nodes:
                        continue
                    port.disconnect_from(connected_port, push_undo=push_undo)

        if push_undo:
            self._undo_stack.endMacro()

    def create_node(
        self,
        node_id: str,
        name: str | None = None,
        selected: bool = True,
        color: tuple[int, int, int, int] | str | None = None,
        text_color: tuple[int, int, int, int] | str | None = None,
        position: tuple[int | float, int | float] | None = None,
        func_signature: str | None = None,
        func_name: str | None = None,
        push_undo: bool = True,
    ) -> BaseNode:
        """
        Creates a new node.

        :param node_id: ID of the node to create.
        :param name: node name.
        :param selected: whether the node is selected or not.
        :param color: node color.
        :param text_color: node text color.
        :param position: initial X, Y node position. Defaults to (0.0, 0.0).
        :param func_signature: function signature.
        :param func_name: function name.
        :param push_undo: whether to push the command to the undo stack.
        :return: created node.
        :raises NodeCreationError: If the node could not be created.
        """

        def _format_color(_clr: str | tuple[int, int, int, int]):
            """
            Internal function that formats a given color input into an RGB tuple.

            If the input is a hexadecimal color code string (e.g., '#FF5733'), it converts
            it into an RGB tuple (255, 87, 51). If the input is already an RGB tuple or
            another format, it returns the input unchanged.

            :param _clr: color input to format. Can bea hexadecimal color code string or an RGB tuple.
            :return: A tuple representing the RGB values of the color if the input was a  hexadecimal string, or the
                original input if it was already a tuple.
            """

            if isinstance(_clr, str):
                _clr = _clr.strip("#")
                return tuple(int(_clr[i : i + 2], 16) for i in (0, 2, 4))
            return _clr

        try:
            node = self._factory.create_node(node_id)
        except exceptions.NodeNotFoundError:
            raise exceptions.NodeCreationError(node_id)
        if not node:
            raise exceptions.NodeCreationError(node_id)

        widget_types = node.model.__dict__.pop("_temp_property_widget_types")
        property_attributes = node.model.__dict__.pop("_temp_property_attributes")
        # noinspection PyTypeChecker
        if self.model.node_common_properties(node.type) is None:
            node_attrs = {
                node.type: {n: {"widget_type": wt} for n, wt in widget_types.items()}
            }
            for property_name, property_attrs in property_attributes.items():
                node_attrs[node.type][property_name].update(property_attrs)
            self.model.set_node_common_properties(node_attrs)

        accept_types = node.model.__dict__.pop("_temp_accept_connection_types")
        reject_types = node.model.__dict__.pop("_temp_reject_connection_types")
        for port_type, port_data in accept_types.get(node.type, {}).items():
            for port_name, accept_data in port_data.items():
                for accept_node_type, accept_node_data in accept_data.items():
                    for accept_port_type, accept_port_names in accept_node_data.items():
                        for accept_port_name in accept_port_names:
                            # noinspection PyTypeChecker
                            self.model.add_port_accept_connection_type(
                                port_name=port_name,
                                port_type=port_type,
                                node_type=node.type,
                                accept_port_name=accept_port_name,
                                accept_port_type=accept_port_type,
                                accept_node_type=accept_node_type,
                            )
        for port_type, port_data in reject_types.get(node.type, {}).items():
            for port_name, reject_data in port_data.items():
                for reject_node_type, reject_node_data in reject_data.items():
                    for reject_port_type, reject_port_names in reject_node_data.items():
                        for reject_port_name in reject_port_names:
                            # noinspection PyTypeChecker
                            self.model.add_port_reject_connection_type(
                                port_name=port_name,
                                port_type=port_type,
                                node_type=node.type,
                                reject_port_name=reject_port_name,
                                reject_port_type=reject_port_type,
                                reject_node_type=reject_node_type,
                            )

        node.graph = self
        node.NODE_NAME = self.unique_node_name(name or node.name)
        node.model.name = node.NODE_NAME
        node.model.selected = selected
        node.model.layout_direction = self.layout_direction
        if color is not None:
            node.model.color = _format_color(color)
        if text_color is not None:
            node.model.text_color = _format_color(text_color)
        if position is not None:
            node.model.xy_pos = [float(position[0]), float(position[1])]

        if isinstance(node, FunctionNode):
            node.function_signature = func_signature
            if func_name:
                node.set_property("name", func_name, push_undo=False)

        node.update_view()

        # noinspection PyTypeChecker
        command = AddNodeCommand(self, node, pos=node.model.xy_pos, emit_signal=True)
        if push_undo:
            self._undo_stack.beginMacro(f'Create Node: "{node.NODE_NAME}"')
            for selected_node in self.selected_nodes():
                selected_node.set_property("selected", False, push_undo=True)
            self._undo_stack.push(command)
            self._undo_stack.endMacro()
        else:
            for selected_node in self.selected_nodes():
                selected_node.set_property("selected", False, push_undo=False)
            command.redo()

        return node

    def node_by_id(self, node_id: str) -> BaseNode | Node | GroupNode | None:
        """
        Returns the node by its ID.

        :param node_id: ID of the node to get.
        :return: node.
        """

        return self.model.nodes.get(node_id, None)

    def node_by_name(self, name: str) -> BaseNode | Node | None:
        """
        Returns the node by its name.

        :param name: name of the node to get.
        :return: node.
        """

        found_node: BaseNode | None = None
        for node in self.nodes():
            if node.name == name:
                found_node = node
                break

        return found_node

    def nodes_by_type(self, node_type: str) -> list[BaseNode | Node]:
        """
        Returns all nodes of a given type.

        :param node_type: type of nodes to get.
        :return: list of nodes.
        """

        return [node for node in self.nodes() if node.type == node_type]

    def register_node(self, node_class: Type[BaseNode], alias: str | None = None):
        """
        Register a node in the registry.

        :param node_class: node to register.
        :param alias: optional alias of the node to register
        """

        self._factory.register_node(node_class, alias=alias)

    def register_nodes(self, node_classes: list[Type[BaseNode]]):
        """
        Register a list of nodes in the registry.

        :param node_classes: list of nodes to register.
        """

        [self._factory.register_node(node_class) for node_class in node_classes]

    def nodes(self) -> list[BaseNode | Node]:
        """
        Returns all nodes in the graph.

        :return: list of nodes.
        """

        return list(self.model.nodes.values())

    def selected_nodes(self) -> list[BaseNode | Node]:
        """
        Returns all selected nodes in the graph.

        :return: list of selected nodes.
        """

        nodes: list[BaseNode | Node] = []
        for node_view in self._viewer.selected_nodes():
            node = self._model.nodes[node_view.id]
            nodes.append(node)

        return nodes

    def unique_node_name(self, name: str) -> str:
        """
        Returns a unique node name to avoid having nodes with the same name.

        :param name: node name.
        :return: unique node name.
        """

        name = " ".join(name.split())
        node_names = [n.name for n in self.nodes()]
        if name not in node_names:
            return name

        unique_name: str = ""

        # Regular expression to match a sequence of word characters followed by a space and a sequence of digits at
        # the end of the string ('Node 1', ...).
        regex = re.compile(r"\w+ (\d+)$")
        search = regex.search(name)
        if not search:
            for i in range(1, len(node_names) + 2):
                new_name = f"{name} {i}"
                if new_name not in node_names:
                    unique_name = new_name
                    break
        if unique_name:
            return unique_name

        # If a numeric suffix is found, it is extracted using search.group(1). The name is then truncated to remove
        # this suffix and any trailing spaces.
        version = search.group(1)
        name = name[: len(version) * -1].strip()
        for i in range(1, len(node_names) + 2):
            new_name = f"{name} {i}"
            if new_name not in node_names:
                unique_name = new_name
                break

        return unique_name

    def select_all_nodes(self):
        """
        Selects all nodes in the graph.
        """

        self._undo_stack.beginMacro("Select All Nodes")
        for node in self.nodes():
            node.selected = True
        self._undo_stack.endMacro()

    def invert_selected_nodes(self):
        """
        Inverts the selection of all nodes in the graph.
        """

        if not self.selected_nodes():
            self.select_all_nodes()
            return

        self._undo_stack.beginMacro("Invert Selection")
        for node in self.nodes():
            node.selected = not node.selected
        self._undo_stack.endMacro()

    def clear_selected_nodes(self):
        """
        Clears the selection of all nodes in the graph.
        """

        self._undo_stack.beginMacro("Clear Selection")
        for node in self.nodes():
            node.selected = False
        self._undo_stack.endMacro()

    def fit_to_selected_nodes(self):
        """
        Sets the zoom level to fit selected nodes.
        If no nodes are selected, then all nodes in the graph will be framed.
        """

        nodes = self.selected_nodes() or self.nodes()
        if not nodes:
            return

        self.viewer.zoom_to_nodes([n.view for n in nodes])

    def center_on(self, nodes: list[BaseNode] | None = None):
        """
        Centers the view on the given nodes.

        :param nodes: nodes to center on.
        """

        nodes = nodes or []
        self.viewer.center_selection([n.view for n in nodes])

    def center_on_selected_nodes(self):
        """
        Centers the view on the selected nodes.
        """

        nodes = self.viewer.selected_nodes()
        self.viewer.center_selection(nodes)

    def reset_zoom(self):
        """
        Resets the zoom level.
        """

        self.viewer.reset_zoom()

    def set_zoom(self, value: float = 0.0):
        """
        Sets the zoom level.

        :param value: zoom level.
        """

        self.viewer.set_zoom_value(value)

    def get_zoom(self) -> float:
        """
        Returns the current zoom level.

        :return: zoom level.
        """

        return self.viewer.zoom_value()

    def toggle_node_search(self):
        """
        Toggles the node search widget.
        """

        if not self._viewer.underMouse():
            return

        self._viewer.tab_search_set_nodes(self)
        self._viewer.tab_search_toggle()

    def serialize_session(self) -> dict:
        """
        Serializes the current node graph session to a dictionary.

        :return: serialized session of the current node layout.
        """

        return self._serialize(self.nodes(), self.variables())

    def deserialize_session(
        self,
        session_data: dict,
        clear_session: bool = True,
        clear_undo_stack: bool = True,
    ):
        """
        Deserializes a node graph session from a dictionary.

        :param session_data: dictionary containing a node graph session.
        :param clear_session: whether to clear current session.
        :param clear_undo_stack: whether to clear the undo stack.
        """

        if clear_session:
            self.clear_session()

        self._deserialize(session_data)
        self.clear_selected_nodes()

        if clear_undo_stack:
            self.clear_undo_stack()

    def save_session(self, file_path: str) -> bool:
        """
        Saves the current node graph session to a JSON file.

        :param file_path: path to save the session to.
        :return: whether the session was saved successfully or not.
        """

        serialized_data = self.serialize_session()
        file_path = file_path.strip()

        def _convert_sets_to_lists(obj: Any) -> Any:
            if isinstance(obj, set):
                return list(obj)
            return obj

        with open(file_path, "w") as f:
            if not jsonio.validate_json(serialized_data):
                logger.error(
                    f"Invalid JSON data:\n{serialized_data}\nCannot write data to file:\n{file_path}"
                )
                return False
            try:
                json.dump(
                    serialized_data,
                    f,
                    indent=2,
                    separators=(",", ":"),
                    default=_convert_sets_to_lists,
                )
            except Exception:
                logger.exception(
                    f"Cannot write data to file:\n{file_path}", exc_info=True
                )
                logger.info(serialized_data)
                return False

        self._model.session = file_path

        return True

    def clear_session(self):
        """
        Clears the current node graph session.
        """

        nodes = self.nodes()
        for node in nodes:
            if not isinstance(node, Node):
                continue
            for input_port in node.inputs:
                if input_port.locked:
                    input_port.set_locked(False, connected_ports=False)
                input_port.clear_connections()
            for output_port in node.outputs:
                if output_port.locked:
                    output_port.set_locked(False, connected_ports=False)
                output_port.clear_connections()
        self._undo_stack.push(RemoveNodesCommand(self, nodes))
        self._undo_stack.clear()
        self._model.session = ""

    def import_session(self, file_path: str, clear_undo_stack: bool = True) -> bool:
        """
        Imports a node graph session from a JSON file.

        :param file_path: path to import session from.
        :param clear_undo_stack: whether to clear undo stack after importing the session.
        :return: whether the session was imported successfully or not.
        """

        try:
            with open(file_path) as data_file:
                layout_data = json.load(data_file)
        except json.JSONDecodeError:
            layout_data = None
            logger.exception(f"Cannot read data from file:\n{file_path}", exc_info=True)
        if not layout_data:
            return False

        self.deserialize_session(
            layout_data, clear_session=False, clear_undo_stack=clear_undo_stack
        )
        self.model.session = file_path

        self.sessionChanged.emit(file_path)

        return True

    def load_session(self, file_path: str) -> bool:
        """
        Loads a node graph session from a JSON file.

        :param file_path: path to load the session from.
        :return: whether the session was loaded successfully or not.
        """

        file_path = file_path.strip()
        if not os.path.isfile(file_path):
            raise IOError(f"File not found: {file_path}")

        self.clear_session()
        return self.import_session(file_path, clear_undo_stack=True)

    def copy_nodes(self, nodes: list[BaseNode] | None = None) -> bool:
        """
        Copies the given nodes to the clipboard.

        :param nodes: nodes to copy.
        :return: whether the nodes were copied successfully or not.
        """

        nodes = nodes or self.selected_nodes()
        if not nodes:
            return False

        clipboard = QApplication.clipboard()
        serialized_data = self._serialize(nodes, [])
        serialized_str = json.dumps(serialized_data)
        if not serialized_str:
            return False
        clipboard.setText(serialized_str)

        return True

    def cut_nodes(self, nodes: list[BaseNode] | None = None) -> bool:
        """
        Cuts the given nodes to the clipboard.

        :param nodes: nodes to cut.
        :return: whether the nodes were cut successfully or not.
        """

        nodes = nodes or self.selected_nodes()
        if not nodes:
            return False

        self.copy_nodes(nodes)
        self._undo_stack.beginMacro("Cut Nodes")
        for node in nodes:
            if isinstance(node, Node):
                for input_port in node.inputs:
                    if input_port.locked:
                        input_port.set_locked(
                            False, connected_ports=False, push_undo=True
                        )
                    input_port.clear_connections()
                for output_port in node.outputs:
                    if output_port.locked:
                        output_port.set_locked(
                            False, connected_ports=False, push_undo=True
                        )
                    output_port.clear_connections()
            # Collapse group nodes before removing.
            if isinstance(node, GroupNode) and node.is_expanded:
                node.collapse()
        self._undo_stack.push(RemoveNodesCommand(self, nodes))
        self._undo_stack.endMacro()

        return True

    def paste_nodes(self) -> list[BaseNode | Node]:
        """
        Pastes the nodes from the clipboard.

        :return: list of pasted nodes.
        """

        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        if not clipboard_text:
            return []

        try:
            serialized_data = json.loads(clipboard_text)
        except json.JSONDecodeError:
            logger.exception("Cannot read data from clipboard", exc_info=True)
            return []

        self._undo_stack.beginMacro("Paste Nodes")
        self.clear_selected_nodes()
        nodes = self._deserialize(serialized_data, relative_pos=True)
        for node in nodes:
            node.selected = True
        self._undo_stack.endMacro()

        return nodes

    def duplicate_nodes(self, nodes: list[BaseNode] | None = None) -> list[BaseNode]:
        """
        Duplicates the given nodes.

        :param nodes: nodes to duplicate.
        :return: list of duplicated nodes.
        """

        nodes = nodes or self.selected_nodes()
        if not nodes:
            return []

        self._undo_stack.beginMacro("Duplicate Nodes")
        self.clear_selected_nodes()
        serialized_data = self._serialize(nodes, [])
        duplicated_nodes = self._deserialize(serialized_data)
        offset: int = 50
        for node in duplicated_nodes:
            x, y = node.xy_pos
            node.xy_pos = (x + offset, y + offset)
            node.set_property("selected", True)
        self._undo_stack.endMacro()

        return duplicated_nodes

    def disable_nodes(
        self, nodes: list[BaseNode] | None = None, mode: bool | None = None
    ):
        """
        Disables the given nodes.

        :param nodes: nodes to disable.
        :param mode: whether to enable or disable the nodes.
        """

        nodes = nodes or self.selected_nodes()
        if not nodes:
            return

        if len(nodes) == 1:
            mode = mode if mode is not None else not nodes[0].disabled
            nodes[0].disabled = mode
            return

        if mode is not None:
            states = {False: "enable", True: "disable"}
            text = "{} ({}) Nodes".format(states[mode], len(nodes))
            self._undo_stack.beginMacro(text)
            for node in nodes:
                node.disabled = mode
            self._undo_stack.endMacro()
            return

        texts: list[str] = []
        enabled_count = len([n for n in nodes if n.disabled])
        disabled_count = len([n for n in nodes if not n.disabled])
        if enabled_count > 0:
            texts.append(f"Enabled ({enabled_count})")
        if disabled_count > 0:
            texts.append(f"Disabled ({disabled_count})")
        text = " / ".join(texts) + " Nodes"

        self._undo_stack.beginMacro(text)
        for node in nodes:
            node.disabled = not node.disabled

        self._undo_stack.endMacro()

    def variables(self) -> list[consts.Variable]:
        """
        Returns all variables in the graph.

        :return: list of variables.
        """

        return self.model.variables

    def unique_variable_name(self, name: str) -> str:
        """
        Returns a unique variable name to avoid having variables with the same name.

        :param name: variable name.
        :return: unique variable name.
        """

        variable_names: list[str] = [v.name for v in self.model.variables]
        if name not in variable_names:
            return name

        index: int = 1
        while f"{name}{index}" in variable_names:
            index += 1
            name = f"{name}{index}"

        return name

    def getter_nodes(self, name: str) -> list[GetNode]:
        """
        Returns all getter nodes in the graph for the given variable.

        :param name: variable name.
        :return: list of getter nodes.
        """

        # noinspection PyUnresolvedReferences,PyTypeChecker
        return [
            node
            for node in self.nodes()
            if isinstance(node, GetNode) and node.variable_name == name
        ]

    def setter_nodes(self, name: str) -> list[SetNode]:
        """
        Returns all setter nodes in the graph for the given variable.

        :param name: variable name.
        :return: list of setter nodes.
        """

        # noinspection PyUnresolvedReferences,PyTypeChecker
        return [
            node
            for node in self.nodes()
            if isinstance(node, SetNode) and node.variable_name == name
        ]

    def create_variable(
        self,
        name: str,
        value: Any = None,
        data_type: consts.DataType | None = None,
        push_undo: bool = True,
    ) -> consts.Variable:
        """
        Creates a new variable.

        :param name: variable name.
        :param value: variable value.
        :param data_type: variable data type.
        :param push_undo: whether to push the command to the undo stack.
        :return created variable.
        """

        name = self.unique_variable_name(name)
        data_type = data_type if data_type is not None else datatypes.Numeric
        value = value if value is not None else data_type.default
        variable = consts.Variable(
            name=name, value=value, data_type=data_type, graph=self
        )

        command = AddVariableCommand(self, variable, emit_signal=True)
        if push_undo:
            self._undo_stack.beginMacro(f'Create Variable: "{variable.name}"')
            self._undo_stack.push(command)
            self._undo_stack.endMacro()
        else:
            command.redo()

        return variable

    def add_variable(self, variable: consts.Variable):
        """
        Adds a variable to the graph.

        :param variable: variable to add.
        """

        self.model.variables.append(variable)

    def variable(self, name: str) -> consts.Variable | None:
        """
        Returns a variable by its name.

        :param name: variable name.
        :return: variable.
        """

        found_variable: consts.Variable | None = None
        for variable in self.model.variables:
            if variable.name == name:
                found_variable = variable
                break

        return found_variable

    def variable_data_type(
        self, name: str, as_data_type: bool = False
    ) -> str | datatypes.DataType:
        """
        Returns the data type of the variable by its name.

        :param name: variable name.
        :param as_data_type: whether to return the data type as a DataType object.
        :return: variable data type.
        """

        variable = self.variable(name)
        return variable.data_type if as_data_type else variable.data_type.name

    def set_variable_data_type(
        self, name: str, data_type_name: str, push_undo: bool = True
    ):
        """
        Sets the data type of the variable by its name.

        :param name: variable name.
        :param data_type_name: data type name.
        :param push_undo: whether to push the command to the undo stack.
        """

        variable = self.variable(name)
        if not variable:
            logger.error(f"Cannot set data type for non existing variable: {name}")
            return

        command = VariableDataTypeChangedCommand(self, variable, data_type_name)
        if push_undo:
            self._undo_stack.push(command)
        else:
            command.redo()

    def variable_value(self, name: str) -> Any:
        """
        Returns the value of the variable by its name.

        :param name: variable name.
        :return: variable value.
        """

        return self.variable(name).value

    def set_variable_value(self, name: str, value: Any):
        """
        Sets the value of the variable by its name.

        :param name: variable name.
        :param value: variable value.
        """

        variable = self.variable(name)
        variable.value = value
        self.variableValueChanged.emit(name)

    def rename_variable(self, old_name: str, new_name: str, push_undo: bool = True):
        """
        Renames a variable in the graph.

        :param old_name: old variable to rename.
        :param new_name: new variable name.
        :param push_undo: whether to push the command to the undo stack.
        """

        variable = self.variable(old_name)
        if not variable:
            logger.error(f"Cannot rename non existing variable: {old_name}")
            return

        command = RenameVariableCommand(self, variable, new_name)
        if push_undo:
            self._undo_stack.push(command)
        else:
            command.redo()

    def remove_variable(self, variable: consts.Variable):
        """
        Removes a variable from the graph.

        :param variable: variable to remove.
        """

        if variable not in self.model.variables:
            logger.error(f"Cannot delete non existing variable: {variable.name}")
            return

        self.model.variables.pop(self.model.variables.index(variable))

    def delete_variable(
        self,
        variable: consts.Variable,
        push_undo: bool = True,
        emit_signal: bool = True,
    ):
        """
        Deletes a variable from the graph.

        :param variable: variable to delete.
        :param push_undo:  whether to push the command to the undo stack.
        :param emit_signal: whether to emit the variableDeleted signal.
        """

        if push_undo:
            self._undo_stack.beginMacro(f'Delete Variable: "{variable.name}"')

        for node in self.getter_nodes(variable.name) + self.setter_nodes(variable.name):
            node.is_invalid = True

        command = RemoveVariablesCommand(self, [variable], emit_signal=emit_signal)
        if push_undo:
            self._undo_stack.push(command)
            self._undo_stack.endMacro()
        else:
            command.redo()

    def widget(self) -> NodeGraphWidget:
        """
        Returns the node graph widget.

        :return: node graph widget.
        """

        if self._widget is not None:
            return self._widget

        self._widget = NodeGraphWidget()
        self._widget.addTab(self._viewer, "Node Graph")
        tab_bar = self._widget.tabBar()
        tab_flags = [QTabBar.RightSide, QTabBar.LeftSide]
        for flag in tab_flags:
            tab_button = tab_bar.tabButton(0, flag)
            if tab_button:
                tab_button.deleteLater()
                # noinspection PyTypeChecker
                tab_bar.setTabButton(0, flag, None)
        self._widget.tabCloseRequested.connect(self._on_close_sub_graph_tab)

        return self._widget

    def message_dialog(
        self,
        text: str,
        title: str = "Node Graph",
        dialog_icon: str | None = None,
        custom_icon: str | None = None,
        parent: QObject | None = None,
    ):
        """
        Prompts a node graph view message dialog widget with "Ok" button.

        :param text: dialog text.
        :param title: dialog title.
        :param dialog_icon: optional display icon ("information", "warning", "critical").
        :param custom_icon: optional custom icon to display.
        :param parent: optional dialog parent widget.
        """

        return self.viewer.message_dialog(
            text=text,
            title=title,
            dialog_icon=dialog_icon,
            custom_icon=custom_icon,
            parent=parent,
        )

    def question_dialog(
        self,
        text: str,
        title: str = "Node Graph",
        dialog_icon: str | None = None,
        custom_icon: str | None = None,
        parent: QObject | None = None,
    ) -> bool:
        """
        Prompts a node graph view question dialog widget with "Yes" and "No" buttons.

        :param text: dialog text.
        :param title: dialog title.
        :param dialog_icon: optional display icon ("information", "warning", "critical").
        :param custom_icon: optional custom icon to display.
        :param parent: optional dialog parent widget.
        :return: True if "Yes" button is clicked, False otherwise.
        """

        return self.viewer.question_dialog(
            text=text,
            title=title,
            dialog_icon=dialog_icon,
            custom_icon=custom_icon,
            parent=parent,
        )

    def load_dialog(
        self,
        start_directory: str | None = None,
        extension: str | None = None,
        parent: QObject | None = None,
    ) -> str | None:
        """
        Prompts a node graph view load dialog widget.

        :param start_directory: optional starting directory path.
        :param extension: optional extension to filter types by.
        :param parent: optional dialog parent widget.
        :return: selected file path.
        """

        return self.viewer.load_dialog(
            start_directory=start_directory, extension=extension, parent=parent
        )

    def save_dialog(
        self,
        start_directory: str | None = None,
        extension: str | None = None,
        parent: QObject | None = None,
    ) -> str | None:
        """
        Prompts a node graph view save dialog widget.

        :param start_directory: optional starting directory path.
        :param extension: optional extension to filter types by.
        :param parent: optional dialog parent widget.
        :return: selected file path.
        """

        return self.viewer.save_dialog(
            start_directory=start_directory, extension=extension, parent=parent
        )

    def show(self):
        """
        Shows the node graph widget.
        """
        self.widget().show()

    def close(self):
        """
        Closes the node graph widget.
        """

        self.widget().close()

    def clear_undo_stack(self):
        """
        Clears the undo stack.
        """

        self._undo_stack.clear()

    def begin_undo(self, name: str):
        """
        Begins an undo macro.

        :param name: name of the undo macro.
        """

        self._undo_stack.beginMacro(name)

    def end_undo(self):
        """
        Ends an undo macro.
        """

        self._undo_stack.endMacro()

    def context_menu(self) -> NodeGraphMenu | None:
        """
        Returns the context menu.

        :return: context menu.
        """

        return self.context_menu_by_name("graph")

    def nodes_context_menu(self) -> NodesMenu | None:
        """
        Returns the nodes context menu.

        :return: nodes context menu.
        """

        return self.context_menu_by_name("nodes")

    def context_menu_by_name(self, name: str) -> NodeGraphMenu | NodesMenu | None:
        """
        Returns the context menu with the given name.

        :param name: name of the context menu to get.
        :return: context menu.
        """

        return self._context_menus.get(name, None)

    def set_context_menu_from_file(self, file_path: str, menu_name: str = "graph"):
        """
        Populates a context menu from a serialized JSON file.

        :param file_path: file path pointing to a valid JSON file containing menu data.
        :param menu_name: name of the parent context menu to populate under.
        """

        menu_name = menu_name or "graph"
        file = pathlib.Path(file_path).resolve()
        if not file.is_file():
            raise IOError(f"File not found: {file_path}")
        with file.open() as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON file: {file_path}")
        context_menu = self.context_menu_by_name(menu_name)
        self._deserialize_context_menu(context_menu, data, file)

    def disable_context_menu(self, flag: bool = True, name: str = "all"):
        """
        Disables/Enables context menus from the node graph.
        Following context menu names are available:
            - "all": all context menu from the node graph.
            - "graph": context menu from the node graph.
            - "nodes": context menu for the nodes.

        :param flag: whether to disable/enable the context menu.
        :param name: menu name.
        """

        if name == "all":
            for context_menu in self.viewer.context_menus.values():
                context_menu.setDisabled(flag)
                context_menu.setVisible(not flag)
            return
        context_menu = self.viewer.context_menus.get(name)
        if not context_menu:
            return
        context_menu.setDisabled(flag)
        context_menu.setVisible(not flag)

    def expand_group_node(self, group_node: GroupNode):
        """
        Expands a group node.

        :param group_node: group node to expand.
        """

        raise NotImplementedError

    def collapse_group_node(self, group_node: GroupNode):
        """
        Collapses a group node.

        :param group_node: group node to collapse.
        """

        raise NotImplementedError

    def _register_context_menus(self):
        """
        Internal function that registers the context menus.
        """

        if not self._viewer:
            return

        menus = self._viewer.context_menus
        if menus.get("graph"):
            self._context_menus["graph"] = NodeGraphMenu(self, menus["graph"])
        if menus.get("nodes"):
            self._context_menus["nodes"] = NodesMenu(self, menus["nodes"])

    def _setup_signals(self):
        """
        Internal function that sets up signals.
        """

        self.variableDataTypeChanged.connect(self._on_variable_data_type_changed)
        self._viewer.nodeSelected.connect(self._on_node_selected)
        self._viewer.nodeSelectionChanged.connect(self._on_node_selection_changed)
        self._viewer.nodeDoubleClicked.connect(self._on_node_double_clicked)
        self._viewer.nodesMoved.connect(self._on_nodes_moved)
        self._viewer.nodeNameChanged.connect(self._on_node_name_changed)
        self._viewer.connectionSliced.connect(self._on_connections_sliced)
        self._viewer.connectionsChanged.connect(self._on_connections_changed)
        self._viewer.nodeDropped.connect(self._on_node_dropped)
        self._viewer.variableDropped.connect(self._on_variable_dropped)
        self._viewer.nodeBackdropUpdated.connect(self._on_node_backdrop_updated)
        self._viewer.contextMenuPrompted.connect(self._on_context_menu_prompted)
        self._viewer.searchTriggered.connect(self._on_search_triggered)

    def _serialize(
        self, nodes: list[BaseNode], variables: list[consts.Variable]
    ) -> dict:
        """
        Internal function that serializes node graph to a dictionary.

        :param nodes: list of nodes instances to serialize.
        :param variables: list of variables instances to serialize.
        :return: serialized node graph.
        """

        serialized_data = {"graph": {}, "nodes": {}, "connections": [], "variables": {}}
        nodes_data: dict[str, dict] = {}
        variables_data: list[dict] = []

        serialized_data["graph"]["layout_direction"] = self.layout_direction
        serialized_data["graph"]["connector_style"] = self.connector_style
        serialized_data["graph"]["acyclic"] = self.acyclic
        serialized_data["graph"]["connector_collision"] = self.connector_collision
        serialized_data["graph"]["connector_slicing"] = self.connector_slicing
        serialized_data["graph"]["accept_connection_types"] = (
            self.model.accept_connection_types
        )
        serialized_data["graph"]["reject_connection_types"] = (
            self.model.reject_connection_types
        )

        for node in nodes:
            node.update_model()
            serialized_node = node.serialize()
            nodes_data.update(serialized_node)

        for node_id, node_data in nodes_data.items():
            serialized_data["nodes"][node_id] = node_data
            inputs = node_data.pop("inputs") if node_data.get("inputs") else {}
            outputs = node_data.pop("outputs") if node_data.get("outputs") else {}
            for port_name, connection_data in inputs.items():
                for connection_id, port_names in connection_data.items():
                    for connected_port in port_names:
                        connector = {
                            consts.PortType.Input.value: [node_id, port_name],
                            consts.PortType.Output.value: [
                                connection_id,
                                connected_port,
                            ],
                        }
                        if connector not in serialized_data["connections"]:
                            serialized_data["connections"].append(connector)
            for port_name, connection_data in outputs.items():
                for connection_id, port_names in connection_data.items():
                    for connected_port in port_names:
                        connector = {
                            consts.PortType.Input.value: [
                                connection_id,
                                connected_port,
                            ],
                            consts.PortType.Output.value: [node_id, port_name],
                        }
                        if connector not in serialized_data["connections"]:
                            serialized_data["connections"].append(connector)

        for variable in variables:
            variable_data = variable.to_dict()
            variables_data.append(variable_data)

        for variable_data in variables_data:
            variable_name = variable_data.pop("name")
            serialized_data["variables"][variable_name] = variable_data

        if not serialized_data["connections"]:
            serialized_data.pop("connections")

        return serialized_data

    def _deserialize(
        self,
        session_data: dict,
        relative_pos: bool = False,
        position: Iterable[int, int] | None = None,
    ) -> list[BaseNode]:
        """
        Internal function that deserializes node graph from a dictionary.

        :param session_data: node graph session data.
        :param relative_pos: position node relative to the cursor.
        :param position: custom X, Y position.
        :return: list of deserialized node instances.
        """

        # Update node graph properties
        for attr_name, attr_value in session_data.get("graph", {}).items():
            if attr_name == "layout_direction":
                self.layout_direction = attr_value
            if attr_name == "acyclic":
                self.acyclic = attr_value
            elif attr_name == "connector_collision":
                self.connector_collision = attr_value
            elif attr_name == "connector_slicing":
                self.connector_slicing = attr_value
            elif attr_name == "connector_style":
                self.connector_style = attr_value
            elif attr_name == "accept_connection_types":
                self.model.accept_connection_types = attr_value
            elif attr_name == "reject_connection_types":
                self.model.reject_connection_types = attr_value

        # Deserialize variables (before nodes).
        for variable_name, variable_data in session_data.get("variables", {}).items():
            data_type_name = variable_data.get("data_type", "")
            data_type = (
                self.factory.data_type_by_name(data_type_name)
                if data_type_name
                else None
            )
            self.create_variable(
                variable_name,
                value=variable_data.get("value", None),
                data_type=data_type,
            )

        # Deserialize nodes.
        nodes: dict[str, BaseNode | Node] = {}
        for node_id, node_data in session_data.get("nodes", {}).items():
            # Create node
            identifier = node_data["type"]
            name = node_data.get("name")
            node = self.create_node(
                identifier, name=name, position=node_data.get("xy_pos")
            )
            if not node:
                continue
            node.deserialize(node_data)
            nodes[node_id] = node

        # Deserialize connections.
        for connection in session_data.get("connections", []):
            node_id, port_name = connection.get("in", ("", ""))
            in_node: Node = nodes.get(node_id) or self.node_by_id(node_id)
            if not in_node:
                continue
            in_port = in_node.input_ports().get(port_name) if in_node else None
            node_id, port_name = connection.get("out", ("", ""))
            out_node = nodes.get(node_id) or self.node_by_id(node_id)
            if not out_node:
                continue
            out_port = out_node.output_ports().get(port_name) if out_node else None
            if in_port and out_port:
                allow_connection = any(
                    [not in_port.model.connected_ports, in_port.model.multi_connection]
                )
                if allow_connection:
                    self._undo_stack.push(
                        PortConnectedCommand(in_port, out_port, emit_signal=False)
                    )
                in_node.on_input_connected(in_port, out_port)

        created_nodes: list[BaseNode | Node] = list(nodes.values())

        if relative_pos:
            self._viewer.move_nodes([n.view for n in created_nodes])
            [setattr(n.model, "xy_pos", n.view.xy_pos) for n in created_nodes]
        elif position:
            self._viewer.move_nodes([n.view for n in created_nodes], position=position)
            [setattr(n.model, "xy_pos", n.view.xy_pos) for n in created_nodes]

        return created_nodes

    def _deserialize_context_menu(
        self,
        menu: NodeGraphMenu | NodesMenu,
        menu_data: list[dict] | dict,
        anchor_path: str | pathlib.Path | None = None,
    ):
        """
        Internal function that populates context menu from a dictionary.

        :param menu: parent context menu.
        :param menu_data: serialized menu data.
        :param anchor_path: optional directory to interpret file paths relative to.
        :return:
        """

        def _build_menu_command(_menu: NodeGraphMenu | NodesMenu, _data: dict):
            """
            Internal function that recursively creates a new menu command from serialized data.

            :param _menu: menu to add command into.
            :param _data: serialized command data.
            """

            _func_path = pathlib.Path(_data["file"])
            if not _func_path.is_absolute():
                _func_path = anchor.joinpath(_func_path)
            _base_name = _func_path.parent.name
            _file_name = _func_path.stem
            _module_name = f"{_base_name}.{_file_name}"
            _spec = importlib.util.spec_from_file_location(_module_name, _func_path)
            _module = importlib.util.module_from_spec(_spec)
            sys.modules[_module_name] = _module
            try:
                _spec.loader.exec_module(_module)
            except FileNotFoundError:
                logger.warning(f"File not found: {_module}")
                return
            try:
                _command_function = getattr(_module, _data["function_name"])
            except AttributeError:
                logger.warning(
                    f"Function not found: {_data['function_name']} within module {_module}"
                )
                return
            _command_name = _data.get("label") or "<command>"
            _command_shortcut = _data.get("shortcut")
            _command_kwargs = {"func": _command_function, "shortcut": _command_shortcut}
            if _menu == nodes_menu and _data.get("node_type"):
                _command_kwargs["node_type"] = _data["node_type"]
            _menu.add_command(name=_command_name, **_command_kwargs)

        if not menu:
            raise ValueError("Menu not found")

        nodes_menu = self.context_menu_by_name("nodes")
        anchor = pathlib.Path(anchor_path).resolve()
        if anchor.is_file():
            anchor = anchor.parent

        if isinstance(menu_data, dict):
            item_type = menu_data.get("type")
            if item_type == "separator":
                menu.add_separator()
            elif item_type == "command":
                _build_menu_command(menu, menu_data)
            elif item_type == "menu":
                sub_menu = menu.add_menu(menu_data["label"])
                items = menu_data.get("items", [])
                self._deserialize_context_menu(sub_menu, items, anchor_path)
        elif isinstance(menu_data, list):
            for item_data in menu_data:
                self._deserialize_context_menu(menu, item_data, anchor_path)

    def _on_variable_data_type_changed(self, variable_name: str):
        """
        Internal callback function that is called each time a variable data type is changed.

        :param variable_name: name of the variable whose data type was changed.
        """

        # noinspection PyBroadException
        try:
            for getter_node in self.getter_nodes(variable_name):
                getter_node.update()
        except Exception:
            logger.exception("Failed to update getters", exc_info=True)

        # noinspection PyBroadException
        try:
            for setter_node in self.setter_nodes(variable_name):
                setter_node.update()
        except Exception:
            logger.exception("Failed to update setters", exc_info=True)

    def _on_node_selected(self, node_id: str):
        """
        Internal callback function that is called each time a node is selected.

        :param node_id: ID of the selected node.
        """

        node = self.node_by_id(node_id)
        self.nodeSelected.emit(node)

    def _on_node_selection_changed(
        self, selected_ids: list[str], deselected_ids: list[str]
    ):
        """
        Internal callback function that is called each time the node selection is changed.

        :param selected_ids: IDs of the selected nodes.
        :param deselected_ids: IDs of the deselected nodes.
        """

        selected_nodes = [self.node_by_id(node_id) for node_id in selected_ids]
        deselected_nodes = [self.node_by_id(node_id) for node_id in deselected_ids]
        self.nodeSelectionChanged.emit(selected_nodes, deselected_nodes)

    def _on_node_double_clicked(self, node_id: str):
        """
        Internal callback function that is called each time a node is double-clicked.

        :param node_id: ID of the double-clicked node.
        """

        node = self.node_by_id(node_id)
        self.nodeDoubleClicked.emit(node)

    def _on_nodes_moved(self, moved_nodes: dict[AbstractNodeView, tuple[float, float]]):
        """
        Internal callback function that is called each time nodes are moved within graph view.

        :param moved_nodes: dictionary that contains moved nodes and their new positions.
        """

        self._undo_stack.beginMacro("Nodes Moved")
        for node_view, prev_pos in moved_nodes.items():
            node = self._model.nodes[node_view.id]
            command = NodeMovedCommand(node, prev_pos)
            self._undo_stack.push(command)
        self._undo_stack.endMacro()

    def _on_node_name_changed(self, node_id: str, name: str):
        """
        Internal callback function that is called each time a node name is changed.

        :param node_id: ID of the node.
        :param name: new name of the node.
        """

        node = self.node_by_id(node_id)
        node.name = name
        node.view.draw()

    def _on_connections_sliced(self, port_views: list[tuple[PortView, PortView]]):
        """
        Internal callback function that is called each time a connection is sliced.

        :param port_views: list of port views.
        """

        if not port_views:
            return

        port_types = {
            consts.PortType.Input.value: "input_ports",
            consts.PortType.Output.value: "output_ports",
        }
        self._undo_stack.beginMacro("Slice Connection(s)")
        for port1_view, port2_view in port_views:
            node1 = self._model.nodes[port1_view.node_view.id]
            node2 = self._model.nodes[port2_view.node_view.id]
            port1 = getattr(node1, port_types[port1_view.port_type])()[port1_view.name]
            port2 = getattr(node2, port_types[port2_view.port_type])()[port2_view.name]
            port1.disconnect_from(port2)
        self._undo_stack.endMacro()

    def _on_connections_changed(
        self,
        disconnected: list[tuple[PortView, PortView]],
        connected: list[tuple[PortView, PortView]],
    ):
        """
        Internal callback function that is called each time connections are changed.

        :param disconnected: tuple of disconnected port views.
        :param connected: tuple of connected port views.
        """

        if not disconnected and not connected:
            return

        port_types = {
            consts.PortType.Input.value: "input_ports",
            consts.PortType.Output.value: "output_ports",
        }

        self._undo_stack.beginMacro(
            "Connect Node(s)" if connected else "Disconnect Node(s)"
        )
        for port1_view, port2_view in disconnected:
            node1: BaseNode = self._model.nodes[port1_view.node_view.id]
            node2: BaseNode = self._model.nodes[port2_view.node_view.id]
            port1 = getattr(node1, port_types[port1_view.port_type])()[port1_view.name]
            port2 = getattr(node2, port_types[port2_view.port_type])()[port2_view.name]
            port1.disconnect_from(port2)
        for port1_view, port2_view in connected:
            node1: BaseNode = self._model.nodes[port1_view.node_view.id]
            node2: BaseNode = self._model.nodes[port2_view.node_view.id]
            port1 = getattr(node1, port_types[port1_view.port_type])()[port1_view.name]
            port2 = getattr(node2, port_types[port2_view.port_type])()[port2_view.name]
            port1.connect_to(port2)
        self._undo_stack.endMacro()

    def _on_node_dropped(self, event: DropNodeEvent):
        """
        Internal callback function that is called each time a node is dropped within graph view.

        :param event: drop node event.
        """

        func_signature = event.json_data.get("func_signature", None)
        func_name = event.json_data.get("title", None)
        self.create_node(
            event.node_id,
            position=event.position,
            func_signature=func_signature,
            func_name=func_name,
        )

    def _on_variable_dropped(self, event: DropVariableEvent):
        """
        Internal callback function that is called each time a variable is dropped within graph view.

        :param event: drop variable event.
        """

        node_id = (
            "tp.nodegraph.nodes.SetNode"
            if event.setter
            else "tp.nodegraph.nodes.GetNode"
        )
        # noinspection PyTypeChecker
        node: GetNode | SetNode = self.create_node(node_id, position=event.position)
        node.set_variable_name(event.variable_name, init_ports=True)

    def _on_node_backdrop_updated(
        self, node_id: str, updated_property: str, updated_geometry: dict[str, Any]
    ):
        """
        Internal callback function that is called each time a node backdrop is updated.

        :param node_id: ID of the backdrop node.
        :param updated_property: backdrop property changed.
        :param updated_geometry: updated geometry of the backdrop node.
        """

        backdrop_node = self.node_by_id(node_id)
        if not backdrop_node or not isinstance(backdrop_node, BackdropNode):
            return

        backdrop_node.on_backdrop_updated(updated_property, updated_geometry)

    def _on_context_menu_prompted(self, menu_name: str, node_id: str):
        """
        Internal callback function that is called each time a context menu is prompted.

        :param menu_name: name of the context menu.
        :param node_id: ID of the node.
        """

        node = self.node_by_id(node_id)
        menu = self.context_menu_by_name(menu_name)
        self.contextMenuPrompted.emit(menu, node)

    def _on_search_triggered(
        self,
        node_type: str,
        func_signature: str,
        function_name: str,
        pos: tuple[int, int],
    ):
        """
        Internal callback function that is called each time a search is triggered.

        :param node_type: type of the node to create.
        :param func_signature: function signature to create the node with.
        :param function_name: name of the function.
        :param pos: position to create the node at.
        """

        self.create_node(
            node_type,
            position=pos,
            func_signature=func_signature,
            func_name=function_name,
        )

    def _on_close_sub_graph_tab(self, index: int):
        """
        Internal callback function that is called each time a sub-graph tab is closed.

        :param index: index of the tab.
        """

        node_id = self.widget().tabToolTip(index)
        group_node = self.node_by_id(node_id)
        self.collapse_group_node(group_node)
