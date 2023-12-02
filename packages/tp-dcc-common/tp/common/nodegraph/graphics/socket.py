from __future__ import annotations

import typing
from typing import Union, Any

from overrides import override

from tp.common.qt import api as qt
from tp.preferences.interfaces import noddle
from tp.common.nodegraph.core import consts

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.socket import Socket


class GraphicsSocket(qt.QGraphicsItem):

    FONT_NAME: str | None = None
    FONT_SIZE: int | None = None
    TEXT_ZOOM_OUT_LIMIT = -0.4
    SOCKET_ZOOM_OUT_LIMIT = -0.75

    def __init__(self, socket: Socket):
        super().__init__(socket.node.view)

        if GraphicsSocket.FONT_NAME is None or GraphicsSocket.FONT_SIZE is None:
            prefs = noddle.noddle_interface()
            GraphicsSocket.FONT_NAME, GraphicsSocket.FONT_SIZE = prefs.builder_node_title_font()

        self._socket = socket

        self._radius = 6.0
        self._empty_radius = 3.0
        self._outline_width = 1.0

        self._color_empty = qt.QColor('#141413')
        self._color_background = self.socket.data_type.get('color')
        self._color_outline = qt.QColor("#FF000000")
        self._pen = qt.QPen(self._color_outline)
        self._pen.setWidthF(self._outline_width)
        self._brush = qt.QBrush(self._color_background)
        self._brush_empty = qt.QBrush(self._color_empty)
        self._label_font = qt.QFont(GraphicsSocket.FONT_NAME, GraphicsSocket.FONT_SIZE)

        self._setup_ui()

    @property
    def socket(self) -> Socket:
        return self._socket

    @property
    def text_item(self) -> qt.QGraphicsTextItem:
        return self._text_item

    @property
    def outline_width(self) -> float:
        return self._outline_width

    @property
    def radius(self) -> float:
        return self._radius

    @property
    def empty_radius(self) -> float:
        return self._empty_radius

    @property
    def color_background(self) -> qt.QColor:
        return self._color_background

    @color_background.setter
    def color_background(self, value: qt.QColor):
        self._color_background = value

    @override
    def boundingRect(self) -> qt.QRectF:
        return qt.QRectF(
            -self.radius - self.outline_width, -self.radius - self.outline_width,
            2 * (self.radius + self.outline_width), 2 * (self.radius + self.outline_width))

    @override
    def itemChange(self, change: qt.QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == self.ItemScenePositionHasChanged:
            self.socket.update_edges()
        return super().itemChange(change, value)

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:

        zoom = self.socket.node.graph.view.zoom_value()
        self.text_item.setVisible(zoom > self.TEXT_ZOOM_OUT_LIMIT)
        if zoom < self.SOCKET_ZOOM_OUT_LIMIT:
            return

        # Update background color
        self._brush.setColor(self._color_background)

        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(int(-self.radius), int(-self.radius), int(2 * self.radius), int(2 * self.radius))
        if not self.socket.has_edge():
            painter.setBrush(self._brush_empty)
            painter.drawEllipse(
                int(-self.empty_radius), int(-self.empty_radius),
                int(2 * self.empty_radius), int(2 * self.empty_radius))

    def _setup_ui(self):
        """
        Internal function that creates graphics socket widgets.
        """

        self.setAcceptHoverEvents(True)
        self.setCacheMode(consts.ITEM_CACHE_MODE)
        self.setFlag(self.ItemIsSelectable, True)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setZValue(consts.SOCKET_Z_VALUE)

        self._setup_label()

    def _setup_label(self):
        """
        Internal function that setup graphics socket label.
        """

        self._text_item = qt.QGraphicsTextItem(self.socket.label, parent=self)
        self._text_item.setFont(self._label_font)
        if self.socket.node_position in [self.socket.Position.RightTop, self.socket.Position.RightBottom]:
            self._align_text_right()

    def _align_text_right(self):
        """
        Internal function that aligns socket label to the right.
        """

        fmt = qt.QTextBlockFormat()
        fmt.setAlignment(qt.Qt.AlignRight)
        cursor = self.text_item.textCursor()
        cursor.select(qt.QTextCursor.Document)
        cursor.mergeBlockFormat(fmt)
        cursor.clearSelection()
        self.text_item.setTextCursor(cursor)
