#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create attribute editors
"""

from Qt.QtCore import Qt, Signal, QPoint, QPointF, QSize, QRegExp
from Qt.QtWidgets import QWidget, QGroupBox, QScrollArea, QLineEdit, QCheckBox, QSlider, QColorDialog
from Qt.QtGui import QColor, QPalette

from tp.core import log
from tp.common.python import strings as string_utils
from tp.common.qt import qtutils, base
from tp.common.qt.widgets import layouts, lineedits, directory, color

logger = log.tpLogger


class AttributeEditor(base.BaseWidget, object):
    def __init__(self, name='AttributeEditor', label='Attribute Editor', parent=None):
        self._label = label
        self._objects = list()
        super(AttributeEditor, self).__init__(parent=parent)
        self.setObjectName(name)

    def get_objects(self):
        return self._objects

    objects = property(get_objects)

    def ui(self):
        super(AttributeEditor, self).ui()

        self._main_group = QGroupBox()
        self._main_group.setProperty('class', 'attr_main_group')
        self._main_group.setFlat(False)
        self._main_group.setTitle('')

        self._main_group_layout = self.get_attributes_layout()
        self._main_group.setLayout(self._main_group_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: rgb(57,57,57);}')
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(self._main_group)

        self.main_layout.addWidget(scroll_area)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_create_context_menu)

    def get_attributes_layout(self):
        """
        Returns layout used for the attributes
        :return: QLayout
        """

        attributes_layout = layouts.HorizontalLayout(margins=(5, 5, 5, 5))
        attributes_layout.setAlignment(Qt.AlignTop)

        return attributes_layout

    def set_title(self, new_title):
        self._main_group.setTitle(new_title)

    def clear_layout(self, reset_title=True):
        """
        Clears main layout and resetes editor title
        """

        qtutils.clear_layout(self._main_group_layout)
        if reset_title:
            self._main_group.setTitle('')

    def _build_layout(self):
        pass

    def _on_create_context_menu(self):
        pass


class BaseEditor(QWidget, object):
    attr_type = 'None'
    valueChanged = Signal(object)

    def __init__(self, parent=None, **kwargs):
        super(BaseEditor, self).__init__(parent=parent)

        self._default_value = 0.0
        self._current_value = None

        self.main_layout = layouts.HorizontalLayout(spacing=3, margins=(1, 1, 1, 1), parent=self)

    def get_default_value(self):
        return self._default_value

    def set_default_value(self, value):
        if value != self._default_value:
            self._default_value = value

    def get_value(self):
        return None

    def set_value(self, value):
        pass

    default_value = property(get_default_value, set_default_value)
    value = property(get_value)

    def OnValueUpdated(self):
        if self.value != self._current_value:
            self._current_value = self.value
            self.valueChanged.emit(self)

    def initialize_editor(self):
        pass


class FloatEditor(BaseEditor, object):

    attr_type = 'float'

    def __init__(self, parent=None, **kwargs):
        super(FloatEditor, self).__init__(parent=parent, **kwargs)

        self._default_value = 0.0

        self.value_line = lineedit.FloatLineEdit(self)
        self.main_layout.addWidget(self.value_line)

    def get_value(self):
        return self.value_line.value

    value = property(get_value)

    def initialize_editor(self):
        editor_value = self.default_value

        node_values = self.values
        if node_values:
            if len(node_values) > 1:
                pass
            elif len(node_values) == 1:
                if node_values[0]:
                    editor_value = node_values[0]
                if node_values[0] is None:
                    editor_value = self.default_value

                self.value_line.blockSignals(True)
                self.value_line.setText(str(editor_value))
                self.value_line.blockSignals(False)
                self.value_line.valueChanged.connect(self.OnValueUpdated)

    def set_connected(self, conn):
        if conn != self._connection:
            self._connection = conn
            self.value_line.setText(conn)
            self.value_line.setEnabled(False)
            self.value_line.setProperty('class', 'Connected')


class Float2Editor(BaseEditor, object):

    attr_type = 'float'

    def __init__(self, parent=None, **kwargs):
        super(Float2Editor, self).__init__(parent=parent, **kwargs)

        self._default_value = (0.0, 0.0)

        self.value1_line = lineedit.FloatLineEdit(self)
        self.value2_line = lineedit.FloatLineEdit(self)
        self.main_layout.addWidget(self.value1_line)
        self.main_layout.addWidget(self.value2_line)

    def get_value(self):
        return self.value1_line.value, self.value2_line.value

    value = property(get_value)

    def initialize_editor(self):
        editor_value = self.default_value

        node_values = self.values
        if node_values:
            if len(node_values) > 1:
                pass
            elif len(node_values) == 1:
                if node_values[0]:
                    editor_value = node_values[0]

                self.value1_line.blockSignals(True)
                self.value2_line.blockSignals(True)

                if type(editor_value) in [QPoint, QPointF]:
                    self.value1_line.setText(str(editor_value.x()))
                    self.value2_line.setText(str(editor_value.y()))
                elif type(editor_value) in [list, tuple]:
                    self.value1_line.setText(str(editor_value[0]))
                    self.value2_line.setText(str(editor_value[1]))
                self.value1_line.blockSignals(False)
                self.value2_line.blockSignals(False)
                self.value1_line.valueChanged.connect(self.OnValueUpdated)
                self.value2_line.valueChanged.connect(self.OnValueUpdated)

    def set_connected(self, conn):
        if conn != self._connection:
            self._conection = conn
            self.value1_line.setText(conn)
            self.value1_line.setEnabled(False)
            self.value2_line.setEnabled(False)
            self.value1_line.setProperty('class', 'Connected')
            self.value2_line.setProperty('class', 'Connected')


class Float3Editor(BaseEditor, object):

    attr_type = 'float'

    def __init__(self, parent=None, **kwargs):
        super(Float3Editor, self).__init__(parent=parent, **kwargs)

        self._default_value = (0.0, 0.0, 0.0)

        self.value1_line = lineedit.FloatLineEdit(self)
        self.value2_line = lineedit.FloatLineEdit(self)
        self.value3_line = lineedit.FloatLineEdit(self)
        self.main_layout.addWidget(self.value1_line)
        self.main_layout.addWidget(self.value2_line)
        self.main_layout.addWidget(self.value3_line)

    def get_value(self):
        return self.value1_line.value(), self.value2_line.value(), self.value3_line.value()

    value = property(get_value)

    def initialize_editor(self):
        editor_value = self.default_value

        node_values = self.values
        if node_values:
            if len(node_values) > 1:
                pass
            elif len(node_values) == 1:
                if node_values[0]:
                    editor_value = node_values[0]

                self.value1_line.blockSignals(True)
                self.value2_line.blockSignals(True)
                self.value3_line.blockSignals(True)
                self.value1_line.setText(str(editor_value[0]))
                self.value2_line.setText(str(editor_value[1]))
                self.value3_line.setText(str(editor_value[2]))
                self.value1_line.blockSignals(False)
                self.value2line.blockSignals(False)
                self.value3line.blockSignals(False)
                self.value1_line.valueChanged.connect(self.OnValueUpdated)
                self.value2_line.valueChanged.connect(self.OnValueUpdated)
                self.value3_line.valueChanged.connect(self.OnValueUpdated)

    def set_connected(self, conn):
        if conn != self._connection:
            self._conection = conn
            self.value1_line.setText(conn)
            self.value1_line.setEnabled(False)
            self.value2_line.setEnabled(False)
            self.value3_line.setEnabled(False)
            self.value1_line.setProperty('class', 'Connected')
            self.value2_line.setProperty('class', 'Connected')
            self.value3_line.setProperty('class', 'Connected')


class StringEditor(BaseEditor, object):

    attr_type = 'str'

    def __init__(self, parent=None, **kwargs):
        super(StringEditor, self).__init__(parent=parent, **kwargs)

        self._default_value = ""
        self._clean_value = kwargs.get('clean', True)

        self.value_line = QLineEdit(self)
        reg_exp = QRegExp('^([a-zA-Z0-9_]+)')
        self.main_layout.addWidget(self.value_line)

        self.value_line.textEdited.connect(self._validate_text)
        self.value_line.editingFinished.connect(self.OnValueUpdated)
        self.value_line.returnPressed.connect(self.OnValueUpdated)

    def get_value(self):
        return str(self.value_line.text())

    value = property(get_value)

    def initialize_editor(self):
        editor_value = self.default_value

        node_values = self.values
        if node_values:
            if len(node_values) > 1:
                pass
            elif len(node_values) == 1:
                if node_values[0]:
                    editor_value = node_values[0]

                self.value_line.blockSignals(True)
                self.value_line.setText(str(editor_value))
                self.value_line.blockSignals(False)

    def set_connected(self, conn):
        if conn != self._connection:
            self._connection = conn
            self.value_line.setText(conn)
            self.value_line.setEnabled(False)
            self.value_line.setProperty('class', 'Connected')

    def _validate_text(self, text):
        """
        Validates the given value and update the current text
        :param text: str, text to validate
        """

        current_text = self.value
        if self._clean_value:
            cursor_pos = self.value_line.cursorPosition()
            cleaned = string_utils.clean_string(text=text)
            self.value_line.blockSignals(True)
            self.value_line.setText(cleaned)
            self.value_line.blockSignals(False)
            self.value_line.setCursorPosition(cursor_pos)


class BoolEditor(BaseEditor, object):

    attr_type = 'bool'

    def __init__(self, parent=None, **kwargs):
        super(BoolEditor, self).__init__(parent=parent, **kwargs)

        self._default_value = False

        self.cbx = QCheckBox(self)
        self.main_layout.addWidget(self.cbx)

        self.cbx.toggled.connect(self.OnValueUpdated)

    def get_value(self):
        return self.cbx.isChecked()

    def initialize_editor(self):
        editor_value = self.default_value

        node_values = self.values
        if node_values:
            if len(node_values) > 1:
                pass
            elif len(node_values) == 1:
                if node_values[0]:
                    editor_value = node_values[0]

                self.cbx.blockSignals(True)
                self.cbx.setChecked(editor_value)
                self.cbx.blockSignals(False)

    def set_connected(self, conn):
        if conn != self._connection:
            self._connection = conn
            self.value_line.setText(conn)
            self.cbx.setEnabled(False)
            self.value_line.setProperty('class', 'Connected')


class ColorPicker(BaseEditor, object):

    attr_type = 'color'

    def __init__(self, parent=None, **kwargs):
        super(ColorPicker, self).__init__(parent=parent, **kwargs)

        self._default_value = (125, 125, 125)
        self.attr = None

        self.normalized = kwargs.get('normalized', False)
        self.min = kwargs.get('min', 0)
        self.max = kwargs.get('max', 99)
        self.color = kwargs.get('color', QColor(1.0, 1.0, 1.0))
        self.mult = kwargs.get('mult', 0.1)

        self.color_swatch = color.ColorSwatch(parent=self, color=self.color, normalized=self.normalized)
        self.color_swatch.setMaximumSize(QSize(75, 20))
        self.color_swatch.setMinimumSize(QSize(75, 20))
        self.color_swatch.set_color(color=self.color)
        self.main_layout.addWidget(self.color_swatch)

        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setValue(self.max)
        self.main_layout.addWidget(self.slider)

        self.set_max(self.max)
        self.set_min(self.min)

        self.slider.valueChanged.connect(self.OnSliderChanged)
        self.slider.sliderReleased.connect(self.OnSliderReleased)
        self.color_swatch.clicked.connect(self.OnColorPicked)

    # region Properties
    def get_rgb(self):
        return self.color_swatch.qcolor.getRgb()[0:3]

    def get_rgbF(self):
        return self.color_swatch.qcolor.getRgbF()[0:3]

    def get_hsv(self):
        return self.color_swatch.qcolor.getHsv()[0:3]

    def get_hsvF(self):
        return self.color_swatch.qcolor.getHsvF()[0:3]

    rgb = property(get_rgb)
    rgbF = property(get_rgbF)
    hsv = property(get_hsv)
    gsvF = property(get_hsvF)

    def OnSliderChanged(self):
        slider_value = float(self.slider.value())
        if not self._current_value:
            logger.debug(
                'Caching color: (%d, %d, %d)' % (
                    self.color_swatch.color[0], self.color_swatch.color[1], self.color_swatch.color[2]))
            self._current_value = self.color_swatch.color
        current_color = QColor(*self._current_value)
        darker = 200 - slider_value
        new_color = current_color.darker(darker)
        self.color_swatch.qcolor = new_color
        self.color_swatch._update()

    def OnSliderReleased(self):
        """
        Updates items color when the slider handle is released
        """

        color = self.color_swatch.color
        self.color_swatch._update()
        self.OnValueUpdated()

    def OnColorPicked(self):
        """
        Event to call color picker
        """

        dialog = QColorDialog(self.color_swatch.qcolor, self)
        if dialog.exec_():
            self.color_swatch.setPalette(QPalette(dialog.currentColor()))
            self.color_swatch.qcolor = dialog.currentColor()
            self.color_swatch._update()
            self.OnValueUpdated()

    def get_value(self):
        return self.color_swatch.color

    def initialize_editor(self):
        editor_value = self.default_value

        node_values = self.values
        if node_values:
            if len(node_values) > 1:
                pass
            elif len(node_values) == 1:
                if node_values[0]:
                    editor_value = node_values[0]

                self.color_swatch.set_color(editor_value)

    def set_connected(self, conn):
        if conn != self._connection:
            self._connection = conn
            self.value_line.setText(conn)
            self.color_swatch.setEnabled(False)

    def sizeHint(self):
        return QSize(350, 27)

    def set_attr(self, value):
        self.attr = value
        return self.attr

    def get_attr(self):
        return self.attr

    def set_min(self, value):
        """
        Sets the slider minimum value
        :param value: int, slider minimum value
        """

        self.min = value
        self.slider.setMinimum(value)

    def set_max(self, value):
        """
        Sets the silder maximum value
        :param value: int, slider maximum value
        """

        self.max = value
        self.slider.setMaximum(value)

    def get_qcolor(self):
        return self.color_swatch.qcolor

    def set_color(self, value):
        return self.color_swatch.set_color(color=value)

    def _update(self):
        return self.color_swatch._update()


class FileEditor(BaseEditor, object):

    attr_type = 'file'

    def __init__(self, parent=None, **kwargs):
        super(FileEditor, self).__init__(parent=parent, **kwargs)

        line_widget = directory.SelectFile()
        self.main_layout.addWidget(line_widget)


# ===============================================================================

WIDGET_MAPPER = dict(
    float=[FloatEditor, 0.0],
    float2=[Float2Editor, [0.0, 0.0]],
    float3=[Float3Editor, [0.0, 0.0, 0.0]],
    bool=[BoolEditor, False],
    str=[StringEditor, ""],
    string=[StringEditor, ""],
    file=[FileEditor, ""],
    dir=[FileEditor, ""],
    # int=[IntEditor, 0],
    # int2=[Int2Editor, [0,0]],
    # int3=[Int3Editor, [0,0,0]],
    # int8=[IntEditor, 0],
    color=[ColorPicker, [172, 172, 172, 255]],
    # short2=[Float2Editor, [0.0, 0.0]],
    # node=[StringEditor, ""],
    # multi=[StringEditor, ""],
    # doc=[DocumentEditor, ""]
)


def map_widget(attr_type, name, parent=None):
    """
    Map the widget to the attribute type
    :param attr_type:
    :param name:
    :param parent:
    :return:
    """

    widget_type = attr_type.replace(' ', '').lower()
    if widget_type not in WIDGET_MAPPER:
        LOGGER.warning('Invalid Editor Class: "{0}" ("{1}")'.format(attr_type, name))
    else:
        cls = WIDGET_MAPPER.get(widget_type)[0]
        return cls(parent=parent, name=name)
    return
