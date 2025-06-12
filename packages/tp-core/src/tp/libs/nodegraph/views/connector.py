from __future__ import annotations

import math
import typing
from typing import Any

from Qt.QtCore import Qt, QPoint, QPointF, QLineF
from Qt.QtWidgets import (
    QWidget,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPolygonItem,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QGraphicsSceneHoverEvent,
)
from Qt.QtGui import (
    QColor,
    QPen,
    QBrush,
    QPainter,
    QPainterPath,
    QPolygonF,
    QTransform,
    QLinearGradient,
)

from . import uiconsts
from .port import PortView
from ..core import consts

if typing.TYPE_CHECKING:
    from .graph import NodeGraphView
    from .scene import NodeGraphScene


class ConnectorView(QGraphicsPathItem):
    CONNECTOR_STYLES = {
        uiconsts.CONNECTOR_DEFAULT_DRAW_TYPE: Qt.SolidLine,
        uiconsts.CONNECTOR_DASHED_DRAW_TYPE: Qt.DashLine,
        uiconsts.CONNECTOR_DOTTED_DRAW_TYPE: Qt.DotLine,
    }

    def __init__(
        self,
        input_port_view: PortView | None = None,
        output_port_view: PortView | None = None,
    ):
        super().__init__()

        self._color: tuple[int, int, int, int] = uiconsts.CONNECTOR_COLOR
        self._thickness: float = uiconsts.CONNECTOR_THICKNESS
        self._style: int = uiconsts.CONNECTOR_DEFAULT_DRAW_TYPE
        self._active: bool = False
        self._highlight: bool = False
        self._ready_to_slice: bool = False
        self._input_port_view: PortView | None = input_port_view
        self._output_port_view: PortView | None = output_port_view

        arrow_size = 6.0
        self._poly = QPolygonF()
        self._poly.append(QPointF(-arrow_size, arrow_size))
        self._poly.append(QPointF(0.0, -arrow_size * 1.5))
        self._poly.append(QPointF(arrow_size, arrow_size))
        self._dir_pointer = QGraphicsPolygonItem(self)
        self._dir_pointer.setPolygon(self._poly)
        self._dir_pointer.setFlag(QGraphicsPathItem.ItemIsSelectable, False)

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setCacheMode(uiconsts.ITEM_CACHE_MODE)
        self.setZValue(uiconsts.Z_VALUE_CONNECTOR)

        self.reset()

    def __repr__(self) -> str:
        """
        Returns a string representation of the connector view.

        :return: string representation.
        """

        in_name = self._input_port_view.name if self._input_port_view else ""
        out_name = self._output_port_view.name if self._output_port_view else ""
        return f"<{self.__module__}.{self.__class__.__name__}>({in_name}, {out_name})"

    @property
    def thickness(self) -> float:
        """
        Returns the connector thickness.

        :return: connector thickness.
        """

        return self._thickness

    @thickness.setter
    def thickness(self, value: float):
        """
        Sets the connector thickness.

        :param value: connector thickness.
        """

        self._thickness = value

    @property
    def style(self) -> int:
        """
        Returns the connector style.

        :return: connector style.
        """

        return self._style

    @style.setter
    def style(self, style: int):
        """
        Sets the connector style.

        :param style: connector style.
        """

        self._style = style

    @property
    def color(self) -> tuple[int, int, int, int]:
        """
        Returns the connector color.

        :return: connector color.
        """

        return self._color

    @color.setter
    def color(self, color: tuple[int, int, int, int]):
        """
        Sets the connector color.

        :param color: connector color.
        """

        self._color = color
        self.update()

    @property
    def active(self) -> bool:
        """
        Returns whether the connector view is active.

        :return: whether the connector view is active.
        """

        return self._active

    @property
    def highlighted(self) -> bool:
        """
        Returns whether the connector view is highlighted.

        :return: whether the connector view is highlighted.
        """

        return self._highlight

    @property
    def ready_to_slice(self) -> bool:
        """
        Returns whether the connector view is ready to slice.

        :return: whether the connector view is ready to slice.
        """

        return self._ready_to_slice

    @ready_to_slice.setter
    def ready_to_slice(self, value: bool):
        """
        Sets whether the connector view is ready to slice.

        :param value: whether the connector view is ready to slice.
        """

        if self._ready_to_slice == value:
            return
        self._ready_to_slice = value
        self.update()

    @property
    def input_port(self) -> PortView | None:
        """
        Returns the input port view.

        :return: input port view.
        """

        return self._input_port_view

    @input_port.setter
    def input_port(self, port: PortView | None):
        """
        Sets the input port view.

        :param port: input port view.
        """

        self._input_port_view = port if isinstance(port, PortView) or not port else None
        self._set_connector_style(self.color, width=2, style=self.style)

    @property
    def output_port(self) -> PortView | None:
        """
        Returns the output port view.

        :return: output port view.
        """

        return self._output_port_view

    @output_port.setter
    def output_port(self, port: PortView | None):
        """
        Sets the output port view.

        :param port: output port view.
        """

        self._output_port_view = (
            port if isinstance(port, PortView) or not port else None
        )
        self._set_connector_style(self.color, width=2, style=self.style)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Overridden QGraphicsItem itemChange method that is called when the item is changed.

        :param change: change to apply.
        :param value: value to apply.
        :return: value after the change.
        """

        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            if value:
                self.highlight()
            else:
                self.reset()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Overridden QGraphicsItem hoverEnterEvent method that is called when the item is hovered.

        :param event: event that triggered the hover.
        """

        self.activate()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Overridden QGraphicsItem hoverLeaveEvent method that is called when the item is not hovered.

        :param event: event that triggered the hover.
        """

        self.reset()
        if self.input_port and self.output_port:
            if self.input_port.node_view.selected:
                self.highlight()
            elif self.output_port.node_view.selected:
                self.highlight()
        if self.isSelected():
            self.highlight()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the connector.

        :param painter: painter to paint the connector view.
        :param option: style option for the connector view.
        :param widget: widget to paint the connector view.
        """

        painter.save()
        try:
            start = self.path().pointAtPercent(0.0)
            end = self.path().pointAtPercent(1.0)

            linear_gradient = QLinearGradient(start.x(), start.y(), end.x(), end.y())
            start_color = QColor(*self.color)
            end_color: QColor | None = None

            pen_style = self.style
            pen_width = self.thickness

            if self.is_disabled() and not self.active:
                start_color = QColor(*uiconsts.CONNECTOR_DISABLED_COLOR)
                pen_style = uiconsts.CONNECTOR_DOTTED_DRAW_TYPE
                pen_width: float = 3.0
            elif self.ready_to_slice:
                start_color = QColor(155, 0, 0, 255)
                pen_style = uiconsts.CONNECTOR_DOTTED_DRAW_TYPE
                pen_width: float = 1.5
            elif self.isSelected():
                end_color = start_color
            elif self.active:
                start_color = start_color.lighter(125)
                if pen_style == uiconsts.CONNECTOR_DOTTED_DRAW_TYPE:
                    pen_width += 1
                else:
                    pen_width += 0.35
            elif self.highlighted:
                start_color = start_color.lighter(255)
                pen_style = uiconsts.CONNECTOR_DEFAULT_DRAW_TYPE
            else:
                if self.input_port and self.output_port:
                    start_color = QColor(*self.input_port.color)
                    end_color = QColor(*self.output_port.color)
            end_color = end_color or start_color

            linear_gradient.setColorAt(0.0, start_color)
            linear_gradient.setColorAt(1.0, end_color)
            gradient_brush = QBrush(linear_gradient)

            pen = QPen(gradient_brush, pen_width)
            pen.setStyle(ConnectorView.CONNECTOR_STYLES.get(pen_style))
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.drawPath(self.path())
        finally:
            painter.restore()

    def viewer(self) -> NodeGraphView | None:
        """
        Returns the node graph view.

        :return: node graph view.
        """

        # noinspection PyTypeChecker
        scene: NodeGraphScene | None = self.scene()
        return scene.viewer() if scene else None

    def viewer_connector_style(self) -> int | None:
        """
        Returns the viewer connector style.

        :return: viewer connector style.
        """

        viewer = self.viewer()
        return viewer.connector_style if viewer else None

    def viewer_layout_direction(self) -> int | None:
        """
        Returns the viewer layout direction.

        :return: viewer layout direction.
        """

        viewer = self.viewer()
        return viewer.layout_direction if viewer else None

    def is_disabled(self) -> bool:
        """
        Returns whether the connector view is disabled.

        :return: whether the connector view is disabled.
        """

        if self._input_port_view and self._input_port_view.node_view.disabled:
            return True
        if self._output_port_view and self._output_port_view.node_view.disabled:
            return True

        return False

    def activate(self):
        """
        Activates the connector view.
        """

        self._active = True
        self._set_connector_style(
            uiconsts.CONNECTOR_ACTIVE_COLOR,
            width=3,
            style=uiconsts.CONNECTOR_DEFAULT_DRAW_TYPE,
        )

    def highlight(self):
        """
        Highlights the connector view.
        """

        self._highlight = True
        self._set_connector_style(
            uiconsts.CONNECTOR_HIGHLIGHTED_COLOR,
            width=2,
            style=uiconsts.CONNECTOR_DEFAULT_DRAW_TYPE,
        )

    def reset(self):
        """
        Resets the connector view.
        """

        self._active = False
        self._highlight = False
        self._set_connector_style(self.color, width=2, style=self.style)
        self._draw_direction_pointer()

    def set_connections(self, source_port_view: PortView, target_port_view: PortView):
        """
        Sets the connections between two ports.

        :param source_port_view: source port view.
        :param target_port_view: target port view.
        """

        ports = {
            source_port_view.port_type: source_port_view,
            target_port_view.port_type: target_port_view,
        }

        self.input_port = ports[consts.PortType.Input.value]
        self.output_port = ports[consts.PortType.Output.value]
        ports[consts.PortType.Input.value].add_connector_view(self)
        ports[consts.PortType.Output.value].add_connector_view(self)

    def port_view_from_pos(self, pos: QPointF, reverse: bool = False) -> PortView:
        """
        Returns the port view from a given position.

        :param pos: current scene position.
        :param reverse: whether to return the nearest port view.
        :return: port view.
        """

        input_port_view_pos = self.input_port.scenePos()
        output_port_view_pos = self.output_port.scenePos()
        input_distance = self._distance_between_points(input_port_view_pos, pos)
        output_distance = self._distance_between_points(output_port_view_pos, pos)
        if input_distance < output_distance:
            port_view = self.output_port if reverse else self.input_port
        else:
            port_view = self.input_port if reverse else self.output_port

        return port_view

    def draw_path(
        self,
        start_port: PortView,
        end_port: PortView | None = None,
        cursor_pos: QPoint | None = None,
    ):
        """
        Draw the path between two points.

        :param start_port: start port view.
        :param end_port: end port view.
        :param cursor_pos: cursor scene position.
        """

        if not start_port:
            return

        pos1 = start_port.scenePos()
        pos1.setX(pos1.x() + (start_port.boundingRect().width() / 2))
        pos1.setY(pos1.y() + (start_port.boundingRect().height() / 2))
        if cursor_pos:
            pos2 = cursor_pos
        elif end_port:
            pos2 = end_port.scenePos()
            pos2.setX(pos2.x() + (start_port.boundingRect().width() / 2))
            pos2.setY(pos2.y() + (start_port.boundingRect().height() / 2))
        else:
            return

        # Visibility check for connected ports. Do not draw connector i a port or node is not visible.
        if self.input_port and self.output_port:
            is_visible = all(
                [
                    self._input_port_view.isVisible(),
                    self._output_port_view.isVisible(),
                    self._input_port_view.node_view.isVisible(),
                    self._output_port_view.node_view.isVisible(),
                ]
            )
            self.setVisible(is_visible)

            # don't draw pipe if a port or node is not visible.
            if not is_visible:
                return

        line = QLineF(pos1, pos2)
        path = QPainterPath()

        direction = self.viewer_layout_direction()

        if end_port and not self.viewer().acyclic:
            if end_port.node_view == start_port.node_view:
                if direction is consts.LayoutDirection.Vertical.value:
                    self._draw_path_cycled_vertical(start_port, pos1, pos2, path)
                    self._draw_direction_pointer()
                    return
                elif direction is consts.LayoutDirection.Horizontal.value:
                    self._draw_path_cycled_horizontal(start_port, pos1, pos2, path)
                    self._draw_direction_pointer()
                    return

        path.moveTo(line.x1(), line.y1())

        if self.viewer_connector_style() == consts.ConnectorStyle.Straight.value:
            path.lineTo(pos2)
            self.setPath(path)
            self._draw_direction_pointer()
            return

        if direction is consts.LayoutDirection.Vertical.value:
            self._draw_path_vertical(start_port, pos1, pos2, path)
        elif direction is consts.LayoutDirection.Horizontal.value:
            self._draw_path_horizontal(start_port, pos1, pos2, path)

        self._draw_direction_pointer()

    def reset_path(self):
        """
        Resets the connector path.
        """

        path = QPainterPath(QPointF(0.0, 0.0))
        self.setPath(path)
        self._draw_direction_pointer()

    def intersects_with(self, point1: QPointF, point2: QPointF) -> bool:
        """
        Returns whether the connector intersects with a given point.

        :param point1: first point.
        :param point2: second point.
        :return: whether the connector intersects with a given point.
        """

        cut_path = QPainterPath(point1)
        cut_path.lineTo(point2)
        return self.path().intersects(cut_path)

    def delete(self):
        """
        Deletes the connector view.
        """

        if self._input_port_view and self._input_port_view.connected_connectors:
            self._input_port_view.remove_connector_view(self)
        if self._output_port_view and self._output_port_view.connected_connectors:
            self._output_port_view.remove_connector_view(self)

        if self.scene():
            self.scene().removeItem(self)

    def _set_connector_style(
        self, color: tuple[int, int, int, int], width: int = 2, style: int = 0
    ):
        """
        Internal function that sets connector view style.

        :param color: connector view color.
        :param width: connector view width.
        :param style: connector style to apply.
        """

        pen = self.pen()
        pen.setWidth(width)
        pen.setColor(QColor(*color))
        pen.setStyle(ConnectorView.CONNECTOR_STYLES.get(style))
        pen.setJoinStyle(Qt.MiterJoin)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.NoBrush))

        input_color = self.input_port.color if self.input_port else color
        output_color = self.output_port.color if self.output_port else color
        r = int(input_color[0] * 0.5 + output_color[0] * 0.5)
        g = int(input_color[1] * 0.5 + output_color[1] * 0.5)
        b = int(input_color[2] * 0.5 + output_color[2] * 0.5)
        pen = self._dir_pointer.pen()
        pen.setJoinStyle(Qt.MiterJoin)
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidth(width)
        pen.setColor(QColor(r, g, b))
        self._dir_pointer.setPen(pen)
        self._dir_pointer.setBrush(QColor(r, g, b).darker(200))
        self._dir_pointer.update()

    def _draw_direction_pointer(self):
        """
        Internal function that draws the direction pointer.
        """

        if not self.input_port or not self.output_port:
            self._dir_pointer.setVisible(False)
            return

        if self.is_disabled():
            if not (self._active or self._highlight):
                color = QColor(*uiconsts.CONNECTOR_DISABLED_COLOR)
                pen = self._dir_pointer.pen()
                pen.setColor(color)
                self._dir_pointer.setPen(pen)
                self._dir_pointer.setBrush(color.darker(200))

        self._dir_pointer.setVisible(True)
        start_point = self.path().pointAtPercent(0.49)
        target_point = self.path().pointAtPercent(0.51)
        radians = math.atan2(
            target_point.y() - start_point.y(), target_point.x() - start_point.x()
        )
        degrees = math.degrees(radians) - 90
        self._dir_pointer.setRotation(degrees)
        self._dir_pointer.setPos(self.path().pointAtPercent(0.5))

        cen_x = self.path().pointAtPercent(0.5).x()
        cen_y = self.path().pointAtPercent(0.5).y()
        dist = math.hypot(target_point.x() - cen_x, target_point.y() - cen_y)

        self._dir_pointer.setVisible(True)
        if dist < 0.3:
            self._dir_pointer.setVisible(False)
            return
        if dist < 1.0:
            self._dir_pointer.setScale(dist)

    def _draw_path_horizontal(
        self, start_port: PortView, pos1: QPointF, pos2: QPointF, path: QPainterPath
    ):
        """
        Internal function that draws the connector path horizontally.

        :param start_port: start port view.
        :param pos1: start position.
        :param pos2: end position.
        :param path: path to draw.
        """

        if self.viewer_connector_style() == consts.ConnectorStyle.Curved.value:
            ctr_offset_x1, ctr_offset_x2 = pos1.x(), pos2.x()
            tangent = abs(ctr_offset_x1 - ctr_offset_x2)
            max_width = start_port.node_view.boundingRect().width()
            tangent = min(tangent, max_width)
            if start_port.port_type == consts.PortType.Input.value:
                ctr_offset_x1 -= tangent
                ctr_offset_x2 += tangent
            else:
                ctr_offset_x1 += tangent
                ctr_offset_x2 -= tangent
            ctr_point1 = QPointF(ctr_offset_x1, pos1.y())
            ctr_point2 = QPointF(ctr_offset_x2, pos2.y())
            path.cubicTo(ctr_point1, ctr_point2, pos2)
            self.setPath(path)
        elif self.viewer_connector_style() == consts.ConnectorStyle.Angle.value:
            ctr_offset_x1, ctr_offset_x2 = pos1.x(), pos2.x()
            distance = abs(ctr_offset_x1 - ctr_offset_x2) / 2
            if start_port.port_type == consts.PortType.Input.value:
                ctr_offset_x1 -= distance
                ctr_offset_x2 += distance
            else:
                ctr_offset_x1 += distance
                ctr_offset_x2 -= distance
            ctr_point1 = QPointF(ctr_offset_x1, pos1.y())
            ctr_point2 = QPointF(ctr_offset_x2, pos2.y())
            path.lineTo(ctr_point1)
            path.lineTo(ctr_point2)
            path.lineTo(pos2)
            self.setPath(path)

    def _draw_path_vertical(
        self, start_port: PortView, pos1: QPointF, pos2: QPointF, path: QPainterPath
    ):
        """
        Internal function that draws the connector path vertically.

        :param start_port: start port view.
        :param pos1: start position.
        :param pos2: end position.
        :param path: path to draw.
        """

        if self.viewer_connector_style() == consts.ConnectorStyle.Curved.value:
            ctr_offset_y1, ctr_offset_y2 = pos1.y(), pos2.y()
            tangent = abs(ctr_offset_y1 - ctr_offset_y2)
            max_height = start_port.node_view.boundingRect().height()
            tangent = min(tangent, max_height)
            if start_port.port_type == consts.PortType.Input.value:
                ctr_offset_y1 -= tangent
                ctr_offset_y2 += tangent
            else:
                ctr_offset_y1 += tangent
                ctr_offset_y2 -= tangent
            ctr_point1 = QPointF(pos1.x(), ctr_offset_y1)
            ctr_point2 = QPointF(pos2.x(), ctr_offset_y2)
            path.cubicTo(ctr_point1, ctr_point2, pos2)
            self.setPath(path)
        elif self.viewer_connector_style() == consts.ConnectorStyle.Angle.value:
            ctr_offset_y1, ctr_offset_y2 = pos1.y(), pos2.y()
            distance = abs(ctr_offset_y1 - ctr_offset_y2) / 2
            if start_port.port_type == consts.PortType.Input.value:
                ctr_offset_y1 -= distance
                ctr_offset_y2 += distance
            else:
                ctr_offset_y1 += distance
                ctr_offset_y2 -= distance
            ctr_point1 = QPointF(pos1.x(), ctr_offset_y1)
            ctr_point2 = QPointF(pos2.x(), ctr_offset_y2)
            path.lineTo(ctr_point1)
            path.lineTo(ctr_point2)
            path.lineTo(pos2)
            self.setPath(path)

    def _draw_path_cycled_horizontal(
        self, start_port: PortView, pos1: QPointF, pos2: QPointF, path: QPainterPath
    ):
        """
        Internal function that draws connector horizontally around node if connection is acyclic.

        :param start_port: start port view.
        :param pos1: start position.
        :param pos2: end position.
        :param path: path to draw.
        """

        padding = 40
        node_rect = start_port.node_view.boundingRect()
        ptype = start_port.port_type
        start_pos = pos1 if ptype == consts.PortType.Input.value else pos2
        end_pos = pos2 if ptype == consts.PortType.Input.value else pos1
        left = end_pos.x() + padding
        right = start_pos.x() - padding
        path.moveTo(start_pos)
        path.lineTo(right, start_pos.y())
        path.lineTo(right, end_pos.y() + node_rect.bottom())
        path.lineTo(left, end_pos.y() + node_rect.bottom())
        path.lineTo(left, end_pos.y())
        path.lineTo(end_pos)
        self.setPath(path)

    def _draw_path_cycled_vertical(
        self, start_port: PortView, pos1: QPointF, pos2: QPointF, path: QPainterPath
    ):
        """
        Internal function that draws connector vertically around node if connection is acyclic.

        :param start_port: start port view.
        :param pos1: start position.
        :param pos2: end position.
        :param path: path to draw.
        """

        padding = 40
        node_rect = start_port.node_view.boundingRect()
        ptype = start_port.port_type
        start_pos = pos1 if ptype == consts.PortType.Input.value else pos2
        end_pos = pos2 if ptype == consts.PortType.Input.value else pos1
        top = start_pos.y() - padding
        bottom = end_pos.y() + padding
        path.moveTo(end_pos)
        path.lineTo(end_pos.x(), bottom)
        path.lineTo(end_pos.x() + node_rect.right(), bottom)
        path.lineTo(end_pos.x() + node_rect.right(), top)
        path.lineTo(start_pos.x(), top)
        path.lineTo(start_pos)
        self.setPath(path)

    @staticmethod
    def _distance_between_points(p1: QPoint, p2: QPoint) -> float:
        """
        Returns the distance between two points.

        :param p1: first point.
        :param p2: second point.
        :return: distance between two points.
        """

        x = math.pow((p2.x() - p1.x()), 2)
        y = math.pow((p2.y() - p1.y()), 2)
        return math.sqrt(x + y)


class LiveConnectorView(ConnectorView):
    """
    Class that defines a live connector view.
    """

    def __init__(self):
        super().__init__()

        self._shift_selected: bool = False

        # self.color = uiconsts.CONNECTOR_ACTIVE_COLOR
        # self.color = [255, 0, 0]
        self.style = uiconsts.CONNECTOR_DASHED_DRAW_TYPE
        self._set_connector_style(self.color, width=3, style=self.style)

        self._index_pointer = LiveConnectorPolygonItem(self)
        self._index_pointer.setPolygon(self._poly)
        self._index_pointer.setBrush(QColor(*self.color).darker(300))
        pen = self._index_pointer.pen()
        pen.setWidth(self.pen().width())
        pen.setColor(self.pen().color())
        pen.setJoinStyle(Qt.MiterJoin)
        self._index_pointer.setPen(pen)

        color = self.pen().color()
        color.setAlpha(80)
        self._index_text = QGraphicsTextItem(self)
        self._index_text.setDefaultTextColor(QColor(255, 255, 255))
        font = self._index_text.font()
        font.setPointSize(7)
        self._index_text.setFont(font)

        self.setZValue(uiconsts.Z_VALUE_NODE_WIDGET + 1)

    @property
    def shift_selected(self) -> bool:
        """
        Returns whether the connector view is shift selected.

        :return: whether the connector view is shift selected.
        """

        return self._shift_selected

    @shift_selected.setter
    def shift_selected(self, value: bool):
        """
        Sets whether the connector view is shift selected.

        :param value: whether the connector view is shift selected.
        """

        self._shift_selected = value

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Overridden QGraphicsItem hoverEnterEvent method that is called when the item is hovered.

        :param event: event that triggered the hover.
        """

        # Hack to avoid connector to lose its styling when another connector is selected.
        QGraphicsPathItem.hoverEnterEvent(self, event)

    def draw_path(
        self,
        start_port: PortView,
        end_port: PortView | None = None,
        cursor_pos: QPointF | None = None,
        color: tuple[int, int, int] | None = None,
    ):
        """
        Draw the path between two points.

        :param start_port: start port view.
        :param end_port: end port view.
        :param cursor_pos: cursor scene position.
        :param color: optional arrow index pointer color.
        """

        super().draw_path(start_port, end_port, cursor_pos)
        self.draw_index_pointer(start_port, cursor_pos, color=color)

    def draw_index_pointer(
        self,
        start_port: PortView,
        cursor_pos: QPointF,
        color: tuple[int, int, int] | None = None,
    ):
        """
        Updates the index pointer arrow position and direction when the live connector is redrawn.

        :param start_port: start port view.
        :param cursor_pos: cursor scene position.
        :param color: optional arrow index pointer color.
        """

        text_rect = self._index_text.boundingRect()
        transform = QTransform()
        transform.translate(cursor_pos.x(), cursor_pos.y())
        if self.viewer_layout_direction() is consts.LayoutDirection.Vertical.value:
            text_pos = (
                cursor_pos.x() + (text_rect.width() / 2.5),
                cursor_pos.y() - (text_rect.height() / 2),
            )
            if start_port.port_type == consts.PortType.Output.value:
                transform.rotate(180)
        else:
            text_pos = (
                cursor_pos.x() - (text_rect.width() / 2),
                cursor_pos.y() - (text_rect.height() * 1.25),
            )
            if start_port.port_type == consts.PortType.Input.value:
                transform.rotate(-90)
            else:
                transform.rotate(90)
        self._index_text.setPos(*text_pos)
        self._index_text.setPlainText("{}".format(start_port.name))

        self._index_pointer.setPolygon(transform.map(self._poly))

        pen_color = QColor(*self.color)

        pen = self._index_pointer.pen()
        pen.setColor(pen_color)
        self._index_pointer.setBrush(pen_color.darker(300))
        self._index_pointer.setPen(pen)


class LiveConnectorPolygonItem(QGraphicsPolygonItem):
    """
    Class that defines a live connector polygon item.
    """

    def __init__(self, parent: LiveConnectorView):
        super().__init__(parent=parent)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the item.

        :param painter: painter to paint the connector view.
        :param option: style option for the connector view.
        :param widget: widget to paint the connector view.
        """

        painter.save()
        try:
            painter.setBrush(self.brush())
            painter.setPen(self.pen())
            painter.drawPolygon(self.polygon())
        finally:
            painter.restore()
