#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains thumbnail functionality
"""

import os
import shutil

from Qt.QtCore import Signal

from tp.common.qt import qtutils
from tp.common.qt.widgets import layouts, buttons, dialog
from tp.maya.cmds import modelpanel, playblast, gui

_instance = None


class ThumbnailCaptureDialog(dialog.BaseDialog, object):

    DEFAULT_WIDTH = 250
    DEFAULT_HEIGHT = 250

    captured = Signal(str)
    capturing = Signal(str)

    @staticmethod
    def thumbnail_capture(
            path, start_frame=None, end_frame=None, step=1, clear_cache=False,
            captured=None, show=False, modifier=True):
        """
        Helper function to capture a playblast and save it to the given path
        :param path: str
        :param start_frame: int or None
        :param end_frame: int or None
        :param step: int
        :param clear_cache: bool
        :param captured: fn or None
        :param show: bool
        :param modifier:
        :return: ThumbnailCaptureDialog
        """

        global _instance

        def _clear_cache():
            dir_name = os.path.dirname(path)
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)

        if _instance:
            _instance.close()

        d = ThumbnailCaptureDialog(path=path, start_frame=start_frame, end_frame=end_frame, step=step)
        if captured:
            d.captured.connect(captured)
        if clear_cache:
            d.capturing.connect(_clear_cache)
        d.show()

        if not show and not (modifier and qtutils.is_control_modifier()):
            d._on_capture()
            d.close()

        _instance = d

        return _instance

    def __init__(self, path='', start_frame=None, end_frame=None, step=1, parent=None):
        super(ThumbnailCaptureDialog, self).__init__(
            name='CaptureThumbnailDialog',
            title='Capture Dialog',
            parent=parent
        )

        self._path = path
        self._step = step
        self._end_frame = None
        self._start_frame = None
        self._captured_path = None

        if start_frame is None:
            start_frame = int(gui.current_frame())
        if end_frame is None:
            end_frame = int(gui.current_frame())
        self.set_start_frame(start_frame)
        self.set_end_frame(end_frame)

        self._capture_btn = buttons.BaseButton('Capture', parent=self)
        self._capture_btn.clicked.connect(self._on_capture)
        self._model_panel_widget = modelpanel.ModelPanelWidget(parent=self)
        # self._model_panel_widget = viewport.MayaViewport(parent=self)
        main_layout = layouts.VerticalLayout()
        main_layout.setObjectName(self.objectName() + 'Layout')
        main_layout.addWidget(self._model_panel_widget)
        main_layout.addWidget(self._capture_btn)
        self.main_layout.addLayout(main_layout)

        width = self.DEFAULT_WIDTH * 1.5
        height = (self.DEFAULT_HEIGHT * 1.5) + 50
        self.set_width_height(width, height)
        self.center(to_cursor=True)

    def capture_path(self):
        """
        Returns the location of the captured thumbnail
        :return: str
        """

        return self._captured_path

    def path(self):
        """
        Returns the target path
        :return: str
        """

        return self._path

    def set_path(self, path):
        """
        Sets the target path
        :param path: str
        """

        self._path = path

    def end_frame(self):
        """
        Returns the end frame of the thumbnail
        :return: int
        """

        return self._end_frame

    def set_end_frame(self, frame):
        """
        Sets the end frame of the thumbnail
        :param frame: int
        """

        self._end_frame = frame

    def start_frame(self):
        """
        Returns the start frame of the thumbnail
        :return: int
        """

        return self._start_frame

    def set_start_frame(self, frame):
        """
        Sets the start frame of the thumbnail
        :param frame: int
        """

        self._start_frame = frame

    def step(self):
        """
        Returns the step amount of the thumbnail
        :return: int
        """

        return self._step

    def set_step(self, step):
        """
        Sets the step amount of the thumbnail
        For example, if the step is set to 2, it will thumbnail every second frame
        :param step: int
        """

        self._step = step

    def _on_capture(self):
        """
        Internal function that captures a playblast and save it to the given path
        """

        path = self.path()
        self.capturing.emit(path)
        model_panel = self._model_panel_widget.name()
        start_frame = self.start_frame()
        end_frame = self.end_frame()
        step = self.step()
        width = self.DEFAULT_HEIGHT
        height = self.DEFAULT_HEIGHT

        self._captured_path = playblast.playblast(
            filename=path, model_panel=model_panel, start_frame=start_frame,
            end_frame=end_frame, width=width, height=height, step=step
        )

        self.accept()
        self.captured.emit(self._captured_path)

        return self._captured_path
