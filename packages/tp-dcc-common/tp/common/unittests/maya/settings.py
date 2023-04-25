#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-unittest unit test Maya settings class
"""

from tpDcc.libs.unittests.core import settings


class MayaUnitTestSettings(settings.BaseUnitTestSettings, object):
    """
    Settings for running unit tests in Maya
    """

    # Specifies whether the standard output and standard error streams are buffered during the test run.
    # Output during a passing test is discarded. Output is echoed normally on test fail or error and is added to
    # the failure messages
    buffer_output = False
