#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different graphic objects
"""

from tpDcc.libs.python.decorators import accepts, returns

from Qt.QtCore import Qt
from Qt.QtWidgets import QGraphicsObject
from Qt.QtGui import QColor, QFont


class BaseObjectItem(QGraphicsObject, object):
    """
    Base graphics object class
    """

    _DEFAULT_OBJECT_COLOR = QColor(150, 150, 150, 255)
    _DEFAULT_OBJECT_BORDER_COLOR = QColor(50, 50, 50, 255)

    def __init__(self, name, color=_DEFAULT_OBJECT_COLOR, border_color=_DEFAULT_OBJECT_BORDER_COLOR, parent=None):
        super(BaseObjectItem, self).__init__(parent)

        self._name = name
        self._children = list()
        self._parent = parent
        self._color = color
        self._border_color = border_color
        self._font = QFont('Tahoma', 9.0)
        self._font_color = QColor(Qt.black)
        self._is_hovered = False
        self._is_double_clicked = False

        if parent:
            self.setParent(parent)
            parent.add_child(self)      # TODO: Remove this?

    @returns(str)
    def get_name(self):
        return self._name

    @accepts(str)
    def set_name(self, value):
        self._name = value

    def get_color(self):
        return self._color

    def set_color(self, value):
        new_color = value
        if value is None:
            new_color = self._DEFAULT_OBJECT_COLOR
        elif isinstance(value, (list, tuple)):
            new_color = QColor(*value)
        assert isinstance(value, QColor), 'color control "%s" is not valid!'
        self._color = new_color
        self.update()

    def get_border_color(self):
        return self._border_color

    def set_border_color(self, value):
        new_color = value
        if value is None:
            new_color = self._DEFAULT_OBJECT_BORDER_COLOR
        elif isinstance(value, (list, tuple)):
            new_color = QColor(*value)
        assert isinstance(value, QColor), 'border color control "%s" is not valid'
        self._border_color = new_color
        self.update()

    @returns(QFont)
    def get_font(self):
        return self._font

    @accepts(QFont)
    def set_font(self, value):
        self._font = value
        self.update()

    @returns(QColor)
    def get_font_color(self):
        return self._font_color

    @accepts(QColor)
    def set_font_color(self, value):
        self._font_color = value
        self.updaet()

    @returns(bool)
    def get_is_hovered(self):
        return self._is_hovered

    @accepts(bool)
    def set_is_hovered(self, value):
        self._is_hovered = value

    @returns(bool)
    def get_is_double_clicked(self):
        return self._is_double_clicked

    @accepts(bool)
    def set_is_double_clicked(self, value):
        self._is_double_clicked = value

    name = property(get_name, set_name)
    color = property(get_color, set_color)
    border_color = property(get_border_color, set_border_color)
    font = property(get_font, set_font)
    font_color = property(get_font_color, set_font_color)
    is_hovered = property(get_is_hovered, set_is_hovered)
    is_double_clicked = property(get_is_double_clicked, set_is_double_clicked)

    def add_child(self, child):
        self._children.append(child)

    def child(self, row):
        """
        Returns a child control located by its index inside the hierarchy
        :param row: int, nidex
        :return: PickerControl, child of the current control
        """

        try:
            return self._children[row]
        except Exception as e:
            return None

    def child_count(self):
        """
        Returns the number of children that this control has
        :return: int, number of childrem
        """

        return len(self._children)

    def row(self):
        """
        Returns the index of this node relative to its parent
        :return: index of this node or -1 if this a parent node
        """

        if self._parent is not None:
            return self._parent._children.index(self)

    def log(self, tab_level=1):
        """
        Outputs information related with this control such as hierarchy, etc
        """

        output = ''
        tab_level += 1
        for i in range(tab_level):
            output += '\t'
        output += "/------" + self._name + '\n'
        for child in self._children:
            output += child.log(tab_level)
        tab_level -= 1
        output += '\n'
        return output

    def properties(self, check_settable=True):
        all_classes = self.__class__.mro()
        result_dict = dict()
        for cls in all_classes:
            for k, v in cls.__dict__.items():
                if isinstance(v, property):
                    if check_settable and v.fset is None:
                        continue
                    result_dict[k] = getattr(self, k)
        return result_dict

    def hoverEnterEvent(self, event):
        super(BaseObjectItem, self).hoverEnterEvent(event)
        self._is_hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        super(BaseObjectItem, self).hoverLeaveEvent(event)
        self._is_hovered = False
        self.update()


class BaseDropItem(BaseObjectItem, object):
    def __init__(self, name='New_Item', color=QColor(), parent=None):
        super(BaseDropItem, self).__init__(name=name, color=color, parent=parent)

        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)
