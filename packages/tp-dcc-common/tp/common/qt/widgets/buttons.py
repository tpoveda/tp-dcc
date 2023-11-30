from __future__ import annotations

from functools import partial
from typing import Tuple, List, Dict, Iterable, Callable, Any

from overrides import override
from Qt.QtCore import Qt, Signal, Property, QPoint, QSize, QTimer, QEvent
from Qt.QtWidgets import (
    QSizePolicy, QWidget, QAbstractButton, QPushButton, QAction, QMenu, QLabel, QFrame, QGridLayout, QToolButton
)
from Qt.QtGui import (
    QCursor, QFontMetrics, QColor, QIcon, QPainter, QMouseEvent, QKeyEvent, QResizeEvent, QPixmap, QRegion
)

from tp.core import log
from tp.preferences.interfaces import core as core_interfaces
from tp.common.python import helpers
from tp.common.resources import icon, api as resources
from tp.common.qt import consts, dpi, qtutils, mixin
from tp.common.qt.widgets import layouts, labels, menus

# cached theme preference
THEME_PREFERENCE = None

logger = log.tpLogger


def styled_button(
        text: str = '', icon: str | QIcon | None = None, icon_size: int = 16,
        icon_color: Tuple[int, int, int] or None =None, icon_hover_color: Tuple[int, int, int] | None = None,
        overlay_icon_color: Tuple[int, int, int] or None = None, overlay_icon: str | QIcon | None = None,
        icon_color_theme: str | None = None, min_width: int | None = None, max_width: int | None = None,
        min_height: int | None = None, max_height: int | None = None, width: int | None = None,
        height: int | None = None, style: int = consts.ButtonStyles.DEFAULT, tooltip: str = '',
        theme_updates: bool = True, checkable: bool = False, checked: bool = False, force_upper: bool = False,
        button_width: int | None = None, button_height: int | None = None,
        parent: QWidget | None = None) -> QPushButton | BaseButton | ShadowedButton | RoundButton | LabelSmallButton:
    """
    Creates a new button with the given options.

    Style 0: Default button with optional text or icon.
    Style 1: Default button with transparent background.
    Style 2: Button with shadow underline (icon in a colored box).
    Style 3: Rounded button with a background color and a colored icon.
    Style 4: Default style using standard Qt PushButton.
    Style 5: Regular Qt label with a small button beside.

    :param str text: button text.
    :param str or QIcon icon: icon name or QIcon instance.
    :param int icon_size: size of the icon in pixels.
    :param tuple(int, int, int) icon_color: icon color in 0 to 255 range.
    :param tuple(int, int, int) icon_hover_color: icon hover color in 0 to 255 range.
    :param tuple(int, int, int) overlay_icon_color: color of the overlay image icon.
    :param str or QIcon overlay_icon: the name of the icon image that will be overlayed on top of the original icon.
    :param str icon_color_theme: color attribute that should be applied from current applied theme.
    :param int min_width: minimum width of the button in pixels.
    :param int max_width: maximum width of the button in pixels.
    :param int min_height: minimum height of the button in pixels.
    :param int max_height: maximum height of the button in pixels.
    :param int width: fixed width of the button in pixels. This one overrides the values defined in min/max values.
    :param int height: fixed height of the button in pixels. This one overrides the values defined in min/max values.
    :param int style: the style of the button.
    :param str tooltip: tooltip as seen with mouse over.
    :param bool theme_updates: whether  button style will be updated when current style changes.
    :param bool checkable: whether the button can be checked.
    :param bool checked: whether (if checkable is True) button is checked by default.
    :param bool force_upper: whether to show button text as uppercase.
    :param int button_width: optional button width.
    :param int button_height: optional button height.
    :param QWidget parent: parent widget.
    :return: newly created button.
    :rtype: QPushButton or BaseButton or ShadowedButton or RoundButton or LabelSmallButton

    ..note:: button icons are always squared.
    """

    global THEME_PREFERENCE

    if not THEME_PREFERENCE:
        THEME_PREFERENCE = core_interfaces.theme_preference_interface()

    icon_color = icon_color or THEME_PREFERENCE.BUTTON_ICON_COLOR
    if not icon_hover_color:
        hover_offset = 25
        icon_hover_color = icon_color
        icon_hover_color = tuple([min(255, c + hover_offset) for c in icon_hover_color])

    min_width = min_width if width is None else width
    max_width = max_width if width is None else width
    min_height = min_height if height is None else height
    max_height = max_height if height is None else height
    icon = resources.icon(icon) if helpers.is_string(icon) else icon
    overlay_icon = resources.icon(overlay_icon) if helpers.is_string(overlay_icon) else overlay_icon

    if style in (consts.ButtonStyles.DEFAULT, consts.ButtonStyles.TRANSPARENT_BACKGROUND):
        new_button = base_button(
            text=text, icon=icon, icon_size=icon_size, icon_color=icon_color, icon_color_theme=icon_color_theme,
            min_width=min_width, max_width=max_width, min_height=min_height, max_height=max_height, style=style,
            tooltip=tooltip, theme_updates=theme_updates, checkable=checkable, checked=checked, parent=parent)
    elif style == consts.ButtonStyles.ICON_SHADOW:
        new_button = shadowed_button(
            text=text, icon=icon, icon_color=icon_color, icon_color_theme=icon_color_theme, min_width=min_width,
            max_width=max_width, max_height=max_height, tooltip=tooltip, theme_updates=theme_updates,
            force_upper=force_upper, parent=parent)
    elif style == consts.ButtonStyles.DEFAULT_QT:
        new_button = regular_button(
            text=text, button_icon=icon, icon_size=icon_size, icon_color=icon_color, overlay_icon_color=overlay_icon_color,
            overlay_icon=overlay_icon, min_width=min_width, max_width=max_width, min_height=min_height,
            max_height=max_height, tooltip=tooltip, checkable=checkable, checked=checked, parent=parent)
    elif style == consts.ButtonStyles.ROUNDED:
        new_button = rounded_button(
            text=text, button_icon=icon, icon_size=icon_size, icon_color=icon_color, tooltip=tooltip,
            button_width=width, button_height=height, checkable=checkable, checked=checked, parent=parent
        )
    elif style == consts.ButtonStyles.LABEL_SMALL:
        new_button = LabelSmallButton(text=text, icon=icon, parent=parent)
    else:
        logger.warning(f'Button style "{style}" is not supported. Default button will be created')
        new_button = regular_button(
            text=text, button_icon=icon, icon_size=icon_size, icon_color=icon_color, overlay_icon_color=overlay_icon_color,
            overlay_icon=overlay_icon, min_width=min_width, max_width=max_width, min_height=min_height,
            max_height=max_height, tooltip=tooltip, checkable=checkable, checked=checked, parent=parent)

    if button_width is not None:
        new_button.setFixedWidth(button_width)
    if button_height is not None:
        new_button.setFixedHeight(button_height)

    return new_button


def base_button(
        text: str = '', icon: str | QIcon | None = None, icon_size: int = 16,
        icon_color: Tuple[int, int, int] or None =None, icon_color_theme: str | None = None,
        min_width: int | None = None, max_width: int | None = None, min_height: int | None = None,
        max_height: int | None = None, style: int = consts.ButtonStyles.DEFAULT, tooltip: str = '',
        status_tip: str = '', theme_updates: bool = True, checkable: bool = False, checked: bool = False,
        parent: QWidget | None = None) -> BaseButton | BasePushButton:
    """
    Creates an extended PushButton with a transparent background or with its regular style.

    :param str text: button text.
    :param str or QIcon icon: icon name or QIcon instance.
    :param int icon_size: size of the icon in pixels.
    :param tuple(int, int, int) icon_color: icon color in 0 to 255 range.
    :param str icon_color_theme: color attribute that should be applied from current applied theme.
    :param int min_width: minimum width of the button in pixels.
    :param int max_width: maximum width of the button in pixels.
    :param int min_height: minimum height of the button in pixels.
    :param int max_height: maximum height of the button in pixels.
    :param int style: the style of the button.
    :param str tooltip: tooltip as seen with mouse over.
    :param str status_tip: status tip as seen with mouse over.
    :param bool theme_updates: whether  button style will be updated when current style changes.
    :param bool checkable: whether the button can be checked.
    :param bool checked: whether (if checkable is True) button is checked by default.
    :param QWidget parent: parent widget.
    :return: newly created button.
    :rtype: BaseButton or BasePushButton
    """

    if icon:
        kwargs = dict(text=text, icon_color_theme=icon_color_theme, theme_updates=theme_updates, parent=parent)
        new_button = BasePushButton(**kwargs) if style == consts.ButtonStyles.DEFAULT else BaseButton(**kwargs)
        new_button.set_icon(icon, size=icon_size, colors=icon_color)
    else:
        kwargs = dict(text=text, icon_color_theme=icon_color_theme, parent=parent)
        new_button = BasePushButton(**kwargs) if style == consts.ButtonStyles.DEFAULT else BaseButton(**kwargs)
    if tooltip:
        new_button.setToolTip(tooltip)
    if status_tip:
        new_button.setStatusTip(status_tip)

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


def regular_button(
        text: str = '', button_icon: str | QIcon | None = None, icon_size: int = 16,
        icon_color: Tuple[int, int, int] or None = None, min_width: int | None = None, max_width: int | None = None,
        min_height: int | None = None, max_height: int | None = None, tooltip: str = '',
        overlay_icon_color: Tuple[int, int, int] or None = None, overlay_icon: str | QIcon | None = None,
        checkable: bool = False, checked: bool = False, parent: QWidget | None = None) -> QPushButton:
    """
    Creates a standard Qt QPushButton.

    :param str text: button text.
    :param str or QIcon button_icon: icon name or QIcon instance.
    :param int icon_size: size of the icon in pixels.
    :param tuple(int, int, int) icon_color: icon color in 0 to 255 range.
    :param int min_width: minimum width of the button in pixels.
    :param int max_width: maximum width of the button in pixels.
    :param int min_height: minimum height of the button in pixels.
    :param int max_height: maximum height of the button in pixels.
    :param str tooltip: tooltip as seen with mouse over.
    :param tuple(int, int, int) overlay_icon_color: color of the overlay image icon.
    :param str or QIcon overlay_icon: the name of the icon image that will be overlayed on top of the original icon.
    :param bool checkable: whether the button can be checked.
    :param bool checked: whether (if checkable is True) button is checked by default.
    :param QWidget parent: parent widget.
    :return: newly created button.
    :rtype: QPushButton
    """

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


def rounded_button(
        text: str = '', button_icon: str | QIcon | None = None, icon_size: int = 16,
        icon_color: Tuple[int, int, int] or None = None, tooltip: str = '', button_width: int = 24,
        button_height: int = 24, checkable: bool = False, checked: bool = False,
        parent: QWidget | None = None) -> RoundButton:
    """
    Creates a rounded button with an icon within a round circle.

    :param str text: button text.
    :param str or QIcon button_icon: icon name or QIcon instance.
    :param int icon_size: size of the icon in pixels.
    :param tuple(int, int, int) icon_color: icon color in 0 to 255 range.
    :param str tooltip: tooltip as seen with mouse over.
    :param int button_width: button width.
    :param int button_height: button height.
    :param bool checkable: whether the button can be checked.
    :param bool checked: whether (if checkable is True) button is checked by default.
    :param QWidget parent: parent widget.
    :return: newly created button.
    :rtype: RoundButton
    """

    button_icon = button_icon or QIcon()
    if button_icon and not button_icon.isNull():
        button_icon = icon.colorize_icon(button_icon, size=icon_size, color=icon_color)
    new_button = RoundButton(text=text, icon=button_icon, tooltip=tooltip, parent=parent)
    new_button.setFixedSize(QSize(button_width, button_height))
    if checkable:
        new_button.setCheckable(True)
        new_button.setChecked(checked)

    return new_button


def shadowed_button(
        text: str = '', icon: str = '', icon_size: int | None = None,
        icon_color: Tuple[int, int, int, int] or None = None, min_width: int | None = None, max_width: int | None = None,
        max_height: int | None = None, shadow_height: int = 4, force_upper: bool = False, tooltip: str = '',
        icon_color_theme: str | None = None, theme_updates: bool = True,
        parent: QWidget | None = None) -> ShadowedButton:
    """
    Creates a new shadowed button with the icon in a coloured box and a button shadow ath the bottom of the button.

    :param str text: button text.
    :param str icon: icon name to set.
    :param int or None icon_size: optional icon size before DPI scaling.
    :param int shadow_height: shadow height.
    :param Tuple[int, int, int, int] or None icon_color: optional icon color which will fill the masked area of the
        icon.
    :param int or None  min_width: minimum width of the button in pixels.
    :param int or None max_width: maximum width of the button in pixels.
    :param int or None max_height: maximum height of the button in pixels.
    :param bool force_upper: whether to force text to be displayed in upper case/
    :param str tooltip: optional tooltip.
    :param str or None icon_color_theme: optional icon color theme to apply.
    :param bool theme_updates: whether to apply theme updates.
    :param QWidget or None parent: optional parent widget.
    :return: newly created shadowed button.
    :rtype: ShadowedButton
    """

    global THEME_PREFERENCE

    if not THEME_PREFERENCE:
        THEME_PREFERENCE = core_interfaces.theme_preference_interface()

    icon = icon or THEME_PREFERENCE.BUTTON_ICON_COLOR

    new_button = ShadowedButton(
        text=text, shadow_height=shadow_height, force_upper=force_upper, tooltip=tooltip,
        icon_color_theme=icon_color_theme, theme_updates=theme_updates, parent=parent)
    new_button.set_icon(icon, colors=icon_color, size=icon_size)
    if max_height is not None:
        new_button.setFixedHeight(max_height)
    if max_width is not None:
        new_button.setMaximumWidth(max_width)
    if min_width is not None:
        new_button.setMinimumWidth(min_width)

    return new_button


def tool_button(text: str = '', icon: str = '', tooltip: str = '', parent: QWidget | None = None) -> BaseToolButton:
    """
    Creates a new QToolButton instance.

    :param str text: tool button text.
    :param str or QIcon icon: tool button icon.
    :param str tooltip: optional button tooltip.
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


def left_aligned_button(
        text: str, icon: str = '', tooltip: str = '', icon_size_override: int | None = None,
        transparent_background: bool = False, padding_override: Tuple[int, int, int, int] | None = None,
        aligment: str = 'left', show_left_click_menu_indicator: bool = False,
        parent: QWidget | None = None) -> LeftAlignedButton:
    """
    Creates a left aligned button.

    :param str text:
    :param str icon:
    :param str tooltip:
    :param int or None icon_size_override:
    :param bool transparent_background:
    :param Tuple[int, int, int, int] or None padding_override:
    :param str aligment:
    :param bool show_left_click_menu_indicator:
    :param QWidget or None parent:
    :return: left aligned button instance.
    :rtype: LeftAlignedButton
    """

    icon_size = dpi.dpi_scale(icon_size_override if icon_size_override else 24 if ':' in icon else 16)
    padding = padding_override if padding_override else dpi.margins_dpi_scale([4, 0, 0, 0] if ':' in icon else [7, 4, 4, 4])
    alignment_text = f'text-align: {aligment};'
    padding_text = f'padding-left: {padding[0]}px; padding-top: {padding[1]}px; padding-right: {padding[2]}px; padding-bottom: {padding[3]}px'
    menu_indicator = '' if show_left_click_menu_indicator else 'QPushButton::menu-indicator{image: none;};'
    transparency = '' if not transparent_background else 'background-color: transparent;'
    icon_obj = QIcon(QPixmap(f'{icon}.png')) if ':' in icon else resources.icon(icon) if icon else None
    new_button = LeftAlignedButton(text, icon=icon_obj, tooltip=tooltip, parent=parent)
    new_button.setIconSize(QSize(icon_size, icon_size))
    new_button.setStyleSheet("QPushButton {} {} {} {} {} \n{}".format(
        "{", alignment_text, padding_text, transparency, "}", menu_indicator))

    return new_button


# class AbstractButton(QAbstractButton, dpi.DPIScaling):
class AbstractButton(dpi.DPIScaling):
    """
    Abstract class for all custom Qt buttons.
    Adds the ability to change button icon based on button press status.
    """

    _idle_icon = None							# type: QIcon
    _pressed_icon = None						# type: QIcon
    _hover_icon = None							# type: QIcon
    _highlight_offset = 40
    _icon_names = []							# type: List[str]
    _icon_colors = (128, 128, 128)
    _icon_scaling = []

    # @override
    def enterEvent(self, event: QEvent) -> None:
        if self._hover_icon is not None and self.isEnabled():
            self.setIcon(self._hover_icon)

    # @override
    def leaveEvent(self, event: QEvent) -> None:
        if self._idle_icon is not None and self.isEnabled():
            self.setIcon(self._idle_icon)

    # @override(check_signature=False)
    def setEnabled(self, flag: bool) -> None:
        super().setEnabled(flag)

        # force update of the icons after resizing
        self.update_icons()

    # @override(check_signature=False)
    def setDisabled(self, flag: bool) -> None:
        super().setDisabled(flag)

        # force update of the icons after resizing
        self.update_icons()

    # @override
    def setIconSize(self, size: QSize) -> None:
        super().setIconSize(dpi.size_by_dpi(size))

        # force update of the icons after resizing
        self.update_icons()

    def set_highlight(self, value: float):
        """
        Sets the highlight offset of the icon.

        :param float value: highlight offset .
        """

        self._highlight_offset = value

    def set_icon(
            self, icon_name: str | QIcon,
            colors: Iterable[int, int, int] | Iterable[None] | Iterable[None, None] | None = None,
            size: int | None = None, color_offset: float | None = None, scaling: List[float, float] = None, **kwargs):
        """
        Set the icon of the button.

        :param str or QIcon icon_name: button icon.
        :param Iterable[int, int, int] or Iterable[None] or Iterable[None, None] or None colors: icon colors.
        :param int size: icon size.
        :param float, color_offset: icon highlight offset.
        :param List[float, float] scaling: icon scaling.
        """

        if size is not None:
            self.setIconSize(QSize(size, size))
        if color_offset is not None:
            self._highlight_offset = color_offset
        if scaling is not None:
            self._icon_scaling = scaling

        self._icon_names = icon_name if isinstance(icon_name, QIcon) else resources.icon(icon_name)
        self._grayscale = kwargs.pop('grayscale', False)
        self._tint_composition = kwargs.pop('tint_composition', QPainter.CompositionMode_Plus)
        colors = colors or self._icon_colors

        # self.set_icon_color(colors, update=False)
        self.update_icons()

    def set_icon_idle(self, idle_icon: QIcon, update: bool = False):
        """
        Sets the icon idle.

        :param QIcon idle_icon: idle icon.
        :param bool update: whether force icons update.
        """

        self._idle_icon = idle_icon
        self.setIcon(idle_icon)
        if update:
            self.update_icons()

    def set_icon_hover(self, hover_icon: QIcon, update: bool = False):
        """
        Sets the icon hover.

        :param QIcon hover_icon: hover icon.
        :param bool update: whether forece icons update.
        """

        self._hover_icon = hover_icon
        if update:
            self.update_icons()

    def set_icon_color(self, colors: QColor | Tuple[int, int, int], update: bool = True):
        """
        Set the color of the icon.

        :param QColor or Tuple[int, int, int] colors: icon color or colors
        :param bool update: whether force icons update.
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

        # Setting the icon colors, causes our current default icons to be tinted with a solid color with an undersired
        # result
        # self._idle_icon = icon.colorize_layered_icon(
        # 	icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
        # 	composition=self._tint_composition, colors=self._icon_colors, grayscale=grayscale)
        # self._hover_icon = icon.colorize_layered_icon(
        # 	icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
        # 	composition=self._tint_composition, colors=self._icon_colors, tint_color=hover_color, grayscale=grayscale)

        self._idle_icon = icon.colorize_layered_icon(
            icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
            composition=self._tint_composition, grayscale=grayscale)
        self._hover_icon = icon.colorize_layered_icon(
            icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
            composition=self._tint_composition, tint_color=hover_color, grayscale=grayscale)

        self.setIcon(self._idle_icon)


class BaseButton(QPushButton, AbstractButton):
    """
    Custom QPushButton that allows to have left, middle and right click.
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

    class BaseMenuButtonMenu(menus.SearchableMenu):
        """
        Custom menu that can be attached to BaseButton
        """

        def __init__(self, *args, **kwargs):
            super(BaseButton.BaseMenuButtonMenu, self).__init__(*args, **kwargs)

            self._key_pressed = False
            self._key = Qt.Key_Control

            self.setAttribute(Qt.WA_TranslucentBackground)

        @override
        def keyPressEvent(self, arg__1: QKeyEvent) -> None:
            if arg__1.key() == self._key:
                pos = self.mapFromGlobal(QCursor.pos())
                action = self.actionAt(pos)
                if tooltip.has_custom_tooltips(action):
                    self._popup_tooltip = tooltip.CustomTooltipPopup(
                        action, icon_size=dpi.dpi_scale(40), popup_release=self._key)
                self._key_pressed = True
            super().keyPressEvent(arg__1)

        @override
        def keyReleaseEvent(self, event: QKeyEvent) -> None:
            if event.key() == Qt.Key_Control:
                self._key_pressed = False

        def index(self, name: str, exclude_search: bool = True) -> int:
            """
            Returns index of the button with given name within the menu.

            :param str name: button name to get index of.
            :param bool exclude_search: whether to exclude search buttons.
            :return: index of the button.
            :rtype: int
            """

            for i, action in enumerate(self.actions()):
                if action.text() == name:
                    result = i
                    if exclude_search:
                        result -= 2
                    return result

    def __init__(
            self, text: str = '', icon: QIcon | str | None = None, icon_hover: QIcon | str | None = None,
            icon_color_theme: str | None =None, elided: bool = False, theme_updates: bool = True, menu_padding: int = 5,
            menu_align: Qt.AlignmentFlag = Qt.AlignLeft, double_click_enabled: bool = False,
            parent: QWidget | None = None):

        self._idle_icon = resources.icon(icon) if icon and helpers.is_string(icon) else (icon or QIcon())
        self._hover_icon = resources.icon(icon_hover) if icon_hover and helpers.is_string(icon_hover) else icon_hover
        self._icon_color_theme = icon_color_theme
        self._text = text

        QPushButton.__init__(self)
        self.setParent(parent)
        if self._idle_icon:
            self.setIcon(self._idle_icon)
        self.setText(self._text)
        # super().__init__(icon=self._idle_icon, text=self._text, parent=parent)

        self._menu_padding = menu_padding
        self._menu_align = menu_align
        self._double_click_interval = 500
        self._double_click_enabled = double_click_enabled
        self._last_click = None
        self._theme_updates_color = theme_updates
        self._elided = elided

        self._menu_active = {  # defines which menus are active
            Qt.LeftButton: True,
            Qt.MiddleButton: True,
            Qt.RightButton: True
        }
        self._click_menu = {  # stores available menus
            Qt.LeftButton: None,									# type: BaseButton.BaseMenuButtonMenu
            Qt.MiddleButton: None,										# type: BaseButton.BaseMenuButtonMenu
            Qt.RightButton: None									# type: BaseButton.BaseMenuButtonMenu
        }
        self._menu_searchable = {  # defines which menus are searchable
            Qt.LeftButton: False,
            Qt.MiddleButton: False,
            Qt.RightButton: False
        }

        self.leftClicked.connect(partial(self._on_context_menu, Qt.LeftButton))
        self.middleClicked.connect(partial(self._on_context_menu, Qt.MiddleButton))
        self.rightClicked.connect(partial(self._on_context_menu, Qt.RightButton))

        self._theme_pref = core_interfaces.theme_preference_interface()
        self._theme_pref.updated.connect(self.update_theme)

    @property
    def menu_align(self) -> Qt.AlignmentFlag:
        return self._menu_align

    @menu_align.setter
    def menu_align(self, align: Qt.AlignmentFlag = Qt.AlignLeft):
        self._menu_align = align

    @property
    def double_click_enabled(self) -> bool:
        return self._double_click_enabled

    @double_click_enabled.setter
    def double_click_enabled(self, flag: bool):
        self._double_click_enabled = flag

    @property
    def double_click_interval(self) -> int:
        return self._double_click_interval

    @double_click_interval.setter
    def double_click_interval(self, interval: int = 150):
        self._double_click_interval = interval

    @override
    def mousePressEvent(self, e: QMouseEvent) -> None:
        """
        Overrides mousePressEvent function.

        :param QMouseEvent e: Qt mouse event.
        :return:
        """

        if e.button() == Qt.MiddleButton:
            self.setDown(True)
        elif e.button() == Qt.RightButton:
            self.setDown(True)

        self._last_click = self.SINGLE_CLICK

        super().mousePressEvent(e)

    @override
    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        """
        Overrides mouseReleaseEvent function.

        :param QMouseEvent e: Qt mouse event.
        :return:
        """

        button = e.button()

        if not self.isCheckable():
            self.setDown(False)

        if not self._double_click_enabled:
            self._mouse_single_click_action(button)
            super().mouseReleaseEvent(e)
            return

        if self._last_click == self.SINGLE_CLICK:
            QTimer.singleShot(self._double_click_interval, lambda: self._mouse_single_click_action(button))
        else:
            self._mouse_double_click_action(button)

        super().mouseReleaseEvent(e)

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """
        Overrides mouseDoubleClickEvent function.

        :param QMouseEvent event: Qt mouse event.
        :return:
        """

        self._last_click = self.DOUBLE_CLICK

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Overrides resizeEvent function that adds elide functionality.

        :param QResizeEvent event: Qt resize event.
        """

        if self._elided:
            has_icon = self.icon() and not self.icon().isNull()
            if has_icon:
                font_metrics = QFontMetrics(self.font())
                elided = font_metrics.elidedText(self._text, Qt.ElideMiddle, self.width() - 30)
                super(BaseButton, self).setText(elided)

        super().resizeEvent(event)

    @override
    def setText(self, text: str) -> None:
        """
        Overrides base setText function.

        :param str text: new button text.
        """

        self._text = text
        super(BaseButton, self).setText(text)

    @override(check_signature=False)
    def actions(self, mouse_menu: Qt.MouseButton = Qt.LeftButton) -> List[QAction]:
        """
        Overrides base actions function to returns the actions of mouse button.

        :param Qt.MouseButton mouse_menu: mouse button.
        :return: list of actions.
        :rtype: list(QAction)
        """

        menu_instance = self._click_menu.get(mouse_menu, None)
        if menu_instance is None:
            return list()

        return menu_instance.actions()[2:]

    @override(check_signature=False)
    def setWindowTitle(self, arg__1: str, mouse_menu: Qt.MouseButton = Qt.LeftButton) -> None:
        """
        Overrides base setWindowTitle function to set the weindow title of the menu, if its get teared off.

        :param str arg__1: window title
        :param Qt.MouseButton mouse_menu: menu button
        """

        menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        menu.setWindowTitle(arg__1)

    @override(check_signature=False)
    def setMenu(self, menu: QMenu, mouse_button: Qt.MouseButton = Qt.LeftButton) -> None:
        """
        Overrides base setMenu function to set the menu based on mouse button.

        :param QMenu menu: menu to set
        :param Qt.MouseButton mouse_button: mouse button.
        """

        self._click_menu[mouse_button] = menu

    @override(check_signature=False)
    def menu(
            self, mouse_menu: Qt.MouseButton = Qt.LeftButton, searchable: bool = False, auto_create: bool = True) -> QMenu:
        """
        Overrides base menu function to get menu depending on the mouse button pressed.

        :param Qt.MouseButton mouse_menu: mouse button.
        :param bool searchable: whether menu is searchable.
        :param bool auto_create: whether to auto create menu if it does not exist yet.
        :return:  requested menu.
        :rtype: QMenu
        """

        if self._click_menu[mouse_menu] is None and auto_create:
            menu_button = BaseButton.BaseMenuButtonMenu(title='Menu Button', parent=self)
            menu_button.setObjectName('menuButton')
            menu_button.triggered.connect(lambda action: self.actionTriggered.emit(action, mouse_menu))
            menu_button.triggered.connect(partial(self._on_menu_changed, mouse_menu))
            if not searchable:
                menu_button.set_search_visible(False)
            self._click_menu[mouse_menu] = menu_button

        return self._click_menu[mouse_menu]

    @override(check_signature=False)
    def addAction(
            self, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton, connect: Callable = None,
            checkable: bool = False, checked: bool = True, action: QAction | None = None,
            action_icon: QIcon | str | None = None, data: Any = None, icon_text: str | None = None,
            icon_color: Tuple[int, int, int] | None = None, icon_size=16, tooltip: str | None = None) -> QAction | None:
        """
        Adds a new menu item through an action.

        :param str name: text for the new menu item.
        :param Qt.LeftButton or Qt.RightButton or Qt.MiddleButton mouse_menu: mouse button.
        :param Callable or None connect: function to connect when the menu item is pressed.
        :param bool checkable: whether menu item is checkable.
        :param bool checked: if checkable is True, whether menu item is checked by default.
        :param QAction or None action: if given this is the action will be added directly without any extra steps.
        :param QIcon or str action_icon: icon for the menu item.
        :param Any data: custom data to store within the action.
        :param str icon_text: text for the icon.
        :param tuple(int, int, int) icon_color: color of the menu item in 0-255 range.
        :param int icon_size: size of the icon.
        :param str tooltip: new menu item tooltip.
        :return: newly created action.
        :rtype: QAction or None
        """

        args = helpers.get_args(locals())

        found_menu = self.menu(mouse_menu, searchable=False)

        if action is not None:
            found_menu.addAction(action)
            return None

        args.pop('action', None)
        new_action = self.new_action(**args)
        found_menu.addAction(new_action)

        return new_action

    def new_action(
            self, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton, connect: Callable = None,
            checkable: bool = False, checked: bool = True, action_icon: QIcon | str | None = None, data: Any = None,
            icon_text: str | None = None, icon_color: QColor | None = None, icon_size: int = 16, tooltip: str | None = None):
        """
        Creates a new menu item through an action.

        :param str name: text for the new menu item.
        :param Qt.MouseButton mouse_menu: mouse button.
        :param callable or None connect: function to connect when the menu item is pressed.
        :param bool checkable: whether menu item is checkable.
        :param bool checked: if checkable is True, whether menu item is checked by default.
        :param QIcon or str action_icon: icon for the menu item.
        :param object data: custom data to store within the action.
        :param str icon_text: text for the icon.
        :param tuple(int, int, int) icon_color: color of the menu item in 0-255 range.
        :param int icon_size: size of the icon.
        :param str tooltip: new menu item tooltip.
        :return: newly created action.
        :rtype: SearchableTaggedAction
        """

        found_menu = self.menu(mouse_menu, searchable=False)

        new_action = menus.SearchableMenu.SearchableTaggedAction(name, parent=found_menu)
        new_action.setCheckable(checkable)
        new_action.setChecked(checked)
        new_action.tags = set(self._string_to_tags(name))
        new_action.setData(data)

        if tooltip:
            new_action.setToolTip(tooltip)

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

    def insert_action_index(
            self, index: int, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton,
            action: QAction | None = None, connect: Callable = None, checkable: bool = False, checked: bool = True,
            action_icon: QIcon | str | None = None, data: Any = None, icon_text: str | None = None,
            icon_color: QColor | None = None, icon_size: int = 16, tooltip: str | None = None) -> QAction | None:
        """
        Inserts action at given index.

        :param int index: index to insert action into.
        :param str name: text for the new menu item.
        :param Qt.Button mouse_menu: mouse button.
        :param QAction or None action: action to insert.
        :param callable or None connect: function to connect when the menu item is pressed.
        :param bool checkable: whether menu item is checkable.
        :param bool checked: if checkable is True, whether menu item is checked by default.
        :param QIcon or str action_icon: icon for the menu item.
        :param object data: custom data to store within the action.
        :param str icon_text: text for the icon.
        :param tuple(int, int, int) icon_color: color of the menu item in 0-255 range.
        :param int icon_size: size of the icon.
        :param str tooltip: new menu item tooltip.
        :return: inserted action.
        :rtype: QAction or None
        """

        menu = self.menu(mouse_menu, searchable=False)
        actions = self.actions(mouse_menu)
        before = actions[index]

        if action:
            menu.insertAction(before, action)
            return None

        new_action = self.new_action(
            name=name, mouse_menu=mouse_menu, connect=connect, checkable=checkable, checked=checked,
            action_icon=action_icon, data=data, icon_text=icon_text, icon_color=icon_color, icon_size=icon_size,
            tooltip=tooltip)
        menu.insertAction(before, new_action)

        return new_action

    def add_separator(self, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Adds a new separator into the menu.

        :param Qt.Button mouse_menu: mouse button.
        """

        found_menu = self.menu(mouse_menu)
        found_menu.addSeparator()

    def insert_separator_index(self, index: int, mouse_menu: Qt.MouseButton | Qt.LeftButton, after_index: bool = False):
        """
        Inserts separator at given index.

        :param int index: index to insert separator into.
        :param Qt.MouseButton mouse_menu: mouse button.
        :param bool after_index: whether to insert separator after given index.
        """

        actions = self.actions(mouse_menu)
        menu = self.menu(mouse_menu, searchable=False)
        if after_index:
            index += 1
        before = actions[index]
        if before:
            menu.insertSeparator(before)

    def is_searchable(self, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Returns whether the button menu is searchable.

        :param Qt.Button mouse_menu: mouse button
        :return: True if the given mouse menu is searchable; False otherwise.
        :rtype: bool
        """

        if self._click_menu[mouse_menu] is not None:
            return self._click_menu[mouse_menu].search_visible()

        return self._menu_searchable[mouse_menu]

    def set_searchable(self, mouse_menu: Qt.MouseButton = Qt.LeftButton, searchable: bool = True):
        """
        Sets whether given menu is searchable.

        :param Qt.Button mouse_menu: mouse button.
        :param bool searchable: True to make menu searchable; False otherwise.
        """

        self._menu_searchable[mouse_menu] = searchable

        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].set_search_visibility(searchable)

    def set_tearoff_enabled(self, mouse_menu: Qt.MouseButton = Qt.LeftButton, tearoff: bool = True):
        """
        Sets whether tear off is enabled for a specific menu.

        :param Qt.Button mouse_menu: mouse button.
        :param flag tearoff: True to enable tearoff; False otherwise.
        """

        found_menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        found_menu.setTearOffEnabled(tearoff)

    def update_theme(self, event):
        """
        Updates theme.
        :param ThemeUpdateEvent event: theme update event.
        """

        if not self._theme_updates_color:
            return

        self._icon_color_theme = self._icon_color_theme or 'BUTTON_ICON_COLOR'
        if self._icon_color_theme:
            icon_color = getattr(event.theme_dict, self._icon_color_theme)
        else:
            icon_color = event.theme_dict.BUTTON_ICON_COLOR
        self.set_icon_color(icon_color)

    def menu_pos(self, align: Qt.AlignmentFlag = Qt.AlignLeft, widget: QWidget | None = None):
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

    def index(self, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Returns the index of the menu item or actoin name.

        :param str name: name of menu item.
        :param Qt.Button mouse_menu: mouse button.
        :return: index of the menu.
        :rtype: int
        """

        return self.menu(mouse_menu).index(name)

    def clear_menu(self, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Clears all the menu items of the specified menu.

        :param Qt.LeftButton or Qt.MiddleButton or Qt.RightButton mouse_menu: mouse button.
        """

        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].clear()

    def _mouse_single_click_action(self, mouse_button: Qt.MouseButton) -> bool:
        """
        Internal function that is called when a single click is triggered.

        :param Qt.MouseButton button: pressed button.
        :return: True if mouse was clicked; False otherwise.
        :rtype: bool
        """

        if self._last_click == self.SINGLE_CLICK or self._double_click_enabled is False:
            if mouse_button == Qt.LeftButton:
                self.leftClicked.emit()
                return True
            elif mouse_button == Qt.MiddleButton:
                self.middleClicked.emit()
                return True
            elif mouse_button == Qt.RightButton:
                self.rightClicked.emit()
                return True

        return False

    def _mouse_double_click_action(self, mouse_button: Qt.MouseButton):
        """
        Internal function that is called when a double click is triggered.

        :param Qt.MouseButton button: pressed button
        """

        if mouse_button == Qt.LeftButton:
            self.leftDoubleClicked.emit()
        elif mouse_button == Qt.MiddleButton:
            self.middleDoubleClicked.emit()
        elif mouse_button == Qt.RightButton:
            self.rightDoubleClicked.emit()

    def _about_to_show(self, mouse_button: Qt.MouseButton):
        """
        Internal function that is called when context menu is about to show

        :param Qt.MouseButton mouse_button: mouse button.
        """

        if mouse_button == Qt.LeftButton:
            self.menuAboutToShow.emit()
        elif mouse_button == Qt.MiddleButton:
            self.middleMenuAboutToShow.emit()
        elif mouse_button == Qt.RightButton:
            self.rightMenuAboutToShow.emit()

    def _string_to_tags(self, string_to_convert: str) -> List[str]:
        """
        Internal function that converst given string into tags.

        :param str string_to_convert: string to convert.
        :return: string tags.
        :rtype: List[str]
        """

        tags = list()
        tags += string_to_convert.split(' ')
        tags += [tag.lower() for tag in string_to_convert.split(' ')]

        return tags

    def _on_context_menu(self, mouse_button: Qt.MouseButton):
        """
        Internal callback function that shows the context menu depending on the mouse button.
        :param Qt.MouseButton mouse_button: mouse button
        """

        menu = self._click_menu[mouse_button]
        if menu is not None and self._menu_active[mouse_button]:
            self._about_to_show(mouse_button)
            pos = self.menu_pos(widget=menu, align=self._menu_align)
            menu.exec_(pos)
            menu._search_edit.setFocus()

    def _on_menu_changed(self, mouse_button: Qt.MouseButton, *args, **kwargs):
        """
        Internal callback function that is called each time menu changes.

        :param Qt.MouseButton mouse_button: mouse button.
        """

        if mouse_button == Qt.LeftButton:
            self.menuChanged.emit()
        elif mouse_button == Qt.MiddleButton:
            self.middleMenuChanged.emit()
        elif mouse_button == Qt.RightButton:
            self.rightMenuChanged.emit()


class BasePushButton(BaseButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qtutils.set_stylesheet_object_name(self, 'DefaultButton')


class IconMenuButton(BaseButton):
    """
    Custom menu that represents a button with an icon (no text). Clicking it will pop up a context menu.
    """

    def __init__(
            self, icon: QIcon | str | None = None, icon_hover: QIcon | str | None = None,
            double_click_enabled: bool = False, color: tuple[int, int, int] | None = None,
            tint_color: tuple[int, int, int] | None = None, menu_name: str = '', switch_icon_on_click: bool = False,
            theme_updates: bool = True, parent: QWidget | None = None):
        super().__init__(
            icon=icon, icon_hover=icon_hover, double_click_enabled=double_click_enabled, theme_updates=theme_updates,
            parent=parent)

        self._tint_color = tint_color
        self._icon_color = color or (255, 255, 255)
        self._current_text = menu_name
        self._switch_icon = switch_icon_on_click

        self.setup_ui()

        self.actionTriggered.connect(self._on_menu_item_clicked)

    @override
    def text(self) -> str:
        """
        Overrides base text function.

        :return: menu name.
        :rtype: str
        """

        return self._current_text

    def setup_ui(self):
        """
        Setup icon menu button UI.
        """

        for found_menu in self._click_menu.values():
            if found_menu is not None:
                found_menu.setToolTipsVisible(True)

        self.menu_align = Qt.AlignRight

    def current_text(self) -> str:
        """
        Returns the current selected menu name.

        :return: current menu name.
        :rtype: str
        """

        return self._current_text

    def current_action(self, mouse_menu: Qt.MouseButton = Qt.LeftButton) -> QAction | None:
        """
        Returns current action.

        :param Qt.MouseButton mouse_menu: mouse button.
        :return: current action.
        :rtype: QAction or None
        """

        for action in self.actions(mouse_menu):
            if action.text() == self._current_text:
                return action

        return None

    def current_index(self, mouse_menu: Qt.MouseButton = Qt.LeftButton) -> int:
        """
        Returns the current selected menu index.

        :param Qt.Button mouse_menu: mouse button.
        :return: current index menu item.
        :rtype: int
        """

        return self.index(self.current_text(), mouse_menu)

    def set_menu_name(self, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton):
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

    def action_connect_list(self, actions: List[Tuple[str, str]], mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Creates the entire menu with the info contained within the actions list.

        :param List[Tuple[str, str]] actions: list of actions. Eg: [('icon1', 'menuName1'), (...), ...]
        :param Qt.MouseButton mouse_menu: button that will open the menu.
        """

        for action in actions:
            self.addAction(action[1], mouse_menu=mouse_menu, action_icon=action[0])
        first_name = actions[0][1]
        self.set_menu_name(first_name)

    def _on_menu_item_clicked(self, action: QAction, mouse_menu: Qt.MouseButton):
        """
        Internal callback function that is called each time a menu item is clicked by the user.

        :param QAction action: action clicked
        :param Qt.MouseButton mouse_menu: mouse button.
        """

        self.set_menu_name(action.text())


class OkCancelButtons(QWidget):

    okButtonPressed = Signal()
    cancelButtonPressed = Signal()

    def __init__(self, ok_text: str = 'OK', cancel_text: str = 'Cancel', parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._main_layout = layouts.horizontal_layout()
        self.setLayout(self._main_layout)
        self._ok_button = QPushButton(ok_text, parent=self)
        self._cancel_button = QPushButton(cancel_text, parent=self)
        self._main_layout.addWidget(self._ok_button)
        self._main_layout.addWidget(self._cancel_button)

        self._setup_signals()

    @property
    def ok_button(self) -> QPushButton:
        return self._ok_button

    @property
    def cancel_button(self) -> QPushButton:
        return self._cancel_button

    def _setup_signals(self):
        """
        Internal function that setup all the signals for this widget.
        """

        self._ok_button.clicked.connect(self.okButtonPressed.emit)
        self._cancel_button.clicked.connect(self.cancelButtonPressed.emit)


class RoundButton(QPushButton, dpi.DPIScaling):
    """
    Custom round button. It can be rendered in two different ways:
        1. Mask: will cut the button into a circle. Allow also stylesheets. It is pixelated when drawing it out.
        2. Stylesheet: creates a smooth circle button without pixelation. For rectangle buttons it will not be round
            and also the user will not be able to user their own stylesheet.
    """

    class RenderingMethod:
        MASK = 0
        STYLESHEET = 1

    def __init__(
            self, text: str | None = None, icon: str | None = None, method: int = RenderingMethod.STYLESHEET, tooltip='',
            parent: QWidget | None = None):
        super().__init__(text=text, icon=icon, parent=parent)

        self._method = method
        self._custom_style = ''
        self.setToolTip(tooltip)

        self._update_button()

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self._update_button()
        super().resizeEvent(event)

    @override(check_signature=False)
    def setStyleSheet(self, text: str) -> None:
        if self._method == self.RenderingMethod.STYLESHEET:
            self._custom_style = text
            self._update_button()
        else:
            super().setStyleSheet(text)

    def set_method(self, method: int):
        """
        Sets the rendering method to use.
            - Mask: pixelated edges but can set custom stylesheets.
            - Stylesheet: Smooth edges but cannot set custom stylesheets.
        :param RoundButton.RenderingMethod method: render method to use.
        """

        self._method = method
        self._update_button()

    def _round_style(self) -> str:
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
            super().setStyleSheet(self._round_style() + self._custom_style)


class LabelSmallButton(QWidget):

    clicked = Signal()

    def __init__(
            self, text: str = '', icon: str | QIcon | None = None, icon_size: int = 16,
            icon_color: Tuple[int, int, int, int] | None = None, min_width: int | None = None,
            min_height: int | None = None, max_height: int | None = None, style: int = consts.ButtonStyles.DEFAULT,
            max_width: int | None = None, tooltip: str = '', force_upper: bool = False, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._text = text
        if text:
            self._label = labels.BaseLabel(text=text, tooltip=tooltip, upper=force_upper)
        self._button = base_button(
            text='', icon=icon, icon_size=icon_size, tooltip=tooltip, icon_color=icon_color, min_width=min_width,
            max_width=max_width,  min_height=min_height, max_height=max_height, style=style, parent=parent)
        button_layout = layouts.horizontal_layout(parent=self)
        if text:
            button_layout.addWidget(self._label, 5)
        button_layout.addWidget(self._button, 1)

        self._setup_signals()

    @override
    def setDisabled(self, arg__1: bool) -> None:
        self._button.setDisabled(arg__1)
        if self._text:
            self._label.setDisabled(arg__1)

    def _setup_signals(self):
        """
        Internal function that setup widget signals.
        """

        self._button.clicked.connect(self.clicked.emit)


class ShadowedButton(BaseButton):

    _MENU_INDICATOR_ICON = 'menu_indicator'

    def __init__(
            self, text: str = '', shadow_height: int = 4, force_upper: bool = False, tooltip: str = '',
            icon_color_theme: str | None = None, theme_updates: bool = True, parent: QWidget | None = None):

        super(ShadowedButton, self).__init__(
            icon_color_theme=icon_color_theme, theme_updates=theme_updates, parent=parent)

        self._main_layout = None									# type: layouts.GridLayout
        self._text_label = None										# type: QLabel
        self._image_widget = None									# type: ShadowedButtonImage
        self._shadow = None											# type: ShadowedButtonShadow
        self._spacing_widget = None									# type: QWidget
        self._force_upper = force_upper
        self._mouse_entered = True
        self._icon_pixmap = None									# type: QPixmap
        self._icon_hovered_pixmap = None							# type: QPixmap
        self._icon_pressed_pixmap = None							# type: QPixmap
        self._is_menu = True
        self._icon_size = dpi.size_by_dpi(QSize(16, 16))
        self._theme_pref = core_interfaces.theme_preference_interface()

        self.setup_ui()

        self.setToolTip(tooltip)
        self.setText(text)
        self.set_shadow_height(shadow_height)

    @property
    def is_menu(self) -> bool:
        return self._is_menu

    @is_menu.setter
    def is_menu(self, flag: bool):
        self._is_menu = flag

    @override
    def setFixedHeight(self, h: int) -> None:
        self.update_image_widget(h)
        super().setFixedHeight(h)

    @override(check_signature=False)
    def setFixedSize(self, size: QSize) -> None:
        self.update_image_widget(size.height())
        super(ShadowedButton, self).setFixedSize(size)

    @override
    def setText(self, text: str) -> None:
        if not self._text_label:
            return
        if self._force_upper and text is not None:
            text = text.upper()

        self._text_label.setText(text)

    @override
    def setIconSize(self, size: QSize) -> None:
        self._icon_size = dpi.size_by_dpi(size)
        self._image_widget.setFixedSize(self._icon_size)

    @override
    def enterEvent(self, event: QEvent) -> None:
        self._mouse_entered = True
        qtutils.set_stylesheet_object_name(self, '')
        qtutils.set_stylesheet_object_name(self._shadow, 'buttonShadowHover')
        qtutils.set_stylesheet_object_name(self._image_widget, 'shadowedImageHover')
        qtutils.set_stylesheet_object_name(self._text_label, 'shadowedLabelHover')
        self._image_widget.setPixmap(self._icon_hovered_pixmap)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self._mouse_entered = False
        qtutils.set_stylesheet_object_name(self, '')
        qtutils.set_stylesheet_object_name(self._shadow, '')
        qtutils.set_stylesheet_object_name(self._image_widget, '')
        qtutils.set_stylesheet_object_name(self._text_label, '')
        self._image_widget.setPixmap(self._icon_pixmap)

    @override
    def mousePressEvent(self, e: QMouseEvent) -> None:
        qtutils.set_stylesheet_object_name(self, 'shadowedButtonPressed')
        qtutils.set_stylesheet_object_name(self._shadow, 'buttonShadowPressed')
        qtutils.set_stylesheet_object_name(self._image_widget, 'shadowedImagePressed')
        qtutils.set_stylesheet_object_name(self._text_label, 'shadowedLabelPressed')
        self._image_widget.setPixmap(self._icon_pressed_pixmap)

        return super().mousePressEvent(e)

    @override
    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        # if mouse still entered while mouse released then set it back to hovered style
        if self._mouse_entered:
            self.enterEvent(e)

        return super().mouseReleaseEvent(e)

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        event.ignore()
        return super().mouseDoubleClickEvent(event)

    @override
    def update_theme(self, event):
        if self._theme_updates_color:
            self._icon_color_theme = self._icon_color_theme or '$BUTTON_ICON_COLOR'

    def setup_ui(self):
        """
        Initializes shadow button UI.
        """

        self._main_layout = QGridLayout(spacing=0)
        self.setLayout(self._main_layout)

        self._image_widget = ShadowedButtonImage(parent=self)
        self._text_label = QLabel(parent=self)
        self._shadow = ShadowedButtonShadow(parent=self)

        self._image_widget.setFixedHeight(self.sizeHint().height())
        self._image_widget.setAlignment(Qt.AlignCenter)
        self._text_label.setAlignment(Qt.AlignCenter)
        self._spacing_widget = QWidget(parent=self)

        self._main_layout.addWidget(self._image_widget, 0, 0, 1, 1)
        self._main_layout.addWidget(self._text_label, 0, 1, 1, 1)
        self._main_layout.addWidget(self._spacing_widget, 0, 2, 1, 1)
        self._main_layout.addWidget(self._shadow, 1, 0, 1, 3)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

    def set_force_upper(self, flag: bool):
        """
        Sets whether button text should appear as upper case.

        :param bool flag: whether to force text upper case.
        """

        self._force_upper = flag

    def set_shadow_height(self, height: int):
        """
        Sets the shadow height in pixels.

        :param int height: shadow height (in pixels).
        """

        self._shadow.setFixedHeight(height)

    def set_icon(
            self, icons: str | List[QIcon] | List[str], colors: Tuple[int, int, int] | None = None,
            hover_colors: Tuple[int, int, int] | None = None, size: int | None = None,
            pressed_colors: Tuple[int, int, int] | None = None, scaling: Tuple[float, float, float] | None = None):
        """
        Set button icon.

        :param str or List[QIcon] or List[str] icons: icon to set.
        :param Tuple[int, int, int] or None colors: optional icon color.
        :param Tuple[int, int, int] or None hover_colors: optional hover icon color.
        :param int or None size: optional icon size.
        :param Tuple[int, int, int] or None pressed_colors: optional icon pressed colors.
        :param Tuple[float, float, float] or None scaling: optional scaling.
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
        self._icon_pixmap = icon.colorize_layered_icon(
            self._icon_names, colors=colors, size=new_size, scaling=scaling).pixmap(QSize(new_size, new_size))
        self._icon_hovered_pixmap = icon.colorize_layered_icon(
            self._icon_names, colors=hover_color, size=new_size, scaling=scaling).pixmap(QSize(new_size, new_size))
        self._icon_pressed_pixmap = icon.colorize_layered_icon(
            self._icon_names, colors=pressed_color, size=new_size, scaling=scaling).pixmap(QSize(new_size, new_size))

        self._image_widget.setPixmap(self._icon_pixmap)

    def update_image_widget(self, new_height: int):
        """
        Updates button to make sure widget is always square.

        :param int new_height: new height of the widget to update to.
        """

        self._image_widget.setFixedSize(QSize(new_height, new_height))
        self._spacing_widget.setFixedWidth(int(dpi.dpi_scale(new_height) * 0.5))


class ShadowedButtonImage(QLabel, dpi.DPIScaling):
    """
    stylesheet purposes
    """

    pass


class ShadowedButtonShadow(QFrame, dpi.DPIScaling):
    """
    stylesheet purposes
    """

    pass


@mixin.cursor_mixin
class BaseToolButton(QToolButton):
    def __init__(self, tooltip: str | None = None, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._image = None
        self._theme_pref = THEME_PREFERENCE or core_interfaces.theme_preference_interface()

        self.setAutoExclusive(False)
        self.setAutoRaise(True)

        self._polish_icon()
        self.toggled.connect(self._polish_icon)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        if tooltip:
            self.setToolTip(tooltip)

        self._theme_size = self._theme_pref.theme_data().default_size

    @override
    def enterEvent(self, arg__1: QEvent) -> None:
        if self._image:
            theme_data = self._theme_pref.theme_data()
            if theme_data:
                accent_color = theme_data.ACCENT_COLOR
                self.setIcon(resources.icon(self._image, color=accent_color))
        return super().enterEvent(arg__1)

    @override
    def leaveEvent(self, arg__1: QEvent) -> None:
        self._polish_icon()
        return super().leaveEvent(arg__1)

    def image(self, name, **kwargs):
        """
        Sets the name of the image to use by the tool button.

        :param str name: name of the icon to use.
        :return: itself instance.
        :rtype: BaseToolButton
        """

        self._image = name
        self._polish_icon(**kwargs)

        return self

    def tiny(self) -> BaseToolButton:
        """
        Sets tool button to tiny size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.theme_size = self._theme_pref.theme_data().TINY

        return self

    def small(self) -> BaseToolButton:
        """
        Sets tool button to small size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.theme_size = self._theme_pref.theme_data().SMALL

        return self

    def medium(self) -> BaseToolButton:
        """
        Sets tool button to medium size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.theme_size = self._theme_pref.theme_data().MEDIUM

        return self

    def large(self) -> BaseToolButton:
        """
        Sets tool button to large size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.theme_size = self._theme_pref.theme_data().LARGE

        return self

    def huge(self) -> BaseToolButton:
        """
        Sets tool button to huge size.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.theme_size = self._theme_pref.theme_data().HUGE

        return self

    def icon_only(self) -> BaseToolButton:
        """
        Sets tool button style to icon only.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(self.theme_size, self.theme_size)

        return self

    def text_only(self) -> BaseToolButton:
        """
        Sets tool button style to text only.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonTextOnly)

        return self

    def text_beside_icon(self) -> BaseToolButton:
        """
        Sets tool button style to text beside icon.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        return self

    def text_under_icon(self) -> BaseToolButton:
        """
        Sets tool button style to text under icon.

        :return: itself instance.
        :rtype: BaseToolButton
        """

        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        return self

    def _polish_icon(self, **kwargs):
        """
        Internal function that polishes button icon.
        """

        if self._image:
            theme_data = self._theme_pref.theme_data()
            accent_color = theme_data.ACCENT_COLOR
            if self.isCheckable() and self.isChecked():
                self.setIcon(resources.icon(self._image, color=accent_color))
            else:
                button_icon = resources.icon(self._image, **kwargs) if helpers.is_string(self._image) else self._image
                if button_icon and not button_icon.isNull():
                    self.setIcon(button_icon)

    def _get_theme_size(self) -> int:
        """
        Internal function that returns the button height size.

        :return: button height size.
        :rtype: int
        """

        return self._theme_size

    def _set_theme_size(self, value: int):
        """
        Sets button height size.

        :param int value: button height size.
        """

        self._theme_size = value
        self.style().polish(self)
        if self.toolButtonStyle() == Qt.ToolButtonIconOnly:
            self.setFixedSize(self._theme_size, self._theme_size)

    theme_size = Property(int, _get_theme_size, _set_theme_size)


class LeftAlignedButton(QPushButton):
    """
    Custom button that is left aligned with text and icon.
    """

    def __init__(
            self, text: str = '', icon: QIcon | None = None, tooltip: str | None = None, parent: QWidget | None = None):
        text = f' {text}' if text else text
        super().__init__(text, parent)

        self._mouse_buttons = {}			# type: Dict[Qt.MouseButton, QMenu]

        if icon is not None:
            self.setIcon(icon)
        if tooltip:
            self.setToolTip(tooltip)

        self.setStyleSheet(
            "QPushButton {} text-align: left; padding-left: {}px; {}".format("{", str(dpi.dpi_scale(7)), "}"))

    def menu(self, mouse_button: Qt.MouseButton = Qt.LeftButton) -> QMenu | None:
        """
        Returns the menu associated to the given mouse button.

        :param Qt.MouseButton mouse_button: mouse button.
        :return: menu for the given menu.
        :rtype: QMenu or None
        """

        return self._mouse_buttons.get(mouse_button, None)

    def set_menu(self, menu: QMenu, mouse_button: Qt.MouseButton):
        """
        Sets the given menu to the given mouse button.

        :param QMenu menu: menu to set to mouse button.
        :param Qt.MouseButton mouse_button: mouse button.
        """

        assert mouse_button in (Qt.LeftButton, Qt.RightButton), f'Unsupported mouse button: {mouse_button}'
        menu.setParent(self)
        self._mouse_buttons[mouse_button] = menu
        if mouse_button == Qt.RightButton:
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._on_custom_context_menu_requested)
        elif mouse_button == Qt.LeftButton:
            super().setMenu(menu)

    def create_menu_item(
            self, text: str = '', icon: str = '', connection: Callable | None = None,
            mouse_button: Qt.MouseButton = Qt.RightButton) -> QAction:
        """
        Creates a menu item to the specific mouse menu. If menu at given mouse button does not exists, it will be
        created.

        :param str text:  menu item text label.
        :param str icon: menu item icon.
        :param Callable or None connection: optional function that should be called when item is clicked by the user.
        :param Qt.MouseButton mouse_click: mouse button to create the menu item for.
        :return: menu item as an action instance.
        :rtype: QAction
        """

        menu = self.menu(mouse_button)
        if not menu:
            menu = QMenu(self)
            self.set_menu(menu, mouse_button)

        action = menu.addAction(text)
        icon_obj = QIcon(f'{icon}.png') if ':' in icon else resources.icon(icon) if icon else None
        if icon_obj:
            action.setIcon(icon_obj)

        if connection:
            action.triggered.connect(connection)

        return action

    def _on_custom_context_menu_requested(self, pos: QPoint):
        """
        Internal callback function that is called when button custom context menu is requested.

        :param QPoint pos: the position to show the context menu at.
        """

        menu = self._mouse_buttons[Qt.RightButton]
        menu.exec_(self.mapToGlobal(pos))
