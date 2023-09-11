#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Unreal utility functions and classes
"""

import unreal


def unreal_version_name() -> str:
    """
    Returns the version name of Unreal engine.

    :return: version name.
    :rtype: str
    """

    return unreal.SystemLibrary.get_engine_version()


def unreal_version() -> list[int]:
    """
    Returns current version of Unreal engine.

    :return: Unreal Engine version as list of integers.
    :rtype: list[int]
    """

    version_name = unreal_version_name()
    version_split = version_name.split('+++')[0]
    versions = version_split.split('-')
    main_version = versions[0].split('.')
    extra_version = versions[-1]
    version_int = [int(version) for version in main_version]
    version_int.append(int(extra_version))

    return version_int
