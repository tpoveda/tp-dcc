#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt splitter widget implementation
"""

from __future__ import annotations

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QFrame, QLabel, QHBoxLayout

from tp.common.qt import consts, dpi
from tp.common.qt.widgets import layouts, labels


def divider(
        text: str = '', orientation: Qt.Orientation = Qt.Horizontal, alignment: Qt.AlignmentFlag = Qt.AlignLeft,
        shadow: bool = True, parent: QWidget | None = None) -> Divider:
    """
    Returns divider widget

    :param str text: optional divider text.
    :param Qt.Orientation orientation: optional divider orientation.
    :param Qt.AlignmentFlag alignment: optional divider alignment.
    :param bool shadow: whether divider should have a shadow
    :param QWidget parent: optional parent widget.
    :return: divider widget instance.
    :rtype: Divider
    """

    new_divider = Divider(text=text, orientation=orientation, shadow=shadow, alignment=alignment, parent=parent)
    return new_divider


def horizontal_separator_widget(max_width: int = 60, parent: QWidget | None = None) -> QWidget:
    """
    Returns vertical separator widget

    :param int max_width: maximum height for the separator
    :param QWidget or None parent: parent widget
    :return: vertical seaprator widget
    :rtype: QWidget
    """

    v_div_w = QWidget(parent=parent)
    main_layout = layouts.vertical_layout(spacing=0, margins=(5, 5, 5, 5), alignment=Qt.AlignLeft, parent=v_div_w)
    v_div = QFrame(parent=v_div_w)
    v_div.setObjectName('dividerSeparator')     # ID selector used by style
    v_div.setMaximumHeight(dpi.dpi_scale(max_width))
    v_div.setFrameShape(v_div.HLine)
    v_div.setFrameShadow(v_div.Sunken)
    main_layout.addWidget(v_div)

    return v_div_w


def vertical_separator_widget(max_height: int = 30, parent: QWidget | None = None) -> QWidget:
    """
    Returns horizontal separator widget

    :param int max_height: maximum height for the separator
    :param QWidget or None parent: parent widget
    :return: horizontal seaprator widget
    :rtype: QWidget
    """

    h_div_w = QWidget(parent=parent)
    main_layout = layouts.vertical_layout(spacing=0, margins=(5, 5, 5, 5), alignment=Qt.AlignLeft, parent=h_div_w)
    main_layout.setAlignment(Qt.AlignLeft)
    h_div = QFrame(parent=h_div_w)
    h_div.setObjectName('dividerSeparator')         # ID selector used by style
    h_div.setMaximumHeight(dpi.dpi_scale(max_height))
    h_div.setFrameShape(h_div.VLine)
    h_div.setFrameShadow(h_div.Sunken)
    main_layout.addWidget(h_div)

    return h_div_w


class Divider(QWidget, dpi.DPIScaling):
    """
    Basic standard splitter with optional text.
    """

    textChanged = Signal(str)

    _ALIGN_MAP = {
        Qt.AlignCenter: 50,
        Qt.AlignLeft: 20,
        Qt.AlignRight: 80
    }

    def __init__(
            self, text: str | None = None, shadow: bool = True, orientation: Qt.Orientation = Qt.Horizontal,
            alignment: Qt.AlignmentFlag = Qt.AlignLeft, parent: QWidget | None = None):
        """
        :param str text: Optional text to include as title in the splitter.
        :param bool shadow: True if you want a shadow above the splitter.
        :param Qt.Orientation orientation: Orientation of the splitter.
        :param Qt.AlignmentFlag alignment: Alignment of the splitter.
        :param QWidget or None parent: Parent of the splitter.
        """

        super().__init__(parent=parent)

        self._orient = orientation
        self._text = None

        main_layout = layouts.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        self._label = labels.BaseLabel(parent=self).strong(True)

        self._first_line = QFrame()
        self._second_line = QFrame()

        main_layout.addWidget(self._first_line)
        main_layout.addWidget(self._label)
        main_layout.addWidget(self._second_line)

        if orientation == Qt.Horizontal:
            self._first_line.setFrameShape(QFrame.HLine)
            self._first_line.setFrameShadow(QFrame.Sunken)
            self._first_line.setFixedHeight(2) if shadow else self._first_line.setFixedHeight(1)
            self._second_line.setFrameShape(QFrame.HLine)
            self._second_line.setFrameShadow(QFrame.Sunken)
            self._second_line.setFixedHeight(2) if shadow else self._second_line.setFixedHeight(1)
        else:
            self._label.setVisible(False)
            self._second_line.setVisible(False)
            self._first_line.setFrameShape(QFrame.VLine)
            self._first_line.setFrameShadow(QFrame.Sunken)
            self.setFixedWidth(2)
            self._first_line.setFixedWidth(2) if shadow else self._first_line.setFixedWidth(1)

        main_layout.setStretchFactor(self._first_line, self._ALIGN_MAP.get(alignment, 50))
        main_layout.setStretchFactor(self._second_line, 100 - self._ALIGN_MAP.get(alignment, 50))

        self.set_text(text)

    @classmethod
    def left(cls, text: str = '') -> Divider:
        """
        Creates a horizontal splitter with text at left.

        :param str text: divider left text.
        :return: Divider instance.
        :rtype: Divider
        """

        return cls(text, alignment=Qt.AlignLeft)

    @classmethod
    def right(cls, text: str = '') -> Divider:
        """
        Creates a horizontal splitter with text at right

        :param str text: divider right text.
        :return: Divider instance.
        :rtype: Divider
        """

        return cls(text, alignment=Qt.AlignRight)

    @classmethod
    def center(cls, text: str = '') -> Divider:
        """
        Creates a horizontal splitter with text at center.

        :param str text: divider center text.
        :return: Divider instance.
        :rtype: Divider
        """

        return cls(text, alignment=Qt.AlignCenter)

    @classmethod
    def vertical(cls) -> Divider:
        """
        Creates a vertical splitter.

        :return: Divider instance.
        :rtype: Divider
        """

        return cls(orientation=Qt.Vertical)

    def text(self) -> str:
        """
        Returns splitter text.

        :return: splitter text.
        :rtype: str
        """

        return self._label.text()

    def set_text(self, text: str):
        """
        Sets splitter text.

        :param str text: splitter text.
        """

        self._text = text
        self._label.setText(text)
        if self._orient == Qt.Horizontal:
            self._label.setVisible(bool(text))
            self._second_line.setVisible(bool(text))

        self.textChanged.emit(self._text)


class DividerLayout(QHBoxLayout, dpi.DPIScaling):
    """
    Basic splitter to separate layouts
    """

    def __init__(self):
        super(DividerLayout, self).__init__(margins=(40, 2, 40, 2))

        splitter = Divider(shadow=False)
        splitter.setFixedHeight(2)

        self.addWidget(splitter)


class LabelDivider(QWidget):
    """
    Custom divider built using a label and a divider
    """

    def __init__(
            self, text: str = '', margins: tuple[int, int, int, int] = (0, consts.SPACING, 0, consts.SMALL_SPACING),
            spacing=consts.SPACING, bold: bool = True, upper: bool = False, tooltip: str = '',
            parent: QWidget | None = None):
        super().__init__(parent)

        main_layout = layouts.horizontal_layout(spacing=spacing, margins=margins, parent=self)
        if text:
            label = labels.label(text=text, bold=bold, upper=upper, tooltip=tooltip)
            main_layout.addWidget(label, 1)
        new_divider = QLabel()
        new_divider.setMaximumHeight(dpi.dpi_scale(2))
        new_divider.setToolTip(tooltip)
        main_layout.addWidget(new_divider, 10)
