#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-tools-renamer controller implementation for Autodesk Maya
"""

from tp.core import dcc
from tp.tools.renamer import controller
from tp.tools.renamer.maya import utils


class RenamerControllerMaya(controller.RenamerController):
	def __init__(self, model):
		super(RenamerControllerMaya, self).__init__(model=model)

	@dcc.undo_decorator()
	def rename_simple(self):
		"""
		Simple renaming operation.
		"""

		new_name = self._model.name
		rename_shape = self._model.rename_shape
		hierarchy_check = self._model.hierarchy_check
		selection_type = self._model.selection_type
		nodes = utils.get_objects_to_rename(hierarchy_check=hierarchy_check, selection_type=selection_type)

		return utils.simple_rename(new_name=new_name, nodes=nodes, rename_shape=rename_shape)

	@dcc.undo_decorator()
	def add_prefix(self):
		"""
		Prefix addition operation.
		"""

		new_prefix = self._model.prefix
		rename_shape = self._model.rename_shape
		hierarchy_check = self._model.hierarchy_check
		only_selection = self._model.only_selection
		filter_type = self._model.filter_type
		filter_type = global_data.get('filter_type', 0)

		return utils.add_prefix(
			new_prefix=new_prefix, rename_shape=rename_shape, hierarchy_check=hierarchy_check,
			only_selection=only_selection, filter_type=filter_type)

	@dcc.undo_decorator()
	def remove_prefix(self):
		"""
		Prefix removal operation.
		"""

		rename_shape = self._model.rename_shape
		hierarchy_check = self._model.hierarchy_check
		only_selection = self._model.only_selection
		filter_type = self._model.filter_type

		return utils.remove_prefix(
			rename_shape=rename_shape, hierarchy_check=hierarchy_check, only_selection=only_selection,
			filter_type=filter_type)

	@dcc.undo_decorator()
	def add_suffix(self):
		"""
		Suffix addition operation.
		"""

		new_suffix = self._model.suffix
		rename_shape = self._model.rename_shape
		hierarchy_check = self._model.hierarchy_check
		only_selection = self._model.only_selection
		filter_type = self._model.filter_type

		return utils.add_suffix(
			new_suffix=new_suffix, rename_shape=rename_shape, hierarchy_check=hierarchy_check,
			only_selection=only_selection, filter_type=filter_type)
