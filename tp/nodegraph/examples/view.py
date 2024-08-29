from __future__ import annotations

import typing
import logging
from typing import Any

from Qt.QtCore import Qt, QObject, QEvent
from Qt.QtWidgets import (
    QWidget,
    QMainWindow,
    QTabWidget,
    QDockWidget,
    QMdiArea,
    QMdiSubWindow,
    QMenuBar,
)

from .widgets import menubar
from ..widgets import palette
from ..widgets.properties import editor
from ...qt import factory, contexts

if typing.TYPE_CHECKING:
    from .model import NodeGraphModel
    from ..core.node import BaseNode
    from ..core.graph import NodeGraph

logger = logging.getLogger(__name__)


class SubWindowEventFiler(QObject):
    """
    Class that defines an event filter for MDI sub windows.
    """

    def __init__(self, parent: NodeGraphToolView):
        super().__init__(parent=parent)

        self._parent = parent

    def eventFilter(self, watched: QMdiSubWindow, event: QEvent):
        if event.type() == QEvent.Close:
            build_graph = self._parent.editor_map.pop(watched)
            self._parent.model.state["node_graphs"].remove(build_graph)

        return super().eventFilter(watched, event)


class NodeGraphToolView(QWidget):
    """
    Class that defines the view of the node graph tool.
    """

    def __init__(self, model: NodeGraphModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._model = model
        self._editor_map: dict[QMdiSubWindow, NodeGraph] = {}

        self._menubar: QMenuBar | None = None
        self._main_window: QMainWindow | None = None
        self._window_main_widget: QWidget | None = None

        self._sub_window_event_filter = SubWindowEventFiler(parent=self)

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    @property
    def model(self) -> NodeGraphModel:
        """
        Getter method that returns the model linked with the view.

        :return: node graph model.
        """

        return self._model

    @property
    def editor_map(self) -> dict[QMdiSubWindow, NodeGraph]:
        """
        Getter method that returns the editor map.

        :return: editor map.
        """

        return self._editor_map

    def _setup_widgets(self):
        """
        Internal function that setup all view widgets.
        """

        self._main_window = QMainWindow()
        self._main_window.setTabPosition(Qt.RightDockWidgetArea, QTabWidget.East)
        self._main_window.setTabPosition(Qt.LeftDockWidgetArea, QTabWidget.North)
        self._window_main_widget = QWidget(parent=self)
        self._main_window.setCentralWidget(self._window_main_widget)

        self._nodes_palette = palette.NodesPalette(parent=self)
        self._nodes_palette_dock = QDockWidget("Nodes Palette")
        self._nodes_palette_dock.setWidget(self._nodes_palette)
        self._nodes_palette_dock.setAllowedAreas(Qt.LeftDockWidgetArea)

        self._properties_editor = editor.PropertyEditor(parent=self)
        self._properties_editor_dock = QDockWidget("Properties Editor")
        self._properties_editor_dock.setWidget(self._properties_editor)
        self._properties_editor_dock.setAllowedAreas(Qt.RightDockWidgetArea)

        self._undo_history_dock = QDockWidget("Undo History")
        self._properties_editor_dock.setAllowedAreas(Qt.RightDockWidgetArea)

        self._mdi_area = QMdiArea(parent=self)
        self._mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._mdi_area.setViewMode(QMdiArea.TabbedView)
        self._mdi_area.setDocumentMode(True)
        self._mdi_area.setTabsClosable(True)
        self._mdi_area.setTabsMovable(True)

        self._main_window.addDockWidget(Qt.LeftDockWidgetArea, self._nodes_palette_dock)
        self._main_window.addDockWidget(
            Qt.RightDockWidgetArea, self._properties_editor_dock
        )
        self._main_window.addDockWidget(Qt.RightDockWidgetArea, self._undo_history_dock)

        self._setup_menubar()

    def _setup_menubar(self):
        """
        Internal function that setup menubar.
        """

        self._menubar = menubar.NodeGraphMenuBar(model=self._model)
        self._main_window.setMenuBar(self._menubar)

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        contents_layout = factory.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(contents_layout)

        window_main_layout = factory.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self._window_main_widget.setLayout(window_main_layout)
        window_main_layout.addWidget(self._mdi_area)

        contents_layout.addWidget(self._main_window)

    def _setup_signals(self):
        """
        Internal function that setup all signals and slots connections.
        """

        self._model.listen("node_graphs", self._on_node_graphs_model_changed)
        self._model.listen(
            "active_node_graph", self._on_active_node_graph_model_changed
        )
        self._model.listen("title", lambda title: self.setWindowTitle(title))

        self._mdi_area.subWindowActivated.connect(self._on_mdi_sub_window_activated)
        self._properties_editor.propertyChanged.connect(
            self._on_properties_editor_property_changed
        )

    def _create_mdi_child(self, build_graph: NodeGraph) -> QMdiSubWindow:
        """
        Internal function that creates a new MDI build graph child window.

        :param build_graph: build graph to create the child window for.
        :return: new MDI child window.
        """

        graph_widget = build_graph.widget()
        sub_window = self._mdi_area.addSubWindow(graph_widget)
        sub_window.installEventFilter(self._sub_window_event_filter)

        self._editor_map[sub_window] = build_graph

        return sub_window

    def _on_node_graphs_model_changed(self, node_graphs: list[NodeGraph]):
        """
        Internal callback function that is called when node graphs changes.

        :param node_graphs: list of build graphs.
        """

        if not node_graphs:
            self._mdi_area.closeAllSubWindows()
            return

        new_node_graph = node_graphs[-1]

        # noinspection PyBroadException
        try:
            sub_window = self._create_mdi_child(new_node_graph)
            sub_window.show()
        except Exception:
            logger.exception("Failed to create new build window", exc_info=True)
            return

        new_node_graph.nodeSelectionChanged.connect(
            self._on_node_graph_node_selection_changed
        )
        new_node_graph.nodeDoubleClicked.connect(
            self._on_node_graph_node_double_clicked
        )
        new_node_graph.propertyChanged.connect(self._on_node_graph_property_changed)
        new_node_graph.nodesDeleted.connect(self._on_node_graph_nodes_deleted)

        undo_history = self._undo_history_dock.widget()
        if undo_history:
            undo_history.close()
        self._undo_history_dock.setWidget(new_node_graph.undo_view)

    def _on_active_node_graph_model_changed(self, active_node_graph: NodeGraph):
        """
        Internal callback function that is called when active build graph changes.

        :param active_node_graph: active node graph.
        """

        active_sub_window: QMdiSubWindow | None = None
        for sub_window, build_graph in self._editor_map.items():
            if build_graph == active_node_graph:
                active_sub_window = sub_window
                break
        if active_sub_window:
            with contexts.block_signals(self._mdi_area):
                self._mdi_area.setActiveSubWindow(active_sub_window)

        with contexts.block_signals(self._nodes_palette):
            self._nodes_palette.refresh(active_node_graph)

    def _on_mdi_sub_window_activated(self, sub_window: QMdiSubWindow):
        """
        Internal callback function that is called when a sub window is activated.

        :param sub_window: activated sub window.
        """

        if not sub_window:
            self._model.set_active_node_graph(None)
            return

        if sub_window not in self._editor_map:
            logger.error("Active sub window is not available within editor map.")
            return

        build_graph = self._editor_map[sub_window]
        self._model.set_active_node_graph(build_graph)

    def _on_properties_editor_property_changed(
        self, node_id: str, property_name: str, property_value: Any
    ):
        """
        Internal callback function that is called when a property in the properties editor changes.

        :param node_id: id of the node that changed.
        :param property_name: name of the property that changed.
        :param property_value: new value of the property.
        """

        active_node_graph: NodeGraph | None = self._model.state["active_node_graph"]
        if not active_node_graph:
            return

        node = active_node_graph.node_by_id(node_id)
        if node.property(property_name) == property_value:
            return

        node.set_property(property_name, property_value)

    def _on_node_graph_node_selection_changed(
        self, selected_nodes: list[BaseNode], deselected_nodes: list[BaseNode]
    ):
        """
        Internal callback function that is called when a node is selected in the node graph.

        :param selected_nodes: list of selected nodes.
        :param deselected_nodes: list of deselected nodes.
        """

        for node in deselected_nodes:
            self._properties_editor.remove_node(node)
        for node in selected_nodes:
            self._properties_editor.add_node(node)

    def _on_node_graph_node_double_clicked(self, node: BaseNode):
        """
        Internal callback function that is called when a node is double-clicked in the node graph.

        :param node: node that was double-clicked.
        """

        self._properties_editor.add_node(node)

    def _on_node_graph_property_changed(
        self, node: BaseNode, property_name: str, property_value: Any
    ):
        """
        Internal callback function that is called when a property in a node changes.

        :param node: node that changed.
        :param property_name: name of the property that changed.
        :param property_value: new value of the property.
        """

        self._properties_editor.update_property_editor_widget(
            node, property_name, property_value
        )

    def _on_node_graph_nodes_deleted(self, node_ids: list[str]):
        """
        Internal callback function that is called when nodes are deleted in the node graph.

        :param node_ids: list of node ids.
        """

        active_node_graph: NodeGraph | None = self._model.state["active_node_graph"]
        if not active_node_graph:
            return

        for node_id in node_ids:
            node = active_node_graph.node_by_id(node_id)
            self._properties_editor.remove_node(node)
