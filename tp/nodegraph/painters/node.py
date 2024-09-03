from __future__ import annotations

import typing

from Qt.QtCore import Qt, QRectF
from Qt.QtWidgets import QWidget, QStyleOptionGraphicsItem
from Qt.QtGui import QColor, QPen, QPainter, QPainterPath

if typing.TYPE_CHECKING:
    from ..views.node import AbstractNodeView, NodeView


class AbstractNodePainter:
    """
    Abstract class that defines a node painter.
    """

    def __init__(self, view: AbstractNodeView | NodeView, debug_mode: bool = False):
        super().__init__()

        self._view = view
        self._margin = 0.5
        self._radius = 3
        self._debug_mode = debug_mode

    @property
    def border_width(self) -> float:
        """
        Getter method that returns the border width of the node view.

        :return: border width of the node view.
        """

        return 0.4 if not self._view.isSelected() else 1.2

    @property
    def margin(self) -> float:
        """
        Getter method that returns the margin of the node view background.

        :return: margin of the node view background.
        """

        return self._margin * self.border_width

    def paint_horizontal(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the node view in the given painter.

        :param painter: painter to paint the node view.
        :param option: style option for the node view.
        :param widget: widget to paint the node view.
        """

        painter.save()
        try:
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.NoBrush)
            self._paint_background(painter, option, widget)
            self._paint_custom(painter, option, widget)

            border_width = self.border_width
            border_color = QColor(*self._view.border_color)
            background_rect = self._background_rect()
            background_path = QPainterPath()
            show_details = self._view.viewer().show_details

            pen = QPen(border_color, border_width)
            pen.setCosmetic(show_details and self._view.viewer().zoom_value() < 0.0)
            if show_details:
                background_path.addRoundedRect(
                    background_rect, self._radius, self._radius
                )
            else:
                background_path.addRect(background_rect)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(pen)

            if self._debug_mode:
                self._paint_debug_mode(painter)
            else:
                painter.drawPath(background_path)

        finally:
            painter.restore()

    def _background_rect(self) -> QRectF:
        """
        Internal function that returns the background rectangle of the node view.

        :return: rectangle used to define node rectangle.
        """

        margin = self.margin

        background_rect = QRectF(
            margin,
            margin,
            self._view.width - (margin * 2),
            self._view.height - (margin * 2),
        )

        return background_rect

    def _paint_background(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Internal function that paints the background of the node view.

        :param painter: painter to paint the node view.
        :param option: style option for the node view.
        :param widget: widget to paint the node view.
        """

        background_color = QColor(*self._view.color)
        show_details = self._view.viewer().show_details

        if self._view.isSelected():
            background_color = background_color.lighter(150)

        background_rect = self._background_rect()

        painter.setBrush(background_color)
        painter.drawRoundedRect(
            background_rect, self._radius, self._radius
        ) if show_details else painter.drawRect(background_rect)

    def _paint_custom(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Internal function that paints the custom of the node view.

        :param painter: painter to paint the node view.
        :param option: style option for the node view.
        :param widget: widget to paint the node view.
        """

        pass

    def _paint_debug_mode(self, painter: QPainter):
        """
        Internal function that paints the debug mode of the node view.

        :param painter: painter to paint the node view.
        """

        painter.setPen(QPen(Qt.blue, 0.75))
        painter.drawRect(self._background_rect())


class NodePainter(AbstractNodePainter):
    """
    Class that defines node painter.
    """

    def __init__(self, view: NodeView, debug_mode: bool = False):
        super().__init__(view=view, debug_mode=debug_mode)

    def _paint_custom(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Internal function that paints the custom of the node view.

        :param painter: painter to paint the node view.
        :param option: style option for the node view.
        :param widget: widget to paint the node view.
        """

        self._paint_label(painter, option, widget)

    def _paint_debug_mode(self, painter: QPainter):
        """
        Internal function that paints the debug mode of the node view.

        :param painter: painter to paint the node view.
        """

        super()._paint_debug_mode(painter)

        painter.setPen(QPen(Qt.green, 0.75))
        painter.drawRect(self._label_rect())

    def _paint_label(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        show_details = self._view.viewer().show_details
        title_color = QColor(*self._view.title_color)

        if self._view.isSelected():
            title_color = title_color.lighter(150)

        label_rect = self._label_rect()

        border_path = QPainterPath()
        border_path.setFillRule(Qt.WindingFill)

        if show_details:
            border_path.moveTo(label_rect.left() + self._radius, label_rect.top())
            border_path.lineTo(label_rect.right() - self._radius, label_rect.top())
            border_path.arcTo(
                QRectF(
                    label_rect.right() - 2 * self._radius,
                    label_rect.top(),
                    2 * self._radius,
                    2 * self._radius,
                ),
                90,
                -90,
            )
            border_path.lineTo(label_rect.right(), label_rect.bottom())
            border_path.lineTo(label_rect.left(), label_rect.bottom())
            border_path.lineTo(label_rect.left(), label_rect.top() + self._radius)
            border_path.arcTo(
                QRectF(
                    label_rect.left(),
                    label_rect.top(),
                    2 * self._radius,
                    2 * self._radius,
                ),
                180,
                -90,
            )
            border_path.closeSubpath()
        else:
            border_path.addRect(label_rect)

        self._view.update_ports_text_visibility()

        painter.setBrush(title_color)
        painter.fillPath(border_path, painter.brush())

    def _label_rect(self) -> QRectF:
        """
        Internal function that returns the label rectangle of the node view.

        :return: rectangle used to define node label rectangle.
        """

        margin = self.margin

        label_rect = QRectF(
            margin, margin, self._view.width - (margin * 2), self._view.title_height
        )

        return label_rect
