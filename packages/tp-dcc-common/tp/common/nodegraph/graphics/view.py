from __future__ import annotations

import enum
import typing
from typing import Iterable

from overrides import override

from tp.core import log
from tp.common.math import scalar
from tp.common.qt import api as qt
from tp.common.python import helpers
from tp.common.nodegraph.core import consts, edgedrag
from tp.common.nodegraph.graphics import node, socket, edge, slicer

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.graphics.scene import GraphicsScene

logger = log.rigLogger


class GraphicsView(qt.QGraphicsView):

    EDGE_DRAG_START_THRESHOLD = 50
    HIGH_QUALITY_ZOOM = 4

    class EdgeMode(enum.IntEnum):
        Noop = 1
        Drag = 2
        Cut = 3
        CutFreehand = 4

    nodeDoubleClicked = qt.Signal(str)
    nodeBackdropUpdated = qt.Signal(object, str, dict)

    def __init__(self, graphics_scene: GraphicsScene, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._graphics_scene = graphics_scene

        self._num_lods = 5
        self._zoom_range = (consts.GRAPH_VIEWER_MINIMUM_ZOOM, consts.GRAPH_VIEWER_MAXIMUM_ZOOM)
        self._scene_rect = qt.QRectF(0, 0, self.size().width(), self.size().height())

        self._last_left_mouse_click_pos = qt.QPointF()
        self._last_scene_mouse_pos = qt.QPointF()
        self._left_mouse_button_state = False
        self._right_mouse_button_state = False
        self._middle_mouse_button_state = False
        self._alt_state = False
        self._ctrl_state = False
        self._shift_state = False
        self._origin_mouse_pos = qt.QPointF(0.0, 0.0)                   # origin position when user click on the scene.
        self._mouse_pos = qt.QPointF(0.0, 0.0)                          # current mouse position.
        # self._prev_mouse_pos = qt.QPoint(self.width(), self.height())   # previous click operation mouse position.
        self._prev_mouse_pos = qt.QPoint(int(self.width() / 2), int(self.height() / 2))

        self._is_view_dragging = False
        self._rubberband_dragging_rect = False

        self._edge_mode = GraphicsView.EdgeMode.Noop
        self._dragging = edgedrag.EdgeDrag(self)

        self._setup_ui()
        self.setScene(self._graphics_scene)

        self._graph_label = GraphTitleLabel()
        self._graph_label.setPlainText('BUILDER')

        self._slicer = slicer.Slicer()
        self._freehand_slicer = slicer.FreehandSlicer()
        self._slicer.setVisible(False)
        self._freehand_slicer.setVisible(False)
        self._over_slicer_edges: list[edge.GraphicsEdge] = []

        self._graphics_scene.addItem(self._graph_label)
        self._graphics_scene.addItem(self._slicer)
        self._graphics_scene.addItem(self._freehand_slicer)
        self._update_scene()
        self._update_edge_width()
        self._update_render_hints()

        self._last_size = self.size()

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}() object at {hex(id(self))}>'

    @property
    def graphics_scene(self) -> GraphicsScene:
        return self._graphics_scene

    @property
    def is_view_dragging(self) -> bool:
        return self._is_view_dragging

    @property
    def last_scene_mouse_pos(self) -> qt.QPointF:
        return self._last_scene_mouse_pos

    @property
    def rubberband_dragging_rect(self) -> bool:
        return self._rubberband_dragging_rect

    @property
    def edge_mode(self) -> GraphicsView.EdgeMode:
        return self._edge_mode

    @property
    def dragging(self) -> edgedrag.EdgeDrag:
        return self._dragging

    @override
    def resizeEvent(self, event: qt.QResizeEvent) -> None:
        width = self.size().width()
        height = self.size().height()

        # Make sure that width and height are not 0.
        # If that's the scale we automatically resize view to last valid size.
        if 0 in [width, height]:
            self.resize(self._last_size)

        delta = max(width / self._last_size.width(), height / self._last_size.height())
        self._set_zoom(delta, sensitivity=None)
        self._last_size = self.size()

        super().resizeEvent(event)

    @override
    def mousePressEvent(self, event: qt.QMouseEvent) -> None:

        def _middle_mouse_press():
            item = self.itemAt(event.pos())
            if event.modifiers() & qt.Qt.ControlModifier:
                self.log_scene_objects(item)

        def _left_mouse_press():
            item = self.itemAt(event.pos())
            self._last_left_mouse_click_pos = self.mapToScene(event.pos())

            # Handle socket click
            if isinstance(item, socket.GraphicsSocket):
                if self._edge_mode == GraphicsView.EdgeMode.Noop:
                    self._edge_mode = GraphicsView.EdgeMode.Drag
                    self._dragging.start_edge_drag(item)
                    return
            if self._edge_mode == GraphicsView.EdgeMode.Drag:
                result = self._dragging.end_edge_drag(item)
                if result:
                    return
            if not item:
                if event.modifiers():
                    print('1', self._ctrl_state, self._shift_state)
                    run_slicer = False
                    if self._ctrl_state and not self._shift_state:
                        print('2')
                        self._edge_mode = GraphicsView.EdgeMode.Cut
                        map_pos = self.mapToScene(event.pos())
                        self._slicer.draw_path(map_pos, map_pos)
                        self._slicer.setVisible(True)
                        run_slicer = True
                    elif self._ctrl_state and self._shift_state:
                        print('3')
                        self._edge_mode = GraphicsView.EdgeMode.CutFreehand
                        self._freehand_slicer.setVisible(True)
                        run_slicer = True
                    if run_slicer:
                        fake_event = qt.QMouseEvent(
                            qt.QEvent.MouseButtonRelease, event.localPos(), event.screenPos(),
                            qt.Qt.LeftButton, qt.Qt.NoButton, event.modifiers())
                        super(GraphicsView, self).mouseReleaseEvent(fake_event)
                        return
                else:
                    self._rubberband_dragging_rect = True

            super(GraphicsView, self).mousePressEvent(event)

        def _right_mouse_press():
            release_event = qt.QMouseEvent(
                qt.QEvent.MouseButtonRelease, event.localPos(), event.screenPos(),
                qt.Qt.LeftButton, qt.Qt.NoButton, event.modifiers())
            super(GraphicsView, self).mouseReleaseEvent(release_event)
            self.setDragMode(qt.QGraphicsView.ScrollHandDrag)
            self.setInteractive(False)
            fake_event = qt.QMouseEvent(
                event.type(), event.localPos(), event.screenPos(),
                qt.Qt.LeftButton, event.buttons() | qt.Qt.LeftButton, event.modifiers())
            super(GraphicsView, self).mousePressEvent(fake_event)

        if event.button() == qt.Qt.LeftButton:
            self._left_mouse_button_state = True
        if event.button() == qt.Qt.RightButton:
            self._right_mouse_button_state = True
        if event.button() == qt.Qt.MiddleButton:
            self._middle_mouse_button_state = True

        self._origin_mouse_pos = event.pos()
        self._prev_mouse_pos = event.pos()

        if event.button() == qt.Qt.MiddleButton:
            _middle_mouse_press()
        elif event.button() == qt.Qt.LeftButton:
            _left_mouse_press()
        elif event.button() == qt.Qt.RightButton:
            _right_mouse_press()
        else:
            super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: qt.QMouseEvent) -> None:

        scene_pos = self.mapToScene(event.pos())
        self._is_view_dragging = not self.isInteractive()
        try:
            if self._edge_mode == GraphicsView.EdgeMode.Drag:
                pos = scene_pos
                pos.setX(pos.x() - 1.0)
                self._dragging.update_positions(int(pos.x()), int(pos.y()))
            if self._edge_mode == GraphicsView.EdgeMode.Cut and self._slicer is not None:
                p1 = self._slicer.path().pointAtPercent(0)
                p2 = self.mapToScene(self._prev_mouse_pos)
                self._slicer.draw_path(p1, p2)
                self._slicer.show()
                self._edges_ready_to_slice(self._slicer.path())
            elif self._edge_mode == GraphicsView.EdgeMode.CutFreehand and self._freehand_slicer is not None:
                self._freehand_slicer.add_point(scene_pos)
                self._edges_ready_to_slice(self._freehand_slicer.path())
            else:
                if self._is_view_dragging:
                    if self._middle_mouse_button_state and self._alt_state:
                        pass
                    elif self._right_mouse_button_state or (self._left_mouse_button_state and self._alt_state):
                        previous_pos = self.mapToScene(self._prev_mouse_pos)
                        delta = previous_pos - scene_pos
                        self._set_pan(delta.x(), delta.y())

        except Exception:
            logger.exception('mouseMoveEvent exception', exc_info=True)

        self._last_scene_mouse_pos = scene_pos
        self._prev_mouse_pos = event.pos()

        super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: qt.QMouseEvent) -> None:

        def _middle_mouse_release():
            pass

        def _left_mouse_release():

            def _check_left_mouse_button_release_delta() -> bool:
                """
                Internal function that measures whether left mouse button position is greater than distance threshold.

                :return: True if distance between clicked positions is greater than threshold; False otherwise.
                :rtype: bool
                """

                new_lmb_release_scene_pos = self.mapToScene(event.pos())
                release_delta = new_lmb_release_scene_pos - self._last_left_mouse_click_pos
                return release_delta.x() ** 2 + release_delta.y() ** 2 > GraphicsView.EDGE_DRAG_START_THRESHOLD ** 2

            item = self.itemAt(event.pos())
            try:
                if self._edge_mode == GraphicsView.EdgeMode.Drag:
                    if _check_left_mouse_button_release_delta():
                        result = self._dragging.end_edge_drag(item)
                        if result:
                            return
                if self._edge_mode == GraphicsView.EdgeMode.Cut:
                    cut_result = self._slicer.cut()
                    if cut_result:
                        self._graphics_scene.graph.history.store_history('Edges Cut', set_modified=True)
                    self._slicer.draw_path(qt.QPointF(0.0, 0.0), qt.QPointF(0.0, 0.0))
                    self._slicer.setVisible(False)
                    self._edge_mode = GraphicsView.EdgeMode.Noop
                    return
                if self._edge_mode == GraphicsView.EdgeMode.CutFreehand:
                    cut_result = self._freehand_slicer.cut()
                    if cut_result:
                        self._graphics_scene.graph.history.store_history('Edges Cut', set_modified=True)
                    self._freehand_slicer.reset()
                    self._freehand_slicer.setVisible(False)
                    self._edge_mode = GraphicsView.EdgeMode.Noop
                    return
                if self._rubberband_dragging_rect:
                    self._rubberband_dragging_rect = False
                    self._graphics_scene.graph._on_selection_changed()
                    return
            except Exception:
                logger.exception('Left mouse release exception', exc_info=True)
            super(GraphicsView, self).mouseReleaseEvent(event)

        def _right_mouse_release():
            fake_event = qt.QMouseEvent(
                event.type(), event.localPos(), event.screenPos(),
                qt.Qt.LeftButton, event.buttons() & ~qt.Qt.LeftButton, event.modifiers())
            super(GraphicsView, self).mouseReleaseEvent(fake_event)
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)
            self.setInteractive(True)

        if event.button() == qt.Qt.LeftButton:
            self._left_mouse_button_state = False
        if event.button() == qt.Qt.RightButton:
            self._right_mouse_button_state = False
        if event.button() == qt.Qt.MiddleButton:
            self._middle_mouse_button_state = False

        if event.button() == qt.Qt.MiddleButton:
            _middle_mouse_release()
        elif event.button() == qt.Qt.LeftButton:
            _left_mouse_release()
        elif event.button() == qt.Qt.RightButton:
            _right_mouse_release()
        else:
            super(GraphicsView, self).mouseReleaseEvent(event)

    @override
    def keyPressEvent(self, event):
        """
        Overrides base keyPressEvent function to handle graph viewer behaviour when user presses a keyboard button.

        :param QEvent event: Qt keyboard press event.
        """

        modifiers = event.modifiers()

        self._alt_state = modifiers == qt.Qt.AltModifier
        self._ctrl_state = modifiers == qt.Qt.ControlModifier
        self._shift_state = modifiers == qt.Qt.ShiftModifier

        if modifiers == (qt.Qt.AltModifier | qt.Qt.ShiftModifier):
            self._alt_state = True
            self._shift_state = True
        if modifiers == (qt.Qt.ControlModifier | qt.Qt.ShiftModifier):
            self._ctrl_state = True
            self._shift_state = True
        if modifiers == (qt.Qt.ControlModifier | qt.Qt.AltModifier):
            self._ctrl_state = True
            self._alt_state = True

        super().keyPressEvent(event)

    @override
    def keyReleaseEvent(self, event):
        """
        Overrides base keyReleaseEvent function to handle graph viewer behaviour when user releases a keyboard button.

        :param QEvent event: Qt keyboard release event.
        """

        modifiers = event.modifiers()

        self._alt_state = modifiers == qt.Qt.AltModifier
        self._ctrl_state = modifiers == qt.Qt.ControlModifier
        self._shift_state = modifiers == qt.Qt.ShiftModifier

        if modifiers == (qt.Qt.AltModifier | qt.Qt.ShiftModifier):
            self._alt_state = False
            self._shift_state = False
        if modifiers == (qt.Qt.ControlModifier | qt.Qt.ShiftModifier):
            self._ctrl_state = False
            self._shift_state = False
        if modifiers == (qt.Qt.ControlModifier | qt.Qt.AltModifier):
            self._ctrl_state = False
            self._alt_state = False

        super().keyReleaseEvent(event)

    @override
    def wheelEvent(self, event: qt.QWheelEvent) -> None:
        try:
            delta = event.delta()
        except AttributeError:
            delta = event.angleDelta().y()
            if delta == 0:
                delta = event.angleDelta().x()
        self._set_zoom(delta, pos=event.pos())
        super().wheelEvent(event)

    @override
    def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
        self._graphics_scene.graph.itemDragEntered.emit(event)

    @override
    def dropEvent(self, event: qt.QDropEvent) -> None:
        self._graphics_scene.graph.itemDropped.emit(event)

    @override(check_signature=False)
    def scale(self, scale_x: float, scale_y: float, pos: qt.QPoint | None = None):
        """
        Overrides base scale function to scale view taking into account current scene rectangle.

        :param float scale_x: scale in X coordinate.
        :param float scale_y: scale in Y coordinate.
        :param QPoint or None pos: position from where the scaling is applied.
        :return:
        """

        scale = [scale_x, scale_y]
        center = pos or self._scene_rect.center()
        width = self._scene_rect.width() / scale[0]
        height = self._scene_rect.height() / scale[1]
        self._scene_rect = qt.QRectF(
            center.x() - (center.x() - self._scene_rect.left()) / scale[0],
            center.y() - (center.y() - self._scene_rect.top()) / scale[1], width, height)
        self._update_scene()

    @override
    def drawBackground(self, painter: qt.QPainter, rect: qt.QRectF) -> None:
        super().drawBackground(painter, rect)
        polygon = self.mapToScene(self.viewport().rect())
        self._graph_label.setPos(polygon[0])

    def add_node(self, node_view: node.BaseGraphicsNode, pos: Iterable[float, float] | None = None):
        """
        Adds node view into the scene.

        :param BaseGraphicsNode node_view: node view to add.
        :param Iterable[float, float] pos: optional position to place the item within the viewer.
        """

        pos = pos or (self._prev_mouse_pos.x(), self._prev_mouse_pos.y())
        node_view.pre_init(self, pos)
        self.scene().addItem(node_view)
        node_view.post_init(self, pos)

    def zoom_value(self) -> float:
        """
        Returns the zoom level currently applied to this graph view.

        :return: graph view zoom level.
        :rtype: float
        """

        transform = self.transform()
        current_scale = (transform.m11(), transform.m22())
        return float('{:0.2f}'.format(current_scale[0] - 1.0))

    def current_view_scale(self) -> float:
        """
        Returns current transform scale of the graph view.

        :return: transform scale.
        :rtype: float
        """

        return self.transform().m22()

    def reset_scale(self):
        """
        Resets current transform scale of the graph view.
        """

        self.resetMatrix()

    def lod_value_from_scale(self, scale: float | None = None):
        """
        Returns the current view LOD value taking into account view scale.

        :param scale: float or None, scale to get LOD of. If not given, current view scale will be used instead.
        :return: int, lod index
        """

        scale = scale if scale is not None else self.current_view_scale()
        scale_percentage = scalar.range_percentage(self._zoom_range[0], self._zoom_range[1], scale)
        lod = scalar.lerp(self._num_lods, 1, scale_percentage)
        return int(round(lod))

    def show_details(self) -> bool:
        """
        Returns whether high quality details should be rendered.

        :return: True if high quality details should be rendered; False otherwise.
        :rtype: bool
        """

        return self.lod_value_from_scale() < 3

    def log_scene_objects(self, item: qt.QGraphicsItem):
        """
        Log data of given item.

        :param qt.QGraphicsItem item: item to log data of.
        """

        if isinstance(item, socket.GraphicsSocket):
            logger.info(item.socket)
            logger.info('  Data Class: {0}'.format(item.socket.data_class))
            logger.info('  Value: {0}'.format(item.socket.value()))
            logger.info('  Connected edge: {0}'.format(item.socket.edges))
        elif isinstance(item, node.GraphicsNode):
            logger.info(item.node)
            logger.info('-- Inputs')
            for input_socket in item.node.inputs:
                logger.info(input_socket)
            logger.info('-- Required Inputs')
            for input_socket in item.node.required_inputs:
                logger.info(input_socket)
            logger.info('-- Outputs')
            for output_socket in item.node.outputs:
                logger.info(output_socket)
        elif isinstance(item, edge.GraphicsEdge):
            logger.info(item.edge)
            logger.info('  Start: {0}, End:{1}'.format(item.edge.start_socket, item.edge.end_socket))

        if not item:
            logger.info('SCENE:')
            logger.info('VARS: {0}'.format(self._graphics_scene.scene.vars._vars))
            logger.info('  Nodes:')
            for scene_node in self._graphics_scene.scene.nodes:
                logger.info('    {0}'.format(scene_node))
            logger.info('  Edges:')
            for scene_edge in self._graphics_scene.scene.edges:
                logger.info('    {0}'.format(scene_edge))

    def reset_edge_mode(self):
        """
        Resets edge mode.
        """

        self._edge_mode = GraphicsView.EdgeMode.Noop

    def all_nodes(self, filtered_classes: list[type] | None = None):
        """
        Returns all node views in current graph. Allows the filtering of specific node classes.

        :param list[type] or None filtered_classes: If given, only nodes with given classes will be taken into account
        :return: all node views within the scene.
        :rtype: list[node.BaseGraphicsNode]
        """

        all_nodes: list[node.BaseGraphicsNode] = []
        current_scene = self.scene()
        if not current_scene:
            return all_nodes

        filtered_classes = helpers.force_list(filtered_classes or [node.BaseGraphicsNode])
        if node.BaseGraphicsNode not in filtered_classes:
            filtered_classes.append(node.BaseGraphicsNode)
        filtered_classes = helpers.force_tuple(filtered_classes)

        for item_view in current_scene.items():
            if not item_view or not isinstance(item_view, filtered_classes):
                continue
            all_nodes.append(item_view)

        return all_nodes

    def selected_nodes(self, filtered_classes: list[type] | None = None) -> list[node.BaseGraphicsNode]:
        """
        Returns current selected views. Allows the filtering of specific node classes.

        :param list[type] or None filtered_classes: list of node classes we want to filter by.
        :return: list of selected node views.
        :rtype: list[node.BaseGraphicsNode]
        """

        selected_nodes: list[node.BaseGraphicsNode] = []

        # if no scene is available, no nodes can be selected
        current_scene = self.scene()
        if not current_scene:
            return selected_nodes

        filtered_classes = helpers.force_list(filtered_classes or [node.BaseGraphicsNode])
        if node.BaseGraphicsNode not in filtered_classes:
            filtered_classes.append(node.BaseGraphicsNode)
        filtered_classes = helpers.force_tuple(filtered_classes)

        for item in current_scene.selectedItems():
            if not item or not isinstance(item, filtered_classes):
                continue
            selected_nodes.append(item)

        return selected_nodes

    def _setup_ui(self):
        """
        Internal function that setup graphics view.
        """

        self.setRenderHint(qt.QPainter.Antialiasing, True)
        self.setRenderHint(qt.QPainter.TextAntialiasing, True)  # NOTE: this is expensive
        self.setRenderHint(qt.QPainter.HighQualityAntialiasing, True)  # NOTE: this is expensive
        self.setRenderHint(qt.QPainter.SmoothPixmapTransform, True)  # NOTE: this is expensive
        self.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(qt.QGraphicsView.FullViewportUpdate)
        # self.setCacheMode(qt.QGraphicsView.CacheBackground)
        self.setOptimizationFlag(qt.QGraphicsView.DontAdjustForAntialiasing)
        self.setTransformationAnchor(qt.QGraphicsView.AnchorUnderMouse)
        self.setDragMode(qt.QGraphicsView.RubberBandDrag)
        self.setAttribute(qt.Qt.WA_AlwaysShowToolTips)
        self.setAcceptDrops(True)

    def _set_zoom(self, value: float, sensitivity: float | None = 0.0, pos: qt.QPoint | None = None):
        """
        Internal function that sets the zoom of the graph view.

        :param float value: zoom value.
        :param float or None sensitivity: zoom sensitivity value.
        :param qt.QPointF pos: position from where the zoom is applied.
        """

        # if zoom position is given, we make sure to convert to scene coordinates
        if pos:
            pos = self.mapToScene(pos)

        # if no sensitivity given we just scale the view
        if sensitivity is None:
            scale = 1.001 ** value
            self.scale(scale, scale, pos)
            return

        # if not zoom value given we just skip zoom operation
        if value == 0.0:
            return

        # scale view taking into account the minimum and maximum levels
        scale = (0.9 + sensitivity) if value < 0.0 else (1.1 - sensitivity)
        zoom = self.zoom_value()

        if self._zoom_range[0] >= zoom:
            if scale == 0.9:
                return
        if self._zoom_range[1] <= zoom:
            if scale == 1.1:
                return

        self.scale(scale, scale, pos)
        self._update_edge_width()
        self._update_render_hints()

    def _set_pan(self, pos_x: float, pos_y: float):
        """
        Internal function that sets the panning of the graph view
        :param float pos_x: pan X coordinate position.
        :param float pos_y: pan Y coordinate position.
        :return:
        """

        # speed = self._scene_rect.width() * 0.0015
        # x = -pos_x * speed
        # y = -pos_y * speed
        # self._scene_rect.adjust(x, y, x, y)

        self._scene_rect.adjust(pos_x, pos_y, pos_x, pos_y)
        self._update_scene()

    def _update_scene(self):
        """
        Internal function that forces redraw of the scene.
        """

        self.setSceneRect(self._scene_rect)
        self.fitInView(self._scene_rect, qt.Qt.KeepAspectRatio)

    def _update_edge_width(self):
        """
        Internal functoin that updates edge widget.
        """

        zoom = self.zoom_value()
        edge.GraphicsEdge.WIDTH = ((zoom - self._zoom_range[0]) / (self._zoom_range[1] - self._zoom_range[0])) * \
            (edge.GraphicsEdge.MIN_WIDTH - edge.GraphicsEdge.MAX_WIDTH) + edge.GraphicsEdge.MAX_WIDTH

    def _update_render_hints(self):
        """
        Internal function that updates render hints.
        """

        zoom = self.zoom_value()
        if zoom > self.HIGH_QUALITY_ZOOM:
            self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.HighQualityAntialiasing | qt.QPainter.TextAntialiasing | qt.QPainter.SmoothPixmapTransform)
        else:
            self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.TextAntialiasing | qt.QPainter.SmoothPixmapTransform)

    def _edges_ready_to_slice(self, slicer_path: qt.QPainterPath):
        """
        Internal function that updates edges painter based on whether an edge it's ready to be sliced or not.

        :param QPainterPath slicer_path: slicer path.
        """

        visible_slicer = None
        if self._slicer.isVisible():
            visible_slicer = self._slicer
        elif self._freehand_slicer.isVisible():
            visible_slicer = self._freehand_slicer
        if visible_slicer is None:
            return

        over_edges = visible_slicer.intersected_edges()
        if not over_edges:
            for over_edge in self._over_slicer_edges:
                over_edge.ready_to_slice = False
            self._over_slicer_edges.clear()
            return

        for over_edge in over_edges:
            over_edge.ready_to_slice = True
            if over_edge not in self._over_slicer_edges:
                self._over_slicer_edges.append(over_edge)
        edges_to_clean = []
        for over_edge in self._over_slicer_edges:
            if over_edge not in over_edges:
                edges_to_clean.append(over_edge)
        for over_edge in edges_to_clean:
            over_edge.ready_to_slice = False


class GraphTitleLabel(qt.QGraphicsTextItem):

    class Signals(qt.QObject):
        textChanged = qt.Signal(str)

    def __init__(self):
        super(GraphTitleLabel, self).__init__()

        self.signals = GraphTitleLabel.Signals()

        self.setFlags(qt.QGraphicsTextItem.ItemIgnoresTransformations)
        self.setDefaultTextColor(qt.QColor(255, 255, 255, 50))
        self.setFont(qt.QFont('Impact', 20, 1))
        self.setZValue(5)

    @override
    def setPlainText(self, text: str) -> None:
        super().setPlainText(text)
        self.signals.textChanged.emit(self.toPlainText())
