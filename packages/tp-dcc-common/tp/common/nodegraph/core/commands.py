from __future__ import annotations

import typing
from typing import Any

from overrides import override

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import BaseNode
    from tp.common.nodegraph.core.graph import NodeGraph


class NodeAddedCommand(qt.QUndoCommand):
    """
    Node added command.
    """

    def __init__(
            self, graph: NodeGraph, node: BaseNode, pos: tuple[float, float] | None = None, emit_signal: bool = True):
        super().__init__()

        self._graph = graph
        self._node = node
        self._pos = pos
        self._emit_signal = emit_signal

        self.setText('Added Node')

    @override
    def undo(self) -> None:
        self._pos = self._pos or self._node.position()
        self._graph.remove_node(self._node, self._emit_signal)

    @override
    def redo(self) -> None:
        self._graph.add_node(self._node, self._pos, self._emit_signal)


class NodeRemovedCommand(qt.QUndoCommand):
    """
    Node removed command.
    """

    def __init__(self, graph: NodeGraph, nodes: list[BaseNode], emit_signal: bool = True):
        super().__init__()

        self._graph = graph
        self._nodes = nodes
        self._emit_signal = emit_signal

        self.setText('Delete Node' if len(self._nodes) < 2 else 'Delete Nodes')

    @override
    def undo(self) -> None:
        for node in self._nodes:
            self._graph.add_node(node, emit_signal=self._emit_signal)

    @override
    def redo(self) -> None:
        self._graph.remove_nodes(self._nodes, emit_signal=self._emit_signal)


class PropertyChangedCommand(qt.QUndoCommand):
    """
    Node property changed command.
    """

    def __init__(self, node: BaseNode, name: str, value: Any):
        super().__init__()

        self._node = node
        self._name = name
        self._old_value = self._node.property(name)
        self._new_value = value

        if name == 'name':
            self.setText(f'Renamed "{node.name()}" to "{value}"')
        else:
            self.setText(f'Property "{node.name()}:{name}" Value Changed.')

    @override
    def undo(self) -> None:
        if self._old_value == self._new_value:
            return

        self._node.set_property(self._name, self._old_value)

    @override
    def redo(self) -> None:
        if self._old_value == self._new_value:
            return

        self._node.set_property(self._name, self._new_value)

