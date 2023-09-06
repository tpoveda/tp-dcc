from __future__ import annotations

import os
import typing
from typing import List, Dict
from functools import partial

import maya.cmds as cmds

from tp.core import log
from tp.common import plugin
from tp.common.python import helpers, decorators
from tp.common.resources import api as resources

if typing.TYPE_CHECKING:
	from tp.maya.libs.triggers.managers import MarkingMenusManager

logger = log.tpLogger


def find_layout(layout_id: str) -> MarkingMenuLayout | None:
	"""
	Finds the layout with given ID from the marking menus register.

	:param str layout_id: ID of the marking menu layout to find.
	:return: found marking menu.
	:rtype: MarkingMenuLayout or None
	"""

	from tp.maya.libs.triggers import managers

	manager = managers.MarkingMenusManager()
	if layout_id in manager.layouts:
		return manager.layouts[layout_id]


class MarkingMenuLayout(dict):
	def __init__(self, **kwargs: Dict):
		kwargs['sortOrder'] = kwargs.get('sortOrder', 0)
		super().__init__(**kwargs)
		self._solved = False

	def __getitem__(self, marking_menu_region: str):
		value = self.get(marking_menu_region)
		if value is None:
			return self.get('items', {}).get(marking_menu_region)

		return value

	def __iter__(self):
		for name, data in iter(self['items'].items()):
			yield name, data

	def items(self) -> Dict:
		"""
		Returns the item dict for this layout with the following form:
		{
			"N": {},
			"NW": {},
			"W": {},
			"SW": {},
			"S": {},
			"SE": {},
			"E": {},
			"NE": {},
			"generic": [{"type": "menu", "name": "Testmenu", "children": [{"type": "command", "id": ""}]]
		}
		:return: layout items dict.
		:rtype: Dict
		"""

		return self.get('items', {}).items()

	def merge(self, layout: MarkingMenuLayout):
		"""
		Merges the layout items into this instance.

		:param MarkingMenuLayout layout: marking menu layout instance to merge.
		"""

		helpers.merge_dictionaries(self, layout['items'])

	def solve(self) -> bool:
		"""
		Recursively solves the marking menu layout by expanding any @layout.id references which will compose a single
		dictionary ready for use.

		:return: True if marking menu layout was solved successfully; False otherwise.
		:rtype: bool
		"""

		from tp.maya.libs.triggers import managers

		manager = managers.MarkingMenusManager()
		solved = False
		for item, data in self.get('items', {}).items():
			if not data:
				continue
			elif item == 'generic':
				solved = True
				continue
			elif data['type'] == 'layout':
				sub_layout = manager.layouts.get(data['id'])
				if not sub_layout:
					logger.warning(f'No layout with ID "{data["id"]}" found, skipping...')
					continue
				sub_layout.solve()
				self['items'][item] = sub_layout
				solved = True
		self._solved = solved

		return solved


class MarkingMenu:

	def __init__(self, layout: MarkingMenuLayout, name: str, parent: str, manager: MarkingMenusManager):

		self._layout = layout
		self._name = name
		self._parent = parent
		self._manager = manager
		self._pop_menu = None
		self._command_arguments = {}

		if cmds.popupMenu(name, ex=True):
			cmds.deleteUI(name)

		self._options = {
			'allowOptionBoxes': True,
			'altModifier': False,
			'button': 1,
			'ctrlModifier': False,
			'postMenuCommandOnce': True,
			'shiftModifier': False
		}

	@property
	def options(self) -> Dict:
		return self._options

	@classmethod
	def build_from_marking_menu_layout_data(
			cls, layout_data: MarkingMenuLayout, menu_name: str, parent: str,
			options: Dict, arguments: Dict) -> MarkingMenu:
		"""
		Creates a new MarkingMenu instance from the given marking menu layout instance.

		:param MarkingMenuLayout layout_data: marking menu layout instance.
		:param str menu_name: name of the menu.
		:param str parent: parent menu.
		:param Dict options: optional options to be passed to the menu.
		:param Dict arguments: optional arguments to be passed to the "attach()" or "create()" functions.
		:return: newly created marking menu instance.
		:rtype: MarkingMenu
		:raises ValueError: if we try to create multiple menus of the active one.
		"""

		from tp.maya.libs.triggers import managers

		marking_menu_manager = managers.MarkingMenusManager()
		if menu_name in marking_menu_manager.active_menus:
			if not cmds.popupMenu(menu_name, ex=True):
				del marking_menu_manager.active_menus[menu_name]
			else:
				raise ValueError(
					f'Menu "{menu_name}" already is active and is not possible to create multiple instances of the same menu')

		new_menu = cls(layout_data, name=menu_name, parent=parent, manager=marking_menu_manager)
		new_menu.options.update(options)
		if cmds.popupMenu(parent, ex=True):
			new_menu.attach(**arguments or {})
		else:
			new_menu.create(**arguments or {})
		marking_menu_manager.active_menus[menu_name] = new_menu

		return new_menu

	def attach(self, **arguments: Dict) -> bool:
		"""
		Generates the marking menu using the parent marking menu.

		:param Dict arguments: arguments to pass to each menu item command.
		:return: True if marking menu was attached successfully to parent marking menu; False otherwise.
		:rtype: bool
		"""

		if cmds.popupMenu(self._parent, exists=True):
			self._command_arguments = arguments
			self._show(self._parent, self._parent)
			return True

		return False

	def create(self, **arguments: Dict) -> MarkingMenu:
		"""
		Creates a new popup marking menu parented to parent marking menu.

		:param Dict arguments: arguments to pass to each menu item command.
		:return: newly created marking menu instance.
		:rtype: MarkingMenu
		"""

		if cmds.popupMenu(self._name, exists=True):
			cmds.deleteUI(self._name)

		self._command_arguments = arguments
		self._pop_menu = cmds.popupMenu(
			self._name, parent=self._parent, markingMenu=True, postMenuCommand=self._show, **self._options)

		return self

	def show(self, layout: MarkingMenuLayout, menu: str, parent: str):
		"""
		Shows marking menu.

		:param MarkingMenuLayout layout: marking menu layout instance.
		:param str menu: menu full path which commands will be attached to.
		:param str parent: parent full path name.
		"""

		def _build_generic(_data: List, _menu: str):
			for _item in _data:
				if _item['type'] == 'command':
					self.add_command(_item, _menu)
				elif _item['type'] == 'menu':
					sub_menu = cmds.menuItem(label=_item['label'], subMenu=True, parent=_menu)
					_build_generic(_item['children'], sub_menu)
				elif _item['type'] == 'radioButtonMenu':
					sub_menu = cmds.menuItem(label=_item['label'], subMenu=True, parent=_menu)
					cmds.radioMenuItemCollection(parent=sub_menu)
					_build_generic(_item['children'], sub_menu)
				elif _item['type'] == 'separator':
					self.add_separator(_menu, _item)

		for item, data in layout.items():
			if not data:
				continue
			if item == 'generic':
				_build_generic(data, menu)
				continue
			elif isinstance(data, MarkingMenuLayout):
				rad_menu = cmds.menuItem(label=data['id'], subMenu=True, parent=menu, radialPosition=item.upper())
				self.show(data, rad_menu, parent)
			elif data['type'] == 'command':
				self.add_command(data, parent=menu, radial_position=item.upper())

	def add_command(self, item: Dict, parent: str, radial_position: str | None = None):
		"""
		Adds the given command item to the parent menu.

		:param Dict item: item data {'type': 'command', 'id': 'myCustomCommand'}
		:param str parent: parent menu full path.
		:param str or None radial_position: optional radial position.
		"""

		command = self._manager.commands_factory.load_plugin(item['id'])
		if command is None:
			logger.warning(f'Failed to find command: {item["id"]}')
			return

		cmd_arg_override = dict(**self._command_arguments)
		cmd_arg_override.update(item.get('arguments', {}))
		ui_data = command.ui_data(cmd_arg_override)
		ui_data.update(item)
		option_box = ui_data.get('optionBox', False)
		enable = ui_data.get('enable', True)
		show = ui_data.get('show', True)
		checkbox = ui_data.get('checkBox', False)
		radio_button_state = ui_data.get('radioButtonState', False)
		try:
			label = ui_data['label']
		except KeyError:
			logger.error(f'Label key missing from marking menu command: {item}')
			return None
		if not show:
			return None

		arguments = dict(
			label=label, parent=parent, command=partial(command.run, cmd_arg_override, False), optionBox=False,
			enable=enable)
		icon_path = ui_data.get('icon', '')
		icon_option_box = ui_data.get('optionBoxIcon', '')
		if icon_path:
			if not icon_path.endswith('.png'):
				icon_path = f'{os.path.splitext(icon_path)[0]}.png'
			new_icon_path = resources.get('icons', 'default', icon_path)
			if new_icon_path:
				icon_path = new_icon_path
			arguments['image'] = icon_path

		if ui_data.get('isRadioButton', False):
			arguments['radioButton'] = radio_button_state
		if ui_data.get('italic', False):
			arguments['italicized'] = True
		if ui_data.get('bold', False):
			arguments['boldFont'] = True
		if radial_position is not None:
			arguments['radialPosition'] = radial_position
		if checkbox:
			arguments['checkBox'] = checkbox

		cmds.menuItem(**arguments)

		if option_box:
			icon_option_box = resources.get(icon_option_box)
			if os.path.exists(icon_option_box):
				arguments['optionIconBox'] = icon_option_box
			arguments.update(dict(optionBox=option_box, command=partial(command.run, cmd_arg_override, True)))
			cmds.menuItem(**arguments)

	def add_separator(self, menu: str, item: Dict | None):
		"""
		Adds separator to the menu.

		:param str menu: parent menu full path.
		:param Dict or None item: optional item data.
		"""

		if item and item.get('id'):
			command = self._manager.commands_factory.load_plugin(item['id'])
			cmd_arg_override = dict(**self._command_arguments)
			cmd_arg_override.update(item.get('arguments', {}))
			ui_data = command.ui_data(cmd_arg_override)
			ui_data.update(item)
			if ui_data.get('show') is False:
				return

		cmds.menuItem(parent=menu, divider=True)

	def _show(self, menu: str, parent: str):
		"""
		Internal function that shows marking menu.

		:param str menu: menu to show.
		:param str parent: parent menu.
		"""

		cmds.setParent(menu, menu=True)
		cmds.menu(menu, edit=True, deleteAllItems=True)
		self.show(self._layout, menu, parent)


class MarkingMenuDynamic(plugin.Plugin):
	"""
	Dynamic marking menu that allows for subclasses to dynamic generate the marking menu layout.
	"""

	DOCUMENTATION = __doc__
	ID = ''

	@decorators.abstractmethod
	def execute(self, layout: MarkingMenuLayout, arguments: Dict) -> MarkingMenuLayout | None:
		"""
		Executes the building of the marking menu.

		:param MarkingMenuLayout layout: marking menu layout instance.
		:param Dict arguments: dictionary containing the marking menu arguments.
		:return: marking menu layout instance.
		:rtype: MarkingMenuLayout or None
		"""

		raise NotImplementedError('Execute method must be implemented in subclasses')


class MarkingMenuCommand(plugin.Plugin):
	"""
	Marking menu that allows to define a single marking menu action
	"""

	DOCUMENTATION = __doc__
	ID = ''

	@staticmethod
	def ui_data(arguments: Dict) -> Dict:
		"""
		Returns dictionary that defines the visual of the command action.

		:param Dict arguments: global arguments for the marking menu command.
		:return: ui data.
		:rtype: Dict
		"""

		return {
			'icon': arguments.get('icon', ''),
			'label': arguments.get('label', ''),
			'enable': True,
			'bold': False,
			'italic': False,
			'optionBox': False,
			'checkBox': None
		}

	def run(self, arguments, *args):
		"""
		Run command.

		:param Dict arguments: command arguments.
		"""

		from tp.maya.libs.triggers import triggercallbacks
		with triggercallbacks.block_selection_callback():
			if arguments.get('optionBox', False):
				self.execute_ui(arguments)
			else:
				self.execute(arguments)

	def execute(self, arguments: Dict):
		"""
		Function that is executed when the action is triggered by the user.

		:param Dict arguments: command arguments.
		"""

		pass

	def execute_ui(self, arguments: Dict):
		"""
		Function that is executed when the user triggers the box icon of the action.

		:param Dict arguments: command arguments.
		"""

		pass
