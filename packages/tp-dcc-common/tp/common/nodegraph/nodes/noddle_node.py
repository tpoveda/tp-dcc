from __future__ import annotations

import typing
from typing import Union

from overrides import override

from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.common.nodegraph.core import node
from tp.common.nodegraph.graphics import node as graphics_node

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import Node


class NoddleNodeGraphics(graphics_node.GraphicsNode):
    def __init__(self, node: Node, parent: qt.QWidget | None = None):
        super().__init__(node, parent=parent)

        status_icon = resources.icon('status_icons')
        self._status_icons = qt.QImage | None
        if status_icon and not status_icon.isNull():
            self._status_icons = qt.QImage(
                status_icon.pixmap(72, 24).toImage().convertToFormat(qt.QImage.Format_ARGB32))

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:

        super().paint(painter, option, widget=widget)

        if self.node.is_invalid():
            icon_offset = 48.0
            self._paint_status_icon(painter, icon_offset)
        elif self.node.STATUS_ICON or self.node.IS_EXEC:
            if self.node.is_compiled():
                icon_offset = 24.0
                self._paint_status_icon(painter, icon_offset)
            elif self.node.is_executing:
                icon_offset = 0
                self._paint_status_icon(painter, icon_offset)

    def _paint_status_icon(self, painter: qt.QPainter, offset: float):
        """
        Internal function that paints node status icon.

        :param qt.QPainter painter: QPainter instance used to paint the status icon.
        :param float offset: status image offset.
        """

        painter.drawImage(qt.QRectF(-13.0, -13.0, 24.0, 24.0), self._status_icons, qt.QRectF(offset, 0, 24.0, 24.0))


class NoddleNode(node.Node):

    DEFAULT_TITLE = 'Noddle Node'
    TITLE_EDITABLE = False
    UNIQUE = False
    CATEGORY = 'Utils'
    ICON = None
    STATUS_ICON = True
    GRAPHICS_CLASS = NoddleNodeGraphics

