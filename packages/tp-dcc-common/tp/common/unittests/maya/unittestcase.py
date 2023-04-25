#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest unit test Maya settings class
"""

import os

from tpDcc.libs.unittests.core import consts, unittestcase, settings

import maya.cmds


class MayaTestCase(unittestcase.BaseUnitTestCase, object):

    """
    Base class for unit test cases run in Maya
    Contains convenience functions to load/unload plug-ins and clean up temporary files
    """

    # Keep track of which plugins were loaded so we can unload them after all tests have been run
    plugins_loaded = set()

    @classmethod
    def load_plugin(cls, plugin):
        """
        Load the given plug-in and saves it to be unloaded when the tpTestCase is finished
        :param str plugin: Plug-in name
        """

        maya.cmds.loadPlugin(plugin, quiet=True)
        cls.plugins_loaded.add(plugin)

    @classmethod
    def unload_plugins(cls):
        """
        Unload any plugins that this test case loaded
        """

        for plugin in cls.plugins_loaded:
            maya.cmds.unloadPlugin(plugin)
        cls.plugins_loaded = []

    def tearDown(self):
        """
        A class method called before tests in an individual class run
        """

        if settings.UnitTestSettings().file_new and consts.UNIT_TEST_VAR not in os.environ.keys():
            # If running tets without the custom runner, like with PyCharm, the file new of the TestResult class
            # is not used so call file new here
            maya.cmds.file(f=True, new=True)

    @classmethod
    def tearDownClass(cls):
        """
        A class method called after tests in an individual class have run
        """

        super(MayaTestCase, cls).tearDownClass()
        cls.delete_temp_files()
        cls.unload_plugins()
