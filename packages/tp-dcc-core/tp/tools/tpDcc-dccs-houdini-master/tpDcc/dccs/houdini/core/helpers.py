#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Houdini utility functions and classes
"""

from __future__ import print_function, division, absolute_import

import hou
import hdefereval


def get_houdini_version(as_string=True):
    """
    Returns version of the executed Houdini
    :param as_string: bool, Whether to return the stiring version or not
    :return: variant, int or str
    """

    if as_string:
        return hou.applicationVersionString()
    else:
        return hou.applicationVersion()


def get_houdini_pass_main_thread_function():
    """
    Return Houdini function to execute function in Houdini main thread
    :return: fn
    """

    return hdefereval.executeInMainThreadWithResult
