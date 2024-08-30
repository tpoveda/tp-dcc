from __future__ import annotations

import typing
from typing import Callable, Any

from . import uiconsts
from ..core import consts, datatypes
from ..painters import port as port_painter

from Qt.QtCore import QPointF, QRectF
from Qt.QtWidgets import (
    QWidget,
    QGraphicsItem,
    QStyleOptionGraphicsItem,
    QGraphicsSceneHoverEvent,
)
from Qt.QtGui import QColor, QPen, QBrush, QPainter, QPolygonF

if typing.TYPE_CHECKING:
    from .node import NodeView
    from .scene import NodeGraphScene
    from .connector import ConnectorView


class PortView(QGraphicsItem):
    """
    Class that defines port views.
    """

    def __init__(self, parent: NodeView):
        super().__init__(parent=parent)

        self._name: str = "port"
        self._display_name: bool = True
        self._port_type: int | None = None
        self._data_type: datatypes.DataType | None = None
        self._multi_connection: bool = False
        self._width: float = uiconsts.PORT_SIZE
        self._height: float = uiconsts.PORT_SIZE
        self._color: tuple[int, int, int, int] = uiconsts.PORT_COLOR
        self._border_color: tuple[int, int, int, int] = uiconsts.PORT_BORDER_COLOR
        self._active_color: tuple[int, int, int, int] = uiconsts.PORT_ACTIVE_COLOR
        self._hover_color: tuple[int, int, int, int] = uiconsts.PORT_HOVER_COLOR
        self._hover_border_color: tuple[int, int, int, int] = (
            uiconsts.PORT_HOVER_BORDER_COLOR
        )
        self._border_size: int = 1
        self._locked: bool = False
        self._hovered: bool = False
        self._connector_views: list[ConnectorView] = []

        self.setAcceptHoverEvents(True)
        self.setCacheMode(uiconsts.ITEM_CACHE_MODE)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setZValue(uiconsts.Z_VALUE_PORT)

    def __repr__(self) -> str:
        """
        Returns a string representation of the object.

        :return: object string representation.
        """

        return f'<{self.__class__.__name__}("{self.name}") object {hex(id(self))}>'

    def boundingRect(self) -> QRectF:
        """
        Returns the bounding rectangle of the port view.

        :return: bounding rectangle.
        """

        return QRectF(0.0, 0.0, self._width + uiconsts.PORT_CLICK_FALLOFF, self._height)

    @property
    def node_view(self) -> NodeView:
        """
        Getter method that returns the node view.

        :return: node view.
        """

        # noinspection PyTypeChecker
        return self.parentItem()

    @property
    def data_type(self) -> datatypes.DataType:
        """
        Getter method that returns the data type of the port view.

        :return: data type of the port view.
        """

        return self._data_type

    @data_type.setter
    def data_type(self, value: datatypes.DataType):
        """
        Setter method that sets the data type of the port view.

        :param value: data type of the port view.
        """

        self._data_type = value
        self._update_colors()

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of the port view.

        :return: name of the port view.
        """

        return self._name

    @name.setter
    def name(self, value: str):
        """
        Setter method that sets the name of the port view.

        :param value: name of the port view.
        """

        self._name = value.strip()

    @property
    def display_name(self) -> bool:
        """
        Getter method that returns whether the name of the port view should be displayed.

        :return: whether the name of the port view should be displayed.
        """

        return self._display_name

    @display_name.setter
    def display_name(self, flag: bool):
        """
        Setter method that sets whether the name of the port view should be displayed.

        :param flag: whether the name of the port view should be displayed.
        """

        self._display_name = flag

    @property
    def port_type(self) -> int | None:
        """
        Getter method that returns the type of the port view.

        :return: type of the port view.
        """

        return self._port_type

    @port_type.setter
    def port_type(self, value: int):
        """
        Setter method that sets the type of the port view.

        :param value: type of the port view.
        """

        self._port_type = value

    @property
    def multi_connection(self) -> bool:
        """
        Getter method that returns whether the port view supports multiple connections.

        :return: whether the port view supports multiple connections.
        """

        return self._multi_connection

    @multi_connection.setter
    def multi_connection(self, flag: bool):
        """
        Setter method that sets whether the port view supports multiple connections.

        :param flag: whether the port view supports multiple connections.
        """

        self._multi_connection = flag
        self.setToolTip(f"{self.name}: ({'multi' if flag else 'single'})")

    @property
    def color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the color of the port view.

        :return: color of the port view.
        """

        return self._color

    @color.setter
    def color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the color of the port view.

        :param value: color of the port view.
        """

        self._color = value
        self.update()

    @property
    def border_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the border color of the port view.

        :return: border color of the port view.
        """

        return self._border_color

    @border_color.setter
    def border_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the border color of the port view.

        :param value: border color of the port view.
        """

        self._border_color = value
        self.update()

    @property
    def active_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the active color of the port view.

        :return: active color of the port view.
        """

        return self._active_color

    @active_color.setter
    def active_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the active color of the port view.

        :param value: active color of the port view.
        """

        self._active_color = value
        self.update()

    @property
    def hover_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the hover color of the port view.

        :return: hover color of the port view.
        """

        return self._hover_color

    @hover_color.setter
    def hover_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the hover color of the port view.

        :param value: hover color of the port view.
        """

        self._hover_color = value
        self.update()

    @property
    def hover_border_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the hover border color of the port view.

        :return: hover border color of the port view.
        """

        return self._hover_border_color

    @hover_border_color.setter
    def hover_border_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the hover border color of the port view.

        :param value: hover border color of the port view.
        """

        self._hover_border_color = value
        self.update()

    @property
    def border_size(self) -> int:
        """
        Getter method that returns the border size of the port view.

        :return: border size of the port view.
        """

        return self._border_size

    @border_size.setter
    def border_size(self, value: int):
        """
        Setter method that sets the border size of the port view.

        :param value: border size of the port view.
        """

        self._border_size = value

    @property
    def width(self) -> float:
        """
        Getter method that returns the width of the port view.

        :return: width of the port view.
        """

        return self._width

    @width.setter
    def width(self, value: float):
        """
        Setter method that sets the width of the port view.

        :param value: width of the port view.
        """

        self._width = value

    @property
    def height(self) -> float:
        """
        Getter method that returns the height of the port view.

        :return: height of the port view.
        """

        return self._height

    @height.setter
    def height(self, value: float):
        """
        Setter method that sets the height of the port view.

        :param value: height of the port view.
        """

        self._height = value

    @property
    def locked(self) -> bool:
        """
        Getter method that returns whether the port view is locked.

        :return: whether the port view is locked.
        """

        return self._locked

    @locked.setter
    def locked(self, flag: bool):
        """
        Setter method that sets whether the port view is locked.

        :param flag: whether the port view is locked.
        """

        self._locked = flag
        tooltip = f"{self.name}: {'multi' if self.multi_connection else 'single'}"
        if flag:
            tooltip += " (L)"
        self.setToolTip(tooltip)

    @property
    def hovered(self) -> bool:
        """
        Getter method that returns whether the port view is hovered.

        :return: whether the port view is hovered.
        """

        return self._hovered

    @hovered.setter
    def hovered(self, flag: bool):
        """
        Setter method that sets whether the port view is hovered.

        :param flag: whether the port view is hovered.
        """

        self._hovered = flag

    @property
    def connected_connectors(self) -> list[ConnectorView]:
        """
        Getter method that returns the connector views for this port view.

        :return: connector views.
        """

        return self._connector_views

    @property
    def connected_ports(self) -> list[PortView]:
        """
        Getter method that returns the connected port views.

        :return: connected port views.
        """

        ports: list[PortView] = []
        port_types = {
            consts.PortType.Input.value: "output_port",
            consts.PortType.Output.value: "input_port",
        }
        for connector in self.connected_connectors:
            ports.append(getattr(connector, port_types[self.port_type]))

        return ports

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the port view in the given painter.

        :param painter: painter to paint the port view.
        :param option: style option for the port view.
        :param widget: widget to paint the port view.
        """

        painter.save()

        try:
            rect_width = self.width / 1.5
            rect_height = self.height / 1.5
            rect_x = self.boundingRect().center().x() - (rect_width / 2)
            rect_y = self.boundingRect().center().y() - (rect_height / 2)
            port_rect = QRectF(rect_x, rect_y, rect_width, rect_height)
            if self.data_type == datatypes.Exec:
                points = [
                    QPointF(
                        port_rect.left() + port_rect.width() * 0.3, port_rect.top()
                    ),  # Top right
                    QPointF(
                        port_rect.right(), port_rect.top() + port_rect.height() / 2
                    ),  # Tip
                    QPointF(
                        port_rect.left() + port_rect.width() * 0.3, port_rect.bottom()
                    ),
                ]
                arrow = QPolygonF(points)
                fill_color = (
                    QColor(*self.color)
                    if not self.connected_ports
                    else QColor(*self.border_color)
                )
                painter.setBrush(QBrush(fill_color))
                border_color = QColor(*self.border_color)
                border_width = 1.5
                if self.hovered:
                    border_color = QColor(200, 200, 255, 255)
                if self.locked:
                    border_color = QColor(150, 150, 150, 255)
                painter.setPen(QPen(border_color, border_width))
                painter.drawPolygon(arrow)
            else:
                if self.hovered:
                    color = QColor(*self.hover_color)
                    border_color = QColor(*self.hover_border_color)
                elif self.connected_connectors:
                    color = QColor(*self.active_color)
                    border_color = QColor(*self.active_color)
                else:
                    color = QColor(*self.color)
                    border_color = QColor(*self.border_color)

                pen = QPen(border_color, 1.8)
                painter.setPen(pen)
                painter.setBrush(color)
                painter.drawEllipse(port_rect)

                if self.connected_connectors and not self.hovered:
                    pass
                elif self.hovered:
                    if self.multi_connection:
                        pen = QPen(border_color, 1.4)
                        painter.setPen(pen)
                        painter.setBrush(color)
                        width = port_rect.width() / 1.8
                        height = port_rect.height() / 1.8
                    else:
                        painter.setBrush(border_color)
                        width = port_rect.width() / 3.5
                        height = port_rect.height() / 3.5
                    rect = QRectF(
                        port_rect.center().x() - width / 2,
                        port_rect.center().y() - height / 2,
                        width,
                        height,
                    )
                    painter.drawEllipse(rect)

            # if self._debug_mode:
            #     pen = QPen(QColor(255, 255, 255, 80), 0.8)
            #     pen.setStyle(Qt.DotLine)
            #     painter.setPen(pen)
            #     painter.drawRect(self.boundingRect())
        finally:
            painter.restore()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Event triggered when the item changes.

        :param change: change type.
        :param value: new value.
        :return: new value.
        """

        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._redraw_connected_connectors()

        return super().itemChange(change, value)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Event triggered when the mouse enters the port view.

        :param event: hover event.
        """

        self._hovered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Event triggered when the mouse leaves the port view.

        :param event: hover event.
        """

        self._hovered = False
        super().hoverLeaveEvent(event)

    def add_connector_view(self, connector_view: ConnectorView):
        """
        Adds a connector view to this port view.

        :param connector_view: connector view to add.
        """

        self._connector_views.append(connector_view)

    def remove_connector_view(self, connector_view: ConnectorView):
        """
        Removes a connector view from this port view.

        :param connector_view: connector view to remove.
        """

        self._connector_views.remove(connector_view)

    def connect_to(self, port_view: PortView):
        """
        Connects this port view to another port view.

        :param port_view: port view to connect to.
        """

        if not port_view:
            for connector in self.connected_connectors:
                connector.delete()
            return

        # noinspection PyTypeChecker
        scene: NodeGraphScene | None = self.scene()
        if scene:
            viewer = scene.viewer()
            viewer.establish_connection(self, port_view)

        port_view.update()
        self.update()

    def disconnect_from(self, port_view: PortView):
        """
        Disconnects this port view from another port view.

        :param port_view: port view to disconnect from.
        """

        port_types = {
            consts.PortType.Input.value: "output_port",
            consts.PortType.Output.value: "input_port",
        }

        for connector_view in self.connected_connectors:
            connected_port_view = getattr(connector_view, port_types[self.port_type])
            if connected_port_view == port_view:
                connector_view.delete()
                break

        port_view.update()
        self.update()

    def _redraw_connected_connectors(self):
        """
        Internal function that redraws the connected connectors.
        """

        if not self.connected_connectors:
            return

        for connector_view in self.connected_connectors:
            if self.port_type == consts.PortType.Input.value:
                connector_view.draw_path(self, connector_view.output_port)
            elif self.port_type == consts.PortType.Output.value:
                connector_view.draw_path(connector_view.input_port, self)

    def _update_colors(self):
        """
        Internal function that updates the colors of the port view.
        """

        if not self.data_type:
            return

        self._color = self._data_type.color.getRgb()
        self._border_color = self._data_type.color.lighter(150).getRgb()
        h, s, v, a = self._data_type.color.getHsv()
        hover_color = QColor.fromHsv(h, s, min(v + 50, 255), a)
        self._hover_color = hover_color.getRgb()
        self._hover_border_color = hover_color.lighter(150).getRgb()
        self._active_color = self._data_type.color.getRgb()


class CustomPortView(PortView):
    """
    Class that defines custom port views.
    """

    def __init__(self, painter_function: Callable, parent: NodeView):
        super().__init__(parent=parent)

        self._painter_function = painter_function

    @property
    def painter_function(self) -> Callable:
        """
        Getter method that returns the painter function.

        :return: painter function.
        """

        return self._painter_function

    @painter_function.setter
    def painter_function(self, value: Callable):
        """
        Setter method that sets the painter function.

        :param value: painter function.
        """

        self._painter_function = value

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the port view in the given painter.

        :param painter: painter to paint the port view.
        :param option: style option for the port view.
        :param widget: widget to paint the port view.
        """

        if self._painter_function:
            rect_width = self._width / 1.8
            rect_height = self._height / 1.8
            rect_x = self.boundingRect().center().x() - (rect_width / 2)
            rect_y = self.boundingRect().center().y() - (rect_height / 2)
            port_rect = QRectF(rect_x, rect_y, rect_width, rect_height)
            port_info = port_painter.PortPaintData(
                port_type=self.port_type,
                color=self.color,
                border_color=self.border_color,
                multi_connection=self.multi_connection,
                connected=bool(self.connected_connectors),
                hovered=self.hovered,
                locked=self.locked,
            )
            self._painter_function(painter, port_rect, port_info)
        else:
            super().paint(painter, option, widget)
