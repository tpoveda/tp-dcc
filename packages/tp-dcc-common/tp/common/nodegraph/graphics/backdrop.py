from __future__ import annotations

import typing
from typing import Union, Any

from overrides import override

from tp.common.qt import api as qt
from tp.common.nodegraph.core import consts
from tp.common.nodegraph.graphics import socket, edge, node as graphics_node

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import Node


class GraphicsBackdrop(graphics_node.BaseGraphicsNode):
    """
    Base backdrop item.
    """

    def __init__(self, node: Node, name: str = 'backdrop', text: str = '', parent: qt.QWidget | None = None):
        super().__init__(node=node, name=name, parent=parent)

        self._properties['backdrop_text'] = ''
        self._min_size = 80, 80
        self._sizer = BackdropSizer(self, 26.0)
        self._sizer.set_pos(*self._min_size)
        self._nodes: list[graphics_node.BaseGraphicsNode] = [self]

        self.setZValue(consts.EDGE_Z_VALUE - 1)

    @property
    def minimum_size(self) -> tuple[int, int]:
        return self._min_size

    @minimum_size.setter
    def minimum_size(self, size: tuple[int, int] = (50, 50)):
        self._min_size = size

    @property
    def backdrop_text(self):
        return self._properties['backdrop_text']

    @backdrop_text.setter
    def backdrop_text(self, text):
        self._properties['backdrop_text'] = text
        self.update(self.boundingRect())

    @graphics_node.GraphicsNode.width.setter
    def width(self, width=0.0):
        graphics_node.GraphicsNode.width.fset(self, width)
        self._sizer.set_pos(self._width, self._height)

    @graphics_node.GraphicsNode.height.setter
    def height(self, height=0.0):
        graphics_node.GraphicsNode.height.fset(self, height)
        self._sizer.set_pos(self._width, self._height)

    @override
    def mouseDoubleClickEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        viewer = self.viewer()
        if viewer:
            viewer.nodeDoubleClicked.emit(self.id)

        super().mouseDoubleClickEvent(event)

    @override
    def mousePressEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        if event.button() == qt.Qt.LeftButton:
            pos = event.scenePos()
            rect = qt.QRectF(pos.x() - 5, pos.y() - 5, 10, 10)
            item = self.scene().items(rect)[0]

            if isinstance(item, (socket.GraphicsSocket, edge.GraphicsEdge)):
                self.setFlag(self.ItemIsMovable, False)
                return
            if self.selected:
                return

            viewer = self.viewer()
            [n.setSelected(False) for n in viewer.selected_nodes()]

            self._nodes += self.nodes(False)
            [n.setSelected(True) for n in self._nodes]

    @override
    def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        self.setFlag(self.ItemIsMovable, True)
        [n.setSelected(True) for n in self._nodes]
        self._nodes = [self]

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:
        painter.save()
        painter.setPen(qt.Qt.NoPen)
        painter.setBrush(qt.Qt.NoBrush)

        margin = 1.0
        rect = self.boundingRect()
        rect = qt.QRectF(
            rect.left() + margin, rect.top() + margin,
            rect.width() - (margin * 2), rect.height() - (margin * 2))

        radius = 2.6
        color = (self.color[0], self.color[1], self.color[2], 50)
        painter.setBrush(qt.QColor(*color))
        painter.setPen(qt.Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        top_rect = qt.QRectF(rect.x(), rect.y(), rect.width(), 26.0)
        painter.setBrush(qt.QBrush(qt.QColor(*self.color)))
        painter.setPen(qt.Qt.NoPen)
        painter.drawRoundedRect(top_rect, radius, radius)
        for pos in [top_rect.left(), top_rect.right() - 5.0]:
            painter.drawRect(qt.QRectF(pos, top_rect.bottom() - 5.0, 5.0, 5.0))

        if self.backdrop_text:
            painter.setPen(qt.QColor(*self.text_color))
            txt_rect = qt.QRectF(
                top_rect.x() + 5.0, top_rect.height() + 3.0,
                rect.width() - 5.0, rect.height())
            painter.setPen(qt.QColor(*self.text_color))
            painter.drawText(txt_rect, qt.Qt.AlignLeft | qt.Qt.TextWordWrap, self.backdrop_text)

        if self.selected:
            sel_color = [x for x in consts.NODE_SELECTED_COLOR]
            sel_color[-1] = 15
            painter.setBrush(qt.QColor(*sel_color))
            painter.setPen(qt.Qt.NoPen)
            painter.drawRoundedRect(rect, radius, radius)

        txt_rect = qt.QRectF(top_rect.x(), top_rect.y(), rect.width(), top_rect.height())
        painter.setPen(qt.QColor(*self.text_color))
        painter.drawText(txt_rect, qt.Qt.AlignCenter, self.node.title)

        border = 0.8
        border_color = self.color
        if self.selected and consts.NODE_SELECTED_BORDER_COLOR:
            border = 1.0
            border_color = consts.NODE_SELECTED_BORDER_COLOR
        painter.setBrush(qt.Qt.NoBrush)
        painter.setPen(qt.QPen(qt.QColor(*border_color), border))
        painter.drawRoundedRect(rect, radius, radius)

        painter.restore()

    def on_sizer_pos_changed(self, pos):
        self._width = pos.x() + self._sizer.size
        self._height = pos.y() + self._sizer.size

    def on_sizer_pos_mouse_release(self):
        size = {
            'pos': self.xy_pos,
            'width': self._width,
            'height': self._height}
        self.viewer().nodeBackdropUpdated.emit(self.node.uuid, 'sizer_mouse_release', size)

    def on_sizer_double_clicked(self):
        size = self.calc_backdrop_size()
        self.viewer().nodeBackdropUpdated.emit(self.node.uid, 'sizer_double_clicked', size)

    def nodes(self, inc_intersects: bool = False) -> list[graphics_node.BaseGraphicsNode]:
        mode = {True: qt.Qt.IntersectsItemShape, False: qt.Qt.ContainsItemShape}
        nodes = list()
        if self.scene():
            polygon = self.mapToScene(self.boundingRect())
            rect = polygon.boundingRect()
            items = self.scene().items(rect, mode=mode[inc_intersects])
            for item in items:
                if item == self or item == self._sizer:
                    continue
                if isinstance(item, graphics_node.BaseGraphicsNode):
                    nodes.append(item)
        return nodes

    def calc_backdrop_size(self, nodes=None):
        nodes = nodes or self.nodes(True)
        padding = 40
        nodes_rect = self._combined_rect(nodes)
        return {
            'pos': [
                nodes_rect.x() - padding, nodes_rect.y() - padding
            ],
            'width': nodes_rect.width() + (padding * 2),
            'height': nodes_rect.height() + (padding * 2)
        }

    def _combined_rect(self, nodes: list[graphics_node.BaseGraphicsNode]) -> qt.QRectF:
        group = self.scene().createItemGroup(nodes)
        rect = group.boundingRect()
        self.scene().destroyItemGroup(group)
        return rect


class BackdropSizer(qt.QGraphicsItem):
    def __init__(self, parent: GraphicsBackdrop, size: float = 6.0):
        super(BackdropSizer, self).__init__(parent)

        self._size = size

        self.setFlag(self.ItemIsSelectable, True)
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(qt.QCursor(qt.Qt.SizeFDiagCursor))
        self.setToolTip('double-click auto resize')

    @property
    def size(self):
        return self._size

    @override
    def boundingRect(self) -> qt.QRectF:
        return qt.QRectF(0.5, 0.5, self._size, self._size)

    @override
    def itemChange(self, change: qt.QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == self.ItemPositionChange:
            item = self.parentItem()                # type: GraphicsBackdrop
            mx, my = item.minimum_size
            x = mx if value.x() < mx else value.x()
            y = my if value.y() < my else value.y()
            value = qt.QPointF(x, y)
            item.on_sizer_pos_changed(value)
            return value
        return super().itemChange(change, value)

    @override
    def mouseDoubleClickEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        item = self.parentItem()                    # type: GraphicsBackdrop
        item.on_sizer_double_clicked()

        super().mouseDoubleClickEvent(event)

    @override
    def mousePressEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        self._prev_xy = (self.pos().x(), self.pos().y())
        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        current_xy = (self.pos().x(), self.pos().y())
        if current_xy != self._prev_xy:
            item = self.parentItem()                # type: GraphicsBackdrop
            item.on_sizer_pos_mouse_release()

        del self._prev_xy

        super().mouseReleaseEvent(event)

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:

        painter.save()

        margin = 1.0
        rect = self.boundingRect()
        rect = qt.QRectF(
            rect.left() + margin, rect.top() + margin,
            rect.width() - (margin * 2), rect.height() - (margin * 2))

        item = self.parentItem()                    # type: GraphicsBackdrop
        if item and item.selected:
            color = qt.QColor(*consts.NODE_SELECTED_COLOR)
        else:
            color = qt.QColor(*item.color)
            color = color.darker(110)
        path = qt.QPainterPath()
        path.moveTo(rect.topRight())
        path.lineTo(rect.bottomRight())
        path.lineTo(rect.bottomLeft())
        painter.setBrush(color)
        painter.setPen(qt.Qt.NoPen)
        painter.fillPath(path, painter.brush())

        painter.restore()

    def set_pos(self, x: float, y: float):
        """
        Sets the position of the node within the node graph view.

        :param float x: X position.
        :param float y: Y position.
        """

        x -= self._size
        y -= self._size
        self.setPos(x, y)
