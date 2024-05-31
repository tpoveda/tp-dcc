from __future__ import annotations

from typing import Any
from functools import partial

from . import menus
from .. import dpi, icon
from ...externals.Qt.QtCore import Qt, Signal, QPoint, QSize, QTimer, QEvent
from ...externals.Qt.QtWidgets import QWidget, QPushButton, QAction
from ...externals.Qt.QtGui import QFontMetrics, QCursor, QColor, QIcon, QPainter, QResizeEvent, QMouseEvent, QKeyEvent


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
            self, button_icon: QIcon,
            size: int | None = None, color_offset: float | None = None, scaling: list[float, float] = None, **kwargs):
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
        self._grayscale = kwargs.pop('grayscale', False)
        self._tint_composition = kwargs.pop('tint_composition', QPainter.CompositionMode_Plus)
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

    def set_icon_color(self, colors: QColor | tuple[int, int, int], update: bool = True):
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

        self._idle_icon = icon.colorize_layered_icon(icons=self._icons, scaling=self._icon_scaling)
        self._hover_icon = icon.colorize_layered_icon(icons=self._icons,  scaling=self._icon_scaling)

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
                pos = self.mapFromGlobal(QCursor.pos())
                action = self.actionAt(pos)
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
            self, text: str = '', button_icon: QIcon | None = None, icon_hover: QIcon | None = None,
            icon_color_theme: str | None = None, elided: bool = False, theme_updates: bool = True,
            menu_padding: int = 5, menu_align: Qt.AlignmentFlag = Qt.AlignLeft, double_click_enabled: bool = False,
            parent: QWidget | None = None):
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
        self._click_menu: dict[Qt.MouseButton, BaseButton.BaseMenuButtonMenu | None] = {}
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
            QTimer.singleShot(self._double_click_interval, lambda: self._mouse_single_click_action(button))
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
                elided = font_metrics.elidedText(self._text, Qt.ElideMiddle, self.width() - 30)
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

    def setMenu(self, menu: BaseMenuButtonMenu, mouse_button: Qt.MouseButton = Qt.LeftButton):
        """
        Overrides base setMenu function to set the menu based on mouse button.

        :param menu: menu to set
        :param mouse_button: mouse button.
        """

        self._click_menu[mouse_button] = menu

    def menu(
            self, mouse_menu: Qt.MouseButton = Qt.LeftButton, searchable: bool = False,
            auto_create: bool = True) -> BaseMenuButtonMenu:
        """
        Overrides base menu function to get menu depending on the mouse button pressed.

        :param mouse_menu: mouse button.
        :param searchable: whether menu is searchable.
        :param auto_create: whether to auto create menu if it does not exist yet.
        :return: requested menu.
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

    def addAction(
            self, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton, connect: callable = None,
            checkable: bool = False, checked: bool = True, action: QAction | None = None,
            action_icon: QIcon | str | None = None, data: Any = None, icon_text: str | None = None,
            icon_color: tuple[int, int, int] | None = None, icon_size=16, tooltip: str | None = None) -> QAction | None:
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
        args.pop('self', None)
        args.pop('__class__', None)

        found_menu = self.menu(mouse_menu, searchable=False)

        if action is not None:
            found_menu.addAction(action)
            return None

        args.pop('action', None)
        new_action = self.new_action(**args)
        found_menu.addAction(new_action)

        return new_action

    def new_action(
            self, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton, connect: callable = None,
            checkable: bool = False, checked: bool = True, action_icon: QIcon | None = None, data: Any = None,
            icon_text: str | None = None, tooltip: str | None = None):
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

        new_action = menus.SearchableMenu.SearchableTaggedAction(name, parent=found_menu)
        new_action.setCheckable(checkable)
        new_action.setChecked(checked)
        new_action.tags = set(self._string_to_tags(name))
        new_action.setData(data)

        if tooltip:
            new_action.setToolTip(tooltip)

        if action_icon is not None:
            new_action.setIcon(action_icon)
            new_action.setIconText(icon_text or '')

        if connect is not None:
            if checkable:
                new_action.triggered.connect(partial(connect, new_action))
            else:
                new_action.triggered.connect(connect)

        return new_action

    def insert_action_index(
            self, index: int, name: str, mouse_menu: Qt.MouseButton = Qt.LeftButton,
            action: QAction | None = None, connect: callable = None, checkable: bool = False, checked: bool = True,
            action_icon: QIcon | None = None, data: Any = None, icon_text: str | None = None,
            tooltip: str | None = None) -> QAction | None:
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
            name=name, mouse_menu=mouse_menu, connect=connect, checkable=checkable, checked=checked,
            action_icon=action_icon, data=data, icon_text=icon_text, tooltip=tooltip)
        menu.insertAction(before, new_action)

        return new_action

    def add_separator(self, mouse_menu: Qt.MouseButton = Qt.LeftButton):
        """
        Adds a new separator into the menu.

        :param mouse_menu: mouse button.
        """

        found_menu = self.menu(mouse_menu)
        found_menu.addSeparator()

    def insert_separator_index(self, index: int, mouse_menu: Qt.MouseButton | Qt.LeftButton, after_index: bool = False):
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

    def set_searchable(self, mouse_menu: Qt.MouseButton = Qt.LeftButton, searchable: bool = True):
        """
        Sets whether given menu is searchable.

        :param mouse_menu: mouse button.
        :param searchable: True to make menu searchable; False otherwise.
        """

        self._menu_searchable[mouse_menu] = searchable

        if self._click_menu[mouse_menu] is not None:
            self._click_menu[mouse_menu].set_search_visible(searchable)

    # noinspection SpellCheckingInspection
    def set_tearoff_enabled(self, mouse_menu: Qt.MouseButton = Qt.LeftButton, tearoff: bool = True):
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

    def menu_pos(self, align: Qt.AlignmentFlag = Qt.AlignLeft, widget: QWidget | None = None) -> QPoint:
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
            point = self.rect().bottomRight() - QPoint(widget.sizeHint().width(), -self._menu_padding)
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


class IconMenuButton(BaseButton):
    """
    Custom menu that represents a button with an icon (no text). Clicking it will pop up a context menu.
    """

    def __init__(
            self, button_icon: QIcon | str | None = None, icon_hover: QIcon | str | None = None,
            double_click_enabled: bool = False, color: tuple[int, int, int] | None = None,
            tint_color: tuple[int, int, int] | None = None, menu_name: str = '', switch_icon_on_click: bool = False,
            theme_updates: bool = True, parent: QWidget | None = None):
        """
        Initialize a new instance of the class.

        :param button_icon: The icon for the button, either as a QIcon or a string path. Default is None.
        :param icon_hover: The icon to display when hovering, either as a QIcon or a string path. Default is None.
        :param double_click_enabled: Whether double-click is enabled. Default is False.
        :param color: The color of the button as an (R, G, B) tuple. Default is None.
        :param tint_color: The tint color for the button as an (R, G, B) tuple. Default is None.
        :param menu_name: The name of the menu. Default is an empty string.
        :param switch_icon_on_click: Whether to switch the icon on click. Default is False.
        :param theme_updates: Whether to update the theme dynamically. Default is True.
        :param parent: The parent widget, if any. Default is None, indicating no parent.
        """

        super().__init__(
            button_icon=button_icon, icon_hover=icon_hover, double_click_enabled=double_click_enabled,
            theme_updates=theme_updates, parent=parent)

        self._tint_color = tint_color
        self._icon_color = color or (255, 255, 255)
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

    def current_action(self, mouse_menu: Qt.MouseButton = Qt.LeftButton) -> QAction | None:
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

    def action_connect_list(self, actions: list[tuple[str, str]], mouse_menu: Qt.MouseButton = Qt.LeftButton):
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
