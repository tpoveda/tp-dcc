#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets to to drag PySide windows and dialogs
"""

from functools import partial

from Qt.QtCore import Qt, Signal, QPoint, QSize, QTimer
from Qt.QtWidgets import QApplication, QSizePolicy, QPushButton, QAbstractButton, QSpacerItem, QMenuBar
from Qt.QtGui import QIcon, QPainter, QCursor

from tp.core import dcc
from tp.core.managers import resources
from tp.preferences import manager as preferences
from tp.common.resources import icon
from tp.common.python import helpers
from tp.common.qt import consts, qtutils, base, dpi
from tp.common.qt.widgets import layouts, labels, tooltips, menus


class WindowDragger(base.BaseFrame):
    """
    Class to create custom window dragger for Solstice Tools
    """

    DEFAULT_LOGO_ICON_SIZE = 22

    doubleClicked = Signal()

    class Style(object):
        DEFAULT = 'DEFAULT'
        THIN = 'THIN'

    def __init__(self, window=None, on_close=None, height=None, show_title=True):

        self._icon_size = 13
        self._theme_preferences = preferences.get_theme_preference_interface()
        self._window = window

        super(WindowDragger, self).__init__(parent=window)

        self._dragging_enabled = True
        self._lock_window_operations = False
        self._mouse_press_pos = None
        self._mouse_move_pos = None
        self._dragging_threshold = 5
        self._minimize_enabled = True
        self._maximize_enabled = True
        self._on_close = on_close
        self._height = height if height is not None else consts.Sizes.MARGIN + consts.Sizes.INDICATOR_WIDTH * 3
        self._title_style = self.Style.THIN

        self.setObjectName('titleFrame')
        self.setFocusPolicy(Qt.NoFocus)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setFixedHeight(dpi.dpi_scale(self._height))

        if not show_title:
            self._title_text.hide()

        QTimer.singleShot(0, self.refresh)
        self.set_title_spacing(False)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def dragging_enabled(self):
        return self._dragging_enabled

    @dragging_enabled.setter
    def dragging_enabled(self, flag):
        self._dragging_enabled = bool(flag)

    @property
    def logo_button(self):
        return self._logo_button

    @property
    def title_label(self):
        return self._title_text

    @property
    def project_button(self):
        return self._project_button

    @property
    def close_button(self):
        return self._close_button

    @property
    def right_contents(self):
        return self._right_contents

    @property
    def left_contents(self):
        return self._left_contents

    @property
    def title_layout(self):
        return self._title_layout

    @property
    def contents_layout(self):
        return self._contents_layout

    @property
    def main_right_layout(self):
        return self._main_right_layout

    @property
    def corner_contents_layout(self):
        return self._corner_contents_layout

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging_enabled:
            self._mouse_press_pos = event.globalPos()
            self._mouse_move_pos = event.globalPos() - self._window.pos()
        super(WindowDragger, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            global_pos = event.globalPos()
            if self._mouse_press_pos and self._dragging_enabled:
                moved = global_pos - self._mouse_press_pos
                if moved.manhattanLength() > self._dragging_threshold:
                    diff = global_pos - self._mouse_move_pos
                    self._window.move(diff)
                    self._mouse_move_pos = global_pos - self._window.pos()
        super(WindowDragger, self).mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._lock_window_operations:
            return
        if self._button_maximized.isVisible():
            self._on_maximize_window()
        else:
            self._on_restore_window()
        super(WindowDragger, self).mouseDoubleClickEvent(event)
        self.doubleClicked.emit()

    def mouseReleaseEvent(self, event):
        if self._mouse_press_pos is not None:
            if event.button() == Qt.LeftButton and self._dragging_enabled:
                moved = event.globalPos() - self._mouse_press_pos
                if moved.manhattanLength() > self._dragging_threshold:
                    event.ignore()
                self._mouse_press_pos = None
        super(WindowDragger, self).mouseReleaseEvent(event)

    def get_main_layout(self):
        """
        Overrides get_main_layout to return an horizontal layout.

        :return: main frame layout.
        :rtype: layout.HorizontalLayout
        """

        main_layout = layouts.HorizontalLayout(spacing=0, margins=(4, 0, 0, 0))
        main_layout.setAlignment(Qt.AlignCenter)

        return main_layout

    def ui(self):
        super(WindowDragger, self).ui()

        menubar = QMenuBar(parent=self)
        self.main_layout.addWidget(menubar)
        menubar.hide()
        menu = menubar.addMenu('Menu')

        if dcc.is_standalone():
            quit_action = menu.addAction('Quit')
            quit_action.triggered.connect(self._on_quit)

        self._logo_button = self._setup_logo_button()
        self._setup_logo_button_actions(self._logo_button)
        self._title_text = labels.ClippedLabel(text=self._window.windowTitle())
        self._title_text.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self._title_text.setMinimumWidth(1)
        self._title_text.setObjectName('WindowDraggerLabel')

        self._button_minimized = QPushButton()
        self._button_minimized.setIconSize(QSize(25, 25))
        self._button_minimized.setIcon(resources.icon('minimize', theme='window'))
        self._button_minimized.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_maximized = QPushButton()
        self._button_maximized.setIcon(resources.icon('maximize', theme='window'))
        self._button_maximized.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_maximized.setIconSize(QSize(25, 25))
        self._button_restored = QPushButton()
        self._button_restored.setVisible(False)
        self._button_restored.setIcon(resources.icon('restore', theme='window'))
        self._button_restored.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_restored.setIconSize(QSize(25, 25))
        self._button_closed = QPushButton()
        self._button_closed.setIcon(resources.icon('close', theme='window'))
        self._button_closed.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_closed.setIconSize(QSize(25, 25))

        self._title_layout = layouts.horizontal_layout(spacing=0, margins=(0, 0, 0, 0))
        self._contents_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._corner_contents_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0))
        self._main_right_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0))
        self._main_right_layout.setAlignment(Qt.AlignVCenter)
        self._window_buttons_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0))
        self._window_buttons_layout.setAlignment(Qt.AlignVCenter)
        self._split_layout = layouts.HorizontalLayout()
        self._left_contents = base.BaseFrame(layout=self._contents_layout, parent=self)
        self._left_contents.setObjectName('leftContentsFrame')
        self._right_contents = base.BaseWidget(layout=self._corner_contents_layout, parent=self)

        self._title_layout.addWidget(self._title_text)

        self._window_buttons_layout.addWidget(self._button_minimized)
        self._window_buttons_layout.addWidget(self._button_maximized)
        self._window_buttons_layout.addWidget(self._button_restored)
        self._window_buttons_layout.addWidget(self._button_closed)

        self._split_layout.addWidget(self._left_contents)
        self._split_layout.addLayout(self._title_layout, 1)
        self._split_layout.addWidget(self._right_contents)

        self._main_right_layout.addLayout(self._split_layout)
        self._main_right_layout.addLayout(self._window_buttons_layout)
        self._main_right_layout.setStretch(0, 1)

        spacing = consts.Sizes.INDICATOR_WIDTH * 2
        self._spacing_item = QSpacerItem(spacing, spacing)
        self._spacing_item2 = QSpacerItem(spacing - 2, spacing - 2)
        self.main_layout.addItem(self._spacing_item)
        self.main_layout.addWidget(self._logo_button)
        self.main_layout.addSpacing(spacing)
        self.main_layout.addItem(self._spacing_item2)
        self.main_layout.addLayout(self._main_right_layout)
        self.main_layout.addSpacing(spacing)

    def setup_signals(self):
        super(WindowDragger, self).setup_signals()

        self._button_maximized.clicked.connect(self._on_maximize_window)
        self._button_minimized.clicked.connect(self._on_minimize_window)
        self._button_restored.clicked.connect(self._on_restore_window)
        self._button_closed.clicked.connect(self._on_close_window)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def refresh(self):
        """
        Refreshes dragger contents.
        """

        qtutils.process_ui_events()
        self.updateGeometry()
        self.update()

    def set_icon(self, icon=None, highlight=False):
        """
        Sets the icon of the window dragger
        :param icon: QIcon
        :param highlight: bool
        """

        icon = icon or self._window.windowIcon()
        if icon and helpers.is_string(icon):
            icon = resources.icon(icon)
        if not icon or icon.isNull():
            icon = resources.icon('tpDcc')

        size = self.DEFAULT_LOGO_ICON_SIZE

        if highlight:
            self._logo_button.set_icon(
                [icon], colors=[None], tint_composition=QPainter.CompositionMode_Plus, size=size,
                icon_scaling=[1], color_offset=0, grayscale=True)
        else:
            self._logo_button.set_icon([icon], colors=None, size=size, icon_scaling=[1], color_offset=0)

        self._logo_button.set_icon_idle(icon)

        # self._lbl_icon.setPixmap(icon.pixmap(icon.actualSize(QSize(24, 24))))

    def set_icon_hover(self, icon=None):
        """
        Sets the icon hover of the window dragger
        :param icon: QIcon
        """

        icon = icon or self._window.windowIcon()
        if icon and helpers.is_string(icon):
            icon = resources.icon(icon)
        if not icon or icon.isNull():
            icon = resources.icon('tpDcc')

        self._logo_button.set_icon_hover(icon)

    def set_height(self, value):
        """
        Sets the size of the dragger and updates icon
        :param value: float
        """

        self.setFixedHeight(dpi.dpi_scale(value))

    def set_title(self, title):
        """
        Sets the title of the window dragger
        :param title: str
        """

        self._title_text.setText(title)

    def set_title_spacing(self, spacing):
        """
        Set title spacing.

        :param bool spacing: whether spacing should be applied.
        """

        _spacing = consts.Sizes.INDICATOR_WIDTH * 2
        if spacing:
            self._spacing_item.changeSize(_spacing, _spacing)
            self._spacing_item2.changeSize(_spacing - 2, _spacing - 2)
        else:
            self._spacing_item.changeSize(0, 0)
            self._spacing_item2.changeSize(0, 0)
            self._split_layout.setSpacing(0)

    def set_dragging_enabled(self, flag):
        """
        Sets whether drag functionality is enabled
        :param flag: bool
        """

        self._dragging_enabled = flag

    def set_minimize_enabled(self, flag):
        """
        Sets whether dragger shows minimize button or not
        :param flag: bool
        """

        self._minimize_enabled = flag
        self._button_minimized.setVisible(flag)

    def set_maximized_enabled(self, flag):
        """
        Sets whether dragger shows maximize button or not
        :param flag: bool
        """

        self._maximize_enabled = flag
        self._button_maximized.setVisible(flag)

    def show_logo(self):
        """
        Shows window logo
        """

        self._logo_button.setVisible(True)

    def hide_logo(self):
        """
        Hides window logo
        """

        self._logo_button.setVisible(False)

    def set_window_buttons_state(self, state, show_close_button=False):
        """
        Sets the state of the dragger buttons
        :param state: bool
        :param show_close_button: bool
        """

        self._lock_window_operations = not state
        self._button_closed.setEnabled(state or show_close_button)
        self._button_closed.setVisible(state or show_close_button)

        if self._maximize_enabled:
            self._button_maximized.setEnabled(state)
            self._button_maximized.setVisible(state)
        else:
            self._button_maximized.setEnabled(False)
            self._button_maximized.setVisible(False)

        if self._minimize_enabled:
            self._button_minimized.setEnabled(state)
            self._button_minimized.setVisible(state)
        else:
            self._button_minimized.setEnabled(False)
            self._button_minimized.setVisible(False)

        if not state:
            self._button_restored.setEnabled(state)
            self._button_restored.setVisible(state)
        else:
            if self.isMaximized():
                self._button_restored.setEnabled(state)
                self._button_restored.setVisible(state)

    def set_frameless_enabled(self, frameless=False):
        """
        Enables/Disables frameless mode or OS system default
        :param frameless: bool
        """

        tool_inst = tools.ToolsManager().get_tool_by_plugin_instance(self._window)
        if not tool_inst:
            return

        offset = QPoint()

        if self._window.docked():
            rect = self._window.rect()
            pos = self._window.mapToGlobal(QPoint(-10, -10))
            rect.setWidth(rect.width() + 21)
            self._window.close()
        else:
            rect = self.window().rect()
            pos = self.window().pos()
            offset = QPoint(3, 15)
            self.window().close()

        tool_inst._launch(launch_frameless=frameless)

        new_tool = tool_inst.latest_tool()

        QTimer.singleShot(
            0, lambda: new_tool.window().setGeometry(
                pos.x() + offset.x(), pos.y() + offset.y(), rect.width(), rect.height()))
        new_tool.framelessChanged.emit(frameless)
        QApplication.processEvents()

        return new_tool

    def _setup_logo_button(self):
        """
        Internal function that setup window dragger button logo
        :return: IconMenuButton
        """

        logo_button = IconMenuButton(parent=self)
        logo_button.setIconSize(QSize(24, 24))
        logo_button.setFixedSize(QSize(30, 30))
        logo_button.menu_align = Qt.AlignLeft

        return logo_button

    def _setup_logo_button_actions(self, logo_button):
        """
        Internal function that setup window dragger button logo actions
        """

        if not logo_button:
            return

        self._toggle_frameless = logo_button.addAction(
            'Toggle Frameless Mode', connect=self._on_toggle_frameless_mode, checkable=True)
        self._toggle_frameless.setChecked(self._window.is_frameless())

        if dcc.is_maya() and dcc.get_version() >= 2022:
            self._toggle_frameless.setText('Toggle Frameless Mode (not available)')
            self._toggle_frameless.setEnabled(False)

    # ==================================================================================================================
    # CALLBACKS
    # ==================================================================================================================

    def _on_quit(self):
        """
        Internal callback function that is called when quit action is triggered by the user.
        """

    def _on_toggle_frameless_mode(self, action):
        """
        Internal callback function that is called when switch frameless mode button is pressed by user
        :param flag: bool
        """

        self.set_frameless_enabled(action.isChecked())

    def _on_maximize_window(self):
        """
        Internal callback function that is called when the user clicks on maximize button
        """

        self._button_restored.setVisible(True)
        self._button_maximized.setVisible(False)
        self._window.setWindowState(Qt.WindowMaximized)

    def _on_minimize_window(self):
        """
        Internal callback function that is called when the user clicks on minimize button
        """

        self._window.setWindowState(Qt.WindowMinimized)

    def _on_restore_window(self):
        """
        Internal callback function that is called when the user clicks on restore button
        """

        self._button_restored.setVisible(False)
        self._button_maximized.setVisible(True)
        self._window.setWindowState(Qt.WindowNoState)

    def _on_close_window(self):
        """
        Internal callback function that is called when the user clicks on close button
        """

        if hasattr(self._window, 'docked'):
            if self._window.docked():
                self._window.fade_close()
            else:
                self.window().fade_close()
        else:
            self._window.fade_close()


class DialogDragger(WindowDragger, object):
    def __init__(self, parent=None, on_close=None):
        super(DialogDragger, self).__init__(window=parent, on_close=on_close)

        for btn in [self._button_maximized, self._button_minimized, self._button_restored]:
            btn.setEnabled(False)
            btn.setVisible(False)

    def mouseDoubleClickEvent(self, event):
        return

    def _setup_logo_button(self):
        """
        Internal function that setup window dragger button logo
        :return: IconMenuButton
        """

        logo_button = IconMenuButton(parent=self)
        logo_button.setIconSize(QSize(24, 24))
        logo_button.setFixedSize(QSize(30, 30))

        return logo_button


class ButtonIcons(QAbstractButton):

    highlightOffset = 40
    iconColors = (128, 128, 128)
    iconScaling = list()
    grayscale = False
    tintComposition = None

    icon = None
    idleIcon = None
    pressedIcon = None
    hoverIcon = None

    def enterEvent(self, event):
        if self.hoverIcon is not None:
            self.setIcon(self.hoverIcon)

    def leaveEvent(self, event):
        if self.idleIcon is not None:
            self.setIcon(self.idleIcon)

    def setIconSize(self, size):
        if self.idleIcon is None:
            return

        super(ButtonIcons, self).setIconSize(dpi.size_by_dpi(size))
        self.update_icons()

    def set_highlight(self, highlight):
        self.highlightOffset = highlight

    def set_icon(self, icon, colors=None, size=None, color_offset=None, icon_scaling=None,
                 tint_composition=QPainter.CompositionMode_Plus, grayscale=False):

        if size is not None:
            self.setIconSize(QSize(size, size))

        if color_offset is not None:
            self.highlightOffset = color_offset

        if icon_scaling is not None:
            self.iconScaling = icon_scaling

        colors = colors or self.iconColors
        self.grayscale = grayscale
        self.tintComposition = tint_composition

        self.icon = icon
        self.set_icon_color(colors, update=False)
        self.update_icons()

    def set_icon_color(self, colors, update=True):
        if any(isinstance(el, list) for el in colors):
            self.iconColors = colors
        else:
            self.iconColors = [helpers.force_list(colors)]
        if update and self.idleIcon is not None and self.icon is not None:
            self.update_icons()

    def update_icons(self):
        if not self.icon:
            return

        hover_color = (255, 255, 255, self.highlightOffset)

        self.idleIcon = icon.colorize_layered_icon(
            icons=self.icon, size=self.iconSize().width(), scaling=self.iconScaling,
            composition=self.tintComposition, colors=self.iconColors, grayscale=self.grayscale
        )

        self.hoverIcon = icon.colorize_layered_icon(
            icons=self.icon, size=self.iconSize().width(), scaling=self.iconScaling,
            composition=self.tintComposition, tint_color=hover_color, grayscale=self.grayscale
        )

        self.setIcon(self.idleIcon)

    def set_icon_idle(self, idle_icon):
        self.idleIcon = idle_icon
        self.setIcon(idle_icon)

    def set_icon_hover(self, hover_icon):
        self.hoverIcon = hover_icon


class BaseMenuButton(QPushButton, ButtonIcons):

    class SearchMenu(menus.SearchableMenu, object):
        def __init__(self, **kwargs):
            super(BaseMenuButton.SearchMenu, self).__init__(**kwargs)

            self._tt_key_pressed = False
            self._tt_key = Qt.Key_Control

        def keyPressEvent(self, event):
            if event.key() == self._tt_key:
                pos = self.mapFromGlobal(QCursor.pos())
                action = self.actionAt(pos)
                if tooltips.has_expanded_tooltips(action):
                    self._popup_tooltip = tooltips.ExpandedTooltipPopup(
                        widget=action, icon_size=dpi.dpi_scale(40), popup_release=self._tt_key)
                    self._tt_key_pressed = True
            super(BaseMenuButton.SearchMenu, self).keyPressEvent(event)

        def keyReleaseEvent(self, event):
            if event.key() == Qt.Key_Control:
                self._tt_key_pressed = False

        def index(self, name, exclude_search=True):
            for i, a in enumerate(self.actions()):
                if a.text() == name:
                    ret = i
                    if exclude_search:
                        ret -= 2
                    return ret

    leftClicked = Signal()
    middleClicked = Signal()
    rightClicked = Signal()

    leftDoubleClicked = Signal()
    middleDoubleClicked = Signal()
    rightDoubleClicked = Signal()
    clicked = leftClicked

    menuAboutToShow = Signal()
    middleMenuAboutToShow = Signal()
    rightMenuAboutToShow = Signal()

    menuChanged = Signal()
    middleMenuChanged = Signal()
    rigthMenuChanged = Signal()

    actionTriggered = Signal(object, object)

    SINGLE_CLICK = 1
    DOUBLE_CLICK = 2

    highlightOffset = 4

    def __init__(self, icon=None, icon_hover=None, text=None, parent=None, double_click_enabled=False,
                 menu_padding=5, menu_align=Qt.AlignLeft):
        """
        :param icon:
        :param icon_hover:
        :param text:
        :param parent:
        :param double_click_enabled:
        """

        self.idleIcon = icon or QIcon()
        self.hoverIcon = icon_hover or QIcon()

        super(BaseMenuButton, self).__init__(icon=self.idleIcon, text=text, parent=parent)

        self._menu_active = {
            Qt.LeftButton: True,
            Qt.MidButton: True,
            Qt.RightButton: True
        }

        self._click_menu = {
            Qt.LeftButton: None,
            Qt.MidButton: None,
            Qt.RightButton: None
        }

        self._menu_searchable = {
            Qt.LeftButton: False,
            Qt.MidButton: False,
            Qt.RightButton: False
        }

        self._last_click = None
        self._icon_color = None
        self._menu_padding = menu_padding
        self._menu_align = menu_align

        self.leftClicked.connect(partial(self._on_context_menu, Qt.LeftButton))
        self.middleClicked.connect(partial(self._on_context_menu, Qt.MidButton))
        self.rightClicked.connect(partial(self._on_context_menu, Qt.RightButton))

        app = QApplication.instance()
        if app and hasattr(app, 'doubleClickInterval') and callable(app.doubleClickInterval):
            self._double_click_interval = QApplication.instance().doubleClickInterval()
        else:
            self._double_click_interval = 500
        self._double_click_enabled = double_click_enabled

    @property
    def double_click_interval(self, interval=150):
        return self._double_click_interval

    @double_click_interval.setter
    def double_click_interval(self, interval=150):
        self._double_click_interval = interval

    @property
    def double_click_enabled(self):
        return self._double_click_enabled

    @double_click_enabled.setter
    def double_click_enabled(self, enabled):
        self._double_click_enabled = enabled

    def setWindowTitle(self, window_title, mouse_menu=Qt.LeftButton):
        new_menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        new_menu.setWindowTitle(window_title)

    def setMenu(self, menu, mouse_button=Qt.LeftButton):
        self._click_menu[mouse_button] = menu

    def setFixedHeight(self, height):
        return super(BaseMenuButton, self).setFixedHeight(dpi.dpi_scale(height))

    def setFixedWidth(self, width):
        return super(BaseMenuButton, self).setFixedWidth(dpi.dpi_scale(width))

    def setFixedSize(self, size):
        super(BaseMenuButton, self).setFixedSize(dpi.dpi_scale(size))

    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setDown(True)
        elif event.button() == Qt.RightButton:
            self.setDown(True)

        self._last_click = self.SINGLE_CLICK

    def mouseReleaseEvent(self, event):
        button = event.button()
        self.setDown(False)
        if not self._double_click_enabled:
            self.mouse_single_click_action(button)
            return

        if self._last_click == self.SINGLE_CLICK:
            QTimer.singleShot(self._double_click_interval, lambda: self.mouse_single_click_action(button))
        else:
            self.mouseDoubleClickAction(event.button())

    def mouseDoubleClickEvent(self, event):
        self._last_click = self.DOUBLE_CLICK

    def menu(self, mouse_menu=Qt.LeftButton, searchable=False, auto_create=True, parent=None):
        """
        Overrides base menu function
        Get menu depending on the mouse button pressed
        :param mouse_menu:
        :param searchable:
        :param auto_create:
        :return:
        """

        if not self._click_menu[mouse_menu] and auto_create:
            self._click_menu[mouse_menu] = BaseMenuButton.SearchMenu(
                objectName='searchButton', title='Search Button', parent=parent)
            self._click_menu[mouse_menu].triggered.connect(lambda action: self.actionTriggered.emit(action, mouse_menu))
            self._click_menu[mouse_menu].triggered.connect(partial(self._on_menu_changed, mouse_menu))
            if not searchable:
                self._click_menu[mouse_menu].set_search_visible(False)

        return self._click_menu[mouse_menu]

    def index(self, name, mouse_menu=Qt.LeftButton):
        """
        Returns the index of the menu or action item
        :param name: str
        :param mouse_menu:
        :return: int
        """

        return self.menu(mouse_menu).index(name)

    def mouse_single_click_action(self, button):
        if self._last_click == self.SINGLE_CLICK or self._double_click_enabled is False:
            if button == Qt.LeftButton:
                self.leftClicked.emit()
            elif button == Qt.MidButton:
                self.middleClicked.emit()
            elif button == Qt.RightButton:
                self.rightClicked.emit()

    def mouse_double_click_action(self, button):
        if button == Qt.LeftButton:
            self.leftDoubleClicked.emit()
        elif button == Qt.MidButton:
            self.middleDoubleClicked.emit()
        elif button == Qt.RightButton:
            self.rightDoubleClicked.emit()

    def set_searchable(self, mouse_menu=Qt.LeftButton, searchable=True):
        """
        Sets whether menu with given mouse interaction is searchable or not
        :param mouse_menu:
        :param searchable: bool
        """

        self._menu_searchable[mouse_menu] = searchable
        if self._click_menu[mouse_menu]:
            self._click_menu[mouse_menu].set_search_visible(searchable)

    def is_searchable(self, mouse_menu=Qt.LeftButton):
        """
        Returns whether given button menu is searchable or not
        :param mouse_menu:
        """

        if self._click_menu[mouse_menu] is not None:
            return self._click_menu[mouse_menu].search_visible()

        return self._menu_searchable[mouse_menu]

    def set_tear_off_enabled(self, mouse_menu=Qt.LeftButton, tear_off=True):
        menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        menu.setTearOffEnabled(tear_off)

    def set_menu_align(self, align=Qt.AlignLeft):
        self._menu_align = align

    def clear_menu(self, mouse_menu):
        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].clear()

    def addAction(
            self, name, mouse_menu=Qt.LeftButton, connect=None, checkable=False, checked=True,
            action=None, action_icon=None, data=None, icon_text=None, icon_color=None, icon_size=16):
        """
        Overrides base addAction function.

        Adds a new menu item through an action.
        :param str name: str, name of the menu item.
        :param Qt.LeftButton or Qt.MidButton or Qt.RightButton mouse_menu: button that will launch menu.
        :param callable connect: fn, function to launch when the item is pressed.
        :param bool checkable: whether this menu is checkable.
        :param bool checked: whether this menu is checked by default.
        :param action:
        :param action_icon:
        :param data:
        :param icon_text:
        :param icon_color:
        :param icon_size:
        :return:
        """

        new_menu = self.menu(mouse_menu, searchable=False)
        if action is not None:
            new_menu.addAction(action)
            return

        new_action = menus.SearchableTaggedAction(label=name, parent=new_menu)
        new_action.setCheckable(checkable)
        new_action.setChecked(checked)
        new_action.tags = set(self._string_to_tags(name))
        new_action.setData(data)
        new_menu.addAction(new_action)

        if action_icon is not None:
            if isinstance(action_icon, QIcon):
                new_action.setIcon(action_icon)
                new_action.setIconText(icon_text or '')
            elif helpers.is_string(action_icon):
                new_action.setIconText(action_icon or icon_text or None)
                action_icon = resources.icon(action_icon)
                new_action.setIcon(
                    icon.colorize_layered_icon(action_icon, colors=[icon_color], size=dpi.dpi_scale(icon_size)))

        if connect is not None:
            if checkable:
                new_action.triggered.connect(partial(connect, new_action))
            else:
                new_action.triggered.connect(connect)

        return new_action

    def add_separator(self, mouse_menu=Qt.LeftButton):
        new_menu = self.menu(mouse_menu)
        new_menu.addSeparator()

    def launch_context_menu(self, mouse_btn):
        menu = self._click_menu[mouse_btn]

        if menu is not None and self._menu_active[mouse_btn]:
            pos = self.menu_pos(widget=menu, align=self._menu_align)
            menu.exec_(pos)
            # add focuss
            # menu.search_edit.focus()

    def menu_pos(self, widget=None, align=Qt.AlignLeft):
        """
        Returns menu position based on the current widget position and size
        :param widget: QWidget, widget to culculate the width based off
        :param align:  Qt.Alignleft or Qt.AlignRight, whether to align menu left or right
        :return:
        """

        pos = 0

        if align == Qt.AlignLeft:
            point = self.rect().bottomLeft() - QPoint(0, -self._menu_padding)
            pos = self.mapToGlobal(point)
        elif align == Qt.AlignRight:
            point = self.rect().bottomRight() - QPoint(widget.sizeHint().width(), -self._menu_padding)
            pos = self.mapToGlobal(point)

        return pos

    def _string_to_tags(self, string):
        res = list()
        res += string.split(' ')
        res += [s.lower() for s in string.split(' ')]

        return res

    def _on_context_menu(self, mouse_btn):
        self.launch_context_menu(mouse_btn=mouse_btn)

    def _on_menu_changed(self, mouse_button, object):
        if mouse_button == Qt.LeftButton:
            self.menuChanged.emit()
        elif mouse_button == Qt.MiddleButton:
            self.middleMenuChanged.emit()
        elif mouse_button == Qt.RightButton:
            self.rigthMenuChanged.emit()


class IconMenuButton(BaseMenuButton, object):

    itemChanged = Signal()

    def __init__(self, icon=None, icon_hover=None, parent=None, double_click_enabled=False, color=(255, 255, 255),
                 icon_menu_state_str='', icon_menu_state_int=0):
        super(IconMenuButton, self).__init__(
            icon=icon, icon_hover=icon_hover, parent=parent, double_click_enabled=double_click_enabled)

        self._icon_color = color
        self._current_menu_item_str = icon_menu_state_str
        self._current_menu_index_int = icon_menu_state_int
        self._menu_name_list = list()
        self._menu_icon_list = list()

        for m in self._click_menu.values():
            if m is not None:
                m.setToolTipsVisible(True)

            self.set_menu_align(Qt.AlignRight)

    @property
    def current_menu_item(self):
        return self._current_menu_item_str

    @property
    def current_menu_index(self):
        return self._current_menu_index_int

    def set_menu_name(self, menu_item_name):
        self._current_menu_item_str = menu_item_name
        self._current_menu_index_int = self._menu_name_list.index(menu_item_name)
        icon_name = self._menu_icon_list[self._current_menu_index_int]

    def icon_and_menu_name_lists(self, mode_list):
        self._menu_name_list = list()
        self._menu_icon_list = list()
        for i, m in enumerate(mode_list):
            self._menu_name_list.append(m[1])
            self._menu_icon_list.append(m[0])