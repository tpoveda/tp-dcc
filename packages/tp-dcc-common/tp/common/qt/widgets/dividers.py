#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt splitter widgets
"""

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QFrame

from tp.common.qt import dpi
from tp.common.qt.widgets import labels, layouts


def divider(text='', orientation=Qt.Horizontal, alignment=Qt.AlignLeft, parent=None):
    """
    Returns divider widget

    :param str text: optional divider text.
    :param Qt.Orientation orientation: optional divider orientation.
    :param Qt.Alignment alignment: optional divider alignment.
    :param QWidget parent: optional parent widget.
    :return: divider widget instance.
    :rtype: Divider
    """

    new_divider = Divider(text=text, orientation=orientation, alignment=alignment, parent=parent)
    return new_divider


class Divider(QWidget, object):

    _ALIGN_MAP = {
        Qt.AlignCenter: 50,
        Qt.AlignLeft: 20,
        Qt.AlignRight: 80
    }

    def __init__(self, text=None, shadow=True, orientation=Qt.Horizontal, alignment=Qt.AlignLeft, parent=None):
        """
        Basic standard splitter with optional text
        :param str text: Optional text to include as title in the splitter
        :param bool shadow: True if you want a shadow above the splitter
        :param Qt.Orientation orientation: Orientation of the splitter
        :param Qt.Align alignment: Alignment of the splitter
        :param QWidget parent: Parent of the splitter
        """

        super(Divider, self).__init__(parent=parent)

        self._orient = orientation
        self._text = None

        main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        self._label = labels.BaseLabel().strong(True)

        first_line = QFrame()
        self._second_line = QFrame()

        main_layout.addWidget(first_line)
        main_layout.addWidget(self._label)
        main_layout.addWidget(self._second_line)

        if orientation == Qt.Horizontal:
            first_line.setFrameShape(QFrame.HLine)
            first_line.setFrameShadow(QFrame.Sunken)
            first_line.setFixedHeight(2) if shadow else first_line.setFixedHeight(1)
            self._second_line.setFrameShape(QFrame.HLine)
            self._second_line.setFrameShadow(QFrame.Sunken)
            self._second_line.setFixedHeight(2) if shadow else self._second_line.setFixedHeight(1)
        else:
            self._label.setVisible(False)
            self._second_line.setVisible(False)
            first_line.setFrameShape(QFrame.VLine)
            first_line.setFrameShadow(QFrame.Plain)
            self.setFixedWidth(2)
            first_line.setFixedWidth(2) if shadow else first_line.setFixedWidth(1)

        main_layout.setStretchFactor(first_line, self._ALIGN_MAP.get(alignment, 50))
        main_layout.setStretchFactor(self._second_line, 100 - self._ALIGN_MAP.get(alignment, 50))

        self.set_text(text)

    @classmethod
    def left(cls, text=''):
        """
        Creates an horizontal splitter with text at left
        :param text:
        :return:
        """

        return cls(text, alignment=Qt.AlignLeft)

    @classmethod
    def right(cls, text=''):
        """
        Creates an horizontal splitter with text at right
        :param text:
        :return:
        """

        return cls(text, alignment=Qt.AlignRight)

    @classmethod
    def center(cls, text=''):
        """
        Creates an horizontal splitter with text at center
        :param text:
        :return:
        """

        return cls(text, alignment=Qt.AlignCenter)

    @classmethod
    def vertical(cls):
        """
        Creates a vertical splitter
        :return:
        """

        return cls(orientation=Qt.Vertical)

    def get_text(self):
        """
        Returns splitter text
        :return: str
        """

        return self._label.text()

    def set_text(self, text):
        """
        Sets splitter text
        :param str text:
        """

        self._text = text
        self._label.setText(text)
        if self._orient == Qt.Horizontal:
            self._label.setVisible(bool(text))
            self._second_line.setVisible(bool(text))


class DividerLayout(layouts.HorizontalLayout, object):
    """
    Basic splitter to separate layouts
    """

    def __init__(self):
        super(DividerLayout, self).__init__(margins=(40, 2, 40, 2))

        splitter = Divider(shadow=False)
        splitter.setFixedHeight(2)

        self.addWidget(splitter)


def get_horizontal_separator_widget(max_width=60, parent=None):
    """
    Returns vertical separator widget
    :param max_width: int, maximum height for the separator
    :param parent: QWidget or None, parent widget
    :return: QWidget
    """

    v_div_w = QWidget(parent=parent)
    v_div_l = layouts.VerticalLayout(spacing=0, margins=(5, 5, 5, 5))
    v_div_l.setAlignment(Qt.AlignLeft)
    v_div_w.setLayout(v_div_l)
    v_div = QFrame(parent=v_div_w)
    v_div.setObjectName('dividerSeparator')     # ID selector used by style
    v_div.setMaximumHeight(dpi.dpi_scale(max_width))
    v_div.setFrameShape(QFrame.HLine)
    v_div.setFrameShadow(QFrame.Sunken)
    v_div_l.addWidget(v_div)

    return v_div_w


def get_vertical_separator_widget(max_height=30, parent=None):
    """
    Returns horizontal separator widget
    :param max_height: int, maximum height for the separator
    :param parent: QWidget or None, parent widget
    :return: QWidget
    """

    h_div_w = QWidget(parent=parent)
    h_div_l = layouts.VerticalLayout(spacing=0, margins=(5, 5, 5, 5))
    h_div_l.setAlignment(Qt.AlignLeft)
    h_div_w.setLayout(h_div_l)
    h_div = QFrame(parent=h_div_w)
    h_div.setObjectName('dividerSeparator')         # ID selector used by style
    h_div.setMaximumHeight(dpi.dpi_scale(max_height))
    h_div.setFrameShape(QFrame.VLine)
    h_div.setFrameShadow(QFrame.Sunken)
    h_div_l.addWidget(h_div)

    return h_div_w
