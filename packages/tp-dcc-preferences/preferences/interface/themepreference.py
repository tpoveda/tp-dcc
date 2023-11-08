#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Theme Preference interface.
Through this interface we can handle all the data related with the tool themes.
"""

from Qt.QtCore import Signal, QObject

from tp.core import consts, log
from tp.preferences import preference
from tp.common import resources
from tp.common.resources import theme, style
from tp.common.python import helpers, strings, color
from tp.common.qt import dpi

logger = log.tpLogger


class ThemeUpdateEvent:
	def __init__(self, stylesheet, theme_dict, preference):
		self.theme = None
		self.stylesheet = stylesheet
		self.theme_dict = theme_dict
		self.preference = preference


class ThemePreferenceInterface(preference.PreferenceInterface):

	class ThemeUpdater(QObject):
		"""
		Sends a signal when a theme is updated. Allows to handle widget specific theme updates.
		"""

		updated = Signal(ThemeUpdateEvent)

	ID = 'theme'

	_RELATIVE_PATH = 'prefs/global/stylesheet{}'.format(consts.PREFERENCE_EXTENSION)
	_PACKAGE_NAME = 'tp-dcc-preferences'
	_THEME_UPDATER = ThemeUpdater()

	def __getattr__(self, item):
		"""
		Retrieves the current theme's key value.

		:param str item: name of the theme key value to retrieve.
		:return: object
		"""

		result = self.stylesheet_value(item)
		if result is None:
			return super(ThemePreferenceInterface, self).__getattribute__(item)

		return result

	@property
	def updated(self):
		"""
		Returns ThemeUpdater updated signal instance.

		:return: theme updater signal.
		:rtype: Signal
		"""

		return self._THEME_UPDATER.updated

	def themes(self):
		"""
		Returns a list of all available themes.

		:return: list of available theme names.
		:rtype: list(str)
		"""

		return list(self._manager.find_setting(self._RELATIVE_PATH, root=None, name='themes').keys())

	def current_theme(self):
		"""
		Returns the current theme name.

		:return: current theme name.
		:rtype: str
		"""

		return self._manager.find_setting(self._RELATIVE_PATH, root=None, name='current_theme')

	def stylesheet(self, theme=None):
		"""
		Returns the StyleSheet instance object for the given theme.

		:param str theme: name of theme we want to retrieve stylesheet of. If None, current theme will be used.
		:return: stylesheet instance object.
		:rtype: StyleSheet
		"""

		current_theme = theme or self.current_theme()
		return self.stylesheet_for_theme(current_theme)

	def stylesheet_for_theme(self, theme):
		"""
		Returns stylesheet from given theme.

		:param str theme: theme name ('dark', 'light', etc).
		:return: StyleSheet instance.
		:rtype: StyleSheet
		:raises ValueError: if not theme data found for given theme name.
		"""

		theme_data = self.theme_data(theme)
		if theme_data is None:
			raise ValueError('stylesheet theme does not exists: {}'.format(theme))

		return self.stylesheet_from_data(theme_data)

	def stylesheet_from_data(self, theme_data):
		"""
		Returns a new StyleSheet instance object from the given theme data.

		:param dict theme_data: data dictionary retrieve from stylesheet.pref.
		:return: stylesheet instance object.
		:rtype: StyleSheet
		"""

		from tp.common.resources import api

		theme_style = theme_data.style
		theme_style = strings.append_extension(theme_style, '.qss')
		style_path = api.get('styles', theme_style)

		return style.StyleSheet.from_path(style_path=style_path, **theme_data)

	def theme_data(self, theme_name=None):
		"""
		Returns the theme data dictionary found in stylesheet.pref for the given theme.

		:param str theme_name: name of the theme whose data dictionary we want to retrieve.
		:return: stylesheet data dictionary instance.
		:rtype: ThemeDict
		"""

		theme_name = theme_name or self.current_theme()
		style_preferences = self._manager.find_setting(self._RELATIVE_PATH, root=None)
		if not style_preferences:
			style_preferences = self._manager.default_preference_settings(self._PACKAGE_NAME, self._RELATIVE_PATH)
		themes = style_preferences.get('settings', dict()).get('themes', dict())
		data = themes.get(theme_name, dict())
		theme_data = theme.Theme(name=theme_name, data_dict=data)

		return theme_data

	def stylesheet_setting(self, key, theme=None):
		"""
		Returns one specific setting from a theme within the stylesheet.

		:param str key: a key from the current theme.
		:param str theme: specific theme to read stylesheet setting from. If not given, default theme will be used.
		:return: key value.
		:rtype: object
		"""

		try:
			settings = self.settings()['settings']
			theme = theme or settings['current_theme']
			result = settings['themes'][theme]['overrides'].get(key)
			if result is None and key.startswith('@'):
				result = settings['themes'][theme]['overrides'].get(key[1:])
		except KeyError:
			logger.error('Incorrectly formatted stylesheet: {}'.format(self._RELATIVE_PATH))
			raise

		try:
			if result is None:
				self._manager.default_preference_settings(self._PACKAGE_NAME, self._RELATIVE_PATH)
		except Exception:
			pass

		return result

	def stylesheet_value(self, key, theme=None):
		"""
		Returns stylesheet setting value with proper format.

		:param str key: a key from the current theme.
		:param str theme: specific theme to read stylesheet setting from. If not given, default theme will be used.
		:return: key value.
		:rtype: object
		"""

		style_attribute_name = key if key.startswith('@') else '@{}'.format(key)
		setting = self.stylesheet_setting(style_attribute_name, theme=theme)
		if setting is None:
			# we try to retrieve the theme value without the @ character
			setting = self.stylesheet_setting(style_attribute_name[1:], theme=theme)
			if setting is None:
				return None
		elif isinstance(setting, int):
			return setting
		elif helpers.is_string(setting):
			if setting.startswith('^'):
				return dpi.dpi_scale(int(setting[1:]))
			if len(setting) in (3, 6, 8):
				return color.hex_to_rgba(setting)

		return None

	def stylesheet_setting_color(self, key, theme=None):
		"""
		Returns a color setting from the current theme style.

		:param str key: key of the setting color.
		:param str theme: specific theme to get stylesheet color setting from.
		:return: color setting value.
		:rtype: tuple(float, float, float)
		"""

		return color.hex_to_rgba(self.stylesheet_setting(key=key, theme=theme))
