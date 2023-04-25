#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom widget for Qt check boxes
"""

from functools import partial
from collections import OrderedDict

from Qt.QtCore import Qt, Property, Signal, QRect, QSize
from Qt.QtWidgets import QCheckBox, QStylePainter, QStyleOption
from Qt.QtGui import QColor, QPainter, QBrush

from tp.core.managers import resources
from tp.common.qt import consts, mixin, base, animation, contexts as qt_contexts
from tp.common.qt.widgets import layouts, labels, menus


def checkbox(text='', flag=False, tooltip='', parent=None):
    """
    Creates a basic QCheckBox widget.

    :param str text: checkbox text.
    :param bool flag: true to check by default; False otherwise.
    :param str tooltip: checkbox tooltip.
    :param QWidget parent: parent widget.
    :return: newly created combo box.
    :rtype: BaseCheckBox
    """

    new_checkbox = BaseCheckBox(text=text, parent=parent)
    new_checkbox.setChecked(flag)
    if tooltip:
        new_checkbox.setToolTip(tooltip)

    return new_checkbox


def checkbox_widget(text='', checked=False, tooltip='', enable_menu=True, parent=None):
    """
    Creates a BaseCheckbox widget.

    :param str text: checkbox text.
    :param bool checked: true to check by default; False otherwise.
    :param str tooltip: checkbox tooltip.
    :param bool enable_menu: whether to enable checkbox menu.
    :param QWidget parent: parent widget.
    :return: newly created combo box.
    :rtype: BaseCheckBoxWidget
    """

    new_checkbox_widget = BaseCheckBoxWidget(
        text=text, checked=checked, tooltip=tooltip, enable_menu=enable_menu, parent=parent)

    return new_checkbox_widget


@mixin.dynamic_property
class BaseCheckBox(QCheckBox, object):
    def __init__(self, text='', parent=None):
        super(BaseCheckBox, self).__init__(text=text, parent=parent)

    def _get_checked(self):
        return self.isChecked()

    def _set_checked(self, flag):
        with qt_contexts.block_signals(self):
            self.setChecked(flag)

    check = Property(bool, _get_checked, _set_checked)


class StyledBaseCheckBox(BaseCheckBox, animation.BaseAnimObject):
    _glow_brushes = dict()
    for index in range(1, 11):
        _glow_brushes[index] = [QBrush(QColor(0, 255, 0, 1 * index)),
                                QBrush(QColor(0, 255, 0, 3 * index)),
                                QBrush(QColor(0, 255, 0, 15 * index)),
                                QBrush(QColor(0, 255, 0, 25.5 * index))]

    _disabled_glow_brushes = {}
    for index in range(1, 11):
        _disabled_glow_brushes[index] = [QBrush(QColor(125, 125, 125, 1 * index)),
                                         QBrush(QColor(125, 125, 125, 3 * index)),
                                         QBrush(QColor(125, 125, 125, 15 * index)),
                                         QBrush(QColor(125, 125, 125, 25.5 * index))]

    def __init__(self, *args, **kwargs):
        QCheckBox.__init__(self, *args, **kwargs)
        animation.BaseAnimObject.__init__(self)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        option = QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height() - 1
        width = option.rect.width() - 1
        font = self.font()
        text = self.text()
        alignment = (Qt.AlignLeft | Qt.AlignVCenter)

        painter.setPen(self._pens_border)
        painter.setBrush(self._brush_border)
        painter.drawRoundedRect(QRect(x + 2, y + 2, 13, 13), 3, 3)

        if self.isEnabled():
            painter.setPen(self._pens_shadow)
            painter.drawText(21, y + 2, width, height, alignment, text)

            painter.setPen(self._pens_text)
            painter.drawText(20, y + 1, width, height, alignment, text)

        else:
            painter.setPen(self._pens_shadow_disabled)
            painter.drawText(21, y + 2, width, height, alignment, text)

            painter.setPen(self._pens_text_disabled)
            painter.drawText(20, y + 1, width, height, alignment, text)

        painter.setPen(self._pens_clear)

        if self.isEnabled():
            glow_brushes = self._glow_brushes
        else:
            glow_brushes = self._disabled_glow_brushes

        if self.checkState():
            for index, pos, size, corner in zip(range(4), (2, 3, 4, 5), (13, 11, 9, 7), (4, 3, 3, 2)):
                painter.setBrush(glow_brushes[10][index])
                painter.drawRoundedRect(QRect(x + pos, y + pos, size, size), corner, corner)

        glow_index = self._glow_index
        if glow_index > 0:
            for index, pos, size, corner in zip(range(4), (3, 4, 5, 6), (11, 9, 7, 5), (3, 3, 2, 2)):
                painter.setBrush(glow_brushes[glow_index][index])
                painter.drawRoundedRect(QRect(x + pos, y + pos, size, size), corner, corner)


@menus.mixin
class BaseCheckBoxWidget(base.BaseWidget):

    leftClicked = Signal()
    middleClicked = Signal()
    rightClicked = Signal()
    stateChanged = Signal(object)

    def __init__(self, text='', checked=False, tooltip='', enable_menu=True, menu_vertical_offset=20, right=False,
                 label_ratio=0, box_ratio=0, parent=None):

        self._label = None
        self._right = right
        self._label_ratio = label_ratio
        self._box_ratio = box_ratio
        self._checkbox = None

        super(BaseCheckBoxWidget, self).__init__(parent=parent)

        if tooltip:
            self.setToolTip(tooltip)

        self.setChecked(checked)
        self.set_text(text)

        if enable_menu:
            self._setup_menu_class(menu_vertical_offset=menu_vertical_offset)
            self.leftClicked.connect(partial(self.show_context_menu, Qt.LeftButton))
            self.middleClicked.connect(partial(self.show_context_menu, Qt.MidButton))
            self.rightClicked.connect(partial(self.show_context_menu, Qt.RightButton))

    def __getattr__(self, item):
        if self._checkbox and hasattr(self._checkbox, item):
            return getattr(self._checkbox, item)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def mousePressEvent(self, event):
        """
        Overrides base QWidget mousePressEvent function.

        :param QEvent event: Qt mouse press event.
        """

        for mouse_button, menu_instance in self._click_menu.items():
            if menu_instance and event.button() == mouse_button:
                if mouse_button == Qt.LeftButton:
                    return self.leftClicked.emit()
                elif mouse_button == Qt.MidButton:
                    return self.middleClicked.emit()
                elif mouse_button == Qt.RightButton:
                    return self.rightClicked.emit()
        super(BaseCheckBoxWidget, self).mousePressEvent(event)

    def get_main_layout(self):
        return layouts.QHBoxLayout()

    def setup_ui(self):
        super(BaseCheckBoxWidget, self).setup_ui()

        self._checkbox = BaseCheckBox(text=self._text, parent=self)
        if self._right:
            self._label = labels.BaseLabel(parent=self)
            self.main_layout.addWidget(self._label, self._label_ratio)
        self.main_layout.addWidget(self._checkbox, self._box_ratio)

    def setup_signals(self):
        super(BaseCheckBoxWidget, self).setup_signals()

        self._checkbox.stateChanged.connect(self.stateChanged.emit)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_text(self, text):
        """
        Sets the text of the checkbox label.

        :param str text: label text.
        """

        if self._label:
            self._label.setText(text)
        self._checkbox.setText('' if self._right else text)

    def text(self):
        """
        Returns checkbox label text.

        :return: label text.
        :rtype: str
        """

        return self._label.text() if self._label else self._checkbox.text()

    def set_checked_quiet(self, value):
        """
        Sets the checkbox without emitting any signal.

        :param flag value: check value.
        """

        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(value)
        self._checkbox.blockSignals(False)


class AxesCheckboxWidget(base.BaseWidget):
    def __init__(self, label_text, parent=None):

        self._label_text = label_text
        self._checkboxes = OrderedDict()

        super(AxesCheckboxWidget, self).__init__(parent)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def get_main_layout(self):
        """
        Returns the main layout used by the widget.

        :return: main widget layout.
        :rtype: QLayout
        """

        return layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))

    def setup_ui(self):
        """
        Function that fills the UI with widgets.
        """

        super(AxesCheckboxWidget, self).setup_ui()

        self._label = labels.BaseLabel('{}:'.format(self._label_text), parent=self)
        self.main_layout.addWidget(self._label)

        self.main_layout.addStretch()
        for axis in 'xyz':
            axis_checkbox = BaseCheckBox(parent=self)
            axis_label = labels.BaseLabel(parent=self)
            axis_label.clicked.connect(partial(self._on_label_clicked, axis))
            axis_label.setPixmap(
                resources.icon('{}_axis'.format(axis), color=QColor(*consts.AXISES_COLORS[axis])).pixmap(QSize(24, 24)))
            self._checkboxes[axis] = axis_checkbox
            self.main_layout.addWidget(axis_label)
            self.main_layout.addWidget(axis_checkbox)
            self.main_layout.addStretch()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_label_width(self, width):
        """
        Sets the width of the label.

        :param int width: label width.
        """

        self._label.setFixedWidth(width)

    def get_states(self):
        """
        Returns the current state axis checkboxes.

        :return: tuple of states.
        :rtype: tuple(bool, bool, bool)
        """

        states = tuple([checkbox.isChecked() for checkbox in list(self._checkboxes.values())])

        return states

    def set_states(self, states):
        """
        Sets the states of the axis checkboxes.

        :param list(bool, bool, bool) states: tuple of states
        """

        for i, cbx in enumerate(list(self._checkboxes.values())):
            cbx.setCheckState(Qt.Checked if states[i] else Qt.Unchecked)

    def _on_label_clicked(self, axis):
        axis_checkbox = self._checkboxes.get(axis, None)
        if not axis_checkbox:
            return
        axis_checkbox.setCheckState(Qt.Checked if not axis_checkbox.isChecked() else Qt.Unchecked)
