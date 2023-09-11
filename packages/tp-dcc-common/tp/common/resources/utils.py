#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility module that contains useful utilities functions for resources
"""

import os
import re
import sys
import subprocess
from xml.etree import ElementTree

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from Qt import __binding__
from Qt.QtWidgets import QApplication

from tp.core import log
from tp.common.python import strings, path, fileio

DEFAULT_DPI = 96

QT_AVAILABLE = True
UILOADER_AVAILABLE = True
PYSIDEUIC_AVAILABLE = True
QT_ERROR_MESSAGE = 'Qt.py is not available and Qt related functionality will not be available!'

logger = log.tpLogger

try:
    from Qt import QtCore, QtGui, QtWidgets
except ImportError as exc:
    QT_AVAILABLE = False
    logger.warning('Impossible to load Qt libraries. Qt dependant functionality will be disabled!')

if QT_AVAILABLE:
    if __binding__ == 'PySide2':
        from PySide2.QtCore import QMetaObject      # Do not remove
        try:
            from PySide2.QtUiTools import QUiLoader
        except ImportError:
            UILOADER_AVAILABLE = False
        try:
            import pyside2uic as pysideuic
        except ImportError:
            PYSIDEUIC_AVAILABLE = False
    elif __binding__ == 'PySide':
        from PySide.QtCore import QMetaObject       # Do not remove
        try:
            from PySide.QtUiTools import QUiLoader
        except ImportError:
            # NOTE: Some DCCs, such as 3ds Max, does not includes QUiLoader in their defaults libraries
            # It is in the user side to make sure that sys.path includes a path where QUiLoader can be
            # found
            UILOADER_AVAILABLE = False
        try:
            import pysideuic
        except ImportError:
            PYSIDEUIC_AVAILABLE = False
    else:
        UILOADER_AVAILABLE = False
        PYSIDEUIC_AVAILABLE = False


if UILOADER_AVAILABLE:
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
            Constructor
            :param baseinstance: loaded user interface is created in the given baseinstance which
            must be an instance of the top-level class in the UI to load, or a subclass thereof
            :param customWidgets: dict, dict mapping from class name to class object for custom widgets
            """
            super(UiLoader, self).__init__(baseinstance)

            self.baseinstance = baseinstance

            if customWidgets is None:
                self.customWidgets = {}
            else:
                self.customWidgets = customWidgets

        def createWidget(self, class_name, parent=None, name=''):
            """
            Function that is called for each widget defined in ui file,
            overridden here to populate baseinstance instead.
            """

            if parent is None and self.baseinstance:
                # supposed to create the top-level widget, return the base
                # instance instead
                return self.baseinstance

            else:

                # For some reason, Line is not in the list of available
                # widgets, but works fine, so we have to special case it here.
                if class_name in self.availableWidgets() or class_name == 'Line':
                    # create a new widget for child widgets
                    widget = QUiLoader.createWidget(self, class_name, parent, name)

                else:
                    # If not in the list of availableWidgets, must be a custom
                    # widget. This will raise KeyError if the user has not
                    # supplied the relevant class_name in the dictionary or if
                    # customWidgets is empty.
                    try:
                        widget = self.customWidgets[class_name](parent)
                    except KeyError:
                        raise Exception('No custom widget ' + class_name + ' '
                                        'found in customWidgets')

                if self.baseinstance:
                    # set an attribute for the new child widget on the base
                    # instance, just like PyQt4.uic.loadUi does.
                    setattr(self.baseinstance, name, widget)

                return widget

        @staticmethod
        def get_custom_widgets(ui_file):
            """
            This function is used to parse a ui file and look for the <customwidgets>
            section, then automatically load all the custom widget classes.
            """

            import importlib
            from xml.etree.ElementTree import ElementTree

            etree = ElementTree()
            ui = etree.parse(ui_file)

            custom_widgets = ui.find('customwidgets')

            if custom_widgets is None:
                return {}

            custom_widget_classes = {}

            for custom_widget in custom_widgets.getchildren():

                cw_class = custom_widget.find('class').text
                cw_header = custom_widget.find('header').text

                module = importlib.import_module(cw_header)

                custom_widget_classes[cw_class] = getattr(module, cw_class)

            return custom_widget_classes


def is_pyqt():
    """
    Returns True if the current Qt binding is PyQt
    :return: bool
    """

    return 'PyQt' in __binding__


def is_pyqt4():
    """
    Retunrs True if the currente Qt binding is PyQt4
    :return: bool
    """

    return __binding__ == 'PyQt4'


def is_pyqt5():
    """
    Retunrs True if the currente Qt binding is PyQt5
    :return: bool
    """

    return __binding__ == 'PyQt5'


def is_pyside():
    """
    Returns True if the current Qt binding is PySide
    :return: bool
    """

    return __binding__ == 'PySide'


def is_pyside2():
    """
    Returns True if the current Qt binding is PySide2
    :return: bool
    """

    return __binding__ == 'PySide2'


def is_pyside6():
    """
    Returns True if the current Qt binding is PySide6
    :return: bool
    """

    return __binding__ == 'PySide6'


def dpi_multiplier():
    """
    Returns current application DPI multiplier
    :return: float
    """

    return max(1, float(QApplication.desktop().logicalDpiY()) / float(DEFAULT_DPI))


def dpi_scale(value):
    """
    Resizes by value based on current DPI
    :param int value: value default 2k size in pixels
    :return: size in pixels now DPI monitor is (4k 2k etc)
    :rtype: int
    """

    mult = dpi_multiplier()
    return value * mult


def find_rcc_executable_file():
    """
    Returns path pointing to a valid PySide/PyQt RCC executable file
    :return: str
    """

    # TODO: Implement PyQt RCC search
    # TODO: Make it work in a cross platform way. For now this only works in Windows.

    if is_pyside() or is_pyside2() or is_pyside6():
        rcc_exe_path = os.environ.get('PYSIDE_RCC_EXE_PATH', None)
        if rcc_exe_path:
            rcc_exe_path = path.clean_path(rcc_exe_path)
            if os.path.isfile(rcc_exe_path):
                return rcc_exe_path

    folders_to_find = list()
    exe_name = None
    if is_pyside():
        exe_name = 'pyside-rcc.exe'
        folders_to_find.extend([
            'C:\\Python27\\Lib\\site-packages\\PySide\\',
            os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'PySide'),
            os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Lib', 'site-packages', 'PySide')
        ])
    elif is_pyside2():
        exe_name = 'pyside2-rcc.exe'
        folders_to_find.extend([
            'C:\\Python38\\Lib\\site-packages\\PySide2\\',
            os.path.join(os.path.dirname(sys.executable)),
        ])
    elif is_pyside6():
        exe_name = 'pyside6-rcc.exe'
        folders_to_find.extend([
            'C:\\Python310\\Lib\\site-packages\\PySide6\\',
            os.path.join(os.path.dirname(sys.executable)),
        ])
    if not exe_name:
        logger.warning('No valid RCC executable find found!')
        return

    for folder in folders_to_find:
        rcc_file_path = path.clean_path(os.path.join(folder, exe_name))
        if not os.path.isfile(rcc_file_path):
            continue
        return rcc_file_path

    return None


def create_python_qrc_file(qrc_file: str, py_file: str):
    """
    Creates a Python file from a QRC file.

    :param str qrc_file: QRC file name.
    :param str py_file: str
    """

    if not os.path.isfile(qrc_file):
        return

    pyside_rcc_exe_path = find_rcc_executable_file()
    if not pyside_rcc_exe_path or not os.path.isfile(pyside_rcc_exe_path):
        logger.warning('Impossible to generate Python QRC file because no PySide RCC executable path found!')
        return

    try:
        subprocess.check_output(f'"{pyside_rcc_exe_path}" -o "{py_file}" "{qrc_file}"')
    except subprocess.CalledProcessError as e:
        raise RuntimeError('command {0} returned with error (code: {1}): {2}'.format(e.cmd, e.returncode, e.output))
    if not os.path.isfile(py_file):
        return

    # We update file to make sure it works with Qt.py, and it works with both Python 2 and Python 3
    elif is_pyside2() or is_pyside6():
        fileio.replace(py_file, "from PySide2 import QtCore", "from Qt import QtCore")
    else:
        fileio.replace(py_file, "from PySide import QtCore", "from Qt import QtCore")
        lines = fileio.get_file_lines(py_file)
        lines = lines[:-8]
        fileio.write_lines(py_file, lines)
        lines_to_append = [
            'def qInitResources():',
            '\ttry:',
            '\t\tQtCore.qRegisterResourceData(0x01, qt_resource_struct, qt_resource_name, qt_resource_data)',
            '\texcept Exception:',
            '\t\tQtCore.qRegisterResourceData(0x01, qt_resource_struct, '
            'qt_resource_name, qt_resource_data)',
            '\ndef qCleanupResources():',
            '\ttry:',
            '\t\tQtCore.qUnregisterResourceData(0x01, qt_resource_struct, qt_resource_name, qt_resource_data)',
            '\texcept Exception:',
            '\t\tQtCore.qUnregisterResourceData(0x01, qt_resource_struct, '
            'qt_resource_name, qt_resource_data)\n',
        ]
        fileio.write_lines(py_file, lines_to_append, append=True)


def create_qrc_file(src_paths, dst_file):

    def _default_filter(x):
        return not x.startswith(".")

    def tree(top='.',
             filters=None,
             output_prefix=None,
             max_level=4,
             followlinks=False,
             top_info=False,
             report=True):
        # The Element of filters should be a callable object or
        # is a byte array object of regular expression pattern.
        topdown = True
        total_directories = 0
        total_files = 0

        top_fullpath = os.path.realpath(top)
        top_par_fullpath_prefix = os.path.dirname(top_fullpath)

        if top_info:
            lines = top_fullpath
        else:
            lines = ""

        if filters is None:
            filters = [_default_filter]

        for root, dirs, files in os.walk(top=top_fullpath, topdown=topdown, followlinks=followlinks):
            assert root != dirs

            if max_level is not None:
                cur_dir = strings.strips(root, top_fullpath)
                path_levels = strings.strips(cur_dir, "/").count("/")
                if path_levels > max_level:
                    continue

            total_directories += len(dirs)
            total_files += len(files)

            for filename in files:
                for _filter in filters:
                    if callable(_filter):
                        if not _filter(filename):
                            total_files -= 1
                            continue
                    elif not re.search(_filter, filename, re.UNICODE):
                        total_files -= 1
                        continue

                    if output_prefix is None:
                        cur_file_fullpath = os.path.join(top_par_fullpath_prefix, root, filename)
                    else:
                        buf = strings.strips(os.path.join(root, filename), top_fullpath)
                        if output_prefix != "''":
                            cur_file_fullpath = os.path.join(output_prefix, buf.strip('/'))
                        else:
                            cur_file_fullpath = buf

                    lines = "%s%s%s" % (lines, os.linesep, cur_file_fullpath)

        lines = lines.lstrip(os.linesep)

        if report:
            report = "%d directories, %d files" % (total_directories, total_files)
            lines = "%s%s%s" % (lines, os.linesep * 2, report)

        return lines

    def scan_files(src_path="."):
        filters = ['.(png|jpg|gif)$']
        output_prefix = './'
        report = False
        lines = tree(src_path, filters=filters, output_prefix=output_prefix, report=report)

        lines = lines.split('\n')
        if "" in lines:
            lines.remove("")

        return lines

    def create_qrc_body(src_path, root_res_path, use_alias=True):

        res_folder_files = path.get_absolute_file_paths(src_path)
        lines = [os.path.relpath(f, root_res_path) for f in res_folder_files]

        if use_alias:
            buf = ['\t\t<file alias="{0}">{1}</file>\n'.format(os.path.splitext(
                os.path.basename(i))[0].lower().replace('-', '_'), i).replace('\\', '/') for i in lines]
        else:
            buf = ["\t\t<file>{0}</file>\n".format(i).replace('\\', '/') for i in lines]
        buf = "".join(buf)
        # buf = QRC_TPL % buf
        return buf

    # Clean existing resources files and append initial resources header text
    if dst_file:
        parent = os.path.dirname(dst_file)
        if not os.path.exists(parent):
            os.makedirs(parent)
        with open(dst_file, 'w') as fh:
            fh.write('<RCC>\n')
            for res_folder in src_paths:
                res_path = os.path.dirname(res_folder)
                start_header = '\t<qresource prefix="{0}">\n'.format(os.path.basename(res_folder))
                qrc_body = create_qrc_body(res_folder, res_path)
                end_header = '\t</qresource>\n'
                res_text = start_header + qrc_body + end_header
                fh.write(res_text)

            # Write end header
            fh.write('</RCC>')


def load_ui(ui_file, parent_widget=None):
    """
    Loads GUI from .ui file
    :param ui_file: str, path to the UI file
    :param parent_widget: QWidget, base instance widget
    :param force_pyside: bool, True to force using PySide1 load UI.
        Sometimes PySide2 gives error when working with custom widgets
    """

    if not QT_AVAILABLE:
        logger.error(QT_ERROR_MESSAGE)
        return None

    if not UILOADER_AVAILABLE:
        logger.error('QtUiLoader is not available, impossible teo load ui file!')
        return None

    # IMPORTANT: Do not change customWidgets variable name
    customWidgets = UiLoader.get_custom_widgets(ui_file)
    loader = UiLoader(parent_widget, customWidgets)
    # if workingDirectory is not None:
    #     loader.setWorkingDirectory(workingDirectory)
    widget = loader.load(ui_file)
    QMetaObject.connectSlotsByName(widget)
    return widget


def load_ui_type(ui_file):
    """
    Loads UI Designer file (.ui) and parse the file
    :param ui_file: str, path to the UI file
    """

    if not QT_AVAILABLE:
        logger.warning(QT_ERROR_MESSAGE)
        return None, None

    if not PYSIDEUIC_AVAILABLE:
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


def compile_ui(ui_file, py_file):
    """
    Compiles a Py. file from Qt Designer .ui file
    :param ui_file: str
    :param py_file: str
    :return:
    """

    if not QT_AVAILABLE:
        logger.warning(QT_ERROR_MESSAGE)
        return

    if not PYSIDEUIC_AVAILABLE:
        logger.warning('pysideuic is not available. UI compilation functionality is not available!')
        return

    if not os.path.isfile(ui_file):
        logger.warning('UI file "{}" does not exists!'.format(ui_file))
        return

    if os.path.isfile(ui_file):
        f = open(py_file, 'w')
        pysideuic.compileUi(ui_file, f, False, 4, False)
        f.close()


def compile_uis(root_path, recursive=True, use_qt=True):
    """
    Loops through all files starting from root_path and compiles all .ui files
    :param root_path: str, path where we want to compiles uis from
    :param recursive: bool, Whether to compile only ui files on given path or compiles all paths recursively
    :param use_qt: bool, Whether to use Qt.py when importing Qt modules or use default PySide modules
    """

    if not QT_AVAILABLE:
        logger.warning(QT_ERROR_MESSAGE)
        return

    if not os.path.exists(root_path):
        logger.error('Impossible to compile UIs because path "{}" is not valid!'.format(root_path))
        return

    if recursive:
        for root, _, files in os.walk(root_path):
            for f in files:
                if f.endswith('.ui'):
                    ui_file = os.path.join(root, f)

                    py_file = ui_file.replace('.ui', '_ui.py')

                    logger.debug('> COMPILING: {}'.format(ui_file))
                    compile_ui(ui_file=ui_file, py_file=py_file)

                    # pysideuic will use the proper Qt version used to compile it when generating .ui Python code
                    # pysideuic: PySide | pysideuic2: PySide2
                    # Here we replace PySide usage with Qt.py module usage
                    if os.path.exists(py_file) and use_qt:

                        fileio.replace(py_file, 'QtGui.', '')
                        fileio.replace(py_file, 'QtCore.', '')
                        fileio.replace(py_file, 'QtWidgets.', '')

                        out_lines = ''
                        lines = open(py_file, 'r').readlines()
                        for line in lines:
                            if 'from PySide' in line or 'from PySide2' in line:
                                line = 'try:\n\tfrom PySide.QtCore import *\n\tfrom PySide.QtGui import ' \
                                       '*\nexcept:\n\tfrom PySide2.QtCore import *\n\tfrom PySide2.QtWidgets import ' \
                                       '*\n\tfrom PySide2.QtGui import *\nfrom Qt import __binding__\n\n'
                            if 'QApplication.UnicodeUTF8' in line:
                                line = line.replace('QApplication.UnicodeUTF8',
                                                    'QApplication.UnicodeUTF8 if __binding__ == "PySide" else -1')
                            elif '-1' in line:
                                line = line.replace('-1', 'QApplication.UnicodeUTF8 if __binding__ == "PySide" else -1')

                            out_lines += '%s' % line
                        out = open(py_file, 'w')
                        out.writelines(out_lines)
                        out.close()
    else:
        raise NotImplementedError()


def clean_compiled_uis(root_path, recusive=True):
    """
    Loops through all files starting from root_path and removes all compile ui files
    :param root_path: str, path where we want to compiles uis from
    :param recursive: bool, Whether to compile only compiled ui files on given path or removes all paths recursively
    """

    if recusive:
        for root, _, files in os.walk(root_path):
            for f in files:
                if f.endswith('_ui.py') or f.endswith('_ui.pyc'):
                    os.remove(os.path.join(root, f))
                    logger.debug('Removed compiled UI: "{}"'.format(os.path.join(root, f)))
