#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for custom PySide/PyQt windows
"""

import os

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QLabel
from Qt.QtGui import QMovie


class GifLabel(QLabel, object):
    def __init__(self, gif_file=None, parent=None):
        super(GifLabel, self).__init__('Name', parent)

        self._movie = QMovie(self)
        self._movie.setCacheMode(QMovie.CacheAll)
        self._movie.setSpeed(100)
        self.set_file(gif_file)
        self.setAlignment(Qt.AlignCenter)
        self.setMovie(self._movie)
        self._movie.start()

    def set_file(self, gif_file):
        if not gif_file or not os.path.isfile(gif_file):
            return

        self._movie.setFileName(gif_file)
        self._movie.start()

    def set_size(self, width, height):
        self._movie.setScaledSize(QSize(width, height))
