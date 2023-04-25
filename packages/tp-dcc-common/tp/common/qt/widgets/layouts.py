#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom extra layout implementations
"""

from Qt.QtCore import Qt, QPoint, QRect, QSize
from Qt.QtWidgets import QLayout, QBoxLayout, QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout, QWidget, QWidgetItem

from tp.common.qt import consts, dpi


DEFAULT_SPACING = -1


def vertical_layout(spacing=DEFAULT_SPACING, margins=(0, 0, 0, 0), alignment=None):
    """
    Returns a new vertical layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :param Qt.Alignment or None alignment: optional layout alignment.

    :return: VerticalLayout
    """

    new_layout = VerticalLayout(spacing=spacing, margins=margins)
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def horizontal_layout(spacing=DEFAULT_SPACING, margins=(0, 0, 0, 0), alignment=None):
    """
    Returns a new horizontal layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :param Qt.Alignment or None alignment: optional layout alignment.

    :return: VerticalLayout
    """

    new_layout = HorizontalLayout(spacing=spacing, margins=margins)
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def grid_layout(spacing=DEFAULT_SPACING, margins=(0, 0, 0, 0)):
    """
    Returns a new grid layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.

    :return: VerticalLayout
    """

    return GridLayout(spacing=spacing, margins=margins)


def form_layout(spacing=DEFAULT_SPACING, margins=(0, 0, 0, 0)):
    """
    Returns a new form layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.

    :return: FormLayout
    """

    return FormLayout(spacing=spacing, margins=margins)


def box_layout(spacing=DEFAULT_SPACING, margins=(0, 0, 0, 0), orientation=Qt.Horizontal):
    """
    Returns a new form layout that automatically handles DPI stuff.

    :param int spacing: layout spacing
    :param tuple(int, int, int, int) margins: layout margins.
    :param Qt.Orientation orientation: layout orientation.

    :return: BoxLayout
    """

    return BoxLayout(orientation, spacing=spacing, margins=margins)


def flow_layout(spacing=DEFAULT_SPACING, parent=None):
    """
    Returns a new flow layout.

    :param int spacing: layout spacing.
    :param QWidget parent: layout parent.
    :return: FlowLayout
    """

    return FlowLayout(spacing_x=spacing, spacing_y=spacing, parent=parent)


class HorizontalLayout(QHBoxLayout, object):
    """
    Custom QHBoxLayout implementation with support for 4k resolution
    """

    def __init__(self, *args, **kwargs):

        margins = kwargs.pop('margins', (0, 0, 0, 0))
        spacing = kwargs.pop('spacing', consts.DEFAULT_SUB_WIDGET_SPACING)

        super(HorizontalLayout, self).__init__(*args, **kwargs)

        self.setContentsMargins(*dpi.margins_dpi_scale(*margins))
        self.setSpacing(dpi.dpi_scale(spacing))


class VerticalLayout(QVBoxLayout, object):
    """
    Custom QVBoxLayout implementation with support for 4k resolution
    """

    def __init__(self, *args, **kwargs):

        margins = kwargs.pop('margins', (0, 0, 0, 0))
        spacing = kwargs.pop('spacing', consts.DEFAULT_SUB_WIDGET_SPACING)

        super(VerticalLayout, self).__init__(*args, **kwargs)

        self.setContentsMargins(*dpi.margins_dpi_scale(*margins))
        self.setSpacing(dpi.dpi_scale(spacing))


class FormLayout(QFormLayout, object):
    """
    Custom QFormLayout implementation with support for 4k resolution
    """

    def __init__(self, *args, **kwargs):

        margins = kwargs.pop('margins', (0, 0, 0, 0))
        spacing = kwargs.pop('spacing', consts.DEFAULT_SUB_WIDGET_SPACING)

        super(FormLayout, self).__init__(*args, **kwargs)

        self.setContentsMargins(*dpi.margins_dpi_scale(*margins))
        self.setSpacing(dpi.dpi_scale(spacing))


class GridLayout(QGridLayout, object):
    """
    Custom QGridLayout implementation with support for 4k resolution
    """

    def __init__(self, *args, **kwargs):

        margins = kwargs.pop('margins', (0, 0, 0, 0))
        spacing = kwargs.pop('spacing', consts.DEFAULT_SUB_WIDGET_SPACING)
        column_min_width = kwargs.pop('column_min_width', None)
        column_min_width_b = kwargs.pop('column_min_width_b', None)
        vertical_spacing = kwargs.pop('vertical_spacing', None)
        horizontal_spacing = kwargs.pop('horizontal_spacing', None)

        super(GridLayout, self).__init__(*args, **kwargs)

        self.setContentsMargins(*dpi.margins_dpi_scale(*margins))

        if not vertical_spacing and not horizontal_spacing:
            self.setHorizontalSpacing(dpi.dpi_scale(spacing))
            self.setVerticalSpacing(dpi.dpi_scale(spacing))
        elif vertical_spacing and not horizontal_spacing:
            self.setHorizontalSpacing(dpi.dpi_scale(horizontal_spacing))
            self.setVerticalSpacing(dpi.dpi_scale(vertical_spacing))
        elif horizontal_spacing and not vertical_spacing:
            self.setHorizontalSpacing(dpi.dpi_scale(horizontal_spacing))
            self.setVerticalSpacing(dpi.dpi_scale(spacing))
        else:
            self.setHorizontalSpacing(dpi.dpi_scale(horizontal_spacing))
            self.setVerticalSpacing(dpi.dpi_scale(vertical_spacing))

        if column_min_width:
            self.setColumnMinimumWidth(column_min_width[0], dpi.dpi_scale(column_min_width[1]))
        if column_min_width_b:
            self.setColumnMinimumWidth(column_min_width_b[0], dpi.dpi_scale(column_min_width_b[1]))


class FlowLayout(QLayout, object):
    """
    Layout that automatically adjust widgets position depending on the available space
    """

    def __init__(self, margin=0, spacing_x=2, spacing_y=2, parent=None):
        super(FlowLayout, self).__init__(parent)

        self._spacing_x = 0
        self._spacing_y = 0
        self._orientation = Qt.Horizontal
        self._item_list = list()
        self._overflow = None
        self._size_hint_layout = self.minimumSize()

        self.set_spacing_x(spacing_x)
        self.set_spacing_y(spacing_y)

    def __del__(self):
        self.clear()

    @property
    def spacing_x(self):
        return self._spacing_x

    @property
    def spacing_y(self):
        return self._spacing_y

    @property
    def items_list(self):
        return self._item_list

    def addItem(self, item):
        """
        Overrides base QLayout addItem function
        :param item: QObject
        """

        self._item_list.append(item)

    def count(self):
        """
        Overrides baes QLayout count function
        :return: int
        """

        return len(self._item_list)

    def itemAt(self, index):
        """
        Overrides base QLayout itemAt function
        :param index: int
        :return: QWidget or None
        """

        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        """
        Overrides base QLayout takeAt function
        :param index: int
        :return: QWidget or None
        """

        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        """
        Sets whether this layout grows only in horizontal or vertical dimension
        Overrides base QLayout expandingDirections function
        :return:Qt.Orientation
        """

        return Qt.Orientations(self.orientation())

    def hasHeightForWidth(self):
        """
        Sets whether layout's preferred height depends on its width or not
        Overrides base QLayout hasHeightForWidth function
        :param width: int
        :return: bool
        """

        return self.orientation() == Qt.Horizontal

    def heightForWidth(self, width):
        """
        Returns the preferred heights a layout item with given width
        Overrides base QLayout heightForWidth function
        :param width: int
        :return: int
        """

        height = self._generate_layout(QRect(0, 0, width, 0), True)
        self._size_hint_layout = QSize(width, height)

        return height

    def setGeometry(self, rect):
        """
        Overrides base QLayout setGeometry function
        :param rect: QRect
        """

        super(FlowLayout, self).setGeometry(rect)
        self._generate_layout(rect, False)

    def sizeHint(self):
        """
        Returns the preferred size of this layout
        Overrides base QLayout sizeHint function
        :return: QSize
        """

        return self._size_hint_layout

    def minimumSize(self):
        """
        Returns the minimum size for this layout
        Overrides base minimumSize function
        :return: QSize
        """

        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2, 2)

        return size

    def items(self):
        """
        Returns all items in the layout
        :return: list
        """

        remove = list()
        for item in self._item_list:
            if not dpi.is_valid_widget(item):
                remove.append(item)

        [self._item_list.remove(r) for r in remove]
        return self._item_list

    def set_spacing_x(self, spacing):
        """
        Sets the X spacing for each item
        :param spacing: float
        """

        self._spacing_x = dpi.dpi_scale(spacing)

    def set_spacing_y(self, spacing):
        """
        Sets the Y spacing for each item
        :param spacing: float
        """

        self._spacing_y = dpi.dpi_scale(spacing)

    def clear(self):
        """
        Clears all the widgets in the layout
        """

        item = self.takeAt(0)
        while item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            item = self.takeAt(0)

    def orientation(self):
        """
        Returns flow layout orientation
        :return: Qt.Horizontal or Qt.Vertical
        """

        return self._orientation

    def set_orientation(self, orientation):
        """
        Sets how widgets will be laid out (horizontally or vertically)
        :param orientation: Qt.Horizontal or Qt.Vertical
        """

        self._orientation = orientation

    def add_spacing(self, spacing):
        """
        Adds new spacing into the widget
        :param spacing: int
        """

        # TODO: Check if we should use spacer items instead of standard widgets

        space_widget = QWidget()
        space_widget.setFixedSize(QSize(spacing, spacing))
        self.addWidget(space_widget)

    def insert_widget(self, index, widget):
        """
        Inserts a new widget into the given index
        :param index: int
        :param widget: QWidget
        """

        item = QWidgetItem(widget)
        self._item_list.insert(index, item)

    def remove_at(self, index):
        """
        Removes widget at given index
        :param index: int
        :return: bool, Whether the deletion operation was successful or not
        """

        item = self.takeAt(index)
        if not item:
            return False

        item.widget().setParent(None)
        item.widget().deleteLater()

        return True

    def allow_overflow(self, flag):
        """
        Sets whether or not alllow layouts to overflow, rather than go onto the next line
        :param flag: bool
        :return:
        """

        self._overflow = flag

    def _generate_layout(self, rect, test_only=True):
        """
        Generates layout with proper flow
        :param rect: QRect
        :param test_only: bool
        :return: int
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


class BoxLayout(QBoxLayout, object):
    """
    Custom QFormLayout implementation with support for 4k resolution
    """

    def __init__(self, *args, **kwargs):

        orientation = kwargs.pop('orientation', Qt.Horizontal)
        margins = kwargs.pop('margins', (0, 0, 0, 0))
        spacing = kwargs.pop('spacing', DEFAULT_SPACING)

        super(BoxLayout, self).__init__(
            QBoxLayout.LeftToRight if orientation == 'horizontal' else QBoxLayout.TopToBottom, *args, **kwargs)

        self.setContentsMargins(*dpi.margins_dpi_scale(*margins))
        self.setSpacing(dpi.dpi_scale(spacing))
