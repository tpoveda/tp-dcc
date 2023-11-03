from __future__ import annotations

import enum
import typing

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.tools.rig.noddle.builder.graph.core import edgedrag
from tp.tools.rig.noddle.builder.graph.graphics import node, socket, edge

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.scene import Scene
    from tp.tools.rig.noddle.builder.graph.graphics.scene import GraphicsScene

logger = log.rigLogger


class GraphicsView(qt.QGraphicsView):

    EDGE_DRAG_START_THRESHOLD = 50
    HIGH_QUALITY_ZOOM = 4

    class EdgeMode(enum.IntEnum):
        Noop = 1
        Drag = 2
        Cut = 3

    def __init__(self, graphics_scene: GraphicsScene, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._graphics_scene = graphics_scene
        self._is_view_dragging = False

        self._zoom_in_factor = 1.25
        self._zoom_clamp = True
        self._zoom = 10
        self._zoom_step = 1
        self._zoom_range = (-5.0, 10.0)

        self._last_left_mouse_click_pos = qt.QPointF()
        self._last_scene_mouse_pos = qt.QPointF()
        self._rubberband_dragging_rect = False

        self._edge_mode = GraphicsView.EdgeMode.Noop
        self._dragging = edgedrag.EdgeDrag(self)

        self._setup_ui()
        self.setScene(self._graphics_scene)

        self._update_edge_width()
        self._update_render_hints()

    @property
    def scene(self) -> Scene:
        return self._graphics_scene.scene

    @property
    def is_view_dragging(self) -> bool:
        return self._is_view_dragging

    @property
    def zoom(self) -> int:
        return self._zoom

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
                if event.modifiers() & qt.Qt.ControlModifier:
                    self._edge_mode = GraphicsView.EdgeMode.Cut
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
                self._dragging.update_positions(pos.x(), pos.y())

            if self._edge_mode == GraphicsView.EdgeMode.Cut and self._cutline is not None:
                self._cutline.line_points.append(scene_pos)
                self._cutlineupdate()
        except Exception:
            logger.exception('mouseMoveEvent exception', exc_info=True)

        self._last_scene_mouse_pos = scene_pos

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
                    self._cut_intersecting_edges()
                    self._cutline.line_points = []
                    self._cutline.update()
                    self._edge_mode = GraphicsView.EdgeMode.Noop
                    return

                if self._rubberband_dragging_rect:
                    self._rubberband_dragging_rect = False
                    self.scene._on_selection_changed()
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

        if event.button() == qt.Qt.MiddleButton:
            _middle_mouse_release()
        elif event.button() == qt.Qt.LeftButton:
            _left_mouse_release()
        elif event.button() == qt.Qt.RightButton:
            _right_mouse_release()
        else:
            super(GraphicsView, self).mouseReleaseEvent(event)

    @override
    def wheelEvent(self, event: qt.QWheelEvent) -> None:
        zoom_out_factor = 1.0 / self._zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = self._zoom_in_factor
            self._zoom += self._zoom_step
        else:
            zoom_factor = zoom_out_factor
            self._zoom -= self._zoom_step

        clamped = False
        if self._zoom < self._zoom_range[0]:
            self._zoom, clamped = self._zoom_range[0], True
        if self._zoom > self._zoom_range[1]:
            self._zoom, clamped = self._zoom_range[1], True

        # Set actual scale.
        if not clamped or not self._zoom_clamp:
            self.scale(zoom_factor, zoom_factor)
            self._update_edge_width()
            self._update_render_hints()

    @override
    def dragEnterEvent(self, event: qt.QDragEnterEvent) -> None:
        self.scene.signals.itemDragEntered.emit(event)

    @override
    def dropEvent(self, event: qt.QDropEvent) -> None:
        self.scene.signals.itemDropped.emit(event)

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
            logger.info('VARS: {0}'.format(self.scene.vars._vars))
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

    def _setup_ui(self):
        """
        Internal function taht setup graphics view.
        """

        self.setViewportUpdateMode(qt.QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(qt.QGraphicsView.AnchorUnderMouse)
        self.setDragMode(qt.QGraphicsView.RubberBandDrag)
        self.setAcceptDrops(True)

    def _update_edge_width(self):
        edge.GraphicsEdge.WIDTH = ((self._zoom - self._zoom_range[0]) / (self._zoom_range[1] - self._zoom_range[0])) * \
            (edge.GraphicsEdge.MIN_WIDTH - edge.GraphicsEdge.MAX_WIDTH) + edge.GraphicsEdge.MAX_WIDTH

    def _update_render_hints(self):
        if self._zoom > self.HIGH_QUALITY_ZOOM:
            self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.HighQualityAntialiasing | qt.QPainter.TextAntialiasing | qt.QPainter.SmoothPixmapTransform)
        else:
            self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.TextAntialiasing | qt.QPainter.SmoothPixmapTransform)
