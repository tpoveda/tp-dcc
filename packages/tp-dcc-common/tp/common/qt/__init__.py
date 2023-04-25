#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains library
"""

from __future__ import print_function, division, absolute_import

import sys
import os

from Qt.QtWidgets import QApplication

from tp.common.qt import consts
from tp.common.resources import font

# set preferred binding
os.environ['QT_PREFERRED_BINDING'] = os.pathsep.join(['PySide2', 'PySide2'])


def font_db():

	from tp.common.resources import font

	global FONT_DB
	if not FONT_DB:
		FONT_DB = font.FontDatabase()

	return FONT_DB


def pixel_ratio():

	from Qt.QtWidgets import QApplication

	global PIXEL_RATIO
	if PIXEL_RATIO is None:
		app = QApplication.instance() or QApplication(sys.argv)
		PIXEL_RATIO = 1.0
		try:
			PIXEL_RATIO = app.primaryScreen().devicePixelRatio() if app else 1.0
		except Exception:
			pass

	return PIXEL_RATIO


# NOTE: Important to make sure that QApplication exists before using Qt related functionality
app = QApplication.instance() or QApplication(sys.argv)
FONT_DB = font.FontDatabase()
# pixel ratio used by the loaded image resources
PIXEL_RATIO = 1.0
try:
	PIXEL_RATIO = app.primaryScreen().devicePixelRatio() if app else 1.0
except Exception:
	pass
