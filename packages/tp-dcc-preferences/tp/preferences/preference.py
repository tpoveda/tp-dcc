#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class to handle tpDcc Tools framework preference files and preferences data
"""

from __future__ import annotations

import os
import copy
import typing
from typing import Dict, Any

from tp.core import consts, exceptions
from tp.common.python import helpers

if typing.TYPE_CHECKING:
	from tp.preferences.manager import PreferenceObject, PreferencesManager

# maximum levels of supported expansions
EXPAND_LIMIT = 5


class PreferenceInterface:
	"""
	Base class that is responsible for interfacing to .pref files withing tpDcc Tools framework.
	Interfaces are a useful concept because allow us to properly handle configuration data when a change on the data
	schema is done.
	"""

	ID = ''
	_RELATIVE_PATH = ''
	_EXPAND_ENTRIES = []
	_SETTINGS = None

	def __init__(self, preferences_manager: PreferencesManager):
		super(PreferenceInterface, self).__init__()

		self._manager = preferences_manager
		self._revert_settings = None						# type: Dict

	@property
	def manager(self) -> PreferencesManager:
		return self._manager

	def are_settings_valid(self) -> bool:
		"""
		Returns whether stored settings are valid.

		:return: True if settings are valid; False otherwise.
		:rtype: bool
		"""

		return self.settings().is_valid()

	def path(self, relative_path: str | None = None, root: str | None = None, refresh: bool = False) -> str:

		relative_path = relative_path or self._RELATIVE_PATH

		if self._SETTINGS is None or refresh:
			self._SETTINGS = self._manager.find_setting(relative_path, root=root)

		return self._SETTINGS.get_path()

	def settings(
			self, relative_path: str | None = None, root: str | None = None, name: str | None = None,
			refresh: bool = False) -> PreferenceObject or dict:
		"""
		Returns the settings stored within the preference interface.

		:param str relative_path: relative path to the preference file.
		:param str or None root: root name to search, if None all roots will be searched.
		:param str name: name of the root to search.
		:param bool refresh: whether to re-cache the queried settings back on this interface instance.
		:return: settings value
		:rtype: PreferenceObject or Dict
		"""

		relative_path = relative_path or self._RELATIVE_PATH

		if self._SETTINGS is None or refresh:
			self._SETTINGS = self._manager.find_setting(relative_path, root=root)

		if name is not None:
			settings = self._SETTINGS.get(consts.PREFERENCE_SETTINGS_KEY, {})
			if name not in settings:
				raise exceptions.SettingsNameDoesNotExistError(
					'Failed to find setting: {} in file: {}'.format(name, relative_path))
			return settings[name]

		self._setup_revert()

		return self._SETTINGS

	def refresh(self):
		"""
		Force a refresh of the interface instance.
		"""

		self.settings(refresh=True)

	def find_setting(
			self, name: str, root: str | None = None, extension: str | None = None, expand_num: int = 0) -> Any:
		"""
		Find setting with given name.

		:param str name: setting name to find.
		:param str or None root: root name to search, if None all roots will be searched.
		:param str or None extension: optional setting extension.
		:param int expand_num: expand token value.
		:return: setting value.
		:rtype: Any
		"""

		name = str(name)
		if name in os.environ:
			result = os.environ[name]
		else:
			result = self._manager.find_setting(self._RELATIVE_PATH, root=root, name=name, extension=extension)
		if result and expand_num < EXPAND_LIMIT:
			result = self._expand_tokens(result, expand_num=expand_num)

		return result

	def _expand_tokens(self, value: Any, expand_num: int) -> Any:
		"""
		Internal function that expands token values for a setting.

		:param Any value: token value to expand.
		:param int expand_num: expand token value.
		:return: expanded tokens.
		"""

		if helpers.is_string(value):
			result = self._expand_value(value, expand_num=expand_num)
		elif isinstance(value, list):
			result = []
			for v in value:
				v = self._expand_value(v, expand_num=expand_num)
				result.append(v)
		else:
			result = value

		return result

	def _expand_value(self, value: Any, expand_num: int):
		"""
		Internal function that expands token value for a setting.

		:param Any value: token value to expand.
		:param int expand_num: expand token value.
		:return: expanded values.
		"""

		result = value
		for name in self._EXPAND_ENTRIES:
			key = '${' + name + '}'
			if key in result:
				key_value = self.find_setting(name=name, expand_num=expand_num)
				result = result.replace(key, key_value)

		return result

	def save_settings(self, indent: bool = True, sort: bool = False):
		"""
		Save settings into disk.

		:param bool indent: whether indent should be respected.
		:param bool sort: whether settings should be respect its order when saving.
		"""

		self._SETTINGS.save(indent=indent, sort=sort)
		self._revert_settings = None

	def revert_settings(self):
		"""
		Reverts the setting back to the previous status.
		"""

		if not self._revert_settings:
			return

		self._SETTINGS.clear()
		self._SETTINGS.update(self._revert_settings)
		self.save_settings()

	def _setup_revert(self):
		"""
		Internal function that setup revert settings.
		"""

		if not self._revert_settings:
			self._revert_settings = copy.deepcopy(self._SETTINGS)


class InvalidPreferencePathError(Exception):
	"""
	Exception that is raised when a Preference interface path does not exist.
	"""

	pass


class PreferenceSettingNameDoesNotExistError(Exception):
	"""
	Exception that is raised when trying to access to a preference setting that does not exist.
	"""

	pass
