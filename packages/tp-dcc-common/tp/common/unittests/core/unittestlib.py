#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest function core implementations
"""

import os
import sys
import logging
import unittest

from tpDcc import dcc
from tpDcc.core import library, reroute
from tpDcc.libs.python import python

from tpDcc.libs.unittests.core import settings, result

LOGGER = logging.getLogger('tpDcc-libs-unittests')


class UnitTestsLib(library.DccLibrary, object):

    ID = 'tpDcc-libs-datalibrary'

    def __init__(self, *args, **kwargs):
        super(UnitTestsLib, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls):
        base_tool_config = library.DccLibrary.config_dict()
        tool_config = {
            'name': 'Unit Tests Library',
            'id': cls.ID,
            'supported_dccs': {'maya': ['2017', '2018', '2019', '2020']},
            'tooltip': 'Library to manage unit tests in a DCC agnostic way'
        }
        base_tool_config.update(tool_config)

        return base_tool_config


@reroute.reroute_factory(UnitTestsLib.ID, 'unittestlib')
def load_default_unit_tests():
    """
    Loads default unit tests of a specific DCC
    """

    return list()


@reroute.reroute_factory(UnitTestsLib.ID, 'unittestlib')
def run_tests_from_command_line():
    """
    Run the tests in Maya standalone mode
    """

    raise NotImplementedError('run test from command line not implemented for current DCC: {}'.format(dcc.name()))


def run_tests(directories=None, test=None, test_suite=None):

    """
    Run all the tests in the given paths
    :param list(str) directories: A generator or list of paths containing tests to run
    :param str test: Optional name of a specific test to run
    :param unittest.TestSuite test_suite: Optional TestSuite to run. If omitted, a TestSuite will be generated
    :return: None
    """

    if test_suite is None:
        test_suite = get_tests(directories, test)

    runner = unittest.TextTestRunner(verbosity=2, resultclass=result.BaseUnitTestResult)
    runner.failfast = False
    try:
        runner.buffer = settings.UnitTestSettings().buffer_output
    except Exception:
        pass
    runner.run(test_suite)


def get_tests(directories=None, test=None, test_suite=None):
    """
    Get a UnitTests containing all the desired tests
    :param list(str) directories:  Optional list of directories with which to search for tests. If omitted, use all
    "tests" directories of the modules found in specific app modules path (e.g, maya - MAYA_MODULE_PATH)
    :param str test: Optional test path to find a specific test such as 'test_myTest.SomeTestCase.test_function'
    :param unittest.TestSuite test_suite: Optional unittest.TestSuite to add the discovered test to. If omitted a new
    TestSuite will be created
    :return: unittest.TestSuite
    """

    directories = python.force_list(directories)
    directories.extend(python.force_list(load_default_unit_tests()))

    # Populate a TestSuite with all the tests
    if test_suite is None:
        test_suite = unittest.TestSuite()

    if test:
        # Find the specified test to run
        directories_added_to_path = [p for p in directories if add_to_path(p)]
        discovered_suite = unittest.TestLoader().loadTestsFromName(test)
        if discovered_suite.countTestCases():
            test_suite.addTests(discovered_suite)
    else:
        # Find all tests to run
        directories_added_to_path = []
        for p in directories:
            discovered_suite = unittest.TestLoader().discover(p)
            if discovered_suite.countTestCases():
                new_test_suite = unittest.TestSuite()
                for suites in discovered_suite:
                    for suite in suites._tests:
                        new_test_suite.addTest(suite)
                test_suite.addTest(new_test_suite)

    # Remove the added paths
    for path in directories_added_to_path:
        sys.path.remove(path)

    return test_suite


def set_temp_dir(directory):

    """
    Sets where files generated from tests should be stored
    :param str directory: A directory path
    :return: None
    """

    if os.path.exists(directory):
        settings.UnitTestSettings().temp_dir = directory
    else:
        raise RuntimeError('{0} does not exists.'.format(directory))


def set_delete_files(value):

    """
    Sets whether temp files should be delted after running all tests in a test case
    :param bool value: True to delete files registered with a TestCase
    :return: None
    """

    settings.UnitTestSettings().delete_files = value


def add_to_path(path):

    """
    Add the specified path to the system path
    :param str path: Path to add
    :return: bool True if the path was added. False if path does not exist or path was already in sys.path
    """

    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        return True

    return False
