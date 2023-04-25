#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definitions for tpNodeGraph GUI
"""

from Qt.QtGui import QVector2D

from tp.common.math import scalar


class AutoPanner(object):
	def __init__(self, amount=0.1):
		super(AutoPanner, self).__init__()

		self._amount = amount
		self._is_allowed = False
		self._auto_pan_delta = QVector2D(0.0, 0.0)
		self._been_outside = False

	def tick(self, rect, pos):
		if self._is_allowed:
			if pos.x() < 0:
				self._auto_pan_delta = QVector2D(-self._amount, 0.0)
				self._been_outside = True
				self._amount = scalar.clamp(abs(pos.x()) * 0.1, 0.0, 25.0)
			if pos.x() > rect.width():
				self._auto_pan_delta = QVector2D(self._amount, 0.0)
				self._been_outside = True
				self._amount = scalar.clamp(abs(rect.width() - pos.x()) * 0.1, 0.0, 25.0)
			if pos.y() < 0:
				self._auto_pan_delta = QVector2D(0.0, -self._amount)
				self._been_outside = True
				self._amount = scalar.clamp(abs(pos.y()) * 0.1, 0.0, 25.0)
			if pos.y() > rect.height():
				self._auto_pan_delta = QVector2D(0.0, self._amount)
				self._been_outside = True
				self._amount = scalar.clamp(abs(rect.height() - pos.y()) * 0.1, 0.0, 25.0)
			if self._been_outside and rect.contains(pos):
				self.reset()

	@property
	def amount(self):
		return self._amount

	@amount.setter
	def amount(self, value):
		self._amount = value

	@property
	def delta(self):
		return self._auto_pan_delta

	def is_active(self):
		return self._is_allowed

	def start(self):
		self._is_allowed = True

	def stop(self):
		self._is_allowed = False
		self.reset()

	def reset(self):
		self._been_outside = False
		self._auto_pan_delta = QVector2D(0.0, 0.0)
