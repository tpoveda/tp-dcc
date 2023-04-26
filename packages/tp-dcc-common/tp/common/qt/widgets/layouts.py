#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom extra layout implementations
"""

from Qt.QtCore import Qt, QPoint, QRect, QSize
from Qt.QtWidgets import (
    QLayout, QBoxLayout, QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout, QGraphicsLinearLayout, QWidget, QWidgetItem
)

from tp.common.qt import consts, dpi, qtutils


def vertical_layout(spacing=consts.DEFAULT_SPACING, margins=(0, 0, 0, 0), alignment=None, parent=None):
    """
    Returns a new vertical layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :param Qt.Alignment or None alignment: optional layout alignment.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :return: new vertical layout instance.
    :rtype: QVBoxLayout
    """

    new_layout = QVBoxLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def horizontal_layout(spacing=consts.DEFAULT_SPACING, margins=(0, 0, 0, 0), alignment=None, parent=None):
    """
    Returns a new horizontal layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :param Qt.Alignment or None alignment: optional layout alignment.
    :param QtWidgets.QWidget or None parent: optional layout parent.
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
        spacing=consts.DEFAULT_SPACING, margins=(0, 0, 0, 0), column_min_width=None, column_min_width_b=None,
        vertical_spacing=None, horizontal_spacing=None, parent=None):
    """
    Returns a new grid layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
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


def form_layout(spacing=consts.DEFAULT_SPACING, margins=(0, 0, 0, 0), parent=None):
    """
    Returns a new form layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :return: new form layout instance.
    :rtype: QFormLayout
    """

    new_layout = QFormLayout(parent)
    new_layout.setContentsMargins(*dpi.margins_dpi_scale(*margins))
    new_layout.setSpacing(dpi.dpi_scale(spacing))

    return new_layout


def box_layout(spacing=consts.DEFAULT_SPACING, margins=(0, 0, 0, 0), orientation=Qt.Horizontal, parent=None):
    """
    Returns a new form layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
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


def flow_layout(spacing=consts.DEFAULT_SPACING, parent=None):
    """
    Returns a new flow layout.

    :param int spacing: layout spacing.
    :param QWidget parent: layout parent.
    :return: FlowLayout
    """

    return FlowLayout(spacing_x=spacing, spacing_y=spacing, parent=parent)


def graphics_linear_layout(margins=(0, 0, 0, 0), spacing=0, orientation=Qt.Vertical, parent=None):
    """
    Returs a new vertical graphics linear layout that autmoatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :param Qt.Orientation orientation: layout orientation.
    :return: new vertical graphics linear layout instance.
    :param QtWidgets.QWidget or None parent: optional layout parent.
    :rtype: QGraphicsLinearLayout
    """

    if orientation == Qt.Vertical:
        return vertical_graphics_linear_layout(margins=margins, spacing=spacing, parent=parent)
    else:
        return horizontal_graphics_linear_layout(margins=margins, spacing=spacing, parent=parent)


def vertical_graphics_linear_layout(margins=(0, 0, 0, 0), spacing=0, parent=None):
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


def horizontal_graphics_linear_layout(margins=(0, 0, 0, 0), spacing=0, parent=None):
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


class FlowLayout(QLayout, object):
    """
    Layout that automatically adjust widgets position depending on the available space
    """

    def __init__(self, spacing_x=2, spacing_y=2, margin=0, parent=None):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setMargin(margin)

        self._spacing_x = 0                                     # spacing in X axis
        self._spacing_y = 0                                     # spacing in Y axis
        self._orientation = Qt.Horizontal                       # layout orientation.
        self._item_list = list()                                # list of items in the layout
        self._overflow = None                                   # whether to allow or not overflow
        self._size_hint_layout = self.minimumSize()             # size hint layout

        self.set_spacing_x(spacing_x)
        self.set_spacing_y(spacing_y)

    def __del__(self):
        self.clear()

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def spacing_x(self):
        return self._spacing_x

    @property
    def spacing_y(self):
        return self._spacing_y

    @property
    def items_list(self):
        return self._item_list

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def addItem(self, item):
        """
        Overrides base QLayout addItem function to add the item into our list of items.

        :param QObject item: item to add into the flow layout.
        """

        self._item_list.append(item)

    def count(self):
        """
        Overrides baes QLayout count function to return the total number of items from our list of items.

        :return: total list of items in the layout.
        :rtype: int
        """

        return len(self._item_list)

    def itemAt(self, index):
        """
        Overrides base QLayout itemAt function to retrieve the item from our list of items.

        :param int index: index in the list where the item we are looking for is located.
        :return: Widget located at the given index in our list of items.
        :rtype: QWidget or None
        """

        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        """
        Overrides base QLayout takeAt function to retrieve the item from our list of items.

        :param int index: index in the list where the item we are looking for is located.
        :return: Widget located at the given index in our list of items.
        :rtype: QWidget or None
        """

        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        """
        Sets whether this layout grows only in horizontal or vertical dimension.
        Overrides base QLayout expandingDirections function to use the orientation defined in the flow layout.

        :return: flow layout orientation.
        :rtype: Qt.Orientation
        """

        return Qt.Orientations(self.orientation())

    def hasHeightForWidth(self):
        """
        Sets whether layout's preferred height depends on its width or not.
        Overrides base QLayout hasHeightForWidth function.

        :return: Whethr or not the current orientatin is horizontal.
        :rtype: bool
        """

        return self.orientation() == Qt.Horizontal

    def heightForWidth(self, width):
        """
        Returns the preferred heights a layout item with given width.
        Overrides base QLayout heightForWidth function.

        :param int width: desired width.
        :return: height based on the given width.
        :rtype: int
        """

        height = self._generate_layout(QRect(0, 0, width, 0), True)
        self._size_hint_layout = QSize(width, height)

        return height

    def setGeometry(self, rect):
        """
        Overrides base QLayout setGeometry function to reposition all items inside the flow layout based on the rect.

        :param QRect rect: new geomtry rectangle.
        """

        super(FlowLayout, self).setGeometry(rect)
        self._generate_layout(rect, False)

    def sizeHint(self):
        """
        Returns the preferred size of this layout.
        Overrides base QLayout sizeHint function.

        :return: desired size to fit all items in the layout.
        :rtype: QSize
        """

        return self._size_hint_layout

    def minimumSize(self):
        """
        Returns the minimum size for this layout.
        Overrides base minimumSize function.

        :return: layout minimum size.
        :rtype: QSize
        """

        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2, 2)

        return size

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def items(self):
        """
        Returns all items in the layout.

        :return: layout items.
        :rtype: list(QObject)
        """

        remove = list()
        for item in self._item_list:
            if not qtutils.is_valid_widget(item):
                remove.append(item)

        [self._item_list.remove(r) for r in remove]
        return self._item_list

    def set_spacing_x(self, spacing):
        """
        Sets the X spacing for each item.

        :param float spacing: spacing between items in X axis.
        """

        self._spacing_x = dpi.dpi_scale(spacing)

    def set_spacing_y(self, spacing):
        """
        Sets the Y spacing for each item.

        :param float spacing: spacing between items in Y axis.
        """

        self._spacing_y = dpi.dpi_scale(spacing)

    def clear(self):
        """
        Clears all the widgest in the layout.
        """

        item = self.takeAt(0)
        while item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            item = self.takeAt(0)

    def orientation(self):
        """
        Returns flow layout orientation.

        :return: flow layout orientation.
        :rtype: Qt.Horizontal or Qt.Vertical
        """

        return self._orientation

    def set_orientation(self, orientation):
        """
        Sets how widgets will be laid out (horizontally or vertically).

        :param Qt.Horizontal or Qt.Vertical orientation: flow layout orientation.
        """

        self._orientation = orientation

    def add_spacing(self, spacing):
        """
        Adds new spacing into the widget.

        :param int spacing: add spacing between the items in the layout
        """

        space_widget = QWidget()
        space_widget.setFixedSize(dpi.size_by_dpi(QSize(spacing, spacing)))
        self.addWidget(space_widget)

    def insert_widget(self, index, widget):
        """
        Inserts a new widget into the given index.

        :param int index: list index where we want to insert the widget.
        :param QWidget widget: widget we want to insert into the layout in the given index.
        """

        item = QWidgetItem(widget)
        self._item_list.insert(index, item)

    def remove_at(self, index):
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

    def allow_overflow(self, flag):
        """
        Sets whether or not alllow layouts to overflow, rather than go onto the next line.

        :param bool flag: whether or not to allow overflow.
        """

        self._overflow = flag

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _generate_layout(self, rect, test_only=True):
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
