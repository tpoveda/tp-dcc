from __future__ import annotations

import math
import typing

from overrides import override

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph
    from tp.common.nodegraph.graphics.view import GraphicsView


class GraphicsScene(qt.QGraphicsScene):
    def __init__(self, graph: NodeGraph, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._graph = graph

        self._grid_size = 20
        self._grid_squares = 5
        self._scene_width = self._scene_height = 64000

        self._color_background = qt.QColor('#393939')
        self._color_light = qt.QColor('#2f2f2f')
        self._color_dark = qt.QColor('#292929')
        self._pen_light = qt.QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = qt.QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_background)

    @property
    def graph(self) -> NodeGraph:
        return self._graph

    @override
    def dragMoveEvent(self, event: qt.QGraphicsSceneDragDropEvent) -> None:
        # override to disable parent event
        pass

    @override
    def drawBackground(self, painter: qt.QPainter, rect: qt.QRectF) -> None:
        super().drawBackground(painter, rect)

        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        firt_left = left - (left % self._grid_size)
        first_top = top - (top % self._grid_size)

        lines_light, lines_dark = [], []
        for x in range(firt_left, right, self._grid_size):
            if x % (self._grid_size * self._grid_squares):
                lines_light.append(qt.QLine(x, top, x, bottom))
            else:
                lines_dark.append(qt.QLine(x, top, x, bottom))
        for y in range(first_top, bottom, self._grid_size):
            if y % (self._grid_size * self._grid_squares):
                lines_light.append(qt.QLine(left, y, right, y))
            else:
                lines_dark.append(qt.QLine(left, y, right, y))

        painter.setPen(self._pen_light)
        painter.drawLines(lines_light)
        painter.setPen(self._pen_dark)
        painter.drawLines(lines_dark)

    def viewer(self) -> GraphicsView | None:
        """
        Returns node graph view this scene is linked to.

        :return: node graph viewer.
        :rtype: GraphicsView or None
        """

        return self.views()[0] if self.views() else None

    def set_scene_size(self, width: int, height: int):
        """
        Sets graphics scene size.

        :param int width: scene width (in pixels).
        :param int height: scene height (in pixels).
        """

        self.setSceneRect(-width // 2, -height // 2, width, height)
