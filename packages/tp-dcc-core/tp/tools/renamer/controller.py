#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-tools-renamer controller
"""

from tp.common.python import decorators


class RenamerController(object):
	def __init__(self, model):
		super(RenamerController, self).__init__()

		self._model = model

	@property
	def model(self):
		return self._model

	@decorators.abstractmethod
	def rename_simple(self):
		"""
		Abstract method that executes a simple renaming operation.

		..note:: Should be implemented within each DCC controller class.
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def add_prefix(self):
		"""
		Abstract method that executes a prefix addition operation.

		..note:: Should be implemented within each DCC controller class.
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def remove_prefix(self):
		"""
		Abstract method that executes a prefix removal operation.

		..note:: Should be implemented within each DCC controller class.
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def add_suffix(self):
		"""
		Abstract method that executes a suffix addition operation.

		..note:: Should be implemented within each DCC controller class.
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def remove_suffix(self):
		"""
		Abstract method that executes a suffix removal operation.

		..note:: Should be implemented within each DCC controller class.
		"""

		raise NotImplementedError

	def set_selection(self):
		"""
		Sets selection mode enabled.
		"""

		self._model.selection_type = 0

	def set_all_selection(self):
		"""
		Sets all selection mode enabled.
		"""

		self._model.selection_type = 1

	def toggle_hierarchy_check(self, flag):
		"""
		Toggles hierarchy check functionality.

		:param bool flag: True to enable/disable check hierarchy functionality.
		"""

		self._model.hierarchy_check = flag

	def toggle_name_check(self, flag):
		"""
		Toggles name check rename functionality.

		:param bool flag: True to enable/disable name rename functionality.
		"""

		self._model.name_check = flag

	def change_name(self, new_name):
		"""
		Sets the name value within model.

		:param str new_name: new model name value.
		"""

		self._model.name = new_name

	def toggle_prefix_check(self, flag):
		"""
		Toggles prefix check rename functionality.

		:param bool flag: True to enable/disable prefix rename functionality.
		"""

		self._model.prefix_check = flag

	def change_prefix(self, new_prefix):
		"""
		Sets the prefix value within model.

		:param str new_prefix: new model prefix value.
		"""

		self._model.prefix = new_prefix

	def toggle_suffix_check(self, flag):
		"""
		Toggles suffix check rename functionality.

		:param bool flag: True to enable/disable suffix rename functionality.
		"""

		self._model.suffix_check = flag
