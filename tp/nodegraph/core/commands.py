from __future__ import annotations

import typing
from typing import Any

from Qt.QtWidgets import QUndoCommand, QGraphicsTextItem

from . import consts

if typing.TYPE_CHECKING:
    from .node import BaseNode  # pragma: no cover
    from .port import NodePort  # pragma: no cover
    from .graph import NodeGraph  # pragma: no cover


class AddNodeCommand(QUndoCommand):
    """Command to add a node to the graph."""

    def __init__(
        self,
        graph: NodeGraph,
        node: BaseNode,
        pos: tuple[float, float],
        emit_signal: bool = True,
    ):
        super().__init__()

        self._graph = graph
        self._node = node
        self._xy_pos = pos
        self._emit_signal = emit_signal

        self.setText("Added Node")

    def undo(self):
        """
        Undo the command.
        """

        node_id = self._node.id
        self._xy_pos = self._xy_pos or self._node.xy_pos
        self._graph.remove_node(self._node)

        if self._emit_signal:
            self._graph.nodesDeleted.emit([node_id])

    def redo(self):
        """
        Redo the command.
        """

        self._graph.add_node(self._node, pos=self._xy_pos)

        if self._emit_signal:
            self._graph.nodeCreated.emit(self._node)


class RemoveNodesCommand(QUndoCommand):
    """Command to removes nodes from the graph."""

    def __init__(
        self, graph: NodeGraph, nodes: list[BaseNode], emit_signal: bool = True
    ):
        super().__init__()

        self._graph = graph
        self._nodes = nodes
        self._emit_signal = emit_signal

        self.setText("Removed Node" if len(nodes) == 1 else "Removed Nodes")

    def undo(self):
        """
        Undo the command.
        """

        for node in self._nodes:
            self._graph.add_node(node)
            if self._emit_signal:
                self._graph.nodeCreated.emit(node)

    def redo(self):
        """
        Redo the command.
        """

        node_ids: list[str] = []
        for node in self._nodes:
            node_ids.append(node.id)
            self._graph.remove_node(node)

        if self._emit_signal:
            self._graph.nodesDeleted.emit(node_ids)


class VariableDataTypeChangedCommand(QUndoCommand):
    def __init__(self, graph: NodeGraph, variable: consts.Variable, data_type: str):
        super().__init__()

        self._graph = graph
        self._variable = variable
        self._old_data_type = variable.data_type
        self._new_data_type = data_type

        self.setText(
            f'Changed data type of variable from "{variable.data_type.name}" to "{data_type}".'
        )

    def undo(self):
        """
        Undo the command.
        """

        if self._old_data_type == self._new_data_type:
            return

        self._set_variable_data_type(self._old_data_type)

    def redo(self):
        """
        Redo the command.
        """

        if self._old_data_type == self._new_data_type:
            return

        self._set_variable_data_type(self._new_data_type)

    def _set_variable_data_type(self, data_type_name: str):
        """
        Internal function that sets the data type of the variable.

        :param data_type_name: name of the data type to set.
        """

        data_type = self._graph.factory.data_type_by_name(data_type_name)
        self._variable.value = data_type.default
        self._variable.data_type = data_type

        self._graph.variableDataTypeChanged.emit(self._variable.name)


class PropertyChangedCommand(QUndoCommand):
    def __init__(self, node: BaseNode, name: str, value: Any):
        super().__init__()

        self._node = node
        self._name = name
        self._old_value = node.property(name)
        self._new_value = value

        if name == "name":
            self.setText(f'Renamed "{node.name}" to "{value}".')
        else:
            self.setText(f'Property "{node.name}:{name} changed.')

    def undo(self):
        """
        Undo the command.
        """

        if self._old_value == self._new_value:
            return

        self._set_node_property(self._name, self._old_value)

    def redo(self):
        """
        Redo the command.
        """

        if self._old_value == self._new_value:
            return

        self._set_node_property(self._name, self._new_value)

    def _set_node_property(self, name: str, value: Any):
        """
        Internal function that sets the value of the property with given name.

        :param name: name of the property to change.
        :param value: new property value.
        """

        model = self._node.model
        view = self._node.view
        graph = self._node.graph

        model.set_property(name, value)

        if name in view.properties():
            setattr(view, name, value)

        view = self._node.view
        if hasattr(view, "widgets") and name in view.widgets:
            if view.widgets[name].get_value() != value:
                view.widgets[name].set_value(value)

        graph.propertyChanged.emit(self._node, name, value)


class NodeMovedCommand(QUndoCommand):
    def __init__(self, node: BaseNode, old_pos: tuple[float, float]):
        super().__init__()

        self._node = node
        self._old_pos = old_pos
        self._new_pos = node.xy_pos

        self.setText(f'Moved "{node.name}".')

    def undo(self):
        """
        Undo the command.
        """

        self._node.model.xy_pos = self._old_pos
        self._node.view.xy_pos = self._old_pos

    def redo(self):
        """
        Redo the command.
        """

        if self._new_pos == self._old_pos:
            return

        self._node.model.xy_pos = self._new_pos
        self._node.view.xy_pos = self._new_pos


class NodeVisibleCommand(QUndoCommand):
    """
    Command to set the visibility of a node.
    """

    def __init__(self, node: BaseNode, visible: bool):
        super().__init__()

        self._node = node
        self._visible = visible
        self._selected = node.selected

    def undo(self):
        """
        Undo the command.
        """

        self._set_node_visible(not self._visible)

    def redo(self):
        """
        Redo the command.
        """

        self._set_node_visible(self._visible)

    def _set_node_visible(self, flag: bool):
        """
        Internal function that sets the visibility of the node.

        :param flag: visibility flag.
        """

        self._node.model.set_property("visible", flag)
        self._node.view.visible = flag

        # Redraw connectors.
        for port_view in self._node.view.inputs + self._node.view.outputs:
            for connector_view in port_view.connected_connectors:
                connector_view.update()

        # Restore the selected state.
        if self._selected != self._node.view.isSelected():
            self._node.view.setSelected(self._node.model.selected)

        self._node.graph.propertyChanged.emit(self._node, "visible", flag)


class NodeWidgetVisibleCommand(QUndoCommand):
    """
    Command to set the visibility of a node widget.
    """

    def __init__(self, node: BaseNode, name: str, visible: bool):
        super().__init__()

        self._view = node.view
        self._node_widget = self._view.widget(name)
        self._visible = visible

        self.setText(
            f'Show node widget "{name}"' if visible else f'Hide node widget "{name}"'
        )

    def undo(self):
        """
        Undo the command.
        """

        self._node_widget.setVisible(not self._visible)
        self._view.draw()

    def redo(self):
        """
        Redo the command.
        """

        self._node_widget.setVisible(self._visible)
        self._view.draw()


class NodeInputConnectedCommand(QUndoCommand):
    """
    Command to connect an input port to an output port.
    """

    def __init__(self, source_port: NodePort, target_port: NodePort):
        super().__init__()

        if source_port.type == consts.PortType.Input.value:
            self._source_port = source_port
            self._target_port = target_port
        else:
            self._source_port = target_port
            self._target_port = source_port

    def undo(self):
        """
        Undo the command.
        """

        node = self._source_port.node
        node.on_input_disconnected(self._source_port, self._target_port)

    def redo(self):
        """
        Redo the command.
        """

        node = self._source_port.node
        node.on_input_connected(self._source_port, self._target_port)


class NodeInputDisconnectedCommand(QUndoCommand):
    """
    Command to disconnect an input port from an output port.
    """

    def __init__(self, source_port: NodePort, target_port: NodePort):
        super().__init__()

        if source_port.type == consts.PortType.Input.value:
            self._source_port = source_port
            self._target_port = target_port
        else:
            self._source_port = target_port
            self._target_port = source_port

    def undo(self):
        """
        Undo the command.
        """

        node = self._source_port.node
        node.on_input_connected(self._source_port, self._target_port)

    def redo(self):
        """
        Redo the command.
        """

        node = self._source_port.node
        node.on_input_disconnected(self._source_port, self._target_port)


class PortConnectedCommand(QUndoCommand):
    """
    Command to connect two ports.
    """

    def __init__(self, source_port: NodePort, target_port: NodePort, emit_signal: bool):
        super().__init__()

        self._source_port = source_port
        self._target_port = target_port
        self._emit_signal = emit_signal

    def undo(self):
        """
        Undo the command.
        """

        source_model = self._source_port.model
        target_model = self._target_port.model
        source_id = self._source_port.node.id
        target_id = self._target_port.node.id

        port_names = source_model.connected_ports.get(target_id)
        # noinspection PySimplifyBooleanCheck
        if port_names == []:
            del source_model.connected_ports[target_id]
        if port_names and self._target_port.name in port_names:
            port_names.remove(self._target_port.name)

        port_names = target_model.connected_ports.get(source_id)
        # noinspection PySimplifyBooleanCheck
        if port_names == []:
            del target_model.connected_ports[source_id]
        if port_names and self._source_port.name in port_names:
            port_names.remove(self._source_port.name)

        self._source_port.view.disconnect_from(self._target_port.view)

        if self._emit_signal:
            ports = {p.type: p for p in [self._source_port, self._target_port]}
            graph = self._source_port.node.graph
            graph.portDisconnected.emit(
                ports[consts.PortType.Input.value], ports[consts.PortType.Output.value]
            )

    def redo(self):
        """
        Redo the command.
        """

        source_model = self._source_port.model
        target_model = self._target_port.model
        source_id = self._source_port.node.id
        target_id = self._target_port.node.id

        source_model.connected_ports[target_id].append(self._target_port.name)
        target_model.connected_ports[source_id].append(self._source_port.name)

        self._source_port.view.connect_to(self._target_port.view)

        if self._emit_signal:
            ports = {p.type: p for p in [self._source_port, self._target_port]}
            graph = self._source_port.node.graph
            graph.portConnected.emit(
                ports[consts.PortType.Input.value], ports[consts.PortType.Output.value]
            )


class PortDisconnectedCommand(QUndoCommand):
    """
    Command to disconnect two ports.
    """

    def __init__(self, source_port: NodePort, target_port: NodePort, emit_signal: bool):
        super().__init__()

        self._source_port = source_port
        self._target_port = target_port
        self._emit_signal = emit_signal

    def undo(self):
        """
        Undo the command.
        """

        source_model = self._source_port.model
        target_model = self._target_port.model
        source_id = self._source_port.node.id
        target_id = self._target_port.node.id

        source_model.connected_ports[target_id].append(self._target_port.name)
        target_model.connected_ports[source_id].append(self._source_port.name)

        self._source_port.view.connect_to(self._target_port.view)

        if self._emit_signal:
            ports = {p.type: p for p in [self._source_port, self._target_port]}
            graph = self._source_port.node.graph
            graph.portConnected.emit(
                ports[consts.PortType.Input.value], ports[consts.PortType.Output.value]
            )

    def redo(self):
        """
        Redo the command.
        """

        source_model = self._source_port.model
        target_model = self._target_port.model
        source_id = self._source_port.node.id
        target_id = self._target_port.node.id

        port_names = source_model.connected_ports.get(target_id)
        # noinspection PySimplifyBooleanCheck
        if port_names == []:
            del source_model.connected_ports[target_id]
        if port_names and self._target_port.name in port_names:
            port_names.remove(self._target_port.name)

        port_names = target_model.connected_ports.get(source_id)
        # noinspection PySimplifyBooleanCheck
        if port_names == []:
            del target_model.connected_ports[source_id]
        if port_names and self._source_port.name in port_names:
            port_names.remove(self._source_port.name)

        self._source_port.view.disconnect_from(self._target_port.view)

        if self._emit_signal:
            ports = {p.type: p for p in [self._source_port, self._target_port]}
            graph = self._source_port.node.graph
            graph.portDisconnected.emit(
                ports[consts.PortType.Input.value], ports[consts.PortType.Output.value]
            )


class PortLockedCommand(QUndoCommand):
    """
    Command to lock or unlock a port.
    """

    def __init__(self, port: NodePort):
        super().__init__()

        self._port = port

        self.setText(f'Lock Port "{port.name}"')

    def undo(self):
        """
        Undo the command.
        """

        self._port.model.locked = False
        self._port.view.locked = False

    def redo(self):
        """
        Redo the command.
        """

        self._port.model.locked = True
        self._port.view.locked = True


class PortUnlockedCommand(QUndoCommand):
    """
    Command to unlock or unlock a port.
    """

    def __init__(self, port: NodePort):
        super().__init__()

        self._port = port

        self.setText(f'Unlock Port "{port.name}"')

    def undo(self):
        """
        Undo the command.
        """

        self._port.model.locked = True
        self._port.view.locked = True

    def redo(self):
        """
        Redo the command.
        """

        self._port.model.locked = False
        self._port.view.locked = False


class PortVisibleCommand(QUndoCommand):
    """
    Port visibility command.
    """

    def __init__(self, port: NodePort, visible: bool):
        super().__init__()

        self._port = port
        self._visible = visible
        if visible:
            self.setText(f'Show Port "{port.name}"')
        else:
            self.setText(f'Hide Port "{port.name}"')

    def undo(self):
        """
        Undo the command.
        """

        self._set_visible(not self._visible)

    def redo(self):
        """
        Redo the command.
        """

        self._set_visible(self._visible)

    def _set_visible(self, flag: bool):
        """
        Internal function that sets the visibility of the port.

        :param flag: visibility flag.
        """

        self._port.model.visible = flag
        self._port.view.setVisible(flag)
        node_view = self._port.node.view
        text_item: QGraphicsTextItem | None = None
        if self._port.type == consts.PortType.Input.value:
            text_item = node_view.input_text_item(self._port.view)
        elif self._port.type == consts.PortType.Output.value:
            text_item = node_view.output_text_item(self._port.view)
        if text_item:
            text_item.setVisible(flag)

        node_view.draw()

        # Redraw connectors in the scene
        for port_view in node_view.inputs + node_view.outputs:
            for connector_view in port_view.connected_connectors:
                connector_view.update()


class AddVariableCommand(QUndoCommand):
    """Command to add a variable to the graph"""

    def __init__(
        self, graph: NodeGraph, variable: consts.Variable, emit_signal: bool = True
    ):
        super().__init__()

        self._graph = graph
        self._variable = variable
        self._emit_signal = emit_signal

        self.setText("Added Variable")

    def undo(self):
        """
        Undo the command.
        """

        variable_name = self._variable.name
        self._graph.remove_variable(self._variable)

        if self._emit_signal:
            self._graph.variablesDeleted.emit([variable_name])

    def redo(self):
        """
        Redo the command.
        """

        self._graph.add_variable(self._variable)

        if self._emit_signal:
            self._graph.variableCreated.emit(self._variable)


class RenameVariableCommand(QUndoCommand):
    """Command to rename a variable in the graph."""

    def __init__(
        self,
        graph: NodeGraph,
        variable: consts.Variable,
        new_name: str,
        emit_signal: bool = True,
    ):
        super().__init__()

        self._graph = graph
        self._variable = variable
        self._new_name = new_name
        self._old_name = variable.name
        self._emit_signal = emit_signal

        self.setText(f'Renamed Variable "{self._old_name}" to "{self._new_name}"')

    def undo(self):
        """
        Undo the command.
        """

        self._variable.name = self._old_name

        for node in self._graph.getter_nodes(self._new_name) + self._graph.setter_nodes(
            self._new_name
        ):
            node.set_variable_name(self._old_name)

        if self._emit_signal:
            self._graph.variableRenamed.emit(self._variable)

    def redo(self):
        """
        Redo the command.
        """

        self._new_name = self._graph.unique_variable_name(self._new_name)
        self._variable.name = self._new_name

        for node in self._graph.getter_nodes(self._old_name) + self._graph.setter_nodes(
            self._old_name
        ):
            node.set_variable_name(self._new_name)

        if self._emit_signal:
            self._graph.variableRenamed.emit(self._variable)


class RemoveVariablesCommand(QUndoCommand):
    """Command to remove variables from the graph."""

    def __init__(
        self,
        graph: NodeGraph,
        variables: list[consts.Variable],
        emit_signal: bool = True,
    ):
        super().__init__()

        self._graph = graph
        self._variables = variables
        self._emit_signal = emit_signal

        self.setText("Removed Variable" if len(variables) == 1 else "Removed Variables")

    def undo(self):
        """
        Undo the command.
        """

        for variable in self._variables:
            self._graph.add_variable(variable)
            if self._emit_signal:
                self._graph.variableCreated.emit(variable)

    def redo(self):
        """
        Redo the command.
        """

        variable_names: list[str] = []
        for variable in self._variables:
            variable_names.append(variable.name)
            self._graph.remove_variable(variable)

        if self._emit_signal:
            self._graph.variablesDeleted.emit(variable_names)
