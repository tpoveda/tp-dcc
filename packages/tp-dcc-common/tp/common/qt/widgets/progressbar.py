#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for different types of progress bars
"""

from Qt.QtCore import Qt, Property
from Qt.QtWidgets import QSizePolicy, QFrame, QLabel, QProgressBar

from tpDcc.libs.qt.widgets import layouts


class BaseProgressBar(QProgressBar, object):

    ERROR_STATUS = 'error'
    NORMAL_STATUS = 'primary'
    SUCCESS_STATUS = 'success'
    WARNING_STATUS = 'warning'

    def __init__(self, parent=None):
        super(BaseProgressBar, self).__init__(parent)

        self.setAlignment(Qt.AlignCenter)
        self._status = BaseProgressBar.NORMAL_STATUS

    def _get_status(self):
        return self._status

    def _set_status(self, value):
        self._status = value
        self.style().polish(self)

    theme_status = Property(str, _get_status, _set_status)

    def normal(self):
        self.theme_status = BaseProgressBar.NORMAL_STATUS

    def success(self):
        self.theme_status = BaseProgressBar.SUCCESS_STATUS

    def error(self):
        self.theme_status = BaseProgressBar.ERROR_STATUS

    def auto_color(self):
        self.valueChanged.connect(self._on_update_color)

        return self

    def _on_update_color(self, value):
        if value >= self.maximum():
            self.theme_status = BaseProgressBar.SUCCESS_STATUS
        else:
            self.theme_status = self._status


class FrameProgressBar(QFrame, object):
    def __init__(self, *args, **kwargs):
        super(FrameProgressBar, self).__init__(*args, **kwargs)

        layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(layout)

        self._label = QLabel('', self)
        self._label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout.addWidget(self._label)

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setFormat('')
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout.addWidget(self._progress_bar)

    def reset(self):
        """
        Reset progress bar
        """

        self._progress_bar.reset()

    def set_text(self, text):
        """
        Set the text of the progress bar
        :param text: str
        """

        self._label.setText(text)

    def set_value(self, value):
        """
        Set the value of the progress bar
        :param value: int or float
        """

        self._progress_bar.setValue(value)

    def set_range(self, min_, max_):
        """
        Set the range of the progress bar
        :param min_: int
        :param max_: int
        """

        self._progress_bar.setRange(min_, max_)
