#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains form field widgets
"""

import re
import logging
import traceback
from functools import partial

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QSizePolicy, QFrame, QMenu, QFileDialog, QTextEdit
from Qt.QtGui import QCursor, QColor, QPixmap, QIntValidator

from tpDcc.managers import resources
from tpDcc.libs.python import decorators, path as path_utils
from tpDcc.libs.resources.core import color as qt_color
from tpDcc.libs.qt.core import contexts as qt_contexts
from tpDcc.libs.qt.widgets import layouts, label, buttons, checkbox, lineedit, combobox, color, sliders, dividers
from tpDcc.libs.qt.widgets import group, message, icon

LOGGER = logging.getLogger('tpDcc-libs-qt')


class FieldWidget(QFrame, object):

    valueChanged = Signal()

    DEFAULT_LAYOUT = 'horizontal'

    def __init__(self, parent=None, data=None, form_widget=None):
        super(FieldWidget, self).__init__(parent)

        self._data = data or dict()
        self._widget = None
        self._default = None
        self._required = None
        self._error_label = None
        self._menu_button = None
        self._action_result = None
        self._form_widget = None
        self._collapsed = False
        if form_widget:
            self.set_form_widget(form_widget)

        self.setObjectName('fieldWidget')

        direction = self._data.get('layout', self.DEFAULT_LAYOUT)
        if direction == 'vertical':
            main_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        else:
            main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        self._label = label.BaseLabel(parent=self)
        self._label.setObjectName('label')
        self._label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        main_layout.addWidget(self._label)

        self._layout2 = layouts.HorizontalLayout()
        main_layout.addLayout(self._layout2)
        if direction == 'vertical':
            self._label.setAlignment(Qt.AlignLeft | Qt .AlignVCenter)
        else:
            self._label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        widget = self.create_widget()
        if widget:
            self.set_widget(widget)

    # =================================================================================================================
    # ABSTRACT FUNCTIONS
    # =================================================================================================================

    @decorators.abstractmethod
    def value(self):
        """
        Returns the current value fo the field widget
        :return: variant
        """

        raise NotImplementedError('value function of FieldWidget is not implemented!')

    @decorators.abstractmethod
    def set_items(self, items):
        """
        Sets the items for the field widget
        :param items: list(str)
        """

        raise NotImplementedError('set_items function of FieldWidget is not implemented!')

    @decorators.abstractmethod
    def set_placeholder(self, placeholder):
        """
        Sets the placeholder text to de displayed for the widget
        :param placeholder: str
        """

        raise NotImplementedError('set_placeholder function of FieldWidget is not implemented!')

    # =================================================================================================================
    # STATIC FUNCTIONS
    # =================================================================================================================

    @staticmethod
    def to_title(name):
        """
        Converts camel case strings to title strings
        :param name: str
        :return: str
        """

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).title()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def name(self):
        """
        Returns the name of the field widget
        :return: str
        """

        return self.data()['name']

    def default_data(self):
        """
        Default data used by the field schema
        :return: dict
        """

        return dict()

    def is_collapsed(self):
        """
        Returns whether or not the field widget is collapsed/visible
        :return: bool
        """

        return self._collapsed

    def set_collapsed(self, flag):
        """
        Sets whether or not the field widget is collapsed/visible
        :param flag: bool
        """

        self._collapsed = flag

    def is_default(self):
        """
        Returns whether the current value is the same as the default value or not
        :return: bool
        """

        return self.value() == self.default()

    def default(self):
        """
        Returns the default value for the field widget
        :return: variant
        """

        return self._default

    def set_default(self, default):
        """
        Sets teh default value for the field widget
        :param default: variant
        """

        self._default = default

    def is_required(self):
        """
        Returns whether current field is required for the field widget or not
        :return: bool
        """

        return bool(self._required)

    def set_required(self, flag):
        """
        Sets whether the field is required for the field widget or not
        :param flag: bool
        """

        self._required = flag
        self.setProperty('required', flag)
        # self.setStyleSheet(self.styleSheet())

    def set_value(self, value):
        """
        Sets the value of the field widget
        :param value: variant
        """

        self._on_emit_value_changed()

    def state(self):
        """
        Returns the current state of the data
        :return: dict
        """

        return {
            'name': self._data['name'],
            'value': self.value()
        }

    def data(self):
        """
        Returns the data for the widget
        :return: dict
        """

        return self._data

    def set_data(self, data):
        """
        Sets the current state of the field widget using a dictionary
        :param data: dict
        """

        state = data

        with qt_contexts.block_signals(self):
            items = state.get('items', None)
            if items is not None:
                self.set_items(items)

            value = state.get('value', None)
            default = state.get('default', None)

            if default is not None:
                self.set_default(default)
            elif value is not None:
                self.set_default(value)

            if value is not None or (value and value != self.value()):
                try:
                    self.set_value(value)
                except TypeError:
                    LOGGER.exception(str(traceback.format_exc()))

            enabled = state.get('enabled', None)
            if enabled is not None:
                self.setEnabled(enabled)
                self._label.setEnabled(enabled)
            hidden = state.get('hidden', None)
            if hidden is not None:
                self.setHidden(hidden)
            required = state.get('required', None)
            if required is not None:
                self.set_required(required)
            error = state.get('error', None)
            if error is not None:
                self.set_error(error)
            error_visible = data.get('errorVisible')
            if error_visible is not None:
                self.set_error_visible(error_visible)
            tooltip = state.get('toolTip', None)
            if tooltip is not None:
                self.setToolTip(tooltip)
                self.setStatusTip(tooltip)
            style = state.get('style', None)
            if style is not None:
                self.setStyleSheet(style)
            title = self.title() or ''
            self.set_text(title)
            lbl = state.get('label')
            if lbl is not None:
                text = lbl.get('name', None)
                if text is not None:
                    self.set_text(text)
                visible = lbl.get('visible', None)
                if visible is not None:
                    self.label().setVisible(visible)

            # Menu items
            actions = state.get('actions', None)
            if actions is not None:
                self._menu_button.setVisible(True)
            menu = state.get('menu', None)
            if menu is not None:
                text = menu.get('name')
                if text is not None:
                    self._menu_button.setText(text)
                visible = menu.get('visible', True)
                self._menu_button.setVisible(visible)
            self._data.update(data)
            self.refresh()

    def has_error(self):
        """
        Returns whether or not this field contains any error
        :return: bool
        """

        return bool(self.data().get('error'))

    def set_error(self, message):
        """
        Sets the error message to be displayed for the field widget
        :param message: str
        """

        self._data['error'] = message
        self.refresh_error()

    def set_error_visible(self, flag):
        """
        Sets wehether or not the error message should be displayed
        :param flag: bool
        """

        self._data['errorVisible'] = flag
        self.refresh_error()

    def refresh_error(self):
        """
        Refreshes the error message with the current data
        """

        error = self._data.get('error', None)
        if self.has_error() and self.data().get('errorVisible', False):
            self._error_label.text = error
            self._error_label.setHidden(False)
            self.setToolTip(error)
        else:
            self._error_label.text = ''
            self._error_label.setHidden(True)
            self.setToolTip(self.data().get('toolTip'))

        self.refresh()

    # =================================================================================================================
    # UI
    # =================================================================================================================

    def label(self):
        """
        Returns label widget
        :return: QLabel
        """

        return self._label

    def set_text(self, text):
        """
        Sets the label text for the field widget
        :param text: str
        """

        self._label.setText(text)

    def form_widget(self):
        """
        Returns the form widget that contains the field widget
        :return: FormWidget
        """

        return self._form_widget

    def set_form_widget(self, form_widget):
        """
        Sets the form widget that contains the field widget
        :param form_widget: FormWidget
        """

        self._form_widget = form_widget

    def create_widget(self):
        """
        Creates the widget to be used by the field
        :return: QWidget or None
        """

        return None

    def title(self):
        """
        Returns the title to be displayed for the field
        :return: str
        """

        data = self.data()
        title = data.get('title', '') or data.get('name', '')
        if title:
            title = self.to_title(title)

        if self.is_required():
            title += '*'

        return title

    def widget(self):
        """
        Returns the widget used to set and get the field value
        :return: QWidget
        """

        return self._widget

    def set_widget(self, widget):
        """
        Sets the widget used to set and get the field value
        :param widget: QWidget
        """

        widget_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))

        self._widget = widget
        self._widget.setParent(self)
        self._widget.setObjectName('widget')
        # self._widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._menu_button = buttons.BaseButton()
        self._menu_button.setIcon(resources.icon('menu_dots'))
        self._menu_button.setHidden(True)
        self._menu_button.setObjectName('menuButton')
        # self._menu_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._menu_button.clicked.connect(self._on_menu_callback)

        widget_layout.addWidget(self._widget)
        widget_layout.addWidget(self._menu_button)

        layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))

        self._error_label = message.BaseMessage(parent=self).error().set_show_icon(False)
        self._error_label.setMaximumHeight(40)
        self._error_label.setHidden(True)
        self._error_label.setObjectName('errorLabel')
        self._error_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addLayout(widget_layout)
        layout.addWidget(self._error_label)

        self._layout2.addLayout(layout)

    def reset(self):
        """
        Resets the field widget back to its default values
        """

        self.set_state(self._data)

    def refresh(self):
        """
        Refresh the style properties of the field
        """

        direction = self._data.get('layout', self.DEFAULT_LAYOUT)
        self.setProperty('layout', direction)
        self.setProperty('default', self.is_default())
        if self.data().get('errorVisible', False):
            self.setProperty('error', self.has_error())

        self.setStyleSheet(self.styleSheet())

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _action_callback(self, callback):
        """
        Internal function that wraps schema callback to get the return value
        :param callback: fn
        """

        self._action_result = callback()

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_menu_callback(self):
        """
        Internal callback function that is triggered when the menu button is clicked
        """

        callback = self.data().get('menu', {}).get('callback', self._on_show_menu)
        callback()

    def _on_show_menu(self):
        """
        Internal callback that shows field menu using the actions from the data
        """

        menu = QMenu(self)

        actions = self.data().get('actions', list())
        for action in actions:
            name = action.get('name', 'No name found')
            enabled = action.get('enabled', True)
            callback = action.get('callback')
            fn = partial(self._action_callback, callback)
            action = menu.addAction(name)
            action.setEnabled(enabled)
            action.triggered.connect(fn)

        point = QCursor.pos()
        point.setX(point.x() + 3)
        point.setY(point.y() + 3)

        self._action_result = None

        menu.exec_(point)

        if self._action_result is not None:
            self.set_value(self._action_result)

    def _on_emit_value_changed(self, *args):
        """
        Emits the value changed signal
        :param args: list
        """

        self.valueChanged.emit()
        self.refresh()


class IntFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(IntFieldWidget, self).__init__(*args, **kwargs)

        widget = sliders.BaseSlider(parent=self)
        widget.setMinimum(-50000000)
        widget.setMaximum(50000000)
        widget.valueChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the widget
        :return: str
        """

        value = self.widget().value()

        return int(value)

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the widget
        :param value: str
        """

        if value == '':
            value = self.default()

        self.widget().setValue(int(value))


class BoolFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(BoolFieldWidget, self).__init__(*args, **kwargs)

        widget = checkbox.BaseCheckBox(parent=self)
        widget.stateChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def set_text(self, text):
        """
        Sets the label text for the field widget
        Override to support inline key.
        :param text: str
        """

        inline = self.data().get('inline')
        if inline:
            self.label().setText('')
            self.widget().setText(text)
        else:
            super(BoolFieldWidget, self).set_text(text)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the checkbox
        :return: str
        """

        return bool(self.widget().isChecked())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the checkbox
        :param value: str
        """

        self.widget().setChecked(value)
        super(BoolFieldWidget, self).set_value(value)


class EnumFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(EnumFieldWidget, self).__init__(*args, **kwargs)

        widget = combobox.BaseComboBox(parent=self)
        widget.currentIndexChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the combo box
        :return: str
        """

        return str(self.widget().currentText())

    def set_value(self, item):
        """
        Overrides FileWidget set_value function
        Sets the value of the combo box
        :param item: str
        """

        self.set_current_text(item)

    def set_items(self, items):
        """
        Overrides FieldWidget set_items function
        Sets the current items of the combo box
        :param items: list(str)
        """

        self.widget().clear()
        self.widget().addItems(items)

    def set_state(self, state):
        """
        Sets the current state with support for editable
        :param state: dict
        """

        super(EnumFieldWidget, self).set_state(state)
        editable = state.get('editable')
        if editable is not None:
            self.widget().setEditable(editable)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_current_text(self, text):
        """
        Sets current text
        :param text: str
        """

        index = self.widget().findText(text, Qt.MatchExactly)
        if index != -1:
            self.widget().setCurrentIndex(index)
        else:
            LOGGER.warning('Cannot set the value for field {}'.format(self.name()))


class StringFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(StringFieldWidget, self).__init__(*args, **kwargs)

        widget = lineedit.BaseLineEdit(parent=self)
        widget.textChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the widget
        :return: str
        """

        return str(self.widget().text())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the widget
        :param value: str
        """

        pos = self.widget().cursorPosition()

        with qt_contexts.block_signals(self.widget()):
            self.widget().setText(value)

        self.widget().setCursorPosition(pos)

        super(StringFieldWidget, self).set_value(value)


class StringDoubleFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(StringDoubleFieldWidget, self).__init__(*args, **kwargs)

        widget = QFrame(self)
        layout = layouts.HorizontalLayout(spacing=4, margins=(0, 0, 0, 0))
        widget.setLayout(layout)

        self._widget1 = lineedit.BaseLineEdit(parent=self)
        self._widget2 = lineedit.BaseLineEdit(parent=self)
        self._widget1.textChanged.connect(self._on_emit_value_changed)
        self._widget2.textChanged.connect(self._on_emit_value_changed)
        layout.addWidget(self._widget1)
        layout.addWidget(self._widget2)

        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def set_placeholder(self, placeholder):
        """
        Sets the placeholder text to de displayed for the widget
        :param placeholder: str
        """

        if isinstance(placeholder, (list, tuple)):
            if len(placeholder) >= 1:
                self._widget1.setPlaceholderText(placeholder[0])
            if len(placeholder) >= 2:
                self._widget2.setPlaceholderText(placeholder[1])
        else:
            self._widget1.setPlaceholderText(str(placeholder))

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the widget
        :return: str
        """

        value1 = self._widget1.text() or ''
        value2 = self._widget2.text() or ''

        return value1, value2

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the widget
        :param value: str
        """

        self._widget1.setText(str(value[0]))
        self._widget2.setText(str(value[1]))

        super(StringDoubleFieldWidget, self).set_value(value)


class PasswordFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(PasswordFieldWidget, self).__init__(*args, **kwargs)

        widget = label.QLineEdit(self)
        widget.setEchoMode(lineedit.BaseLineEdit.EchoMode.Password)
        widget.textChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the widget
        :return: str
        """

        return str(self.widget().text())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the widget
        :param value: str
        """

        self.widget().setText(value)
        super(PasswordFieldWidget, self).set_value(value)


class TextFieldWidget(FieldWidget, object):

    DEFAULT_LAYOUT = 'vertical'

    def __init__(self, *args, **kwargs):
        super(TextFieldWidget, self).__init__(*args, **kwargs)

        widget = QTextEdit(parent=self)
        # widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        widget.textChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the text edit
        :return: str
        """

        return str(self.widget().toPlainText())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the text edit
        :param value: str
        """

        print(value)
        self.widget().setText(value)
        super(TextFieldWidget, self).set_value(value)


class PathFieldWidget(StringFieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(PathFieldWidget, self).__init__(*args, **kwargs)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def set_data(self, data):
        """
        Overrides StringFieldWidget set_data function
        Adds a browse button to folder button
        :param data: dict
        """

        if 'menu' not in data:
            data['menu'] = {
                'callback': self._on_browse
            }

        super(PathFieldWidget, self).set_data(data)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_browse(self):
        """
        Opens file dialog
        """

        path = self.value()
        path = QFileDialog.getExistingDirectory(None, 'Browse Folder', path)
        if path:
            self.set_value(path)


class SeparatorFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(SeparatorFieldWidget, self).__init__(*args, **kwargs)

        widget = dividers.Divider()
        widget.setObjectName('widget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.set_widget(widget)
        if not self.data().get('title'):
            self.label().hide()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the separator
        :return: str
        """

        return str(self.widget().get_text())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the separator
        :param value: str
        """

        self.widget().set_text(str(value))


class LabelFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(LabelFieldWidget, self).__init__(*args, **kwargs)

        widget = label.RightElidedLabel(parent=self)
        widget.setAlignment(Qt.AlignVCenter)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the label
        :return: str
        """

        try:
            return str(self.widget().text())
        except Exception:
            return str(path_utils.normalize_path(self.widget().text()))

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the label
        :param value: str
        """

        self.widget().setText(value)
        super(LabelFieldWidget, self).set_value(value)


class ImageFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(ImageFieldWidget, self).__init__(*args, **kwargs)

        self._value = ''
        self._pixmap = None

        widget = label.BaseLabel(parent=self)
        widget.setObjectName('widget')
        self.setStyleSheet('min-height: 32px;')
        widget.setScaledContents(False)
        widget.setAlignment(Qt.AlignHCenter)
        self.set_widget(widget)
        self.layout().addStretch()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def resizeEvent(self, event):
        """
        Overrides FieldWidget resizeEvent function
        Called when teh field widget is resized
        :param event: QResizeEvent
        """

        self.update()

    def value(self):
        """
        Implements FieldWidget value function
        Returns the path of the image in disk
        :return: str
        """

        return self._value

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the path of the image in disk
        :param value: str
        """

        self._value = value
        self._pixmap = QPixmap(value)
        self.update()

    def update(self):
        """
        Updates the image depending on the size
        """

        if not self._pixmap:
            return

        width = self.widget().height()
        if self.widget().width() > self.widget().height():
            pixmap = self._pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        else:
            pixmap = self._pixmap.scaledToHeight(width, Qt.SmoothTransformation)
        self.widget().setPixmap(pixmap)
        self.widget().setAlignment(Qt.AlignLeft)


class RadioFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(RadioFieldWidget, self).__init__(*args, **kwargs)

        self._radio_buttons = list()

        layout = layouts.VerticalLayout(margins=(0, 0, 0, 0))
        self._radio_frame = QFrame(self)
        self._radio_frame.setLayout(layout)

        self.set_widget(self._radio_frame)

        self.label().setStyleSheet('margin-top: 2px;')
        self.label().setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.widget().setStyleSheet('margin-top: 2px;')

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the path of the image in disk
        :return: str
        """

        for radio_button in self._radio_buttons:
            if radio_button.isChecked():
                return radio_button.text()

        return ''

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the path of the image in disk
        :param value: str
        """

        for radio_button in self._radio_buttons:
            checked = radio_button.text() == value
            radio_button.setChecked(checked)

    def set_items(self, items):
        """
        Sets the items for the field widget
        :param items: list(str)
        """

        self.clear()

        for item in items:
            widget = buttons.BaseRadioButton(parent=self)
            widget.setText(item)
            widget.clicked.connect(self._on_emit_value_changed)
            self._radio_buttons.append(widget)
            self._radio_frame.layout().addWidget(widget)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def clear(self):
        """
        Destroy all radio buttons
        """

        for radio_button in self._radio_buttons:
            radio_button.destroy()
            radio_button.close()
            radio_button.hide()


class SliderFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(SliderFieldWidget, self).__init__(*args, **kwargs)

        widget = sliders.DoubleSlider(parent=self)
        widget.setOrientation(Qt.Horizontal)
        widget.setObjectName('widget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        widget.valueChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the slider
        :return: str
        """

        return self.widget().value()

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the slider
        :param value: str
        """

        self.widget().setValue(value)


class RangeFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(RangeFieldWidget, self).__init__(*args, **kwargs)

        widget = QFrame(self)
        layout = layouts.HorizontalLayout(spacing=4, margins=(0, 0, 0, 0))
        widget.setLayout(layout)

        validator = QIntValidator(-50000000, 50000000, self)

        self._min_widget = lineedit.BaseLineEdit(parent=self)
        self._min_widget.setValidator(validator)
        self._min_widget.textChanged.connect(self._on_emit_value_changed)
        widget.layout().addWidget(self._min_widget)

        self._max_widget = lineedit.BaseLineEdit(parent=self)
        self._max_widget.setValidator(validator)
        self._max_widget.textChanged.connect(self._on_emit_value_changed)
        widget.layout().addWidget(self._max_widget)

        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Implements FieldWidget value function
        Returns the current range
        :return: list(int)
        """

        min_value = int(float(self._min_widget.text() or '0'))
        max_value = int(float(self._max_widget.text() or '0'))

        return min_value, max_value

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the current range
        :param value: list(int)
        """

        min_value, max_value = int(value[0], int(value[1]))
        self._min_widget.setText(str(min_value))
        self._max_widget.setText(str(max_value))

        super(RangeFieldWidget, self).set_value(value)


class ColorFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(ColorFieldWidget, self).__init__(*args, **kwargs)

        widget = color.ColorPicker()
        widget.setObjectName('widget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        widget.colorChanged.connect(self._on_color_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def set_data(self, data):
        """
        Overrides FieldWidget data function
        :param data: dict
        """

        colors = data.get('colors')
        if colors:
            self.widget().set_colors(colors)

        super(ColorFieldWidget, self).set_data(data)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the color picker
        :return: Color
        """

        return self.widget().current_color()

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the color picker
        :param value: str
        """

        self.widget().set_current_color(value)

    def set_items(self, items):
        """
        Sets the items for the field widget
        :param items: list(str)
        """

        self.widget().set_colors(items)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_color_changed(self, new_color):
        """
        Internal callback function triggered when the color changes from the color browser
        :param new_color: QColor
        """

        if isinstance(new_color, QColor):
            new_color = qt_color.Color(new_color).to_string()

        self.set_value(new_color)
        self._on_emit_value_changed()


class IconPickerFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(IconPickerFieldWidget, self).__init__(*args, **kwargs)

        self._value = 'rgb(100, 100, 100)'

        widget = icon.IconPicker()
        widget.setObjectName('widget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        widget.iconChanged.connect(self._on_icon_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def set_data(self, data):
        """
        Overrides FieldWidget data function
        :param data: dict
        """

        colors = data.get('colors')
        if colors:
            self.widget().set_colors(colors)

        super(IconPickerFieldWidget, self).set_data(data)

    def value(self):
        """
        Overrides FieldWidget value function
        Returns the value of the color picker
        :return: Color
        """

        return self.widget().current_icon()

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the color picker
        :param value: str
        """

        self.widget().set_current_icon(value)

    def set_items(self, items):
        """
        Sets the items for the field widget
        :param items: list(str)
        """

        self.widget().set_icons(items)
        self.widget().menu_button().setVisible(False)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_icon_changed(self, icon):
        """
        Internal callback function that is triggered when the color changes from the color browser
        :param icon: QIcon
        """

        self.set_value(icon)
        self._on_emit_value_changed()


class GroupFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(GroupFieldWidget, self).__init__(*args, **kwargs)

        widget = group.GroupBoxWidget(self.data().get('title'), None)
        widget.set_checked(True)
        widget.toggled.connect(self.set_value)

        self.set_widget(widget)

        self.label().hide()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def default_data(self):
        """
        Returns the default data for the group field
        :return: dict
        """

        return {
            'value': True,
            'persistent': True,
            'validate': False,
            'persistentKey': 'BaseItem'
        }

    def value(self):
        """
        Overrides FieldWidget value function
        Called when teh field widget is resized
        """

        return self.widget().is_checked()

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the path of the image in disk
        :param value: str
        """

        self.widget().set_checked(value)

        is_child = False
        if self.form_widget():
            for field_widget in self.form_widget().field_widgets():
                if field_widget.name() == self.name():
                    is_child = True
                    continue
                if is_child:
                    if isinstance(field_widget, GroupFieldWidget):
                        break
                    field_widget.set_collapsed(not value)
                    if value and field_widget.data().get('visible') is not None:
                        field_widget.setVisible(field_widget.data().get('visible'))
                    else:
                        field_widget.setVisible(value)


class ButtonGroupFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(ButtonGroupFieldWidget, self).__init__(*args, **kwargs)

        self._value = ''
        self._buttons = dict()

        items = self.data().get('items')

        widget = QFrame(self)
        layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        widget.setLayout(layout)

        index = 0
        for item in items:
            index += 1
            button = buttons.BaseButton(item, parent=self)
            button.setCheckable(True)
            button_callback = partial(self.set_value, item)
            button.clicked.connect(button_callback)
            self._buttons[item] = button
            if index == 1:
                button.setProperty('first', True)
            if index == len(items):
                button.setProperty('last', True)
            layout.addWidget(button)

        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Overrides FieldWidget value function
        """

        return self._value

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the path of the image in disk
        :param value: str
        """

        self._value = value

        with qt_contexts.block_signals(self):
            for button in list(self._buttons.values()):
                button.setChecked(False)
            if value in self._buttons:
                self._buttons[value].setChecked(True)

        super(ButtonGroupFieldWidget, self).set_value(value)

    def set_items(self, items):
        """
        Sets the items for the field widget
        Override to avoid not implemented error
        :param items: list(str)
        """

        pass


class TagsFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(TagsFieldWidget, self).__init__(*args, **kwargs)

        widget = combobox.BaseComboBox(parent=self)
        widget.setEditable(True)
        widget.editTextChanged.connect(self._on_emit_value_changed)
        widget.editTextChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Overrides FieldWidget value function
        Called when teh field widget is resized
        """

        try:
            current_text = self.widget().currentText()
        except AttributeError:
            current_text = self.widget().itemText(self.widget().currentIndex())

        return self._string_to_list(current_text)

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the path of the image in disk
        :param value: str
        """

        text = self._list_to_string(value)
        self.widget().setEditText(text)

    def set_items(self, items):
        """
        Sets the items for the field widget
        :param items: list(str)
        """

        self.widget().clear()
        self.widget().addItems(items or list())

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _list_to_string(self, data):
        """
        Internal function that returns a string from the given list
        ['a', 'b', c'] to 'a,b,c
        :param data: list
        :return: str
        """

        data = [str(item) for item in data]
        data = str(data).replace("[", "").replace("]", "")
        data = data.replace("'", "").replace('"', "")

        return data

    def _string_to_list(self, data):
        """
        Returns a list from the given string
        a,b,c to ['a', 'b', c']
        :param data: str
        :return: list(str)
        """

        data = '["' + str(data) + '"]'
        data = data.replace(' ', '')
        data = data.replace(',', '","')

        return eval(data)


class ObjectsFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(ObjectsFieldWidget, self).__init__(*args, **kwargs)

        self._value = list()

        widget = label.RightElidedLabel(parent=self)
        widget.setAlignment(Qt.AlignVCenter)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.set_widget(widget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def value(self):
        """
        Overrides FieldWidget value function
        """

        return self._value

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        :param value: str
        """

        if value:
            count = len(value)
            plural = 's' if count > 1 else ''
            msg = '{} object{} selected for saving'.format(count, plural)
        else:
            msg = 'Nothing selected for saving'

        self._value = value
        self.widget().setText(msg)
        super(ObjectsFieldWidget, self).set_value(value)


FIELD_WIDGET_REGISTRY = {
    'int': IntFieldWidget,
    'bool': BoolFieldWidget,
    'enum': EnumFieldWidget,
    'string': StringFieldWidget,
    'stringDouble': StringDoubleFieldWidget,
    'password': PasswordFieldWidget,
    'text': TextFieldWidget,
    'path': PathFieldWidget,
    'radio': RadioFieldWidget,
    'separator': SeparatorFieldWidget,
    'label': LabelFieldWidget,
    'image': ImageFieldWidget,
    'slider': SliderFieldWidget,
    'range': RangeFieldWidget,
    'color': ColorFieldWidget,
    'iconPicker': IconPickerFieldWidget,
    'group': GroupFieldWidget,
    'buttonGroup': ButtonGroupFieldWidget,
    'tags': TagsFieldWidget,
    'objects': ObjectsFieldWidget,
}
