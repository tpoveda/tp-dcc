from __future__ import annotations

import contextlib

from Qt.QtCore import QObject
from Qt.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QStackedLayout
from maya import cmds

from . import utils
from ..cmds.ui import nodeeditor


@contextlib.contextmanager
def disable_node_editor_add_node_context():
    """
    Context manager that disables the current node editors "Add to graph or create",
    which slows down Maya node a lot.
    """

    node_editor: NodeEditorWrapper | None = None
    node_editor_name = nodeeditor.primary_node_editor()
    state: bool = False
    if node_editor_name:
        node_editor = NodeEditorWrapper(node_editor_name)
        if node_editor.add_nodes_on_create():
            node_editor.set_add_nodes_on_create(False)

    yield

    if state and node_editor:
        node_editor.set_add_nodes_on_create(state)


class NodeEditorWrapper(QObject):
    """
    Class that wraps a Maya node editor and provides Qt-related functions to interact
    with it.
    """

    def __init__(self, node_editor: str | None = None):
        super().__init__()

        self._editor: QWidget | None = None
        self._view: QGraphicsView | None = None
        self._scene: QGraphicsScene | None = None

        if not node_editor:
            self._editor_name = nodeeditor.primary_node_editor()
            self.setObjectName(self._editor_name)
            if self._editor:
                self._editor, self._view, self._scene = NodeEditorWrapper.as_qt_widgets(
                    self._editor_name
                )
        else:
            self.setObjectName(node_editor)
            self._editor_name = node_editor
            self._editor, self._view, self._scene = NodeEditorWrapper.as_qt_widgets(
                node_editor
            )

    @staticmethod
    def as_qt_widgets(
        node_editor: str,
    ) -> tuple[QWidget, QGraphicsView, QGraphicsScene]:
        """
        Returns the Qt widgets that compose the given node editor.

        :param node_editor: Name of the node editor to get the Qt widgets from.
        :return: tuple containing the node editor widget, the node editor view and
            the node editor scene.
        """

        node_editor_widget = utils.to_qt_object(node_editor)
        stack = node_editor_widget.findChild(QStackedLayout)
        view = stack.currentWidget().findChild(QGraphicsView)

        return node_editor_widget, view, view.scene()

    def exists(self) -> bool:
        """
        Returns whether the node editor exists.

        :return: True if the node editor exists, False otherwise.
        """

        return (
            cmds.nodeEditor(self.objectName(), exists=True)
            if self.objectName()
            else False
        )

    def show(self):
        """
        Shows the node editor.
        """

        cmds.NodeEditorWindow()
        self._editor, self._view, self._scene = NodeEditorWrapper.as_qt_widgets(
            nodeeditor.primary_node_editor()
        )

    def add_nodes_on_create(self):
        """
        Returns whether new nodes are added to the graph when created.

        :return: True if new nodes are added to the graph when created, False otherwise.
        """

        return cmds.nodeEditor(self.objectName(), addNewNodes=True, query=True)

    def set_add_nodes_on_create(self, flag: bool):
        """
        Sets whether new nodes are added to the graph when created.

        :param flag: True to add new nodes to the graph when created, False otherwise.
        """

        cmds.nodeEditor(self.objectName(), addNewNodes=flag, edit=True)
