#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC functionality for MotionBuilder
"""

from tp.core import dcc
from tp.common.python import decorators
from tp.mobu.core import helpers, gui


def get_name():
    """
    Returns the name of the DCC
    :return: str
    """

    return dcc.Dccs.MotionBuilder


def get_extensions():
    """
    Returns supported extensions of the DCC
    :return: list(str)
    """

    return ['.fbx']


def get_allowed_characters():
    """
    Returns regular expression of allowed characters in current DCC
    :return: str
    """

    return 'A-Za-z0-9_. /+*<>=|-'


def get_version():
    """
    Returns version of the DCC
    :return: int
    """

    return helpers.get_mobu_version()


def get_version_name():
    """
    Returns version of the DCC
    :return: str
    """

    return str(helpers.get_mobu_version())


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

    return False


# =================================================================================================================
# GUI
# =================================================================================================================

def get_main_window():
    """
    Returns Qt object that references to the main DCC window
    :return:
    """

    return gui.get_mobu_window()


def get_main_menubar():
    """
    Returns Qt object that references to the main DCC menubar
    :return:
    """

    win = get_main_window()
    menu_bar = win.menuBar()

    return menu_bar


def parent_widget_to_dcc_window(widget):
    """
    Parents given widget to main DCC window
    :param widget: QWidget
    """

    flags = widget.windowFlags()
    widget.setParent(get_main_window())
    widget.setWindowFlags(flags)


# =================================================================================================================
# OBJECTS / NODES
# =================================================================================================================

def node_types():
    """
    Returns dictionary that provides a mapping between tpDcc object types and  DCC specific node types
    Can be the situation where a tpDcc object maps maps to more than one MFn object
    None values are ignored. This is because either do not exists or there is not equivalent type in Maya
    :return: dict
    """

    return dict()


def dcc_to_tpdcc_types():
    """
    # Returns a dictionary that provides a mapping between Dcc object types and tpDcc object types
    :return:
    """

    pass


def dcc_to_tpdcc_str_types():
    """
    Returns a dictionary that provides a mapping between Dcc string object types and tpDcc object types
    :return:
    """

    pass


def node_tpdcc_type(self, node, as_string=False):
    """
    Returns the DCC object type as a string given a specific tpDcc object type
    :param node: str
    :param as_string: bool
    :return: str
    """

    pass


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

    return decorators.empty_decorator


def suspend_refresh_decorator():
    """
    Returns decorators that selects again the objects that were selected before executing the decorated function
    """

    return decorators.empty_decorator


def restore_selection_decorator():
    """
    Returns decorators that selects again the objects that were selected before executing the decorated function
    """

    return decorators.empty_decorator
