# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with Autodesk 3ds Max
"""

from Qt.QtWidgets import QWidget

import MaxPlus

from tp.common.python import path
from tp.common.qt import qtutils
from tp.max.core import helpers


def get_max_window():
    """
    Returns an instance of the current Max window
    """

    # 17000 = Max 2015
    # 18000 = Max 2016
    # 19000 = Max 2017
    # 20000 = Max

    version = int(helpers.get_max_version(as_year=True))

    if version == 2014:
        import ctypes
        import ctypes.wintypes
        # Swig Object Containing HWND *
        pyobject = MaxPlus.Win32.GetMAXHWnd()
        # Getting actual HWND* mem address
        hwndptr = pyobject.__int__()
        # Casting to HWD* of Void*
        ptr = ctypes.c_void_p(hwndptr)
        # Getting actual Void* mem address (should be same as hwndptr)
        ptrvalue = ptr.value
        # Getting derefeerence Void* and get HWND as c_longlong
        clonglong = ctypes.c_longlong.from_address(ptrvalue)
        # Getting actual HWND value from c_longlong
        longhwnd = clonglong.value
        # Getting derefeerence Void* and get HWND as c_longlong
        chwnd = ctypes.wintypes.HWND.from_address(ptrvalue)
        # Getting actual HWND value from c_longlong
        hwnd = clonglong.value
        return hwnd
    elif version == 2015 or version == 2016:
        return long(MaxPlus.Win32.GetMAXHWnd())
    elif version == 2017:
        return MaxPlus.GetQMaxWindow()
    else:
        return MaxPlus.GetQMaxMainWindow()


def to_qt_object(max_ptr, qobj=None):
    """
    Returns an instance of the Max UI element as a QWidget
    """

    if qtutils.QT_AVAILABLE:
        if not qobj:
            qobj = QWidget
        if max_ptr is not None:
            return qtutils.wrapinstance(long(max_ptr), qobj)

    return None


def open_get_path_dialog(init_directory=None):
    """
    Opens standard 3ds Max get path dialog
    :param init_directory: str, init directory to browse
    :return: str
    """

    result = MaxPlus.FPValue()
    if init_directory is None:
        MaxPlus.Core.EvalMAXScript('getSavePath caption:"Export directory" initialDir:(getDir #maxroot)', result)
    else:
        MaxPlus.Core.EvalMAXScript('getSavePath caption:"Export directory" initialDir:"{}"'.format(
            path.clean_path(init_directory)), result)

    try:
        selected_path = result.Get()
        return selected_path
    except Exception:
        return ""


def show_error_window(title, message):
    """
    Shows a native Max error window with the given title and message
    :param title: str, title of the error window
    :param message: str, message of the error window
    """

    message = message.replace("\"", "\\\"")
    cmd = 'messageBox "{}" title:"{}" beep:False'.format(message, title)
    MaxPlus.Core.EvalMAXScript(cmd)


def show_warning_message(message):
    """
    Prints a warning message in the 3ds Max listener window
    :param message: str, message of the warning
    """

    message = message.replace("\"", "\\\"")
    cmd = ''.join(('print "', message, '"'))
    MaxPlus.Core.EvalMAXScript(cmd)
