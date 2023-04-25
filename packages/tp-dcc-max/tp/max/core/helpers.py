# !/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import

"""
Module that contains Max Python functions to work with 3ds Max application
"""

import os
import math
import logging

from pymxs import runtime as rt

from tp.common.python import win32

LOGGER = logging.getLogger()


def get_max_version(as_year=True):
    """
    Returns the current version of 3ds Max

    :param  bool as_year: Whether to return version as a year or not
    :return: Current version of your 3ds Max
    :rtype: long or float

    >>> print(get_max_version())
    2018.0

    >>> print(get_max_version(False))
    20000L
    """

    max_version = rt.maxVersion()
    version_number = max_version[0]

    if as_year:
        if version_number <= 20000:
            year = float(2000 + (math.ceil(version_number / 1000.0) - 2))
        else:
            year = float(max_version[7])
        return year

    return version_number


def get_scripts_folder():
    """
    Returns path where dccutils MaxScript files are stored

    :return: Path to MaxScript folder
    :rtype: str
    """

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maxscripts')


def get_installation_path():
    """
    Returns 3ds Max installation folder
    NOTE: This function is added here to avoid some errors related with 3ds Max PATH env var setup
    This functionality is available in dcclib for each specific DCC
    :return: str
    """

    version = rt.maxVersion()
    max_version = str(float(version[3]))
    year = float(version[7])

    if not win32.get_reg_key('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Autodesk\\3dsMax\\{}'.format(max_version)):
        LOGGER.error('3ds Max "{}" is not installed in your computer!'.format(year))
        return None

    key = win32.list_reg_key_values('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Autodesk\\3dsMax\\{}'.format(max_version))
    for keys in key:
        if keys[0] == 'Installdir':
            return keys[1]


def convert_python_list_to_maxscript_array(python_list):
    """
    Converts given Python list to a MaxScript Byte array
    :param python_list: list
    :return: rt.ByteArray
    """

    rt.execute('fn b2a b = (return b as Array)')
    return rt.b2a(python_list)


def convert_python_list_to_maxscript_bit_array(python_list):
    """
    Converts given Python list to a MaxScript Byte array
    :param python_list: list
    :return: rt.ByteArray
    """

    rt.execute('fn b2a b = (return b as BitArray)')
    return rt.b2a(python_list)
