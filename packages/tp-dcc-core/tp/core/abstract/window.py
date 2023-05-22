#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC window abstract implementation
"""

from __future__ import annotations

import os
import json
import uuid
import tempfile
from typing import Tuple
from collections import defaultdict

from overrides import override
from Qt.QtCore import Signal, QEvent
from Qt.QtWidgets import QApplication, QWidget, QDialog, QMainWindow, QCheckBox, QMessageBox

from tp.core import dcc
from tp.common.python import path, decorators, win32
from tp.common.resources import palette


class AbstractWindow(QMainWindow):
    """
    Base class for all DCC Qt based windows.

    Each window must be provided with a unique "ID" attribute to enable following features:
        - Saving and loading of its location.
        - Automatic closing of previous windows, if a new one is launched.
    Also, "Name" attribute will define the window title.

    Dockable windows are supported and its functionality must be implemented for each DCC.
    """

    clearedInstance = Signal()
    windowReady = Signal()

    _WINDOW_INSTANCES = dict()

    def __init__(self, parent: QWidget | None = None, **kwargs):
        super().__init__(parent, **kwargs)

        self._enable_state = True
        self._child_window = False
        self._window_closed = False
        self._window_loaded = False
        self._dockable = getattr(self, 'Dockable', False)
        self._was_docked = None
        self._initial_pos_override = None                       # type: Tuple[int, int]
        self._window_palette = None                             # type: str
        self._signals = defaultdict(list)
        self._signals_cache = defaultdict(list)

        self._standalone = False
        self._batch = False
        self._maya = False
        self._nuke = False
        self._houdini = False
        self._max = False
        self._fusion = False
        self._blender = False
        self._unreal = False
        self._painter = False
        self._designer = False

        self._force_disable_saving = not hasattr(self, 'ID')
        if self._force_disable_saving:
            self.ID = str(uuid.uuid4())

        self.setWindowTitle(getattr(self, 'Name', 'New Window'))

        self._window_data_path = self.window_settings_path(self.ID)
        temp_folder = path.dirname(self._window_data_path)
        if not path.is_dir(temp_folder):
            os.makedirs(temp_folder)
        self._window_settings = self.window_settings(self.ID, settings_path=self._window_data_path)

        AbstractWindow._WINDOW_INSTANCES[self.ID] = {
            'window': self,
            'callback': dict()
        }

        self.windowReady.connect(lambda: setattr(self, '_window_loaded', True))

    @classmethod
    def window_settings_path(cls, window_id: str) -> str:
        """
        Returns the path where window settings are stored.

        :param str window_id: ID of the window we want to save settings path.
        :return: window settings absolute path.
        :rtype: str
        """

        return path.join_path(tempfile.gettempdir(), f'tp.dcc.window.{window_id}.json')

    @classmethod
    def window_settings(cls, window_id: str, settings_path: str | None = None):
        """
        Opens the window settings file and returns its contents.

        :param str window_id: ID of the window we want to open settings for.
        :param str or None settings_path: optional path where window settings are located. If not given, settings path
            will be automatically retrieved based on given window_id.
        :return: window settings.
        :rtype: dict
        """

        settings_path = settings_path or cls.window_settings_path(window_id)
        try:
            with open(settings_path, 'r') as f:
                return json.loads(f.read())
        except (IOError, ValueError):
            return dict()

    @classmethod
    def save_window_settings(cls, window_id: str, data: dict, settings_path: str | None) -> bool:
        """
        Save window settings.

        :param str window_id: ID of the window we want to save settings for.
        :param dict data: settings dictionary.
        :param str or None settings_path: optional path where window settings are located. If not given, settings path
            will be automatically retrieved based on given window_id.
        :return: True if save window settings operation was successful; False otherwise.
        :rtype: bool
        """

        settings_path = settings_path or cls.window_settings_path(window_id)
        try:
            with open(settings_path, 'w') as f:
                f.write(json.dumps(data, indent=2))
        except IOError:
            return False

        return True

    @classmethod
    def clear_window_instance(cls, window_id: str) -> dict:
        """
        Closes the lats class instance that matches its ID with the given one.

        :param str window_id: ID of the window to close.
        :return: closed window instance dictionary.
        :rtype: dict
        """

        window_to_close = cls._WINDOW_INSTANCES.pop(window_id, None)
        if window_to_close is not None and not window_to_close['window'].is_dialog():
            try:
                window_to_close['window'].clearedInstance.emit()
            except RuntimeError:
                pass

        return window_to_close

    @classmethod
    def clear_window_instances(cls):
        """
        Internal function that closes down every loaded window.
        """

        for window_id in tuple(cls._WINDOW_INSTANCES):
            cls.clear_window_instance(window_id)

    @decorators.HybridMethod
    @override(check_signature=False)
    def show(cls, self, *args, **kwargs) -> AbstractWindow:
        """
        Shows the window and loads its position.
        """

        # Window has been already initialized
        if self is not cls:
            return super().show()

        # Close existing windows and open a new one
        try:
            cls.clear_window_instance(cls.ID)
        except AttributeError:
            pass
        new_window = cls(*args, **kwargs)
        super(AbstractWindow, new_window).show()
        new_window.load_window_position()
        dcc.deferred_function(new_window.windowReady.emit)

        return new_window

    @override(check_signature=False)
    def closeEvent(self, event: QEvent):
        """
        Closes the window and marks it as closed.

        :param QEvent event: Qt event.
        """

        self._window_closed = True
        self.clear_window_instance(self.ID)
        if self.is_dialog():
            return self.parent().close()

        return super().closeEvent(event)

    def exists(self) -> bool:
        """
        Returns whether this window currently exists.

        :return: True if window exists; False otherwise.
        :rtype: bool
        """

        return True

    def is_instance(self) -> bool:
        """
        Returns whether this window is a child of another window.

        :return: True if this window is a child of another window; False otherwise.
        :rtype: bool
        """

        return self._child_window

    def is_dialog(self) -> bool:
        """
        Returns whether this window is a dialog.

        :return: True if window is a dialog; False otherwise.
        :rtype: bool
        """

        try:
            return isinstance(self.parent(), QDialog)
        except RuntimeError:
            return False

    def is_closed(self) -> bool:
        """
        Returns whether window has been closed.

        :return: True if window has been closed; False otherwise.
        :rtype: bool
        """

        return self._window_closed

    def is_loaded(self) -> bool:
        """
        Returns whether window is currently loaded.

        :return: True if window is currently loaded; False otherwise.
        :rtype: bool
        """

        return self._window_loaded and not self.is_closed()

    def set_enable_save_window_position(self, flag: bool):
        """
        Sets whether save window position should be saved.

        :param bool flag: True to save window position; False otherwise.
        """

        self._enable_state = flag

    def load_window_position(self):
        """
        Loads the previous position or center the window.
        """

        if self.is_instance():
            return

        if self._initial_pos_override is not None:
            x, y = self._initial_pos_override
            x, y = win32.set_coordinates_to_screen(x, y, self.width(), self.height(), padding=5)
            self.move(x, y)
        else:
            self.center()

    def center(self, parent_geometry=None, child_geometry=None):
        """
        Centers the current window to its parent.

        :param parent_geometry:
        :param child_geometry:
        """

        if parent_geometry is None or child_geometry is None:
            base = self.parent() if self.is_dialog() else self
            if parent_geometry is None:
                try:
                    parent_geometry = base.parent().frameGeometry()
                except AttributeError:
                    parent_geometry = QApplication.desktop().screenGeometry()
            child_geometry = child_geometry if child_geometry is not None else base.frameGeometry()

        self.move(
            int(parent_geometry.x() + (parent_geometry.width() - child_geometry.width()) / 2),
            int(parent_geometry.y() + (parent_geometry.height() - child_geometry.height()) / 2),
        )

    def window_palette(self) -> str | None:
        """
        Returns the current palette of the window.

        :return: window palette name.
        :rtype: str or None
        """

        return self._window_palette

    def set_window_palette(self, name: str, version: int | None, style: bool = True):
        """
        Sets palette with given name and version to this window.

        :param str name: name of the paelette to set.
        :param int or None version: optional palette version to set.
        :param bool style:
        """

        palette.set_palette(name, version=version, style=style)
        self._window_palette = f'{name}.{version}' if version is not None else name

    def display_message(
            self, title: str, message: str, details: str | None = None, buttons: Tuple[str, ...] = ('Ok',),
            default_button: str | None = None, cancel_button: str | None = None,
            checkbox: bool | QCheckBox | None = None) -> str | Tuple[str, bool]:
        """
        Displays a popup message box.

        :param str title: title of the message box.
        :param str message: short sentence with a question or statement.
        :param str or None details: optional extra information.
        :param Tuple[str] buttons: defines which buttons to use.
        :param str or None default_button: defines which button is selected by default.
        :param str or None cancel_button: defines which button acts as the no/cancel option.
        :param bool or QCheckBox or None checkbox: optional checkbox to add.
        :return: tuple with the name of  button clicked and the checkbox status if checkbox is not None else the name
            of the button clicked.
        :rtype: str | Tuple[str, bool]
        """

        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setInformativeText(details)

        buttons_dict = dict()
        for button in buttons:
            buttons_dict[getattr(QMessageBox, button)] = button
        standard_buttons = 0
        for button in buttons_dict:
            standard_buttons |= button
        msg.setStandardButtons(standard_buttons)
        msg.setDefaultButton(getattr(QMessageBox, buttons[-1] if default_button is None else default_button))
        if cancel_button is not None:
            msg.setEscapeButton(getattr(QMessageBox, cancel_button))
        if checkbox is not None:
            checkbox = QCheckBox(checkbox) if not isinstance(checkbox, QCheckBox) else checkbox
            try:
                msg.setCheckBox(checkbox)
            except AttributeError:
                pass

        result = buttons_dict[msg.exec_()]

        return result, checkbox.isChecked() if checkbox is not None else result

    def _set_child_window(self, flag: bool):
        """
        Internal function that sets whether this window is a child of another window.

        :param bool flag: True to mark this window as a child of other window; False otherwise.
        """

        self._child_window = flag
