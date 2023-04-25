#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different graphic items
"""

from Qt.QtCore import Qt, Signal, QObject, QPoint, QPointF
from Qt.QtWidgets import QGraphicsItem
from Qt.QtGui import QColor


class BaseItemCommunicator(QObject, object):
    sendCommandData = Signal(str, list, list, list, str)
    itemChanged = Signal(str)
    sizeChanged = Signal()
    redefineMember = Signal(QGraphicsItem)
    changeMember = Signal(QGraphicsItem, str, bool, str)
    editRemote = Signal(QGraphicsItem)
    mousePressed = Signal()
    mouseReleased = Signal()
    aboutToRemove = Signal(QGraphicsItem)


class BaseGraphicsItem(QGraphicsItem, object):
    """
    Base class for graphics items
    """

    itemChanged = Signal()
    itemDeleted = Signal()

    def __init__(self, parent=None, **kwargs):
        QGraphicsItem.__init__(self, parent=parent)

        self.enabled = kwargs.get('enabled', True)
        self.color = kwargs.get('color', QColor(31, 32, 33, 255))
        self.disabled_color = kwargs.get('disabled_color', QColor(125, 125, 125, 255))
        self.selected_color = kwargs.get('selected_color', QColor(30, 35, 40, 255))
        self.disabled_border_width = kwargs.get('disabled_border_width', 1.5)
        self.selected_border_width = kwargs.get('selected_border_width', 1.5)
        self.disabled_border_color = kwargs.get('disabled_border_color', QColor(40, 40, 40, 255))
        self.selected_border_color = kwargs.get('selected_border_color', QColor(250, 210, 90, 255))
        self.disabled_shadow_color = kwargs.get('disabled_shadow_color', QColor(35, 35, 35, 60))
        self.selected_shadow_color = kwargs.get('selected_shadow_color', QColor(105, 55, 0, 60))
        self.disabled_border_style = kwargs.get('disabled_border_style', Qt.DashDotLine)
        self.selected_border_style = kwargs.get('selected_border_style', Qt.DashLine)

        self._border_width = kwargs.get('border_width', 1.5)
        self._shadow_color = kwargs.get('shadow_color', QColor(0, 0, 0, 60))
        self._border_color = kwargs.get('border_color', QColor(10, 10, 10, 255))
        self._border_type = kwargs.get('border_type', Qt.SolidLine)

        self._current_pos = QPointF(0, 0)
        self._new_pos = QPointF(0, 0)

        self._width = kwargs.get('width', 120)
        self._height = kwargs.get('height', 40)
        self._sizes = [0, 0, self._width, self._height, 7, 7]  # [x, y, width, height, radius_x, radius_x]
        self._is_hovered = False

        self._render_effects = True

    @property
    def enabled(self):
        return self.isEnabled()

    @enabled.setter
    def enabled(self, is_enabled):
        self.setEnabled(is_enabled)

    @property
    def selected(self):
        return self.isSelected()

    @selected.setter
    def selected(self, is_selected):
        self.setSelected(is_selected)

    @property
    def hovered(self):
        return self._is_hovered

    @hovered.setter
    def hovered(self, is_hovered):
        self._is_hovered = is_hovered

    @property
    def position(self):
        return (self.pos().x(), self.pos().y())

    @position.setter
    def position(self, new_position):
        if type(new_position) in [list, tuple]:
            self.setPos(QPointF(new_position[0], new_position[1]))
        elif type(new_position) in [QPoint, QPointF]:
            self.setPos(new_position)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, new_width):
        self._width = new_width
        self._sizes[2] = new_width

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, new_height):
        self._height = new_height
        self._sizes[3] = new_height

    @property
    def background_color(self):
        if not self.enabled:
            return self.disabled_color
        if self.selected:
            # return QColor(*[255, 183, 44])
            return self.selected_color
        if self.hovered:
            base_color = QColor(self.color)
            return base_color.lighter(150)

        return QColor(self.color)

    @property
    def border_width(self):
        if not self.enabled:
            return self.disabled_border_width
        if self.selected:
            return self.selected_border_width

        return self._border_width

    @property
    def border_color(self):
        if not self.enabled:
            return self.disabled_border_color
        if self.selected:
            return self.selected_border_color

        return self._border_color

    @property
    def shadow_color(self):
        if not self.enabled:
            return self.disabled_shadow_color
        if self.selected:
            return self.selected_shadow_color

        return self._shadow_color

    @property
    def border_type(self):
        if not self.enabled:
            return self.disabled_border_style
        if self.selected:
            return self.selected_border_style

        return self._border_type

    @property
    def render_effects(self):
        return self._render_effects

    @render_effects.setter
    def render_effects(self, has_render_effects):
        self._render_effects = has_render_effects

    def mousePressEvent(self, event):
        self.update()
        QGraphicsItem.mousePressEvent(self, event)
        self._current_pos = self.pos()

    def mouseReleaseEvent(self, event):
        self.update()
        QGraphicsItem.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        self.update()
        QGraphicsItem.mouseDoubleClickEvent(self, event)

    def hoverEnterEvent(self, event):
        QGraphicsItem.hoverEnterEvent(self, event)
        self._is_hovered = True

    def hoverLeaveEvent(self, event):
        QGraphicsItem.hoverLeaveEvent(self, event)
        self._is_hovered = False
