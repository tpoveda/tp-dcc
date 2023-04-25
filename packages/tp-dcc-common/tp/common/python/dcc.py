#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with apps
"""

import sys


def is_nuke():
    """
    Checks if Nuke is available or not
    :return: bool
    """

    try:
        import nuke
        return True
    except ImportError:
        return False


def is_maya():
    """
    Checks if Maya is available or not
    :return: bool
    """

    return 'maya.exe' in sys.executable.lower()


def is_mayapy():
    """
    Checks if Maya is available or not
    :return: bool
    """

    return 'mayapy.exe' in sys.executable.lower()


def is_max():
    """
    Checks if Max is available or not
    :return: bool
    """

    return '3dsmax' in sys.executable.lower()


def is_houdini():
    """
    Checks if Houdini is available or not
    :return: bool
    """

    return 'houdini' in sys.executable


def is_motionbuilder():
    """
    Checks if MotionBuilder is available or not
    :return: bool
    """

    return 'motionbuilder' in sys.executable.lower()
