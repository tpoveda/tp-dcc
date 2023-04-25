#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes that extend QToolBar functionality
"""

from Qt.QtCore import Qt, Property, QSize
from Qt.QtWidgets import QWidget, QToolBar, QAction, QFrame

from tpDcc.dcc import dialog
from tpDcc.managers import resources
from tpDcc.libs.python import python
from tpDcc.libs.resources.core import icon
from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import layouts, buttons


class ToolBar(QToolBar, object):
    """
    Class that adds functionality to expand/collapse QToolBars
    """

    DEFAULT_EXPANDED_HEIGHT = 32
    DEFAULT_COLLAPSED_HEIGHT = 10
    ICON_SIZE = 32

    def __init__(self, *args, **kwargs):
        super(ToolBar, self).__init__(*args, **kwargs)

        self._dpi = 1
        self._is_expanded = True
        self._expanded_height = self.DEFAULT_EXPANDED_HEIGHT
        self._collapsed_height = self.DEFAULT_COLLAPSED_HEIGHT

        self.setMinimumHeight(self.DEFAULT_EXPANDED_HEIGHT)

    def _get_expanded(self):
        return self._is_expanded

    def _set_expanded(self, flag):
        self._is_expanded = flag

    expanded = Property(bool, _get_expanded, _set_expanded)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def mousePressEvent(self, event):
        if not self.is_expanded():
            self.expand()

    def setFixedHeight(self, value):
        """
        Overrides base QToolBar setFixedHeight
        Allows to also set the height for all child widgets of the menu bar
        :param value: float
        """

        self.set_children_height(value)
        super(ToolBar, self).setFixedHeight(value)
        print(self.height())

    def insertAction(self, before, action):
        """
        Overrides base QToolBar insertAction function
        Support the before argument as string
        :param before: QAction or str
        :param action: QAction
        :return: QAction
        """

        action.setParent(self)
        if python.is_string(before):
            before = self.find_action(before)

        action = super(ToolBar, self).insertAction(before, action)

        return action

    def actions(self):
        """
        Overrides base QToolBar actions function
        Returns all the widgets that are a child of the menu bar widget
        :return: list(QWidget)
        """

        actions = list()

        for child in self.children():
            if isinstance(child, QAction):
                actions.append(child)

        return actions

    # =================================================================================================================
    # DPI
    # =================================================================================================================

    def dpi(self):
        """
        Returns the zoom multiplier
        :return: float
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Set the zoom multiplier
        :param : float
        """

        self._dpi = dpi
        if self.is_expanded():
            self.expand()
        else:
            self.collapse()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def widgets(self):
        """
        Returns all the widgets that are a child of the menu bar widget
        :return: list(QWidget)
        """

        widgets = list()
        for i in range(self.layout().count()):
            w = self.layout().itemAt(i).widget()
            if isinstance(w, QWidget):
                widgets.append(w)

        return widgets

    def is_expanded(self):
        """
        Returns whether the menu bar is expanded or not
        :return: bool
        """

        return self._is_expanded

    def expand_height(self):
        """
        Returns the height of menu bar when is expanded
        :return: float
        """

        return int(self._expanded_height * self.dpi())

    def collapse_height(self):
        """
        Returns the height of widget when collapsed
        :return: int
        """

        return int(self._collapsed_height * self.dpi())

    def set_children_hidden(self, flag):
        """
        Hide/Show all child widgets
        :param flag: bool
        """

        for action in self.actions():
            action.setVisible(not flag)

        # for w in self.widgets():
        #     w.setHidden(flag)

    def set_children_height(self, height):
        """
        Set the height of all the child widgets to the given height
        :param height: int
        """

        for w in self.widgets():
            w.setFixedHeight(height)

    def expand(self):
        """
        Expand the menu bar to the expand height
        """

        self._is_expanded = True
        height = self.expand_height()
        self.setFixedHeight(height)
        self.set_children_hidden(False)
        icon_size = self.ICON_SIZE * self.dpi()
        self.setIconSize(QSize(icon_size, icon_size))
        self.setStyleSheet(self.styleSheet())

    def collapse(self):
        """
        Collapse the menu bar to the collapse height
        """

        self._is_expanded = False
        height = self.collapse_height()
        self.setFixedHeight(height)
        self.set_children_height(0)
        self.set_children_hidden(True)
        self.setIconSize(QSize(0, 0))
        self.setStyleSheet(self.styleSheet())

    def set_icon_color(self, color):
        """
        Set the icon colors to the current foregroundRole
        :param color: QColor
        """

        for action in self.actions():
            action_icon = action.icon()
            action_icon = icon.Icon(action_icon)
            action_icon.set_color(color)
            action.setIcon(action_icon)

    def find_action(self, text):
        """
        Find the action with the given text
        :param text: str
        :return: QAction or None
        """

        for child in self.children():
            if isinstance(child, QAction):
                if child.text() == text:
                    return child

    def find_tool_button(self, text):
        """
        Find the QToolButton with the given text
        :param text: str
        :return: QToolButton or None
        """

        for child in self.children():
            if isinstance(child, QAction):
                if child.text() == text:
                    return self.widgetForAction(child)


class FlowToolBar(QFrame, object):
    """
    Custom toolbar whose buttons will flow from left to right and wrap to next row if there is no space
    """

    def __init__(self, menu_indicator_icon=None, icon_size=20, icon_padding=2, parent=None):
        super(FlowToolBar, self).__init__(parent)

        self._icon_size = icon_size
        self._icon_padding = icon_padding
        self._overflow_button_color = (128, 128, 128)
        self._menu_indicator_icon = menu_indicator_icon or resources.icon('arrow_menu')
        self._overflow_icon = resources.icon('sort_down')
        self._overflow_menu = False
        self._overflow_menu_button = None

        self.ui()

    @property
    def flow_layout(self):
        return self._flow_layout

    @property
    def overflow_layout(self):
        return self._overflow_layout

    def resizeEvent(self, event):
        self.update_widgets_overflow(event.size())

    def sizeHint(self):
        spacing_x = self._flow_layout.spacing_x
        next_x = 0
        for item in self._flow_layout.items_list:
            widget = item.widget()
            next_x += widget.sizeHint().width() + spacing_x

        return QSize(next_x + 3, super(FlowToolBar, self).sizeHint().height())

    def ui(self):
        main_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0), spacing=0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(main_layout)

        self._flow_layout = layouts.FlowLayout(margin=0, spacing_x=1, spacing_y=1)
        main_layout.addLayout(self._flow_layout)

        self._overflow_menu_button = self._setup_overflow_menu_button()
        self._overflow_menu = FlowToolbarMenu(parent=self)
        self._overflow_layout = self._overflow_menu.layout()

    def get_icon_size(self):
        """
        Returns the icon size
        :return: QSize
        """

        return QSize(self._icon_size + self._icon_padding, self._icon_size + self._icon_padding)

    def set_icon_size(self, size):
        """
        Sets the size of the icons of the toolbar
        :param size: QSize
        """

        self._icon_size = size

        for i in range(0, self._flow_layout.count()):
            widget = self._flow_layout.itemAt(i).widget()
            widget.setIconSize(self.get_icon_size())

        self._overflow_menu_button = self._setup_overflow_menu_button(btn=self._overflow_menu_button)

    def set_icon_padding(self, padding):
        """
        Sets the padding for the icons of the toolbar
        :param padding: int
        """

        self._icon_padding = qtutils.dpi_scale(padding)

    def set_overflow_button_color(self, button_color):
        """
        Sets the color used for the overflow button
        :param button_color:
        """

        self._overflow_button_color = button_color

    def set_height(self, height):
        """
        Sets fixed height for the toolbar
        :param height: int
        """

        self.setFixedHeight(height)

    def set_spacing_x(self, value):
        """
        Sets spacing of items in layout in X
        :param value: float
        """

        self._flow_layout.set_spacing_x(value)

    def set_spacing_y(self, value):
        """
        Sets spacing of items in layout in Y
        :param value: float
        """

        self._flow_layout.set_spacing_y(value)

    def items_list(self):
        """
        Returns list of item in toolbar without the overflow menu button
        :return: list
        """

        return self._flow_layout.items_list[:-1]

    def items(self):
        """
        Returns all items in the toolbar
        :return: list
        """

        return self._flow_layout.items()

    def update_widgets_overflow(self, size=None):
        """
        Function that hides or show widgets based on the size of the flow toolbar
        If it is too small, it will move widgets to overflow menu and if there are widget in the overflow menu,
        placce it back into the flow toolbar if there is space
        :param size: QSize, new size
        """

        if not self._overflow_menu_button or not self._overflow_menu:
            return

        spacing_x = self._flow_layout.spacing_x
        spacing_y = self._flow_layout.spacing_y

        if not size:
            size = self.size()
        if len(self.items_list()) == 0:
            return

        overflow_button_width = self._overflow_menu_button.sizeHint().width()
        width = size.width() - overflow_button_width - spacing_x
        height = size.height()
        hidden = list()

        self.setUpdatesEnabled(False)

        next_x = 0
        next_y = self.items_list()[0].widget().height()

        for item in self.items_list():
            item_widget = item.widget()
            widget_width = item_widget.sizeHint().width() + spacing_x
            next_x += widget_width
            if next_x > width:
                next_y += item_widget.height() + (spacing_y * 2)
                next_x = 0
            if next_y > height:
                item_widget.hide()
                hidden.append(item_widget)
            else:
                item_widget.show()

        menu = self._overflow_menu_button.menu(mouse_menu=Qt.LeftButton)
        for a in menu.actions():
            a.setVisible(False)

        for hidden_widget in hidden:
            for a in menu.actions():
                if a.text() == hidden_widget.property('name'):
                    a.setVisible(True)
                    break

        self._overflow_menu_button.setVisible(len(hidden) > 0)
        self.setUpdatesEnabled(True)

        return hidden

    def clear(self):
        """
        Clears all toolbar widgets
        """

        self._overflow_menu_button.clear_menu(Qt.LeftButton)
        self._flow_layout.removeWidget(self._overflow_menu_button)
        self._flow_layout.clear()
        qtutils.clear_layout(self._overflow_layout)

    def overflow_menu_active(self, flag):
        self._overflow_menu = flag
        self._overflow_menu_button.setVisible(flag)

    def _setup_overflow_menu_button(self, btn=None):
        """
        Internal function that setup overflow menu and connects it to given button.
        If button is not given, it will be created
        :param btn:
        :return:
        """

        overflow_color = self._overflow_button_color
        overflow_icon = self._overflow_icon
        if not btn:
            btn = buttons.IconMenuButton(parent=self)
        btn.set_icon(overflow_icon, colors=overflow_color, size=self._icon_size, color_offset=40)
        btn.double_click_enabled = False
        btn.setProperty('name', 'overflow')
        btn.setIconSize(self.get_icon_size())
        btn.setVisible(False)

        return btn


class FlowToolbarMenu(dialog.Dialog, object):
    def __init__(self, parent=None):
        super(FlowToolbarMenu, self).__init__(parent=parent, show_on_initialize=False)

    def ui(self):
        super(FlowToolbarMenu, self).ui()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

    def sizeHint(self):
        return self.minimumSize()

    def show(self, *args, **kwargs):
        super(FlowToolbarMenu, self).show(*args, **kwargs)
        self.resize(self.sizeHint())

    def layout(self):
        return self.main_layout
