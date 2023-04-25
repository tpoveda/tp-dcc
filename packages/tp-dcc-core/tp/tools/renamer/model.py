#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-tools-renamer model
"""

from Qt.QtCore import Signal, QObject


class RenamerModel(QObject):

	selectionTypeChanged = Signal(int)
	checkHierarchyChanged = Signal(bool)
	filterTypeChanged = Signal(str)
	checkNameChanged = Signal(bool)
	nameChanged = Signal(str)
	doRename = Signal()
	checkPrefixChanged = Signal(bool)
	prefixChanged = Signal(str)
	checkSuffixChanged = Signal(bool)
	suffixChanged = Signal(str)

	def __init__(self):
		super(RenamerModel, self).__init__()

		self._selection_type = 0
		self._hierarchy_check = False
		self._filter_type = ''
		self._name_check = True
		self._name = ''
		self._prefix_check = True
		self._prefix = ''
		self._suffix_check = True
		self._suffix = ''

	@property
	def selection_type(self):
		return self._selection_type

	@selection_type.setter
	def selection_type(self, value):
		self._selection_type = value
		self.selectionTypeChanged.emit(value)

	@property
	def hierarchy_check(self):
		return self._hierarchy_check

	@hierarchy_check.setter
	def hierarchy_check(self, flag):
		self._hierarchy_check = flag
		self.checkHierarchyChanged.emit(flag)

	@property
	def filter_type(self):
		return self._selection_type

	@filter_type.setter
	def filter_type(self, value):
		self._filter_type = value
		self.filterTypeChanged.emit(value)

	@property
	def name_check(self):
		return self._name_check

	@name_check.setter
	def name_check(self, flag):
		self._name_check = bool(flag)
		self.checkNameChanged.emit(self._name_check)

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, value):
		self._name = str(value)
		self.nameChanged.emit(self._name)

	@property
	def prefix_check(self):
		return self._prefix_check

	@prefix_check.setter
	def prefix_check(self, flag):
		self._prefix_check = flag
		self.checkPrefixChanged.emit(flag)

	@property
	def prefix(self):
		return self._prefix

	@prefix.setter
	def prefix(self, value):
		self._prefix = str(value)
		self.prefixChanged.emit(value)

	@property
	def rename_settings(self):
		text = str(self.name.strip()) if self.check else ''

		return {
			'name': text
		}
