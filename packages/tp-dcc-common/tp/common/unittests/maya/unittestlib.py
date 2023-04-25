#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest function implementations for Maya
"""

import os
import sys

import maya.cmds
import maya.standalone

from tpDcc.libs.unittests.core import settings, unittestlib


def load_default_unit_tests():
    """
    Loads default unit tests of a specific DCC
    """

    pass


def maya_module_tests():
    """
    Generator function to iterate over all the Maya module tests directories
    """

    maya_modules_paths = list()
    for path in os.environ['MAYA_MODULE_PATH'].split(os.pathsep):
        p = '{0}/tests'.format(path)
        if os.path.exists(p):
            maya_modules_paths.append(p)

    return maya_modules_paths


def run_tests_from_command_line():
    """
    Run the tests in Maya standalone mode
    """

    maya.standalone.initialize()

    # Make sure all paths in PYTHONPATH are also in sys.path
    # When a Maya module is loaded, the scripts folder is added to PYTHONPATH, but it doesn't seem to be added
    # sys.path. So we are unable to import any of the python files that are in the module/scripts folder. To
    # workaround this, we simply add the pats to sys ourselves
    real_sys_path = [os.path.realpath(p) for p in sys.path]
    python_path = os.environ.get('PYTHONPATH', '')
    for p in python_path.split(os.pathsep):
        p = os.path.realpath(p)     # Make sure symbolic links are resolved
        if p not in real_sys_path:
            sys.path.insert(0, p)

    unittestlib.run_tests()

    # Starting Maya 2016, we have to call uninitialize
    if float(maya.cmds.about(v=True)) >= 2016.0:
        maya.standalone.uninitialize()


def set_buffer_output(value):
    """
    Sets whether the standard output and standard error streams are buffered during the test run
    :param bool value: True to buffer output and standard error streams
    """

    settings.UnitTestSettings().bufferOutput = value


def set_file_new(value):
    """
    Sets whether a new file should be created after each test
    :param bool value: True if a new file should be created after each test
    """

    settings.UnitTestSettings().fileNew = value
