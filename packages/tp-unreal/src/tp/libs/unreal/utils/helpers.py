from __future__ import print_function, division, absolute_import

import unreal


def get_unreal_version_name() -> str:
    """
    Returns the version name of Unreal engine.

    :return: Unreal Engine version name.
    """

    return unreal.SystemLibrary.get_engine_version()


def get_unreal_version() -> list[int]:
    """
    Returns current version of Unreal engine

    :return: Unreal Engine version as a list of integers.
    """

    version_name = get_unreal_version_name()
    version_split = version_name.split("+++")[0]
    versions = version_split.split("-")
    main_version = versions[0].split(".")
    extra_version = versions[-1]
    version_int = [int(version) for version in main_version]
    version_int.append(int(extra_version))

    return version_int
