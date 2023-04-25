#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest unit test base result class
"""

import os
import unittest

from tpDcc import dcc
from tpDcc.libs.python import decorators
from tpDcc.libs.unittests.core import consts


class MetaUnitTestResult(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tpDcc.libs.unittests.dccs.maya import result
            if as_class:
                return result.MayaUnitTestResult
            else:
                return type.__call__(result.MayaUnitTestResult, *args, **kwargs)
        else:
            if as_class:
                return BaseUnitTestResult
            else:
                return type.__call__(BaseUnitTestResult, *args, **kwargs)


class BaseUnitTestResult(unittest.TextTestResult):
    """
    Base test result class
    """

    def __init__(self, stream, descriptions, verbosity):
        super(BaseUnitTestResult, self).__init__(stream, descriptions, verbosity)
        self._successes = list()

    @property
    def successes(self):
        return self._successes

    def startTestRun(self):
        """
        Called before any tests are run
        """

        super(BaseUnitTestResult, self).startTestRun()

        # Create an environment variable that specifies tests are being run through the custom runner
        os.environ[consts.UNIT_TEST_VAR] = '1'

    def stopTestRun(self):
        """
        Called after all tests are run
        """

        del os.environ[consts.UNIT_TEST_VAR]

        super(BaseUnitTestResult, self).stopTestRun()

    def stopTest(self, test):
        """
        Called after an individual test is run
        @param test: TestCase that just ran
        """
        super(BaseUnitTestResult, self).stopTest(test)

    def addSuccess(self, test):
        """
        Override the base addSuccess method so we can store a list of the successful tests
        @param test: Testase that sucessfully ran.
        """

        super(BaseUnitTestResult, self).addSuccess(test)
        self._successes.append(test)


@decorators.add_metaclass(MetaUnitTestResult)
class UnitTestResult(object):
    pass
