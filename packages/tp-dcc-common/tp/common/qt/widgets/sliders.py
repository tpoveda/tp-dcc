#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt slider widgets
"""

from copy import copy

from Qt.QtCore import Qt, Signal, Property, QPoint, QPointF, QEvent
from Qt.QtWidgets import QSizePolicy, QWidget, QAbstractSpinBox, QDoubleSpinBox, QStyle, QStyleOptionSlider
from Qt.QtWidgets import QGroupBox, QSlider, QToolTip
from Qt.QtGui import QCursor, QColor, QFont, QPainter, QMouseEvent

from tpDcc import dcc
from tpDcc.libs.python import color as core_color
from tpDcc.libs.resources.core import theme, color
from tpDcc.libs.qt.core import utils, qtutils, contexts as qt_contexts
from tpDcc.libs.qt.widgets import layouts, label

FLOAT_SLIDER_DRAG_STEPS = [100.0, 10.0, 1.0, 0.1, 0.01, 0.001]
INT_SLIDER_DRAG_STEPS = [100.0, 10.0, 1.0]


@theme.mixin
class BaseSlider(QSlider, object):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(BaseSlider, self).__init__(orientation, parent=parent)

    def mouseMoveEvent(self, event):
        QToolTip.showText(event.globalPos(), str(self.value()), self)
        return super(BaseSlider, self).mouseMoveEvent(event)


class SliderDraggers(QWidget, object):
    increment = Signal(object)

    def __init__(self, parent=None, is_float=True, dragger_steps=None, main_color=None):
        super(SliderDraggers, self).__init__(parent)

        self._drags = list()
        self._initial_pos = None
        self._active_drag = None
        self._last_delta_x = 0
        self._change_direction = 0
        self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()
        dragger_steps = dragger_steps or FLOAT_SLIDER_DRAG_STEPS

        self.setWindowFlags(Qt.Popup)

        draggers_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(draggers_layout)

        steps = copy(dragger_steps)
        if not is_float:
            steps = list(filter(lambda x: abs(x) >= 1.0, steps))
        for i in steps:
            drag = HoudiniInputDragger(self, i)
            self._drags.append(drag)
            draggers_layout.addWidget(drag)

        self.installEventFilter(self)

    @property
    def active_drag(self):
        return self._active_drag

    @active_drag.setter
    def active_drag(self, input_dragger):
        self._active_drag = input_dragger

    @property
    def drags(self):
        return self._drags

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            if self._active_drag:
                modifiers = event.modifiers()
                self._active_drag.setStyleSheet(self._get_style_sheet())
                if not self._initial_pos:
                    self._initial_pos = event.globalPos()
                delta_x = event.globalPos().x() - self._initial_pos.x()
                self._change_direction = utils.clamp(delta_x - self._last_delta_x, -1.0, 1.0)
                if self._change_direction != 0:
                    v = self._change_direction * self._active_drag.factor
                    if modifiers == Qt.NoModifier and delta_x % 4 == 0:
                        self.increment.emit(v)
                    if modifiers in [Qt.ShiftModifier, Qt.ControlModifier] and delta_x % 8 == 0:
                        self.increment.emit(v)
                    if modifiers == Qt.ShiftModifier | Qt.ControlModifier and delta_x % 32 == 0:
                        self.increment.emit(v)
                self._last_delta_x = delta_x
        if event.type() == QEvent.MouseButtonRelease:
            self.hide()
            self._last_delta_x = 0
            del(self)

        return False

    def _get_style_sheet(self):
        return """
        QGroupBox{
            border: 0.5 solid darkgrey;
            background : %s;
            color: white;
        }
        QLabel{
            background: transparent;
            border: 0 solid transparent;
            color: white;
        }
        """ % "rgba%s" % str(self._main_color)


class Slider(QSlider, object):
    """
    Custom slider that allows:
    - Left/Mid: Click to move handle
    - Ctrl and drag to move handle half velocity
    - Shift and drag to move handle quarter velocity
    - Ctrl + Shift and drag to move handle eighty velocity
    """

    editingFinihsed = Signal()
    valueIncremented = Signal(object)
    floatValueChanged = Signal(object)

    def __init__(self, parent=None, dragger_steps=None, slider_range=None, *args, **kwargs):
        if dragger_steps is None:
            dragger_steps = INT_SLIDER_DRAG_STEPS
        if slider_range is None:
            slider_range = [-100, 100]
        super(Slider, self).__init__(parent=parent, **kwargs)

        self._slider_range = slider_range
        self._dragger_steps = dragger_steps
        self._is_float = False
        self._default_value = 0
        self._prev_value = 0
        self._delta_value = 0
        self._start_drag_pos = QPointF()
        self._real_start_drag_pos = QPointF()
        self._draggers = None

        if dcc.is_maya():
            self._left_button = Qt.MidButton
            self._mid_button = Qt.LeftButton
        else:
            self._left_button = Qt.LeftButton
            self._mid_button = Qt.MidButton

        self.setFocusPolicy(Qt.StrongFocus)
        self.setOrientation(Qt.Horizontal)
        self.setRange(self._slider_range[0], self._slider_range[1])

    def mousePressEvent(self, event):
        self._prev_value = self.value()
        self._start_drag_pos = event.pos()
        if event.button() == Qt.MidButton:
            if not self._draggers:
                self._draggers = SliderDraggers(parent=self, is_float=self._is_float, dragger_steps=self._dragger_steps)
                self._draggers.increment.connect(self.valueIncremented.emit)
            self._draggers.show()
            if self._is_float:
                self._draggers.move(
                    self.mapToGlobal(QPoint(event.pos().x() - 1, event.pos().y() - self._draggers.height() / 2)))
            else:
                draggers_height = self._draggers.height()
                self._draggers.move(
                    self.mapToGlobal(
                        QPoint(event.pos().x() - 1, event.pos().y() - (self._draggers.height() - draggers_height / 6))))
        elif event.button() == self._left_button and event.modifiers() not in \
                [Qt.ControlModifier, Qt.ShiftModifier, Qt.ControlModifier | Qt.ShiftModifier]:
            buttons = Qt.MouseButtons(self._mid_button)
            mouse_event = QMouseEvent(event.type(), event.pos(), self._mid_button, buttons, event.modifiers())
            super(Slider, self).mousePressEvent(mouse_event)
        elif event.modifiers() in [Qt.ControlModifier, Qt.ShiftModifier, Qt.ControlModifier | Qt.ShiftModifier]:
            style_slider = QStyleOptionSlider()
            style_slider.initFrom(self)
            style_slider.orientation = self.orientation()
            available = self.style().pixelMetric(QStyle.PM_SliderSpaceAvailable, style_slider, self)
            x_loc = QStyle.sliderPositionFromValue(
                self.minimum(), self.maximum(), super(Slider, self).value(), available)
            buttons = Qt.MouseButtons(self._mid_button)
            new_pos = QPointF()
            new_pos.setX(x_loc)
            mouse_event = QMouseEvent(event.type(), new_pos, self._mid_button, buttons, event.modifiers())
            self._start_drag_pos = new_pos
            self._real_start_drag_pos = event.pos()
            super(Slider, self).mousePressEvent(mouse_event)
            self._delta_value = self.value() - self._prev_value
            self.setValue(self._prev_value)
        else:
            super(Slider, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        delta_x = event.pos().x() - self._real_start_drag_pos.x()
        delta_y = event.pos().y() - self._real_start_drag_pos.y()
        new_pos = QPointF()
        if event.modifiers() in [Qt.ControlModifier, Qt.ShiftModifier, Qt.ControlModifier | Qt.ShiftModifier]:
            if event.modifiers() == Qt.ControlModifier:
                new_pos.setX(self.startDragpos.x() + delta_x / 2)
                new_pos.setY(self.startDragpos.y() + delta_y / 2)
            elif event.modifiers() == Qt.ShiftModifier:
                new_pos.setX(self.startDragpos.x() + delta_x / 4)
                new_pos.setY(self.startDragpos.y() + delta_y / 4)
            elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier:
                new_pos.setX(self.startDragpos.x() + delta_x / 8)
                new_pos.setY(self.startDragpos.y() + delta_y / 8)
            mouse_event = QMouseEvent(event.type(), new_pos, event.button(), event.buttons(), event.modifiers())
            super(Slider, self).mouseMoveEvent(mouse_event)
            self.setValue(self.value() - self._delta_value)
        else:
            super(Slider, self).mouseMoveEvent(event)

    def keyPressEvent(self, event):
        p = self.mapFromGlobal(QCursor.pos())
        self._start_drag_pos = p
        self._real_start_drag_pos = p
        self._default_value = 0
        super(Slider, self).keyPressEvent(event)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super(Slider, self).wheelEvent(event)

    @property
    def slider_range(self):
        return self._slider_range


class DoubleSlider(Slider, object):
    doubleValueChanged = Signal(float)

    def __init__(self, parent=None, slider_range=None, default_value=0.0, maximum_value=1000000, dragger_steps=None):
        if slider_range is None:
            slider_range = (-100.0, 100.0)
        if dragger_steps is None:
            dragger_steps = FLOAT_SLIDER_DRAG_STEPS
        super(DoubleSlider, self).__init__(parent=parent, dragger_steps=dragger_steps, slider_range=slider_range)

        self._is_float = True
        self._maximum_value = abs(maximum_value)

        self.setOrientation(Qt.Horizontal)
        self.setMinimum(0)
        self.setMaximum(self._maximum_value)

        self.valueChanged.connect(self._on_value_changed)
        self.valueIncremented.connect(self._on_value_incremented)
        self.set_mapped_value(default_value, True)

    def mapped_value(self):
        return self._map_value(self.value())

    def set_mapped_value(self, value, block_signals=False):
        internal_value = self._unmap_value(value)
        if block_signals:
            self.blockSignals(True)
        self.setValue(internal_value)
        if self.signalsBlocked() and block_signals:
            self.blockSignals(False)

    def _map_value(self, in_value):
        """
        Internal function that converts slider integer value to slider float range value
        :param in_value:
        :return:
        """

        return utils.map_range_unclamped(
            in_value, self.minimum(), self.maximum(), self._slider_range[0], self._slider_range[1])

    def _unmap_value(self, out_value):
        """
        Converts mapped float value to slider integer value
        :param out_value:
        :return:
        """

        return int(utils.map_range_unclamped(
            out_value, self._slider_range[0], self._slider_range[1], self.minimum(), self.maximum()))

    def _on_value_changed(self, x):
        mapped_value = self._map_value(x)
        self.doubleValueChanged.emit(mapped_value)

    def _on_value_incremented(self, step):
        slider_internal_range = (self.minimum(), self.maximum())
        slider_dst = max(slider_internal_range) - min(slider_internal_range)
        value_dst = max(self._slider_range) - min(self._slider_range)
        factor = slider_dst / value_dst
        unmapped_step = step * factor
        current_internal_value = self.value()
        new_unmapped_value = current_internal_value + unmapped_step
        self.setValue(new_unmapped_value)


class HoudiniInputDragger(QWidget, object):
    """
    Widget that allow to drag values when mid click over widget.
    Right Drag increments values and Left Drag decreases value
    """

    def __init__(self, parent, factor, main_color=None, *args, **kwargs):
        super(HoudiniInputDragger, self).__init__(*args, **kwargs)

        self._parent = parent
        self._factor = factor
        self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()
        self._size = 35

        self.setAttribute(Qt.WA_Hover)
        self.setStyleSheet(self._get_style_sheet())
        self.setMinimumHeight(self._size)
        self.setMinimumWidth(self._size)
        self.setMaximumHeight(self._size)
        self.setMaximumWidth(self._size)

        main_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        frame_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._frame = QGroupBox()
        self._frame.setLayout(frame_layout)
        main_layout.addWidget(self._frame)

        self._label = label.BaseLabel('+' + str(factor), parent=self)
        font = self._label.font()
        font.setPointSize(7)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self._label)

        self.installEventFilter(self)
        self._label.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            self.setStyleSheet(self._get_style_sheet(hover_style=True))
            self._parent.active_drag = self
            for drag in self._parent.drags:
                if drag != self:
                    drag.setStyleSheet(self._get_style_sheet())
        if event.type() == QEvent.HoverLeave:
            if event.pos().y() > self.height() or event.pos().y() < 0:
                self.setStyleSheet(self._get_style_sheet())
        if event.type() == QEvent.MouseMove:
            self._parent.eventFilter(self, event)

        return False

    @property
    def factor(self):
        return self._factor

    def _get_style_sheet(self, hover_style=False):
        if hover_style:
            return """
            QGroupBox{
                border: 0.5 solid darkgrey;
                background : %s;
                color: white;
            }
            QLabel{
                background: transparent;
                border: 0 solid transparent;
                color: white;
            }
            """ % "rgba%s" % str(self._main_color)
        else:
            return """
            QGroupBox{
                border: 0.5 solid darkgrey;
                background : black;
                color: white;
            }
            QLabel{
                background: transparent;
                border: 0 solid transparent;
                color: white;
            }
            """


class DraggerSlider(QDoubleSpinBox, object):
    """
    Slider that holds Houdini style draggers to drag values when mid click over them.
    Middle click to display draggers to change value by adding different delta values
    """

    valueIncremented = Signal(object)

    def __init__(self, label_text='', slider_type='float', buttons=False, decimals=3, dragger_steps=None,
                 apply_style=True, main_color=None, *args, **kwargs):
        super(DraggerSlider, self).__init__(*args, **kwargs)

        self._label_text = label_text
        self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()
        self._dragger_steps = dragger_steps or FLOAT_SLIDER_DRAG_STEPS
        self._is_float = slider_type == 'float'
        self._draggers = None

        self.setFocusPolicy(Qt.StrongFocus)
        if not self._is_float:
            self.setDecimals(0)
            self.setRange(qtutils.FLOAT_RANGE_MIN, qtutils.FLOAT_RANGE_MAX)
        else:
            self.setDecimals(decimals)
            self.setRange(qtutils.INT_RANGE_MIN, qtutils.INT_RANGE_MAX)
        if not buttons:
            self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        if apply_style:
            self._label_font = QFont('Serif', 10, QFont.Bold)
            self.setStyleSheet(self._get_style_sheet())
        else:
            self._label_font = self.lineEdit().font()

        self.lineEdit().installEventFilter(self)
        self.installEventFilter(self)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super(DraggerSlider, self).wheelEvent(event)

    def update(self):
        self.setStyleSheet(self._get_style_sheet())

    def paintEvent(self, event):
        super(DraggerSlider, self).paintEvent(event)

        p = QPainter()
        p.begin(self)
        p.setPen(color.DARK_GRAY)
        p.setFont(self._label_font)
        p.drawText(self.rect(), Qt.AlignCenter, self._label_text)
        p.end()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                if not self._draggers:
                    self._draggers = SliderDraggers(self, self._is_float, dragger_steps=self._dragger_steps)
                    self._draggers.increment.connect(self._on_value_incremented)
                self._draggers.show()
                if self._is_float:
                    self._draggers.move(
                        self.mapToGlobal(QPoint(event.pos().x() - 1, event.pos().y() - self._draggers.height() / 2)))
                else:
                    self._draggers.move(
                        self.mapToGlobal(QPoint(event.pos().x() - 1, event.pos().y() - self._draggers.height() + 15)))

        return False

    def _get_style_sheet(self):
        return """
        QWidget{
            border: 1.25 solid black;
        }
        QSlider::groove:horizontal,
            QSlider::sub-page:horizontal {
            background: %s;
        }
        QSlider::add-page:horizontal,
            QSlider::sub-page:horizontal:disabled {
            background: rgb(32, 32, 32);
        }
        QSlider::add-page:horizontal:disabled {
            background: grey;
        }
        QSlider::handle:horizontal {
            width: 1px;
         }
        """ % "rgba%s" % str(self._main_color)

    def _on_value_incremented(self, step):
        self.valueIncremented.emit(step)
        self.setValue(self.value() + step)


@theme.mixin
class HoudiniDoubleSlider(QWidget, object):
    """
    Slider that encapsulates a DoubleSlider and Houdini draggers linked together
    """

    valueChanged = Signal(object)

    def __init__(self, parent, slider_type='float', style=0, name=None, slider_range=None, default_value=0.0,
                 dragger_steps=None, main_color=None, *args):
        if slider_range is None:
            slider_range = (-100.0, 100.0)
        if dragger_steps is None:
            dragger_steps = FLOAT_SLIDER_DRAG_STEPS
        super(HoudiniDoubleSlider, self).__init__(parent=parent, *args)

        h = 20
        self._parent = parent
        self._type = slider_type
        self._value = 0.0
        self._label = None
        self._style_type = style

        theme = self.theme()
        if theme:
            theme_color = theme.accent_color
            if core_color.string_is_hex(theme_color):
                theme_color = core_color.hex_to_rgb(theme_color)
                main_color = QColor(*theme_color).getRgb()

        self._main_color = main_color or QColor(215, 128, 26).getRgb()

        self.setMaximumHeight(h)
        self.setMinimumHeight(h)

        self._main_layout = layouts.HorizontalLayout(margins=(10, 0, 0, 0))
        self.setLayout(self._main_layout)

        self._input = DraggerSlider(slider_type=slider_type)
        self._input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._input.setRange(slider_range[0], slider_range[1])
        self._input.setContentsMargins(0, 0, 0, 0)
        self._input.setMinimumWidth(60 if self._type == 'float' else 40)
        self._input.setMaximumWidth(60 if self._type == 'float' else 40)
        self._input.setMinimumHeight(h)
        self._input.setMaximumHeight(h)
        self._input.valueIncremented.connect(self._on_increment_value)

        if self._type == 'float':
            self._slider = DoubleSlider(parent=self, default_value=default_value, slider_range=slider_range,
                                        dragger_steps=dragger_steps)
        else:
            self._slider = Slider(parent=self, slider_range=slider_range)
            self._slider.valueIncremented.connect(self._on_increment_value)
        self._slider.setContentsMargins(0, 0, 0, 0)
        self._slider.setMinimumHeight(h)
        self._slider.setMaximumHeight(h)
        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        if name:
            self._label = label.BaseLabel(name + '  ', parent=self)
            self._main_layout.addWidget(self._label)
        self._main_layout.addWidget(self._input)
        self._main_layout.addWidget(self._slider)

        style_sheet = self._get_style_sheet(self._style_type)
        if self._style_type == 0:
            self._main_layout.setSpacing(0)
        self._slider.setStyleSheet(style_sheet)

        self._slider.valueChanged.connect(self._on_slider_value_changed)
        self._input.valueChanged.connect(self._on_houdini_slider_value_changed)

    def update(self):
        style_sheet = self._get_style_sheet(self._style_type)
        if self._style_type == 0:
            self._main_layout.setSpacing(0)
        self._slider.setStyleSheet(style_sheet)

    @property
    def minimum(self):
        return self._input.minimum()

    @property
    def maximum(self):
        return self._input.maximum()

    @property
    def _value_range(self):
        return self.maximum - self.minimum

    def _get_value(self):
        return self.value()

    def _set_value(self, value):
        with qt_contexts.block_signals(self):
            self.set_value(value)

    intValue = Property(int, _get_value, _set_value, user=True)
    floatValue = Property(float, _get_value, _set_value, user=True)

    def value(self):
        self._value = self._input.value()
        if self._type == 'int':
            self._value = int(self._value)

        return self._value

    def set_value(self, value):
        self._input.setValue(value)
        self._value = self._input.value()
        self.valueChanged.emit(self.value())
        # self._on_houdini_slider_value_changed(0)

    def set_decimals(self, decimals):
        self._input.setDecimals(decimals)

    def set_single_step(self, step):
        self._input.setSingleStep(step)

    def hide_label(self):
        if self._label:
            self._label.hide()

    def show_label(self):
        if self._label:
            self._label.show()

    def hide_slider(self):
        self._slider.hide()

    def show_slider(self):
        self._slider.show()

    def set_range(self, minimum_value, maximum_value):
        self._input.setRange(minimum_value, maximum_value)

    def _on_increment_value(self, step):
        if step == 0.0:
            return
        old = self._input.value()
        new = old + step
        self._input.setValue(new)
        self.valueChanged.emit(new)

    def _on_slider_value_changed(self, value):
        out_value = utils.map_range_unclamped(
            value, self._slider.minimum(), self._slider.maximum(), self._input.minimum(), self._input.maximum())
        with qt_contexts.block_signals(self._input):
            self._input.setValue(out_value)
        self.valueChanged.emit(out_value)

    def _on_houdini_slider_value_changed(self, value):
        in_value = utils.map_range_unclamped(
            self._input.value(), self._input.minimum(), self._input.maximum(),
            self._slider.minimum(), self._slider.maximum())
        with qt_contexts.block_signals(self._slider):
            self._slider.setValue(int(in_value))
        self.valueChanged.emit(value)

    def _get_style_sheet(self, style_type):
        if style_type == 0:
            return """
            QWidget{
                border: 1.25 solid black;
            }
            QSlider::groove:horizontal,
                QSlider::sub-page:horizontal {
                background: %s;
            }
            QSlider::add-page:horizontal,
                QSlider::sub-page:horizontal:disabled {
                background: rgb(32, 32, 32);
            }
            QSlider::add-page:horizontal:disabled {
                background: grey;
            }
            QSlider::handle:horizontal {
                width: 1px;
             }
            """ % "rgba%s" % str(self._main_color)
        else:
            return """
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 3px;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: %s;
                border: 0px solid #777;
                height: 3px;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #fff;
                border: 1px solid #777;
                height: 3px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eee, stop:1 #ccc);
                border: 1px solid #777;
                width: 4px;
                margin-top: -8px;
                margin-bottom: -8px;
                border-radius: 2px;
                height : 10px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fff, stop:1 #ddd);
                border: 1px solid #444;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal:disabled {
                background: #bbb;
                border-color: #999;
            }
            QSlider::add-page:horizontal:disabled {
                background: #eee;
                border-color: #999;
            }
            QSlider::handle:horizontal:disabled {
                background: #eee;
                border: 1px solid #aaa;
                border-radius: 2px;
                height : 10;
            }
            """ % "rgba%s" % str(self._main_color)
