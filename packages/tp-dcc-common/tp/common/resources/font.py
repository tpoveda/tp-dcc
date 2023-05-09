#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines classes and functions that extend QFont functionality
"""

import os

from Qt.QtWidgets import QApplication
from Qt.QtGui import QFontDatabase, QFontMetrics

from tp.core import log
from tp.common.python import path, folder
from tp.common.qt import consts

logger = log.tpLogger


class FontRole(object):
	PRIMARY = 0
	SECONDARY = PRIMARY + 1
	METRICS = SECONDARY + 1


class FontDatabase(QFontDatabase):
	"""
	Helper class to load and retrieve application custom fonts.
	"""

	CACHE = {
		FontRole.PRIMARY: dict(),
		FontRole.SECONDARY: dict(),
		FontRole.METRICS: dict(),
	}

	def __init__(self, parent=None):
		if not QApplication.instance():
			raise RuntimeError('FontDatabase must be created after a QApplication was initiated.')
		super().__init__(parent=parent)

		self._metrics = dict()
		# self.add_custom_fonts()

	# def add_custom_fonts(self):
	# 	"""
	# 	Loads the fonts used by Assets Manager to the font database.
	# 	"""
	#
	# 	if 'Roboto-Medium' in self.families():
	# 		return
	#
	# 	fonts_folder = resources.get('fonts')
	# 	if not path.is_dir(fonts_folder):
	# 		logger.warning('Fonts path "{}" was not found!'.format(fonts_folder))
	# 		return
	#
	# 	for font_folder_name in os.listdir(fonts_folder):
	# 		font_folder_path = path.join_path(fonts_folder, font_folder_name)
	# 		font_files = folder.get_files(font_folder_path, full_path=True, recursive=True)
	# 		for font_file in font_files:
	# 			logger.debug('Registering custom font: {} | {}'.format(path.get_basename(font_file), font_file))
	# 			index = self.addApplicationFont(font_file)
	# 			if index < 0:
	# 				logger.warning('Failed to add required font to the framework')
	# 				continue
	# 			family = self.applicationFontFamilies(index)
	# 			if not family:
	# 				logger.warning('Failed to add required font to the framework')

	def primary_font(self, font_size, family='Roboto', style='Bold'):
		"""
		Returns primary font used by the application.
		"""

		if font_size in self.CACHE[FontRole.PRIMARY]:
			return self.CACHE[FontRole.PRIMARY][font_size]
		font = self.font(family, style, font_size)
		if font.family() != family:
			raise RuntimeError('Failed to add required font to the application')
		font.setPixelSize(font_size)
		metrics = QFontMetrics(font)
		self.CACHE[FontRole.PRIMARY][font_size] = (font, metrics)
		return self.CACHE[FontRole.PRIMARY][font_size]

	def secondary_font(self, font_size=None, family='Roboto', style='Medium'):
		"""
		Returns secondary font used by the application.
		"""

		font_size = font_size if font_size is not None else consts.Sizes.SMALL_FONT_SIZE

		if font_size in self.CACHE[FontRole.SECONDARY]:
			return self.CACHE[FontRole.SECONDARY][font_size]
		font = self.font(family, style, font_size)
		if font.family() != family:
			raise RuntimeError('Failed to add required font to the application')
		font.setPixelSize(font_size)
		metrics = QFontMetrics(font)
		self.CACHE[FontRole.SECONDARY][font_size] = (font, metrics)
		return self.CACHE[FontRole.SECONDARY][font_size]
