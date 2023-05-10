#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Menu tp-dcc-tools framework interface.
"""

from tp.preferences import preference


class MenuInterface(preference.PreferenceInterface):
	"""
	Base interface that allow to interact with the preferences that handles the loading of tp-dcc-tools-framework main menu
	"""

	ID = 'menu'

	def menu_name(self):
		"""
		Returns tp-dcc-tools framework main menu name.

		:return: menu name.
		:rtype: str
		"""

		return self.manager.find_setting(self._RELATIVE_PATH, root=None, name='menuName', default='')


class MayaMenuInterface(MenuInterface):
	"""
	Maya interface implementation for MenuInterface
	"""

	_RELATIVE_PATH = 'prefs/maya/menu.pref'
	DCCS = 'maya'

	def load_shelf_at_startup(self):
		"""
		Returns whether Maya shelves should be created at startup.

		:return: True if Maya shelves should be created at startup; False otherwise.
		:rtype: bool
		"""

		return self.manager.find_setting(self._RELATIVE_PATH, root=None, name='loadShelfAtStartup', default=False)
