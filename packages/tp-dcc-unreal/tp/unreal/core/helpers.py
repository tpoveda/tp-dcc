#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Unreal utility functions and classes
"""

import unreal


def get_unreal_version_name():
    """
    Returns the version name of Unreal engine
    :return: str
    """

    return unreal.SystemLibrary.get_engine_version()


def get_unreal_version():
    """
    Returns current version of Unreal engine
    :return: list(int)
    """

    version_name = get_unreal_version_name()
    version_split = version_name.split('+++')[0]
    versions = version_split.split('-')
    main_version = versions[0].split('.')
    extra_version = versions[-1]
    version_int = [int(version) for version in main_version]
    version_int.append(int(extra_version))

    return version_int
