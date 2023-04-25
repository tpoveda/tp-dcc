#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains form widgets for library
"""

import logging
from functools import partial

from Qt.QtCore import Signal
from Qt.QtWidgets import QSizePolicy, QFrame, QSpacerItem

from tpDcc.libs.qt.core import contexts as qt_contexts
from tpDcc.libs.qt.widgets import layouts, label, buttons, formfields

from tpDcc.tools.datalibrary.core import settings

LOGGER = logging.getLogger('tpDcc-libs-qt')


class FormDialog(QFrame, object):

    accepted = Signal(object)
    rejected = Signal(object)

    def __init__(self, parent=None, form=None):
        super(FormDialog, self).__init__(parent)

        self._settings = None

        self.main_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(self.main_layout)

        self._widgets = list()
        self._validator = None

        self._title = label.BaseLabel(parent=self)
        self._title.setObjectName('title')
        self._title.setText('FORM')
        self._description = label.BaseLabel(parent=self)
        self._description.setObjectName('description')
        self._form_widget = FormWidget(self)
        self._form_widget.setObjectName('formWidget')
        self._form_widget.validated.connect(self._on_validated)
        btn_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._accept_btn = buttons.BaseButton(parent=self)
        self._accept_btn.setObjectName('acceptButton')
        self._accept_btn.setText('Accept')
        self._accept_btn.clicked.connect(self.accept)
        self._reject_btn = buttons.BaseButton(parent=self)
        self._reject_btn.setObjectName('rejectButton')
        self._reject_btn.setText('Cancel')
        self._reject_btn.clicked.connect(self.reject)
        btn_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        btn_layout.addWidget(self._accept_btn)
        btn_layout.addWidget(self._reject_btn)

        self.main_layout.addWidget(self._title)
        self.main_layout.addWidget(self._description)
        self.main_layout.addWidget(self._form_widget)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(btn_layout)

        if form:
            self.set_settings(form)

    def accept_button(self):
        """
        Returns the accept button
        :return: QPushButton
        """

        return self._accept_btn

    def reject_button(self):
        """
        Returns the reject button
        :return: QPushButton
        """

        return self._reject_btn

    def set_settings(self, settings):
        """
        Sets dialog form settings
        :param settings: dict
        """

        self._settings = settings
        title = settings.get("title")
        if title is not None:
            self._title.setText(title)
        callback = settings.get("accepted")
        if not callback:
            self._settings["accepted"] = self._validate_accepted
        callback = settings.get("rejected")
        if not callback:
            self._settings["rejected"] = self._validate_rejected
        description = settings.get("description")
        if description is not None:
            self._description.setText(description)
        validator = settings.get("validator")
        if validator is not None:
            self._form_widget.set_validator(validator)
        layout = settings.get("layout")
        schema = settings.get("schema")
        if schema is not None:
            self._form_widget.set_schema(schema, layout=layout)

    def accept(self):
        """
        Function called when the dialog is accepted
        """

        callback = self._settings.get('accepted')
        if callback:
            callback(**self._form_widget.values())
        self.close()

    def reject(self):
        """
        Function called when the dialog is rejected
        """

        callback = self._settings.get('rejected')
        if callback:
            callback(**self._form_widget.default_values())
        self.close()

    def _validate_accepted(self, **kwargs):
        """
        Internal function called when the accept button has been clicked
        :param kwargs: dict, default values of the form fields
        """

        self._form_widget.validator()(**kwargs)

    def _validate_rejected(self, **kwargs):
        """
        Internal function called when reject button has been clicked
        :param kwargs: dict, default values of the form fields
        """

        self._form_widget.validator()(**kwargs)

    def _on_validated(self):
        """
        Internal callback function that is triggered when the has been validated
        """

        self._accept_btn.setEnabled(not self._form_widget.has_errors())


class FormWidget(QFrame, object):

    accepted = Signal(object)
    stateChanged = Signal()
    validated = Signal()

    def __init__(self, *args, **kwargs):
        super(FormWidget, self).__init__(*args, **kwargs)

        self._schema = dict()
        self._widgets = list()
        self._validator = None

        main_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        self._fields_frame = QFrame(self)
        self._fields_frame.setObjectName('fieldsFrame')
        options_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._fields_frame.setLayout(options_layout)

        self._title_widget = buttons.BaseButton(parent=self)
        self._title_widget.setCheckable(True)
        self._title_widget.setObjectName('titleWidget')
        self._title_widget.toggled.connect(self._on_title_clicked)
        self._title_widget.hide()

        main_layout.addWidget(self._title_widget)
        main_layout.addWidget(self._fields_frame)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def closeEvent(self, event):
        self.save_persistent_values()
        super(FormWidget, self).closeEvent(event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def title_widget(self):
        """
        Returns the title widget
        :return: QWidget
        """

        return self._title_widget

    def set_title(self, title):
        """
        Sets the title text
        :param title: str
        """

        self.title_widget().setText(title)

    def is_expanded(self):
        """
        Returns whether the item is expanded or not
        :return: bool
        """

        return self._title_widget.isChecked()

    def set_expanded(self, flag):
        """
        Expands the options if True, otherwise collapses the options
        :param flag: bool
        """

        with qt_contexts.block_signals(self._title_widget):
            self._title_widget.setChecked(flag)
            self._fields_frame.setVisible(flag)

    def set_title_visible(self, flag):
        """
        Sets whether the title widget is visible or not
        :param flag: bool
        """

        self.title_widget().setVisible(flag)

    def widget(self, name):
        """
        Returns the widget for the given widget name
        :param name: str
        :return: FieldWidget
        """

        for widget in self._widgets:
            if widget.data().get('name') == name:
                return widget

    def value(self, name):
        """
        Returns the value for the given widget name
        :param name: str
        :return: object
        """

        widget = self.widget(name)
        if not widget:
            return None

        return widget.value()

    def set_value(self, name, value):
        """
        Sets the value for the given field name
        :param name: str
        :param value: variant
        """

        widget = self.widget(name)
        widget.set_value(value)

    def values(self):
        """
        Returns all the field values indexed by the field name
        :return: dict
        """

        values = dict()
        for widget in self._widgets:
            name = widget.data().get('name')
            if name:
                values[name] = widget.value()

        return values

    def set_values(self, values):
        """
        Sets the field values for the current form
        :param values: dict
        """

        state = list()
        for name in values:
            state.append({'name': name, 'value': values[name]})

        self._set_state(state)

    def default_values(self):
        """
        Returns all teh default field values indexed by the field name
        :return: dict
        """

        values = dict()
        for widget in self._widgets:
            name = widget.data().get('name')
            if name:
                values[name] = widget.default()

        return values

    def set_data(self, name, data):
        """
        Sets the data for the given field name
        :param name: str
        :param data: dict
        """

        widget = self.widget(name)
        if not widget:
            return
        widget.set_data(data)

    def fields(self):
        """
        Returns fields data for the form
        :return: list(dict)
        """

        options = list()
        for widget in self._widgets:
            options.append(widget.data())

        return options

    def field_widgets(self):
        """
        Returns all field widgets
        :return: list(FieleWidget)
        """

        return self._widgets

    def state(self):
        """
        Returns the current state
        :return: dict
        """

        fields = list()
        for widget in self._widgets:
            fields.append(widget.state())

        state = {
            'fields': fields,
            'expanded': self.is_expanded()
        }

        return state

    def set_state(self, state):
        """
        Sets the current state
        :param state: dict
        """

        expanded = state.get('expanded')
        if expanded is not None:
            self.set_expanded(expanded)

        fields = state.get('fields')
        if fields is not None:
            self._set_state(fields)

        self.validate()

    def schema(self):
        """
        Returns form's schema
        :return: dict
        """

        return self._schema

    def set_schema(self, schema, layout=None, errors_visible=False):
        """
        Sets the schema for the widget
        :param schema: list(dict)
        :param layout: str
        :param errors_visible: str
        """

        self._schema = self._sort_schema(schema)
        if not self._schema:
            return

        for field in schema:
            cls = formfields.FIELD_WIDGET_REGISTRY.get(field.get('type', 'label'))
            if not cls:
                LOGGER.warning('Cannot find widget for {}'.format(field))
                continue
            if layout and not field.get('layout'):
                field['layout'] = layout

            enabled = field.get('enabled', True)
            read_only = field.get('readOnly', False)

            error_visible = field.get('errorVisible')
            field['errorVisible'] = error_visible if error_visible is not None else errors_visible

            widget = cls(data=field, parent=self._fields_frame, form_widget=self)
            data = widget.default_data()
            data.update(field)

            widget.set_data(data)

            value = field.get('value')
            default = field.get('default')
            if value is None and default is not None:
                widget.set_value(default)

            if not enabled or read_only:
                widget.setEnabled(False)

            self._widgets.append(widget)

            callback = partial(self._on_field_changed, widget)
            widget.valueChanged.connect(callback)

            self._fields_frame.layout().addWidget(widget)

        self.load_persistent_values()

    def validator(self):
        """
        Returns the validator for the form
        :return: fn
        """

        return self._validator

    def set_validator(self, validator):
        """
        Sets the validator for the options
        :param validator: fn
        """

        self._validator = validator

    def reset(self):
        """
        Reset all option widget back to the ir default values
        """

        for widget in self._widgets:
            widget.reset()
        self.validate()

    def validate(self, widget=None):
        """
        Validates the current options using the validator
        """

        if not self._validator:
            return

        values = dict()
        for name, value in self.values().items():
            data = self.widget(name).data()
            if data.get('validate', True):
                values[name] = value

        if widget:
            values['fieldChanged'] = widget.name()

        fields = self._validator(**values)
        if fields is not None:
            self._set_state(fields)

        self.validated.emit()

    def errors(self):
        """
        Returns all form errors
        :return: list(str)
        """

        errors = list()
        for widget in self._widgets:
            error = widget.data().get('error')
            if error:
                errors.append(error)

        return errors

    def has_errors(self):
        """
        Returns whether the form contains any error
        :return: bool
        """

        return bool(self.errors())

    def save_persistent_values(self):
        """
        Saves form widget values
        Triggered when the user changes field values
        """

        data = dict()

        for widget in self._widgets:
            name = widget.data().get('name')
            if name and widget.data().get('persistent'):
                key = self.objectName() or 'FormWidget'
                key = widget.data().get('persistentKey', key)
                data.setdefault(key, dict())
                data[key][name] = widget.value()

        for key in data:
            settings.set(key, data[key])

    def load_persistent_values(self):
        """
        Returns the options from the user settings
        :return: dict
        """

        values = dict()
        default_values = self.default_values()

        for field in self.schema():
            name = field.get('name')
            persistent = field.get('persistent')
            if persistent:
                key = self.objectName() or 'FormWidget'
                key = field.get('persistentKey', key)
                value = settings.get(key, dict()).get(name)
            else:
                value = default_values.get(name)

            if value is not None:
                values[name] = value

        self.set_values(values)

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _sort_schema(self, schema):
        """
        Internal function that sorts the schema depending on the group order
        :param schema: list(dict)
        :return: list(dict)
        """

        def _key(field):
            return field['order']

        order = 0

        if not schema:
            return

        for i, field in enumerate(schema):
            if field.get('type') == 'group':
                order = field.get('order', order)
            field['order'] = order

        return sorted(schema, key=_key)

    def _set_state(self, fields):
        """
        Internal function that sets fields state
        :param fields: list(dict)
        """

        for widget in self._widgets:
            widget.blockSignals(True)

        try:
            for widget in self._widgets:
                widget.set_error('')
                for field in fields:
                    if field.get('name') == widget.data().get('name'):
                        widget.set_data(field)
        finally:
            for widget in self._widgets:
                widget.blockSignals(False)

        self.stateChanged.emit()

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_title_clicked(self, toggle):
        """
        Internal callback function that is triggered when the user clicks in the title widget
        """

        self.set_expanded(toggle)
        self.stateChanged.emit()

    def _on_field_changed(self, widget):
        """
        Internal callback function triggered when the given option widget changes its value
        :param widget: FieldWidget
        """

        self.validate(widget=widget)
