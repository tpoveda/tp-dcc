#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains mixin decorators for Qt
"""

from functools import partial

from Qt.QtCore import Qt, QPoint, QEvent, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import QApplication, QGraphicsDropShadowEffect, QGraphicsOpacityEffect

from tp.common.qt import qtutils


def dynamic_property(cls):
    """
    Mixin decorator that runs a function after an object dynamic property value changed.
    The decorator will for functions of the following format _set_{property_name} and will use that function
    to update the Qt property dynamically.

    :param cls:
    :return: cls
    """

    def _new_event(self, event):
        if event.type() == QEvent.DynamicPropertyChange:
            property_name = event.propertyName()
            if hasattr(self, '_set_{}'.format(property_name)):
                callback = getattr(self, '_set_{}'.format(property_name))
                callback(self.property(str(property_name)))
        return super(cls, self).event(event)

    setattr(cls, 'event', _new_event)

    return cls


def cursor_mixin(cls):
    """
    Mixin decorator that changes cursor to Qt.PointingHandCursor when mouse is over an enabled widget and to
    Qt.ForbiddenCursor when mouse is over a disabled widget.
    """

    old_enter_event = cls.enterEvent
    old_leave_event = cls.leaveEvent
    old_hide_event = cls.hideEvent

    def _new_enter_event(self, *args, **kwargs):
        old_enter_event(self, *args, **kwargs)
        self.__dict__.update({'__tpdcc_enter': True})
        QApplication.setOverrideCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ForbiddenCursor)
        return super(cls, self).enterEvent(*args, **kwargs)

    def _new_leave_event(self, *args, **kwargs):
        old_leave_event(self, *args, **kwargs)
        if self.__dict__.get('__tpdcc_enter', False):
            QApplication.restoreOverrideCursor()
            self.__dict__.update({'__tpdcc_enter': False})
        return super(cls, self).leaveEvent(*args, **kwargs)

    def _new_hide_event(self, *args, **kwargs):
        old_hide_event(self, *args, **kwargs)
        if self.__dict__.get('__tpdcc_enter', False):
            QApplication.restoreOverrideCursor()
            self.__dict__.update({'__tpdcc_enter': False})
        return super(cls, self).hideEvent(*args, **kwargs)

    setattr(cls, 'enterEvent', _new_enter_event)
    setattr(cls, 'leaveEvent', _new_leave_event)
    setattr(cls, 'hideEvent', _new_hide_event)

    return cls


def focus_shadow_mixin(cls):
    """
    Adds a shadow effect for decorated class when widget is focused.
    If the widget is focused, shadow effect is enabled; otherwise shadow effect is disabled.
    """

    old_focus_in_event = cls.focusInEvent
    old_focus_out_event = cls.focusOutEvent

    def _new_focus_in_event(self, *args, **kwargs):
        old_focus_in_event(self, *args, **kwargs)
        if not self.graphicsEffect():
            shadow_effect = QGraphicsDropShadowEffect(self)
            object_type = self.property('type')
            theme = getattr(cls, 'theme') if hasattr(cls, 'theme') else None
            if theme:
                color = vars(theme).get('{}_color'.format(object_type or 'primary'))
            else:
                color = Qt.red
            shadow_effect.setColor(color)
            shadow_effect.setOffset(0, 0)
            shadow_effect.setBlurRadius(5)
            shadow_effect.setEnabled(False)
            self.setGraphicsEffect(shadow_effect)
        if self.isEnabled():
            self.graphicsEffect().setEnabled(True)

    def _new_focus_out_event(self, *args, **kwargs):
        old_focus_out_event(self, *args, **kwargs)
        if self.graphicsEffect():
            self.graphicsEffect().setEnabled(False)

    setattr(cls, 'focusInEvent', _new_focus_in_event)
    setattr(cls, 'focusOutEvent', _new_focus_out_event)

    return cls


def hover_shadow_mixin(cls):
    """
    Adds a shadow effect for decorated class when widget is hovered.
    If the widget is hovered, shadow effect is enabled; otherwise shadow effect is disabled.
    :param cls:
    :return: cls
    """

    old_enter_event = cls.enterEvent
    old_leave_event = cls.leaveEvent

    def _new_enter_event(self, *args, **kwargs):
        old_enter_event(self, *args, **kwargs)
        if not self.graphicsEffect():
            shadow_effect = QGraphicsDropShadowEffect(self)
            object_type = self.property('type')
            theme = getattr(cls, 'theme') if hasattr(cls, 'theme') else None
            if theme:
                color = vars(theme).get('{}_color'.format(object_type or 'primary'))
            else:
                color = Qt.red
            shadow_effect.setColor(color)
            shadow_effect.setOffset(0, 0)
            shadow_effect.setBlurRadius(5)
            shadow_effect.setEnabled(False)
            self.setGraphicsEffect(shadow_effect)
        if self.isEnabled():
            self.graphicsEffect().setEnabled(True)

    def _new_leave_event(self, *args, **kwargs):
        old_leave_event(self, *args, **kwargs)
        if self.graphicsEffect():
            self.graphicsEffect().setEnabled(False)

    setattr(cls, 'enterEvent', _new_enter_event)
    setattr(cls, 'leaveEvent', _new_leave_event)

    return cls


def stacked_opacity_animation_mixin(cls):
    """
    Decorators for stacked widget
    When stacked widget index changes, show opacity and position animation for current widget
    :param cls:
    :return:
    """

    if not qtutils.is_stackable(cls):
        return cls

    old_init = cls.__init__

    def _new_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        self._prev_index = 0
        self._to_show_pos_anim = QPropertyAnimation()
        self._to_show_pos_anim.setDuration(400)
        self._to_show_pos_anim.setPropertyName(b'pos')
        self._to_show_pos_anim.setEndValue(QPoint(0, 0))
        self._to_show_pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._to_hide_pos_anim = QPropertyAnimation()
        self._to_hide_pos_anim.setDuration(400)
        self._to_hide_pos_anim.setPropertyName(b'pos')
        self._to_hide_pos_anim.setEndValue(QPoint(0, 0))
        self._to_hide_pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._opacity_effect = QGraphicsOpacityEffect()
        self._opacity_anim = QPropertyAnimation()
        self._opacity_anim.setDuration(400)
        self._opacity_anim.setEasingCurve(QEasingCurve.InCubic)
        self._opacity_anim.setPropertyName(b'opacity')
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setTargetObject(self._opacity_effect)
        self._opacity_anim.finished.connect(self._on_disable_opacity)
        self.currentChanged.connect(self._on_play_anim)

    def _on_play_anim(self, index):
        current_widget = self.widget(index)
        if self._prev_index < index:
            self._to_show_pos_anim.setStartValue(QPoint(self.width(), 0))
            self._to_show_pos_anim.setTargetObject(current_widget)
            self._to_show_pos_anim.start()
        else:
            self._to_hide_pos_anim.setStartValue(QPoint(-self.width(), 0))
            self._to_hide_pos_anim.setTargetObject(current_widget)
            self._to_hide_pos_anim.start()
        current_widget.setGraphicsEffect(self._opacity_effect)
        current_widget.graphicsEffect().setEnabled(True)
        self._opacity_anim.start()
        self._prev_index = index

    def _on_disable_opacity(self):
        self.currentWidget().graphicsEffect().setEnabled(False)

    setattr(cls, '__init__', _new_init)
    setattr(cls, '_on_play_anim', _on_play_anim)
    setattr(cls, '_on_disable_opacity', _on_disable_opacity)

    return cls


class FieldMixin(object):
    """
    Class that allows to implement a register/bind system to simply the usage of of Qt signals and the update
    of Qt UIs in respnse to signals emitions.
    """

    computed_dict = None
    properties_dict = None

    def register_field(self, name, getter=None, setter=None, required=False):
        """
        Registers a field with default values.

        :param str name: name of the field to register.
        :param callable or object getter:  bind getter function or default value of the field. If callable is given,
            the default value is retrieved from the getter function.
        :param callable setter:  bind setter function that is called when the binded propery is updated.
        :param bool required:
        :return:
        """

        if self.computed_dict is None:
            self.computed_dict = dict()
        if self.properties_dict is None:
            self.properties_dict = dict()
        if callable(getter):
            value = getter()
            self.computed_dict[name] = {
                'value': value,
                'getter': getter,
                'setter': setter,
                'required': required,
                'bind': list()
            }
        else:
            self.properties_dict[name] = {
                'value': getter,
                'required': required,
                'bind': list()
            }

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def bind(self, field_name, widget, qt_property, index=None, signal=None, callback=None):
        """
        Bind the given field to given widget Qt property.

        :param str field_name: name of the field to bind.
        :param QWidget widget: widget we want to bind to the field.
        :param Property qt_property: QWidget property to bind to the field.
        :param index:
        :param Signal signal:
        :param callback:
        :return:

        ..note:: Before binding a field, you must register it calling register_field function.
        """

        data_dict = {
            'data_name': field_name,
            'widget': widget,
            'widget_property': qt_property,
            'index': index,
            'callback': callback
        }
        if field_name in self.computed_dict:
            self.computed_dict[field_name]['bind'].append(data_dict)
        else:
            self.properties_dict[field_name]['bind'].append(data_dict)
        if signal:
            getattr(widget, signal).connect(partial(self._slot_changed_from_user, data_dict))

        self._data_update_ui(data_dict)

        return widget

    def fields(self):
        """
        Returns all the registered fields.

        :return: list of registered fields.
        :rtype: list(str)
        """
        return list(self.properties_dict.keys()) + list(self.computed_dict.keys())

    def field(self, name):
        """
        Returns the value of the current registered field.

        :param str name: name of the field we want to get value of.
        :return: field value. If field is not registrered, None value if returned.
        :rtype: object or None
        """

        if name in self.properties_dict:
            return self.properties_dict[name]['value']
        elif name in self.computed_dict:
            new_value = self.computed_dict[name]['getter']()
            self.computed_dict[name]['value'] = new_value
            return new_value
        else:
            logger.error('No field with name "{}" found!'.format(name))
            return None

    def set_field(self, name, value):
        """
        Sets the value of the given registrerd field name updating the UI.

        :param str name: name of the field we want to set value of.l
        :param object value: new value of the field.
        """

        if name in self.properties_dict:
            self.properties_dict[name]['value'] = value
            self._slot_property_changed(name)
        elif name in self.computed_dict:
            self.computed_dict[name]['value'] = value

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _data_update_ui(self, data_dict):
        """
        Internal function thta updates binded wiget based on property data.

        :param dict data_dict: binded field data.
        """

        # retrieve binded data
        data_name = data_dict.get('data_name')
        widget = data_dict['widget']
        index = data_dict['index']
        widget_property = data_dict['widget_property']
        callback = data_dict['callback']

        value = None
        if index is None:
            value = self.field(data_name)
        elif isinstance(self.field(data_name), dict):
            value = self.field(data_name).get(index)
        elif isinstance(self.field(data_name), list):
            value = self.field(data_name)[index] if index < len(self.field(data_name)) else None
        if widget.metaObject().indexOfProperty(widget_property) > -1 or widget_property in list(
                map(str, [dynamic_property.data().decode() for dynamic_property in widget.dynamicPropertyNames()])):
            widget.setProperty(widget_property, value)
        else:
            widget.set_field(widget_property, value)
        if callable(callback):
            callback()

    def _slot_property_changed(self, property_name):
        """
        Internal function that checks registered fields and force the update of the UI if given property name
        is binded.

        :param str property_name: name of the changed property.
        """

        for key, setting_dict in self.properties_dict.items():
            if key == property_name:
                for data_dict in setting_dict['bind']:
                    self._data_update_ui(data_dict)

        for key, setting_dict in self.computed_dict.items():
            for data_dict in setting_dict['bind']:
                self._data_update_ui(data_dict)

    def _slot_changed_from_user(self, data_dict, ui_value):
        """
        Internal function that is called when a binded field with a default signals is setted.

        :param dict data_dict:  binded field data.
        :param object ui_value: new widget property value.
        """

        self._ui_update_data(data_dict, ui_value)

    def _ui_update_data(self, data_dict, ui_value):
        """
        Internal function that updates data for the given widget based on given field data.

        :param dict data_dict:  binded field data.
        :param object ui_value: new widget property value.
        """

        data_name = data_dict.get('data_name')
        index = data_dict.get('index', None)
        if index is None:
            self.set_field(data_name, ui_value)
        else:
            old_value = self.field(data_name)
            old_value[index] = ui_value
            self.set_field(data_name, old_value)
        if data_name in self.properties_dict.items():
            self._slot_property_changed(data_name)
