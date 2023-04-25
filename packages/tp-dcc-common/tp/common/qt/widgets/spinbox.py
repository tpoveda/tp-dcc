#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt spinner widgets
"""

from Qt.QtCore import Qt, Signal, Property, QPoint, QRect
from Qt.QtWidgets import QSizePolicy, QFrame, QSpinBox, QDoubleSpinBox
from Qt.QtGui import QColor, QPainter, QDoubleValidator

from tp.common.resources import theme
from tp.common.qt import base, contexts as qt_contexts
from tp.common.qt.widgets import layouts, lineedits, buttons, labels


@theme.mixin
# @mixin.cursor_mixin
class BaseSpinBox(QSpinBox, object):
    def __init__(self, parent=None):
        super(BaseSpinBox, self).__init__(parent=parent)

        self._size = self.theme_default_size()

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the spin box height size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets spin box height size
        :param value: float
        """

        self._size = value
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def tiny(self):
        """
        Sets spin box to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets spin box to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets spin box to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets spin box to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets spin box to huge size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self


@theme.mixin
# @mixin.cursor_mixin
class BaseDoubleSpinBox(QDoubleSpinBox, object):
    def __init__(self, parent=None):
        super(BaseDoubleSpinBox, self).__init__(parent=parent)

        self._size = self.theme_default_size()

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the double spin box height size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets double spin box height size
        :param value: float
        """

        self._size = value
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def tiny(self):
        """
        Sets double spin box to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets double spin box to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets double spin box to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets double spin box to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets double spin box to huge size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self


class BaseNumberWidget(base.BaseWidget, object):
    valueChanged = Signal(object)

    def __init__(self, name='', parent=None):
        self._name = name
        super(BaseNumberWidget, self).__init__(parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(BaseNumberWidget, self).ui()

        self._number_widget = self.get_number_widget()
        self._number_label = label.BaseLabel(self._name, parent=self)
        self._number_label.setAlignment(Qt.AlignRight)
        self._number_label.setMinimumWidth(75)
        self._number_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        if not self._name:
            self._number_label.hide()
        self._value_label = label.BaseLabel('value', parent=self)
        self._value_label.setAlignment(Qt.AlignRight)
        self._value_label.setMinimumWidth(75)
        self._value_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._value_label.hide()

        self.main_layout.addWidget(self._number_label)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self._value_label, alignment=Qt.AlignRight)
        self.main_layout.addWidget(self._number_widget)

    def get_number_widget(self):
        """
        Returns the widget used to edit numeric value
        :return: QWidget
        """

        spin_box = BaseSpinBox(parent=self)
        spin_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return spin_box

    def get_value(self):
        """
        Returns the number value of the numeric widget
        :return: variant, int || float
        """

        return self._number_widget.value()

    def set_value(self, new_value):
        """
        Sets the value of the numeric widget
        :param new_value: variant, int || float
        """

        if new_value:
            self._number_widget.setValue(new_value)

    def get_label_text(self):
        return self._number_label.text()

    def set_label_text(self, new_text):
        self._number_label.setText(new_text)

    def setDecimals(self, value):
        self._number_widget.setDecimals(value)

    def set_value_label(self, new_value):
        self._value_label.show()
        self._value_label.setText(str(new_value))

    def _on_value_changed(self):
        self.valueChanged.emit(self.get_value())


class BaseSpinBoxNumber(BaseNumberWidget):
    enterPressed = Signal()

    def __init__(self, name='', parent=None):
        super(BaseSpinBoxNumber, self).__init__(name=name, parent=parent)

        self._setup_spin_widget()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.enterPressed.emit()

    def get_number_widget(self):
        spin_box = BaseSpinBox()
        spin_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return spin_box

    def _setup_spin_widget(self):
        if hasattr(self._number_widget, 'CorrectToNearestValue'):
            self._number_widget.setCorrectionMode(self._number_widget.CorrectToNearestValue)
        if hasattr(self._number_widget, 'setWrapping'):
            self._number_widget.setWrapping(False)
        if hasattr(self._number_widget, 'setDecimals'):
            self._number_widget.setDecimals(3)

        self._number_widget.setMaximum(100000000)
        self._number_widget.setMinimum(-100000000)
        # self._number_widget.setButtonSymbols(self._number_widget.NoButtons)

        self._number_widget.valueChanged.connect(self._on_value_changed)


class BaseDoubleNumberSpinBox(BaseSpinBoxNumber, object):
    def __init__(self, name='', parent=None):
        super(BaseDoubleNumberSpinBox, self).__init__(name=name, parent=parent)

    def get_number_widget(self):
        spin_box = BaseDoubleSpinBox()
        spin_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return spin_box


class DragDoubleSpinBox(BaseNumberWidget, object):
    def __init__(self, name='', parent=None):
        super(DragDoubleSpinBox, self).__init__(name=name, parent=parent)

    def get_number_widget(self):
        spin_box = DragDoubleSpinBoxLine()
        spin_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return spin_box


class DragDoubleSpinBoxLine(lineedit.BaseLineEdit, object):
    """
    Using middle mouse from left to right will scale the value and a little bar will show the
    percent of the current value
    """

    valueChanged = Signal(float)

    def __init__(self, start=0.0, max=10, min=-10, positive=False, decimals=4, parent=None):
        super(DragDoubleSpinBoxLine, self).__init__(parent=parent)

        self._click = False
        self._default = str(start)
        self._mouse_position = QPoint(0, 0)
        self._min = 0.01 if positive else min
        self._max = max
        self._decimals = decimals or 3
        self._sup = positive
        self.setText(str(start))

        self._setup_validator()

        theme = self.theme()
        self._color = theme.accent_color_5 or QColor(0, 255, 0)

        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text):

        cursor_pos = self.cursorPosition()

        value = round(float(text), self._decimals)
        if value > self._max:
            value = self._max
        elif value < self._min:
            value = self._min

        value = str(value)

        self.setText(value)

        self.setCursorPosition(cursor_pos)

    @property
    def default(self):
        return self._default

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._click = True
            self._mouse_position = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._click = False

    def mouseDoubleClickEvent(self, event):
        self.setText(self._default)

    def mouseMoveEvent(self, event):
        if self._click:
            delta = event.x() - self._mouse_position.x()
            v = float(self.text()) + delta / 100.0
            v = max(self._min, min(self._max, v))
            self.setText(str(round(v, self._decimals)))
            self._mouse_position = event.pos()
            self.valueChanged.emit(v)

    def paintEvent(self, event):
        super(DragDoubleSpinBoxLine, self).paintEvent(event)
        p = QPainter()
        p.begin(self)

        try:
            v = float(self.text())
        except Exception:
            v = 0.0000001

        try:
            v /= self._max if v > 0 else (self._min * -1)
        except Exception:
            pass
        if self._sup:
            p.fillRect(QRect(0, self.height() - 4, v * self.width(), 4), self._color)
        else:
            p.fillRect(
                QRect(self.width() * 0.5, self.height() - 4, v * self.width() * 0.5, 4),
                self._color if v > 0 else QColor(255, 0, 0))
        p.end()

    def get_validator(self):
        return QDoubleValidator()

    def set_default(self, default):
        self._default = default

    def set_minimum(self, minimum_value):
        self._min = minimum_value
        if self.value() < self._min:
            self.setValue(self._min)
        self.update()

    def set_maximum(self, maximum_value):
        self._max = maximum_value
        if self.value() > self._max:
            self.setValue(self._max)
        self.update()

    def value(self):
        try:
            return float(self.text())
        except Exception:
            return 0.0

    def setText(self, text):
        super(DragDoubleSpinBoxLine, self).setText(text)
        self.valueChanged.emit(self.value())

    def setDecimals(self, value):
        self._decimals = int(value)

    # NOTE: Here I'm breaking naming nomenclature on purpose. Doing this we follow nomenclature of Qt SpinBoxes
    def setValue(self, new_value):
        self.setText(str(new_value))

    def _setup_validator(self):
        self.setValidator(self.get_validator())


class DoubleSpinBoxAxis(base.BaseWidget, object):

    textChanged = Signal(str)
    valueChanged = Signal(float)

    def __init__(self, axis, start=0.0, max=10, min=-10, positive=False, parent=None):
        self._axis = axis
        self._start = start
        self._max = max
        self._min = min
        if positive:
            self._min = 0
        super(DoubleSpinBoxAxis, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(DoubleSpinBoxAxis, self).ui()

        axis_widget = QFrame(parent=self)
        axis_widget.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        axis_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        axis_widget.setLayout(axis_layout)
        self._axis_btn = buttons.get_axis_button(axis_type=self._axis, parent=self)
        self._line = BaseDoubleSpinBox(parent=self)
        self._line.setRange(self._min, self._max)
        self._line.setValue(self._start)
        axis_layout.addWidget(self._axis_btn)
        axis_layout.addWidget(self._line)

        self.main_layout.addWidget(axis_widget)

    def setup_signals(self):
        self._line.valueChanged.connect(self.valueChanged.emit)

    def _get_value(self):
        return self.value()

    def _set_value(self, value):
        with qt_contexts.block_signals(self, children=True):
            self.setValue(value)

    floatValue = Property(float, _get_value, _set_value)

    def value(self):
        return self._line.value()

    def setValue(self, new_value):
        self._line.setValue(new_value)

    def setDecimals(self, value):
        self._line.setDecimals(value)

    def setRange(self, min_range, max_range):
        self._min = min_range
        self._max = max_range
        self._line.setMinimum(min_range)
        self._line.setMaximum(max_range)

    def set_minimum(self, minimum_value):
        self._min = minimum_value
        self._line.setMinimum(self._min)

    def set_maximum(self, maximum_value):
        self._max = maximum_value
        self._line.setMaximum(self._max)


class DragDoubleSpinBoxLineAxis(base.BaseWidget, object):

    textChanged = Signal(str)
    valueChanged = Signal(float)

    def __init__(self, axis, reset=True, start=0.0, max=10, min=-10, positive=False, parent=None):
        self._axis = axis
        self._reset = reset
        self._start = start
        self._max = max
        self._min = min
        self._positive = positive
        super(DragDoubleSpinBoxLineAxis, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(DragDoubleSpinBoxLineAxis, self).ui()

        axis_widget = QFrame()
        axis_widget.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        axis_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        axis_widget.setLayout(axis_layout)
        self._axis_btn = buttons.get_axis_button(axis_type=self._axis, parent=self)
        self._line = DragDoubleSpinBoxLine(
            start=self._start, max=self._max, min=self._min, positive=self._positive, parent=self)
        self._reset_btn = buttons.BaseToolButton(parent=self).image('reset').icon_only()
        self._reset_btn.setVisible(self._reset)
        self._reset_btn.setEnabled(self._reset)
        axis_layout.addWidget(self._axis_btn)
        axis_layout.addWidget(self._line)
        axis_layout.addWidget(self._reset_btn)

        self.main_layout.addWidget(axis_widget)

    def setup_signals(self):
        self._reset_btn.clicked.connect(self._on_reset)
        self._line.valueChanged.connect(self.valueChanged.emit)
        self._line.textChanged.connect(self.textChanged.emit)

    def _get_value(self):
        return self.value()

    def _set_value(self, value):
        with qt_contexts.block_signals(self, children=True):
            self.setValue(value)

    floatValue = Property(float, _get_value, _set_value)

    def value(self):
        return self._line.value()

    def setValue(self, new_value):
        self._line.setValue(new_value)

    def setDecimals(self, value):
        self._line.setDecimals(value)

    def setRange(self, min_range, max_range):
        self._line.set_minimum(min_range)
        self._line.set_maximum(max_range)

    def set_default(self, default):
        self._line.set_default(default)

    def set_minimum(self, minimum_value):
        self._min = minimum_value
        self._line.set_minimum(self._min)

    def set_maximum(self, maximum_value):
        self._max = maximum_value
        self._line.set_maximum(self._max)

    def _on_reset(self):
        self._line.setValue(str(self._line.default))
