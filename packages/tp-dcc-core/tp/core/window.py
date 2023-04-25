#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Dcc window classes
"""

from tp.core import dcc
from tp.core.abstract import window as abstract_window
from tp.common.python import decorators
from tp.common.qt.widgets import window


class _MetaWindow(type):
    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import window as maya_window
            if as_class:
                return maya_window.MayaWindow
            else:
                return type.__call__(maya_window.MayaWindow, *args, **kwargs)
        elif dcc.is_unreal():
            from tp.unreal.ui import window as unreal_window
            if as_class:
                return unreal_window.UnrealWindow
            else:
                return type.__call__(unreal_window.UnrealWindow, *args, **kwargs)
        else:
            if as_class:
                return window.MainWindow
            else:
                return type.__call__(window.MainWindow, *args, **kwargs)


@decorators.add_metaclass(_MetaWindow)
class Window(abstract_window.AbstractWindow):
    pass
