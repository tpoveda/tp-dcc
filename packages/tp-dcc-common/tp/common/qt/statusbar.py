#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that creates a status widgets which can be used the state of an app
"""

from Qt.QtCore import Qt, Property, QSize, QTimer
from Qt.QtWidgets import QSizePolicy, QHBoxLayout, QFrame
from Qt.QtGui import QPixmap

from tp.core.managers import resources
# from tp.common.resources import theme


# @theme.mixin
class StatusWidget(QFrame, object):

    DEFAULT_DISPLAY_TIME = 10000  # milliseconds -> 10 seconds

    def __init__(self, *args):
        super(StatusWidget, self).__init__(*args)

        self._status = None
        self._blocking = False
        self._timer = QTimer(self)

        self.setObjectName('StatusWidget')
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(19)
        self.setMinimumWidth(5)

        self._label = label.BaseLabel('', parent=self)
        self._label.setStyleSheet('background-color: transparent;')
        self._label.setCursor(Qt.IBeamCursor)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.label_image = label.BaseLabel(parent=self)
        self.label_image.setMaximumSize(QSize(17, 17))
        self.label_image.hide()

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(1, 0, 0, 0)

        self.main_layout.addWidget(self.label_image)
        self.main_layout.addWidget(self._label)

        self.setLayout(self.main_layout)

        self._timer.timeout.connect(self._reset)

        # Force set to initialize default status Qt property
        self.status = ''

    def _get_status(self):
        return self._status

    def _set_status(self, value):
        self._status = str(value)
        self.polish()

    status = Property(str, _get_status, _set_status)

    def is_blocking(self):
        """
        Returns True if the status widget is blocking, otherwise return False
        :return: bool
        """

        return self._blocking

    def show_ok_message(self, message, msecs=None):
        """
        Set an ok message to be displayed in the status widget
        :param message: str
        :param msecs: int
        """

        if self.is_blocking():
            return

        self.status = 'ok'
        icon = resources.icon('ok')
        self._show_message(message, icon, msecs)

    def show_info_message(self, message, msecs=None):
        """
        Set an info message to be displayed in the status widget
        :param message: str
        :param msecs: int
        """

        if self.is_blocking():
            return

        self.status = 'info'
        icon = resources.icon('info')
        self._show_message(message, icon, msecs)

    def show_warning_message(self, message, msecs=None):
        """
       Set a warning message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        if self.is_blocking():
            return

        self.status = 'warning'
        icon = resources.icon('warning')
        self._show_message(message, icon, msecs)

    def show_error_message(self, message, msecs=None):
        """
       Set an error message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        self.status = 'error'
        icon = resources.icon('error', extension='png')
        self._show_message(message, icon, msecs, blocking=True)

    def _reset(self):
        """
        Called when the current animation has finished
        """

        self._timer.stop()
        self.label_image.setVisible(False)
        self._label.setText('')
        icon = resources.pixmap('blank')
        self.label_image.setPixmap(icon) if icon else self.label_image.setPixmap(QPixmap())
        self.setStyleSheet('')
        self._blocking = False
        self.status = ''

    def _show_message(self, message, icon, msecs=None, blocking=False):
        """
        Set the given text to be displayed in the status widget
        :param message: str
        :param icon: QIcon
        :param msecs: int
        :param blocking: bool
        """

        msecs = msecs or self.DEFAULT_DISPLAY_TIME
        self._blocking = blocking

        self.label_image.setStyleSheet('border: 0px;')

        if icon:
            self.label_image.setPixmap(icon.pixmap(QSize(17, 17)))
            self.label_image.show()
        else:
            self.label_image.hide()

        if message:
            self._label.setText(str(message))
            self._timer.stop()
            self._timer.start(msecs)
        else:
            self._reset()

        self.update()
