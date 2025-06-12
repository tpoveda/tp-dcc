from __future__ import annotations

from typing import Type, Any

from Qt.QtCore import Qt, QPointF, QRectF
from Qt.QtWidgets import (
    QWidget,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
)
from Qt.QtGui import QCursor, QColor, QPen, QPainter, QPainterPath

from ..core.node import Node
from ..views import uiconsts
from ..views.port import PortView
from ..views.connector import ConnectorView
from ..views.node import AbstractNodeView


class BackdropNode(Node):
    """
    Node that defines a backdrop node.
    """

    NODE_NAME = "Backdrop"
    CATEGORY = "Utils"
    IS_EXEC = False

    def __init__(self, view_class: Type[BackdropNodeView] | None = None):
        super().__init__(view_class=view_class or BackdropNodeView)

        self.model.color = (5, 129, 138, 255)
        self.create_property(
            "backdrop_text",
            "",
            widget_type=uiconsts.PropertyWidget.TextEdit.value,
            tab="Backdrop",
        )

    def auto_size(self):
        """
        Function that automatically resizes the backdrop to fit around the intersecting nodes.
        """

        # noinspection PyTypeChecker
        view: BackdropNodeView = self.view
        self.graph.begin_undo(f'"{self.name}" Auto Resize')
        size = view.calculate_backdrop_size()
        self.set_property("width", size["width"])
        self.set_property("height", size["height"])
        self.xy_pos = size["pos"]
        self.graph.end_undo()

    def on_backdrop_updated(
        self, updated_property: str, updated_geometry: dict[str, Any]
    ):
        """
        Callback function that is called when the backdrop is updated.

        :param updated_property: backdrop property changed.
        :param updated_geometry: updated geometry of the backdrop node.
        """

        if updated_property == "sizer_mouse_release":
            self.graph.begin_undo(f'Resized "{self.name}"')
            self.set_property("width", updated_geometry["width"])
            self.set_property("height", updated_geometry["height"])
            self.xy_pos = updated_geometry["pos"]
            self.graph.end_undo()
        elif updated_geometry == "sizer_double_clicked":
            self.graph.begin_undo(f'"{self.name}" Auto Resize')
            self.set_property("width", updated_geometry["width"])
            self.set_property("height", updated_geometry["height"])
            self.xy_pos = updated_geometry["pos"]
            self.graph.end_undo()


class BackdropNodeView(AbstractNodeView):
    """
    Class that defines a backdrop node view.
    """

    def __init__(
        self,
        name: str = "backdrop",
        text: str = "",
        parent: AbstractNodeView | None = None,
    ):
        super().__init__(name=name, parent=parent)

        self._min_size: tuple[int, int] = (80, 80)
        self._properties["backdrop_text"] = text
        self._nodes: list[AbstractNodeView] = [self]

        self._sizer = BackdropNodeViewSizer(26.0, parent=self)
        self._sizer.set_pos(*self._min_size)

        self.setZValue(uiconsts.Z_VALUE_BACKDROP)

    @AbstractNodeView.width.setter
    def width(self, value: int):
        """
        Sets the width of the backdrop.

        :param value: new backdrop width.
        """

        AbstractNodeView.width.fset(self, value)
        self._sizer.set_pos(self._width, self._height)

    @AbstractNodeView.height.setter
    def height(self, value: int):
        """
        Sets the height of the backdrop.

        :param value: new backdrop height.
        """

        AbstractNodeView.height.fset(self, value)
        self._sizer.set_pos(self._width, self._height)

    @property
    def minimum_size(self) -> tuple[int, int]:
        """
        Returns the minimum size of the backdrop.

        :return: tuple[int, int]
        """

        return self._min_size

    @minimum_size.setter
    def minimum_size(self, value: tuple[int, int]):
        """
        Sets the minimum size of the backdrop.

        :param value: tuple[int, int]
        """

        self._min_size = value

    @property
    def backdrop_text(self) -> str:
        """
        Returns the backdrop text.

        :return: str
        """

        return self._properties["backdrop_text"]

    @backdrop_text.setter
    def backdrop_text(self, value: str):
        """
        Sets the backdrop text.

        :param value: str
        """

        self._properties["backdrop_text"] = value
        self.update(self.boundingRect())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is pressed.

        :param event: mouse event.
        """

        if not event.button() == Qt.LeftButton:
            return

        pos = event.scenePos()
        rect = QRectF(pos.x() - 5, pos.y() - 5, 10, 10)
        item = self.scene().items(rect)[0]
        if isinstance(item, (PortView, ConnectorView)):
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            return
        if self.selected:
            return
        viewer = self.viewer()
        [n.setSelected(False) for n in viewer.selected_nodes()]
        self._nodes += self.nodes(False)
        [n.setSelected(True) for n in self._nodes]

    def mouseDoubleClickEvent(self, event):
        """
        Function that is called when a mouse button is double-clicked.

        :param event: mouse event.
        """

        viewer = self.viewer()
        if viewer:
            viewer.nodeDoubleClicked.emit(self.id)
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is released.

        :param event: mouse event.
        """

        super().mouseReleaseEvent(event)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        [n.setSelected(True) for n in self._nodes]
        self._nodes = [self]

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the backdrop view in the given painter.

        :param painter: painter to paint the port view.
        :param option: style option for the port view.
        :param widget: widget to paint the port view.
        """

        painter.save()
        try:
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.NoBrush)

            margin: float = 1.0
            radius: float = 2.6

            rect = self.boundingRect()
            rect = QRectF(
                rect.left() + margin,
                rect.top() + margin,
                rect.width() - (margin * 2),
                rect.height() - (margin * 2),
            )
            color = (self.color[0], self.color[1], self.color[2], 50)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(*color))
            painter.drawRoundedRect(rect, radius, radius)

            top_rect = QRectF(rect.x(), rect.y(), rect.width(), 26.0)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(*self.color))
            painter.drawRoundedRect(top_rect, radius, radius)
            for pos in [top_rect.left(), top_rect.right() - 5.0]:
                painter.drawRect(QRectF(pos, top_rect.bottom() - 5.0, 5.0, 5.0))

            if self.backdrop_text:
                text_rect = QRectF(
                    top_rect.x() + 5.0,
                    top_rect.height() + 3.0,
                    rect.width() - 5.0,
                    rect.height(),
                )
                painter.setPen(QColor(*self.text_color))
                painter.drawText(
                    text_rect, Qt.AlignLeft | Qt.TextWordWrap, self.backdrop_text
                )

            if self.selected:
                selected_color = [x for x in uiconsts.NODE_SELECTED_COLOR]
                selected_color[-1] = 15
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(*selected_color))
                painter.drawRoundedRect(rect, radius, radius)

            text_rect = QRectF(
                top_rect.x(), top_rect.y(), rect.width(), top_rect.height()
            )
            painter.setPen(QColor(*self.text_color))
            painter.drawText(text_rect, Qt.AlignCenter, self.name)

            border = 0.8
            border_color = self.color
            if self.selected:
                border = 1.0
                border_color = uiconsts.NODE_BORDER_SELECTED_COLOR
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(*border_color), border))
            painter.drawRoundedRect(rect, radius, radius)
        finally:
            painter.restore()

    def from_dict(self, data: dict[str, Any]):
        """
        Sets the backdrop properties from a dictionary.

        :param data: dictionary containing the backdrop properties.
        """

        super().from_dict(data)

        custom_properties = data.get("custom") or {}
        for prop_name, value in custom_properties.items():
            if prop_name == "backdrop_text":
                self.backdrop_text = value

    def nodes(self, include_intersected_items: bool = False) -> list[AbstractNodeView]:
        """
        Returns the nodes contained in the backdrop.

        :param include_intersected_items: include intersected items.
        :return: list[AbstractNodeView]
        """

        mode = {True: Qt.IntersectsItemShape, False: Qt.ContainsItemShape}

        found_nodes: list[AbstractNodeView] = []
        if not self.scene():
            return found_nodes

        polygon = self.mapToScene(self.boundingRect())
        rect = polygon.boundingRect()
        items = self.scene().items(rect, mode=mode[include_intersected_items])
        for item in items:
            if item == self or item == self._sizer:
                continue
            if isinstance(item, AbstractNodeView):
                found_nodes.append(item)

        return found_nodes

    def calculate_backdrop_size(
        self, nodes: list[AbstractNodeView] | None = None
    ) -> dict[str, Any]:
        """
        Internal function that calculates the size of the backdrop.

        :param nodes: list of nodes to calculate the size from.
        :return: dictionary containing the new pos, width and height of the backdrop view.
        """

        padding: int = 40

        nodes = nodes or self.nodes()
        if nodes:
            nodes_rect = self._combined_rect(nodes)
        else:
            center = self.mapToScene(self.boundingRect().center())
            nodes_rect = QRectF(
                center.x(), center.y(), self._min_size[0], self._min_size[1]
            )

        return {
            "pos": [nodes_rect.x() - padding, nodes_rect.y() - padding],
            "width": nodes_rect.width() + (padding * 2),
            "height": nodes_rect.height() + (padding * 2),
        }

    def auto_resize(self):
        """
        Function that automatically resizes the backdrop.
        """

        size = self.calculate_backdrop_size()
        self.viewer().nodeBackdropUpdated.emit(self.id, "sizer_double_clicked", size)

    def on_sizer_position_changed(self, pos: QPointF):
        """
        Callback function that is called when the sizer position changes.

        :param pos: new position of the sizer.
        """

        self._width = pos.x() + self._sizer.size
        self._height = pos.y() + self._sizer.size

    def on_sizer_position_mouse_release(self):
        """
        Callback function that is called when the sizer position is released.
        """

        size = {"pos": self.xy_pos, "width": self._width, "height": self._height}
        self.viewer().nodeBackdropUpdated.emit(self.id, "sizer_mouse_release", size)

    def _combined_rect(self, nodes: list[AbstractNodeView]) -> QRectF:
        """
        Internal function that returns the combined rect of the backdrop.

        :param nodes: list of nodes to calculate the rect from.
        :return: QRectF
        """

        if not self.scene():
            return QRectF()

        group = self.scene().createItemGroup(nodes)
        rect = group.boundingRect()
        self.scene().destroyItemGroup(group)

        # rect = QRectF()
        # for node in nodes:
        #     rect = rect.united(node.boundingRect())

        return rect


class BackdropNodeViewSizer(QGraphicsItem):
    """
    Class that defines a backdrop node view sizer.
    """

    def __init__(self, size: float = 6.0, parent: BackdropNodeView | None = None):
        super().__init__(parent=parent)

        self._size = size
        self._previous_xy: tuple[float, float] | None = None

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(Qt.SizeFDiagCursor))
        self.setToolTip("Double-Click to auto resize.")

    @property
    def size(self) -> float:
        """
        Returns the size of the sizer.

        :return: float
        """

        return self._size

    def boundingRect(self) -> QRectF:
        """
        Returns the bounding rectangle of the item.

        :return: QRectF
        """

        return QRectF(0.5, 0.5, self._size, self._size)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Called when the item changes.

        :param change: type of change.
        :param value: value of the change.
        :return: value of the change.
        """

        if change == QGraphicsItem.ItemPositionChange:
            # noinspection PyTypeChecker
            node_view: BackdropNodeView = self.parentItem()
            minimum_size_x, minimum_size_y = node_view.minimum_size
            x = minimum_size_x if value.x() < minimum_size_x else value.x()
            y = minimum_size_y if value.y() < minimum_size_y else value.y()
            value = QPointF(x, y)
            node_view.on_sizer_position_changed(value)
            return value

        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is pressed.

        :param event: mouse event.
        """

        self._previous_xy = (self.pos().x(), self.pos().y())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is double-clicked.

        :param event: mouse event.
        """

        # noinspection PyTypeChecker
        node_view: BackdropNodeView = self.parentItem()
        node_view.auto_resize()
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function that is called when a mouse button is released.

        :param event: mouse event.
        """

        current_xy = (self.pos().x(), self.pos().y())
        if current_xy != self._previous_xy:
            # noinspection PyTypeChecker
            node_view: BackdropNodeView = self.parentItem()
            node_view.on_sizer_position_mouse_release()

        self._previous_xy = None

        super().mouseReleaseEvent(event)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the resizer in the given painter.

        :param painter: painter to paint the port view.
        :param option: style option for the port view.
        :param widget: widget to paint the port view.
        """

        painter.save()
        try:
            margin: float = 1.0
            rect = self.boundingRect()
            rect = QRectF(
                rect.left() + margin,
                rect.top() + margin,
                rect.width() - (margin * 2),
                rect.height() - (margin * 2),
            )
            # noinspection PyTypeChecker
            node_view: BackdropNodeView = self.parentItem()
            if node_view and node_view.selected:
                color = QColor(*uiconsts.NODE_BORDER_SELECTED_COLOR)
            else:
                color = QColor(*node_view.color)
                color = color.darker(110)
            path = QPainterPath()
            path.moveTo(rect.topRight())
            path.lineTo(rect.bottomRight())
            path.lineTo(rect.bottomLeft())
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.fillPath(path, painter.brush())
        finally:
            painter.restore()

    def set_pos(self, x: float, y: float):
        """
        Sets the position of the sizer.

        :param x: position in X coordinate.
        :param y: position in Y coordinate.
        """

        x -= self._size
        y -= self._size
        self.setPos(x, y)
