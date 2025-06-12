from __future__ import annotations

import json
import typing
import logging
from typing import Type, Iterable

from Qt.QtCore import (
    Qt,
    QObject,
    Signal,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    QDataStream,
    QIODevice,
)
from Qt.QtWidgets import (
    QWidget,
    QGraphicsView,
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsSceneMouseEvent,
    QUndoStack,
    QAction,
    QMenu,
    QMenuBar,
    QRubberBand,
)
from Qt.QtGui import (
    QColor,
    QFont,
    QPixmap,
    QPainter,
    QPainterPath,
    QKeySequence,
    QFocusEvent,
    QKeyEvent,
    QMouseEvent,
    QWheelEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QDragLeaveEvent,
)

from . import uiconsts
from .port import PortView
from .scene import NodeGraphScene
from .slicer import Slicer, FreehandSlicer
from .node import AbstractNodeView, NodeView
from .connector import ConnectorView, LiveConnectorView
from ..widgets import actions, dialogs, search
from ..core import consts, events
from ..nodes.node_backdrop import BackdropNodeView
from ...math import scalar

if typing.TYPE_CHECKING:
    from ..core.graph import NodeGraph
    from ..core.datatypes import DataType

logger = logging.getLogger(__name__)


class NodeGraphView(QGraphicsView):
    """
    Class that defines the graph view for the node graph.
    """

    nodeDropped = Signal(events.DropNodeEvent)
    nodeSelected = Signal(str)
    nodeSelectionChanged = Signal(list, list)
    nodeDoubleClicked = Signal(str)
    nodesMoved = Signal(object)
    nodeNameChanged = Signal(str, str)
    nodeInserted = Signal(object, str, object)
    variableDropped = Signal(events.DropVariableEvent)
    connectionSliced = Signal(list)
    connectionsChanged = Signal(list, list)
    nodeBackdropUpdated = Signal(str, str, object)
    contextMenuPrompted = Signal(str, object)
    searchTriggered = Signal(str, str, str, tuple)

    def __init__(
        self, undo_stack: QUndoStack | None = None, parent: QWidget | None = None
    ):
        super().__init__(parent=parent)

        self._acyclic: bool = True
        self._scene_rect = QRectF(0, 0, self.size().width(), self.size().height())
        self._graphics_scene = NodeGraphScene(parent=self)
        self._layout_direction: int = consts.LayoutDirection.Horizontal.value
        self._connector_style: int = consts.ConnectorStyle.Curved.value
        self._connector_mode: int = uiconsts.ConnectorMode.Disabled.value
        self._num_lods: int = 5
        self._zoom_range: tuple[float, float] = (
            uiconsts.NODE_GRAPH_MINIMUM_ZOOM,
            uiconsts.NODE_GRAPH_MAXIMUM_ZOOM,
        )
        self._undo_action: QAction | None = None
        self._redo_action: QAction | None = None

        # Create hidden menu bar as a workaround to allow shortcuts to work.
        self._context_menu_bar = QMenuBar(parent=self)
        self._context_menu_bar.setNativeMenuBar(False)
        self._context_menu_bar.setMaximumSize(0, 0)
        self._context_graph_menu = actions.BaseMenu("NodeGraph", parent=self)
        self._context_node_menu = actions.BaseMenu("Nodes", parent=self)

        self._alt_state: bool = False
        self._ctrl_state: bool = False
        self._shift_state: bool = False
        self._left_mouse_button_state: bool = False
        self._right_mouse_button_state: bool = False
        self._middle_mouse_button_state: bool = False
        self._mouse_pos = QPointF(0.0, 0.0)
        self._origin_mouse_pos = QPoint(
            0, 0
        )  # mouse position when user clicks on the scene.
        self._previous_mouse_pos = QPoint(int(self.width() / 2), int(self.height() / 2))
        self._node_positions: dict[AbstractNodeView, tuple[float, float]] = {}
        self._previous_selected_nodes: list[AbstractNodeView] = []
        self._previous_selected_connectors: list[AbstractNodeView] = []
        self._connector_collision: bool = False
        self._allow_connector_slicing: bool = True
        self._colliding_state: bool = False
        self._detached_port: PortView | None = None
        self._start_port: PortView | None = None

        if undo_stack:
            self._undo_action = undo_stack.createUndoAction(self, "&Undo")
            self._redo_action = undo_stack.createRedoAction(self, "&Redo")

        self._rubber_band = QRubberBand(QRubberBand.Rectangle, parent=self)
        self._rubber_band.setProperty("is_active", False)

        self._setup_ui()
        self._setup_context_menus()
        self.setScene(self._graphics_scene)

        self._graph_label = NodeGraphViewTitleLabel()
        self._graph_label.setPlainText("Node Graph")
        self._live_connector = LiveConnectorView()
        self._live_connector.setVisible(False)
        self._slicer = Slicer()
        self._slicer.setVisible(False)
        self._freehand_slicer = FreehandSlicer()
        self._freehand_slicer.setVisible(False)
        self._over_slicer_connectors: list[ConnectorView] = []
        self._search_widget = search.NodesTabSearchWidget(parent=self)
        self._search_widget.searchSubmitted.connect(self._on_search_submitted)

        text_color = QColor(
            *tuple(
                map(
                    lambda i, j: i - j,
                    (255, 255, 255),
                    uiconsts.NODE_GRAPH_BACKGROUND_COLOR,
                )
            )
        )
        text_color.setAlpha(50)
        self._cursor_text = QGraphicsTextItem()
        self._cursor_text.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self._cursor_text.setDefaultTextColor(text_color)
        self._cursor_text.setZValue(uiconsts.Z_VALUE_CONNECTOR - 1)
        font = self._cursor_text.font()
        font.setPointSize(7)
        self._cursor_text.setFont(font)

        self._graphics_scene.addItem(self._graph_label)
        self._graphics_scene.addItem(self._live_connector)
        self._graphics_scene.addItem(self._slicer)
        self._graphics_scene.addItem(self._freehand_slicer)
        self._graphics_scene.addItem(self._cursor_text)

        self._update_scene()

        self._last_size: QSize = self.size()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("QGraphicsView { border: none; }")

    def __repr__(self) -> str:
        """
        Returns a string representation of the node graph view.

        :return: string representation.
        """

        return f"<{self.__class__.__name__}() object at {hex(id(self))}>"

    @property
    def graphics_scene(self) -> NodeGraphScene:
        """
        Getter method that returns the graphics scene of the view.

        :return: graphics scene.
        """

        return self._graphics_scene

    @property
    def acyclic(self) -> bool:
        """
        Getter method that returns whether the node graph is acyclic or not.

        :return: acyclic state.
        """

        return self._acyclic

    @acyclic.setter
    def acyclic(self, value: bool):
        """
        Setter method that sets the acyclic state of the node graph.

        :param value: acyclic state.
        """

        self._acyclic = value

    @property
    def layout_direction(self) -> int:
        """
        Getter method that returns the layout direction of the view.

        :return: layout direction.
        """

        return self._layout_direction

    @layout_direction.setter
    def layout_direction(self, value: int):
        """
        Setter method that sets the layout direction of the view.

        :param value: layout direction.
        """

        self._layout_direction = value

    @property
    def connector_style(self) -> int:
        """
        Getter method that returns the connector style of the view.

        :return: connector layout.
        """

        return self._connector_style

    @connector_style.setter
    def connector_style(self, value: int):
        """
        Setter method that sets the connector style of the view.

        :param value: connector style.
        """

        self._connector_style = value
        for connector_view in self.connectors():
            connector_view.draw_path(
                connector_view.input_port, connector_view.output_port
            )

    @property
    def show_details(self) -> bool:
        """
        Getter method that returns whether the node view shows details or not.

        :return: show details state.
        """

        return self.lod_value_from_scale() < 3

    @property
    def context_menus(self) -> dict[str, actions.BaseMenu]:
        """
        Getter method that returns the context menus of the view.

        :return: context menus.
        """

        return {
            "graph": self._context_graph_menu,
            "nodes": self._context_node_menu,
        }

    def resizeEvent(self, event):
        """
        Reimplemented resize event to update the scene rect.

        :param event: resize event.
        """

        width = self.size().width()
        height = self.size().height()
        # Make sure that width and height are not 0.
        # If that's the scale we automatically resize view to last valid size.
        if 0 in [width, height]:
            self.resize(self._last_size)
        delta = max(width / self._last_size.width(), height / self._last_size.height())
        self._set_zoom(delta)
        self._last_size = self.size()
        super().resizeEvent(event)

    def focusInEvent(self, event: QFocusEvent):
        """
        Reimplemented focus in event to emit focusIn signal.

        :param event: focus in event.
        """

        # Re-populate menubar so QAction shortcuts do not conflict with parent app.
        self._context_menu_bar.addMenu(self._context_graph_menu)
        self._context_menu_bar.addMenu(self._context_node_menu)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        """
        Reimplemented focus out event to emit focusOut signal.

        :param event: focus out event.
        """

        # Clear menubar so QAction shortcuts do not conflict with parent app.
        self._context_menu_bar.clear()

        # Make sure cursor text is hidden.
        self._cursor_text.setVisible(False)

        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Reimplemented key press event to handle key press events.

        :param event: key press event.
        :return:
        """

        self._alt_state = bool(event.modifiers() & Qt.AltModifier)
        self._ctrl_state = bool(event.modifiers() & Qt.ControlModifier)
        self._shift_state = bool(event.modifiers() & Qt.ShiftModifier)

        if self._live_connector.isVisible():
            super().keyPressEvent(event)
            return

        self._cursor_text.setVisible(False)
        overlay_text: str | None = None
        if not self._alt_state:
            if self._ctrl_state and self._shift_state:
                if self._allow_connector_slicing:
                    overlay_text = "\n    CTRL + SHIFT:\n    Connector Slicer Enabled"
            elif self._shift_state:
                overlay_text = "\n    SHIFT:\n    Toggle/Extend Selection"
            elif self._ctrl_state:
                overlay_text = "\n    CTRL:\n    Deselect Nodes"
        else:
            if self._ctrl_state and self._shift_state:
                if self._allow_connector_slicing:
                    overlay_text = "\n    ALT + CTRL + SHIFT:\n    Connector Freehand Slicer Enabled"

        if overlay_text:
            self._cursor_text.setPlainText(overlay_text)
            self._cursor_text.setPos(self.mapToScene(self._previous_mouse_pos))
            self._cursor_text.setVisible(True)

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        """
        Reimplemented key release event to handle key release events.

        :param event: key release event.
        """

        self._alt_state = bool(event.modifiers() & Qt.AltModifier)
        self._ctrl_state = bool(event.modifiers() & Qt.ControlModifier)
        self._shift_state = bool(event.modifiers() & Qt.ShiftModifier)

        super().keyReleaseEvent(event)

        self._cursor_text.setPlainText("")
        self._cursor_text.setVisible(False)

    def mousePressEvent(self, event: QMouseEvent):
        """
        Reimplemented mouse press event to emit nodesMoved signal.

        :param event: mouse press event.
        """

        if event.button() == Qt.LeftButton:
            self._left_mouse_button_state = True
        elif event.button() == Qt.RightButton:
            self._right_mouse_button_state = True
        elif event.button() == Qt.MiddleButton:
            self._middle_mouse_button_state = True

        self._origin_mouse_pos = event.pos()
        self._previous_mouse_pos = event.pos()
        self._previous_selected_nodes, self._previous_selected_connectors = (
            self.selected_items()
        )
        map_pos = self.mapToScene(event.pos())

        if self._search_widget.isVisible():
            self.tab_search_toggle()

        if self._allow_connector_slicing:
            slicer_mode = all(
                [self._ctrl_state, self._shift_state, self._left_mouse_button_state]
            )
            freehand_slicer_mode = all(
                [
                    self._alt_state,
                    self._ctrl_state,
                    self._shift_state,
                    self._left_mouse_button_state,
                ]
            )
            if freehand_slicer_mode:
                self._freehand_slicer.draw_path(map_pos, map_pos)
                self._freehand_slicer.setVisible(True)
                self._connector_mode = uiconsts.ConnectorMode.CutFreehand.value
                return
            if slicer_mode:
                self._slicer.draw_path(map_pos, map_pos)
                self._slicer.setVisible(True)
                self._connector_mode = uiconsts.ConnectorMode.Cut.value
                return

        # Pan mode.
        if self._alt_state:
            return

        nodes: list[AbstractNodeView] = []
        connectors: list[ConnectorView] = []
        backdrop: BackdropNodeView | None = None
        items = self._items_near(map_pos, item_type=None, width=20, height=20)
        for item in items:
            if isinstance(item, ConnectorView):
                connectors.append(item)
            elif isinstance(item, AbstractNodeView):
                if isinstance(item, BackdropNodeView):
                    backdrop = item
                    continue
                nodes.append(item)
        if nodes:
            self._middle_mouse_button_state = False

        # Retrieve all current selected nodes manually because the selected nodes from view are not updated at this
        # point.
        selection = set([])
        if self._left_mouse_button_state:
            # Toggle extend node selection.
            if self._shift_state:
                if items and backdrop == items[0]:
                    backdrop.selected = not backdrop.selected
                    if backdrop.selected:
                        selection.add(backdrop)
                    for n in backdrop.nodes():
                        n.selected = backdrop.selected
                        if backdrop.selected:
                            selection.add(n)
                else:
                    for node in nodes:
                        node.selected = not node.selected
                        if node.selected:
                            selection.add(node)
            # Unselected nodes.
            elif self._ctrl_state:
                if items and backdrop == items[0]:
                    backdrop.selected = False
                else:
                    for node in nodes:
                        node.selected = False
            # Add to selection.
            else:
                if backdrop:
                    selection.add(backdrop)
                    for n in backdrop.nodes():
                        selection.add(n)
                for node in nodes:
                    if node.selected:
                        selection.add(node)
        selection.update(self.selected_nodes())

        # Store updated node positions.
        self._node_positions.update(
            {node_view: node_view.xy_pos for node_view in selection}
        )

        # Show selection rubber band.
        if self._left_mouse_button_state and not items:
            rect = QRect(self._previous_mouse_pos, QSize())
            rect = rect.normalized()
            map_rect = self.mapToScene(rect).boundingRect()
            self.scene().update(map_rect)
            self._rubber_band.setGeometry(rect)
            self._rubber_band.setProperty("is_active", True)
            self._rubber_band.show()

        # Stop here, se we do not select a node.
        if self._ctrl_state:
            return

        # Allow new live connector with Shift modifier on port view that allow for multi connection.
        if self._shift_state:
            if connectors:
                connectors[0].reset()
                port_view = connectors[0].port_view_from_pos(map_pos, reverse=True)
                if not port_view.locked and port_view.multi_connection:
                    self._cursor_text.setPlainText("")
                    self._cursor_text.setVisible(False)
                    self._start_live_connection(port_view)

            # Return here to avoid default behaviour of unselecting nodes with the Shift modifier.
            return

        if not self._live_connector.isVisible():
            super().mousePressEvent(event)

    # noinspection PyPep8Naming
    def sceneMousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is pressed on the scene.

        :param event: mouse event.
        """

        # Pan mode or connector slicer is enabled.
        if self._alt_state or self._connector_mode in (
            uiconsts.ConnectorMode.Cut.value,
            uiconsts.ConnectorMode.CutFreehand.value,
        ):
            return

        if self._live_connector.isVisible():
            self._apply_live_connection(event)
            return

        pos = event.scenePos()

        node_view: AbstractNodeView | NodeView | None = None
        port_view: PortView | None = None
        connector_view: ConnectorView | None = None
        items = self._items_near(pos, None, 5, 5)
        for item in items:
            if isinstance(item, AbstractNodeView):
                node_view = item
            elif isinstance(item, PortView):
                port_view = item
            elif isinstance(item, ConnectorView):
                connector_view = item
            if any([node_view, port_view, connector_view]):
                break

        if port_view:
            if port_view.locked:
                return
            if not port_view.multi_connection and port_view.connected_ports:
                self._detached_port = port_view.connected_ports[0]
            self._start_live_connection(port_view)
            if not port_view.multi_connection:
                [
                    connector_view.delete()
                    for connector_view in port_view.connected_connectors
                ]
            return

        if node_view:
            node_items = self._items_near(pos, AbstractNodeView, 3, 3)
            for node_view in node_items:
                self._node_positions[node_view] = node_view.xy_pos
            if event.button() == Qt.LeftButton:
                self.nodeSelected.emit(node_view.id)
            if not isinstance(node_view, BackdropNodeView):
                return

        if connector_view:
            if not self._left_mouse_button_state:
                return
            from_port_view = connector_view.port_view_from_pos(pos, True)
            if from_port_view.locked:
                return
            from_port_view.hovered = True
            attr = {
                consts.PortType.Input.value: "output_port",
                consts.PortType.Output.value: "input_port",
            }
            self._detached_port = getattr(
                connector_view, attr[from_port_view.port_type]
            )
            self._start_live_connection(from_port_view)
            self._live_connector.draw_path(self._start_port, cursor_pos=pos)
            if self._shift_state:
                self._live_connector.shift_selected = True
                return
            connector_view.delete()

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Reimplemented mouse move event.

        :param event: mouse move event.
        """

        scene_pos = self.mapToScene(event.pos())
        self._alt_state = bool(event.modifiers() & Qt.AltModifier)
        self._ctrl_state = bool(event.modifiers() & Qt.ControlModifier)
        self._shift_state = bool(event.modifiers() & Qt.ShiftModifier)

        # Update slicer.
        if self._connector_mode in (
            uiconsts.ConnectorMode.Cut.value,
            uiconsts.ConnectorMode.CutFreehand.value,
        ):
            if self._allow_connector_slicing:
                if self._left_mouse_button_state:
                    if self._slicer.isVisible():
                        p1 = self._slicer.path().pointAtPercent(0)
                        p2 = self.mapToScene(self._previous_mouse_pos)
                        self._slicer.draw_path(p1, p2)
                        self._slicer.show()
                        self._connectors_ready_to_slice(self._slicer.path())
                    elif self._freehand_slicer.isVisible():
                        self._freehand_slicer.add_point(scene_pos)
                        self._connectors_ready_to_slice(self._freehand_slicer.path())
                else:
                    self._cursor_text.setPos(scene_pos)
            self._previous_mouse_pos = event.pos()
            super().mouseMoveEvent(event)
            return

        if self._middle_mouse_button_state and self._alt_state:
            pos_x = event.x() - self._previous_mouse_pos.x()
            zoom = 0.1 if pos_x > 0 else -0.1
            self._set_zoom(zoom, 0.05, pos=QPointF(event.pos()))
        elif self._middle_mouse_button_state or (
            self._left_mouse_button_state and self._alt_state
        ):
            previous_pos = self.mapToScene(self._previous_mouse_pos)
            current_pos = scene_pos
            delta = previous_pos - current_pos
            self._set_pan(delta.x(), delta.y())

        # Update cursor text position.
        # if not self._alt_state:
        if self._shift_state or self._ctrl_state:
            if not self._live_connector.isVisible():
                self._cursor_text.setPos(scene_pos)

        # Handle selection of nodes/connectors based on rubber band area.
        if self._left_mouse_button_state and self._rubber_band.property("is_active"):
            rect = QRect(self._origin_mouse_pos, event.pos()).normalized()
            if max(rect.width(), rect.height()) > 5:
                if not self._rubber_band.isVisible():
                    self._rubber_band.show()
                map_rect = self.mapToScene(rect).boundingRect()
                path = QPainterPath()
                path.addRect(map_rect)
                self._rubber_band.setGeometry(rect)
                self.scene().setSelectionArea(
                    path, Qt.ReplaceSelection, Qt.IntersectsItemShape
                )
                self.scene().update(map_rect)
                if self._shift_state or self._ctrl_state:
                    selected_node_views, selected_connector_views = (
                        self.selected_items()
                    )
                    for node_view in self._previous_selected_nodes:
                        node_view.selected = True
                    if self._ctrl_state:
                        for selected_connector_view in selected_connector_views:
                            selected_connector_view.setSelected(False)
                        for selected_node_view in selected_node_views:
                            selected_node_view.selected = True
        # Handle the selection of connector views.
        elif self._left_mouse_button_state:
            self._colliding_state = False
            selected_node_views, selected_connector_views = self.selected_items()
            if len(selected_node_views) == 1:
                node_view = selected_node_views[0]
                [
                    connector_view.setSelected(False)
                    for connector_view in selected_connector_views
                ]
                if self._connector_collision:
                    colliding_connectors = [
                        i
                        for i in node_view.collidingItems()
                        if isinstance(i, ConnectorView) and i.isVisible()
                    ]
                    for connector_view in colliding_connectors:
                        if not connector_view.input_port:
                            continue
                        port_node_check = all(
                            [
                                connector_view.input_port.node_view is not node_view,
                                connector_view.output_port.node_view is not node_view,
                            ]
                        )
                        if port_node_check:
                            connector_view.setSelected(True)
                            self._colliding_state = True
                            break

        self._previous_mouse_pos = event.pos()

        super().mouseMoveEvent(event)

    # noinspection PyPep8Naming
    def sceneMouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when the mouse is moved on the scene.

        :param event: mouse event.
        """

        if not self._live_connector.isVisible() or not self._start_port:
            return

        pos = event.scenePos()
        pointer_color: tuple[int, int, int, int] | None = None
        for item in self.scene().items(pos):
            if not isinstance(item, PortView):
                continue
            x = item.boundingRect().width() / 2
            y = item.boundingRect().height() / 2
            pos = item.scenePos()
            pos.setX(pos.x() + x)
            pos.setY(pos.y() + y)
            if item == self._start_port:
                break
            pointer_color = uiconsts.CONNECTOR_HIGHLIGHTED_COLOR
            break

        self._live_connector.draw_path(
            self._start_port, cursor_pos=pos, color=pointer_color
        )

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Reimplemented mouse release event to emit nodesMoved signal.

        :param event: mouse release event.
        """

        if event.button() == Qt.LeftButton:
            self._left_mouse_button_state = False
        elif event.button() == Qt.RightButton:
            self._right_mouse_button_state = False
        elif event.button() == Qt.MiddleButton:
            self._middle_mouse_button_state = False

        # Hide slicer.
        if self._slicer.isVisible():
            self._slice_connectors(self._slicer.path())
            self._slicer.draw_path(QPointF(0.0, 0.0), QPointF(0.0, 0.0))
            self._slicer.setVisible(False)
            self._connector_mode = uiconsts.ConnectorMode.Disabled
        if self._freehand_slicer.isVisible():
            self._slice_freehand_connectors(
                self._freehand_slicer.intersected_connectors()
            )
            self._freehand_slicer.reset()
            self._freehand_slicer.setVisible(False)
            self._connector_mode = uiconsts.ConnectorMode.Disabled

        # Get selected nodes, emit signal and hide selection rubber band.
        if self._rubber_band.property("is_active"):
            self._rubber_band.setProperty("is_active", False)
            if self._rubber_band.isVisible():
                rect = self._rubber_band.rect()
                map_rect = self.mapToScene(rect).boundingRect()
                self._rubber_band.hide()
                rect = QRect(self._origin_mouse_pos, event.pos()).normalized()
                rect_items = self.scene().items(self.mapToScene(rect).boundingRect())
                node_ids: list[str] = []
                for item in rect_items:
                    if isinstance(item, AbstractNodeView):
                        node_ids.append(item.id)
                if node_ids:
                    prev_ids = [
                        n.id for n in self._previous_selected_nodes if not n.selected
                    ]
                    self.nodeSelected.emit(node_ids[0])
                    self.nodeSelectionChanged.emit(node_ids, prev_ids)
                else:
                    # Make sure to deselect nodes if no nodes are selected.
                    node_views, _ = self.selected_items()
                    prev_ids = [
                        n.id for n in self._previous_selected_nodes if not n.selected
                    ]
                    self.nodeSelectionChanged.emit([], prev_ids)
                self.scene().update(map_rect)
                return

        # Find new node position and emit signal (only if is not colliding with a connector).
        moved_nodes = {
            node_view: xy_pos
            for node_view, xy_pos in self._node_positions.items()
            if node_view.xy_pos != xy_pos
        }
        if moved_nodes and not self._colliding_state:
            self.nodesMoved.emit(moved_nodes)
        self._node_positions.clear()

        # If select node collides with a connector then we call signal to insert node.
        node_views, connector_views = self.selected_items()
        if self._colliding_state and node_views and connector_views:
            self.nodeInserted.emit(connector_views[0], node_views[0].id, moved_nodes)

        # Emit node selection changed signal
        prev_ids = [n.id for n in self._previous_selected_nodes if not n.selected]
        node_ids = [n.id for n in node_views if n not in self._previous_selected_nodes]
        self.nodeSelectionChanged.emit(node_ids, prev_ids)

        super().mouseReleaseEvent(event)

    # noinspection PyPep8Naming
    def sceneMouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is released on the scene.

        :param event: mouse event.
        """

        if event.button() != Qt.MiddleButton:
            self._apply_live_connection(event)

    def wheelEvent(self, event: QWheelEvent):
        """
        Reimplemented wheel event to zoom in and out of the node graph view.

        :param event: wheel event.
        """

        delta = event.angleDelta().y()
        delta = delta if delta != 0 else event.angleDelta().x()
        self._set_zoom(delta, pos=event.position())

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Reimplemented drag enter event to emit itemDragEntered signal.

        :param event: drag enter event.
        """

        if event.mimeData().hasFormat(
            consts.NODES_PALETTE_ITEM_MIME_DATA_FORMAT
        ) or event.mimeData().hasFormat(consts.VARS_ITEM_MIME_DATA_FORMAT):
            event.acceptProposedAction()
        else:
            logger.warning(f"Invalid mime data: {event.mimeData().formats()}")
            event.setAccepted(False)

    def dragMoveEvent(self, event: QDragMoveEvent):
        """
        Reimplemented drag move event to emit itemDragEntered signal.

        :param event: drag move event.
        """

        if event.mimeData().hasFormat(
            consts.NODES_PALETTE_ITEM_MIME_DATA_FORMAT
        ) or event.mimeData().hasFormat(consts.VARS_ITEM_MIME_DATA_FORMAT):
            event.acceptProposedAction()
        else:
            event.setAccepted(False)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """
        Reimplemented drag leave event to emit itemDragLeft signal.

        :param event: drag leave event.
        """

        event.ignore()

    def dropEvent(self, event):
        """
        Reimplemented drop event to emit itemDropped signal.

        :param event: drop event.

        """

        if event.mimeData().hasFormat(consts.NODES_PALETTE_ITEM_MIME_DATA_FORMAT):
            event_data = event.mimeData().data(
                consts.NODES_PALETTE_ITEM_MIME_DATA_FORMAT
            )
            data_stream = QDataStream(event_data, QIODevice.ReadOnly)
            pixmap = QPixmap()
            data_stream >> pixmap
            node_id = data_stream.readQString()
            json_data = json.loads(data_stream.readQString())
            mouse_pos = event.pos()
            scene_pos = self.mapToScene(mouse_pos)
            logger.debug(
                f"Dropped Item:\n> NODE_ID: {node_id}\n> Data: {json_data}\n> Mouse Pos:"
                f" {mouse_pos}\n> Scene Pos: {scene_pos}"
            )
            self.nodeDropped.emit(
                events.DropNodeEvent(node_id, json_data, (scene_pos.x(), scene_pos.y()))
            )
            event.setDropAction(Qt.MoveAction)
            event.accept()
        elif event.mimeData().hasFormat(consts.VARS_ITEM_MIME_DATA_FORMAT):
            event_data = event.mimeData().data(consts.VARS_ITEM_MIME_DATA_FORMAT)
            data_stream = QDataStream(event_data, QIODevice.ReadOnly)
            json_data = json.loads(data_stream.readQString())
            mouse_pos = event.pos()
            scene_pos = self.mapToScene(mouse_pos)
            logger.debug(
                f"Dropped Variable:\n> Data: {json_data}\n> Mouse Pos:"
                f" {mouse_pos}\n> Scene Pos: {scene_pos}"
            )
            variable_name = json_data["variable_name"]
            get_set_menu = QMenu(parent=self)
            getter_action = QAction("Get", get_set_menu)
            setter_action = QAction("Set", get_set_menu)
            get_set_menu.addAction(getter_action)
            get_set_menu.addAction(setter_action)
            result_action = get_set_menu.exec_(self.mapToGlobal(event.pos()))
            if result_action is None:
                return
            self.variableDropped.emit(
                events.DropVariableEvent(
                    variable_name,
                    result_action == setter_action,
                    (scene_pos.x(), scene_pos.y()),
                )
            )
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            logger.warning(f"Unsupported item format: {event.mimeData().formats()}")
            event.ignore()

    def contextMenuEvent(self, event):
        """
        Reimplemented context menu event to show context menu.

        :param event: context menu event.
        """

        self._right_mouse_button_state = False

        context_menus = self.context_menus
        context_menu: actions.BaseMenu | None = None
        prompted_data: tuple[str, str | None] | None = None

        if context_menus["nodes"].isEnabled():
            pos = self.mapToScene(self._previous_mouse_pos)
            items = self._items_near(pos)
            node_views = [i for i in items if isinstance(i, AbstractNodeView)]
            if node_views:
                node_view = node_views[0]
                context_menu = context_menus["nodes"].menu(
                    node_view.node_type, node_view.id
                )
                if context_menu:
                    # noinspection PyTypeChecker
                    menu_actions: list[actions.NodeAction] = context_menu.actions()
                    for action in menu_actions:
                        action.node_id = node_view.id
                    prompted_data = "nodes", node_view.id

        if not context_menu:
            context_menu = context_menus["graph"]
            prompted_data = "graph", None

        if len(context_menu.actions()) > 0:
            if context_menu.isEnabled():
                self.contextMenuPrompted.emit(prompted_data[0], prompted_data[1])
                context_menu.exec_(event.globalPos())
            else:
                super().contextMenuEvent(event)
                return

        super().contextMenuEvent(event)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)

        polygon = self.mapToScene(self.viewport().rect())
        self._graph_label.setPos(polygon[0])

    def scale(self, sx, sy, pos: QPoint | None = None):
        """
        Scales the view by the given factors.

        :param sx: horizontal scale factor.
        :param sy: vertical scale factor.
        :param pos: position to scale from.
        """

        scale = [sx, sy]
        center = pos or self._scene_rect.center()
        width = self._scene_rect.width() / scale[0]
        height = self._scene_rect.height() / scale[1]
        self._scene_rect = QRectF(
            center.x() - (center.x() - self._scene_rect.left()) / scale[0],
            center.y() - (center.y() - self._scene_rect.top()) / scale[1],
            width,
            height,
        )
        self._update_scene()

    def force_update(self):
        """
        Forces the update of the node graph scene.
        """

        self._update_scene()

    def add_node(
        self, node: AbstractNodeView | NodeView, pos: tuple[float, float] | None = None
    ):
        """
        Adds a node view to the graph.

        :param node: node view to add.
        :param pos: position to add
        """

        pos = pos or (self._previous_mouse_pos.x(), self._previous_mouse_pos.y())
        node.pre_init(self, pos)
        self.scene().addItem(node)
        node.post_init(self, pos)

    def nodes(self) -> list[AbstractNodeView | NodeView]:
        """
        Returns all node views in the graph.

        :return: list of all node views.
        """

        return [i for i in self.scene().items() if isinstance(i, AbstractNodeView)]

    def selected_nodes(self) -> list[AbstractNodeView | NodeView]:
        """
        Returns all selected node views in the graph.

        :return: list of all selected node views.
        """

        return [
            i for i in self.scene().selectedItems() if isinstance(i, AbstractNodeView)
        ]

    def connectors(self) -> list[ConnectorView]:
        """
        Returns all connectors in the graph.

        :return: list of all connectors.
        """

        items_to_exclude = [self._live_connector, self._slicer]
        return [
            i
            for i in self.scene().items()
            if isinstance(i, ConnectorView) and i not in items_to_exclude
        ]

    def selected_connectors(self) -> list[ConnectorView]:
        """
        Returns all selected connectors in the graph.

        :return: list of all selected connectors.
        """

        return [i for i in self.scene().selectedItems() if isinstance(i, ConnectorView)]

    def selected_items(
        self,
    ) -> tuple[list[AbstractNodeView | NodeView], list[ConnectorView]]:
        """
        Returns all selected items in the graph.

        :return: list of all selected items.
        """

        selected_nodes: list[AbstractNodeView | NodeView] = []
        selected_connectors: list[ConnectorView] = []
        for item in self.scene().selectedItems():
            if isinstance(item, AbstractNodeView):
                selected_nodes.append(item)
            elif isinstance(item, ConnectorView):
                selected_connectors.append(item)

        return selected_nodes, selected_connectors

    def current_view_scale(self) -> float:
        """
        Returns the current scale of the node graph view.

        :return: current scale value.
        """

        # m22() is a method of the QTransform class that returns the element at the second row and second column of
        # a 3D transformation matrix. This element (m22) represents the vertical scaling factor.
        # In a transformation matrix:
        #
        # | m11       m12       m13  |
        # | m21       m22       m23  |
        # | m31 (dx)  m32 (dy)  m33  |
        #
        # m11:indicates how much the view is scaled along the horizontal axis.
        # m12: indicates how much the view is sheared in the vertical direction.
        # m13:indicates horizontal projection.
        # m21 indicates how much the view is sheared in the horizontal direction.
        # m22 indicates how much the view is scaled along the vertical axis.
        # m23:indicates vertical projection.
        # m31 (dx): indicates the horizontal translation.
        # m32 (dx): indicates the vertical translation.
        # m33: projection factor.

        return self.transform().m22()

    def zoom_value(self) -> float:
        """
        Returns the zoom level currently applied to this node graph view.

        :return: zoom level.
        """

        transform = self.transform()
        current_scale = (transform.m11(), transform.m22())
        return float(f"{current_scale[0] - 1.0:.2f}")

    def set_zoom_value(self, value: float = 0.0):
        """
        Sets the zoom level of the node graph view.

        :param value: zoom level value.
        """

        if value == 0.0:
            self.reset_zoom()
            return
        zoom = self.zoom_value()
        if zoom < 0.0:
            if (
                not uiconsts.NODE_GRAPH_MINIMUM_ZOOM
                <= zoom
                <= uiconsts.NODE_GRAPH_MAXIMUM_ZOOM
            ):
                return
        else:
            if (
                not uiconsts.NODE_GRAPH_MINIMUM_ZOOM
                <= zoom
                <= uiconsts.NODE_GRAPH_MAXIMUM_ZOOM
            ):
                return
        value = value - zoom
        self._set_zoom(value, 0.0)

    def reset_scale(self):
        """
        Resets the scale of the node graph view.
        """

        self.resetTransform()
        # self.resetMatrix()

    def reset_zoom(self, center: QPoint | QPointF | None = None):
        """
        Resets the zoom level of the node graph view.

        :param center: center position to zoom to.
        """

        self._scene_rect = QRectF(0, 0, self.size().width(), self.size().height())
        if center:
            self._scene_rect.translate(center - self._scene_rect.center())
        self._update_scene()

    def zoom_to_nodes(self, node_views: list[NodeView]):
        """
        Zooms to the given node views.

        :param node_views: node views to zoom to.
        """

        if not node_views:
            return

        self._scene_rect = self._combined_rect(node_views)
        self._update_scene()

        if self.zoom_value() > 0.1:
            self.reset_zoom(self._scene_rect.center())

    def move_nodes(
        self,
        nodes: Iterable[AbstractNodeView],
        position: Iterable[int, int] | None = None,
        offset: Iterable[int, int] | None = None,
    ):
        """
        Moves the given nodes to the given position.

        :param nodes: node views to move.
        :param position: position to move the nodes to.
        :param offset: offset to move the nodes by.
        """

        group = self.scene().createItemGroup(nodes)
        group_rect = group.boundingRect()
        if position:
            x, y = position
        else:
            pos = self.mapToScene(self._previous_mouse_pos)
            x = pos.x() - group_rect.center().x()
            y = pos.y() - group_rect.center().y()
        if offset:
            x += offset[0]
            y += offset[1]
        group.setPos(x, y)
        self.scene().destroyItemGroup(group)

    def center_selection(self, nodes: list[NodeView] | None = None):
        """
        Centers the view to the given nodes.

        :param nodes: node views to center the view to.
        """

        if not nodes:
            nodes = self.selected_nodes() or self.nodes()
            if not nodes:
                return

        rect = self._combined_rect(nodes)
        self._scene_rect.translate(rect.center() - self._scene_rect.center())
        self.setSceneRect(self._scene_rect)

    def lod_value_from_scale(self, scale: float | None = None) -> int:
        """
        Returns the level of detail value from the given scale.

        :param scale: scale value to get level of detail from.
        :return: level of detail index.
        """

        scale = scale if scale is not None else self.current_view_scale()
        scalar_percentage = scalar.range_percentage(
            self._zoom_range[0], self._zoom_range[1], scale
        )
        lod = int(round(scalar.lerp_value(self._num_lods, 1, scalar_percentage)))
        return lod

    def establish_connection(self, start_port_view: PortView, end_port_view: PortView):
        """
        Establishes a connection between two ports.

        :param start_port_view: start port view.
        :param end_port_view: end port view.
        """

        connector = ConnectorView()
        self.scene().addItem(connector)
        connector.set_connections(start_port_view, end_port_view)
        connector.draw_path(connector.input_port, connector.output_port)
        if start_port_view.node_view.selected or end_port_view.node_view.selected:
            connector.highlight()
        if not start_port_view.node_view.visible or not end_port_view.node_view.visible:
            connector.hide()

    def tab_search_set_nodes(self, graph: NodeGraph):
        """
        Sets the nodes for the tab search widget.

        :param graph: node graph.
        """

        data_type_filter: DataType | None = None
        if self._live_connector.isVisible():
            data_type_filter = (
                self._live_connector.output_port.data_type
                if self._live_connector.output_port
                else self._live_connector.input_port.data_type
                if self._live_connector.input_port
                else None
            )

        self._search_widget.populate(
            graph, data_type_filter=data_type_filter, functions_first=True
        )

    def tab_search_toggle(self):
        """
        Toggles the tab search widget.
        """

        state = self._search_widget.isVisible()
        if not state:
            self._search_widget.setVisible(state)
            self.setFocus()
            return

        pos = self._previous_mouse_pos
        rect = self._search_widget.rect()
        new_pos = QPoint(
            int(pos.x() - rect.width() / 2), int(pos.y() - rect.height() / 2)
        )
        self._search_widget.move(new_pos)
        self._search_widget.setVisible(state)
        self._search_widget.setFocus()

        rect = self.mapToScene(rect).boundingRect()
        self.scene().update(rect)

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

        parent = parent or self
        self._clear_key_state()
        dialogs.message_dialog(
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

        parent = parent or self
        self._clear_key_state()
        return dialogs.question_dialog(
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

        parent = parent or self
        self._clear_key_state()
        extension = f"*{extension}" if extension else ""
        extension_filter = ";;".join(
            [f"Node Graph ({extension}*json)", "All Files (*)"]
        )
        file_dialog = dialogs.get_open_file_name(
            title="Open Session",
            start_directory=start_directory,
            extension_filter=extension_filter,
            parent=parent,
        )
        file = file_dialog[0] or None

        return file

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

        parent = parent or self
        self._clear_key_state()
        extension_label = f"*{extension}" if extension else ""
        extension_type = f".{extension}" if extension else ".json"
        extension_map = {
            f"Node Graph ({extension_label}*json)": extension_type,
            "All Files (*)": "",
        }
        extension_filter = ";;".join(extension_map.keys())
        file_dialog = dialogs.get_save_file_name(
            title="Save Session",
            start_directory=start_directory,
            extension_filter=extension_filter,
            parent=parent,
        )
        file = file_dialog[0] or None
        if not file:
            return None
        ext = extension_map[file_dialog[1]]
        if ext and not file.endswith(ext):
            file += ext

        return file

    def _setup_ui(self):
        """
        Internal function that set up the UI of the view.
        """

        self.setRenderHint(QPainter.Antialiasing, True)
        # Follow render hints are expensive and should be used only when needed.
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        self.setAcceptDrops(True)

    def _setup_context_menus(self):
        """
        Internal function that sets up context menus.
        """

        # Disable "node" context menu by default.
        self._context_node_menu.setEnabled(False)

        self._context_menu_bar.addMenu(self._context_graph_menu)
        self._context_menu_bar.addMenu(self._context_node_menu)

        if self._undo_action and self._redo_action:
            self._undo_action.setShortcuts(QKeySequence.Undo)
            self._redo_action.setShortcuts(QKeySequence.Redo)
            self._undo_action.setShortcutVisibleInContextMenu(True)
            self._redo_action.setShortcutVisibleInContextMenu(True)
            self._context_graph_menu.addAction(self._undo_action)
            self._context_graph_menu.addAction(self._redo_action)
            self._context_node_menu.addSeparator()

    def _combined_rect(self, nodes: list[NodeView]) -> QRectF:
        """
        Internal function that returns the combined bounding rect of given nodes.

        :param nodes: list of node views.
        :return: combined bounding rect.
        """

        group = self.scene().createItemGroup(nodes)
        rect = group.boundingRect()
        self.scene().destroyItemGroup(group)

        return rect

    def _update_scene(self):
        """
        Internal function that updates the scene.
        """

        self.setSceneRect(self._scene_rect)
        self.fitInView(self._scene_rect, Qt.KeepAspectRatio)

    def _set_pan(self, pos_x: float, pos_y: float):
        """
        Internal function that sets the pan of the node graph view.

        :param pos_x: x position.
        :param pos_y: y position.
        """

        self._scene_rect.adjust(pos_x, pos_y, pos_x, pos_y)
        self._update_scene()

    def _set_zoom(
        self, value: float, sensitivity: float | None = None, pos: QPointF | None = None
    ):
        """
        Internal function that sets the zoom of the node graph view.

        :param value: zoom factor.
        :param sensitivity: optional zoom sensitivity.
        :param pos: optional origin position for the zoom to be applied from.
        """

        pos = self.mapToScene(pos.toPoint()) if pos else None
        if sensitivity is None:
            scale = 1.001**value
            self.scale(scale, scale, pos)
            return

        if value == 0.0:
            return

        scale = (0.9 + sensitivity) if value < 0.0 else (1.1 - sensitivity)
        zoom = self.zoom_value()
        if uiconsts.NODE_GRAPH_MINIMUM_ZOOM >= zoom:
            if scale == 0.9:
                return
        if uiconsts.NODE_GRAPH_MAXIMUM_ZOOM <= zoom:
            if scale == 1.1:
                return
        self.scale(scale, scale, pos)

    def _items_near(
        self,
        pos: QPointF,
        item_type: Type[QGraphicsItem] | None = None,
        width: int = 20,
        height: int = 20,
    ) -> list[QGraphicsItem]:
        """
        Internal function that returns all items near given position and within given area.


        :param pos: scene position.
        :param item_type: optional filter type.
        :param width: width area.
        :param height: height area.
        :return: list of items near given position.
        """

        found_items: list[QGraphicsItem] = []
        items_to_exclude = [self._live_connector, self._slicer]

        x, y = pos.x() - width, pos.y() - height
        rect = QRectF(x, y, width, height)

        for item in self.scene().items(rect):
            if item in items_to_exclude:
                continue
            if item_type and not isinstance(item, item_type):
                continue
            found_items.append(item)

        return found_items

    def _start_live_connection(self, selected_port: PortView):
        """
        Internal function that starts a live connection.

        :param selected_port: port to start the live connection from.
        """

        if not selected_port:
            return

        self._start_port = selected_port

        if self._start_port.port_type == consts.PortType.Input.value:
            self._live_connector.input_port = self._start_port
        elif self._start_port.port_type == consts.PortType.Output.value:
            self._live_connector.output_port = self._start_port
        self._live_connector.color = self._start_port.color
        self._live_connector.setVisible(True)
        self._live_connector.draw_index_pointer(
            selected_port, self.mapToScene(self._origin_mouse_pos)
        )

    def _apply_live_connection(self, event: QGraphicsSceneMouseEvent):
        """
        Internal function that applies a live connection.

        :param event:  mouse event.
        """

        if not self._live_connector.isVisible():
            return

        self._start_port.hovered = False

        end_port: PortView | None = None
        for item in self.scene().items(event.scenePos()):
            if isinstance(item, PortView):
                end_port = item
                break

        connected: list[tuple[PortView, PortView]] = []
        disconnected: list[tuple[PortView, PortView]] = []

        if end_port is None:
            self._end_live_connection()
            return
        else:
            if self._start_port is end_port:
                return

        same_node_condition = end_port.node_view == self._start_port.node_view
        if not self.acyclic:
            same_node_condition = False

        accept_connection = True
        reject_connection = False

        restore_connection = any(
            [
                end_port.locked,
                end_port.port_type == self._start_port.port_type,
                same_node_condition,
                end_port == self._start_port,
                self._detached_port == end_port,
            ]
        )
        if restore_connection:
            self._end_live_connection()
            return

        if not end_port.multi_connection and end_port.connected_ports:
            detached_end = end_port.connected_ports[0]
            disconnected.append((end_port, detached_end))

        if self._detached_port:
            disconnected.append((self._start_port, self._detached_port))

        connected.append((self._start_port, end_port))

        self.connectionsChanged.emit(disconnected, connected)

        self._detached_port = None
        self._end_live_connection()

    def _end_live_connection(self):
        """
        Internal function that ends a live connection.
        """

        self._live_connector.reset_path()
        self._live_connector.setVisible(False)
        self._live_connector.shift_selected = False
        self._start_port = None

    def _connectors_ready_to_slice(self, path: QPainterPath):
        """
        Internal function that prepares connectors to be sliced.

        :param path: path to slice connectors.
        """

        visible_slicer: Slicer | FreehandSlicer | None = None
        if self._slicer.isVisible():
            visible_slicer = self._slicer
        elif self._freehand_slicer.isVisible():
            visible_slicer = self._freehand_slicer
        if visible_slicer is None:
            return

        over_connectors = visible_slicer.intersected_connectors()
        if not over_connectors:
            for over_connector in self._over_slicer_connectors:
                over_connector.ready_to_slice = False
            self._over_slicer_connectors.clear()
            return

        for over_connector in over_connectors:
            over_connector.ready_to_slice = True
            if over_connector not in self._over_slicer_connectors:
                self._over_slicer_connectors.append(over_connector)

        connectors_to_clean: list[ConnectorView] = []
        for over_connector in self._over_slicer_connectors:
            if over_connector not in over_connectors:
                connectors_to_clean.append(over_connector)
        for over_connector in connectors_to_clean:
            over_connector.ready_to_slice = False

    def _slice_connectors(self, path: QPainterPath):
        """
        Internal function that slices connectors.

        :param path: path to slice connectors.
        """

        port_views: list[tuple[PortView, PortView]] = []

        for item in self.scene().items(path):
            if isinstance(item, ConnectorView) and item != self._live_connector:
                if any([item.input_port.locked, item.output_port.locked]):
                    continue
                port_views.append((item.input_port, item.output_port))

        self.connectionSliced.emit(port_views)

    def _slice_freehand_connectors(self, connector_views: list[ConnectorView]):
        """
        Internal function that slices freehand connectors.

        :param connector_views: connectors to slice.
        """

        port_views: list[tuple[PortView, PortView]] = []

        for item in connector_views:
            if item != self._live_connector:
                if any([item.input_port.locked, item.output_port.locked]):
                    continue
                port_views.append((item.input_port, item.output_port))

        self.connectionSliced.emit(port_views)

    def _clear_key_state(self):
        """
        Internal function that resets the control, shift and alt key states.
        """

        self._ctrl_state = False
        self._shift_state = False
        self._alt_state = False

    def _on_search_submitted(self, node_type: str, func_signature: str, func_type: str):
        """
        Internal callback function that is called when a node search is submitted.

        :param node_type: node type to search.
        :param func_signature: function signature.
        :param func_type: function type.
        """

        pos = self.mapToScene(self._previous_mouse_pos)
        self.searchTriggered.emit(
            node_type, func_signature, func_type, (pos.x(), pos.y())
        )


class NodeGraphViewTitleLabel(QGraphicsTextItem):
    """
    Class that defines the title label for the node graph.
    """

    class Signals(QObject):
        """
        Signals class that defines all signals for the title
        """

        textChanged = Signal(str)

    def __init__(self):
        super().__init__()

        self.signals = NodeGraphViewTitleLabel.Signals()

        self.setFlags(QGraphicsTextItem.ItemIgnoresTransformations)
        self.setDefaultTextColor(QColor(255, 255, 255, 50))
        self.setFont(QFont("Impact", 20, 1))
        self.setZValue(5)

    def setPlainText(self, text: str):
        """
        Sets the plain text of the title label.

        :param text: text to set.
        """

        super().setPlainText(text)

        self.signals.textChanged.emit(self.toPlainText())
