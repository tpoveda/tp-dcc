#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-tools-renamer model for Autodesk Maya
"""

from Qt.QtCore import Signal

from tp.tools.renamer import model


class RenamerModelMaya(model.RenamerModel):

	renameShapeChanged = Signal(bool)

	def __init__(self):
		super(RenamerModelMaya, self).__init__()

		self._rename_shape = True

	@property
	def rename_shape(self):
		return self._rename_shape

	@rename_shape.setter
	def rename_shape(self, flag):
		self._rename_shape = flag
		self.renameShapeChanged.emit(flag)