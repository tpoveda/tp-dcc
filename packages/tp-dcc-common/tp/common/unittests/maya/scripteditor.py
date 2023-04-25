#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya script editor state class implementation
"""

import maya.cmds

from tpDcc.libs.unittests.core import settings


class MayaScriptEditorState (object):
    """
    Provides methods to suppress and restore script editor output
    """

    # Used to restore logging states in the script editor
    suppress_results = None
    suppress_errors = None
    suppress_warnings = None
    suppress_info = None

    @classmethod
    def suppress_output(cls):
        """
        Hides all script editor output
        """

        if settings.UnitTestSettings().buffer_output:
            cls.suppress_results = maya.cmds.scriptEditorInfo(query=True, suppressResults=True)
            cls.suppress_errors = maya.cmds.scriptEditorInfo(query=True, suppressErrors=True)
            cls.suppress_warnings = maya.cmds.scriptEditorInfo(query=True, suppressWarnings=True)
            cls.suppress_info = maya.cmds.scriptEditorInfo(query=True, supressInfo=True)
            maya.cmds.scriptEditorInfo(
                edit=True, suppressResults=True, suppressInfo=True, suppressWarnings=True, suppressErrors=True)

    @classmethod
    def restore_output(cls):
        """
        Restores the script editor output settings to their original values
        """

        if None not in {cls.suppress_results, cls.suppress_errors, cls.suppress_warnings, cls.suppress_info}:
            maya.cmds.scriptEditorInfo(
                edit=True, suppressResults=cls.suppress_results, suppressInfo=cls.suppress_info,
                suppressWarnings=cls.suppress_warnings, suppressErrors=cls.suppress_errors)
