from __future__ import annotations

from functools import partial

from overrides import override
from Qt.QtCore import Qt, Signal, QPoint, QSize, QTimer, QEvent
from Qt.QtWidgets import QWidget, QAbstractButton, QPushButton
from Qt.QtGui import QCursor, QFontMetrics, QIcon, QPainter

from tp.preferences.interfaces import core as core_interfaces
from tp.common.python import helpers
from tp.common.resources import icon, api as resources
from tp.common.qt import dpi
from tp.common.qt.widgets import layouts, menus


class AbstractButton(QAbstractButton, dpi.DPIScaling):
	"""
	Abstract class for all custom Qt buttons.
	Adds the ability to change button icon based on button press status.
	"""

	_idle_icon = None
	_pressed_icon = None
	_hover_icon = None
	_highlight_offset = 40
	_icon_names = list()
	_icon_colors = (200, 200, 200)
	_icon_scaling = list()

	@override
	def enterEvent(self, event: QEvent) -> None:
		if self._hover_icon is not None and self.isEnabled():
			self.setIcon(self._hover_icon)

	@override
	def leaveEvent(self, event: QEvent) -> None:
		if self._idle_icon is not None and self.isEnabled():
			self.setIcon(self._idle_icon)

	@override(check_signature=False)
	def setEnabled(self, flag: bool) -> None:
		super().setEnabled(flag)

		# force update of the icons after resizing
		self.update_icons()

	@override(check_signature=False)
	def setDisabled(self, flag: bool) -> None:
		super().setDisabled(flag)

		# force update of the icons after resizing
		self.update_icons()

	@override
	def setIconSize(self, size: QSize) -> None:
		super().setIconSize(dpi.size_by_dpi(size))

		# force update of the icons after resizing
		self.update_icons()

	def set_highlight(self, value):
		"""
		Sets the highlight offset of the icon.

		:param float value: highlight offset .
		"""

		self._highlight_offset = value

	def set_icon(self, icon_name, colors=None, size=None, color_offset=None, scaling=None, **kwargs):
		"""
		Set the icon of the button.

		:param str or QIcon icon_name: button icon.
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

		self._icon_names = icon_name
		self._grayscale = kwargs.pop('grayscale', False)
		self._tint_composition = kwargs.pop('tint_composition', QPainter.CompositionMode_Plus)
		colors = colors or self._icon_colors

		self.set_icon_color(colors, update=False)
		self.update_icons()

	def set_icon_idle(self, idle_icon, update=False):
		"""
		Sets the icon idle.

		:param QIcon idle_icon: idle icon.
		:param bool update: whether force icons update.
		"""

		self._idle_icon = idle_icon
		self.setIcon(idle_icon)
		if update:
			self.update_icons()

	def set_icon_hover(self, hover_icon, update=False):
		"""
		Sets the icon hover.

		:param QIcon hover_icon: hover icon.
		:param bool update: whether forece icons update.
		"""

		self._hover_icon = hover_icon
		if update:
			self.update_icons()

	def set_icon_color(self, colors, update=True):
		"""
		Set the color of the icon.

		:param QColor or list colors: icon color or colors
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

		self._idle_icon = icon.colorize_layered_icon(
			icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
			composition=self._tint_composition, colors=self._icon_colors, grayscale=grayscale)

		self._hover_icon = icon.colorize_layered_icon(
			icons=self._icon_names, size=self.iconSize().width(), scaling=self._icon_scaling,
			composition=self._tint_composition, colors=self._icon_colors, tint_color=hover_color, grayscale=grayscale)

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

		def keyPressEvent(self, event):
			if event.key() == self._key:
				pos = self.mapFromGlobal(QCursor.pos())
				action = self.actionAt(pos)
				if tooltip.has_custom_tooltips(action):
					self._popup_tooltip = tooltip.CustomTooltipPopup(
						action, icon_size=dpi.dpi_scale(40), popup_release=self._key)
				self._key_pressed = True
			super().keyPressEvent(event)

		def keyReleaseEvent(self, event):
			if event.key() == Qt.Key_Control:
				self._key_pressed = False

		def index(self, name, exclude_search=True):
			for i, action in enumerate(self.actions()):
				if action.text() == name:
					result = i
					if exclude_search:
						result -= 2
					return result

	def __init__(self, text='', icon=None, icon_hover=None, icon_color_theme=None, elided=False, theme_updates=True,
				 menu_padding=5, menu_align=Qt.AlignLeft, double_click_enabled=False, parent=None):

		self._idle_icon = icon or QIcon()
		self._hover_icon = icon_hover
		self._icon_color_theme = icon_color_theme
		self._text = text

		super().__init__(icon=self._idle_icon, text=self._text, parent=parent)

		self._menu_padding = menu_padding
		self._menu_align = menu_align
		self._double_click_interval = 500
		self._double_click_enabled = double_click_enabled
		self._last_click = None
		self._theme_updates_color = theme_updates
		self._elided = elided

		self._menu_active = {  # defines which menus are active
			Qt.LeftButton: True,
			Qt.MidButton: True,
			Qt.RightButton: True
		}
		self._click_menu = {  # stores available menus
			Qt.LeftButton: None,
			Qt.MidButton: None,
			Qt.RightButton: None
		}
		self._menu_searchable = {  # defines which menus are searchable
			Qt.LeftButton: False,
			Qt.MidButton: False,
			Qt.RightButton: False
		}

		self.leftClicked.connect(partial(self._on_context_menu, Qt.LeftButton))
		self.middleClicked.connect(partial(self._on_context_menu, Qt.MidButton))
		self.rightClicked.connect(partial(self._on_context_menu, Qt.RightButton))

		self._theme_pref = core_interfaces.theme_preference_interface()
		self._theme_pref.updated.connect(self.update_theme)

	@property
	def menu_align(self):
		return self._menu_align

	@menu_align.setter
	def menu_align(self, align=Qt.AlignLeft):
		self._menu_align = align

	@property
	def double_click_enabled(self):
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

		if not self.isCheckable():
			self.setDown(False)

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

	def setText(self, text):
		"""
		Overrides base setText function.

		:param str text: new button text.
		"""

		self._text = text
		super(BaseButton, self).setText(text)

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

	def actions(self, mouse_menu=Qt.LeftButton):
		"""
		Overrides base actions function to returns the actions of mouse button.

		:param Qt.Button mouse_menu: mouse button.
		:return: list of actions.
		:rtype: list(QAction)
		"""

		menu_instance = self._click_menu.get(mouse_menu, None)
		if menu_instance is None:
			return list()

		return menu_instance.actions()[2:]

	def setWindowTitle(self, window_title, mouse_menu=Qt.LeftButton):
		"""
		Overrides base setWindowTitle function to set the weindow title of the menu, if its get teared off.

		:param str window_title: window title
		:param Qt.Button mouse_menu: menu button
		"""

		menu = self.menu(mouse_menu, searchable=self.is_searchable(mouse_menu))
		menu.setWindowTitle(window_title)

	def setMenu(self, menu, mouse_button=Qt.LeftButton):
		"""
		Overrides base setMenu function to set the menu based on mouse button.

		:param QMenu menu: menu to set
		:param Qt.Button mouse_button: mouse button.
		"""

		self._click_menu[mouse_button] = menu

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
		:param bool checkable: whether menu item is checkable.
		:param bool checked: if checkable is True, whether menu item is checked by default.
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

		args = helpers.get_args(locals())

		found_menu = self.menu(mouse_menu, searchable=False)

		if action is not None:
			found_menu.addAction(action)
			return

		args.pop('action', None)
		new_action = self.new_action(**args)
		found_menu.addAction(new_action)

		return new_action

	def new_action(
			self, name, mouse_menu=Qt.LeftButton, connect=None, checkable=False, checked=True,
			action_icon=None, data=None, icon_text=None, icon_color=None, icon_size=16, tooltip=None):
		"""
		Creates a new menu item through an action.

		:param str name: text for the new menu item.
		:param Qt.LeftButton or Qt.RightButton or Qt.MidButton mouse_menu: mouse button.
		:param callable or None connect: function to connect when the menu item is pressed.
		:param bool checkable: whether menu item is checkable.
		:param bool checked: if checkable is True, whether menu item is checked by default.
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

		new_action = menus.SearchableTaggedAction(name, parent=found_menu)
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

	def add_separator(self, mouse_menu=Qt.LeftButton):
		"""
		Adds a new separator into the menu.

		:param Qt.Button mouse_menu: mouse button.
		"""

		found_menu = self.menu(mouse_menu)
		found_menu.addSeparator()

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

	def set_tearoff_enabled(self, mouse_menu=Qt.LeftButton, tearoff=True):
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
		:param UpdateThemeEVENT event: theme update event.
		"""

		print('agfasdfasdfasdf')

		if not self._theme_updates_color:
			return

		self._icon_color_theme = self._icon_color_theme or 'BUTTON_ICON_COLOR'
		if self._icon_color_theme:
			icon_color = getattr(event.theme_dict, self._icon_color_theme)
		else:
			icon_color = event.theme_dict.BUTTON_ICON_COLOR
		self.set_icon_color(icon_color)

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

	def clear_menu(self, mouse_menu=Qt.LeftButton):
		"""
		Clears all the menu items of the specified menu.

		:param Qt.LeftButton or Qt.MidButton or Qt.RightButton mouse_menu: mouse button.
		"""

		if self._click_menu[mouse_menu] is not None:
			self._click_menu[mouse_menu].clear()

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

	def _string_to_tags(self, string_to_convert):
		"""
		Internal function that converst given string into tags.

		:param str string_to_convert: string to convert.
		:return: string tags.
		:rtype: list[str]
		"""

		tags = list()
		tags += string_to_convert.split(' ')
		tags += [tag.lower() for tag in string_to_convert.split(' ')]

		return tags

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
			menu._search_edit.setFocus()

	def _on_menu_changed(self, mouse_button, *args, **kwargs):
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

	def __init__(self, icon=None, icon_hover=None, double_click_enabled=False, color=None, tint_color=None,
				 menu_name='', switch_icon_on_click=False, theme_updates=True, parent=None):
		super().__init__(
			icon=icon, icon_hover=icon_hover, double_click_enabled=double_click_enabled, theme_updates=theme_updates,
			parent=parent)

		self._tint_color = tint_color
		self._icon_color = color or (255, 255, 255)
		self._current_text = menu_name
		self._switch_icon = switch_icon_on_click

		self.setup_ui()

		self.actionTriggered.connect(self._on_menu_item_clicked)

	def text(self):
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

	def current_text(self):
		"""
		Returns the current selected menu name.

		:return: current menu name.
		:rtype: str
		"""

		return self._current_text

	def current_action(self, mouse_menu=Qt.LeftButton):
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

	def current_index(self, mouse_menu=Qt.LeftButton):
		"""
		Returns the current selected menu index.

		:param Qt.Button mouse_menu: mouse button.
		:return: current index menu item.
		:rtype: int
		"""

		return self.index(self.current_text(), mouse_menu)

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

	def _on_menu_item_clicked(self, action, mouse_menu):
		"""
		Internal callback function that is called each time a menu item is clicked by the user.

		:param QAction action: action clicked
		:param Qt.Button mouse_menu: mouse button.
		"""

		self.set_menu_name(action.text())


class OkCancelButtons(QWidget):

	okButtonPressed = Signal()
	cancelButtonPressed = Signal()

	def __init__(self, ok_text: str = 'OK', cancel_text: str = 'Cancel', parent: QWidget | None = None):
		super().__init__(parent=parent)

		self._main_layout = layouts.horizontal_layout()
		self._ok_button = QPushButton(ok_text, parent=self)
		self._cancel_button = QPushButton(cancel_text, parent=self)
		self._main_layout.addWidget(self._ok_button)
		self._main_layout.addWidget(self._cancel_button)

	def _setup_signals(self):
		"""
		Internal function that setup all the signals for this widget.
		"""

		self._ok_button.clicked.connect(self.okButtonPressed.emit)
		self._cancel_button.clicked.connect(self.cancelButtonPressed.emit)
