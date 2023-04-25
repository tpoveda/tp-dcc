#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Dcc dialog classes
"""

import contextlib

from tp.core import dcc
from tp.core.abstract import dialog as abstract_dialog
from tp.common.python import decorators
from tp.common.qt import contexts
from tp.common.qt.widgets import dialog


class _MetaDialog(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import dialog as maya_dialog
            if as_class:
                return maya_dialog.MayaDialog
            else:
                return type.__call__(maya_dialog.MayaDialog, *args, **kwargs)
        else:
            if as_class:
                return dialog.BaseDialog
            else:
                return type.__call__(dialog.BaseDialog, *args, **kwargs)


class _MetaColorDialog(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import dialog as maya_dialog
            if as_class:
                return maya_dialog.MayaColorDialog
            else:
                return type.__call__(maya_dialog.MayaColorDialog, *args, **kwargs)
        else:
            if as_class:
                return dialog.BaseColorDialog
            else:
                return type.__call__(dialog.BaseColorDialog, *args, **kwargs)


class _MetaOpenFileDialog(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import dialog as maya_dialog
            if as_class:
                return maya_dialog.MayaOpenFileDialog
            else:
                return type.__call__(maya_dialog.MayaOpenFileDialog, *args, **kwargs)
        else:
            if as_class:
                return dialog.BaseOpenFileDialog
            else:
                return type.__call__(dialog.BaseOpenFileDialog, *args, **kwargs)


class _MetaSaveFileDialog(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import dialog as maya_dialog
            if as_class:
                return maya_dialog.MayaSaveFileDialog
            else:
                return type.__call__(maya_dialog.MayaSaveFileDialog, *args, **kwargs)
        else:
            if as_class:
                return dialog.BaseSaveFileDialog
            else:
                return type.__call__(dialog.BaseSaveFileDialog, *args, **kwargs)


class _MetaSelectFolderDialog(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import dialog as maya_dialog
            if as_class:
                return maya_dialog.MayaSelectFolderDialog
            else:
                return type.__call__(maya_dialog.MayaSelectFolderDialog, *args, **kwargs)
        else:
            if as_class:
                return dialog.BaseSelectFolderDialog
            else:
                return type.__call__(dialog.BaseSelectFolderDialog, *args, **kwargs)


class _MetaNativeFolderDialog(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import dialog as maya_dialog
            if as_class:
                return maya_dialog.MayaNativeDialog
            else:
                return type.__call__(maya_dialog.MayaNativeDialog, *args, **kwargs)
        else:
            if as_class:
                return dialog.BaseNativeDialog
            else:
                return type.__call__(dialog.BaseNativeDialog, *args, **kwargs)


@decorators.add_metaclass(_MetaDialog)
class Dialog(abstract_dialog.AbstractDialog):
    pass


@decorators.add_metaclass(_MetaColorDialog)
class ColorDialog(abstract_dialog.AbstractColorDialog):
    pass


@decorators.add_metaclass(_MetaOpenFileDialog)
class OpenFileDialog(abstract_dialog.AbstractFileFolderDialog):
    pass


@decorators.add_metaclass(_MetaSaveFileDialog)
class SaveFileDialog(abstract_dialog.AbstractFileFolderDialog):
    pass


@decorators.add_metaclass(_MetaSelectFolderDialog)
class SelectFolderDialog(abstract_dialog.AbstractFileFolderDialog):
    pass


@decorators.add_metaclass(_MetaNativeFolderDialog)
class NativeFolderDialog(abstract_dialog.AbstractNativeDialog):
    pass


@contextlib.contextmanager
def exec_dialog(widget, *args, **kwargs):
    with contexts.application():
        exec_fn = kwargs.pop('exec_fn', None)
        force_close_signal = kwargs.pop('force_close_signal', None)
        new_dialog = Dialog(*args, **kwargs)
        new_dialog.main_layout.addWidget(widget)

        if force_close_signal:
            force_close_signal.connect(new_dialog.close)

        new_dialog.exec_()

        if exec_fn and callable(exec_fn):
            exec_fn()

        yield new_dialog
