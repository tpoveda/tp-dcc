#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different group widgets
"""

from Qt.QtCore import Qt, Signal, Property
from Qt.QtWidgets import QSizePolicy, QWidget, QFrame, QBoxLayout, QGroupBox, QButtonGroup
from Qt.QtGui import QIcon

from tp.core.managers import resources
from tp.common.python import helpers, decorators
from tp.common.resources import theme
from tp.common.qt import base
from tp.common.qt.widgets import layouts, buttons


class BaseGroup(QGroupBox, object):
    def __init__(self, name='', parent=None, layout_spacing=2, layout_orientation=Qt.Vertical):

        self._layout_orientation = layout_orientation

        super(BaseGroup, self).__init__(parent)

        self.setTitle(name)

        if layout_orientation == Qt.Horizontal:
            self.main_layout = layouts.HorizontalLayout(spacing=layout_spacing, margins=(2, 2, 2, 2))
        else:
            self.main_layout = layouts.VerticalLayout(spacing=layout_spacing, margins=(2, 2, 2, 2))
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.main_layout)

        self.ui()
        self.setup_signals()

    def ui(self):
        """
        Function that sets up the ui of the widget
        Override it on new widgets
        """

        pass

    def setup_signals(self):
        """
        Function that set up signals of the group widgets
        """

        pass

    def set_title(self, new_title):
        """
        Set the title of the group
        """

        self.setTitle(new_title)

    def addWidget(self, widget):
        """
        Adds a a new widget to the group box layout
        NOTE: We do not follow the nomenclature to make the call similar to Qt
        :param widget: QWidget
        """

        if not widget:
            return

        self.main_layout.addWidget(widget)

    def addLayout(self, layout):
        """
        Adds a a new layout to the group box layout
        NOTE: We do not follow the nomenclature to make the call similar to Qt
        :param widget: QLayout
        """

        if not layout:
            return

        self.main_layout.addLayout(layout)


class CollapsableGroup(BaseGroup, object):
    def __init__(self, name='', parent=None, collapsable=True):
        self._collapsable = collapsable
        super(CollapsableGroup, self).__init__(name, parent, layout_orientation=Qt.Horizontal)

    def ui(self):
        super(CollapsableGroup, self).ui()

        self._base_widget = QWidget()
        if self._layout_orientation == Qt.Vertical:
            manager_layout = layouts.VerticalLayout(spacing=2, margins=(4, 4, 4, 4))
        else:
            manager_layout = layouts.HorizontalLayout(spacing=2, margins=(4, 4, 4, 4))
        manager_layout.setAlignment(Qt.AlignCenter)
        self._base_widget.setLayout(manager_layout)
        self.main_layout.addWidget(self._base_widget)
        self.main_layout = manager_layout

    def mousePressEvent(self, event):
        super(CollapsableGroup, self).mousePressEvent(event)

        if not event.button() == Qt.LeftButton:
            return

        if self._collapsable:
            if event.y() < 30:
                if self._base_widget.isHidden():
                    self.expand_group()
                else:
                    self.collapse_group()

    def set_collapsable(self, flag):
        """
        Sets if the group can be collapsed or not
        :param flag: bool
        """

        self._collapsable = flag

    def set_title(self, title):
        if not title.startswith('+ '):
            title = '+ ' + title
        self.setTitle(title)

    def expand_group(self):
        """
        Expands the content of the group
        """

        self.setVisible(True)
        title = self.title()
        title = title.replace('+', '-')
        self.setTitle(title)

    def collapse_group(self):
        """
        Collapse the content of the group
        """

        self._base_widget.setVisible(False)
        title = self.title()
        title = title.replace('-', '+')
        self.setTitle(title)


@theme.mixin
class GroupBoxWidget(base.BaseFrame):

    toggled = Signal(bool)

    def __init__(self, title, widget=None, persistent=False, settings=None, *args, **kwargs):

        self._title = title
        self._widget = None
        self._persistent = None
        self._settings = settings

        super(GroupBoxWidget, self).__init__(*args, **kwargs)

        if widget:
            self.set_widget(widget)
            # We force the update of the check status to make sure that the wrapped widget visibility is updated
            self.set_checked(self.is_checked())

        self.set_persistent(persistent)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def get_main_layout(self):
        return layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))

    def ui(self):
        super(GroupBoxWidget, self).ui()

        self._title_widget = buttons.BaseButton(self._title, parent=self)
        self._title_widget.setCheckable(True)

        self._on_icon = resources.icon('down_button')
        self._off_icon = resources.icon('right_button')
        self._title_widget.setIcon(self._off_icon)

        self._widget_frame = QFrame(self)
        self._widget_frame.setObjectName('contentsWidget')
        widget_frame_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._widget_frame.setLayout(widget_frame_layout)

        self.main_layout.addWidget(self._title_widget)
        self.main_layout.addWidget(self._widget_frame)

    def setup_signals(self):
        self._title_widget.toggled.connect(self._on_toggled_title)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def is_checked(self):
        """
        Returns whether or not group box is checked
        :return: bool
        """

        return self._title_widget.isChecked()

    def set_checked(self, flag):
        """
        Sets the check statue of the group box
        :param flag: bool
        """

        self._title_widget.setChecked(flag)
        self._title_widget.setIcon(self._on_icon if flag else self._off_icon)
        self._widget_frame.setVisible(flag)
        if self._widget:
            self._widget.setVisible(flag)

    def is_persistent(self):
        """
        Returns whether or not widget state is stored in settings
        :return: bool
        """

        return self._persistent

    def set_persistent(self, flag):
        """
        Sets whether or not widget state is stored in settings
        :param flag: bool
        """

        self._persistent = flag
        self.load_settings()

    def title(self):
        """
        Returns group box title
        :return: str
        """

        return self._title_widget.text()

    def set_widget(self, widget):
        """
        Sets the widget to hide when the user clicks the title
        :param widget: QWidget
        """

        self._widget = widget
        self._widget.setParent(self._widget_frame)
        self._widget_frame.layout().addWidget(self._widget)

    # ============================================================================================================
    # SETTINGS
    # ============================================================================================================

    def load_settings(self):
        """
        Loads widget state from given settings
        """

        if not self._settings or not self._persistent:
            return
        if not self.objectName():
            raise NameError('Impossible to save "{}" widget state because no objectName is defined!'.format(self))

        data = {self.objectName(): {'checked': self.is_checked()}}
        self._settings.save(data)

    def save_settings(self):
        """
        Saves current widget state into settings
        """

        if not self._settings or not self._persistent:
            return
        if not self.objectName():
            raise NameError('Impossible to load "{}" widget state because no objectName is defined!'.format(self))

        data = self._settings.read()
        data = data.get(self.objectName(), dict())
        if data and isinstance(data, dict):
            checked = data.get('checked', True)
            self.set_checked(checked)

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_toggled_title(self, flag):
        """
        Internal callback function that is called each time title group widget is toggled
        :param flag: bool
        """

        self.save_settings()
        self.set_checked(flag)
        self.toggled.emit(flag)


class BaseButtonGroup(base.BaseWidget, object):
    def __init__(self, orientation=Qt.Horizontal, parent=None):

        self._orientation = 'horizontal' if orientation == Qt.Horizontal else 'vertical'

        super(BaseButtonGroup, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QBoxLayout(
            QBoxLayout.LeftToRight if self._orientation == 'horizontal' else QBoxLayout.TopToBottom)
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(BaseButtonGroup, self).ui()

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self._button_group = QButtonGroup()

    @decorators.abstractmethod
    def create_button(self, data_dict):
        """
        Must be implemented in custom button groups
        Creates a new button for this group
        :param data_dict: dict
        :return: new button instance
        """

        raise NotImplementedError(
            'Function create_button for class "{}" is not implemented!'.format(self.__class__.__name__))

    def get_button_group(self):
        """
        Returns button group internal object
        :return: QButtonGroup
        """

        return self._button_group

    def clear(self):
        """
        Clears all buttons contained in this group
        """

        for btn in self._button_group.buttons():
            self._button_group.removeButton(btn)
            self.main_layout.removeWidget(btn)
            btn.setVisible(False)
            btn.deleteLater()

    def add_button(self, data_dict, index=None):
        """
        Adds a new button to this group
        :param data_dict: dict
        :param index: int or None
        :return: new added button
        """

        if helpers.is_string(data_dict):
            data_dict = {'text': data_dict}
        elif isinstance(data_dict, QIcon):
            data_dict = {'icon': data_dict}

        new_btn = self.create_button(data_dict)
        new_btn.setProperty('combine', self._orientation)

        if data_dict.get('text'):
            new_btn.setProperty('text', data_dict.get('text'))
        if data_dict.get('icon'):
            new_btn.setProperty('icon', data_dict.get('icon'))
        if data_dict.get('data'):
            new_btn.setProperty('data', data_dict.get('data'))
        if data_dict.get('checked'):
            new_btn.setProperty('checked', data_dict.get('checked'))
        if data_dict.get('shortcut'):
            new_btn.setProperty('shortcut', data_dict.get('shortcut'))
        if data_dict.get('tooltip'):
            new_btn.setProperty('toolTip', data_dict.get('tooltip'))
        if data_dict.get('clicked'):
            new_btn.clicked.connect(data_dict.get('clicked'))
        if data_dict.get('toggled'):
            new_btn.toggled.connect(data_dict.get('toggled'))

        if index is None:
            self._button_group.addButton(new_btn)
        else:
            self._button_group.addButton(new_btn, index)

        if self.main_layout.count() == 0:
            new_btn.setChecked(True)

        self.main_layout.insertWidget(self.main_layout.count(), new_btn)

        return new_btn

    def set_button_list(self, button_list):
        """
        Empties group and add all buttons given in the list of buttons
        :param button_list: list(dict)
        """

        self.clear()

        for index, data_dict in enumerate(button_list):
            new_btn = self.add_button(data_dict=data_dict, index=index)
            if index == 0:
                new_btn.setProperty('position', 'left')
            elif index == len(button_list) - 1:
                new_btn.setProperty('position', 'right')
            else:
                new_btn.setProperty('position', 'center')


class PushButtonGroup(BaseButtonGroup, object):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(PushButtonGroup, self).__init__(orientation=orientation, parent=parent)

        self._type = buttons.BaseButton.Types.PRIMARY
        self._size = theme.Theme.DEFAULT_SIZE
        self._button_group.setExclusive(True)
        self.set_spacing(1)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def create_button(self, data_dict):
        """
        Implements BaseButtonGroup create_button abstract function
        :param data_dict:
        :return:
        """

        new_btn = buttons.StyleBaseButton()
        new_btn.size = data_dict.get('size', self._size)
        new_btn.type = data_dict.get('type', self._type)

        return new_btn


class RadioButtonGroup(BaseButtonGroup, object):
    checkedChanged = Signal(int)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(RadioButtonGroup, self).__init__(orientation=orientation, parent=parent)

        self._button_group.setExclusive(True)
        self.set_spacing(15)

    def setup_signals(self):
        self._button_group.buttonClicked.connect(self.checkedChanged)

    def create_button(self, data_dict):
        """
        Implements BaseButtonGroup create_button abstract function
        :param data_dict:
        :return:
        """

        return buttons.BaseRadioButton()

    def _get_checked(self):
        return self._button_group.checkedId()

    def _sert_checked(self, value):
        btn = self._button_group.button(value)
        if btn:
            btn.setChecked(True)
            self.checkedChanged.emiet(value)

    checked = Property(int, _get_checked, _sert_checked, notify=checkedChanged)
