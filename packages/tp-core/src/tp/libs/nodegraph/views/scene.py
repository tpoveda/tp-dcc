from __future__ import annotations

import math
import typing

from Qt.QtCore import Qt, QLine, QPoint, QRectF
from Qt.QtWidgets import QWidget, QGraphicsScene, QGraphicsSceneMouseEvent
from Qt.QtGui import QColor, QPainter, QPen

from . import uiconsts

if typing.TYPE_CHECKING:
    from .graph import NodeGraphView
    from .node import AbstractNodeView, NodeView


class NodeGraphScene(QGraphicsScene):
    """
    Class that defines the scene for the node graph.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._grid_mode: int = uiconsts.NODE_GRAPH_GRID_DISPLAY_LINES
        self._grid_size: int = uiconsts.NODE_GRAPH_GRID_SIZE
        self._grid_squares: int = uiconsts.NODE_GRAPH_GRID_SQUARES
        self._background_color: tuple[int, int, int] = (
            uiconsts.NODE_GRAPH_BACKGROUND_COLOR
        )
        self._grid_color: tuple[int, int, int] = uiconsts.NODE_GRAPH_GRID_COLOR

        self.setBackgroundBrush(QColor(*self._background_color))

    @property
    def grid_mode(self) -> int:
        """
        Returns the grid mode of the scene.

        :return: grid mode.
        """

        return self._grid_mode

    @grid_mode.setter
    def grid_mode(self, value: int | None = None):
        """
        Sets the grid mode of the scene.

        :param value: grid mode to set.
        """

        value = value if value is not None else uiconsts.NODE_GRAPH_GRID_DISPLAY_LINES
        self._grid_mode = value

    @property
    def background_color(self) -> tuple[int, int, int]:
        """
        Returns the background color of the scene.

        :return: background color.
        """

        return self._background_color

    @background_color.setter
    def background_color(self, value: tuple[int, int, int]):
        """
        Sets the background color of the scene.

        :param value: color to set.
        """

        self._background_color = value
        self.setBackgroundBrush(QColor(*self._background_color))

    @property
    def grid_color(self) -> tuple[int, int, int]:
        """
        Returns the grid color of the scene.

        :return: grid color.
        """

        return self._grid_color

    @grid_color.setter
    def grid_color(self, value: tuple[int, int, int]):
        """
        Sets the grid color of the scene.

        :param value: color to set.
        """

        self._grid_color = value

    def __repr__(self) -> str:
        """
        Returns a string representation of the object.

        :return: object string representation.
        """

        return f'<{self.__class__.__name__}("{self.viewer()}") object {hex(id(self))}'

    def viewer(self) -> NodeGraphView | None:
        """
        Returns the viewer linked with this scene.

        :return: node graph viewer.
        """

        return self.views()[0] if self.views() else None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is pressed.

        :param event: mouse event.
        """

        selected_nodes: list[AbstractNodeView | NodeView] | None = None
        if self.viewer():
            selected_nodes = self.viewer().selected_nodes()
            self.viewer().sceneMousePressEvent(event)

        super().mousePressEvent(event)

        keep_selection = any(
            [
                event.button() == Qt.MiddleButton,
                event.button() == Qt.RightButton,
                event.button() == Qt.AltModifier,
            ]
        )
        if keep_selection:
            for node in selected_nodes:
                node.setSelected(True)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when the mouse is moved.

        :param event: mouse event.
        """

        if self.viewer():
            self.viewer().sceneMouseMoveEvent(event)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is released.

        :param event: mouse event.
        """

        if self.viewer():
            self.viewer().sceneMouseReleaseEvent(event)

        super().mouseReleaseEvent(event)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """
        Function that is called to draw the background of the scene.

        :param painter: object used to paint the scene.
        :param rect: paint rectangle area.
        """

        super().drawBackground(painter, rect)

        painter.save()
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setBrush(self.backgroundBrush())

            if self._grid_mode == uiconsts.NODE_GRAPH_GRID_DISPLAY_DOTS:
                pen = QPen(QColor(*self._grid_color), 0.65)
                self._draw_dots(painter, rect, pen)
            elif self._grid_mode == uiconsts.NODE_GRAPH_GRID_DISPLAY_LINES:
                zoom = self.viewer().zoom_value()
                color = QColor(*self._background_color).darker(200)
                if zoom < 0.0:
                    color = color.darker(100 - int(zoom * 110))
                pen1 = QPen(QColor(*self._grid_color), 0.65)
                pen2 = QPen(QColor(color), 2.0)
                self._draw_lines(painter, rect, pen1, pen2)
        finally:
            painter.restore()

    def _draw_dots(self, painter: QPainter, rect: QRectF, pen: QPen):
        """
        Internal function that is called to draw the grid dots.

        :param painter: object used to paint the scene.
        :param rect: paint rectangle area.
        :param pen: pen used to draw the dots.
        """

        zoom = self.viewer().zoom_value()
        grid_size = self._grid_size
        if zoom < 0.0:
            grid_size = int(abs(zoom) / 0.3 + 1) * self._grid_size

        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % grid_size)
        first_top = top - (top % grid_size)

        pen.setWidth(int(grid_size / 10))
        painter.setPen(pen)

        points = [
            QPoint(int(x), int(y))
            for x in range(first_left, right, grid_size)
            for y in range(first_top, bottom, grid_size)
        ]
        painter.drawPoints(points)

    def _draw_lines(self, painter: QPainter, rect: QRectF, pen1: QPen, pen2: QPen):
        """
        Internal function that is called to draw the grid lines.

        :param painter: object used to paint the scene.
        :param rect: paint rectangle area.
        :param pen1: pen used to draw the dots.
        :param pen2: pen used to draw the dots.
        """

        grid_size = self._grid_size

        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % grid_size)
        first_top = top - (top % grid_size)

        lines_light, lines_dark = [], []
        for x in range(first_left, right, grid_size):
            if x % (grid_size * self._grid_squares):
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))
        for y in range(first_top, bottom, grid_size):
            if y % (grid_size * self._grid_squares):
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))

        zoom = self.viewer().zoom_value()
        if zoom > -0.5:
            painter.setPen(pen1)
            painter.drawLines(lines_light)
        painter.setPen(pen2)
        painter.drawLines(lines_dark)
