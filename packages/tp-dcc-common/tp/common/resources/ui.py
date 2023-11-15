#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality to load Qt related UIs from .ui files
"""

from __future__ import print_function, division, absolute_import

import os
import importlib
from xml.etree.ElementTree import ElementTree
from Qt.QtCore import QFile

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from tp.core import log
from tp.common.python import path, folder, fileio

logger = log.tpLogger

_QT_AVAILABLE = True
_UILOADER_AVAILABLE = True
_PYSIDEUIC_AVAILABLE = True
_QT_ERROR_MESSAGE = 'Qt.py is not available and Qt related functionality will not be available!'
try:
    from Qt import QtCore, QtGui, QtWidgets
    from Qt import __binding__
except ImportError as exc:
    _QT_AVAILABLE = False
    _UILOADER_AVAILABLE = False
    _PYSIDEUIC_AVAILABLE = False

if _QT_AVAILABLE:
    if __binding__ == 'PySide6':
        from PySide6.QtCore import QMetaObject # do not remove
        try:
            from PySide6.QtUiTools import QUiLoader
        except ImportError:
            _UILOADER_AVAILABLE = False
        _PYSIDEUIC_AVAILABLE = False
    if __binding__ == 'PySide2':
        from PySide2.QtCore import QMetaObject  # do not remove

        try:
            from PySide2.QtUiTools import QUiLoader
        except ImportError:
            _UILOADER_AVAILABLE = False
        try:
            import pyside2uic as pysideuic
        except ImportError:
            _PYSIDEUIC_AVAILABLE = False
    elif __binding__ == 'PySide':
        from PySide.QtCore import QMetaObject  # do not remove
        try:
            from PySide.QtUiTools import QUiLoader
        except ImportError:
            # NOTE: Some DCCs, such as 3ds Max, does not includes QUiLoader in their defaults libraries
            # It is in the developer side to make sure that sys.path includes a path where QUiLoader can be found
            _UILOADER_AVAILABLE = False
        try:
            import pysideuic
        except ImportError:
            try:
                from tp.common.qt.vendors import pysideuic
            except ImportError:
                _PYSIDEUIC_AVAILABLE = False
    else:
        _UILOADER_AVAILABLE = False
        _PYSIDEUIC_AVAILABLE = False

if _UILOADER_AVAILABLE:
    class UiLoader(QUiLoader):
        """
        Custom UILoader that support custom widgets definition
        Qt.py QtCompat module does not handles custom widgets very well
        This class create the user interface in the given baseinstance instance. If not given,
        created widget is returned

        https://github.com/spyder-ide/qtpy/blob/master/qtpy/uic.py
        https://gist.github.com/cpbotha/1b42a20c8f3eb9bb7cb8
        """

        def __init__(self, baseinstance, customWidgets=None):
            """
            :param baseinstance: loaded user interface is created in the given baseinstance which
            must be an instance of the top-level class in the UI to load, or a subclass thereof
            :param customWidgets: dict, dict mapping from class name to class object for custom widgets
            """
            super(UiLoader, self).__init__(baseinstance)

            self.baseinstance = baseinstance
            if customWidgets is None:
                self.customWidgets = dict()
            else:
                self.customWidgets = customWidgets

        def createWidget(self, class_name, parent=None, name=''):
            """
            Function that is called for each widget defined in ui file,
            overridden here to populate baseinstance instead.
            """

            if parent is None and self.baseinstance:
                # supposed to create the top-level widget, return the base instance instead
                return self.baseinstance

            else:
                # For some reason, Line is not in the list of available widgets, but works fine,
                # so we have to special case it here.
                if class_name in self.availableWidgets() or class_name == 'Line':
                    # create a new widget for child widgets
                    widget = QUiLoader.createWidget(self, class_name, parent, name)
                else:
                    # If not in the list of availableWidgets, must be a custom  widget. This will raise
                    # KeyError if the user has not supplied the relevant class_name in the dictionary or if
                    # customWidgets is empty.
                    try:
                        widget = self.customWidgets[class_name](parent)
                    except KeyError:
                        raise Exception('No custom widget ' + class_name + ' found in customWidgets')
                if self.baseinstance:
                    # set an attribute for the new child widget on the base instance, just like PyQt4.uic.loadUi does.
                    setattr(self.baseinstance, name, widget)

                return widget

        @staticmethod
        def get_custom_widgets(ui_file):
            """
            This function is used to parse a ui file and look for the <customwidgets>
            section, then automatically load all the custom widget classes.
            """

            etree = ElementTree()
            ui = etree.parse(ui_file)
            custom_widgets = ui.find('customwidgets')
            if custom_widgets is None:
                return dict()
            custom_widget_classes = dict()
            for custom_widget in custom_widgets.getchildren():
                cw_class = custom_widget.find('class').text
                cw_header = custom_widget.find('header').text
                module = importlib.import_module(cw_header)
                custom_widget_classes[cw_class] = getattr(module, cw_class)

            return custom_widget_classes


def load_ui(ui_file, parent_widget=None):
    """
    Loads GUI from .ui file.

    :param str ui_file: str, path to the UI file.
    :param QWidget or None parent_widget: QWidget, base instance widget.
    """

    if not _QT_AVAILABLE:
        logger.warning(_QT_ERROR_MESSAGE)
        return None, None

    if not _UILOADER_AVAILABLE:
        logger.error('QtUiLoader is not available, impossible teo load ui file!')
        return None

    # IMPORTANT: do not change customWidgets variable name
    customWidgets = UiLoader.get_custom_widgets(ui_file)
    loader = UiLoader(parent_widget, customWidgets)
    # if workingDirectory is not None:
    #     loader.setWorkingDirectory(workingDirectory)
    widget = loader.load(ui_file)
    QMetaObject.connectSlotsByName(widget)

    return widget


def load_ui_type(ui_file):
    """
    Loads UI Designer file (.ui) and parse the file.

    :param str ui_file: path to the UI file.
    """

    if not _QT_AVAILABLE:
        logger.warning(_QT_ERROR_MESSAGE)
        return None, None

    if not _PYSIDEUIC_AVAILABLE:
        logger.warning('pysideuic is not available. UI compilation functionality is not available!')
        return None, None

    parsed = ElementTree.parse(ui_file)
    widget_class = parsed.find('widget').get('class')
    form_class = parsed.find('class').text
    with open(ui_file, 'r') as f:
        o = StringIO()
        frame = {}
        pysideuic.compileUi(f, o, indent=0)
        pyc = compile(o.getvalue(), '<string>', 'exec')
        exec(pyc in frame)
        # Fetch the base_class and form class based on their type in the XML from designer
        form_class = frame['Ui_{}'.format(form_class)]
        base_class = eval('{}'.format(widget_class))

    return form_class, base_class


def compile_ui(ui_file, py_file=None, use_qt=True):
    """
    Compiles a Py. file from Qt Designer .ui file.

    :param str ui_file: UI file to compile.
    :param str py_file: optional Python that will be used to store UI compile python code.
    :param bool use_qt: whether to use Qt.py when importing Qt modules or use default PySide modules.
    :return: Compiled Python file absolute path.
    :rtype: str

    ..note:: If not py_file is given, the Python compiled code will be stored in the same location where UI file
        is located but with using _ui.py extension. So for example, test.ui would be stored in test_ui.py.
    """

    if not _QT_AVAILABLE:
        logger.warning(_QT_ERROR_MESSAGE)
        return

    if not _PYSIDEUIC_AVAILABLE:
        logger.warning('Was not possible to compile UI file because pysideuic is not available!')
        return

    if not path.is_file(ui_file):
        logger.warning('UI file "{}" does not exists!'.format(ui_file))
        return

    if py_file is None:
        ui_dir, ui_base_name, _ = path.split_path(ui_file)
        py_file = path.join_path(ui_dir, '{}_ui.py'.format(ui_base_name))

    with open(py_file, 'w') as fh:
        pysideuic.compileUi(ui_file, fh, False, 4, False)

    # pysideuic will use the proper Qt version used to compile it when generating .ui Python code
    # pysideuic: PySide | pysideuic2: PySide2
    # here we replace PySide usage with Qt.py module usage
    if path.is_file(py_file) and use_qt:
        fileio.replace(py_file, 'QtGui.', '')
        fileio.replace(py_file, 'QtCore.', '')
        fileio.replace(py_file, 'QtWidgets.', '')

        out_lines = ''
        lines = open(py_file, 'r').readlines()
        for line in lines:
            if 'from PySide' in line or 'from PySide2' in line:
                line = 'from Qt.QtCore import *\nfrom Qt.QtWidgets import *\nfrom Qt.QtGui import *\nfrom Qt import __binding__\n\n'
            if 'QApplication.UnicodeUTF8' in line:
                line = line.replace('QApplication.UnicodeUTF8',
                                    'QApplication.UnicodeUTF8 if __binding__ == "PySide" else -1')
            elif '-1' in line:
                line = line.replace('-1', 'QApplication.UnicodeUTF8 if __binding__ == "PySide" else -1')
            out_lines += '%s' % line
        out = open(py_file, 'w')
        out.writelines(out_lines)
        out.close()

    return py_file


def compile_uis(root_path, recursive=True, use_qt=True):
    """
    Loops through all files starting from root_path and compiles all .ui files.

    :param str root_path: path where we want to compiles uis from.
    :param bool recursive: whether to compile only ui files on given path or compiles all paths recursively.
    :param bool use_qt: whether to use Qt.py when importing Qt modules or use default PySide modules.
    """

    if not _QT_AVAILABLE:
        logger.warning(_QT_ERROR_MESSAGE)
        return

    if not path.is_dir(root_path):
        logger.error('Impossible to compile UIs because path "{}" is not valid!'.format(root_path))
        return

    ui_files = folder.get_files(root_path, full_path=True, recursive=recursive, pattern='*.ui') or list()
    for ui_file in ui_files:
        py_file = ui_file.replace('.ui', '_ui.py')

        logger.debug('> COMPILING: {}'.format(ui_file))
        compile_ui(ui_file=ui_file, py_file=py_file, use_qt=use_qt)


def clean_compiled_uis(root_path, pattern='*_ui.py*', recursive=True):
    """
    Loops through all files starting from root_path and removes all compile ui files.
    :param str root_path: path where we want to compiles uis from.
    :param str pattern: pattern used to identify UI files..
    :param bool recursive: whether to compile only compiled ui files on given path or removes all paths recursively.
    """

    ui_files = folder.get_files(root_path, full_path=True, recursive=recursive, pattern=pattern) or list()
    for ui_file in ui_files:
        os.remove(ui_file)
        logger.debug('Removed compiled UI: "{}"'.format(ui_file))


def ui_importer(ui_path):
    """
    Returns the QT Designer UI as a widget

    :param str ui_path: Full path and file name of the .ui file
    :return: Returns the QT Designer UI as a widget
    :rtype: PySide2.QtWidgets.QWidget
    """

    ui_file = QFile(ui_path)
    ui_file.open(QFile.ReadOnly)
    loader = QUiLoader()
    ui_window = loader.load(ui_file)
    ui_file.close()
    return ui_window
