from __future__ import annotations

import typing

from Qt.QtCore import QObject, Signal

from . import exceptions, datatypes
from .consts import PortType
from .commands import (
    PortConnectedCommand,
    NodeInputConnectedCommand,
    PortDisconnectedCommand,
    NodeInputDisconnectedCommand,
    PortVisibleCommand,
    PortLockedCommand,
    PortUnlockedCommand,
)
from .validators import validate_accept_connection, validate_reject_connection
from ..models.port import PortModel


if typing.TYPE_CHECKING:
    from .node import Node
    from .datatypes import DataType
    from ..views.port import PortView


class NodePort:
    """Class that defines a port in a node which is used for connecting one node to another."""

    class Signals(QObject):
        """Signals class that defines the signals for the node port."""

        valueChanged = Signal()

    def __init__(self, node: Node, view: PortView):
        super().__init__()

        self._model = PortModel(node=node)
        self._view = view
        self._signals = NodePort.Signals()
        self._affected_ports: list[NodePort] = []

    def __repr__(self) -> str:
        """
        Returns a string representation of the object.

        :return: object string representation.
        """

        return f'<{self.__class__.__name__}("{self.name}") object {hex(id(self))}'

    @property
    def model(self) -> PortModel:
        """
        Getter method that returns the port model.

        :return: port model.
        """

        return self._model

    @property
    def view(self) -> PortView:
        """
        Getter method that returns the port view.

        :return: port view.
        """

        return self._view

    @property
    def signals(self) -> NodePort.Signals:
        """
        Getter method that returns the port signals.

        :return: port signals.
        """

        return self._signals

    @property
    def type(self) -> str:
        """
        Getter method that returns the type of the port.

        :return: type of the port.
        """

        return self.model.type

    @property
    def data_type(self) -> DataType:
        """
        Getter method that returns the data type of the port.

        :return: data type of the port.
        """

        return self.model.data_type

    @data_type.setter
    def data_type(self, data_type: DataType):
        """
        Setter method that sets the data type of the port.

        :param data_type: data type to set.
        """

        self.model.data_type = data_type
        self.view.data_type = data_type

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of the port.

        :return: name of the port.
        """

        return self.model.name

    @property
    def node(self) -> Node:
        """
        Getter method that returns the node the port belongs to.

        :return: node the port belongs to.
        """

        return self.model.node

    @property
    def visible(self) -> bool:
        """
        Getter method that returns whether the port is visible.

        :return: whether the port is visible.
        """

        return self.model.visible

    @property
    def locked(self) -> bool:
        """
        Getter method that returns whether the port is locked.

        :return: whether the port is locked.
        """

        return self.model.locked

    @property
    def multi_connection(self) -> bool:
        """
        Getter method that returns whether the port allows multiple connections.

        :return: whether the port allows multiple connections.
        """

        return self.model.multi_connection

    @property
    def color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the color of the port.

        :return: color of the port.
        """

        return self.view.color

    @color.setter
    def color(self, color: tuple[int, int, int, int]):
        """
        Setter method that sets the color of the port.

        :param color: color to set.
        """

        self.view.color = color

    @property
    def border_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the border color of the port.

        :return: border color of the port.
        """

        return self.view.border_color

    @border_color.setter
    def border_color(self, color: tuple[int, int, int, int]):
        """
        Setter method that sets the border color of the port.

        :param color: border color to set.
        """

        self.view.border_color = color

    def value(self) -> typing.Any:
        """
        Returns the value of the port.

        :return: value of the port.
        """

        if self.type == PortType.Input.value:
            if self.connected_ports():
                output_socket = self.connected_ports()[0]
                return output_socket.value()

        return self.model.value

    def set_value(self, value: typing.Any):
        """
        Sets the value of the port.

        :param value: value to set.
        """

        if self.data_type == datatypes.Exec:
            return
        if self._model.value == value:
            return

        self._model.value = value
        self.signals.valueChanged.emit()

    def set_visible(self, flag, push_undo: bool = True):
        """
        Sets the port visibility.

        :param flag: visibility state.
        :param push_undo: whether to push undo command.
        """

        if flag == self.visible:
            return

        command = PortVisibleCommand(self, flag)
        if push_undo:
            self.node.graph.undo_stack.push(command)
        else:
            command.redo()

    def set_locked(
        self, flag: bool, connected_ports: bool = True, push_undo: bool = True
    ):
        """
        Sets the port locked state. When a port is locked, connections cannot be made to it.

        :param flag: lock state.
        :param connected_ports: whether to apply to lock state to connected ports.
        :param push_undo: whether to push undo command.
        """

        # If the port is already locked, we skip it.
        if flag == self.locked:
            return

        undo_stack = self.node.graph.undo_stack
        command = PortLockedCommand(self) if flag else PortUnlockedCommand(self)
        undo_stack.push(command) if push_undo else command.redo()

        if connected_ports:
            for port in self.connected_ports():
                port.set_locked(flag, connected_ports=False, push_undo=push_undo)

    def lock(self):
        """
        Locks the port, so new connections can be connected or disconnected.
        """

        self.set_locked(True, connected_ports=True)

    def unlock(self):
        """
        Unlocks the port, so new connections can be connected or disconnected.
        """

        self.set_locked(False, connected_ports=True)

    def connect_to(
        self,
        port: NodePort | None = None,
        push_undo: bool = True,
        emit_signal: bool = True,
    ):
        """
        Connects the port to another port.

        :param port: port to connect to.
        :param push_undo: whether to push undo command.
        :param emit_signal: whether to emit signal.
        """

        if not port:
            return

        # If port is already connected, we just skip it.
        if self in port.connected_ports():
            return

        # Raise exception is node or port are locked.
        if self.locked or port.locked:
            name = [port.name for port in [self, port] if port.locked][0]
            # noinspection PyTypeChecker
            raise exceptions.NodePortLockedError(name, self.node.type)

        if not validate_accept_connection(self, port):
            return

        if not validate_reject_connection(self, port):
            return

        graph = self.node.graph

        undo_stack = None
        if push_undo:
            undo_stack = graph.undo_stack
            undo_stack.beginMacro("Connect Port")

        if push_undo:
            port_connected_command = PortConnectedCommand(self, port, emit_signal)
            undo_stack.push(port_connected_command)
            node_input_connected_command = NodeInputConnectedCommand(self, port)
            undo_stack.push(node_input_connected_command)
            undo_stack.endMacro()
        else:
            PortConnectedCommand(self, port, emit_signal).redo()
            NodeInputConnectedCommand(self, port).redo()

    def disconnect_from(
        self,
        port: NodePort | None = None,
        push_undo: bool = True,
        emit_signal: bool = True,
    ):
        """
        Disconnects the port from another port.

        :param port: port to disconnect from.
        :param push_undo: whether to push undo command.
        :param emit_signal: whether to emit signal.
        """

        if not port:
            return

        # Raise exception is node or port are locked.
        if self.locked or port.locked:
            name = [port.name for port in [self, port] if port.locked][0]
            # noinspection PyTypeChecker
            raise exceptions.NodePortLockedError(name, self.node.type)

        graph = self.node.graph
        if push_undo:
            graph.undo_stack.beginMacro("Disconnect Port")
            graph.undo_stack.push(PortDisconnectedCommand(self, port, emit_signal))
            graph.undo_stack.push(NodeInputDisconnectedCommand(self, port))
            graph.undo_stack.endMacro()
        else:
            PortDisconnectedCommand(self, port, emit_signal).redo()
            NodeInputDisconnectedCommand(self, port).redo()

    def clear_connections(self, push_undo: bool = True, emit_signal: bool = True):
        """
        Disconnects from all port connections.

        :param push_undo: whether to push undo command.
        :param emit_signal: whether to emit signal.
        """

        if self.locked:
            raise exceptions.NodeLockedError(self.name)

        if not self.connected_ports():
            return

        if push_undo:
            undo_stack = self.node.graph.undo_stack
            undo_stack.beginMacro(f'"{self.name}" Clear Connections')
            for connected_port_view in self.connected_ports():
                self.disconnect_from(connected_port_view, emit_signal=emit_signal)
            undo_stack.endMacro()
            return

        for connected_port_view in self.connected_ports():
            self.disconnect_from(
                connected_port_view, push_undo=False, emit_signal=emit_signal
            )

    def connected_ports(self) -> list[NodePort]:
        """
        Returns a list of ports connected to this port.

        :return: list of connected ports.
        """

        ports: list[NodePort] = []
        graph = self.node.graph
        for node_id, port_names in self.model.connected_ports.items():
            for port_name in port_names:
                node = graph.node_by_id(node_id)
                if self.type == PortType.Input.value:
                    ports.append(node.output_ports()[port_name])
                elif self.type == PortType.Output.value:
                    ports.append(node.input_ports()[port_name])

        return ports

    def accepted_port_types(self) -> dict[str, dict[str, str]]:
        """
        Returns a dictionary of connection constraints of the port types that allow for a connection with this port.

        :return: dictionary of connection constraints.
        """

        return self.node.accepted_port_types(self)

    def add_accept_port_type(self, port_name: str, port_type: str, node_type: str):
        """
        Adds a constraint to "accept" a connection of a specific port type from a specific node type.

        :param port_name: name of the port.
        :param port_type: type of the port.
        :param node_type: type of the node.
        """

        self.node.add_accept_port_type(
            port=self,
            port_type_data={
                "port_name": port_name,
                "port_type": port_type,
                "node_type": node_type,
            },
        )

    def rejected_port_types(self) -> dict[str, dict[str, str]]:
        """
        Returns a dictionary of connection constraints of the port types that do not allow for a connection with this port.

        :return: dictionary of connection constraints.
        """

        return self.node.rejected_port_types(self)

    def add_reject_port_type(self, port_name: str, port_type: str, node_type: str):
        """
        Adds a constraint to "reject" a connection of a specific port type from a specific node type.

        :param port_name: name of the port.
        :param port_type: type of the port.
        :param node_type: type of the node.
        """

        self.node.add_reject_port_type(
            port=self,
            port_type_data={
                "port_name": port_name,
                "port_type": port_type,
                "node_type": node_type,
            },
        )

    def affects(self, port: NodePort):
        """
        Adds given port to the list of affected ports, so that when the value of this port changes,
         the affected ports are updated.
        """

        self._affected_ports.append(port)

    def update_affected(self):
        """
        Updates the affected nodes of the port.
        """

        for port in self._affected_ports:
            port.set_value(self.value())

        # for port in self.connected_ports():
        #     port.value = self.value
