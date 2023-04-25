#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest unit test base class
"""

import os
import shutil
import unittest

from tpDcc import dcc
from tpDcc.libs.python import decorators

from tpDcc.libs.unittests.core import settings


class MetaUnitTestCase(type):
    def __call__(cls, *args, **kwargs):
        as_class = kwargs.get('as_class', True)
        if dcc.is_maya():
            from tpDcc.libs.unittests.dccs.maya import unittest
            if as_class:
                return unittest.MayaUnitTestCase
            else:
                return type.__call__(unittest.MayaUnitTestCase, *args, **kwargs)
        else:
            if as_class:
                return BaseUnitTestCase
            else:
                return type.__call__(BaseUnitTestCase, *args, **kwargs)


class BaseUnitTestCase(unittest.TestCase):
    """
    Base class for unit test cases inside tpDcc.libs.unittest
    New tests are not mandatory to inherit from this TestCase but this derived TestCase contains convenience
    functions to clean up temporary files
    """

    # Keep track of all temporary files that where created so they can be cleaned up after all tests have been run
    files_created = []

    # region Functions
    @classmethod
    def delete_temp_files(cls):
        """
        Delete the temp files in the cache and clear the cache
        """

        # If we don't want to keep temp files around for debugging purposes, delete them when
        # all tests in this tpTestCase have been run
        if settings.UnitTestSettings().delete_files:
            for f in cls.files_created:
                if os.path.exists(f):
                    os.remove(f)
            cls.files_created = []
            if os.path.exists(settings.UnitTestSettings().temp_dir):
                shutil.rmtree(settings.UnitTestSettings().temp_dir)

    @classmethod
    def get_temp_filename(cls, file_name):
        """
        Get a unique file path name in the testing directory
        The file will not be created, that is up to the caller. This file will be deleted when the test are finished
        :param str file_name: A partial path ex: 'directory/someFile.txt'
        :return: str, The full path to the temporary file
        """

        temp_dir = settings.UnitTestSettings().temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        base_name, ext = os.path.splitext(file_name)
        path = '{0}/{1}{2}'.format(temp_dir, base_name, ext)
        count = 0
        while os.path.exists(path):
            # If the file already exists, add an incremented number
            count += 1
            path = '{0}/{1}{2}{3}'.format(temp_dir, base_name, count, ext)
        cls.files_created.append(path)
        return path

    def assert_list_almost_equal(self, first, second, places=7, msg=None, delta=None):
        """
        Asserts that a list of floating point values are almost equal
        unittest has assertAlmostEqual and assertListEqual but no assertListAlmostEqual
        """

        self.assertEqual(len(first), len(second), msg)
        for a, b in zip(first, second):
            self.assertAlmostEqual(a, b, places, msg, delta)
    # endregion

    # region Override Functions
    def tearDown(self):
        """
        Method that is called before test in an individual class run
        For custom unit tests classes, this method should be override
        """

        super(BaseUnitTestCase, self).tearDown()

    @classmethod
    def tearDownClass(cls):
        """
        A class method called after tests in an individual class have run
        """

        super(BaseUnitTestCase, cls).tearDownClass()


@decorators.add_metaclass(MetaUnitTestCase)
class UnitTestCase(object):
    pass
