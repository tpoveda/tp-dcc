#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class to handle tpDcc Tools framework preference files and preferences data
"""

import os
import copy

from tp.core import consts, exceptions
from tp.common.python import helpers

# maximum levels of supported expansions
EXPAND_LIMIT = 5


class PreferenceInterface(object):
	"""
	Base class that is responsible for interfacing to '.pref files withing tpDcc Tools framework.
	Interfaces are a useful concept because allow us to properly handle configuration data when a change on the data
	schema is done.
	"""

	ID = ''
	_RELATIVE_PATH = ''
	_SETTINGS = None

	def __init__(self, preferences_manager):
		super(PreferenceInterface, self).__init__()

		self._manager = preferences_manager
		self._revert_settings = None

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def manager(self):
		return self._manager

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def are_settings_valid(self):
		"""
		Returns whether stored settings are valid.

		:return: True if settings are valid; False otherwise.
		:rtype: bool
		"""

		return self.settings().is_valid()

	def settings(self, relative_path=None, root=None, name=None, refresh=False):
		"""
		Returns the settings stored within the preference interface.

		:param str relative_path: relative path to the preference file.
		:param str or None root: root name to search, if None all roots will be searched.
		:param str name: name of the root to search.
		:param bool refresh: whether to re-cache the queried settings back on this interface instance.
		:return: settings value
		:rtype: PreferenceObject or object
		"""

		relative_path = relative_path or self._RELATIVE_PATH

		if self._SETTINGS is None or refresh:
			self._SETTINGS = self._manager.find_setting(relative_path, root=root)

		if name is not None:
			settings = self._SETTINGS.get(consts.PREFERENCE_SETTINGS_KEY, dict())
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

	def find_setting(self, name, root=None, extension=None, expand_num=0):
		name = str(name)
		if name in os.environ:
			result = os.environ[name]
		else:
			result = self._manager.find_setting(self._RELATIVE_PATH, root=root, name=name, extension=extension)
		if result and expand_num < EXPAND_LIMIT:
			result = self._expand_tokens(result, expand_num=expand_num)

		return result

	def _expand_tokens(self, value, expand_num):
		if helpers.is_string(value):
			result = self._expand_value(value, expand_num=expand_num)
		elif isinstance(value, list):
			result = list()
			for v in value:
				v = self._expand_value(v, expand_num=expand_num)
				result.append(v)
		else:
			result = value

		return result

	def _expand_value(self, value, expand_num):
		result = value
		for name in self._EXPAND_ENTRIES:
			key = '${' + name + '}'
			if key in result:
				key_value = self.find_setting(name=name, expand_num=expand_num)
				result = result.replace(key, key_value)

		return result

	def save_settings(self, indent=True, sort=False):
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

	# =================================================================================================================
	# INTERNAL
	# =================================================================================================================

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
