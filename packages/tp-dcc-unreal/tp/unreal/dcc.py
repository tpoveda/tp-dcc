#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Unreal DCC implementation
"""

import unreal

from Qt.QtWidgets import QDialogButtonBox

from tp.core import dcc
from tp.common.python import decorators
from tp.unreal.core import helpers


# =================================================================================================================
# GENERAL
# =================================================================================================================


def get_name():
    """
    Returns the name of the DCC
    :return: str
    """

    return dcc.Dccs.Unreal


def get_extensions():
    """
    Returns supported extensions of the DCC
    :return: list(str)
    """

    return ['.uproject']


def get_version():
    """
    Returns version of the DCC
    :return: int
    """

    return helpers.get_unreal_version()


def get_version_name():
    """
    Returns version of the DCC
    :return: str
    """

    return helpers.get_unreal_version_name()


def is_batch():
    """
    Returns whether DCC is being executed in batch mode or not
    :return: bool
    """

    return False


def enable_component_selection():
    """
    Enables DCC component selection mode
    """

    pass


# =================================================================================================================
# GUI
# =================================================================================================================

def get_dpi(value=1):
    """
    Returns current DPI used by DCC
    :param value: float
    :return: float
    """

    return 1.0


def get_dpi_scale(value):
    """
    Returns current DPI scale used by DCC
    :return: float
    """

    return 1.0


def get_main_window():
    """
    Returns Qt object that references to the main DCC window
    :return:
    """

    return None


def get_main_menubar():
    """
    Returns Qt object that references to the main DCC menubar
    :return:
    """

    return None


def warning(message):
    """
    Prints a warning message
    :param message: str
    :return:
    """

    unreal.log_warning(message)


def error(message):
    """
    Prints a error message
    :param message: str
    :return:
    """

    unreal.log_error(message)


def is_window_floating(window_name):
    """
    Returns whether or not DCC window is floating
    :param window_name: str
    :return: bool
    """

    return False


def confirm_dialog(title, message, button=None, cancel_button=None, default_button=None, dismiss_string=None):
    """
    Shows DCC confirm dialog
    :param title:
    :param message:
    :param button:
    :param cancel_button:
    :param default_button:
    :param dismiss_string:
    :return:
    """

    from tp.common.qt.widgets import messagebox

    buttons = button or QDialogButtonBox.Yes | QDialogButtonBox.No
    if cancel_button:
        buttons = buttons | QDialogButtonBox.Cancel

    return messagebox.MessageBox.question(None, title=title, text=message, buttons=buttons)


# =================================================================================================================
# DECORATORS
# =================================================================================================================

def undo_decorator():
    """
    Returns undo decorator for current DCC
    """

    return decorators.empty_decorator


def repeat_last_decorator(command_name=None):
    """
    Returns repeat last decorator for current DCC
    """

    return decorators.empty_decorator(command_name)


def restore_selection_decorator():
    """
    Returns decorators that selects again the objects that were selected before executing the decorated function
    """

    return decorators.empty_decorator
