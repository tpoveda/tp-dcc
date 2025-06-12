from __future__ import annotations

import typing

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QMenuBar, QMenu, QAction, QActionGroup
from Qt.QtGui import QIcon, QKeySequence

from tp.python import paths

if typing.TYPE_CHECKING:
    from ..model import NodeGraphModel


class NodeGraphMenuBar(QMenuBar):
    """
    Class that defines a menubar for Node Graph tool.
    """

    def __init__(self, model: NodeGraphModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._file_menu = FileMenu(model=model, parent=self)
        self._graph_menu = GraphMenu(model=model, parent=self)

        self.addMenu(self._file_menu)
        self.addMenu(self._graph_menu)


class FileMenu(QMenu):
    """
    Class that defines the File menu for NodeGraph tool.
    """

    def __init__(self, model: NodeGraphModel, parent: QWidget | None = None):
        super().__init__("File", parent=parent)

        self._model = model

        self._setup_actions()
        self._setup_shortcuts()
        self._populate()
        self._setup_signals()

        self.setTearOffEnabled(True)

    def _setup_actions(self):
        """
        Internal function that creates all actions for the menu.
        """

        self._new_build_action = QAction("New Build", parent=self)

    def _setup_shortcuts(self):
        """
        Internal function that setup all shortcuts for the actions.
        """

        self._new_build_action.setShortcut("Ctrl+N")

    def _populate(self):
        """
        Internal function that populates the menu with all actions.
        """

        self.addSection("Build Graph")
        self.addAction(self._new_build_action)

    def _setup_signals(self):
        """
        Internal function that setup all signals for the actions.
        """

        self._new_build_action.triggered.connect(self._model.new_graph)


class GraphMenu(QMenu):
    """
    Class that defines the Graph menu for NodeGraph tool.
    """

    def __init__(self, model: NodeGraphModel, parent: QWidget | None = None):
        super().__init__("&Graph", parent=parent)

        self._model = model

        self._setup_actions()
        self._setup_sub_menus()
        self._setup_shortcuts()
        self._populate()
        self._setup_signals()

        self.setTearOffEnabled(True)

    def _setup_actions(self):
        """
        Internal function that creates all actions for the menu.
        """

        self._connector_type_group = QActionGroup(self)
        self._connector_type_direct_action = QAction("Direct", parent=self)
        self._connector_type_bezier_action = QAction("Bezier", parent=self)
        self._connector_type_square_action = QAction("Square", parent=self)
        self._connector_type_group.addAction(self._connector_type_direct_action)
        self._connector_type_group.addAction(self._connector_type_bezier_action)
        self._connector_type_group.addAction(self._connector_type_square_action)
        self._connector_type_direct_action.setCheckable(True)
        self._connector_type_bezier_action.setCheckable(True)
        self._connector_type_square_action.setCheckable(True)

        self._reset_stepped_execution_action = QAction(
            "&Reset Stepped Execution", parent=self
        )
        self._execute_step_action = QAction("&Execute Step", parent=self)
        self._execute_action = QAction(
            QIcon(paths.canonical_path("../resources/icons/execute.svg")),
            "&Execute",
            parent=self,
        )

    def _setup_sub_menus(self):
        """
        Internal function that creates all sub-menus for the menu.
        """

        self._connector_type_menu = QMenu("Connector Type", parent=self)

    # noinspection PyTypeChecker
    def _setup_shortcuts(self):
        """
        Internal function that setup all shortcuts for the actions.
        """

        self._execute_step_action.setShortcut(QKeySequence(Qt.Key_F6))
        self._execute_action.setShortcut(QKeySequence(Qt.Key_F5))

    def _populate(self):
        """
        Internal function that populates the menu with all actions.
        """

        self.addMenu(self._connector_type_menu)
        self._connector_type_menu.addAction(self._connector_type_direct_action)
        self._connector_type_menu.addAction(self._connector_type_bezier_action)
        self._connector_type_menu.addAction(self._connector_type_square_action)

        self.addSection("Execution")
        self.addAction(self._reset_stepped_execution_action)
        self.addAction(self._execute_step_action)
        self.addSeparator()
        self.addAction(self._execute_action)

    def _setup_signals(self):
        """
        Internal function that setup all signals for the actions.
        """

        self._execute_action.triggered.connect(self._on_execute_action_triggered)

    def _on_execute_action_triggered(self):
        """
        Internal callback function that is called when the execute action is triggered.
        """

        self._model.execute_graph()
