#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Core tp-dcc-tools framework Preference interface.
This preference handles the core preferences for tp-dcc-tools framework.
"""

import os

from tp.bootstrap import api
from tp.preferences import preference
from tp.common.python import path


class CorePreferenceInterface(preference.PreferenceInterface):

	ID = 'core'
	_PACKAGE_NAME = 'tp-dcc-preferences'
	_PREFERENCE_ROOTS_PATH = 'env/preference_roots.config'

	def root_config_path(self):
		"""
		Returns path where preference root configuration file is located.

		:return: root configuration absolute file path.
		:rtype: str
		"""

		packages_manager = api.current_package_manager()
		return path.clean_path(
			os.path.abspath(path.join_path(packages_manager.config_path, self._PREFERENCE_ROOTS_PATH)))

	def user_preferences(self):
		"""
		Returns user preferences path.

		:return: user preferences absolute path.
		:rtype: str
		"""

		user_preferences_path = path.clean_path(os.path.normpath(str(self._manager.root('user_preferences'))))
		if user_preferences_path != '~/tp/dcc/preferences':
			return user_preferences_path

		return path.clean_path(os.path.normpath(os.path.expanduser('~/tp/dcc/preferences')))
