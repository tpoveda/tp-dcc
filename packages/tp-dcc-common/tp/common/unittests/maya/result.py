#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest unit test Maya result class
"""

import os
import shutil
import logging

import maya.cmds

from tpDcc.libs.unittests.core import settings, result
from tpDcc.libs.unittests.dccs.maya import scripteditor


class MayaUnitTestResult(result.BaseUnitTestResult, object):
    """
    Customize Maya the test result so we can do things like do a file new between each test and suppress script
    editor output
    """

    def startTestRun(self):
        """
        Called before any tests are run
        """

        super(MayaUnitTestResult, self).startTestRun()

        scripteditor.MayaScriptEditorState.suppress_output()
        if settings.UnitTestSettings().buffer_output:
            # Disable any logging while running tests. By disabling critical, we are disabling logging at all levels
            # below critical as well
            logging.disable(logging.CRITICAL)

    def stopTestRun(self):
        """
        Called after all tests are run
        """

        if settings.UnitTestSettings().buffer_output:
            # Restore logging state
            logging.disable(logging.NOTSET)
        scripteditor.MayaScriptEditorState.restore_output()
        if settings.UnitTestSettings().delete_files and os.path.exists(settings.UnitTestSettings().temp_dir):
            shutil.rmtree(settings.UnitTestSettings().temp_dir)

        super(MayaUnitTestResult, self).stopTestRun()

    def stopTest(self, test):
        """
        Called after an individual test is run
        @param test: TestCase that just ran
        """
        super(MayaUnitTestResult, self).stopTest(test)

        if settings.UnitTestSettings().file_new:
            maya.cmds.file(f=True, new=True)

    def addSuccess(self, test):
        """
        Override the base addSuccess method so we can store a list of the successful tests
        @param test: Testase that sucessfully ran.
        """

        super(MayaUnitTestResult, self).addSuccess(test)
        self._successes.append(test)
