# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains MaxPlus related Python functions
"""

import math
import logging

import MaxPlus

from tp.core import log
from tp.common.python import win32

logger = log.tpLogger


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

    # 3dsMax Version returns a number which contains max version, sdk version, etc...
    version_id = MaxPlus.Application_Get3DSMAXVersion()

    # Transform it to a version id
    # (Macro to get 3ds max release from version id)
    # NOTE: 17000 = 2015, 17900 = 2016, etc
    version_number = (version_id >> 16) & 0xffff

    if as_year:
        year = 2000 + (math.ceil(version_number / 1000.0) - 2)
        return year

    return version_number


def get_max_release_version(version_id):
    """
    Returns current release version of 3ds Max

    :param version_id: int, release ID of the current Max version
    :return: 3ds Max release version
    :rtype: long

    .. code-block:: python

        import MaxPlus
        from dccutils.max import app

        version_id = MaxPlus.Application_Get3DSMAXVersion()
        print(app.get_max_release_version(version_id))
        # Result: 20000

    .. tip::
        Release 17000 == Max 2015, Release 179000 == 2016 alpha, etc

    .. seealso::
        `Max Plus Application Class: Get3DSMAXVersion
        <https://help.autodesk.com/view/3DSMAX/2018/ENU/?guid=__py_ref_class_max_plus_1_1_application_html>`_
    """

    version_number = (version_id >> 16) & 0xffff

    return version_number


def get_max_version_to_year(version):
    """
    Get 3ds Max year from the release version

    :return: Max release version
    :rtype: int

    .. code-block:: python

        import MaxPlus
        import dccutils

        release_version = app.get_max_release_version(version_id)
        print(app.get_max_version_to_year(release_version))
        # Result: 2018.0
    """

    year = 2000 + (math.ceil(version / 1000.0) - 2)
    return year


def get_installation_path():
    """
    Returns 3ds Max installation folder
    NOTE: This function is added here to avoid some errors related with 3ds Max PATH env var setup
    This functionality is available in dcclib for each specific DCC
    :return: str
    """

    version_id = MaxPlus.Application_Get3DSMAXVersion()
    version_number = (version_id >> 16) & 0xffff
    year = 2000 + (math.ceil(version_number / 1000.0) - 2)
    max_version = str(float(str(version_number)[:2]))

    if not win32.get_reg_key('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Autodesk\\3dsMax\\{}'.format(max_version)):
        logger.error('3ds Max "{}" is not installed in your computer!'.format(year))
        return None

    key = win32.list_reg_key_values('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Autodesk\\3dsMax\\{}'.format(max_version))
    for keys in key:
        if keys[0] == 'Installdir':
            return keys[1]
