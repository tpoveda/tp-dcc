#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom extra layout implementations
"""

from __future__ import annotations

from typing import Optional, Union, Tuple, List

from overrides import override
from Qt.QtCore import Qt, QObject, QPoint, QRect, QSize
from Qt.QtWidgets import (
    QLayout, QBoxLayout, QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout, QGraphicsLinearLayout, QWidget,
    QWidgetItem, QLayoutItem
)

from tp.common.qt import consts, dpi, qtutils


def vertical_layout(
        spacing: int = consts.DEFAULT_SPACING, margins: Tuple[int, int, int, int] = (2, 2, 2, 2),
        alignment: Qt.AlignmentFlag | None = None, parent: QWidget | None = None) -> QVBoxLayout:
    """
    Returns a new vertical layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param Tuple[int, int, int, int] margins: layout margins.
    :param Qt.AlignmentFlag or None alignment: optional layout alignment.
    :param QWidget or None parent: optional layout parent.
    :return: new vertical layout instance.
    :rtype: QVBoxLayout
    """

    new_layout = QVBoxLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def horizontal_layout(
        spacing: int = consts.DEFAULT_SPACING, margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
        alignment: Qt.AlignmentFlag | None = None, parent: QWidget | None = None) -> QHBoxLayout:
    """
    Returns a new horizontal layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param Tuple[int, int, int, int] margins: layout margins.
    :param Qt.AlignmentFlag or None alignment: optional layout alignment.
    :param QWidget or None parent: optional layout parent.
    :return: new horizontal layout instance.
    :rtype: QHBoxLayout
    """

    new_layout = QHBoxLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def grid_layout(
        spacing: int = consts.DEFAULT_SPACING, margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
        column_min_width: int | None = None, column_min_width_b: int | None = None,
        vertical_spacing: int | None = None, horizontal_spacing: int | None = None,
        parent: QWidget | None = None) -> QGridLayout:
    """
    Returns a new grid layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param Tuple[int, int, int, int] margins: layout margins.
    :param int or None column_min_width: optional colum minimum width.
    :param int or None column_min_width_b: optional colum secondary minimum width.
    :param int or None vertical_spacing: optional vertical spacing.
    :param int or None horizontal_spacing: optional horizontal spacing.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :return: new grid layout instance.
    :rtype: QGridLayout
    """

    new_layout = QGridLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    if not vertical_spacing and not horizontal_spacing:
        new_layout.setHorizontalSpacing(dpi.dpi_scale(spacing))
        new_layout.setVerticalSpacing(dpi.dpi_scale(spacing))
    elif vertical_spacing and not horizontal_spacing:
        new_layout.setHorizontalSpacing(dpi.dpi_scale(horizontal_spacing))
        new_layout.setVerticalSpacing(dpi.dpi_scale(vertical_spacing))
    elif horizontal_spacing and not vertical_spacing:
        new_layout.setHorizontalSpacing(dpi.dpi_scale(horizontal_spacing))
        new_layout.setVerticalSpacing(dpi.dpi_scale(spacing))
    else:
        new_layout.setHorizontalSpacing(dpi.dpi_scale(horizontal_spacing))
        new_layout.setVerticalSpacing(dpi.dpi_scale(vertical_spacing))

    if column_min_width:
        new_layout.setColumnMinimumWidth(column_min_width[0], dpi.dpi_scale(column_min_width[1]))
    if column_min_width_b:
        new_layout.setColumnMinimumWidth(column_min_width_b[0], dpi.dpi_scale(column_min_width_b[1]))

    return new_layout


def form_layout(
        spacing: int = consts.DEFAULT_SPACING, margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
        parent: QWidget | None = None) -> QFormLayout:
    """
    Returns a new form layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param Tuple[int, int, int, int] margins: layout margins.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :return: new form layout instance.
    :rtype: QFormLayout
    """

    new_layout = QFormLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))

    return new_layout


def box_layout(
        spacing: int = consts.DEFAULT_SPACING, margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
        orientation: Qt.AlignmentFlag = Qt.Horizontal, parent: QWidget | None = None) -> QBoxLayout:
    """
    Returns a new form layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param Tuple[int, int, int, int] margins: layout margins.
    :param Qt.Orientation orientation: layout orientation.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :return: new box layout instance.
    :rtype: QBoxLayout
    """

    new_layout = QBoxLayout(
        QBoxLayout.LeftToRight if orientation == Qt.Horizontal else QBoxLayout.TopToBottom, parent=parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))

    return new_layout


def flow_layout(spacing: int = consts.DEFAULT_SPACING, parent: QWidget | None = None) -> FlowLayout:
    """
    Returns a new flow layout.

    :param int spacing: layout spacing.
    :param QWidget parent: layout parent.
    :return: FlowLayout
    """

    return FlowLayout(spacing_x=spacing, spacing_y=spacing, parent=parent)


def graphics_linear_layout(
        spacing: int = 0, margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
        orientation: Qt.AlignmentFlag = Qt.Vertical, parent: QWidget | None =None) -> QGraphicsLinearLayout:
    """
    Returs a new vertical graphics linear layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param Tuple[int, int, int, int] margins: layout margins.
    :param Qt.Orientation orientation: layout orientation.
    :return: new vertical graphics linear layout instance.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :rtype: QGraphicsLinearLayout
    """

    if orientation == Qt.Vertical:
        return vertical_graphics_linear_layout(margins=margins, spacing=spacing, parent=parent)
    else:
        return horizontal_graphics_linear_layout(margins=margins, spacing=spacing, parent=parent)


def vertical_graphics_linear_layout(
        spacing: int = 0, margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
        parent: QWidget | None =None) -> QGraphicsLinearLayout:
    """
    Returs a new vertical graphics linear layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :return: new vertical graphics linear layout instance.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :rtype: QGraphicsLinearLayout
    """

    new_layout = QGraphicsLinearLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))
    new_layout.setOrientation(Qt.Vertical)

    return new_layout


def horizontal_graphics_linear_layout(
        spacing: int = 0, margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
        parent: QWidget | None =None) -> QGraphicsLinearLayout:
    """
    Returs a new vertical graphics linear layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :return: new vertical graphics linear layout instance.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :rtype: QGraphicsLinearLayout
    """

    new_layout = QGraphicsLinearLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))
    new_layout.setOrientation(Qt.Horizontal)

    return new_layout


class FlowLayout(QLayout):
    """
    Layout that automatically adjust widgets position depending on the available space
    """

    def __init__(self, spacing_x: int = 2, spacing_y: int = 2, margin: int = 0, parent: QWidget | None = None):
        super().__init__(parent)

        if parent is not None:
            self.setMargin(margin)

        self._spacing_x = 0                                     # spacing in X axis
        self._spacing_y = 0                                     # spacing in Y axis
        self._orientation = Qt.Horizontal                       # layout orientation.
        self._item_list = []                                    # list of items in the layout
        self._overflow = None                                   # whether to allow or not overflow
        self._size_hint_layout = self.minimumSize()             # size hint layout

        self.set_spacing_x(spacing_x)
        self.set_spacing_y(spacing_y)

    def __del__(self):
        self.clear()

    @property
    def spacing_x(self) -> int:
        return self._spacing_x

    @property
    def spacing_y(self) -> int:
        return self._spacing_y

    @property
    def items_list(self) -> List[QObject]:
        return self._item_list

    @override
    def addItem(self, arg__1: QLayoutItem) -> None:
        self._item_list.append(arg__1)

    @override
    def count(self) -> int:
        return len(self._item_list)

    @override
    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    @override
    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    @override
    def expandingDirections(self) -> Union[Qt.Orientations, Qt.Orientation]:
        return Qt.Orientations(self.orientation())

    @override
    def hasHeightForWidth(self) -> bool:
        return self.orientation() == Qt.Horizontal

    @override
    def heightForWidth(self, arg__1: int) -> int:
        height = self._generate_layout(QRect(0, 0, arg__1, 0), True)
        self._size_hint_layout = QSize(arg__1, height)

        return height

    @override
    def setGeometry(self, arg__1: QRect) -> None:
        super().setGeometry(arg__1)
        self._generate_layout(arg__1, False)

    @override
    def sizeHint(self) -> QSize:
        return self._size_hint_layout

    @override
    def minimumSize(self) -> QSize:

        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2, 2)

        return size

    def items(self) -> List[QObject]:
        """
        Returns all items in the layout.

        :return: layout items.
        :rtype: List[QObject]
        """

        remove = list()
        for item in self._item_list:
            if not qtutils.is_valid_widget(item):
                remove.append(item)

        [self._item_list.remove(r) for r in remove]
        return self._item_list

    def set_spacing_x(self, spacing: int):
        """
        Sets the X spacing for each item.

        :param int spacing: spacing between items in X axis.
        """

        self._spacing_x = dpi.dpi_scale(spacing)

    def set_spacing_y(self, spacing: int):
        """
        Sets the Y spacing for each item.

        :param int spacing: spacing between items in Y axis.
        """

        self._spacing_y = dpi.dpi_scale(spacing)

    def clear(self):
        """
        Clears all the widgets in the layout.
        """

        item = self.takeAt(0)
        while item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            item = self.takeAt(0)

    def orientation(self) -> Qt.Orientation:
        """
        Returns flow layout orientation.

        :return: flow layout orientation.
        :rtype: Qt.Orientation
        """

        return self._orientation

    def set_orientation(self, orientation: Qt.Orientation):
        """
        Sets how widgets will be laid out (horizontally or vertically).

        :param Qt.Orientation orientation: flow layout orientation.
        """

        self._orientation = orientation

    def add_spacing(self, spacing: int):
        """
        Adds new spacing into the widget.

        :param int spacing: add spacing between the items in the layout
        """

        space_widget = QWidget()
        space_widget.setFixedSize(dpi.size_by_dpi(QSize(spacing, spacing)))
        self.addWidget(space_widget)

    def insert_widget(self, index: int, widget: QWidget):
        """
        Inserts a new widget into the given index.

        :param int index: list index where we want to insert the widget.
        :param QWidget widget: widget we want to insert into the layout in the given index.
        """

        item = QWidgetItem(widget)
        self._item_list.insert(index, item)

    def remove_at(self, index: int):
        """
        Removes widget at given index.

        :param int index: widget index from the list of items we want to remove from layout.
        :return: whether the deletion operation was successful or not.
        :rtype: bool
        """

        item = self.takeAt(index)
        if not item:
            return False

        item.widget().setParent(None)
        item.widget().deleteLater()

        return True

    def allow_overflow(self, flag: bool):
        """
        Sets whether to allow layouts to overflow, rather than go onto the next line.

        :param bool flag: whether to allow overflow.
        """

        self._overflow = flag

    def _generate_layout(self, rect: QRect, test_only: bool = True):
        """
        Internal function that generates layout with proper flow.

        :param QRect rect: layout geometry.
        :param bool test_only: test only flag.
        :return: flow layout height or width based on layout orientation.
        :rtype: int
        """

        x = rect.x()
        y = rect.y()
        line_height = 0
        orientation = self.orientation()

        for item in self._item_list:
            widget = item.widget()
            if widget.isHidden():
                continue

            space_x = self._spacing_x
            space_y = self._spacing_y

            if orientation == Qt.Horizontal:
                next_x = x + item.sizeHint().width() + space_x
                if next_x - space_x > rect.right() and line_height > 0:
                    if not self._overflow:
                        x = rect.x()
                        y = y + line_height + (space_y * 2)
                        next_x = x + item.sizeHint().width() + space_x
                        line_height = 0
                if not test_only:
                    item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                x = next_x
                line_height = max(line_height, item.sizeHint().height())
            else:
                next_y = y + item.sizeHint().height() + space_y
                if next_y - space_y > rect.bottom() and line_height > 0:
                    if not self._overflow:
                        y = rect.y()
                        x = x + line_height + (space_x * 2)
                        next_y = y + item.sizeHint().height() + space_y
                        line_height = 0
                if not test_only:
                    item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                x = next_y
                line_height = max(line_height, item.sizeHint().height())

        if orientation == Qt.Horizontal:
            return y + line_height - rect.y()
        else:
            return x + line_height - rect.x()
