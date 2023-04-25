#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different buttons
"""

from functools import partial

from Qt.QtCore import Qt, Signal, Property, QPoint, QSize, QRect, QTimer
from Qt.QtWidgets import QApplication, QSizePolicy, QAbstractButton, QPushButton, QToolButton, QRadioButton, QWidget
from Qt.QtWidgets import QDialog, QButtonGroup, QGraphicsOpacityEffect
from Qt.QtGui import QCursor, QIcon, QFontMetrics, QPainter, QColor, QRegion

from tp.core import dcc, log
from tp.core.managers import resources
from tp.common.python import helpers, decorators
from tp.common.resources import icon, theme
from tp.common.qt import consts, animation, qtutils, dpi, base
from tp.common.qt.widgets import tooltips, layouts, labels, menus

logger = log.tpLogger


def button(text='', icon=None, icon_size=16, icon_color=None, icon_hover_color=None, overlay_icon_color=None,
           overlay_icon=None, icon_color_theme=None, min_width=None, max_width=None, min_height=None,
           max_height=None, width=None, height=None, style=None, tooltip='', theme_updates=True, checkable=False,
           checked=False, parent=None):
    """
    Creates a new button with the given options.

    :param str text: button text.
    :param str or QIcon icon: icon name or QIcon instance.
    :param int icon_size: size of the icon in pixels.
    :param tuple(int, int, int) icon_color: icon color in 0 to 255 range.
    :param tuple(int, int, int) icon_hover_color: icon hover color in 0 to 255 range.
    :param tuple(int, int, int) overlay_icon_color: color of the overlay image icon.
    :param str or QIcon overlay_icon: the name of the icon image that will be overlay on top of the original icon.
    :param str icon_color_theme: color attribute that should be applied from current applied theme.
    :param int min_width: minimum width of the button in pixels.
    :param int max_width: maximum width of the button in pixels.
    :param int min_height: minimum height of the button in pixels.
    :param int max_height: maximum height of the button in pixels.
    :param int width: fixed width of the button in pixels. This one overrides the values defined in min/max values.
    :param int height: fixed height of the button in pixels. This one overrides the values defined in min/max values.
    :param ButtonStyles style: the style of the button.
    :param str tooltip: tooltip as seen with mouse over.
    :param bool theme_updates: whether  button style will be updated when current style changes.
    :param bool checkable: whether the button can be checked.
    :param bool checked: whether (if checkable is True) button is checked by default.
    :param QWidget parent: parent widget.
    :return: newly created button.
    :rtype: QPushButton

    ..note:: button icons are always squared.
    """

    style = style or ButtonStyles.DEFAULT
    min_width = min_width if width is None else width
    max_width = max_width if width is None else width
    min_height = min_height if height is None else height
    max_height = max_height if height is None else height
    icon = resources.icon(icon) if helpers.is_string(icon) else icon
    overlay_icon = resources.icon(overlay_icon) if helpers.is_string(overlay_icon) else overlay_icon

    if style in (ButtonStyles.DEFAULT, ButtonStyles.TRANSPARENT_BACKGROUND):
        return base_button(
            text=text, icon=icon, icon_size=icon_size, icon_color=icon_color, icon_hover_color=icon_hover_color,
            icon_color_theme=icon_color_theme, min_width=min_width, max_width=max_width, min_height=min_height,
            max_height=max_height, style=style, tooltip=tooltip, theme_updates=theme_updates, checkable=checkable,
            checked=checked, parent=parent)
    elif style == ButtonStyles.DEFAULT_QT:
        return regular_button(
            text=text, icon=icon, icon_size=icon_size, icon_color=icon_color, overlay_icon_color=overlay_icon_color,
            overlay_icon=overlay_icon, min_width=min_width, max_width=max_width, min_height=min_height,
            max_height=max_height, style=style, tooltip=tooltip, theme_updates=theme_updates, checkable=checkable,
            checked=checked, parent=parent)
    elif style == ButtonStyles.ROUNDED:
        return rounded_button(
            text=text, icon=icon, icon_size=icon_size, icon_color=icon_color, tooltip=tooltip,
            button_width=width, button_height=height, checkable=checkable, checked=checked, parent=parent
        )
    else:
        logger.warning('Button style "{}" is not supported. Default button will be created'.format(style))
        return regular_button(
            text=text, icon=icon, icon_size=icon_size, icon_color=icon_color, overlay_icon_color=overlay_icon_color,
            overlay_icon=overlay_icon, min_width=min_width, max_width=max_width, min_height=min_height,
            max_height=max_height, style=style, tooltip=tooltip, theme_updates=theme_updates, checkable=checkable,
            checked=checked, parent=parent)


def base_button(text='', **kwargs):
    """
    Creates an extended CPG PushButton with a transparent background or with its regular style.

    :param str text: button text.
    :param dict kwargs: keyword arguments.
    :return: newly created button.
    :rtype: QPushButton
    """

    icon = kwargs.get('icon', None)
    icon_size = kwargs.get('icon_size', 16)
    icon_color = kwargs.get('icon_color', None)
    icon_hover_color = kwargs.get('icon_hover_color', None)
    icon_color_theme = kwargs.get('icon_color_theme', None)
    style = kwargs.get('style', None)
    tooltip = kwargs.get('tooltip', '')
    theme_updates = kwargs.get('theme_updates', True)
    min_width = kwargs.get('min_width', None)
    max_width = kwargs.get('max_width', None)
    min_height = kwargs.get('min_height', None)
    max_height = kwargs.get('max_height', None)
    parent = kwargs.get('parent', None)
    checkable = kwargs.get('checkable', False)
    checked = kwargs.get('checked', False)

    if icon:
        kwargs = dict(text=text, icon_color_theme=icon_color_theme, theme_updates=theme_updates, parent=parent)
        new_button = BasePushButton(**kwargs) if style == ButtonStyles.DEFAULT else BaseButton(**kwargs)
        new_button.set_icon(icon, size=icon_size, colors=icon_color, hover_colors=icon_hover_color)
    else:
        kwargs = dict(text=text, icon_color_theme=icon_color_theme, parent=parent)
        new_button = BasePushButton(**kwargs) if style == ButtonStyles.DEFAULT else BaseButton(**kwargs)
    new_button.setToolTip(tooltip)

    if min_width is not None:
        new_button.setMinimumWidth(min_width)
    if max_width is not None:
        new_button.setMaximumWidth(max_width)
    if min_height is not None:
        new_button.setMinimumHeight(min_height)
    if max_height is not None:
        new_button.setMaximumHeight(max_height)
    if checkable:
        new_button.setCheckable(True)
        new_button.setChecked(checked)

    return new_button


def base_push_button(text='', **kwargs):
    """
    Creates an extended CPG PushButton with a transparent background or with its regular style.

    :param str text: button text.
    :param dict kwargs: keyword arguments.
    :return: newly created button.
    :rtype: QPushButton
    """

    kwargs.pop('style', None)
    return base_button(text=text, style=ButtonStyles.DEFAULT, **kwargs)


def regular_button(**kwargs):
    """
    Creates a standard Qt QPushButton.

    :param dict kwargs: keyword arguments.
    :return: newly created button.
    :rtype: QPushButton
    """

    text = kwargs.get('text', '')
    button_icon = kwargs.get('icon', None)
    icon_size = kwargs.get('icon_size', 16)
    icon_color = kwargs.get('icon_color', None)
    overlay_icon = kwargs.get('overlay_icon', None)
    overlay_icon_color = kwargs.get('overlay_icon_color', None)
    tooltip = kwargs.get('tooltip', '')
    min_width = kwargs.get('min_width', None)
    max_width = kwargs.get('max_width', None)
    min_height = kwargs.get('min_height', None)
    max_height = kwargs.get('max_height', None)
    parent = kwargs.get('parent', None)
    checkable = kwargs.get('checkable', False)
    checked = kwargs.get('checked', False)

    new_button = QPushButton(text, parent=parent)
    if button_icon:
        new_button.setIcon(icon.colorize_icon(
            button_icon, size=dpi.dpi_scale(icon_size), color=icon_color,
            overlay_icon=overlay_icon, overlay_color=overlay_icon_color))
    new_button.setToolTip(tooltip)

    if min_width is not None:
        new_button.setMinimumWidth(dpi.dpi_scale(min_width))
    if max_width is not None:
        new_button.setMaximumWidth(dpi.dpi_scale(max_width))
    if min_height is not None:
        new_button.setMinimumHeight(dpi.dpi_scale(min_height))
    if max_height is not None:
        new_button.setMaximumHeight(dpi.dpi_scale(max_height))
    if checkable:
        new_button.setCheckable(True)
        new_button.setChecked(checked)

    return new_button


def rounded_button(**kwargs):

    text = kwargs.get('text', '')
    button_icon = kwargs.get('icon', None)
    icon_size = kwargs.get('icon_size', 16)
    icon_color = kwargs.get('icon_color', None)
    tooltip = kwargs.get('tooltip', '')
    parent = kwargs.get('parent', None)
    button_width = kwargs.get('button_width', None) or 24
    button_height = kwargs.get('button_height', None) or 24
    checkable = kwargs.get('checkable', False)
    checked = kwargs.get('checked', False)

    button_icon = button_icon or QIcon()
    if button_icon and not button_icon.isNull():
        button_icon = icon.colorize_icon(button_icon, size=icon_size, color=icon_color)
    new_button = RoundButton(text=text, icon=button_icon, tooltip=tooltip, parent=parent)
    new_button.setFixedSize(QSize(button_width, button_height))
    if checkable:
        new_button.setCheckable(True)
        new_button.setChecked(checked)

    return new_button


def tool_button(text='', icon=None, tooltip='', parent=None):
    """
    Creates a new QToolButton instance.

    :param str text: tool button text.
    :param str or QIcon icon: tool button icon.
    :param QWidget parent: tool button parent widget.

    :return: new tool button instance.
    :rtype: BaseToolButton
    """

    new_tool_button = BaseToolButton(parent=parent)
    new_tool_button.setText(text)
    if icon:
        new_tool_button.image(icon)
    if tooltip:
        new_tool_button.setToolTip(tooltip)

    return new_tool_button


def axis_button(axis_type='x', parent=None, as_tool_button=True):
    """
    Creates a new button with the icon defined by the axis type argument.

    :param str axis_type: axis type we want to create button for ('x' or 'y' or 'z')
    :param QWidget parent: optional button parent widget.
    :param bool as_tool_button: whether to create a normal button or a tool button.
    :return: newly created axis button.
    :rtype: BaseButton or BaseToolButton
    """

    axis = axis_type.lower() if axis_type else 'x'
    axis = axis if axis in consts.AXISES_COLORS else 'x'
    if as_tool_button:
        axis_btn = BaseToolButton(parent=parent)
    else:
        axis_btn = BaseButton(parent=parent)
    axis_icon = resources.icon('{}_axis'.format(axis), color=QColor(*consts.AXISES_COLORS[axis]))
    axis_btn.setIcon(axis_icon)

    return axis_btn


def shadowed_button(text='', shadow_height=4, force_upper=False, tooltip='', icon_color_theme=None,
                    theme_updates=True, parent=None):
    """
    Creates a new shadowed button.

    :param text:
    :param shadow_height:
    :param force_upper:
    :param tooltip:
    :param icon_color_theme:
    :param theme_updates:
    :param parent:
    :return: newly created shadowed button.
    :rtype: ShadowedButton
    """

    new_button = ShadowedButton(
        text=text, shadow_height=shadow_height, force_upper=force_upper, tooltip=tooltip,
        icon_color_theme=icon_color_theme, theme_updates=theme_updates, parent=parent)

    return new_button


class ButtonStyles(object):
    DEFAULT = 0                         # default CPG BaseButton with optional text or an icon.
    TRANSPARENT_BACKGROUND = 1          # default CPG BaseButton with a transparent background.
    DEFAULT_QT = 2                      # default style using standard Qt PushButton.
    ROUNDED = 3                         # rounded button with a background color and a colored icon.


class AbstractButton(QAbstractButton, dpi.DPIScaling):

    _icon = None
    _idle_icon = None
    _pressed_icon = None
    _hover_icon = None
    _highlight_offset = 40
    _icon_names = list()
    _icon_colors = (200, 200, 200)
    _icon_scaling = list()
    _grayscale = False
    _tint_composition = None

    def __init__(self, *args, **kwargs):
        super(AbstractButton, self).__init__(*args, **kwargs)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def enterEvent(self, event):
        """
        Overrides base enterEvent function to update hover icon.

        :param QEvent event: Qt event.
        """

        if self._hover_icon and self.isEnabled():
            self.setIcon(self._hover_icon)

    def leaveEvent(self, event):
        """
        Overrides base leaveEvent function to update hover icon.

        :param QEvent event: Qt event.
        """

        if self._idle_icon and self.isEnabled():
            self.setIcon(self._idle_icon)

    def setEnabled(self, flag):
        """
        Overrides base setEnabled function to make sure icons are updated when enable status changes.

        :param bool flag: True to enable the button; False otherwise.
        """

        super(AbstractButton, self).setEnabled(flag)
        self.update_icons()

    def setIconSize(self, size):
        """
        Overrides base setIconSize function to make sure icon size respects DPI

        :param QSize size: new icon size
        """

        super(AbstractButton, self).setIconSize(dpi.size_by_dpi(size))

        # force update of the icons after resizing
        self.update_icons()

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def set_highlight(self, value):
        """
        Sets the highlight offset of the icon.

        :param float value: highlight offset .
        """

        self._highlight_offset = value

    def set_icon(self, icon, colors=None, hover_colors=None, size=None, color_offset=None, scaling=None, **kwargs):
        """
        Set the icon of the button.

        :param str or QIcon icon: button icon.
        :param colors:
        :param int size: icon size.
        :param float, color_offset: icon highlight offset.
        :param list(float, float) scaling: icon scaling.
        :param dict kwargs: extra arguments.
        """

        if size is not None:
            self.setIconSize(QSize(size, size))
        if color_offset is not None:
            self._highlight_offset = color_offset
        if scaling is not None:
            self._icon_scaling = scaling

        self._icon_names = icon

        self._grayscale = kwargs.pop('grayscale', False)
        self._tint_composition = kwargs.pop('tint_composition', QPainter.CompositionMode_Plus)
        colors = colors or self._icon_colors
        # self.set_icon_color(colors, update=False)
        self.update_icons()

    def set_icon_idle(self, idle_icon, update=True):
        """
        Sets the icon idle.

        :param QIcon idle_icon: idle icon.
        :param bool update: whether force icons update.
        """

        self._idle_icon = idle_icon
        self.setIcon(idle_icon)
        if update:
            self.update_icons()

    def set_icon_hover(self, hover_icon, update=True):
        """
        Sets the icon hover.

        :param QIcon hover_icon: hover icon.
        :param bool update: whether to force icons update.
        """

        self._hover_icon = hover_icon
        if update:
            self.update_icons()

    def set_icon_color(self, colors, update=True):
        """
        Set the color of the icon.

        :param QColor or list colors: icon color or colors
        :param bool update: whether to force icons update.
        """

        if type(self._icon_names) is list and len(self._icon_names) >= 2:
            icons = len(self._icon_names)
            if type(colors) is tuple and len(colors) == 3:
                colors = [colors for i in range(icons)]

        self._icon_colors = colors

        if update and self._idle_icon is not None and self._icon_names is not None:
            self.update_icons()

    def update_icons(self):
        """
        Updates the button icons.
        """

        if not self._icon_names:
            return

        hover_color = (255, 255, 255, self._highlight_offset)

        grayscale = self._grayscale or not self.isEnabled()

        self._idle_icon = icon.colorize_layered_icon(
            icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
            composition=self._tint_composition, colors=self._icon_colors, grayscale=grayscale)

        self._hover_icon = icon.colorize_layered_icon(
            icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
            composition=self._tint_composition, colors=self._icon_colors, tint_color=hover_color,
            grayscale=grayscale)

        self.setIcon(self._idle_icon)


@theme.mixin
class BaseButton(QPushButton, AbstractButton):
    """
    Custom button implementation that extends default Qt QPushButton widget
    """

    SINGLE_CLICK = 1
    DOUBLE_CLICK = 2

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
    rightMenuChanged = Signal()
    actionTriggered = Signal(object, object)

    class Types(object):
        DEFAULT = 'default'
        PRIMARY = 'primary'
        SUCCESS = 'success'
        WARNING = 'warning'
        DANGER = 'danger'

    class BaseMenuButtonMenu(menus.SearchableMenu):
        """
        Custom menu that can be attached to BaseButton
        """

        def __init__(self, *args, **kwargs):
            super(BaseButton.BaseMenuButtonMenu, self).__init__(*args, **kwargs)

            self._key_pressed = False
            self._key = Qt.Key_Control

            self.setAttribute(Qt.WA_TranslucentBackground)

        # =============================================================================================================
        # OVERRIDES
        # =============================================================================================================

        def keyPressEvent(self, event):
            if event.key() == self._key:
                pos = self.mapFromGlobal(QCursor.pos())
                action = self.actionAt(pos)
                if tooltips.has_expanded_tooltips(action):
                    self._popup_tooltip = tooltips.ExpandedTooltipPopup(
                        action, icon_size=dpi.dpi_scale(40), popup_release=self._key)
                self._key_pressed = True
            super(BaseButton.BaseMenuButtonMenu, self).keyPressEvent(event)

        def keyReleaseEvent(self, event):
            if event.key() == Qt.Key_Control:
                self._key_pressed = False

        # =============================================================================================================
        # BASE
        # =============================================================================================================

        def index(self, name, exclude_search=True):
            for i, action in enumerate(self.actions()):
                if action.text() == name:
                    result = i
                    if exclude_search:
                        result -= 2
                    return result

    def __init__(self, text='', icon=None, icon_hover=None, icon_color_theme=None, elided=False, theme_updates=True,
                 parent=None, **kwargs):
        super(BaseButton, self).__init__(text=text, parent=parent)

        self._text = text
        self._elided = elided
        self._idle_icon = icon or QIcon()
        self._hover_icon = icon_hover or QIcon()
        self._icon_color_theme = icon_color_theme
        self._theme_updates = theme_updates
        self._double_click_enabled = kwargs.pop('double_click_enabled', False)
        self._double_click_interval = 500
        self._last_click = None
        self._menu_padding = kwargs.pop('menu_padding', 5)
        self._menu_align = kwargs.pop('menu_align', Qt.AlignLeft)
        self._icon_colors = helpers.force_list(kwargs.pop('color', None)) or self._icon_colors
        description = kwargs.pop('description', '')

        self._menu_active = {           # defines which menus are active
            Qt.LeftButton: True,
            Qt.MidButton: True,
            Qt.RightButton: True
        }
        self._click_menu = {            # stores available menus
            Qt.LeftButton: None,
            Qt.MidButton: None,
            Qt.RightButton: None
        }
        self._menu_searchable = {       # defines which menus are searchable
            Qt.LeftButton: False,
            Qt.MidButton: False,
            Qt.RightButton: False
        }

        self._type = self.Types.DEFAULT
        self._size = self.theme_default_size()

        # without this, button will not call focusIn/out events when pressed
        self.setFocusPolicy(Qt.StrongFocus)

        self.setStatusTip(description)
        self.setToolTip(description)
        self.setWhatsThis(description)

        if icon:
            self.set_icon(icon)

        self.leftClicked.connect(partial(self._on_context_menu, Qt.LeftButton))
        self.middleClicked.connect(partial(self._on_context_menu, Qt.MidButton))
        self.rightClicked.connect(partial(self._on_context_menu, Qt.RightButton))

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def menu_align(self):
        return self._menu_align

    @menu_align.setter
    def menu_align(self, align=Qt.AlignLeft):
        self._menu_align = align

    @property
    def double_click_enabled(self, flag):
        return self._double_click_enabled

    @double_click_enabled.setter
    def double_click_enabled(self, flag):
        self._double_click_enabled = flag

    @property
    def double_click_interval(self):
        return self._double_click_interval

    @double_click_interval.setter
    def double_click_interval(self, interval=150):
        self._double_click_interval = interval

    # =================================================================================================================
    # QT PROPERTIES
    # =================================================================================================================

    def _get_type(self):
        """
        Returns button type.

        :return: button type.
        :rtype: str
        """

        return self._type

    def _set_type(self, value):
        """
        Sets button type.

        :param str value: button type.
        """

        if value in [self.Types.DEFAULT, self.Types.PRIMARY, self.Types.SUCCESS, self.Types.WARNING, self.Types.DANGER]:
            self._type = value
        else:
            logger.warning(
                'Given button type: "{}" is not supported. Supported types '
                'are: default, primary, success, warning and danger'.format(value))

        self.style().polish(self)

    def _get_size(self):
        """
        Returns the button height size.

        :return: button height.
        :rtype: int
        """

        return self._size

    def _set_size(self, value):
        """
        Sets button height size.

        :param int value: button height.
        """

        self._size = value
        self.style().polish(self)

    theme_type = Property(str, _get_type, _set_type)
    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def mousePressEvent(self, event):
        """
        Overrides mousePressEvent function.

        :param QEvent event: Qt mouse event.
        :return:
        """

        if event.button() == Qt.MidButton:
            self.setDown(True)
        elif event.button() == Qt.RightButton:
            self.setDown(True)

        self._last_click = self.SINGLE_CLICK

        super(BaseButton, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Overrides mouseReleaseEvent function.

        :param QEvent event: Qt mouse event.
        :return:
        """

        button = event.button()

        # TODO: This breaks the button checkable status ...
        # self.setDown(False)

        if not self._double_click_enabled:
            self._mouse_single_click_action(button)
            super(BaseButton, self).mouseReleaseEvent(event)
            return

        if self._last_click == self.SINGLE_CLICK:
            QTimer.singleShot(self._double_click_interval, lambda: self._mouse_single_click_action(button))
        else:
            self._mouse_double_click_action(button)

        super(BaseButton, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        Overrides mouseDoubleClickEvent function.

        :param QEvent event: Qt mouse event.
        :return:
        """

        self._last_click = self.DOUBLE_CLICK

    def resizeEvent(self, event):
        """
        Overrides resizeEvent function that adds elide functionality.

        :param QEvent event: Qt resize event.
        """

        if self._elided:
            has_icon = self.icon() and not self.icon().isNull()
            if has_icon:
                font_metrics = QFontMetrics(self.font())
                elided = font_metrics.elidedText(self._text, Qt.ElideMiddle, self.width() - 30)
                super(BaseButton, self).setText(elided)
        super(BaseButton, self).resizeEvent(event)

    def setText(self, text):
        """
        Overrides base setText function.

        :param str text: new button text.
        """

        self._text = text
        super(BaseButton, self).setText(text)

    def actions(self, mouse_menu=Qt.LeftButton):
        """
        Overrides base actions function to returns the actions of mouse button.

        :param Qt.Button mouse_menu: mouse button.
        :return: list of actions.
        :rtype: list(QAction)(
        """

        return self._click_menu[mouse_menu].actions()[2:]   # ignore search widget and separator

    def setMenu(self, menu, mouse_button=Qt.LeftButton):
        """
        Overrides base setMenu function to set the menu based on mouse button.

        :param QMenu menu: menu to set
        :param Qt.Button mouse_button: mouse button.
        """

        self._click_menu[mouse_button] = menu

    def setWindowTitle(self, window_title, mouse_menu=Qt.LeftButton):
        """
        Overrides base setWindowTitle function to set the weindow title of the menu, if its get teared off.

        :param str window_title: window title
        :param Qt.Button mouse_menu: menu button
        """

        menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        menu.setWindowTitle(window_title)

    def menu(self, mouse_menu=Qt.LeftButton, searchable=False, auto_create=True):
        """
        Overrides base menu function to get menu depending on the mouse button pressed.

        :param Qt.Button mouse_menu: mouse button.
        :param bool searchable: whether menu is searchable.
        :param bool auto_create: whether to auto create menu if it does not exist yet.
        :return:  requested menu.
        :rtype: QMenu
        """

        if self._click_menu[mouse_menu] is None and auto_create:
            self._click_menu[mouse_menu] = BaseButton.BaseMenuButtonMenu(title='Menu Button', parent=self)
            self._click_menu[mouse_menu].setObjectName('menuButton')
            self._click_menu[mouse_menu].triggered.connect(lambda action: self.actionTriggered.emit(action, mouse_menu))
            self._click_menu[mouse_menu].triggered.connect(partial(self._on_menu_changed, mouse_menu))
            if not searchable:
                self._click_menu[mouse_menu].set_search_visible(False)

        return self._click_menu[mouse_menu]

    def addAction(self, name, mouse_menu=Qt.LeftButton, connect=None, checkable=False, checked=True, action=None,
                  action_icon=None, data=None, icon_text=None, icon_color=None, icon_size=16, tooltip=None):
        """
        Adds a new menu item through an action.

        :param str name: text for the new menu item.
        :param Qt.LeftButton or Qt.RightButton or Qt.MidButton mouse_menu: mouse button.
        :param callable or None connect: function to connect when the menu item is pressed.
        :param bool checkable: whether or not menu item is checkable.
        :param bool checked: if checkable is True, whether or not menu item is checked by default.
        :param QAction or None action: if given this is the action will be added directly without any extra steps.
        :param QIcon action_icon: icon for the menu item.
        :param object data: custom data to store within the action.
        :param str icon_text: text for the icon.
        :param tuple(int, int, int) icon_color: color of the menu item in 0-255 range.
        :param int icon_size: size of the icon.
        :param str tooltip: new menu item tooltip.
        :return: newly created action.
        :rtype: SearchableTaggedAction
        """

        found_menu = self.menu(mouse_menu, searchable=False)

        if action is not None:
            found_menu.addAction(action)
            return

        # convert string to tags, so they are easily searchable
        tags = list()
        tags += name.split(' ')
        tags += [tag.lower() for tag in name.split(' ')]

        new_action = menus.SearchableTaggedAction(name, parent=found_menu)
        new_action.setCheckable(checkable)
        new_action.setChecked(checked)
        new_action.tags = set(tags)
        new_action.setData(data)

        if tooltip:
            new_action.setToolTip(tooltip)
        found_menu.addAction(new_action)

        if action_icon is not None:
            if isinstance(action_icon, QIcon):
                new_action.setIcon(action_icon)
                new_action.setIconText(icon_text or '')
            elif helpers.is_string(action_icon):
                new_action.setIconText(action_icon or icon_text or None)
                new_action.setIcon(icon.colorize_layered_icon(
                    resources.icon(action_icon), colors=[icon_color], size=dpi.dpi_scale(icon_size)))

        if connect is not None:
            if checkable:
                new_action.triggered.connect(partial(connect, new_action))
            else:
                new_action.triggered.connect(connect)

        return new_action

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def default(self):
        """
        Sets button to default style.

        :return: button instance.
        :rtype: BaseButton
        """
        self.theme_type = self.Types.DEFAULT

        return self

    def primary(self):
        """
        Sets button to primary style.

        :return: button instance.
        :rtype: BaseButton
        """

        self.theme_type = self.Types.PRIMARY

        return self

    def success(self):
        """
        Sets button to success style.

        :return: button instance.
        :rtype: BaseButton
        """

        self.theme_type = self.Types.SUCCESS

        return self

    def warning(self):
        """
        Sets button to warning style.

        :return: button instance.
        :rtype: BaseButton
        """

        self.theme_type = self.Types.WARNING

        return self

    def danger(self):
        """
        Sets button to danger style.

        :return: button instance.
        :rtype: BaseButton
        """

        self.theme_type = self.Types.DANGER

        return self

    def tiny(self):
        """
        Sets button to tiny size.

        :return: button instance.
        :rtype: BaseButton
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.TINY if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets button to small size.

        :return: button instance.
        :rtype: BaseButton
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.SMALL if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets button to medium size.

        :return: button instance.
        :rtype: BaseButton
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.MEDIUM if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets button to large size.

        :return: button instance.
        :rtype: BaseButton
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.LARGE if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets button to huge size.

        :return: button instance.
        :rtype: BaseButton
        """

        widget_theme = self.theme_data()
        self.theme_size = widget_theme.HUGE if widget_theme else theme.Theme.Sizes.HUGE

        return self

    def add_separator(self, mouse_menu=Qt.LeftButton):
        """
        Adds a new separator into the menu.

        :param Qt.Button mouse_menu: mouse button.
        """

        found_menu = self.menu(mouse_menu)
        found_menu.addSeparator()

    def set_tearoff_enabled(self, mouse_menu=Qt.LeftButton, tearoff=True):
        """
        Sets whether tear off is enabled for a specific menu.

        :param Qt.Button mouse_menu: mouse button.
        :param flag tearoff: True to enable tearoff; False otherwise.
        """

        found_menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        found_menu.setTearOffEnabled(tearoff)

    def menu_pos(self, align=Qt.AlignLeft, widget=None):
        """
        Returns the menu position based on the current position and perimeter.

        :param Qt.AlignLeft or Qt.AlignRight align: align the menu left or right.
        :param QWidget widget: widget used to calculate the width based off. Usually it is the menu itself.
        :return: position of the menu.
        :rtype: QPoint
        """

        pos = 0

        if align == Qt.AlignLeft:
            point = self.rect().bottomLeft() - QPoint(0, -self._menu_padding)
            pos = self.mapToGlobal(point)
        elif align == Qt.AlignRight:
            point = self.rect().bottomRight() - QPoint(widget.sizeHint().width(), -self._menu_padding)
            pos = self.mapToGlobal(point)

        return pos

    def index(self, name, mouse_menu=Qt.LeftButton):
        """
        Returns the index of the menu item or actoin name.

        :param str name: name of menu item.
        :param Qt.Button mouse_menu: mouse button.
        :return: index of the menu.
        :rtype: int
        """

        return self.menu(mouse_menu).index(name)

    def is_searchable(self, mouse_menu=Qt.LeftButton):
        """
        Returns whether the button menu is searchable.

        :param Qt.Button mouse_menu: mouse button
        :return: True if the given mouse menu is searchable; False otherwise.
        :rtype: bool
        """

        if self._click_menu[mouse_menu] is not None:
            return self._click_menu[mouse_menu].search_visible()

        return self._menu_searchable[mouse_menu]

    def set_searchable(self, mouse_menu=Qt.LeftButton, searchable=True):
        """
        Sets whether given menu is searchable.

        :param Qt.Button mouse_menu: mouse button.
        :param bool searchable: True to make menu searchable; False otherwise.
        """

        self._menu_searchable[mouse_menu] = searchable

        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].set_search_visibility(searchable)

    def clear_menu(self, mouse_menu=Qt.LeftButton):
        """
        Clears all the menu items of the specified menu.

        :param Qt.LeftButton or Qt.MidButton or Qt.RightButton mouse_menu: mouse button.
        """

        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].clear()

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _mouse_single_click_action(self, button):
        """
        Internal function that is called when a single click is triggered.

        :param Qt.Button button: pressed button.
        """

        if self._last_click == self.SINGLE_CLICK or self._double_click_enabled is False:
            if button == Qt.LeftButton:
                self.leftClicked.emit()
                return True
            elif button == Qt.MidButton:
                self.middleClicked.emit()
                return True
            elif button == Qt.RightButton:
                self.rightClicked.emit()
                return True
            return False

    def _mouse_double_click_action(self, button):
        """
        Internal function that is called when a double click is triggered.

        :param Qt.Button button: pressed button
        """

        if button == Qt.LeftButton:
            self.leftDoubleClicked.emit()
        elif button == Qt.MiddleButton:
            self.middleDoubleClicked.emit()
        elif button == Qt.RightButton:
            self.rightDoubleClicked.emit()

    def _about_to_show(self, mouse_button):
        """
        Internal function that is called when context menu is about to show

        :param Qt.Button mouse_button: mouse button.
        """

        if mouse_button == Qt.LeftButton:
            self.menuAboutToShow.emit()
        elif mouse_button == Qt.MiddleButton:
            self.middleMenuAboutToShow.emit()
        elif mouse_button == Qt.RightButton:
            self.rightMenuAboutToShow.emit()

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_context_menu(self, mouse_button):
        """
        Internal callback function that shows the context menu depending on the mouse button.
        :param Qt.button mouse_button: mouse button
        """

        menu = self._click_menu[mouse_button]
        if menu is not None and self._menu_active[mouse_button]:
            self._about_to_show(mouse_button)
            pos = self.menu_pos(widget=menu, align=self._menu_align)
            menu.exec_(pos)
            try:
                menu._search_edit.setFocus()
            except Exception:
                pass

    def _on_menu_changed(self, mouse_button, *args, **kwargs):
        if mouse_button == Qt.LeftButton:
            self.menuChanged.emit()
        elif mouse_button == Qt.MiddleButton:
            self.middleMenuChanged.emit()
        elif mouse_button == Qt.RightButton:
            self.rightMenuChanged.emit()


@theme.mixin
class BasePushButton(BaseButton):
    def __init__(self, *args, **kwargs):
        super(BasePushButton, self).__init__(*args, **kwargs)

        qtutils.set_stylesheet_object_name(self, 'DefaultButton')


@theme.mixin
class BaseToolButton(QToolButton, AbstractButton):
    def __init__(self, icon=None, tooltip=None, parent=None):
        super(BaseToolButton, self).__init__(parent=parent)

        self._image = icon
        self._image_theme = None
        self._size = self.theme_default_size()

        self.setAutoExclusive(False)
        self.setAutoRaise(True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        if tooltip:
            self.setToolTip(tooltip)

        self._polish_icon()

        self.toggled.connect(self._polish_icon)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the button height size.

        :return: button height size.
        :rtype: int
        """

        return self._size

    def _set_size(self, value):
        """
        Sets button height size.

        :param int value: button height size
        """

        self._size = value
        self.style().polish(self)
        if self.toolButtonStyle() == Qt.ToolButtonIconOnly:
            self.setFixedSize(self._size, self._size)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def enterEvent(self, event):
        """
        Overrides base enterEvent function to automatically update icon color based on theme accent color.

        :param QEvent event: Qt event.
        """

        if self._image:
            theme_data = self.theme_data()
            if theme_data:
                accent_color = theme_data.ACCENT_COLOR
                if self._image_theme:
                    self.setIcon(resources.icon(self._image, theme=self._image_theme, color=accent_color))
                else:
                    self.setIcon(resources.icon(self._image, color=accent_color))
        return super(BaseToolButton, self).enterEvent(event)

    def leaveEvent(self, event):
        """
        Overrides base leaveEvent function to automatically update icon color based on theme accent color.

        :param QEvent event: Qt event.
        """

        self._polish_icon()
        return super(BaseToolButton, self).leaveEvent(event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def image(self, name, **kwargs):
        """
        Sets the name of the image to use by the tool button.

        :param str name: name of the icon to use.
        :return: itself instance.
        :rtype: BaseToolButton
        """

        self._image = name
        self._image_theme = kwargs.get('theme', None)
        self._polish_icon(**kwargs)

        return self

    def tiny(self):
        """
        Sets tool button to tiny size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        theme_data = self.theme_data()
        self.theme_size = theme_data.TINY if theme_data else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets tool button to small size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        theme_data = self.theme_data()
        self.theme_size = theme_data.SMALL if theme_data else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets tool button to medium size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        theme_data = self.theme_data()
        self.theme_size = theme_data.MEDIUM if theme_data else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets tool button to large size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        theme_data = self.theme_data()
        self.theme_size = theme_data.LARGE if theme_data else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets tool button to huge size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        theme_data = self.theme_data()
        self.theme_size = theme_data.HUGE if theme_data else theme.Theme.Sizes.HUGE

        return self

    def icon_only(self):
        """
        Sets tool button style to icon only.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(self._size, self._size)

        return self

    def text_only(self):
        """
        Sets tool button style to text only.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonTextOnly)

        return self

    def text_beside_icon(self):
        """
        Sets tool button style to text beside icon.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        return self

    def text_under_icon(self):
        """
        Sets tool button style to text under icon.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        return self

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _polish_icon(self, checked=None, **kwargs):
        if self._image:
            image_theme = kwargs.get('theme', self._image_theme)
            if image_theme:
                kwargs['theme'] = image_theme
            image = resources.icon(self._image, **kwargs) if helpers.is_string(self._image) else self._image
            if image and not image.isNull():
                self.setIcon(image)


@theme.mixin
class BaseRadioButton(QRadioButton, object):
    def __init__(self, *args, **kwargs):
        super(BaseRadioButton, self).__init__(*args, **kwargs)


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

        super(ButtonIcons, self).setIconSize(qtutils.size_by_dpi(size))
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
            icons=self.icon, size=self.iconSize().width(), icon_scaling=self.iconScaling,
            tint_composition=self.tintComposition, colors=self.iconColors, grayscale=self.grayscale
        )

        self.hoverIcon = icon.colorize_layered_icon(
            icons=self.icon, size=self.iconSize().width(), icon_scaling=self.iconScaling,
            tint_composition=self.tintComposition, tint_color=hover_color, grayscale=self.grayscale
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
                        widget=action, icon_size=qtutils.dpi_scale(40), popup_release=self._tt_key)
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
        return super(BaseMenuButton, self).setFixedHeight(qtutils.dpi_scale(height))

    def setFixedWidth(self, width):
        return super(BaseMenuButton, self).setFixedWidth(qtutils.dpi_scale(width))

    def setFixedSize(self, size):
        super(BaseMenuButton, self).setFixedSize(qtutils.dpi_scale(size))

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
        Overrides base addAction function
        Adds a new menu item through an action
        :param name: str, name of the menu item
        :param mouse_menu: button that will launch menu (Qt.LeftButton or Qt.MidButton or Qt.RightButton)
        :param connect: fn, function to launch when the item is pressed
        :param checkable: bool, Whether or not this menu is checkable
        :param checked: bool, Whether or not this menu is checked by default
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

        new_action = menu.SearchableTaggedAction(label=name, parent=new_menu)
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
                    icon.colorize_layered_icon(action_icon, colors=[icon_color], size=qtutils.dpi_scale(icon_size)))

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


@theme.mixin
class IconMenuButton(BaseButton):
    def __init__(self, icon=None, icon_hover=None, double_click_enabled=False, color=None, tint_color=None,
                 menu_name='', switch_icon_on_click=False, theme_updates=True, parent=None):
        super(IconMenuButton, self).__init__(
            icon=icon, icon_hover=icon_hover, double_click_enabled=double_click_enabled, theme_updates=theme_updates,
            parent=parent)

        self._tint_color = tint_color
        self._icon_color = color or (255, 255, 255)
        self._current_text = menu_name
        self._switch_icon = switch_icon_on_click

        self.setup_ui()

        self.actionTriggered.connect(self._on_menu_item_clicked)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def text(self):
        """
        Overrides base text function.

        :return: menu name.
        :rtype: str
        """

        return self._current_text

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def setup_ui(self):
        """
        Setup icon menu button UI.
        """

        for found_menu in self._click_menu.values():
            if found_menu is not None:
                found_menu.setToolTipsVisible(True)

        self.menu_align = Qt.AlignRight

    def get_current_text(self):
        """
        Returns the current selected menu name.

        :return: current menu name.
        :rtype: str
        """

        return self._current_text

    def get_current_action(self, mouse_menu=Qt.LeftButton):
        """
        Returns current action.

        :param Qt.Button mouse_menu: mouse button.
        :return: curreent action.
        :rtype: QAction
        """

        for action in self.actions(mouse_menu):
            if action.text() == self._current_text:
                return action

        return None

    def get_current_index(self, mouse_menu=Qt.LeftButton):
        """
        Returns the current selected menu index.

        :param Qt.Button mouse_menu: mouse button.
        :return: current index menu item.
        :rtype: int
        """

        return self.index(self.get_current_text(), mouse_menu)

    def set_menu_name(self, name, mouse_menu=Qt.LeftButton):
        """
        Sets the main icon and menu states by the menu item name.

        :param str name: name of the menu item to set.
        :param Qt.Button mouse_menu: mouse button.
        """

        for i, action in enumerate(self.actions(mouse_menu)):
            if action.text() == name:
                self._current_text = action.text()
                if self._switch_icon:
                    icon_name = action.iconText()
                    action_icon = resources.icon(icon_name)
                    self.set_icon(action_icon, colors=self._icon_color)
                break

    def action_connect_list(self, actions, mouse_menu=Qt.LeftButton):
        """
        Creates the entire menu with the info contained within the actions list.

        :param list(tuple(str, str)) actions: list of actions. Eg: [('icon1', 'menuName1'), (...), ...]
        :param Qt.MouseClick mouse_menu: button that will open the menu.
        """

        for action in actions:
            self.addAction(action[1], mouse_menu=mouse_menu, action_icon=action[0])
        first_name = actions[0][1]
        self.set_menu_name(first_name)

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_menu_item_clicked(self, action, mouse_menu):
        """
        Internal callback function that is called each time a menu item is clicked by the user.

        :param QAction action: action clicked
        :param Qt.Button mouse_menu: mouse button.
        """

        self.set_menu_name(action.text())


class HoverButton(QPushButton, object):
    """
    Button widget that allows to setup different icons during mouse interaction
    """

    def __init__(self, icon=None, hover_icon=None, pressed_icon=None, parent=None):
        super(HoverButton, self).__init__(parent)

        self._idle_icon = icon
        self._hover_icon = hover_icon
        self._pressed_icon = pressed_icon
        self._mouse_pressed = False
        self._higlight_offset = 40

        self.setIcon(self._idle_icon)

    def enterEvent(self, event):
        if self._hover_icon is not None:
            self.setIcon(self._hover_icon)
        super(HoverButton, self).enterEvent(event)

    def leaveEvent(self, event):
        if self._idle_icon is not None:
            self.setIcon(self._idle_icon)
        super(HoverButton, self).leaveEvent(event)

    def mousePressEvent(self, event):
        if self.rect().contains(event.pos()):
            if self._pressed_icon:
                self.setIcon(self._pressed_icon)
            self._mouse_pressed = True
        super(HoverButton, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.rect().contains(event.pos()):
            self.setIcon(self._idle_icon)
        else:
            if self._mouse_pressed:
                if self._pressed_icon:
                    self.setIcon(self._pressed_icon)

        super(HoverButton, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rect().contains(event.pos()):
            self.setIcon(self._hover_icon)
        else:
            self.setIcon(self._idle_icon)
        self._mouse_pressed = False
        super(HoverButton, self).mouseReleaseEvent(event)


class ColorButton(QPushButton, object):

    colorChanged = Signal()

    def __init__(self, color_r=1.0, color_g=0.0, color_b=0.0, parent=None, **kwargs):
        super(ColorButton, self).__init__(parent=parent, **kwargs)
        self._color = QColor.fromRgbF(color_r, color_g, color_b)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self._update_color()

        self.clicked.connect(self.show_color_editor)

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = color
        self._update_color()

    def show_color_editor(self):
        if dcc.is_maya():
            import maya.cmds as cmds
            cmds.colorEditor(rgbValue=(self._color.redF(), self._color.greenF(), self._color.blueF()))
            if not cmds.colorEditor(query=True, result=True):
                return
            new_color = cmds.colorEditor(query=True, rgbValue=True)
            self.color = QColor.fromRgbF(new_color[0], new_color[1], new_color[2])
            self.colorChanged.emit()
        else:
            raise RuntimeError('Code Editor is not available for DCC: {}'.format(dcc.get_name()))

    def _update_color(self):
        self.setStyleSheet(
            'background-color:rgb({0},{1},{2});'.format(
                self._color.redF() * 255, self._color.greenF() * 255, self._color.blueF() * 255))

    color = property(get_color, set_color)


class RoundButton(QPushButton, dpi.DPIScaling):
    """
    Custom round button. It can be rendered in two different ways:
        1. Mask: will cut the button into a circle. Allow also stylesheets. It is pixelated when drawing it out.
        2. Stylesheet: creates a smooth circle button without pixelation. For rectangle buttons it will not be round
            and also the user will not be able to user their own stylesheet.
    """

    class RenderingMethod(object):
        MASK = 0
        STYLESHEET = 1

    def __init__(self, text=None, icon=None, method=RenderingMethod.STYLESHEET, tooltip='', parent=None):
        super(RoundButton, self).__init__(text=text, icon=icon, parent=parent)

        self._method = method
        self._custom_style = ''
        self.setToolTip(tooltip)

        self._update_button()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def resizeEvent(self, event):
        """
        Overrides base QPushButton resizeEvent function.

        :param QEvent event: Qt resize event.
        """

        self._update_button()
        super(RoundButton, self).resizeEvent(event)

    def setStyleSheet(self, text):
        """
        Overrides base QPushButton setStyleSheet function.

        :param str text: stylesheet text to apply.
        """

        if self._method == self.RenderingMethod.STYLESHEET:
            self._custom_style = text
            self._update_button()
        else:
            super(RoundButton, self).setStyleSheet(text)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_method(self, method):
        """
        Sets the rendering method to use.
            - Mask: pixelated edges but can set custom stylesheets.
            - Stylesheet: Smooth edges but cannot set custom stylesheets.
        :param RoundButton.RenderingMethod method: render method to use.
        """

        self._method = method
        self._update_button()

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_round_style(self):
        """
        Internal function that returns custom rounded stylesheet string.

        :return: rounded stylesheet string.
        :rtype: str
        """

        radius = (min(self.rect().width() * 0.5, self.rect().height() * 0.5) - 1.0)
        return 'border-radius: {}px;'.format(radius)

    def _update_button(self):
        """
        Internal function that updates the button drawing.
        """

        if self._method == self.RenderingMethod.MASK:
            self.setMask(QRegion(self.rect(), QRegion.Ellipse))
        else:
            super(RoundButton, self).setStyleSheet(self._get_round_style() + self._custom_style)


class ShadowedButton(BaseButton):

    _MENU_INDICATOR_ICON = 'menu_indicator'

    def __init__(self, text='', shadow_height=4, force_upper=False, tooltip='', icon_color_theme=None,
                 theme_updates=True, parent=None):

        self._text_label = None
        self._force_upper = force_upper
        self._mouse_entered = True
        self._icon_pixmap = None
        self._icon_hovered_pixmap = None
        self._icon_pressed_pixmap = None
        self._is_menu = True
        self._icon_size = dpi.size_by_dpi(QSize(16, 16))

        super(ShadowedButton, self).__init__(
            icon_color_theme=icon_color_theme, theme_updates=theme_updates, parent=parent)

        self.setToolTip(tooltip)

        self.setup_ui()

        self.setText(text)
        self.set_shadow_height(shadow_height)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def is_menu(self):
        return self._is_menu

    @is_menu.setter
    def is_menu(self, flag):
        self._is_menu = flag

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def setFixedHeight(self, height):
        """
        Overrides base QPushButton setFixedHeight function.

        :param int height: button height.
        """

        self.update_image_widget(height)
        super(ShadowedButton, self).setFixedHeight(height)

    def setFixedSize(self, size):
        """
        Overrides base QPushButton setFixedSize function.

        :param QSize size: button size.
        """

        self.update_image_widget(size.height())
        super(ShadowedButton, self).setFixedSize(size)

    def setText(self, text):
        """
        Overrides base QPushButton setText function.

        :param str text: button text.
        """

        if not self._text_label:
            return
        if self._force_upper and text is not None:
            text = text.upper()

        self._text_label.setText(text)

    def setIconSize(self, size):
        """
        Overrides base QPushButton setIconSize function.

        :param QSize size: icon size.
        """

        self._icon_size = dpi.size_by_dpi(size)
        self._image_widget.setFixedSize(self._icon_size)

    def enterEvent(self, event):
        """
        Overrides base QPushButton enterEvent function.

        :param QEvent event: Qt enter event.
        """

        self._mouse_entered = True
        qtutils.set_stylesheet_object_name(self, '')
        qtutils.set_stylesheet_object_name(self._shadow, 'buttonShadowHover')
        qtutils.set_stylesheet_object_name(self._image_widget, 'shadowedImageHover')
        qtutils.set_stylesheet_object_name(self._text_label, 'shadowedLabelHover')
        self._image_widget.setPixmap(self._icon_hovered_pixmap)

    def leaveEvent(self, event):
        """
        Overrides base QPushButton leaveEvent function.

        :param QEvent event: Qt leave event.
        """

        self._mouse_entered = False
        qtutils.set_stylesheet_object_name(self, '')
        qtutils.set_stylesheet_object_name(self._shadow, '')
        qtutils.set_stylesheet_object_name(self._image_widget, '')
        qtutils.set_stylesheet_object_name(self._text_label, '')
        self._image_widget.setPixmap(self._icon_pixmap)

    def mousePressEvent(self, event):
        """
        Overrides base QPushButton mousePressEvent function.

        :param QEvent event: Qt mouse press event.
        """

        qtutils.set_stylesheet_object_name(self, 'shadowedButtonPressed')
        qtutils.set_stylesheet_object_name(self._shadow, 'buttonShadowPressed')
        qtutils.set_stylesheet_object_name(self._image_widget, 'shadowedImagePressed')
        qtutils.set_stylesheet_object_name(self._text_label, 'shadowedLabelPressed')
        self._image_widget.setPixmap(self._icon_pressed_pixmap)

        return super(ShadowedButton, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Overrides base QPushButton mouseReleaseEvent function.

        :param QEvent event: Qt mouse release event.
        """

        # if mouse still entered while mouse released then set it back to hovered style
        if self._mouse_entered:
            self.enterEvent(event)

        return super(ShadowedButton, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        Overrides base QPushButton mouseDoubleClickEvent function.

        :param QEvent event: Qt mouse double click event.
        """

        event.ignore()
        return super(ShadowedButton, self).mouseDoubleClickEvent(event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def setup_ui(self):
        """
        Initializes shadow button UI.
        """

        self.main_layout = layouts.GridLayout(spacing=0)
        self.setLayout(self.main_layout)

        self._image_widget = ShadowedButtonImage(parent=self)
        self._text_label = labels.BaseLabel(parent=self)
        self._shadow = ShadowedButtonShadow(parent=self)

        self._image_widget.setFixedHeight(self.sizeHint().height())
        self._image_widget.setAlignment(Qt.AlignCenter)
        self._text_label.setAlignment(Qt.AlignCenter)
        self._spacing_widget = QWidget(parent=self)

        self.main_layout.addWidget(self._image_widget, 0, 0, 1, 1)
        self.main_layout.addWidget(self._text_label, 0, 1, 1, 1)
        self.main_layout.addWidget(self._spacing_widget, 0, 2, 1, 1)
        self.main_layout.addWidget(self._shadow, 1, 0, 1, 3)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def set_force_upper(self, flag):
        """
        Sets whether or not button text should appear as upper case.

        :param bool flag: whether or not to force text upper case.
        """

        self._force_upper = flag

    def set_shadow_height(self, height):
        """
        Sets the shadow height in pixels.

        :param int height: shadow height (in pixels).
        """

        self._shadow.setFixedHeight(height)

    def set_icon(self, icons, colors=None, hover_colors=None, size=None, pressed_colors=None, scaling=None):
        """
        Set the icon of the button.

        :param QIcon or str or list(QIcon) or list(str) icons: button icon.
        :param colors:
        :param int size: icon size.
        :param list(float, float) scaling: icon scaling.
        """

        if size is not None:
            self.setIconSize(QSize(size, size))

        hover_colors = hover_colors or colors
        pressed_colors = pressed_colors or colors

        colors = [colors]
        hover_color = [hover_colors]
        pressed_color = [pressed_colors]

        self._icon_names = icons

        if self._is_menu and helpers.is_string(icons):
            self._icon_names = [icons, self._MENU_INDICATOR_ICON]
            colors += colors
            hover_color += hover_color
            pressed_color += pressed_color

        new_size = self._icon_size.width()
        self._icon_pixmap = resources.colorize_layered_icon(
            self._icon_names, colors=colors, size=new_size, scaling=scaling).pixmap(QSize(new_size, new_size))
        self._icon_hovered_pixmap = resources.colorize_layered_icon(
            self._icon_names, colors=hover_color, size=new_size, scaling=scaling).pixmap(QSize(new_size, new_size))
        self._icon_pressed_pixmap = resources.colorize_layered_icon(
            self._icon_names, colors=pressed_color, size=new_size, scaling=scaling).pixmap(QSize(new_size, new_size))

        self._image_widget.setPixmap(self._icon_pixmap)

    def update_image_widget(self, new_height):
        """
        Updates button to make sure widget is always square.

        :param int new_height: new height of the wigdet to update to.
        """

        self._image_widget.setFixedSize(QSize(new_height, new_height))
        self._spacing_widget.setFixedWidth(int(dpi.dpi_scale(new_height) * 0.5))


class ShadowedButtonImage(labels.BaseLabel):
    """
    stylesheet purposes
    """

    pass


class ShadowedButtonShadow(base.BaseFrame):
    """
    stylesheet purposes
    """

    pass


class FloatingButton(QDialog):
    """
    Custom floating button that can be placed anywhere on the screen. Note that it does not float outside the parent,
    so make sure the button is within the parent bounds to be visible.
    """

    clicked = Signal()

    def __init__(self, size=24, parent=None):
        super(FloatingButton, self).__init__(parent=parent)

        self._button = QPushButton(parent=self)
        self.main_layout = layouts.horizontal_layout(self)
        self.setLayout(self.main_layout)
        self.resize(dpi.dpi_scale(size), dpi.dpi_scale(size))
        self._alignment = Qt.AlignBottom

        self.setup_ui()
        self.setup_signals()
        self.setStyleSheet("background-color: transparent;")

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def setup_ui(self):
        """
        Setup floating button UI.
        """

        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self._button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.main_layout.addWidget(self._button)
        self.show()

    def setup_signals(self):
        """
        Setups floating button signals.
        """

        self._button.clicked.connect(self.clicked.emit)

    def set_alignment(self, align):
        """
        Sets the alignment of the button

        :param Qt.Alignment align: button alignment.
        """

        self._alignment = align

    def move(self, x, y):
        """
        Moves the floating button based on the alignment.

        :param int x: X coordinates.
        :param int y: Y coordinates.
        """

        width = self.rect().width()
        height = self.rect().height()

        if self.alignment == Qt.AlignTop:
            super(FloatingButton, self).move(x+(width*0.5), y)
        elif self.alignment == Qt.AlignRight:
            super(FloatingButton, self).move(x-width, y-(height*0.5))
        elif self.alignment == Qt.AlignBottom:
            super(FloatingButton, self).move(x, y-height)
        elif self.alignment == Qt.AlignLeft:
            super(FloatingButton, self).move(x, y-(height*0.5))


class OkCancelButtons(QWidget):

    okPressed = Signal()
    cancelPressed = Signal()

    def __init__(self, ok_text='Ok', cancel_text='Cancel', parent=None):
        super(OkCancelButtons, self).__init__(parent=parent)

        self.main_layout = layouts.HorizontalLayout()
        self.setLayout(self.main_layout)
        self._ok_button = BasePushButton(ok_text, parent=self)
        self._cancel_button = BasePushButton(cancel_text, parent=self)
        self.main_layout.addWidget(self._ok_button)
        self.main_layout.addWidget(self._cancel_button)

        self._ok_button.clicked.connect(self.okPressed.emit)
        self._cancel_button.clicked.connect(self.cancelPressed.emit)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def ok_button(self):
        return self._ok_button

    @property
    def cancel_button(self):
        return self._cancel_button


class BaseButtonGroup(base.BaseWidget, object):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        self._orientation = 'horizontal' if orientation == Qt.Horizontal else 'vertical'
        super(BaseButtonGroup, self).__init__(parent=parent)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def get_main_layout(self):
        return layouts.BoxLayout(orientation=self._orientation, spacing=0, margins=(0, 0, 0, 0))

    def setup_ui(self):
        super(BaseButtonGroup, self).setup_ui()
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._button_group = QButtonGroup()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    @decorators.abstractmethod
    def create_button(self, data_dict):
        """
        Must be implemented in custom button groups
        Creates a new button for this group.

        :param dict data_dict: button data.
        :return: newly created button instance.
        :rtype: QPushButton
        """

        raise NotImplementedError(
            'Function create_button for class "{}" is not implemented!'.format(self.__class__.__name__))

    def get_button_group(self):
        """
        Returns button group internal object.

        :return: attached button group.
        :rtype: QButtonGroup
        """

        return self._button_group

    def clear(self):
        """
        Clears all buttons contained in this group.
        """

        for btn in self._button_group.buttons():
            self._button_group.removeButton(btn)
            self.main_layout.removeWidget(btn)
            btn.setVisible(False)
            btn.deleteLater()

    def add_button(self, data_dict, index=None):
        """
        Adds a new button to this group.

        :param dict data_dict: button data to add.
        :param int or None index: index of the button within the group.
        :return: newly added button.
        :rtype: QPushButton
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
        Empties group and add all buttons given in the list of buttons.

        :param list(dict) button_list: list of button data to set.
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

        self._type = BaseButton.Types.PRIMARY
        self._size = theme.Theme.default_size
        self._button_group.setExclusive(True)
        self.set_spacing(1)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

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

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def create_button(self, data_dict):
        """
        Implements BaseButtonGroup create_button abstract function
        :param data_dict:
        :return:
        """

        new_btn = BasePushButton()
        # new_btn = StyleBaseButton()
        # new_btn.size = data_dict.get('size', self._size)
        # new_btn.type = data_dict.get('type', self._type)

        return new_btn


class RadioButtonGroup(BaseButtonGroup, object):
    checkedChanged = Signal(int)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(RadioButtonGroup, self).__init__(orientation=orientation, parent=parent)

        self._button_group.setExclusive(True)
        self.set_spacing(15)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def setup_signals(self):
        self._button_group.buttonClicked.connect(self.checkedChanged)

    def create_button(self, data_dict):
        """
        Implements BaseButtonGroup create_button abstract function
        :param data_dict:
        :return:
        """

        return BaseRadioButton()

    def _get_checked(self):
        return self._button_group.checkedId()

    def _set_checked(self, value):
        btn = self._button_group.button(value)
        if btn:
            btn.setChecked(True)
            self.checkedChanged.emit(value)

    checked = Property(int, _get_checked, _set_checked, notify=checkedChanged)


class FadeButton(QToolButton):
    def __init__(self, parent=None):
        super(FadeButton, self).__init__(parent=parent)

        self._width = 20
        self._height = 20
        self._opacity = 0.3
        self._end_opacity = 0.7
        self._in_anim_duration = 300
        self._out_anim_duration = 800
        self._active_button = None

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self.setAutoFillBackground(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.set_opacity(self._opacity)

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def active_button(self):
        return self._active_button

    @active_button.setter
    def active_button(self, flag):
        self._active_button = flag

    @property
    def opacity_effect(self):
        return self._opacity_effect

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def enterEvent(self, event):
        if self._active_button is False:
            animation.fade_opacity_effect(
                start='current', end=self._end_opacity, duration=self._in_anim_duration,
                target_object=self._opacity_effect)

    def leaveEvent(self, event):
        if self._active_button is False:
            animation.fade_opacity_effect(
                start='current', end=self._opacity, duration=self._out_anim_duration,
                target_object=self._opacity_effect)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def set_opacity(self, opacity):
        """
        Sets button opacity.

        :param float opacity: opacity value between 0.0 and 1.0
        """

        self._opacity_effect.setOpacity(opacity)
        self._opacity = opacity

    def set_size(self, width, height):
        """
        Sets icon size.

        :param int width: button width.
        :param int height: button height.
        """

        self.setIconSize(QSize(width, height))
        self._width = width
        self._height = height
