from __future__ import annotations

import enum
from typing import Any
from functools import partial

from Qt.QtCore import Qt, Signal, Property, QPoint, QSize, QTimer, QEvent
from Qt.QtWidgets import (
    QSizePolicy,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QToolButton,
    QAction,
    QMenu,
    QHBoxLayout,
    QGridLayout,
)
from Qt.QtGui import (
    QFontMetrics,
    QColor,
    QPixmap,
    QIcon,
    QPainter,
    QRegion,
    QResizeEvent,
    QMouseEvent,
    QKeyEvent,
)

from . import menus, labels
from ...resources.style import theme
from .. import dpi, icon, color, utils as qtutils


class AbstractButton(dpi.DPIScaling):
    """
    Abstract class for all custom Qt buttons.
    Adds the ability to change button icon based on button press status.
    """

    _idle_icon: QIcon | None = None
    _pressed_icon: QIcon | None = None
    _hover_icon: QIcon | None = None
    _highlight_offset = 40
    _icons: list[QIcon] = []
    _icon_colors = (128, 128, 128)
    _icon_scaling: list[float] = []

    def __init__(self):
        super().__init__()

        self._grayscale: bool = False
        self._tint_composition: QPainter.CompositionMode | None = None

    # noinspection PyUnresolvedReferences,PyPep8Naming,PyUnusedLocal
    def enterEvent(self, event: QEvent):
        if self._hover_icon is not None and self.isEnabled():
            self.setIcon(self._hover_icon)

    # noinspection PyUnresolvedReferences,PyPep8Naming,PyUnusedLocal
    def leaveEvent(self, event: QEvent):
        if self._idle_icon is not None and self.isEnabled():
            self.setIcon(self._idle_icon)

    # noinspection PyUnresolvedReferences,PyPep8Naming
    def setEnabled(self, flag: bool):
        super().setEnabled(flag)

        # force update of the icons after resizing
        self.update_icons()

    # noinspection PyUnresolvedReferences,PyPep8Naming
    def setDisabled(self, flag: bool):
        super().setDisabled(flag)

        # force update of the icons after resizing
        self.update_icons()

    # noinspection PyUnresolvedReferences,PyPep8Naming
    def setIconSize(self, size: QSize):
        super().setIconSize(dpi.size_by_dpi(size))

        # force update of the icons after resizing
        self.update_icons()

    def set_highlight(self, value: float):
        """
        Sets the highlight offset of the icon.

        :param value: highlight offset .
        """

        self._highlight_offset = value

    def set_icon(
        self,
        button_icon: QIcon,
        size: int | None = None,
        color_offset: float | None = None,
        scaling: list[int | float] = None,
        **kwargs,
    ):
        """
        Set the icon of the button.

        :param button_icon: button icon.
        :param size: icon size.
        :param color_offset: icon highlight offset.
        :param scaling: icon scaling.
        """

        if size is not None:
            self.setIconSize(QSize(size, size))
        if color_offset is not None:
            self._highlight_offset = color_offset
        if scaling is not None:
            self._icon_scaling = scaling

        self._icons = [button_icon]
        self._grayscale = kwargs.pop("grayscale", False)
        self._tint_composition = kwargs.pop(
            "tint_composition", QPainter.CompositionMode_Plus
        )
        self.update_icons()

    def set_icon_idle(self, idle_icon: QIcon, update: bool = False):
        """
        Sets the icon idle.

        :param idle_icon: idle icon.
        :param update: whether force icons update.
        """

        self._idle_icon = idle_icon
        # noinspection PyUnresolvedReferences
        self.setIcon(idle_icon)
        if update:
            self.update_icons()

    def set_icon_hover(self, hover_icon: QIcon, update: bool = False):
        """
        Sets the icon hover.

        :param hover_icon: hover icon.
        :param update: whether forces icons update.
        """

        self._hover_icon = hover_icon
        if update:
            self.update_icons()

    def set_icon_color(
        self, colors: QColor | tuple[int, int, int], update: bool = True
    ):
        """
        Set the color of the icon.

        :param colors: icon color or colors
        :param update: whether force icons update.
        """

        if type(self._icons) is list and len(self._icons) >= 2:
            icons = len(self._icons)
            if type(colors) is tuple and len(colors) == 3:
                colors = [colors for _ in range(icons)]

        self._icon_colors = colors

        if update and self._idle_icon is not None and self._icons is not None:
            self.update_icons()

    def update_icons(self):
        """
        Updates the button icons.
        """

        if not self._icons:
            return

        self._idle_icon = icon.colorize_layered_icon(
            icons=self._icons, scaling=self._icon_scaling
        )
        self._hover_icon = icon.colorize_layered_icon(
            icons=self._icons, scaling=self._icon_scaling
        )

        # noinspection PyUnresolvedReferences
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

    class Type(enum.Enum):
        """Enumerator that defines available push button types"""

        Default = "default"
        Primary = "primary"
        Success = "success"
        Warning = "warning"
        Danger = "danger"

    class BaseMenuButtonMenu(menus.SearchableMenu):
        """
        Custom menu that can be attached to BaseButton
        """

        def __init__(self, *args, **kwargs):
            super(BaseButton.BaseMenuButtonMenu, self).__init__(*args, **kwargs)

            self._key_pressed = False
            self._key = Qt.Key_Control

            self.setAttribute(Qt.WA_TranslucentBackground)

        # noinspection PyUnusedLocal
        def keyPressEvent(self, arg__1: QKeyEvent):
            if arg__1.key() == self._key:
                pass
                # pos = self.mapFromGlobal(QCursor.pos())
                # action = self.actionAt(pos)
                # if tooltip.has_custom_tooltips(action):
                #     self._popup_tooltip = tooltip.CustomTooltipPopup(
                #         action, icon_size=dpi.dpi_scale(40), popup_release=self._key)
                self._key_pressed = True
            super().keyPressEvent(arg__1)

        def keyReleaseEvent(self, event: QKeyEvent):
            if event.key() == Qt.Key_Control:
                self._key_pressed = False

        def index(self, name: str, exclude_search: bool = True) -> int:
            """
            Returns index of the button with given name within the menu.

            :param name: button name to get index of.
            :param exclude_search: whether to exclude search buttons.
            :return: index of the button.
            """

            for i, action in enumerate(self.actions()):
                if action.text() == name:
                    result = i
                    if exclude_search:
                        result -= 2
                    return result

    # noinspection PyDictCreation
    def __init__(
        self,
        text: str = "",
        button_icon: QIcon | None = None,
        icon_hover: QIcon | None = None,
        icon_color_theme: str | None = None,
        elided: bool = False,
        theme_updates: bool = True,
        menu_padding: int = 5,
        menu_align: Qt.AlignmentFlag = Qt.AlignLeft,
        double_click_enabled: bool = False,
        parent: QWidget | None = None,
    ):
        """
        Initialize a new instance of the class.

        :param text: The text to display. Default is an empty string.
        :param button_icon: The icon to display. Default is None.
        :param icon_hover: The icon to display when hovering. Default is None.
        :param icon_color_theme: The color theme for the icon. Default is None.
        :param elided: Whether to elide the text if it's too long. Default is False.
        :param theme_updates: Whether to update the theme dynamically. Default is True.
        :param menu_padding: The padding for the menu. Default is 5.
        :param menu_align: The alignment for the menu. Default is Qt.AlignLeft.
        :param double_click_enabled: Whether double-click is enabled. Default is False.
        :param parent: The parent widget, if any. Default is None, indicating no parent.
        """

        self._idle_icon = button_icon or QIcon()
        self._hover_icon = icon_hover or QIcon()
        self._icon_color_theme = icon_color_theme
        self._text = text
        self._type = BasePushButton.Type.Default.value
        self._size = theme.Theme.Sizes.Default.value
        self._size_value = theme.instance().sizes[self._size]

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

        # defines which menus are active
        self._menu_active: dict[Qt.MouseButton, bool] = {}
        self._menu_active[Qt.LeftButton] = True
        self._menu_active[Qt.MiddleButton] = True
        self._menu_active[Qt.RightButton] = True

        # stores available menus
        self._click_menu: dict[
            Qt.MouseButton, BaseButton.BaseMenuButtonMenu | None
        ] = {}
        self._click_menu[Qt.LeftButton] = None
        self._click_menu[Qt.MiddleButton] = None
        self._click_menu[Qt.RightButton] = None

        # defines which menus are searchable
        self._menu_searchable: dict[Qt.MouseButton, bool] = {}
        self._menu_searchable[Qt.LeftButton] = False
        self._menu_searchable[Qt.MiddleButton] = False
        self._menu_searchable[Qt.RightButton] = False

        self.leftClicked.connect(partial(self._on_context_menu, Qt.LeftButton))
        self.middleClicked.connect(partial(self._on_context_menu, Qt.MiddleButton))
        self.rightClicked.connect(partial(self._on_context_menu, Qt.RightButton))

        # self._theme_pref = core_interfaces.theme_preference_interface()
        # self._theme_pref.updated.connect(self.update_theme)

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

    def mousePressEvent(self, event: QMouseEvent):
        """
        Overrides mousePressEvent function.

        :param event: Qt mouse event.
        """

        if event.button() == Qt.MiddleButton:
            self.setDown(True)
        elif event.button() == Qt.RightButton:
            self.setDown(True)

        self._last_click = self.SINGLE_CLICK

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Overrides mouseReleaseEvent function.

        :param event: Qt mouse event.
        """

        button = event.button()

        if not self.isCheckable():
            self.setDown(False)

        if not self._double_click_enabled:
            self._mouse_single_click_action(button)
            super().mouseReleaseEvent(event)
            return

        if self._last_click == self.SINGLE_CLICK:
            QTimer.singleShot(
                self._double_click_interval,
                lambda: self._mouse_single_click_action(button),
            )
        else:
            self._mouse_double_click_action(button)

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """
        Overrides mouseDoubleClickEvent function.

        :param event: Qt mouse event.
        """

        self._last_click = self.DOUBLE_CLICK

    def resizeEvent(self, event: QResizeEvent):
        """
        Overrides resizeEvent function that adds elide functionality.

        :param event: Qt resize event.
        """

        if self._elided:
            has_icon = self.icon() and not self.icon().isNull()
            if has_icon:
                font_metrics = QFontMetrics(self.font())
                elided = font_metrics.elidedText(
                    self._text, Qt.ElideMiddle, self.width() - 30
                )
                super(BaseButton, self).setText(elided)

        super().resizeEvent(event)

    def setText(self, text: str):
        """
        Overrides base setText function.

        :param text: new button text.
        """

        self._text = text
        super(BaseButton, self).setText(text)

    def actions(self, mouse_menu: Qt.MouseButton = Qt.LeftButton) -> list[QAction]:
        """
        Overrides base actions function to returns the actions of mouse button.

        :param mouse_menu: mouse button.
        :return: list of actions.
        """

        menu_instance = self._click_menu.get(mouse_menu, None)
        if menu_instance is None:
            return list()

        return menu_instance.actions()[2:]

    def setWindowTitle(self, title: str, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Overrides base setWindowTitle function to set the window title of the menu, if its get teared off.

        :param title: window title
        :param mouse_menu: menu button
        """

        menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        menu.setWindowTitle(title)

    def setMenu(
        self, menu: BaseMenuButtonMenu, mouse_button: Qt.MouseButton = Qt.LeftButton
    ):
        """
        Overrides base setMenu function to set the menu based on mouse button.

        :param menu: menu to set
        :param mouse_button: mouse button.
        """

        self._click_menu[mouse_button] = menu

    def menu(
        self,
        mouse_menu: Qt.MouseButton = Qt.LeftButton,
        searchable: bool = False,
        auto_create: bool = True,
    ) -> BaseMenuButtonMenu:
        """
        Overrides base menu function to get menu depending on the mouse button pressed.

        :param mouse_menu: mouse button.
        :param searchable: whether menu is searchable.
        :param auto_create: whether to auto create menu if it does not exist yet.
        :return: requested menu.
        """

        if self._click_menu[mouse_menu] is None and auto_create:
            menu_button = BaseButton.BaseMenuButtonMenu(
                title="Menu Button", parent=self
            )
            menu_button.setObjectName("menuButton")
            menu_button.triggered.connect(
                lambda action: self.actionTriggered.emit(action, mouse_menu)
            )
            menu_button.triggered.connect(partial(self._on_menu_changed, mouse_menu))
            if not searchable:
                menu_button.set_search_visible(False)
            self._click_menu[mouse_menu] = menu_button

        return self._click_menu[mouse_menu]

    def addAction(
        self,
        name: str,
        mouse_menu: Qt.MouseButton = Qt.LeftButton,
        connect: callable = None,
        checkable: bool = False,
        checked: bool = True,
        action: QAction | None = None,
        action_icon: QIcon | str | None = None,
        data: Any = None,
        icon_text: str | None = None,
        icon_color: tuple[int, int, int] | None = None,
        icon_size=16,
        tooltip: str | None = None,
    ) -> QAction | None:
        """
        Adds a new menu item through an action.

        :param name: text for the new menu item.
        :param mouse_menu: mouse button.
        :param connect: function to connect when the menu item is pressed.
        :param checkable: whether menu item is checkable.
        :param checked: if checkable is True, whether menu item is checked by default.
        :param action: if given this is the action will be added directly without any extra steps.
        :param action_icon: icon for the menu item.
        :param data: custom data to store within the action.
        :param icon_text: text for the icon.
        :param icon_color: color of the menu item in 0-255 range.
        :param icon_size: size of the icon.
        :param tooltip: new menu item tooltip.
        :return: newly created action.
        """

        args = locals()
        args.pop("self", None)
        args.pop("__class__", None)

        found_menu = self.menu(mouse_menu, searchable=False)

        if action is not None:
            found_menu.addAction(action)
            return None

        args.pop("action", None)
        new_action = self.new_action(**args)
        found_menu.addAction(new_action)

        return new_action

    def new_action(
        self,
        name: str,
        mouse_menu: Qt.MouseButton = Qt.LeftButton,
        connect: callable = None,
        checkable: bool = False,
        checked: bool = True,
        action_icon: QIcon | None = None,
        data: Any = None,
        icon_text: str | None = None,
        tooltip: str | None = None,
    ):
        """
        Creates a new menu item through an action.

        :param name: text for the new menu item.
        :param mouse_menu: mouse button.
        :param connect: function to connect when the menu item is pressed.
        :param checkable: whether menu item is checkable.
        :param checked: if checkable is True, whether menu item is checked by default.
        :param action_icon: icon for the menu item.
        :param object data: custom data to store within the action.
        :param icon_text: text for the icon.
        :param tooltip: new menu item tooltip.
        :return: newly created action.
        """

        found_menu = self.menu(mouse_menu, searchable=False)

        new_action = menus.SearchableMenu.SearchableTaggedAction(
            name, parent=found_menu
        )
        new_action.setCheckable(checkable)
        new_action.setChecked(checked)
        new_action.tags = set(self._string_to_tags(name))
        new_action.setData(data)

        if tooltip:
            new_action.setToolTip(tooltip)

        if action_icon is not None:
            new_action.setIcon(action_icon)
            new_action.setIconText(icon_text or "")

        if connect is not None:
            if checkable:
                new_action.triggered.connect(partial(connect, new_action))
            else:
                new_action.triggered.connect(connect)

        return new_action

    def insert_action_index(
        self,
        index: int,
        name: str,
        mouse_menu: Qt.MouseButton = Qt.LeftButton,
        action: QAction | None = None,
        connect: callable = None,
        checkable: bool = False,
        checked: bool = True,
        action_icon: QIcon | None = None,
        data: Any = None,
        icon_text: str | None = None,
        tooltip: str | None = None,
    ) -> QAction | None:
        """
        Inserts action at given index.

        :param index: index to insert action into.
        :param  name: text for the new menu item.
        :param mouse_menu: mouse button.
        :param action: action to insert.
        :param connect: function to connect when the menu item is pressed.
        :param checkable: whether menu item is checkable.
        :param checked: if checkable is True, whether menu item is checked by default.
        :param action_icon: icon for the menu item.
        :param data: custom data to store within the action.
        :param icon_text: text for the icon.
        :param tooltip: new menu item tooltip.
        :return: inserted action.
        """

        menu = self.menu(mouse_menu, searchable=False)
        actions = self.actions(mouse_menu)
        before = actions[index]

        if action:
            menu.insertAction(before, action)
            return None

        new_action = self.new_action(
            name=name,
            mouse_menu=mouse_menu,
            connect=connect,
            checkable=checkable,
            checked=checked,
            action_icon=action_icon,
            data=data,
            icon_text=icon_text,
            tooltip=tooltip,
        )
        menu.insertAction(before, new_action)

        return new_action

    def add_separator(self, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Adds a new separator into the menu.

        :param mouse_menu: mouse button.
        """

        found_menu = self.menu(mouse_menu)
        found_menu.addSeparator()

    def insert_separator_index(
        self,
        index: int,
        mouse_menu: Qt.MouseButton | Qt.LeftButton,
        after_index: bool = False,
    ):
        """
        Inserts separator at given index.

        :param index: index to insert separator into.
        :param mouse_menu: mouse button.
        :param after_index: whether to insert separator after given index.
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

        :param mouse_menu: mouse button
        :return: True if the given mouse menu is searchable; False otherwise.
        """

        if self._click_menu[mouse_menu] is not None:
            return self._click_menu[mouse_menu].search_visible()

        return self._menu_searchable[mouse_menu]

    def set_searchable(
        self, mouse_menu: Qt.MouseButton = Qt.LeftButton, searchable: bool = True
    ):
        """
        Sets whether given menu is searchable.

        :param mouse_menu: mouse button.
        :param searchable: True to make menu searchable; False otherwise.
        """

        self._menu_searchable[mouse_menu] = searchable

        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].set_search_visible(searchable)

    # noinspection SpellCheckingInspection
    def set_tearoff_enabled(
        self, mouse_menu: Qt.MouseButton = Qt.LeftButton, tearoff: bool = True
    ):
        """
        Sets whether tear off is enabled for a specific menu.

        :param mouse_menu: mouse button.
        :param tearoff: True to enable tearoff; False otherwise.
        """

        found_menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
        found_menu.setTearOffEnabled(tearoff)

    # def update_theme(self, event):
    #
    #     if not self._theme_updates_color:
    #         return
    #
    #     self._icon_color_theme = self._icon_color_theme or 'BUTTON_ICON_COLOR'
    #     if self._icon_color_theme:
    #         icon_color = getattr(event.theme_dict, self._icon_color_theme)
    #     else:
    #         icon_color = event.theme_dict.BUTTON_ICON_COLOR
    #     self.set_icon_color(icon_color)

    def menu_pos(
        self, align: Qt.AlignmentFlag = Qt.AlignLeft, widget: QWidget | None = None
    ) -> QPoint:
        """
        Returns the menu position based on the current position and perimeter.

        :param align: align the menu left or right.
        :param widget: widget used to calculate the width based off. Usually it is the menu itself.
        :return: position of the menu.
        """

        pos = 0

        if align == Qt.AlignLeft:
            point = self.rect().bottomLeft() - QPoint(0, -self._menu_padding)
            pos = self.mapToGlobal(point)
        elif align == Qt.AlignRight:
            point = self.rect().bottomRight() - QPoint(
                widget.sizeHint().width(), -self._menu_padding
            )
            pos = self.mapToGlobal(point)

        return pos

    def index(self, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Returns the index of the menu item or action name.

        :param name: name of menu item.
        :param mouse_menu: mouse button.
        :return: index of the menu.
        """

        return self.menu(mouse_menu).index(name)

    def clear_menu(self, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Clears all the menu items of the specified menu.

        :param mouse_menu: mouse button.
        """

        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].clear()

    def primary(self) -> BaseButton:
        """Sets push button style to primary.

        :return: current push button instance.
        """

        self._set_type(BaseButton.Type.Primary.value)
        return self

    def success(self) -> BaseButton:
        """Sets push button style to success.

        :return: current push button instance.
        """

        self._set_type(BaseButton.Type.Success.value)
        return self

    def warning(self) -> BaseButton:
        """Sets push button style to warning.

        :return: current push button instance.
        """

        self._set_type(BaseButton.Type.Warning.value)
        return self

    def danger(self) -> BaseButton:
        """Sets push button style to danger.

        :return: current push button instance.
        """

        self._set_type(BaseButton.Type.Danger.value)
        return self

    def tiny(self) -> BaseButton:
        """Sets push button size to tiny.

        :return: current push button instance.
        """

        self._set_size(theme.Theme.Sizes.Tiny.value)
        return self

    def small(self) -> BaseButton:
        """Sets push button size to small.

        :return: current push button instance.
        """

        self._set_size(theme.Theme.Sizes.Small.value)
        return self

    def medium(self) -> BaseButton:
        """Sets push button size to medium.

        :return: current push button instance.
        """

        self._set_size(theme.Theme.Sizes.Medium.value)
        return self

    def large(self) -> BaseButton:
        """Sets push button size to large.

        :return: current push button instance.
        """

        self._set_size(theme.Theme.Sizes.Large.value)
        return self

    def huge(self) -> BaseButton:
        """Sets push button size to huge.

        :return: current push button instance.
        """

        self._set_size(theme.Theme.Sizes.Huge.value)
        return self

    def set_size(self, value: int):
        """Sets tool button custom size.

        :param value: button size.
        """

        self._size_value = value
        self.setFixedHeight(self._size_value)

    def _mouse_single_click_action(self, mouse_button: Qt.MouseButton) -> bool:
        """
        Internal function that is called when a single click is triggered.

        :param mouse_button: pressed button.
        :return: True if mouse was clicked; False otherwise.
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

        :param mouse_button: pressed button
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

        :param mouse_button: mouse button.
        """

        if mouse_button == Qt.LeftButton:
            self.menuAboutToShow.emit()
        elif mouse_button == Qt.MiddleButton:
            self.middleMenuAboutToShow.emit()
        elif mouse_button == Qt.RightButton:
            self.rightMenuAboutToShow.emit()

    @staticmethod
    def _string_to_tags(string_to_convert: str) -> list[str]:
        """
        Internal function that converts given string into tags.

        :param string_to_convert: string to convert.
        :return: string tags.
        """

        tags: list[str] = []
        tags += string_to_convert.split(" ")
        tags += [tag.lower() for tag in string_to_convert.split(" ")]

        return tags

    def _get_type(self) -> str:
        """Internal function that returns push button type.

        Returns:
            str: push button type.
        """

        return self._type

    def _set_type(self, value: str):
        """Sets push button type.

        Args:
            value (str): push button type.
        """

        if value in [
            BaseButton.Type.Default.value,
            BaseButton.Type.Primary.value,
            BaseButton.Type.Success.value,
            BaseButton.Type.Warning.value,
            BaseButton.Type.Danger.value,
        ]:
            self._type = value
        else:
            raise ValueError(
                'Input argument "value" should be: "default", "primary", "success", "warning" or "danger"'
            )

    def _get_size(self) -> str:
        """Internal function that returns push button size.

        Returns:
            str: push button size.
        """

        return self._size

    def _set_size(self, value: str):
        """Internal function that sets push button size.

        Args:
            value (str): new push button size.
        """

        self._size = value
        self._size_value = theme.instance().sizes[self._size]
        self.setFixedHeight(self._size_value)

    type = Property(str, _get_type, _set_type)
    size = Property(int, _get_size, _set_size)

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
            # noinspection PyProtectedMember
            menu._search_edit.setFocus()

    # noinspection PyUnusedLocal
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

        qtutils.set_stylesheet_object_name(self, "DefaultButton")


class BaseToolButton(QToolButton):
    def __init__(self, tooltip: str | None = None, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._image: QIcon | None = None
        self._theme = theme.instance()

        self.setAutoExclusive(False)
        self.setAutoRaise(True)

        self._polish_icon()
        self.toggled.connect(self._polish_icon)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        if tooltip:
            self.setToolTip(tooltip)

        self._theme_size = self._theme.sizes.default

    def enterEvent(self, arg__1: QEvent) -> None:
        if self._image:
            accent_color = self._theme.primary_color
            self.setIcon(
                icon.colorize_icon(self._image, color=color.from_string(accent_color))
            )
        return super().enterEvent(arg__1)

    def leaveEvent(self, arg__1: QEvent) -> None:
        self._polish_icon()
        return super().leaveEvent(arg__1)

    def image(self, image_icon: QIcon, **kwargs):
        """
        Sets the name of the image to use by the tool button.

        :param image_icon: name of the icon to use.
        :return: itself instance.
        """

        self._image = image_icon
        self._polish_icon(**kwargs)

        return self

    def tiny(self) -> BaseToolButton:
        """
        Sets tool button to tiny size.

        :return: itself instance.
        """

        self.theme_size = self._theme.sizes.tiny

        return self

    def small(self) -> BaseToolButton:
        """
        Sets tool button to small size.

        :return: itself instance.
        """

        self.theme_size = self._theme.sizes.small

        return self

    def medium(self) -> BaseToolButton:
        """
        Sets tool button to medium size.

        :return: itself instance.
        """

        self.theme_size = self._theme.sizes.medium

        return self

    def large(self) -> BaseToolButton:
        """
        Sets tool button to large size.

        :return: itself instance.
        """

        self.theme_size = self._theme.sizes.large

        return self

    def huge(self) -> BaseToolButton:
        """
        Sets tool button to huge size.

        :return: itself instance.
        """

        self.theme_size = self._theme.sizes.huge

        return self

    def icon_only(self) -> BaseToolButton:
        """
        Sets tool button style to icon only.

        :return: itself instance.
        """

        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(self.theme_size, self.theme_size)

        return self

    def text_only(self) -> BaseToolButton:
        """
        Sets tool button style to text only.

        :return: itself instance.
        """

        self.setToolButtonStyle(Qt.ToolButtonTextOnly)

        return self

    def text_beside_icon(self) -> BaseToolButton:
        """
        Sets tool button style to text beside icon.

        :return: itself instance.
        """

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        return self

    def text_under_icon(self) -> BaseToolButton:
        """
        Sets tool button style to text under icon.

        :return: itself instance.
        """

        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        return self

    # noinspection PyUnusedLocal
    def _polish_icon(self, **kwargs):
        """
        Internal function that polishes button icon.
        """

        if self._image and not self._image.isNull():
            accent_color = self._theme.primary_color
            if self.isCheckable() and self.isChecked():
                self.setIcon(
                    icon.colorize_icon(
                        self._image, color=color.from_string(accent_color)
                    )
                )
            else:
                self.setIcon(self._image)

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


class IconMenuButton(BaseButton):
    """
    Custom menu that represents a button with an icon (no text). Clicking it will pop up a context menu.
    """

    def __init__(
        self,
        button_icon: QIcon | str | None = None,
        icon_hover: QIcon | str | None = None,
        double_click_enabled: bool = False,
        button_color: tuple[int, int, int] | None = None,
        tint_color: tuple[int, int, int] | None = None,
        menu_name: str = "",
        switch_icon_on_click: bool = False,
        theme_updates: bool = True,
        parent: QWidget | None = None,
    ):
        """
        Initialize a new instance of the class.

        :param button_icon: The icon for the button, either as a QIcon or a string path. Default is None.
        :param icon_hover: The icon to display when hovering, either as a QIcon or a string path. Default is None.
        :param double_click_enabled: Whether double-click is enabled. Default is False.
        :param button_color: The color of the button as an (R, G, B) tuple. Default is None.
        :param tint_color: The tint color for the button as an (R, G, B) tuple. Default is None.
        :param menu_name: The name of the menu. Default is an empty string.
        :param switch_icon_on_click: Whether to switch the icon on click. Default is False.
        :param theme_updates: Whether to update the theme dynamically. Default is True.
        :param parent: The parent widget, if any. Default is None, indicating no parent.
        """

        super().__init__(
            button_icon=button_icon,
            icon_hover=icon_hover,
            double_click_enabled=double_click_enabled,
            theme_updates=theme_updates,
            parent=parent,
        )

        self._tint_color = tint_color
        self._icon_color = button_color or (255, 255, 255)
        self._current_text = menu_name
        self._switch_icon = switch_icon_on_click

        self.setup_ui()

        self.actionTriggered.connect(self._on_menu_item_clicked)

    def text(self) -> str:
        """
        Overrides base text function.

        :return: menu name.
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
        """

        return self._current_text

    def current_action(
        self, mouse_menu: Qt.MouseButton = Qt.LeftButton
    ) -> QAction | None:
        """
        Returns current action.

        :param mouse_menu: mouse button.
        :return: current action.
        """

        for action in self.actions(mouse_menu):
            if action.text() == self._current_text:
                return action

        return None

    def current_index(self, mouse_menu: Qt.MouseButton = Qt.LeftButton) -> int:
        """
        Returns the current selected menu index.

        :param mouse_menu: mouse button.
        :return: current index menu item.
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
                # if self._switch_icon:
                #     icon_name = action.iconText()
                #     action_icon = resources.icon(icon_name)
                #     self.set_icon(action_icon, colors=self._icon_color)
                break

    def action_connect_list(
        self, actions: list[tuple[str, str]], mouse_menu: Qt.MouseButton = Qt.LeftButton
    ):
        """
        Creates the entire menu with the info contained within the actions list.

        :param actions: list of actions. Eg: [('icon1', 'menuName1'), (...), ...]
        :param mouse_menu: button that will open the menu.
        """

        for action in actions:
            self.addAction(action[1], mouse_menu=mouse_menu, action_icon=action[0])
        first_name = actions[0][1]
        self.set_menu_name(first_name)

    # noinspection PyUnusedLocal
    def _on_menu_item_clicked(self, action: QAction, mouse_menu: Qt.MouseButton):
        """
        Internal callback function that is called each time a menu item is clicked by the user.

        :param action: action clicked
        :param mouse_menu: mouse button.
        """

        self.set_menu_name(action.text())


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
        self,
        text: str | None = None,
        button_icon: QIcon | None = None,
        method: int = RenderingMethod.STYLESHEET,
        tooltip="",
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        if text:
            self.setText(text)
        if button_icon:
            self.setIcon(button_icon)

        self._method = method
        self._custom_style = ""
        self.setToolTip(tooltip)

        self._update_button()

    def resizeEvent(self, event: QResizeEvent):
        self._update_button()
        super().resizeEvent(event)

    def setStyleSheet(self, text: str):
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
        :param method: render method to use.
        """

        self._method = method
        self._update_button()

    def _round_style(self) -> str:
        """
        Internal function that returns custom rounded stylesheet string.

        :return: rounded stylesheet string.
        """

        radius = min(self.rect().width() * 0.5, self.rect().height() * 0.5) - 1.0
        return "border-radius: {}px;".format(radius)

    def _update_button(self):
        """
        Internal function that updates the button drawing.
        """

        if self._method == self.RenderingMethod.MASK:
            self.setMask(QRegion(self.rect(), QRegion.Ellipse))
        else:
            super().setStyleSheet(self._round_style() + self._custom_style)


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


class ShadowedButton(BaseButton):
    """
    Custom button with shadow indicator.
    """

    _MENU_INDICATOR_ICON = "menu_indicator"

    def __init__(
        self,
        text: str = "",
        shadow_height: int = 4,
        force_upper: bool = False,
        tooltip: str = "",
        icon_color_theme: str | None = None,
        theme_updates: bool = True,
        parent: QWidget | None = None,
    ):
        super(ShadowedButton, self).__init__(
            icon_color_theme=icon_color_theme,
            theme_updates=theme_updates,
            parent=parent,
        )

        self._main_layout: QGridLayout | None = None
        self._text_label: QLabel | None = None
        self._image_widget: ShadowedButtonImage | None = None
        self._shadow: ShadowedButtonShadow | None = None
        self._spacing_widget: QWidget | None = None
        self._force_upper = force_upper
        self._mouse_entered = True
        self._icon_pixmap: QPixmap | None = None
        self._icon_hovered_pixmap: QPixmap | None = None
        self._icon_pressed_pixmap: QPixmap | None = None
        self._is_menu = True
        self._icon_size = dpi.size_by_dpi(QSize(16, 16))
        self._icon_names: list[str] = []

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

    def setFixedHeight(self, height: int):
        self.update_image_widget(height)
        super().setFixedHeight(height)

    # noinspection PyMethodOverriding
    def setFixedSize(self, size: QSize):
        self.update_image_widget(size.height())
        super(ShadowedButton, self).setFixedSize(size)

    def setText(self, text: str):
        if not self._text_label:
            return
        if self._force_upper and text is not None:
            text = text.upper()

        self._text_label.setText(text)

    def setIconSize(self, size: QSize):
        self._icon_size = dpi.size_by_dpi(size)
        self._image_widget.setFixedSize(self._icon_size)

    def enterEvent(self, event: QEvent):
        self._mouse_entered = True
        qtutils.set_stylesheet_object_name(self, "")
        qtutils.set_stylesheet_object_name(self._shadow, "buttonShadowHover")
        qtutils.set_stylesheet_object_name(self._image_widget, "shadowedImageHover")
        qtutils.set_stylesheet_object_name(self._text_label, "shadowedLabelHover")
        self._image_widget.setPixmap(self._icon_hovered_pixmap)

    def leaveEvent(self, event: QEvent):
        self._mouse_entered = False
        qtutils.set_stylesheet_object_name(self, "")
        qtutils.set_stylesheet_object_name(self._shadow, "")
        qtutils.set_stylesheet_object_name(self._image_widget, "")
        qtutils.set_stylesheet_object_name(self._text_label, "")
        self._image_widget.setPixmap(self._icon_pixmap)

    def mousePressEvent(self, e: QMouseEvent):
        qtutils.set_stylesheet_object_name(self, "shadowedButtonPressed")
        qtutils.set_stylesheet_object_name(self._shadow, "buttonShadowPressed")
        qtutils.set_stylesheet_object_name(self._image_widget, "shadowedImagePressed")
        qtutils.set_stylesheet_object_name(self._text_label, "shadowedLabelPressed")
        self._image_widget.setPixmap(self._icon_pressed_pixmap)

        return super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent):
        # if mouse still entered while mouse released then set it back to hovered style
        if self._mouse_entered:
            self.enterEvent(e)

        return super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        event.ignore()
        return super().mouseDoubleClickEvent(event)

    # def update_theme(self, event):
    #     if self._theme_updates_color:
    #         self._icon_color_theme = self._icon_color_theme or '$BUTTON_ICON_COLOR'

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

        :param flag: whether to force text upper case.
        """

        self._force_upper = flag

    def set_shadow_height(self, height: int):
        """
        Sets the shadow height in pixels.

        :param height: shadow height (in pixels).
        """

        self._shadow.setFixedHeight(height)

    def set_icon(
        self,
        icons: QIcon | list[QIcon],
        colors: QColor | None = None,
        hover_colors: QColor | None = None,
        size: int | None = None,
        pressed_colors: QColor | None = None,
        scaling: tuple[float, float, float] | None = None,
    ):
        """
        Set button icon.

        :param icons: icon to set.
        :param colors: optional icon color.
        :param hover_colors: optional hover icon color.
        :param size: optional icon size.
        :param pressed_colors: optional icon pressed colors.
        :param scaling: optional scaling.
        """

        if size is not None:
            self.setIconSize(QSize(size, size))

        hover_colors = hover_colors or colors
        pressed_colors = pressed_colors or colors

        colors = [colors]
        hover_color = [hover_colors]
        pressed_color = [pressed_colors]

        self._icon_names = icons

        if self._is_menu:
            self._icon_names = [icons, self._MENU_INDICATOR_ICON]
            colors += colors
            hover_color += hover_color
            pressed_color += pressed_color

        new_size = self._icon_size.width()
        self._icon_pixmap = icon.colorize_layered_icon(
            self._icon_names, colors=colors, scaling=scaling
        ).pixmap(QSize(new_size, new_size))
        self._icon_hovered_pixmap = icon.colorize_layered_icon(
            self._icon_names, colors=hover_color, scaling=scaling
        ).pixmap(QSize(new_size, new_size))
        self._icon_pressed_pixmap = icon.colorize_layered_icon(
            self._icon_names, colors=pressed_color, scaling=scaling
        ).pixmap(QSize(new_size, new_size))

        self._image_widget.setPixmap(self._icon_pixmap)

    def update_image_widget(self, new_height: int):
        """
        Updates button to make sure widget is always square.

        :param new_height: new height of the widget to update to.
        """

        self._image_widget.setFixedSize(QSize(new_height, new_height))
        self._spacing_widget.setFixedWidth(int(dpi.dpi_scale(new_height) * 0.5))


class LabelSmallButton(QWidget):
    clicked = Signal()

    def __init__(
        self,
        text: str = "",
        button_icon: QIcon | None = None,
        tooltip: str = "",
        text_caps: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._text = text
        if text:
            self._label = labels.BaseLabel(text=text, tooltip=tooltip, upper=text_caps)

        self._button = BaseButton(text="", button_icon=button_icon, parent=self)

        button_layout = QHBoxLayout()
        self.setLayout(button_layout)

        if text:
            button_layout.addWidget(self._label, 5)
        button_layout.addWidget(self._button)

        self._setup_signals()

    def setDisabled(self, flag: bool):
        """
        Overrides base setDisabled function.

        :param flag: whether to disable the button.
        """

        self._button.setDisabled(flag)
        if self._text:
            self._label.setDisabled(flag)

    def _setup_signals(self):
        """
        Internal function that sets up signals.
        """

        self._button.clicked.connect(self._on_button_clicked)

    def _on_button_clicked(self):
        """
        Internal callback function that is called when button is clicked.
        """

        self.clicked.emit()


class LeftAlignedButton(QPushButton):
    """
    Custom button that is left aligned with text and icon.
    """

    def __init__(
        self,
        text: str = "",
        button_icon: QIcon | None = None,
        tooltip: str | None = None,
        parent: QWidget | None = None,
    ):
        text = f" {text}" if text else text
        super().__init__(text, parent)

        self._mouse_buttons: dict[Qt.MouseButton, QMenu] = {}

        if button_icon is not None:
            self.setIcon(button_icon)
        if tooltip:
            self.setToolTip(tooltip)

        self.setStyleSheet(
            "QPushButton {} text-align: left; padding-left: {}px; {}".format(
                "{", str(dpi.dpi_scale(7)), "}"
            )
        )

    def menu(self, mouse_button: Qt.MouseButton = Qt.LeftButton) -> QMenu | None:
        """
        Returns the menu associated to the given mouse button.

        :param mouse_button: mouse button.
        :return: menu for the given menu.
        """

        return self._mouse_buttons.get(mouse_button, None)

    def set_menu(self, menu: QMenu, mouse_button: Qt.MouseButton):
        """
        Sets the given menu to the given mouse button.

        :param menu: menu to set to mouse button.
        :param mouse_button: mouse button.
        """

        assert mouse_button in (
            Qt.LeftButton,
            Qt.RightButton,
        ), f"Unsupported mouse button: {mouse_button}"
        menu.setParent(self)
        self._mouse_buttons[mouse_button] = menu
        if mouse_button == Qt.RightButton:
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(
                self._on_custom_context_menu_requested
            )
        elif mouse_button == Qt.LeftButton:
            super().setMenu(menu)

    def create_menu_item(
        self,
        text: str = "",
        menu_item_icon: QIcon | None = None,
        connection: callable = None,
        mouse_button: Qt.MouseButton = Qt.RightButton,
    ) -> QAction:
        """
        Creates a menu item to the specific mouse menu. If menu at given mouse button does not exist, it will be
        created.

        :param text:  menu item text label.
        :param menu_item_icon: menu item icon.
        :param connection: optional function that should be called when item is clicked by the user.
        :param mouse_button: mouse button to create the menu item for.
        :return: menu item as an action instance.
        :rtype: QAction
        """

        menu = self.menu(mouse_button)
        if not menu:
            menu = QMenu(self)
            self.set_menu(menu, mouse_button)

        action = menu.addAction(text)
        if menu_item_icon:
            action.setIcon(menu_item_icon)

        if connection:
            action.triggered.connect(connection)

        return action

    def _on_custom_context_menu_requested(self, pos: QPoint):
        """
        Internal callback function that is called when button custom context menu is requested.

        :param pos: the position to show the context menu at.
        """

        menu = self._mouse_buttons[Qt.RightButton]
        menu.exec_(self.mapToGlobal(pos))


class OkCancelButtons(QWidget):
    """
    Custom widget that contains Ok and Cancel buttons.
    """

    okPressed = Signal()
    cancelPressed = Signal()

    def __init__(
        self,
        ok_text: str = "Ok",
        cancel_text: str = "Cancel",
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)
        self._ok_button = BasePushButton(ok_text, parent=self)
        self._cancel_button = BasePushButton(cancel_text, parent=self)
        self.main_layout.addWidget(self._ok_button)
        self.main_layout.addWidget(self._cancel_button)

        self._ok_button.clicked.connect(self.okPressed.emit)
        self._cancel_button.clicked.connect(self.cancelPressed.emit)

    @property
    def ok_button(self) -> BasePushButton:
        """
        Getter method that returns the Ok button.

        :return: Ok button.
        """

        return self._ok_button

    @property
    def cancel_button(self) -> BasePushButton:
        """
        Getter method that returns the Cancel button.

        :return: Cancel button.
        """

        return self._cancel_button
