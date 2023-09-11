#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes that extends default behaviour of QMenu
"""

from __future__ import annotations

from functools import partial
from typing import Tuple, List, Set, Callable

from overrides import override
from Qt.QtCore import Qt, Signal, QPoint
from Qt.QtWidgets import QWidget, QMenu, QAction, QWidgetAction
from Qt.QtGui import QIcon, QMouseEvent, QShowEvent

from tp.common.python import helpers
from tp.common.resources import api as resources
from tp.common.qt import qtutils, dpi
from tp.common.qt.widgets import dividers, search


def menu(label: str = '', icon: QIcon | None = None, parent: QWidget | None = None) -> BaseMenu:
	"""
	Creates a new menu with extended functionality.

	:param str label: label text of the menu.
	:param QIcon icon: optional menu icon.
	:param QWidget or None parent: parent widget.
	:return: newly created menu.
	:rtype: Menu
	"""

	new_menu = BaseMenu(label, parent=parent)
	if icon and not icon.isNull():
		new_menu.setIcon(icon)

	return new_menu


def extended_menu(label: str = '', icon: QIcon | None = None, parent: QWidget | None = None) -> ExtendedMenu:
	"""
	Creates a new menu with extended functionality.

	:param str label: label text of the menu.
	:param QIcon icon: optional menu icon.
	:param QWidget or None parent: parent widget.
	:return: newly created menu.
	:rtype: Menu
	"""

	new_menu = ExtendedMenu(label, parent=parent)
	if icon and not icon.isNull():
		new_menu.setIcon(icon)

	return new_menu


def searchable_menu(
		label: str = '', icon: QIcon | None = None, search_visible: bool = True,
		parent: QWidget | None = None) -> SearchableMenu:
	"""
	Creates a new searchable menu.

	:param str label: label text of the menu.
	:param QIcon icon: optional menu icon.
	:param bool search_visible: whether search widget is visible.
	:param QWidget parent: parent widget.
	:return: newly created menu.
	:rtype: SearchableMenu
	"""

	new_menu = SearchableMenu(label, search_visible=search_visible, parent=parent)
	if icon and not icon.isNull():
		new_menu.setIcon(icon)

	return new_menu


def mixin(cls):
	"""
	Decorator that can be added to custom widgets to automatize the creation of left/right/middle click menus.
	"""

	original_init__ = cls.__init__

	def my__init__(self, *args, **kwargs):
		original_init__(self, *args, **kwargs)

	def get_menu(self, mouse_button=Qt.RightButton):
		"""
		Returns the menu based on the given mouse button.

		:param Qt.ButtonClick mouse_button: the clicked mouse button.
		:return: registered menu on that mouse button.
		:rtype: QMenu or None
		"""

		return self._click_menu[mouse_button]

	def set_menu(self, menu, action_list=None, mouse_button=Qt.RightButton):
		"""
		Sets the left/middle/right click menu. If a model_list is given, then the menu will be  filled with that info.

		:param QMenu menu: Qt menu to show on left/middle/right click.
		:param list(tuple(str)) action_list: list of menu modes. Eg: [('icon1', 'menuName1'), (...), ...]
		:param Qt.ButtonClick mouse_button: the mouse button menu will be assigned to.
		"""

		self._click_menu[mouse_button] = menu
		self._menu_active[mouse_button] = True
		if action_list:
			self._add_action_list(action_list, mouse_button=mouse_button)

	def show_context_menu(self, mouse_button):
		"""
		Shows the menu depending on the given mouse click.

		:param Qt.ButtonClick mouse_button: the mouse button menu will be assigned to.
		"""

		if not self._click_menu:
			return

		menu = self.get_menu(mouse_button=mouse_button)
		if menu is not None and self._menu_active[mouse_button]:
			self.setFocus()
			parent_position = self.mapToGlobal(QPoint(0, 0))
			pos = parent_position + QPoint(0, dpi.dpi_scale(self._menu_vertical_offset))
			menu.exec_(pos)

	def _setup_menu_class(self, menu_vertical_offset=20):
		"""
		Internal function that handles the setup of menu creation.

		:param int menu_vertical_offset: negative vertical offset of the drawn menu
		"""

		self._menu_vertical_offset = menu_vertical_offset
		self._menu_active = {Qt.LeftButton: False, Qt.MiddleButton: False, Qt.RightButton: False}
		self._click_menu = {Qt.LeftButton: None, Qt.MiddleButton: None, Qt.RightButton: None}
		self._menu_searchable = {Qt.LeftButton: False, Qt.MiddleButton: False, Qt.RightButton: False}

	def _add_action_list(self, actions_list, mouse_button=Qt.RightButton):
		"""
		Internal function that resets the menu and fills its with given list of actions.

		:param list(tuple(str, str)) actions_list: list of menu actions. Eg: [('icon1', 'menuName1'), (...), ...]
		:param Qt.ButtonClick mouse_button: the mouse button menu will be assigned to.

		..warning:: this function only works with CPG DCC Tools framework Menu class
		"""

		menu = self.get_menu(mouse_button=mouse_button)
		if menu is not None:
			menu.action_connect_list(actions_list)

	setattr(cls, '__init__', my__init__)
	setattr(cls, 'get_menu', get_menu)
	setattr(cls, 'set_menu', set_menu)
	setattr(cls, 'show_context_menu', show_context_menu)
	setattr(cls, '_setup_menu_class', _setup_menu_class)
	setattr(cls, '_add_action_list', _add_action_list)

	return cls


class BaseMenu(QMenu):
	"""
	Extends standadr QMenu.
	"""

	mouseButtonClicked = Signal(Qt.MouseButton, QAction)

	@override
	def mouseReleaseEvent(self, arg__1: QMouseEvent) -> None:
		"""
		Extends mouseReleaseEvent QMenu function.

		:param QMouseEvent arg__1: mouse event.
		"""

		self.mouseButtonClicked.emit(arg__1.button(), self.actionAt(arg__1.pos()))

		return super().mouseReleaseEvent(arg__1)


class SearchableMenu(BaseMenu):
	"""
	Extends BaseMenu to make it searchable.
	First action is a QLineEdit used to recursively search on all actions.
	"""

	class SearchableTaggedAction(QAction):
		"""
		Class that defines a searchable tag action.
		"""

		def __init__(self, label: str, icon: QIcon | None = None, parent: SearchableMenu | None = None):
			super().__init__(label, parent)

			self._tags = set()  # Set[str]

			if icon:
				self.setIcon(icon)

		@property
		def tags(self) -> Set[str]:
			return self._tags

		@tags.setter
		def tags(self, new_tags: Set[str]):
			self._tags = new_tags

		def has_tag(self, tag: str) -> bool:
			"""
			Searches this instance tags. Returns True if the tag is valid or False otherwise

			:param str tag: partial or full tag to search for
			:return: bool
			"""

			for t in self._tags:
				if tag in t:
					return True

			return False

		def has_any_tag(self, tags: List[str]) -> bool:
			"""
			Returns True if current action has some given tags; False otherwise.

			:param tags: List[str]
			:return: bool
			"""

			for t in tags:
				for i in self._tags:
					if t in i:
						return True

			return False

	def __init__(self, *args, **kwargs):

		self._search_visible = kwargs.pop('search_visible') if kwargs.get('search_visible', None) is not None else True

		super(SearchableMenu, self).__init__(*args, **kwargs)

		self._search_action = None  # type: QWidgetAction
		self._search_edit = None  # type: search.SearchFindWidget

		self.setObjectName(kwargs.get('objectName', ''))
		self.setTitle(kwargs.get('title', ''))
		self._init_search_edit()
		self.set_search_visible(self._search_visible)

		self.setAttribute(Qt.WA_TranslucentBackground, False)

		# When menu is hidden we make that search text is cleared out
		self.aboutToShow.connect(self._on_about_to_show_menu)

	@override
	def clear(self) -> None:
		"""
		Overrides base clear function.
		"""

		super().clear()

		self._init_search_edit()

	def showEvent(self, event: QShowEvent) -> None:
		"""
		Overrides base showEvent function to set the search visible or not.

		:param QShowEvent event: Qt show event.
		"""

		if self.search_visible():
			self._search_edit.setFocus()

	def search_visible(self) -> bool:
		"""
		Returns whether search edit is visible

		:return: bool
		"""

		return self._search_action.isVisible()

	def set_search_visible(self, flag: bool):
		"""
		Sets the visibility of the search edit

		:param flag: bool
		"""

		self._search_visible = flag
		if not self._search_edit:
			return

		self._search_action.setVisible(flag)
		self._search_edit.setVisible(flag)

	def update_search(self, search_string: str | None = None):
		"""
		Search all actions for a string tag.

		:param str or None search_string: tag names separated by spaces (for example, "elem1 elem2")
		:return: str
		"""

		def _recursive_search(_menu: QMenu, _search_str: str):
			"""
			Internal function that recursively searches for menu actions.

			:param QMenu _menu: menu to search actions for.
			:param str _search_str: search string.
			"""

			for action in _menu.actions():
				if not search_str:
					action.setVisible(True)
					continue
				# This is not valid because for some reason accession QAction menu() attributes makes Qt to
				# not display the menu anymore. The bug was noticeable in the following scenario:
				# 1) Type something in the menu search
				# 2) Navigate inside a Menu
				# 3) Execute one of the menu items
				# 4) Now when you open the main menu again all the menus inside it will not appear.
				# sub_menu = action.menu() if hasattr(action, 'menu') else None
				# if sub_menu:
				# _recursive_search(sub_menu, search_str)
				# continue
				if action.isSeparator():
					continue
				elif isinstance(action, SearchableMenu.SearchableTaggedAction) and not action.has_tag(search_str):
					action.setVisible(False)

			for sub_menu in _menu.findChildren(QMenu):
				_recursive_search(sub_menu, search_str)

			actions = [action for action in _menu.actions() if not action.isSeparator()]
			menu_vis = any(action.isVisible() for action in actions)
			_menu.menuAction().setVisible(menu_vis)

		def _recursive_search_by_tags(_menu: QMenu, _tags: List[str]):
			"""
			Internal function that recursively searches for menu actions.

			:param QMenu _menu: menu to search actions for.
			:param List[str] _tags: list of tags.
			"""

			for action in _menu.actions():
				sub_menu = action.menu()
				if sub_menu:
					_recursive_search_by_tags(sub_menu, _tags)
					continue
				elif action.isSeparator():
					continue
				elif isinstance(action, SearchableMenu.SearchableTaggedAction):
					action.setVisible(action.has_any_tag(_tags))

			actions = [action for action in _menu.actions() if not action.isSeparator()]
			menu_vis = any(action.isVisible() for action in actions)
			_menu.menuAction().setVisible(menu_vis)

		search_str = str(search_string or '').lower()
		tags = search_str.split()
		if not search_str:
			qtutils.recursively_set_menu_actions_visibility(menu=self, state=True)
			return
		elif len(tags) > 1:
			_recursive_search_by_tags(self, tags)
			return

		_recursive_search(self, tags[0])

	def _init_search_edit(self):
		"""
		Internal function that adds a QLineEdit as the first action in the menu
		"""

		self._search_action = QWidgetAction(self)
		self._search_action.setObjectName('SearchAction')
		self._search_edit = search.SearchFindWidget(parent=self)
		self._search_edit.setStyleSheet('QPushButton {background-color: transparent; border: none;}')
		self._search_edit.set_placeholder_text('Search ...')
		self._search_edit.textChanged.connect(self._on_update_search)
		self._search_action.setDefaultWidget(self._search_edit)
		self.addAction(self._search_action)
		self.addSeparator()

	def _on_update_search(self, search_string):
		"""
		Internal callback function that is called when the user interacts with the search line edit
		"""

		self.update_search(search_string)

	def _on_about_to_show_menu(self):
		"""
		Internal callback function that is called when the menu is about to be showed
		:return:
		"""

		self._search_edit.clear()


class ExtendedMenu(SearchableMenu):
	"""
	Extends searchable menu by adding automatic menu generation and menu state management.
	"""

	menuChanged = Signal()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# internal list that contains item names read from actions list
		self._menu_items_list = list()

		# internal list that contains icon names read from the actions list
		self._menu_icons_list = list()

		self._current_menu_item = ''
		self._current_menu_index = 0

		self.setStyleSheet("* {menu-scrollable: 1;}")

	@override(check_signature=False)
	def insertAction(self, before: str | QAction, *args) -> None:
		"""
		Overrides insertAction QMenu function
		Add supports for finding the before action by the given string

		:param str or QAction before: str or QAction
		:param str or QAction before: str or QAction
		"""

		if helpers.is_string(before):
			before = self.find_action(before)

		return super().insertAction(before, *args)

	@override(check_signature=False)
	def insertMenu(self, before: str | QAction, menu: QMenu) -> QAction:
		"""
		Overrides insertMenu QMenu function
		Add supports for finding the before action by the given string

		:param str or QAction before: before action.
		:param QMenu menu: QMenu
		:return: newly created action.
		:rtype: QAction
		"""

		if helpers.is_string(before):
			before = self.find_action(before)

		return super().insertMenu(before, menu)

	@override(check_signature=False)
	def insertSeparator(self, before: str | QAction) -> QAction:
		"""
		Extends insertSeparator QMenu function

		:param str or QAction before: before action.
		:return: newly created action.
		:rtype: QAction
		"""

		if helpers.is_string(before):
			before = self.find_action(before)

		return super().insertSeparator(before)

	def current_menu_item(self) -> str:
		"""
		Returns the current selected menu name.

		:return: current menu name
		:rtype: str
		"""

		return self._current_menu_item

	def set_current_menu_item(self, menu_item_name: str):
		"""
		Sets both menu states for the given menu item name (without triggering a menu action).

		:param str menu_item_name: name of a meny name within the menu.
		"""

		self._current_menu_item = menu_item_name
		self._current_menu_index = self._menu_items_list.index(menu_item_name)

	def current_menu_index(self) -> int:
		"""
		Returns the current selected menu index.

		:return: current menu index.
		:rtype: int
		"""

		return self._current_menu_index

	def set_current_menu_index(self, menu_item_index: int):
		"""
		Sets both menu states for the given menu item index (without triggering a menu action).

		:param int menu_item_index: index of a menu name within the menu.
		"""

		self._current_menu_index = menu_item_index
		self._current_menu_item = self._menu_items_list[menu_item_index]

	def add_text_separator(self, text: str) -> QWidgetAction:
		"""
		Adds a new QWidgetAction that acts as separator with text.

		:param str text: text to add to the widget action.
		:return: text widget action
		:rtype: QWidgetAction
		"""

		separator = QWidgetAction(self)
		text_label = dividers.divider(text, alignment=Qt.AlignLeft, shadow=False, parent=self)
		text_label._first_line.setVisible(False)
		separator.setDefaultWidget(text_label)
		self.addAction(separator)

		return separator

	def add_action(
			self, name: str, connect: Callable = None, checkable: bool = False, checked: bool = True,
			action: SearchableMenu.SearchableTaggedAction | None = None,
			icon: str | QIcon | None = None) -> SearchableMenu.SearchableTaggedAction:
		"""
		Creates a new QAction and adds it into this menu.

		:param str name: text for the new menu item.
		:param callable connect: optional function to connect when the menu item is clicked.
		:param bool checkable: whether the menu item is checkable.
		:param bool checked: whether the menu item is checked by default.
		:param SearchableMenu.SearchableTaggedAction or None action: set the action directly (without creating a new one).
		:param str or QIcon or None icon: icon to set to the menu item.
		:return: newly added action.
		:rtype: SearchableMenu.SearchableTaggedAction
		"""

		if action is not None:
			self.addAction(action)
			return action

		new_action = SearchableMenu.SearchableTaggedAction(name, parent=self)
		new_action.setCheckable(checkable)
		new_action.setChecked(checked)
		new_action.tags = set(self._string_to_tags(name))
		self.addAction(new_action)

		icon = resources.icon(icon) if helpers.is_string(icon) else icon
		if icon and not icon.isNull():
			new_action.setIcon(icon)

		if connect is not None:
			if checkable:
				new_action.triggered.connect(partial(connect, new_action))
			else:
				new_action.triggered.connect(connect)

		return new_action

	def find_action(self, text: str) -> QAction | None:
		"""
		Returns the action that contains the given text

		:param str text: action text.
		:return: QAction
		"""

		for child in self.children():
			action = None
			if isinstance(child, QMenu):
				action = child.menuAction()
			elif isinstance(child, QAction):
				action = child
			if action and action.text().lower() == text.lower():
				return action

		return None

	def find_menu(self, text: str) -> QMenu | None:
		"""
		Returns the menu that contains given text.

		:param str text: menu text.
		:return: QMenu
		"""

		found_menu = None
		for child in self.children():
			if isinstance(child, QMenu) and child.text().lower() == text.lower():
				found_menu = child
				break

		return found_menu

	def action_connect_list(self, actions_list: List[Tuple[str, str]], default_menu_item: str | None = None):
		"""
		Fills the menu with the given icons and action names from the list.

		:param List[Tuple[str, str]] actions_list: list of menu actions. Eg: [('icon1', 'menuName1'), (...), ...]
		:param str or None default_menu_item: optional default menu item name.
		"""

		self.clear()
		self._set_icon_and_menu_name_from_actions_list(actions_list)
		for i, menu_item_name in enumerate(self._menu_items_list):
			if menu_item_name != 'separator':
				item_icon = self._menu_icons_list[i]
				item_icon = resources.icon(item_icon) if helpers.is_string(item_icon) else item_icon
				self.add_action(menu_item_name, icon=item_icon or QIcon(), connect=partial(
					self._action_connect, menu_item_name, i))
			else:
				self.addSeparator()

		if default_menu_item is None:
			self._current_menu_item = self._menu_items_list[0]
			self._current_menu_index = 0

	def _string_to_tags(self, string_to_convert: str) -> List[str]:
		"""
		Internal function that converts given string into searchable tags.

		:param str string_to_convert: string to convert.
		:return: tag names.
		:rtype: List[str]
		"""

		result = list()
		result += string_to_convert.split(' ')
		result += [s.lower() for s in string_to_convert.split(' ')]

		return result

	def _set_icon_and_menu_name_from_actions_list(self, actions_list: List[Tuple[str, str]]):
		"""
		Internal function that set up the variables that stores the list of icons and their names from the given
		actions list.

		:param List[Tuple[str, str]] actions_list: list of menu actions. Eg: [('icon1', 'menuName1'), (...), ...]
		"""

		self._menu_icons_list = list()
		self._menu_items_list = list()
		for action_tuple in actions_list:
			self._menu_icons_list.append(action_tuple[0])
			self._menu_items_list.append(action_tuple[1])

	def _action_connect(self, current_menu_item: str, current_menu_index: int):
		"""
		Internal function that creates a single IconMenuButton item in one menu entry. Also sets the icon to switch
		when a menu item is clicked.

		:param str current_menu_item: the current menu name.
		:param int current_menu_index: index of the menu item within menu, being 0 the first menu item.
		"""

		self._current_menu_item = current_menu_item
		self._current_menu_index = current_menu_index
		self.menuChanged.emit()
