#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base classes for graphic widgets
"""

from Qt.QtCore import QRectF, QSizeF
from Qt.QtWidgets import QGraphicsWidget
from Qt.QtGui import QColor, QBrush, QPainterPath


class BaseGraphicWidget(QGraphicsWidget, object):

    DEFAULT_GRAPHIC_WIDGET_COLOR = QColor(0, 100, 0, 255)
    DEFAULT_GRAPHIC_WIDGET_BORDER_COLOR = QColor(0, 0, 0, 255)

    def __init__(self, name, color=DEFAULT_GRAPHIC_WIDGET_COLOR, border_color=DEFAULT_GRAPHIC_WIDGET_BORDER_COLOR):
        super(BaseGraphicWidget, self).__init__()

        self._name = name.strip().replace(' ', '_')
        self._color = color
        self._border_color = border_color
        self._hovered = False

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = color

    def get_border_color(self):
        return self._border_color

    def set_border_color(self, border_color):
        self._border_color = border_color

    def set_hovered(self, flag):
        self._hovered = flag

    def get_hovered(self):
        return self._hovered

    name = property(get_name, set_name)
    color = property(get_color, set_color)
    border_color = property(get_border_color, set_border_color)
    hovered = property(get_hovered, set_hovered)

    def hoverEnterEvent(self, *args, **kwargs):
        self.update()
        self._hovered = True

    def hoverLeaveEvent(self, *args, **kwargs):
        self.update()
        self._hovered = False


class EllipseWidget(BaseGraphicWidget, object):
    def __init__(self, name, width, height, color=QColor(0, 100, 0, ), border_color=QColor(0, 0, 0, 255)):
        super(EllipseWidget, self).__init__(name=name, color=color, border_color=border_color)

        self._width = width
        self._height = height

    def get_width(self):
        return self._width

    def set_width(self, width):
        self._width = width

    def get_height(self):
        return self._height

    def set_height(self, height):
        self._height = height

    width = property(get_width, set_width)
    height = property(get_height, set_height)

    def boundingRect(self):
        return QRectF(0, -0.5, self._width, self._height)

    def sizeHint(self, which, constraint):
        return QSizeF(self._width, self._height)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def paint(self, painter, option, widget):

        background_rect = self.boundingRect()
        if self.hovered:
            painter.setBrush(QBrush(self.color.lighter(160)))
        else:
            painter.setBrush(QBrush(self.color))
        painter.drawEllipse(background_rect)
